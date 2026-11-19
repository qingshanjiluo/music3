# -*- coding: utf-8 -*-
"""music3 桌面启动器 —— 双击即可用的统一入口。

设计要点：
  * 纯标准库，无第三方依赖，Windows 控制台可用
  * 菜单式交互，不需要记命令
  * 服务状态实时探测（端口 + HTTP 探活）
  * 配置可视化编辑（读 config.json 逐项修改，自动备份）
  * 所有动作调用既有模块，不重复实现业务逻辑
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

PORT = 8420
BASE = "http://127.0.0.1:%d" % PORT

# ---------- 终端颜色 ----------
if os.name == "nt":
    try:
        import ctypes

        k = ctypes.windll.kernel32
        k.SetConsoleMode(k.GetStdHandle(-11), 7)   # 开启 VT100
    except Exception:
        pass

NO_COLOR = not sys.stdout.isatty()


def c(code, s):
    if NO_COLOR:
        return s
    return "\033[%sm%s\033[0m" % (code, s)


def dim(s):
    return c("2", s)


def bold(s):
    return c("1", s)


def ok(s):
    return c("32", s)


def warn(s):
    return c("33", s)


def bad(s):
    return c("31", s)


def acc(s):
    return c("36", s)


def dwidth(s):
    """显示宽度：东亚宽字符算 2 列，ANSI 转义不计。"""
    import re
    import unicodedata

    s = re.sub(r"\033\[[0-9;]*m", "", s)
    w = 0
    for ch in s:
        w += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return w


def dpad(s, width):
    """按显示宽度右补空格。"""
    return s + " " * max(0, width - dwidth(s))


def line(ch="-", n=58):
    print(dim(ch * n))


def title(s):
    print()
    line("=")
    print("  " + bold(s))
    line("=")


# ---------- 服务状态 ----------
def port_up(port=PORT):
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.4)
    try:
        return s.connect_ex(("127.0.0.1", port)) == 0
    finally:
        s.close()


def api(path, timeout=3):
    """GET 一个 API，返回 dict 或 None。"""
    try:
        req = urllib.request.Request(BASE + path)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def service_status():
    up = port_up()
    if not up:
        return False, {}
    st = api("/api/stat", timeout=2) or {}
    return True, st


# ---------- 配置 ----------
CFG = os.path.join(HERE, "config.json")

FIELD_DESC = {
    "root": "音乐根目录",
    "sources": "默认源（逗号分隔）",
    "search_size": "搜索条数",
    "min_score": "最低匹配分（0~1）",
    "workers": "并发下载数",
    "retries": "失败重试次数",
    "tag_cover": "写封面标签（true/false）",
    "tag_lyric": "写歌词标签（true/false）",
    "auto_lyric": "下载后自动补歌词（true/false）",
    "audio_format": "B站音质优先级",
    "ffmpeg": "ffmpeg 路径",
    "ffprobe": "ffprobe 路径",
    "valid_min_sec": "最短有效时长（秒）",
    "valid_max_sec": "最长有效时长（秒）",
    "valid_min_bytes": "最小文件字节",
    "cache_dir": "缓存目录",
}


def load_cfg():
    try:
        with open(CFG, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(bad("读配置失败: %r" % (e,)))
        return {}


def save_cfg(d):
    try:
        bak = CFG + ".bak"
        if os.path.exists(CFG):
            with open(CFG, "r", encoding="utf-8") as f:
                old = f.read()
            with open(bak, "w", encoding="utf-8") as f:
                f.write(old)
        tmp = CFG + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, CFG)
        return True
    except Exception as e:
        print(bad("写配置失败: %r" % (e,)))
        return False


def parse_val(s):
    """把字符串解析成 JSON 可接受的类型。"""
    t = s.strip()
    low = t.lower()
    if low in ("true", "yes", "y", "1"):
        return True
    if low in ("false", "no", "n", "0"):
        return False
    try:
        return int(t)
    except ValueError:
        pass
    try:
        return float(t)
    except ValueError:
        pass
    if t.startswith("[") or t.startswith("{"):
        try:
            return json.loads(t)
        except Exception:
            pass
    return t


# ---------- 动作 ----------
def _stale_web_procs():
    """找出命令行含 run.py web 的 python 进程。"""
    if os.name != "nt":
        return []
    try:
        ps = (
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "Where-Object { $_.CommandLine -like '*run.py*web*' } | "
            "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"
        )
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=15)
        out = []
        for line in (r.stdout or "").splitlines():
            line = line.strip()
            if line:
                out.append(line)
        return out
    except Exception:
        return []


def act_start():
    title("启动 Web 服务")
    if port_up():
        print(warn("  服务已在运行 → ") + acc(BASE))
        return

    stale = _stale_web_procs()
    if stale:
        print(warn("  发现残留进程（占着端口但没响应）:"))
        for s in stale:
            print("    " + dim(s[:90]))
        print("  " + dim("先清掉再启动？(Y/n)"))
        if not ask("  > ").strip().lower().startswith("n"):
            for s in stale:
                pid = s.split("\t")[0].strip()
                if pid.isdigit():
                    try:
                        subprocess.run(["taskkill", "/F", "/PID", pid],
                                       capture_output=True, timeout=10)
                    except Exception:
                        pass
            time.sleep(1.5)
            print(ok("  已清理"))

    args = [sys.executable, "-X", "utf8", "run.py", "web"]
    try:
        if os.name == "nt":
            subprocess.Popen(args, cwd=HERE,
                             creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(args, cwd=HERE)
    except Exception as e:
        print(bad("  启动失败: %r" % (e,)))
        return

    print(dim("  等待服务就绪（首次启动需编译缓存，可能十几秒）…"))
    for _ in range(40):          # 最多 20 秒
        time.sleep(0.5)
        if port_up():
            print(ok("  已启动 → ") + acc(BASE))
            st = api("/api/stat", timeout=3)
            if st:
                print("  " + dim("曲库 " + " / ".join("%s %d" % (k, v) for k, v in st.items())))
            return
    # 失败诊断
    print(bad("  20 秒内未监听端口 %d" % PORT))
    print("  " + dim("诊断:"))
    print("    python  " + sys.executable)
    print("    run.py  " + ("存在" if os.path.exists(os.path.join(HERE, "run.py")) else bad("缺失")))
    print("    web.py  " + ("存在" if os.path.exists(os.path.join(HERE, "src", "web.py")) else bad("缺失")))
    print("  " + dim("直接跑一次看报错："))
    print("    " + acc("python -X utf8 run.py web"))
    print("  " + dim("端口被谁占用："))
    print("    " + acc("Get-NetTCPConnection -LocalPort 8420 | Select OwningProcess"))


def act_open_web():
    if not port_up():
        print(warn("  服务未运行，先启动"))
        act_start()
        if not port_up():
            return
    import webbrowser

    webbrowser.open(BASE)
    print(ok("  已在浏览器打开 ") + acc(BASE))


def act_stop():
    title("停止 Web 服务")
    if not port_up():
        print(dim("  服务未运行"))
        return
    if os.name == "nt":
        try:
            ps = (
                "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                "Where-Object { $_.CommandLine -like '*run.py*web*' } | "
                "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps],
                capture_output=True,
                timeout=20,
            )
        except Exception as e:
            print(bad("  停止失败: %r" % (e,)))
            return
    time.sleep(1.2)
    print(ok("  已停止") if not port_up() else bad("  端口仍被占用"))


def act_status():
    title("运行状态")
    up, st = service_status()
    print("  服务   " + (ok("● 运行中") + "  " + acc(BASE) if up else dim("○ 未启动")))

    # 曲库（library.count 返回 {子目录名: mp3 数} 整本字典）
    try:
        from src import library, config as cfg

        root = cfg.get("root") or "D:\\音乐"
        cnt = library.count(root) or {}
        sub = int(cnt.get("投稿", 0))
        arc = int(cnt.get("_归档_封存", 0))
        total = sum(int(v) for v in cnt.values())
        print("  曲库   投稿 %s / 归档 %s  共 %s 首" % (
            bold(str(sub)), bold(str(arc)), bold(str(total))))
        others = {k: v for k, v in cnt.items() if k not in ("投稿", "_归档_封存")}
        if others:
            print("         其他 " + dim(", ".join("%s %d" % (k, v) for k, v in others.items())))
        print("  目录   " + dim(root))
    except Exception as e:
        print(bad("  曲库读取失败: %r" % (e,)))

    # 维护
    try:
        from src import maintain

        s = maintain.status()
        t = s.get("totals") or {}
        print("  维护   已跑 %s 轮，上次 %s" % (bold(str(s["runs"])), s["last_run_str"] or dim("从未")))
        print("         累计 歌词 +%s / 封面 +%s / 清理 %s" % (
            bold(str(t.get("lyric", 0))), bold(str(t.get("cover", 0))), bold(str(t.get("clean", 0)))))
        if s.get("cursor"):
            for k, v in s["cursor"].items():
                print("         断点 %s → %s" % (dim(k or "(全库)"), dim(os.path.basename(v))))
    except Exception:
        pass

    # 缓存
    try:
        from src import coverfill, lyricfill, covercache

        cs = coverfill.cache_stats()
        ls = lyricfill.cache_stats()
        print("  缓存   封面 %s 个 / %.1f MB     歌词 %s 个 / %.1f KB" % (
            bold(str(cs["files"])), cs["bytes"] / 1048576,
            bold(str(ls["files"])), ls["bytes"] / 1024))
    except Exception:
        pass


def act_config():
    title("配置编辑")
    d = load_cfg()
    if not d:
        return
    keys = [k for k in d.keys() if k not in ("src_subdir", "src_weight")]
    for i, k in enumerate(keys, 1):
        v = d[k]
        vs = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        if len(vs) > 46:
            vs = vs[:43] + "…"
        print("  %2d) %-16s %s" % (i, k, acc(vs)))
        print("      " + dim(FIELD_DESC.get(k, "")))
    print()
    print("  " + dim("输入编号改一项，回车返回"))
    s = ask("  > ").strip()
    if not s.isdigit():
        return
    idx = int(s) - 1
    if idx < 0 or idx >= len(keys):
        print(bad("  编号超范围"))
        return
    k = keys[idx]
    cur = d[k]
    print("  %s 当前: %s" % (k, acc(json.dumps(cur, ensure_ascii=False) if not isinstance(cur, str) else cur)))
    nv = ask("  新值（回车取消）: ").strip()
    if not nv:
        print(dim("  已取消"))
        return
    d[k] = parse_val(nv)
    if save_cfg(d):
        print(ok("  已保存（原文件备份为 config.json.bak）"))
        if port_up():
            print(warn("  服务在运行，改配置需重启生效 → 菜单 3 停止后重新 1 启动"))


def act_search():
    title("搜索与下载")
    print("  " + dim("输入「歌名 歌手」，回车搜索；直接回车返回"))
    kw = ask("  > ").strip()
    if not kw:
        return
    try:
        from src import router, downloader, library
    except Exception as e:
        print(bad("  模块加载失败: %r" % (e,)))
        return
    # 只用快源（酷我/千千/咪咕 常年 503，会拖到 17s+）
    srcs = ["qq", "netease", "bilibili"]
    print(dim("  搜索中（qq + netease + bilibili）…"))
    t0 = time.time()
    try:
        res = router.search(kw, sources=srcs, limit=12, bili=True, use_cache=True)
    except Exception as e:
        print(bad("  搜索失败: %r" % (e,)))
        return
    if not res:
        print(bad("  无结果"))
        print("  " + dim("试试：只写歌名 / 换个歌手名 / 检查网络"))
        return
    print(ok("  %d 条结果  %.2fs" % (len(res), time.time() - t0)))
    line()
    for i, t in enumerate(res, 1):
        print("  %2d) %s" % (i, dpad((t.title or "")[:34], 36))
              + dim("%s · %s · %.0fs" % (t.artists or "?", t.source, t.duration_s or 0)))
    line()
    s = ask("  下载第几首（回车取消）: ").strip()
    if not s.isdigit():
        return
    i = int(s) - 1
    if i < 0 or i >= len(res):
        print(bad("  超范围"))
        return
    t = res[i]
    dest = library.dest_dir(t.source)
    print(dim("  下载到 %s …" % dest))
    t0 = time.time()
    okk, msg, path = downloader.download(t, dest)
    if okk:
        print(ok("  完成 %.1fs" % (time.time() - t0)))
        print("  " + acc(path))
    else:
        print(bad("  失败: %s" % (msg,)))
        print("  " + dim("换一首试试（QQ 的 vkey 有时会失效，选网易云那条）"))


def act_fill():
    title("批量补全")
    print("  1) 补歌词    2) 补封面    3) 两个都补")
    s = ask("  > ").strip()
    if s not in ("1", "2", "3"):
        return
    print("  " + dim("子目录（留空=全库，例如 投稿\\QQ音乐）"))
    sub = ask("  > ").strip()
    print("  " + dim("最多处理几首（留空=20）"))
    n = ask("  > ").strip()
    limit = int(n) if n.isdigit() else 20
    try:
        from src import lyricfill, coverfill, browse, config as cfg
    except Exception as e:
        print(bad("  模块加载失败: %r" % (e,)))
        return
    root = cfg.get("root") or "D:\\音乐"
    paths = [t["path"] for t in browse.list_tracks(root, sub, limit=1000000)][:limit]
    if not paths:
        print(bad("  没有曲目"))
        return
    print(dim("  处理 %d 首…" % len(paths)))
    dok = dm = cok = cm = 0
    for i, p in enumerate(paths, 1):
        name = os.path.basename(p)[:34]
        if s in ("1", "3"):
            try:
                if lyricfill.fill_one(p, write_id3=True).get("ok"):
                    dok += 1
                else:
                    dm += 1
            except Exception:
                dm += 1
        if s in ("2", "3"):
            try:
                if coverfill.fill_one(p, write_id3=True).get("ok"):
                    cok += 1
                else:
                    cm += 1
            except Exception:
                cm += 1
        print("  [%d/%d] %-36s" % (i, len(paths), name), end="\r")
    print()
    if s in ("1", "3"):
        print("  歌词  " + ok("+%d" % dok) + " / " + dim("-%d" % dm))
    if s in ("2", "3"):
        print("  封面  " + ok("+%d" % cok) + " / " + dim("-%d" % cm))


def act_health():
    title("库健康检查")
    print("  " + dim("深度模式读 ID3，慢但准（y/N）"))
    deep = ask("  > ").strip().lower().startswith("y")
    try:
        from src import health, config as cfg
    except Exception as e:
        print(bad("  模块加载失败: %r" % (e,)))
        return
    root = cfg.get("root") or "D:\\音乐"
    print(dim("  扫描中…"))
    t0 = time.time()
    try:
        r = health.scan(root, "", deep=deep, limit=2000)
    except Exception as e:
        print(bad("  扫描失败: %r" % (e,)))
        return
    print("  %.1fs  共 %d 首  %.1f MB  健康分 %s" % (
        time.time() - t0, r["total"], r["total_size_mb"], bold(str(r["score"]))))
    line()
    for k, v in r["summary"].items():
        print("  %-8s %s" % (k, ok(str(v)) if v == 0 else warn(str(v))))


def act_maintain():
    title("维护守护")
    print("  1) 跑一轮（20 首）   2) 跑 5 轮   3) 跑到完成   4) 看日志")
    s = ask("  > ").strip()
    try:
        from src import maintain
    except Exception as e:
        print(bad("  模块加载失败: %r" % (e,)))
        return
    if s == "4":
        for l in maintain.tail_log(40):
            print("  " + l)
        return
    rounds = {"1": 1, "2": 5, "3": 0}.get(s, 1)
    i = 0
    while True:
        i += 1
        print(dim("\n  --- 第 %d 轮 ---" % i))
        r = maintain.tick(batch=20)
        print("  歌词 +%d/-%d   封面 +%d/-%d   清理 %d" % (
            r["lyric_ok"], r["lyric_miss"], r["cover_ok"], r["cover_miss"], r["cleaned"]))
        if r["done"]:
            print(ok("  已跑完全库一轮"))
            break
        if rounds and i >= rounds:
            break
        time.sleep(5)


def act_export():
    title("导出")
    print("  1) 曲库 m3u8   2) 曲库 CSV   3) 全库索引")
    s = ask("  > ").strip()
    fmt = {"1": "m3u8", "2": "csv", "3": "index"}.get(s)
    if not fmt:
        return
    try:
        from src import export, browse, config as cfg
    except Exception as e:
        print(bad("  模块加载失败: %r" % (e,)))
        return
    root = cfg.get("root") or "D:\\音乐"
    print(dim("  生成中…"))
    if fmt == "index":
        text = json.dumps(export.library_index(root, fast=True), ensure_ascii=False, indent=1)
        ext = "json"
    else:
        paths = [t["path"] for t in browse.list_tracks(root, "", limit=1000000)]
        text = export.to_m3u8(paths, root) if fmt == "m3u8" else export.to_csv(paths, root)
        ext = fmt
    out = os.path.join(root, "music3_export_%s.%s" % (time.strftime("%Y%m%d_%H%M%S"), ext))
    if export.write_file(out, text):
        print(ok("  已导出 ") + acc(out))
        print("  " + dim("%.1f KB" % (len(text.encode("utf-8")) / 1024)))
    else:
        print(bad("  写入失败"))


def act_open_dir():
    title("打开目录")
    d = load_cfg()
    root = d.get("root") or "D:\\音乐"
    targets = [
        ("音乐根目录", root),
        ("程序目录", HERE),
        ("缓存目录", os.path.join(HERE, "_cache")),
    ]
    for i, (n, p) in enumerate(targets, 1):
        ex = "" if os.path.exists(p) else dim(" (不存在)")
        print("  %d) %-10s %s%s" % (i, n, p, ex))
    s = ask("  打开第几个（回车取消）: ").strip()
    if not s.isdigit():
        return
    i = int(s) - 1
    if 0 <= i < len(targets) and os.path.exists(targets[i][1]):
        os.startfile(targets[i][1])


def act_checkenv():
    """环境自检：依赖 / 路径 / 工具 / 配置 / 端口。"""
    title("环境自检")
    fails = 0

    def row(name, good, detail=""):
        nonlocal fails
        if not good:
            fails += 1
        print("  %-14s %s %s" % (name, ok("✓") if good else bad("✗"), dim(detail)))

    # Python
    row("Python", sys.version_info >= (3, 8),
        "%d.%d.%d" % sys.version_info[:3])

    # 关键第三方库
    for mod, why in (
        ("requests", "HTTP 请求"),
        ("mutagen", "ID3 标签读写"),
        ("yt_dlp", "B站下载"),
    ):
        try:
            __import__(mod)
            row(mod, True, why)
        except ImportError:
            row(mod, False, why + " — pip install " + mod.replace("_", "-"))

    # 项目文件
    for f, why in (
        ("run.py", "统一入口"),
        ("config.json", "配置"),
        ("src/web.py", "Web 层"),
        ("src/downloader.py", "下载器"),
        ("README.md", "文档"),
    ):
        p = os.path.join(HERE, f.replace("/", os.sep))
        row(f, os.path.exists(p), why)

    # 外部工具
    cfg_d = load_cfg()
    for key in ("ffmpeg", "ffprobe"):
        p = cfg_d.get(key) or ""
        ex = os.path.exists(p) if p else False
        row(key, ex, p if p else "未配置")
    # PATH 里能不能找到
    import shutil

    for exe in ("ffmpeg", "ffprobe"):
        row(exe + "(PATH)", shutil.which(exe) is not None,
            shutil.which(exe) or "不在 PATH")

    # 音乐目录
    root = cfg_d.get("root") or ""
    has_root = bool(root) and os.path.isdir(root)
    row("音乐目录", has_root, root or "未配置")
    if has_root:
        try:
            from src import library

            cnt = library.count(root) or {}
            row("  可写", os.access(root, os.W_OK),
                "共 %d 首" % sum(int(v) for v in cnt.values()))
        except Exception:
            pass

    # 缓存目录
    cache = cfg_d.get("cache_dir") or os.path.join(HERE, "_cache")
    try:
        os.makedirs(cache, exist_ok=True)
        row("缓存目录", os.path.isdir(cache), cache)
    except Exception:
        row("缓存目录", False, "无法创建 " + cache)

    # 端口：占用=服务在跑（正常），空闲=待启动（也正常），只报告不算失败
    in_use = port_up()
    print("  %-14s %s %s" % (
        "端口 %d" % PORT,
        ok("✓"),
        (ok("服务在运行") + "  " + BASE) if in_use else dim("空闲，按 1 启动服务"),
    ))

    # 桌面快捷方式
    try:
        desk = os.path.join(os.path.expanduser("~"), "Desktop")
        lnk = os.path.join(desk, "music3 音乐工具.lnk")
        row("桌面快捷方式", os.path.exists(lnk), lnk if os.path.exists(lnk) else "未创建")
    except Exception:
        pass

    print()
    if fails:
        print("  " + warn("%d 项不通过" % fails) + dim("（不影响核心功能，按提示补齐即可）"))
    else:
        print("  " + ok("全部通过，可以正常使用"))


def act_learn():
    title("使用说明 / 学习")
    items = [
        ("快速上手", "双击桌面「music3 音乐工具」→ 1 启动 → 2 打开界面"),
        ("搜索下载", "界面「搜索」页输入「歌名 歌手」，点结果行下载"),
        ("批量下载", "界面「批量」页每行一个关键词，设并发数后开始"),
        ("曲库浏览", "「曲库」页切换分类片，网格/列表双视图，点封面播放"),
        ("播放器", "底部常驻：波形 / 歌词 / 播放列表 / 均衡器 / 变速 / 播放模式"),
        ("快捷键", "空格暂停 ←→±5秒 ↑↓音量 L歌词 E均衡 [ ]变速 N/P上下首 Esc关闭"),
        ("补歌词", "「清理」页 → 健康检查（勾读ID3）→ 看缺歌词数 → 补"),
        ("补封面", "「清理」页 → 健康检查 → 点「补封面」按钮逐首联网补"),
        ("维护守护", "「清理」页 → 维护守护 → 跑一轮，断点续传，日志落 _cache"),
        ("导出", "「清理」页底部 → m3u8 / CSV / 全库索引"),
        ("命令行", "python -X utf8 run.py --help 看全部 23 条命令"),
        ("完整文档", "README.md（39KB，含 39 条踩坑记录与实测数据）"),
    ]
    for k, v in items:
        print("  " + bold(k))
        print("    " + dim(v))
    print()
    print("  " + dim("打开 README？(y/N)"))
    if ask("  > ").strip().lower().startswith("y"):
        rd = os.path.join(HERE, "README.md")
        if os.path.exists(rd):
            os.startfile(rd)


def act_log():
    title("运行日志")
    p = os.path.join(HERE, "_cache", "maintain.log")
    if not os.path.exists(p):
        print(dim("  还没有日志（跑一次维护守护就有了）"))
        return
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        print(bad("  读取失败: %r" % (e,)))
        return
    for l in lines[-40:]:
        print("  " + l.rstrip())


def ask(prompt="  > "):
    """安全 input：stdin 耗尽/管道关闭时返回 ""，不让 traceback 糊到用户脸上。

    ask() 在 EOF 时抛 EOFError。真实场景：用户 Ctrl+Z、双击后被脚本管道调用、
    或 stdin 被父进程关掉。双击交互时不会触发，但一触发就是满屏 traceback。
    """
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return ""


# ---------- 关于 ----------
REPO_URL = "https://github.com/qingshanjiluo/music3"
AUTHOR = "最中幻想"
WECHAT = "andyloveanny"


def _open_url(url):
    try:
        if os.name == "nt":
            os.startfile(url)
        else:
            import webbrowser

            webbrowser.open(url)
    except Exception as e:
        print(bad("  打开失败: %r" % (e,)))


def _copy_clip(text):
    """复制到剪贴板（Windows 用 clip.exe，零依赖）。"""
    try:
        if os.name == "nt":
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True)
            p.communicate(text)
            if p.returncode == 0:
                print(ok("  已复制: ") + acc(text))
                return
        raise RuntimeError("clip 不可用")
    except Exception:
        print(warn("  复制失败，手动记录: ") + acc(text))


def act_about():
    """关于：作者 / 微信 / 仓库 / 求 Star。"""
    title("关于本工具")
    line("=")
    print("  " + bold("music3 · 三源音乐工具") + "    " + dim("B站 / 网易云 / QQ音乐"))
    line("=")
    print()
    print("  作者    " + bold(AUTHOR))
    print("  微信    " + acc(WECHAT))
    print("  仓库    " + acc(REPO_URL))
    print()
    line()
    print("  这个工具从第一行代码到 46 条踩坑记录都是实打实趟出来的。")
    print("  觉得有用就点个 " + ok("Star") + "，这是最直接的鼓励。")
    print("  有问题、提需求、聊实现，加微信 " + acc(WECHAT))
    line()
    print()
    print("  1) 浏览器打开仓库   2) 复制微信号   3) 复制仓库地址")
    s = ask("  > ").strip()
    if s == "1":
        _open_url(REPO_URL)
        print(ok("  已打开 ") + acc(REPO_URL))
    elif s == "2":
        _copy_clip(WECHAT)
    elif s == "3":
        _copy_clip(REPO_URL)


# ---------- 主菜单 ----------
MENU = [
    ("1", "启动 Web 服务", act_start),
    ("2", "打开 Web 界面", act_open_web),
    ("3", "停止服务", act_stop),
    ("4", "查看状态", act_status),
    ("5", "修改配置", act_config),
    ("6", "搜索与下载", act_search),
    ("7", "批量补全（歌词/封面）", act_fill),
    ("8", "库健康检查", act_health),
    ("9", "维护守护", act_maintain),
    ("e", "导出歌单/索引", act_export),
    ("d", "打开目录", act_open_dir),
    ("l", "运行日志", act_log),
    ("c", "环境自检", act_checkenv),
    ("h", "使用说明 / 学习", act_learn),
    ("a", "关于 / 求 Star", act_about),
]


def set_title(text):
    """设控制台窗口标题（中文）。

    .bat 里写 title 中文会炸：cmd 按 ANSI 码页解析 .bat 文件本身，
    chcp 只有效于控制台 I/O，管不到文件解析，中文字节被拆成命令。
    所以 .bat 只放 ASCII 标题，中文标题在这里用 Win32 API 设。
    """
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.kernel32.SetConsoleTitleW(ctypes.c_wchar_p(text))
    except Exception:
        # 兜底：ANSI 转义（Windows Terminal 支持）
        try:
            sys.stdout.write("\033]0;%s\007" % text)
            sys.stdout.flush()
        except Exception:
            pass


def main():
    set_title("music3 三源音乐工具")
    # 首次运行提示（用标记文件判断）
    flag = os.path.join(HERE, "_cache", ".launcher_seen")
    first = not os.path.exists(flag)
    try:
        os.makedirs(os.path.dirname(flag), exist_ok=True)
        with open(flag, "w", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        pass

    GROUPS = [
        ("服务", ["1", "2", "3", "4"]),
        ("设置", ["5", "c"]),
        ("干活", ["6", "7", "8", "9"]),
        ("工具", ["e", "d", "l", "h", "a"]),
    ]
    name_of = {k: n for k, n, _ in MENU}
    fn_of = {k: f for k, _n, f in MENU}

    while True:
        os.system("cls" if os.name == "nt" else "clear")
        line("=")
        print("  " + bold("music3 · 三源音乐工具") + "    " + dim("B站 / 网易云 / QQ音乐"))
        line("=")
        up, st = service_status()
        if up:
            info = ""
            if st:
                info = "  " + dim(" / ".join("%s %d" % (k, v) for k, v in st.items()))
            print("  服务: " + ok("● 运行中") + "  " + acc(BASE) + info)
        else:
            print("  服务: " + dim("○ 未启动") + "  " + dim("（按 1 启动）"))
        line()
        for gname, keys in GROUPS:
            print("  " + dim("[" + gname + "]"))
            row = []
            for k in keys:
                row.append("%s) %s" % (acc(k.rjust(2)), name_of[k]))
            # 两个一行（按显示宽度对齐）
            while row:
                a = row.pop(0)
                if row:
                    b = row.pop(0)
                    print("   " + dpad(a, 30) + b)
                else:
                    print("   " + a)
        line()
        print("  " + dim("q) 退出"))
        if first:
            print()
            print("  " + warn("首次使用建议先按 c 做环境自检，按 h 看说明"))
            first = False
        print()
        s = ask("  选择 > ").strip().lower()
        if s in ("q", "quit", "exit", ""):
            break
        fn = fn_of.get(s)
        if not fn:
            print(bad("  无此项"))
            time.sleep(0.8)
            continue
        try:
            fn()
        except KeyboardInterrupt:
            print(warn("\n  已中断"))
        except Exception as e:
            print(bad("\n  出错: %r" % (e,)))
        print()
        ask(dim("  按回车返回菜单…"))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
