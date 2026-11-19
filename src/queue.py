# -*- coding: utf-8 -*-
"""并发下载队列：多线程 + 失败重试 + 状态持久化。"""
from __future__ import annotations

import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from . import downloader, library, router
from .models import norm

STATE_NAME = ".music3_queue.json"


def _state_path(root):
    return os.path.join(root, STATE_NAME)


def load_state(root=library.DEFAULT_ROOT):
    p = _state_path(root)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"done": [], "failed": []}


def save_state(st, root=library.DEFAULT_ROOT):
    try:
        with open(_state_path(root), "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
        return True
    except Exception:
        return False


def run(
    keywords,
    workers=3,
    per_kw=1,
    sources=None,
    bili=True,
    retries=2,
    root=library.DEFAULT_ROOT,
    progress=None,
    force=False,
    gap=1.5,
    job_id=None,
    resume=True,
):
    """批量搜索+下载。返回统计 dict。

    keywords: 关键词列表
    workers : 并发线程数
    per_kw  : 每个关键词下载几首
    retries : 单曲失败重试次数
    job_id  : 传入则把进度同步推到任务中心（SSE 消费）
    resume  : 落盘任务清单，进程中断后可用 resume_queue() 续跑
    """
    sources = sources or (["qq", "netease", "bilibili"] if bili else ["qq", "netease"])
    st = load_state(root)
    stats = {"ok": 0, "skip": 0, "fail": 0, "total": 0}
    lock = threading.Lock()
    tasks = []

    # 任务中心桥接
    _jp = None
    if job_id:
        from . import jobs as _jobs

        def _jp(text, **cnt):
            _jobs.log(job_id, text, **cnt)

        try:
            _jobs.progress(job_id, total=len(keywords))
        except Exception:
            pass

    # 持久化清单（用于中断恢复）
    from . import persist

    pstate = None
    if resume:
        pstate = {
            "created": time.time(),
            "meta": {
                "n": per_kw,
                "sources": list(sources),
                "bili": bool(bili),
                "workers": workers,
            },
            "tasks": persist.make_tasks(
                list(keywords), n=per_kw, sources=list(sources), bili=bili
            ),
        }
        persist.save(pstate["tasks"], root, pstate["meta"])

    # 阶段1：串行搜索（避免并发搜索触发风控）
    # 首选源空结果 -> 自动换备用源再搜一次，避免单源限流被误判成"无结果"
    fallback = [s for s in ("netease", "qq") if s not in sources]
    def say(text, **cnt):
        """统一日志出口：同时写任务中心与本地 progress。"""
        if _jp:
            try:
                _jp(text, **cnt)
            except Exception:
                pass
        if progress:
            try:
                progress(text)
            except Exception:
                pass

    def search_one(kw):
        """单关键词搜索，带多源兜底。返回 (kw, res, used)。"""
        try:
            res = router.search(kw, sources=sources, limit=15, bili=bili)
            used = ",".join(sources)
            if not res and fallback:
                say("[搜索] %s -> 首选源空，换 %s 重搜" % (kw, fallback[0]))
                res = router.search(kw, sources=fallback, limit=15, bili=False)
                used = fallback[0]
            return kw, res or [], used
        except Exception as e:
            say("[搜索] %s -> ERR %r" % (kw, e), fail=1)
            return kw, [], ""

    # 搜索并发度：2（源限流限制，再高会触发 412/空结果）
    search_workers = min(2, max(1, len(keywords)))
    say("[搜索] 开始 %d 个关键词，并发 %d" % (len(keywords), search_workers))

    results = []
    with ThreadPoolExecutor(max_workers=search_workers) as ex:
        futs = [ex.submit(search_one, kw) for kw in keywords]
        for fu in as_completed(futs):
            try:
                results.append(fu.result())
            except Exception as e:
                say("[搜索] 异常 %r" % (e,), fail=1)

    # 按原顺序整理
    order = {kw: i for i, kw in enumerate(keywords)}
    results.sort(key=lambda x: order.get(x[0], 999))

    for kw, res, used in results:
        if not res:
            with lock:
                stats["fail"] += 1
                stats["total"] += 1
            say("[搜索] %s -> 无结果" % kw, fail=1)
            if pstate:
                for t in pstate["tasks"]:
                    if t["kw"] == kw and t["state"] == "pending":
                        t["state"] = "fail"
                        t["err"] = "no result"
                        break
                persist.save(pstate["tasks"], root, pstate["meta"])
            continue
        picked = res[:per_kw]
        for t in picked:
            tasks.append((kw, t))
        with lock:
            stats["total"] += len(picked)
        say("[搜索] %s -> %d 首（%s）" % (kw, len(picked), used))

    idx = library.scan(root)

    def work(item):
        kw, t = item
        key = norm(t.artists)[:12] + "|" + norm(t.title)
        with lock:
            if key in idx and not force:
                return ("skip", t, idx[key])
        d = library.dest_dir(t.source, root)
        say("[下载中] %s - %s [%s]" % (t.artists or "?", t.title, t.source))
        last = ""
        for attempt in range(retries + 1):
            try:
                ok, msg, path = downloader.download(t, d)
            except Exception as e:
                ok, msg, path = False, repr(e), ""
            if ok:
                with lock:
                    idx[key] = path
                return ("ok", t, path)
            last = msg
            if attempt < retries:
                say("[重试%d] %s | %s" % (attempt + 1, t.title, str(msg)[:80]))
                time.sleep(3 * (attempt + 1))
        return ("fail", t, last)

    # 阶段2：并发下载
    _jobs_mod = None
    if job_id:
        from . import jobs as _jobs_mod

    with ThreadPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {ex.submit(work, it): it for it in tasks}
        for fu in as_completed(futs):
            if _jobs_mod and _jobs_mod.is_canceled(job_id):
                for f in futs:
                    f.cancel()
                say("[取消] 用户中止")
                break
            try:
                kind, t, info = fu.result()
            except Exception as e:
                with lock:
                    stats["fail"] += 1
                say("[下载] ERR %r" % (e,), fail=1)
                continue
            with lock:
                stats[kind] += 1
                done_n = stats["ok"] + stats["skip"] + stats["fail"]
            it_kw = (futs.get(fu) or ("", None))[0]
            if kind == "ok":
                say("[OK]   %s -> %s" % (t.display.split(" [")[0], info), ok=1, done=1)
            elif kind == "skip":
                say("[SKIP] %s 已存在" % t.title, skip=1, done=1)
            else:
                say("[FAIL] %s | %s" % (t.title, str(info)[:120]), fail=1, done=1)

            # 持久化：该关键词标记完成
            if pstate:
                with lock:
                    for pt in pstate["tasks"]:
                        if pt["kw"] == it_kw and pt["state"] == "pending":
                            pt["state"] = "done" if kind in ("ok", "skip") else "fail"
                            pt["path"] = info if kind == "ok" else ""
                            pt["err"] = "" if kind in ("ok", "skip") else str(info)[:200]
                            break
                    persist.save(pstate["tasks"], root, pstate["meta"])
            if _jobs_mod:
                try:
                    _jobs_mod.progress(job_id, done=done_n, total=stats["total"])
                except Exception:
                    pass

    st["done"] = list(set(st.get("done", []) + [t[1].track_id for t in tasks]))
    save_state(st, root)
    library.save_index(idx, root)
    return stats


def resume_queue(
    root=library.DEFAULT_ROOT,
    workers=None,
    progress=None,
    job_id=None,
    force=False,
    retries=2,
):
    """从落盘清单继续未完成的任务。返回 stats 或 None（无待办）。

    用法：进程中断后重跑同一条命令即可，或调这个函数。
    """
    from . import persist

    d = persist.load(root)
    if not d:
        return None
    meta = d.get("meta") or {}
    todo = [t for t in d["tasks"] if t.get("state") == "pending"]
    if not todo:
        # 全部完成，清掉清单
        persist.clear(root)
        return {"ok": 0, "skip": 0, "fail": 0, "total": 0, "resumed": 0}

    kws = [t["kw"] for t in todo]
    # 用清单里第一个任务的原参数（同一批任务参数一致）
    first = todo[0]
    return run(
        kws,
        workers=workers or meta.get("workers") or 3,
        per_kw=first.get("n") or meta.get("n") or 1,
        sources=first.get("sources") or meta.get("sources"),
        bili=first.get("bili", meta.get("bili", False)),
        retries=retries,
        root=root,
        progress=progress,
        force=force,
        job_id=job_id,
        resume=True,
    )
