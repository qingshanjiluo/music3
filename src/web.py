# -*- coding: utf-8 -*-
"""music3 Web 服务：可视化界面 + JSON API（供 AI/脚本调用）。

启动: python -X utf8 -m src.web
默认: http://127.0.0.1:8420

API:
  GET  /api/search?q=晴天&sources=qq,netease&limit=15
  GET  /api/get?q=晴天 周杰伦&n=1&sources=qq
  GET  /api/stat
  POST /api/batch   body: {"keywords": ["a","b"], "n": 1}
"""
from __future__ import annotations

import json
import os
import sys
import threading
import time

if __package__ in (None, ""):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    __package__ = "src"

import logging

logging.getLogger("musicdl").setLevel(logging.WARNING)

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse, quote as _urlquote

from src import router, library, downloader
from src.models import norm

HOST = "127.0.0.1"
PORT = 8420

# 取链缓存命中计数: 落盘 _cache/pv_hits.json(累计, 重启不归 0), 节流 1s 写盘
import os as _os
_PV_HITS_FILE = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "_cache", "pv_hits.json")
_PV_HITS = 0
_PV_HITS_DIRTY = False
_PV_HITS_LAST_FLUSH = 0.0
_PV_CALLS = 0   # 累计取链调用次数(命中率分母, 落盘 _cache/pv_calls.json)
_PV_CALLS_FILE = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "_cache", "pv_calls.json")
_PV_CALLS_DIRTY = False
_PV_CALLS_LAST_FLUSH = 0.0


def _pv_load_calls():
    global _PV_CALLS
    try:
        with open(_PV_CALLS_FILE, "r", encoding="utf-8") as _f:
            _PV_CALLS = int(_json_load(_f) or 0)
    except Exception:
        _PV_CALLS = 0


def _pv_on_call():
    global _PV_CALLS, _PV_CALLS_DIRTY, _PV_CALLS_LAST_FLUSH
    _PV_CALLS += 1
    _PV_CALLS_DIRTY = True
    import time as _t
    if _t.time() - _PV_CALLS_LAST_FLUSH < 1.0:
        return
    try:
        _os.makedirs(_os.path.dirname(_PV_CALLS_FILE), exist_ok=True)
        with open(_PV_CALLS_FILE, "w", encoding="utf-8") as _f:
            _f.write(str(_PV_CALLS))
        _PV_CALLS_DIRTY = False
        _PV_CALLS_LAST_FLUSH = _t.time()
    except Exception:
        pass


_pv_load_calls()


def _pv_flush_calls():
    """读时落一次 calls 脏(与 hits 对称)。"""
    global _PV_CALLS_DIRTY, _PV_CALLS_LAST_FLUSH
    import time as _t
    if not _PV_CALLS_DIRTY:
        return
    try:
        _os.makedirs(_os.path.dirname(_PV_CALLS_FILE), exist_ok=True)
        with open(_PV_CALLS_FILE, "w", encoding="utf-8") as _f:
            _f.write(str(_PV_CALLS))
        _PV_CALLS_DIRTY = False
        _PV_CALLS_LAST_FLUSH = _t.time()
    except Exception:
        pass


def _pv_load_hits():
    """启动时读累计命中。"""
    global _PV_HITS
    try:
        with open(_PV_HITS_FILE, "r", encoding="utf-8") as _f:
            _PV_HITS = int(_json_load(_f) or 0)
    except Exception:
        _PV_HITS = 0


def _pv_flush_hits():
    """节流写盘(距上次 >=1s 才落, 免高频 IO)。"""
    global _PV_HITS, _PV_HITS_DIRTY, _PV_HITS_LAST_FLUSH
    import time as _t
    if not _PV_HITS_DIRTY:
        return
    if _t.time() - _PV_HITS_LAST_FLUSH < 1.0:
        return
    try:
        _os.makedirs(_os.path.dirname(_PV_HITS_FILE), exist_ok=True)
        with open(_PV_HITS_FILE, "w", encoding="utf-8") as _f:
            _f.write(str(_PV_HITS))
        _PV_HITS_DIRTY = False
        _PV_HITS_LAST_FLUSH = _t.time()
    except Exception:
        pass


def _pv_on_hit():
    """命中: 内存 +1, 标脏(写盘由节流器/关键路径触发)。"""
    global _PV_HITS, _PV_HITS_DIRTY
    _PV_HITS += 1
    _PV_HITS_DIRTY = True


def _json_load(f):
    import json as _j
    return _j.load(f)


def _pv_reset_hits():
    """清缓存: 删 pv_hits.json + pv_calls.json + 内存归 0。"""
    global _PV_HITS, _PV_HITS_DIRTY, _PV_CALLS, _PV_CALLS_DIRTY
    try:
        if os.path.exists(_PV_HITS_FILE):
            os.remove(_PV_HITS_FILE)
    except Exception:
        pass
    try:
        if os.path.exists(_PV_CALLS_FILE):
            os.remove(_PV_CALLS_FILE)
    except Exception:
        pass
    _PV_HITS = 0
    _PV_HITS_DIRTY = False
    _PV_CALLS = 0
    _PV_CALLS_DIRTY = False


_pv_load_hits()

PAGE = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0e1014">
<link rel="manifest" href="/manifest.json">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="/icon.svg">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>music3 · 三源音乐</title>
<style>
:root{
  color-scheme:light;   /* 系统深色模式下强制原生控件(checkbox/select/scrollbar)走浅色, 免与纸白皮撕裂 */
  /* 唱片内页（liner notes）：纸白底 · 墨黑字 · 朱砂红唱片标签 */
  --bg:#f7f5f0; --panel:#ffffff; --panel2:#efece5; --line:#e2ddd3;
  --fg:#1c1a17; --dim:#77706a; --acc:#c4381f; --acc2:#2f4f44;
  --ok:#2f7d55; --warn:#96650a; --bad:#a3261a; --radius:3px;

  --glass:rgba(247,245,240,.94);
  /* 版心四档（prose 65ch / grid 960 / wide 1180 / full 100%） */
  --content-prose:65ch; --content-grid:960px; --content-wide:1180px;
  /* 4px 基间距阶梯 + 栅格 gap（12 栏可除 2/3/4/6，破格留余量） */
  --space-1:4px; --space-2:8px; --space-3:12px; --space-4:16px; --space-6:24px;
  --gap:clamp(8px, 1.4vw, 16px); --gap-grid:clamp(8px, 1vw, 12px);
  --sect:clamp(1.5rem, 3vw, 2.5rem);
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{margin:0;padding:0}
/* 滚动条槽：弹层锁 body 滚动时占位不塌，消横向跳动 */
html{scrollbar-gutter:stable}
body.ov{overflow:hidden}
body::before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:-1;
  background-image:url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="140" height="140"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2"/></filter><rect width="140" height="140" filter="url(%23n)" opacity="0.05"/></svg>');
}
body{
  background:var(--bg);color:var(--fg);
  font:14px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  padding-bottom:calc(84px + env(safe-area-inset-bottom));
}
.wrap{max-width:var(--content-wide);margin:0 auto;padding:var(--space-4) var(--space-4) 40px}
/* 焦点可见（键盘可达） */
a:focus-visible,button:focus-visible,input:focus-visible,[tabindex]:focus-visible{
  outline:2px solid var(--acc);outline-offset:2px;
}
@media (prefers-reduced-motion:reduce){
  *{animation-duration:.01ms !important;transition-duration:.01ms !important}
}

/* 顶栏 */
header{display:flex;align-items:center;gap:10px;padding:6px 0 14px;
  position:relative}
header::after{content:"";position:absolute;left:0;right:0;bottom:0;height:1px;
  background:var(--line)}
.hd h1{letter-spacing:-.2px;font-weight:800}
.logo{
  width:34px;height:34px;border-radius:3px;flex:0 0 auto;
  background:var(--acc);
  display:flex;align-items:center;justify-content:center;
  font-size:17px;font-weight:800;color:#fff;
}
.hd h1{font-size:16.5px;margin:0}
.hd .sub{color:var(--dim);font-size:11.5px;margin-top:1px}

/* 竖轨导航：桌面贴左侧，手机横向可滚（不换行） */
.tabs{
  display:flex;gap:3px;background:var(--panel);padding:4px;border-radius:11px;
  margin-bottom:14px;flex-wrap:nowrap;overflow-x:auto;scrollbar-width:none;
  scroll-snap-type:x mandatory;-webkit-overflow-scrolling:touch;
  position:sticky;top:0;z-index:90;box-shadow:0 1px 0 var(--line);
}
.tabs::-webkit-scrollbar{display:none}
.tab{
  flex:1;text-align:center;padding:11px 8px;border-radius:8px;cursor:pointer;
  color:var(--dim);font-size:13px;transition:.15s;user-select:none;white-space:nowrap;
  scroll-snap-align:center;min-height:44px;box-sizing:border-box;
}
.tab.on{background:var(--fg);color:var(--bg);font-weight:700}
.pane{display:none}.pane.on{display:block}

/* 消抖动：消息条/内容区常占位，刷新不顶动页面 */
.msg{min-height:20px}
.bar{display:flex;gap:var(--space-2);flex-wrap:wrap;align-items:center;margin-bottom:var(--space-3)}
input[type=text],input[type=number]{
  flex:1;min-width:170px;background:var(--panel);border:1px solid var(--line);
  color:var(--fg);padding:11px 13px;border-radius:10px;font-size:14px;outline:none;transition:.15s;
}
input[type=text]:focus{border-color:var(--acc);background:var(--panel2)}
input::placeholder{color:#a39c92}
button{transition:transform .1s ease, background .15s, border-color .15s, color .15s;
  background:var(--acc);border:0;color:#ffffff;font-weight:600;
  padding:11px 17px;border-radius:10px;cursor:pointer;font-size:13.5px;transition:.15s;
  flex:0 0 auto;
}
button:hover:not(:disabled){filter:brightness(1.1)}
button:active:not(:disabled){transform:scale(.97)}
button:disabled{opacity:.4;cursor:default}
button.ghost{background:var(--panel);color:var(--fg);border:1px solid var(--line);font-weight:500}
button.ghost:hover:not(:disabled){border-color:var(--acc);color:var(--acc)}
button.danger{background:#f7e8e6;color:#a3261a;border:1px solid #e8c9c4;font-weight:500}
button.sm{padding:6px 11px;font-size:12px;border-radius:8px}
label.chk{color:var(--dim);font-size:12px;display:flex;gap:5px;align-items:center;cursor:pointer;user-select:none}
input[type=checkbox],input[type=radio]{accent-color:var(--acc);cursor:pointer}

/* 提示 */
.msg{
  margin:10px 0;color:var(--dim);font-size:12px;white-space:pre-wrap;
  font-family:ui-monospace,Consolas,monospace;max-height:150px;overflow:auto;
  padding:9px 11px;background:var(--panel);border-radius:9px;border-left:2px solid var(--line);
}
.msg:empty{display:none}
.msg.ok{border-left-color:var(--ok);color:#1f6b46}
.msg.bad{border-left-color:var(--bad);color:#a3261a}

/* 表格 */
.tablewrap{background:var(--panel);border-radius:var(--radius);overflow:hidden;min-height:44px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line)}
th{color:var(--dim);font-weight:500;font-size:11.5px;background:var(--panel2);position:sticky;top:0;z-index:1}
tr:last-child td{border-bottom:0}
tbody tr:hover td{background:#efece5}
tbody tr.playing td{background:#fbe9e4}
.sc{font-variant-numeric:tabular-nums;font-weight:700;font-size:12.5px}
.sc.hi{color:var(--ok)}.sc.mid{color:var(--warn)}.sc.lo{color:#a39c92}
.src{font-size:10.5px;padding:2px 7px;border-radius:99px;background:#eae6dd;color:var(--dim);white-space:nowrap}
.src.qq{color:#1f6b46;background:#e6f2ec}
.src.netease{color:#b03030;background:#f7e8e6}
.src.bilibili{color:#1a5f9e;background:#e6eef5}
.mono{font-family:ui-monospace,Consolas,monospace;font-size:11.5px;color:var(--dim);word-break:break-all}
.n{color:var(--dim);font-size:11px}

/* 分类片 */
.chips{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:12px}
/* 面包屑: 多级可点回跳(结构硬规则4 往返保留) */
.crumbs{display:flex;flex-wrap:wrap;align-items:center;gap:3px;margin:-4px 0 10px;font-size:12.5px;min-height:20px}
.crumbs .cb{color:var(--dim);text-decoration:none;cursor:pointer;padding:2px 4px;border-radius:3px}
.crumbs .cb:hover{color:var(--acc);background:rgba(196,56,31,.07)}
.crumbs .cb.cur{color:var(--fg);font-weight:700;cursor:default}
.crumbs .cs{color:var(--dim);opacity:.6}
/* 页头右侧按钮 */
.hdr-right{margin-left:auto;display:flex;gap:7px;align-items:center;flex:0 0 auto}
/* 关于弹窗 */
.modal{
  position:fixed;inset:0;z-index:300;display:none;
  background:rgba(28,26,23,.34);backdrop-filter:blur(6px);
  align-items:center;justify-content:center;padding:20px;
}
.modal.on{display:flex}
.mbox{
  background:var(--panel);
  border:1px solid var(--line);border-radius:6px;
  width:100%;max-width:440px;max-height:86vh;overflow-y:auto;
  padding:26px 24px 20px;position:relative;
  box-shadow:0 24px 64px rgba(28,26,23,.34);
  animation:mIn .18s ease;
}
@keyframes mIn{from{transform:translateY(10px) scale(.98);opacity:0}to{transform:none;opacity:1}}
.mclose{
  position:absolute;top:12px;right:12px;width:28px;height:28px;
  border-radius:8px;border:0;background:#ffffff;color:var(--dim);
  cursor:pointer;font-size:15px;line-height:1;
}
.mclose:hover{background:#efece5;color:var(--fg)}
.mlogo{
  width:52px;height:52px;border-radius:4px;margin:0 auto 14px;
  background:var(--acc);
  display:flex;align-items:center;justify-content:center;
  font-size:26px;color:#fff;font-weight:800;
}
.mtitle{text-align:center;font-size:18px;font-weight:700;margin-bottom:4px}
.mver{text-align:center;font-size:11.5px;color:var(--dim);margin-bottom:18px}
.mrow{
  display:flex;align-items:center;gap:10px;padding:10px 12px;
  background:#f7f5f0;border:1px solid var(--line);border-radius:10px;
  margin-bottom:8px;
}
.mrow .mk{font-size:11.5px;color:var(--dim);width:52px;flex:0 0 auto}
.mrow .mv{font-size:13px;flex:1;min-width:0;word-break:break-all}
.mrow .mv b{color:var(--acc);font-weight:600}
.copybtn{
  border:0;background:#ffffff;color:var(--dim);border-radius:6px;
  padding:4px 9px;font-size:11px;cursor:pointer;flex:0 0 auto;
}
.copybtn:hover{background:#efece5;color:var(--fg)}
.mstar{
  display:block;text-align:center;margin:16px 0 10px;padding:12px;
  background:linear-gradient(135deg,rgba(240,194,92,.16),rgba(217,164,65,.08));
  border:1px solid rgba(217,164,65,.42);border-radius:11px;
  color:#f0c25c;text-decoration:none;font-size:13.5px;font-weight:600;
  transition:.15s;
}
.mstar:hover{background:linear-gradient(135deg,rgba(240,194,92,.26),rgba(217,164,65,.14));transform:translateY(-1px)}
.mnote{
  font-size:11.5px;color:var(--dim);line-height:1.8;text-align:center;
  margin-top:12px;padding-top:14px;border-top:1px solid var(--line);
}
.mactions{display:flex;gap:8px;margin-top:14px}
.mactions button{flex:1}
.chip{
  padding:7px 14px;background:var(--panel);border:1px solid var(--line);
  border-radius:99px;cursor:pointer;font-size:12.5px;transition:.15s;user-select:none;
  line-height:1.35;
}
.chip:hover{border-color:var(--acc)}
.chip.on{background:var(--fg);border-color:var(--fg);color:var(--bg);font-weight:700}
/* 视图切换 */
.vtog{display:flex;gap:2px;background:var(--panel);padding:2px;border-radius:8px;margin-left:auto}
.vtog span{padding:5px 11px;font-size:12px;border-radius:6px;cursor:pointer;color:var(--dim)}
.vtog span.on{background:var(--panel2);color:var(--fg);font-weight:600}
/* 列表视图 */
.listview{background:var(--panel);border-radius:var(--radius);overflow:hidden}
.lrow{display:flex;align-items:center;gap:10px;padding:9px 12px;cursor:pointer;border-bottom:1px solid var(--line)}
.lrow:hover{background:#efece5}
.lrow.on{background:#fbe9e4}
.lrow:last-child{border-bottom:0}
.lcov{
  width:38px;height:38px;border-radius:7px;flex:0 0 auto;overflow:hidden;
  background:linear-gradient(135deg,#eae6dd,#f4f2ec);
  display:flex;align-items:center;justify-content:center;font-size:15px;
}
.lcov img{width:100%;height:100%;object-fit:cover}
.ltxt{flex:1;min-width:0}
.lt1{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lt2{font-size:11.5px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lsz{font-size:11px;color:var(--dim);flex:0 0 auto}
/* 统计卡片 */
.statgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:var(--gap-grid)}
/* 维护页 7 卡: 两行 4+3(桌面), 窄屏 auto-fit 自动折 */
.mtgrid{grid-template-columns:repeat(4,1fr)}
.mtgrid .statcard:nth-child(5){grid-column:1}
.mtgrid .statcard:nth-child(9){grid-column:1}
/* 趋势 sparkline 容器: 4 卡统一 100% 宽 + 等高 22px + 底部对齐(挂趋势卡时 4 折线一条线对齐) */
.mtspark{display:block;width:100%;height:22px;margin-top:6px;overflow:hidden;position:relative}
.mtspark svg{display:block;width:100%;height:22px}
@media(max-width:640px){.mtgrid{grid-template-columns:repeat(2,1fr)}.mtgrid .statcard:nth-child(5),.mtgrid .statcard:nth-child(9){grid-column:auto}}
.statcard{
  background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:14px 16px;
}
/* 维护卡片 hover 微交互: 抬升 + 阴影 + 末点圆点放大(#mtresult 作用域, 不影响曲库/批量卡片) */
#mtresult .statcard{transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease}
#mtresult .statcard:hover{transform:translateY(-2px);box-shadow:0 6px 18px -8px rgba(0,0,0,.25);border-color:var(--acc)}
#mtresult .statcard:hover .mtspark .mtspark-hover{transition:width .12s ease,height .12s ease}
.statcard .k{font-size:11px;color:var(--dim);margin-bottom:6px}
.statcard .v{font-size:22px;font-weight:700;font-variant-numeric:tabular-nums;
  font-weight:800;letter-spacing:-.5px;color:var(--fg)}
.statcard .u{font-size:11px;color:var(--dim);margin-left:2px}

/* 播放器 */
/* 播放器：常驻占位（idle 也占同高，首播零位移） */
.player{
  position:fixed;left:0;right:0;bottom:0;z-index:100;
  background:var(--glass);backdrop-filter:blur(20px) saturate(1.2);
  border-top:1px solid rgba(196,56,31,.22);
  box-shadow:0 -8px 32px rgba(0,0,0,.45);
  padding:9px 14px calc(9px + env(safe-area-inset-bottom));
  display:flex;gap:12px;align-items:center;overflow:hidden;
}
.player:not(.on){opacity:.72}
.player.on{border-top-color:rgba(196,56,31,.34)}
.player.on.pulsing{animation:edgeBreath 2.6s ease-in-out infinite}
@keyframes edgeBreath{0%,100%{border-top-color:rgba(196,56,31,.45)}
  50%{border-top-color:rgba(196,56,31,.85)}}
@media (prefers-reduced-motion:reduce){.player.on.pulsing{animation:none}}
.player:not(.on) .pbtn{pointer-events:none;opacity:.55}
.pcov{
  width:46px;height:46px;border-radius:9px;flex:0 0 auto;
  background:linear-gradient(135deg,#eae6dd,#f4f2ec);
  display:flex;align-items:center;justify-content:center;
  font-size:19px;overflow:hidden;
}
.pcov img{width:100%;height:100%;object-fit:cover}
.pinfo{flex:1;min-width:0}
.ptitle{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.partist{font-size:11.5px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.pbtns{display:flex;gap:7px;flex:0 0 auto}
.pbtn:active{transform:scale(.92)}
.pbtn{
  width:38px;height:38px;border-radius:50%;background:var(--panel2);
  border:1px solid var(--line);color:var(--fg);cursor:pointer;
  display:flex;align-items:center;justify-content:center;font-size:15px;
}
.pbtn.main{background:var(--acc);color:#ffffff;border:0;width:44px;height:44px;font-size:17px}
.pbar{
  position:absolute;left:0;right:0;top:-1px;height:2px;background:#e2ddd3;cursor:pointer;
}
.pbar{height:2px}
.pbar i{display:block;height:100%;width:0;background:var(--acc);transition:width .1s linear}
.playicon,.pbtn svg{width:15px;height:15px;display:block;pointer-events:none}
.pbtn.main svg{width:17px;height:17px}
/* 歌词手动取词候选列表 */
.lycands{max-height:44vh;overflow-y:auto;border-top:1px solid var(--line);background:#ffffff}
.lycands:empty{display:none}
.lycand{
  display:flex;align-items:center;gap:10px;padding:9px 14px;cursor:pointer;
  border-bottom:1px solid var(--line);transition:background .12s;
}
.lycand:hover{background:#efece5}
.lcsrc{
  font-size:10.5px;padding:2px 7px;border-radius:5px;flex:0 0 auto;
  background:#232a38;color:var(--acc);
}
.lct{flex:1;min-width:0;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lcn{font-size:11px;color:var(--dim);margin-top:1px}
.lyok{padding:14px;text-align:center;color:var(--ok);font-size:12.5px}
/* 大图灯箱 */
.lightbox{
  position:fixed;inset:0;z-index:400;background:rgba(6,7,10,.94);
  display:none;align-items:center;justify-content:center;flex-direction:column;
  padding:30px;cursor:zoom-out;
}
.lightbox.on{display:flex}
.lightbox img{max-width:min(92vw,900px);max-height:82vh;object-fit:contain;
  border-radius:12px;box-shadow:0 20px 60px #0009}
.lbclose{position:absolute;top:16px;right:18px;width:38px;height:38px;border-radius:50%;
  border:0;background:#ffffff1a;color:#fff;font-size:18px;cursor:pointer}
.lbclose:hover{background:#ffffff33}
.lbcap{margin-top:14px;color:var(--dim);font-size:13px;text-align:center;max-width:70vw}
/* 收藏列表行 */
.favrow{display:flex;align-items:center;gap:10px;padding:11px 14px;
  background:var(--panel);border:1px solid var(--line);border-radius:10px;margin-bottom:8px}
.favrow .ftxt{flex:1;min-width:0}
.favrow .ft1{font-size:13.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.favrow .ft2{font-size:11.5px;color:var(--dim);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.favrow .fops{display:flex;gap:6px;flex:0 0 auto}
/* 卡片删改按钮 */
.cardops{position:absolute;top:6px;right:6px;display:flex;gap:4px;
  opacity:0;transition:opacity .15s}
.card:hover .cardops{opacity:1}
.cop{width:26px;height:26px;border-radius:7px;border:1px solid var(--line);
  background:rgba(255,255,255,.93);color:var(--dim);font-size:13px;cursor:pointer;
  display:flex;align-items:center;justify-content:center;padding:0}
.cop:hover{background:#efece5;color:var(--fg);border-color:rgba(28,26,23,.18)}
/* 触屏(无hover设备): 揭示按钮常驻可见 + 触控44px红线(hover-only在触屏不可达=可交互硬伤) */
@media (hover:none){
  .cardops{opacity:1}
  .cop{width:44px;height:44px;font-size:15px;border-radius:4px}
  .rowops button{min-width:44px;min-height:44px;padding:8px;font-size:14px}
  .lrow,.plitem{min-height:48px}
}
.cop[data-act="del"]:hover{color:var(--bad)}
.card{position:relative}
/* 加载骨架：曲库/表格加载时显示，避免空白跳动 */
.sk{background:linear-gradient(90deg,#eeebe4 25%,#faf9f5 50%,#eeebe4 75%);
  background-size:200% 100%;animation:skSlide 1.2s linear infinite;border-radius:9px}
@keyframes skSlide{0%{background-position:200% 0}100%{background-position:-200% 0}}
@media (prefers-reduced-motion:reduce){.sk{animation:none;background:#eeebe4}}
.skg{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:var(--gap-grid)}
.skc{height:170px;display:flex;flex-direction:column}
.skc .a{height:148px}
.skc .b{height:13px;margin-top:8px}
.skc .c{height:11px;margin-top:5px;width:70%}
.skrow{height:38px;margin-bottom:6px}
/* 空状态 */
.empty{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  padding:52px 20px;color:var(--dim);text-align:center;gap:8px;
}
.empty .eic{font-size:30px;opacity:.5;letter-spacing:4px}
.empty .et{font-size:14px;color:var(--fg)}
.empty .es{font-size:12.5px;line-height:1.7;max-width:420px}
.empty .eh{font-size:11.5px;color:#9a938a;margin-top:4px}
.empty .eact{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;justify-content:center}
/* 搜索表微交互 */
#tb tr{transition:background .12s, box-shadow .12s}
#tb tr:hover{background:#efece5;box-shadow:inset 3px 0 0 var(--acc)}
#tb tr:hover .sc{transform:scale(1.12);display:inline-block;transition:transform .12s}
/* 搜索表选中态 */
#tb tr.picked{background:rgba(196,56,31,.08)}
#tb tr.picked td{border-color:rgba(196,56,31,.3)!important}
/* 预听浮窗 */
.pvbox{display:flex;align-items:center;gap:8px;margin-top:10px}
.pvbox audio{flex:1;height:38px}
/* 波形层：铺在播放器背景，不挡交互 */
.pwave{
  position:absolute;left:0;right:0;bottom:0;width:100%;height:44px;
  opacity:.45;pointer-events:none;display:block;
}
.player{overflow:hidden}
/* 搜索结果分组标签 */
.gtag{
  display:inline-block;font-size:10px;line-height:1;padding:3px 5px;margin-right:6px;
  border-radius:4px;vertical-align:1.5px;border:1px solid var(--line);
}
.g-song{color:var(--acc);border-color:rgba(196,56,31,.45);background:rgba(196,56,31,.1)}
.g-artist{color:#1f6b5e;border-color:rgba(31,107,94,.4);background:rgba(31,107,94,.09)}
.g-mv{color:#6b3fa0;border-color:rgba(107,63,160,.4);background:rgba(107,63,160,.10)}
/* 设置弹窗 */
.setrow{
  display:flex;align-items:center;gap:10px;padding:11px 12px;
  background:#f7f5f0;border:1px solid var(--line);border-radius:10px;margin-bottom:8px;
}
.setrow .k{font-size:12.5px;width:86px;flex:0 0 auto;color:var(--fg)}
.setrow .h{font-size:11px;color:var(--dim);margin-top:3px;line-height:1.5}
.setrow select,.setrow input[type=text]{
  flex:1;min-width:0;background:var(--panel);border:1px solid var(--line);color:var(--fg);
  padding:8px 10px;border-radius:8px;font-size:13px;outline:none;
}
.setrow select:focus,.setrow input:focus{border-color:var(--acc)}
.creditbox{
  display:flex;align-items:center;gap:10px;padding:14px;border-radius:10px;
  background:rgba(196,56,31,.06);
  border:1px solid rgba(196,56,31,.25);margin-bottom:8px;
}
.creditbox .cv{font-size:22px;font-weight:700;color:var(--acc)}
/* 播放列表抽屉 */
.plist{
  position:fixed;right:0;top:0;bottom:0;width:340px;max-width:88vw;z-index:200;
  background:#fbfaf7;backdrop-filter:blur(16px);
  border-left:1px solid var(--line);
  transform:translateX(100%);transition:transform .22s ease;
  display:flex;flex-direction:column;
}
.plist.on{transform:translateX(0)}
.plhead{
  display:flex;align-items:center;gap:8px;padding:14px 14px 10px;
  border-bottom:1px solid var(--line);
}
.plhead b{font-size:14px;flex:1}
.plbody{flex:1;overflow-y:auto;padding:6px 0}
.plitem{
  display:flex;align-items:center;gap:8px;padding:9px 12px;cursor:pointer;
  border-left:3px solid transparent;transition:.12s;position:relative;
}
.plitem:hover{background:#efece5}
.plitem.on{background:#fbe9e4;border-left-color:var(--acc)}
.plitem.drag{opacity:.4}
.plitem.over{border-top:2px solid var(--acc)}
.plitem .idx{width:22px;color:var(--dim);font-size:11px;text-align:right;flex:0 0 auto}
.plitem .txt{flex:1;min-width:0}
.plitem .t1{font-size:12.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.plitem .t2{font-size:11px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.plitem .del{color:var(--dim);font-size:14px;padding:0 4px;flex:0 0 auto}
.plitem .del:hover{color:var(--bad)}
.plmask{
  position:fixed;inset:0;background:rgba(28,26,23,.38);z-index:199;display:none;
}
.plmask.on{display:block}
@media (max-width:640px){
  .plist{width:100%;max-width:100%}
}
/* 歌词面板 */
.lyrics{
  position:fixed;inset:0;z-index:210;display:none;
  background:#f7f5f0;backdrop-filter:blur(20px);
}
.lyrics.on{display:flex;flex-direction:column}
.lyhead{
  display:flex;align-items:center;gap:10px;padding:14px 16px;
  border-bottom:1px solid var(--line);
}
.lyhead b{flex:1;font-size:14px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.lybody{
  flex:1;overflow-y:auto;padding:38vh 20px;
  scroll-behavior:smooth;text-align:center;
}
.lyline{
  font-size:16px;line-height:2.4;color:#a39c92;transition:.22s;
  padding:3px 0;cursor:pointer;border-radius:6px;
}
.lyline:hover{color:var(--dim)}
.lyline.cur{color:var(--fg);font-weight:600;font-size:18px;transform:scale(1.03)}
.lyline.near{color:#6f6862}
.lyempty{color:var(--dim);text-align:center;padding-top:20vh;font-size:13px}
/* 快捷键提示 */
.kbd{
  display:inline-block;padding:1px 6px;background:#ffffff;border:1px solid var(--line);
  border-radius:4px;font-size:10.5px;font-family:ui-monospace,monospace;color:var(--dim);
}
/* 音量条 */
.pvol{
  width:0;overflow:hidden;transition:width .18s,opacity .18s;opacity:0;
  display:flex;align-items:center;gap:6px;flex:0 0 auto;
}
.player:hover .pvol,.pvol.on{width:92px;opacity:1}
.pvol input{width:74px;accent-color:var(--acc);cursor:pointer}
/* 均衡器面板 */
.eqpanel{
  position:fixed;right:0;top:0;bottom:0;width:400px;max-width:94vw;z-index:205;
  background:#fbfaf7;backdrop-filter:blur(16px);
  border-left:1px solid var(--line);transform:translateX(100%);
  transition:transform .22s ease;display:flex;flex-direction:column;
}
.eqpanel.on{transform:translateX(0)}
.eqhead{display:flex;align-items:center;gap:8px;padding:14px;border-bottom:1px solid var(--line)}
.eqhead b{flex:1;font-size:14px}
.eqbody{flex:1;overflow-y:auto;padding:16px}
.eqpresets{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:16px}
.eqpresets span{
  padding:6px 13px;background:var(--panel);border:1px solid var(--line);
  border-radius:99px;cursor:pointer;font-size:12px;transition:.15s;
}
.eqpresets span:hover{border-color:var(--acc);color:var(--acc)}
.eqsliders{display:flex;gap:6px;justify-content:space-between;align-items:flex-end;height:190px}
.eqcol{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px}
.eqslider{
  -webkit-appearance:none;writing-mode:vertical-lr;direction:rtl;
  width:26px;height:150px;background:#ffffff;border-radius:99px;
  accent-color:var(--acc);cursor:ns-resize;outline:none;
}
.eqlabels{display:flex;gap:6px;justify-content:space-between;margin-top:10px;font-size:10px;color:var(--dim);text-align:center}
.eqlabels span{flex:1}
.eqlabels b{color:var(--acc);font-weight:600}

/* 进度卡 */
.jobcard{
  background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:12px 14px;margin-bottom:10px;
}
.jobhead{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:8px}
.jobtitle{font-size:13px;font-weight:600}
.pbar2{height:6px;background:#ffffff;border-radius:99px;overflow:hidden}
.pbar2 i{display:block;height:100%;width:0;background:var(--acc);transition:width .25s}
.jobmeta{display:flex;gap:12px;margin-top:7px;font-size:11.5px;color:var(--dim)}
.jobmeta b{color:var(--fg);font-weight:600}
.joblog{
  margin-top:8px;max-height:150px;overflow:auto;font-family:ui-monospace,Consolas,monospace;
  font-size:11px;color:var(--dim);background:#f4f2ec;padding:8px 10px;border-radius:8px;
  white-space:pre-wrap;line-height:1.5;
}

/* 网格卡（曲库） */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(148px,1fr));gap:var(--gap-grid);min-height:120px}
.card{
  background:var(--panel);border-radius:var(--radius);overflow:hidden;
  cursor:pointer;transition:.15s;border:1px solid transparent;
}
.card:hover{border-color:var(--fg)}
.card.on{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc)}
.cardcov{
  aspect-ratio:1;background:linear-gradient(135deg,#eae6dd,#f4f2ec);
  display:flex;align-items:center;justify-content:center;font-size:30px;
}
.cardcov img{width:100%;height:100%;object-fit:cover}
.cardbody{padding:8px 9px 10px}
.cardtitle{font-size:12.5px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.cardartist{font-size:11px;color:var(--dim);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-top:1px}

.rowops{display:flex;gap:5px;justify-content:flex-start}
.rowops button{min-width:30px;padding:6px 7px;font-size:12.5px;line-height:1}
/* 更多控制(窄屏): 桌面隐藏, ≤640 反转 */
.pmore,.pmorebox{display:none}
@media (max-width:640px){
  /* 收纳: 次要按钮隐藏, 只留 上/播/下 + ⋯ */
  #peq,#plyr,#plopen,#prate,#pmode,#pclose,.pvol{display:none !important}
  .pmore{display:flex !important}
  .pbtns{position:relative;flex:0 0 auto}
  .pmorebox{
    display:none;position:absolute;right:0;bottom:46px;
    background:var(--panel);border:1px solid var(--line);border-radius:6px;
    padding:6px;flex-direction:column;gap:5px;z-index:150;
    box-shadow:0 12px 32px rgba(28,26,23,.2);min-width:118px;
  }
  .pmorebox.on{display:flex}
  .pmorebox button{width:100%;text-align:left}
  .pcov{width:40px;height:40px}
  .ptitle{font-size:12.5px}
}
/* 健康分 hero(破格1处 · 范式15超大字): 全库核心指标单独立一面 */
.healthhero{
  background:var(--panel);border:1px solid var(--line);border-radius:3px;
  padding:26px 28px 22px;margin-bottom:14px;position:relative;overflow:hidden;
}
.healthhero::after{
  content:"";position:absolute;left:0;top:0;bottom:0;width:5px;background:var(--dim);
}
.healthhero.hero-ok::after{background:var(--ok)}
.healthhero.hero-mid::after{background:var(--warn)}
.healthhero.hero-bad::after{background:var(--bad)}
.healthhero .hk{font-size:12px;color:var(--dim);letter-spacing:.5px}
.healthhero .hv{line-height:1;margin:8px 0 6px;display:flex;align-items:baseline;gap:8px}
.healthhero .hv b{
  font-size:clamp(3.2rem,7vw,5.5rem);font-weight:800;letter-spacing:-.04em;
  font-variant-numeric:tabular-nums;color:var(--fg);
}
.healthhero.hero-ok .hv b{color:var(--ok)}
.healthhero.hero-mid .hv b{color:var(--warn)}
.healthhero.hero-bad .hv b{color:var(--bad)}
.healthhero .hden{font-size:1.3rem;color:var(--dim);font-weight:600}
.healthhero .hmeta{font-size:12px;color:var(--dim)}
/* 移动端 */
@media (max-width:640px){
  .wrap{padding:12px 10px 30px}
  .hd h1{font-size:15px}
  .tab{font-size:12px;padding:8px 4px}
  input[type=text]{min-width:120px;padding:10px 11px;font-size:13.5px}
  button{padding:10px 13px;font-size:13px}
  th:nth-child(3),td:nth-child(3){display:none}
  .grid{grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px}
  .pcov{width:40px;height:40px}
  .ptitle{font-size:12px}
}
@keyframes spin{ to{ transform:rotate(360deg);} }
</style></head><body>
<div class="wrap">
<header>
  <div class="logo">♪</div>
  <div class="hd"><h1>music3</h1><div class="sub">B站 / 网易云 / QQ音乐 · 打分去重</div></div>
  <div class="hdr-right">
    <button class="ghost sm" id="btnset" title="设置">设置</button>
    <button class="ghost sm" id="btnabout" title="关于本工具">关于</button>
  </div>
</header>

<!-- 设置弹窗：音质 / 登录 / 赠金 -->
<div class="modal" id="setmodal" role="dialog" aria-modal="true" aria-labelledby="settitle">
  <div class="mbox">
    <button class="mclose" id="setclose" aria-label="关闭设置">✕</button>
    <div class="mlogo">⚙</div>
    <div class="mtitle" id="settitle">设置</div>
    <div class="mver">音质 · 登录 · 赠金</div>

    <div class="creditbox">
      <span style="font-size:20px">◈</span>
      <div style="flex:1">
        <div style="font-size:12px;color:var(--dim)">赠金余额（假设为本地记账额度，可编辑）</div>
        <div class="h">每成功下载 1 首扣 1 赠金，余额 0 时仍可下载（记为欠费）</div>
      </div>
      <span class="cv" id="creditv">--</span>
    </div>
    <div class="setrow">
      <span class="k">调整赠金</span>
      <input type="text" id="creditin" placeholder="如 100 或 -10">
      <button class="ghost sm" id="creditset">应用</button>
    </div>

    <div class="setrow" style="flex-direction:column;align-items:stretch">
      <span class="k">下载路径 <span class="n">（相对曲库根的子目录，留空=按来源自动分类）</span></span>
      <input type="text" id="destsub" placeholder="如 投稿/QQ音乐 或 投稿/我的收藏">
      <div class="h">留空 = 按来源自动投到 投稿/ 下各源子目录；填了则全部进该子目录（自动创建）。</div>
    </div>
    <div class="setrow">
      <span class="k">QQ 音质</span>
      <select id="qquality">
        <option value="14,11,10,8,4">综合（默认，死链过滤顺序）</option>
        <option value="14,8,4">偏高码率（320 优先）</option>
        <option value="4,8,10,11,14">偏快速（低档先取，秒下）</option>
      </select>
    </div>
    <div class="setrow" style="flex-direction:column;align-items:stretch">
      <span class="k">QQ 登录 <span class="n">（qm_keyst cookie，提高取链成功率）</span></span>
      <input type="text" id="qqcookie" placeholder="粘贴浏览器 y.qq.com Cookie: qm_keyst=xxx">
      <div class="h">从 y.qq.com 页面 F12 → Application → Cookies 复制 qm_keyst。留空=游客模式。</div>
    </div>
    <div class="setrow" style="flex-direction:column;align-items:stretch">
      <span class="k">网易云登录 <span class="n">（MUSIC_U cookie）</span></span>
      <input type="text" id="necookie" placeholder="粘贴 music.163.com 的 Cookie: MUSIC_U=xxx">
      <div class="h">登录后可搜到版权原唱（未登录只能搜到翻唱）。留空=游客模式。</div>
    </div>

    <div class="mactions">
      <button class="ghost" id="setsave">保存设置</button>
      <button class="ghost" id="setclose2">关闭</button>
    </div>
    <div class="mnote" id="setmsg" role="status" aria-live="polite">保存即生效，源搜索/下载下次请求携带新配置。</div>
  </div>
</div>

<!-- 关于弹窗 -->
<div class="modal" id="aboutmodal" role="dialog" aria-modal="true" aria-labelledby="abouttitle">
  <div class="mbox">
    <button class="mclose" id="mclose" aria-label="关闭关于">✕</button>
    <div class="mlogo">♪</div>
    <div class="mtitle">music3 · 三源音乐工具</div>
    <div class="mver">B站 / 网易云 / QQ音乐 · 统一搜索 · 打分去重 · v1.0.0</div>

    <div class="mrow">
      <span class="mk">作者</span>
      <span class="mv"><b>最中幻想</b></span>
    </div>
    <div class="mrow">
      <span class="mk">微信</span>
      <span class="mv" id="wxid">andyloveanny</span>
      <button class="copybtn" data-copy="andyloveanny">复制</button>
    </div>
    <div class="mrow">
      <span class="mk">仓库</span>
      <span class="mv" id="repo">github.com/qingshanjiluo/music3</span>
      <button class="copybtn" data-copy="https://github.com/qingshanjiluo/music3">复制</button>
    </div>

    <a class="mstar" id="gostar" href="https://github.com/qingshanjiluo/music3" target="_blank" rel="noopener">
      ⭐ 点个 Star 支持一下
    </a>

    <div class="mactions">
      <button class="ghost sm" id="openrepo">打开仓库</button>
      <button class="ghost sm" id="copywx">复制微信号</button>
    </div>

    <div class="mrow" style="flex-direction:column;align-items:stretch;gap:6px">
      <div class="mk" style="width:auto">快捷键</div>
      <div class="mv" style="font-size:12px;line-height:1.9;color:var(--dim)">
        <span class="kbd">Space</span> 播放/暂停 · <span class="kbd">←</span><span class="kbd">→</span> 快退/快进 5s · <span class="kbd">↑</span><span class="kbd">↓</span> 音量<br>
        <span class="kbd">N</span>/<span class="kbd">P</span> 下/上曲 · <span class="kbd">L</span> 歌词 · <span class="kbd">E</span> 均衡器 · <span class="kbd">[</span><span class="kbd">]</span> 倍速<br>
        <span class="kbd">Esc</span> 关闭浮层 · <span class="kbd">Tab</span> 走到播放器按钮，<span class="kbd">Enter</span>/<span class="kbd">Space</span> 按下 · 窄屏 <span class="kbd">⋯</span> 收纳次要控制
      </div>
    </div>
    <div class="mnote">
      这个工具从第一行代码到 <b id="mnotePits">46</b> 条踩坑记录都是实打实趟出来的（<span id="mnoteRounds">—</span> 轮迭代 · <span id="mnoteCommits">—</span> 次提交）。<br>
      觉得有用就点个 ⭐ Star，这是最直接的鼓励。<br>
      有问题、提需求、聊实现，加微信 <b style="color:var(--acc)">andyloveanny</b>
    </div>
  </div>
</div>

<div class="tabs" role="tablist" aria-label="主导航">
  <div class="tab on" role="tab" aria-selected="true" data-p="s" aria-selected=" on" aria-controls="p-s">搜索</div>
  <div class="tab" role="tab" data-p="b" aria-selected="" aria-controls="p-b">曲库</div>
  <div class="tab" role="tab" data-p="h" aria-selected="" aria-controls="p-h">历史</div>
  <div class="tab" role="tab" data-p="st" aria-selected="" aria-controls="p-st">统计</div>
  <div class="tab" role="tab" data-p="f" aria-selected="" aria-controls="p-f">收藏</div>
  <div class="tab" role="tab" data-p="q" aria-selected="" aria-controls="p-q">批量</div>
  <div class="tab" role="tab" data-p="d" aria-selected="" aria-controls="p-d">清理</div>
</div>

<!-- ========== 搜索 ========== -->
<div class="pane on" id="p-s" role="tabpanel" aria-labelledby="tab-s" tabindex="-1">
  <div class="bar">
    <div class="vtog" id="smode" role="radiogroup" aria-label="搜索模式">
      <span class="on" data-sm="all">全部</span>
      <span data-sm="song">歌曲</span>
      <span data-sm="artist">歌手</span>
      <span data-sm="mv">MV</span>
    </div>
    <input type="text" id="q" placeholder="歌名 歌手，如：晴天 周杰伦" autofocus>
    <button id="go">搜索</button>
  </div>
  <div class="bar">
    <label class="chk"><input type="checkbox" id="bili" checked> 含B站</label>
    <label class="chk"><input type="checkbox" id="force"> 忽略查重</label>
    <button class="ghost sm" id="top1">只下第一首</button>
    <button class="ghost sm" id="selall">全选</button>
    <button class="ghost sm" id="selnone">全不选</button>
    <button class="ghost sm" id="bulkdl">批量下载所选</button>
    <button class="ghost sm" id="tofav" title="把所选加入收藏歌单">加入收藏</button>
    <button class="ghost sm" id="bysong" title="把搜索词加入批量页">加入批量</button>
    <span class="n" id="smodetip">歌名模式</span>
  </div>
  <div class="bar">
    <input type="text" id="linkin" placeholder="粘贴歌单页链接（y.qq.com / music.163.com / bilibili.com，可多行；BV 链接也行）" style="flex:1">
    <button class="ghost sm" id="linkgo">歌单链接下载</button>
  </div>
  <div class="msg" id="msg" role="status" aria-live="polite"></div>
  <div class="tablewrap">
  <table><thead><tr>
    <th style="width:38px"><input type="checkbox" id="selallh" title="全选"></th>
    <th style="width:40px">#</th><th style="width:44px">分</th><th style="width:48px">时长</th>
    <th style="width:66px">来源</th><th>标题</th><th style="width:116px">操作</th>
  </tr></thead><tbody id="tb"></tbody></table>
  </div>
</div>

<!-- 大图灯箱 -->
<div class="lightbox" id="lightbox" role="dialog" aria-modal="true" aria-label="封面大图">
  <button class="lbclose" id="lbclose" aria-label="关闭大图">✕</button>
  <img id="lbimg" alt="">
  <div class="lbcap" id="lbcap"></div>
</div>

<!-- ========== 曲库 ========== -->
<div class="pane" id="p-b" role="tabpanel" aria-labelledby="tab-b" tabindex="-1">
  <div class="bar">
    <input type="text" id="fq" placeholder="在曲库中查找…">
    <button id="fgo">查找</button>
    <button class="ghost" id="reload">刷新</button>
    <button class="ghost" id="mkdir">新建文件夹</button>
    <button class="ghost" id="redir">改名当前</button>
    <div class="vtog" role="radiogroup" aria-label="视图切换">
      <span class="on" data-v="grid">网格</span>
      <span data-v="list">列表</span>
    </div>
  </div>
  <div class="crumbs" id="crumbs" role="navigation" aria-label="目录位置"><span class="n">全部目录</span></div>
  <div class="chips" id="chips"></div>
  <div class="msg" id="bmsg" role="status" aria-live="polite"></div>
  <div class="grid" id="grid"></div>
</div>

<!-- ========== 历史 ========== -->
<div class="pane" id="p-h" role="tabpanel" aria-labelledby="tab-h" tabindex="-1">
  <div class="bar">
    <button class="ghost" id="hreload">刷新</button>
    <button class="danger sm" id="hclear">清空历史</button>
    <span class="n" id="hcount"></span>
  </div>
  <div class="msg" id="hmsg" role="status" aria-live="polite"></div>
  <table><thead><tr>
    <th style="width:36px">#</th><th>标题</th><th style="width:120px">歌手</th>
    <th style="width:130px">时间</th><th style="width:56px">操作</th>
  </tr></thead><tbody id="htb"></tbody></table>
</div>

<!-- ========== 收藏歌单 ========== -->
<div class="pane" id="p-f" role="tabpanel" aria-labelledby="tab-f" tabindex="-1">
  <div class="bar">
    <button class="ghost" id="favreload">刷新</button>
    <button class="ghost" id="favdlall" title="把收藏的曲目逐首下载">一键下载</button>
    <button class="ghost" id="favexport" title="导出收藏为 m3u8">导出 m3u8</button>
    <button class="ghost" id="favexpjson" title="导出完整字段 JSON（跨设备迁移用）">导出JSON</button>
    <button class="ghost" id="favimp" title="导入收藏 JSON">导入JSON</button>
    <input type="file" id="favimpfile" accept=".json,application/json" style="display:none">
    <button class="danger sm" id="favclear">清空</button>
    <span class="n" id="favcount"></span>
  </div>
  <div class="msg" id="favmsg" role="status" aria-live="polite"></div>
  <div id="favlist"></div>
</div>

<!-- ========== 统计 ========== -->
<div class="pane" id="p-st" role="tabpanel" aria-labelledby="tab-st" tabindex="-1">
  <div class="bar">
    <button class="ghost" id="streload">刷新</button>
    <button class="danger sm" id="stclear">清空统计</button>
    <span class="n">播满 30 秒才计一次</span>
  </div>
  <div class="msg" id="stmsg" role="status" aria-live="polite"></div>
  <div class="statgrid" id="stcards"></div>
  <div class="bar" style="margin-top:14px">
    <div class="vtog" role="radiogroup" aria-label="视图切换">
      <span class="on" data-sv="count">按次数</span>
      <span data-sv="seconds">按时长</span>
    </div>
  </div>
  <div class="chips" id="sttabs"></div>
  <div class="tablewrap">
  <table><thead><tr>
    <th style="width:36px">#</th><th>曲目</th><th style="width:80px">次数</th>
    <th style="width:86px">时长</th><th style="width:56px">操作</th>
  </tr></thead><tbody id="sttb"></tbody></table>
  </div>
</div>

<!-- ========== 批量 ========== -->
<div class="pane" id="p-q" role="tabpanel" aria-labelledby="tab-q" tabindex="-1">
  <div class="bar">
    <input type="text" id="bkws" placeholder="多行关键词，逗号或换行分隔" style="min-height:74px;resize:vertical">
  </div>
  <div class="bar">
    <label class="chk">每词下载 <input type="number" id="bn" value="1" min="1" max="10" style="width:56px;flex:0 0 auto;padding:6px 8px"> 首</label>
    <label class="chk">并发 <input type="number" id="bw" value="3" min="1" max="8" style="width:52px;flex:0 0 auto;padding:6px 8px"> 线程</label>
    <label class="chk"><input type="checkbox" id="bbili"> 含B站</label>
    <label class="chk">到 <input type="text" id="bdest" placeholder="目标子目录（留空=按来源分目录）" style="min-width:150px;width:200px;flex:0 0 auto;padding:7px 9px;font-size:12.5px"></label>
    <button id="bstart">开始下载</button>
    <button class="ghost" id="bstop">停止</button>
    <button class="ghost sm" id="bclear" title="关掉事件流并清空已完成的下载卡片">清空队列</button>
  </div>
  <div id="jobbox"></div>
</div>

<!-- ========== 清理 ========== -->
<div class="pane" id="p-d" role="tabpanel" aria-labelledby="tab-d" tabindex="-1">
  <div class="bar">
    <button id="hscan">健康检查</button>
    <label class="chk"><input type="checkbox" id="hdeep"> 读 ID3（准但慢）</label>
    <button class="ghost" id="hfixcover" title="对「无封面」列表逐首联网补">补封面</button>
    <button class="ghost" id="hfixlyric" title="对「缺歌词」列表逐首联网补">补歌词</button>
    <button class="ghost" id="hfixmeta" title="ID3 双缺批量修复：标题=清洗文件名，歌手=非通用父目录（先 500 采样快估，估 0 秒级收尾）">修ID3</button>
    <span class="n" id="hdeeptip">深扫全库约 136s（读 ID3）；快扫按文件名约 5s</span>
  </div>
  <div class="msg" id="hmsg2" role="status" aria-live="polite"></div>
  <div id="hresult"></div>

  <div class="bar" style="margin-top:18px;border-top:1px solid var(--line);padding-top:16px">
    <b style="font-size:13px">查重</b>
  </div>
  <div class="bar">
    <button id="scan">扫描重复</button>
    <label class="chk"><input type="radio" name="by" value="name" checked> 按名</label>
    <label class="chk"><input type="radio" name="by" value="hash"> 按内容</label>
  </div>
  <div class="msg" id="dmsg" role="status" aria-live="polite"></div>
  <div id="dlist"></div>

  <div class="bar" style="margin-top:18px;border-top:1px solid var(--line);padding-top:16px">
    <b style="font-size:13px">维护守护</b>
    <button class="ghost sm" id="mtfold" style="float:right;margin-top:-2px" title="折叠/展开「看状态」区(卡片+进度+最近补入+日志), 记忆到 localStorage" onclick="mtFold()">▾ 折叠</button>
  </div>
  <div class="bar">
    <button id="mtrun">跑一轮</button>
    <button class="ghost" id="mtstat">看状态</button>
    <button class="ghost sm" id="mtrefresh" title="只重拉 8 卡数据(不重铺日志区)">刷新</button>
    <button class="ghost" id="mtlog">看日志</button>
    <button class="ghost sm" id="mtloglive" title="每 2s 刷新日志(跑维护时挂上)">实时日志</button>
    <button class="ghost sm" id="mtautoref" title="每 5s 自动重拉 9 卡(跑维护/跑到全库时挂着, 实时看累计/delta/本轮补变化)" onclick="mtAutoRef()">自动刷 5s</button>
    <button class="ghost sm" id="mtlogexport" title="导出当前日志(maintain.log 全量)">导出日志</button>
    <input type="text" id="mtlogfilter" placeholder="过滤日志：歌词 / 封面 / 异常…" title="本地过滤(实时刷新也生效), 命中行高亮" style="width:220px;flex:0 0 auto;padding:6px 8px">
    <span class="n" style="display:flex;gap:4px;align-items:center"><button class="ghost sm" data-lf="歌词">歌词</button><button class="ghost sm" data-lf="封面">封面</button><button class="ghost sm" data-lf="异常">异常</button><button class="ghost sm" data-lf="">全部</button></span>
    <button class="danger sm" id="mtreset">重置断点</button>
  </div>
  <div class="bar">
    <label class="chk">每轮 <input type="number" id="mtbatch" value="20" min="1" max="100" style="width:56px;flex:0 0 auto;padding:6px 8px"> 首</label>
    <label class="chk">连跑 <input type="number" id="mtruns" value="1" min="1" max="50" style="width:48px;flex:0 0 auto;padding:6px 8px"> 轮 <input type="checkbox" id="mtfull" title="勾选则忽略轮数, 连跑到全库跑完一圈(5188 首, 每 tick 20 首)"> 跑到全库</label>
    <label class="chk"><input type="checkbox" id="mtlyric" checked> 补歌词</label>
    <label class="chk"><input type="checkbox" id="mtcover" checked> 补封面</label>
    <label class="chk"><input type="checkbox" id="mtclean" checked> 清临时</label>
  </div>
  <div class="msg" id="mtmsg" role="status" aria-live="polite"></div>
  <div id="mtresult"></div>

  <div class="bar" style="margin-top:18px;border-top:1px solid var(--line);padding-top:16px">
    <b style="font-size:13px">导出</b>
  </div>
  <div class="bar">
    <button class="ghost" onclick="doExport('m3u8','lib')">曲库 m3u8</button>
    <button class="ghost" onclick="doExport('csv','lib')">曲库 CSV</button>
    <button class="ghost" onclick="doExport('json','lib')">曲库 JSON</button>
    <button class="ghost" onclick="doExport('index','lib')">全库索引(快)</button>
    <button class="ghost" onclick="doExport('index','lib',0)">全库索引(含时长)</button>
  </div>
  <div class="bar">
    <button class="ghost" onclick="doExport('m3u8','playlist')">当前播放列表 m3u8</button>
  </div>
  <div class="n">m3u8 通用（foobar2000 / VLC / 手机播放器）；CSV 带 UTF-8 BOM，Excel 直接开不乱码；「快」不读 ID3 时长约 3s，「含时长」全量解析约 2min</div>
</div>

</div>

<!-- 播放器 -->
<div class="player" id="player" role="toolbar" aria-label="播放器控制条">
  <canvas class="pwave" id="pwave" width="600" height="44"></canvas>
  <div class="pbar" id="pbar" role="progressbar" aria-label="播放进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><i></i></div>
  <div class="pcov" id="pcov">♪</div>
  <div class="pinfo">
    <div class="ptitle" id="ptitle">未播放</div>
    <div class="partist" id="partist"></div>
  </div>
  <div class="pbtns">
    <div class="pvol" id="pvolBox"><input type="range" id="pvol" min="0" max="100" value="100" aria-label="音量"></div>
    <div class="pbtn" id="peq" title="均衡器" aria-label="均衡器"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 21v-6M5 9V3M12 21v-10M12 5V3M19 21v-4M19 11V3"/><path d="M2 15h6M10 5h4M17 11h4"/></svg></div>
    <div class="pbtn" id="plyr" title="歌词" aria-label="歌词"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg></div>
    <div class="pbtn" id="plopen" title="播放列表" aria-label="播放列表"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 6h16M4 12h10M4 18h13"/></svg></div>
    <div class="pbtn" id="prate" title="播放速度" aria-label="播放速度">1x</div>
    <div class="pbtn" id="pmode" title="播放模式" aria-label="播放模式"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg></div>
    <div class="pbtn" id="pprev" title="上一首" aria-label="上一首"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 5h2v14H6zM20 5v14L9.5 12z"/></svg></div>
    <div class="pbtn main" id="ptoggle" aria-label="播放"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4l13 8-13 8z"/></svg></div>
    <div class="pbtn" id="pnext" title="下一首" aria-label="下一首"><svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 5h2v14h-2zM4 5v14l10.5-7z"/></svg></div>
    <div class="pbtn" id="pclose" title="关闭播放" aria-label="关闭"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg></div>
    <div class="pbtn pmore" id="pmore" title="更多控制" aria-label="更多控制" aria-expanded="false">⋯</div>
    <div class="pmorebox" id="pmorebox" role="menu" hidden>
      <button class="ghost sm" onclick="lyOpen()" role="menuitem">歌词</button>
      <button class="ghost sm" onclick="plOpen()" role="menuitem">播放列表</button>
      <button class="ghost sm" onclick="eqOpen()" role="menuitem">均衡器</button>
      <button class="ghost sm" onclick="pmode.click()" role="menuitem">模式</button>
      <button class="ghost sm" onclick="prate.click()" role="menuitem">速度</button>
      <button class="ghost sm" onclick="pcloseBtn()" role="menuitem">关闭</button>
    </div>
  </div>
</div>
<audio id="audio" preload="none" crossorigin="anonymous"></audio>

<!-- 均衡器面板 -->
<div class="eqpanel" id="eqpanel">
  <div class="eqhead">
    <b>均衡器</b>
    <label class="chk"><input type="checkbox" id="eqoff"> 旁通</label>
    <button class="ghost sm" id="eqclose">✕</button>
  </div>
  <div class="eqbody">
    <div class="eqpresets">
      <span onclick="eqSetPreset('flat')">平直</span>
      <span onclick="eqSetPreset('pop')">流行</span>
      <span onclick="eqSetPreset('rock')">摇滚</span>
      <span onclick="eqSetPreset('vocal')">人声</span>
      <span onclick="eqSetPreset('bass')">重低音</span>
      <span onclick="eqSetPreset('treble')">高音</span>
    </div>
    <div class="eqsliders" id="eqsliders"></div>
    <div class="eqlabels" id="eqlabels"></div>
    <div class="n" style="margin-top:18px;line-height:1.7">
      拖动竖条调各频段增益（-12 ~ +12 dB）。<br>
      设置自动保存，切页面不丢。<br>
      旁通时全部归零但不丢配置。
    </div>
  </div>
</div>

<!-- 歌词全屏面板 -->
<div class="lyrics" id="lyrics">
  <div class="lyhead">
    <b id="lytitle">歌词</b>
    <span class="n">点歌词可跳转 · <span class="kbd">Esc</span> 关闭</span>
    <button class="ghost sm" id="lyfetch" title="手动取词（各源同名候选）">手动取词</button>
    <button class="ghost sm" id="lyclose">✕</button>
  </div>
  <div class="lybody" id="lybody"></div>
  <div class="lycands" id="lycands"></div>
</div>

<!-- 播放列表抽屉 -->
<div class="plmask" id="plmask"></div>
<aside class="plist" id="plist">
  <div class="plhead">
    <b>播放列表 <span class="n" id="plcount"></span></b>
    <button class="ghost sm" id="plclear">清空</button>
    <button class="ghost sm" id="plclose">✕</button>
  </div>
  <div class="plbody" id="plbody"></div>
</aside>

<script>
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const scCls=v=>v>=0.8?'hi':v>=0.5?'mid':'lo';
const srcCls=s=>['qq','netease','bilibili'].includes(s)?s:'';
const mb=b=>(b/1048576).toFixed(1)+'MB';
const setMsg=(el,t,cls)=>{el.textContent=t;el.className='msg'+(cls?' '+cls:'');};

/* 窄屏「⋯」更多控制开合(点外部关闭) */
function pcloseBtn(){ if(curRel) $('#pclose').click(); $('#pmorebox').classList.remove('on'); $('#pmore').setAttribute('aria-expanded','false'); }
document.addEventListener('click', (e)=>{
  const box=$('#pmorebox'), btn=$('#pmore');
  if(!box || box.hidden!==undefined && !box.classList.contains('on')) return;
  if(!box.classList.contains('on')) return;
  if(box.contains(e.target) || btn.contains(e.target)) return;
  box.classList.remove('on'); btn.setAttribute('aria-expanded','false');
});
document.addEventListener('DOMContentLoaded', ()=>{ const b=$('#pmore'); if(b) b.onclick=(e)=>{
  e.stopPropagation();
  const box=$('#pmorebox'); const on=box.classList.toggle('on');
  b.setAttribute('aria-expanded', on?'true':'false');
};});
/* 键盘可达: .pbtn 是 div, 补 role/tabindex + Enter/Space 激活 (原 Tab 到不了播放器) */
function _makeFocusablePbtns(){
  $$('.pbtn').forEach(el=>{
    if(el.getAttribute('tabindex')!=null) return;
    if(!el.getAttribute('role')) el.setAttribute('role','button');
    el.setAttribute('tabindex','0');
    el.addEventListener('keydown', (e)=>{
      if(e.key==='Enter' || e.key===' '){
        e.preventDefault(); e.stopPropagation();   // 拦掉全局空格=播放, 走当前聚焦钮
        el.click();
        if(el.id==='pmore'){ const f=$('#pmorebox button'); if(f) f.focus(); }
      }
    });
  });
}
_makeFocusablePbtns();
/* ⋯ 弹层键盘流: Esc 关闭并把焦点还给 ⋯ (menu role 合规) */
document.addEventListener('keydown', (e)=>{
  if(e.key!=='Escape') return;
  const box=$('#pmorebox');
  if(box && box.classList.contains('on')){
    box.classList.remove('on');
    $('#pmore').setAttribute('aria-expanded','false');
    $('#pmore').focus();
  }
});
/* ---------- 标签切换：往返保留滚动位置(结构硬规则4) + 有数据不整页重拉 ---------- */
const _scrollMem = {};   // p -> 离开时 scrollY
function _restoreScroll(p){
  requestAnimationFrame(()=>{ const y = _scrollMem[p]|0; if(y>0) window.scrollTo(0, y); });
}
$$('.tab').forEach(t=>t.onclick=()=>{
  const prev = document.querySelector('.tab.on');
  if(prev) _scrollMem[prev.dataset.p] = window.scrollY;   // 离开前记住位置
  $$('.tab').forEach(x=>x.classList.remove('on'));
  $$('.pane').forEach(x=>x.classList.remove('on'));
  t.classList.add('on'); $('#p-'+t.dataset.p).classList.add('on');
  const p = t.dataset.p;
  if(p==='b'){
    if(!document.querySelector('#chips .chip')) loadChips().then(()=>{ if(curSub) openDir(curSub).then(()=>_restoreScroll('b')); });
    else if(curSub) _restoreScroll('b');                    // 曲库已有数据: 只回位不重拉
  }
  if(p==='h'){
    if($('#htb') && $('#htb').children.length) _restoreScroll('h');   // 历史已有: 回位
    else loadHistory().then(()=>_restoreScroll('h'));
  }
  if(p==='st'){
    if($('#sttb') && $('#sttb').children.length) _restoreScroll('st');
    else stLoad().then(()=>_restoreScroll('st'));
  }
  if(p==='f'){
    if($('#favlist') && $('#favlist').children.length) _restoreScroll('f');
    else favLoad().then(()=>_restoreScroll('f'));
  }
});

/* ---------- 播放器 ---------- */
const audio=$('#audio'), player=$('#player'), pbar=$('#pbar');
let curRel='', playing=false, playList=[], playIdx=-1;
let playRecorded=false, playStart=0;
/* 播放模式：list(列表循环) / one(单曲循环) / shuffle(随机) / seq(顺序不循环) */
let playMode = localStorage.getItem('m3_mode') || 'list';
const MODE_SVG = {
  list:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>',
  one:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/><path d="M11 10l2 2-2 2" fill="none"/></svg>',
  shuffle:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M16 3h5v5M4 20L21 3M21 16v5h-5M15 15l6 6M4 4l5 5"/></svg>',
  seq:'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M5 4l7 8-7 8M12 4l7 8-7 8"/></svg>',
};
const PLAY_SVG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M7 4l13 8-13 8z"/></svg>';
const PAUSE_SVG = '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>';
const MODE_NAME = {list:'列表循环', one:'单曲循环', shuffle:'随机', seq:'顺序播放'};
function setPlayIcon(on){
  player.classList.toggle('pulsing', !!on);
  const _t=$('#ptoggle'); if(_t) _t.setAttribute('aria-label', on? '暂停':'播放');
  const t = $('#ptoggle');
  if(t) t.innerHTML = on ? PAUSE_SVG : PLAY_SVG;
}
/* 播放速度 */
const RATES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0];
let playRate = parseFloat(localStorage.getItem('m3_rate') || '1') || 1;

/* 波形：AudioContext + AnalyserNode 实时频谱 */
let actx=null, analyser=null, srcNode=null, waveRAF=0, freqData=null;
const waveCanvas=$('#pwave'), waveCtx=waveCanvas.getContext('2d');

/* 8 段均衡器：60/170/350/1000/3500/5000/10000/16000 Hz */
const EQ_FREQS = [60, 170, 350, 1000, 3500, 5000, 10000, 16000];
const EQ_LABELS = ['60', '170', '350', '1k', '3.5k', '5k', '10k', '16k'];
let eqFilters = [];
let eqGains = JSON.parse(localStorage.getItem('m3_eq') || 'null') || [0,0,0,0,0,0,0,0];
let eqBypass = localStorage.getItem('m3_eq_off') === '1';

function ensureAudioGraph(){
  if(actx) return true;
  try{
    const AC = window.AudioContext || window.webkitAudioContext;
    if(!AC) return false;
    actx = new AC();
    srcNode = actx.createMediaElementSource(audio);

    // 串联 8 个 peaking filter
    let prev = srcNode;
    eqFilters = EQ_FREQS.map((f,i)=>{
      const bq = actx.createBiquadFilter();
      bq.type = 'peaking';
      bq.frequency.value = f;
      bq.Q.value = 1.1;
      bq.gain.value = eqBypass ? 0 : (eqGains[i] || 0);
      prev.connect(bq);
      prev = bq;
      return bq;
    });

    analyser = actx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.82;
    prev.connect(analyser);
    analyser.connect(actx.destination);
    freqData = new Uint8Array(analyser.frequencyBinCount);
    return true;
  }catch(e){
    console.warn('audio graph 创建失败（可能是 CORS）', e);
    actx = null;
    return false;
  }
}

function eqApply(i, val){
  eqGains[i] = +val;
  localStorage.setItem('m3_eq', JSON.stringify(eqGains));
  if(eqFilters[i]) eqFilters[i].gain.value = eqBypass ? 0 : +val;
  eqLabels();
}
function eqSetPreset(name){
  const P = {
    flat:   [0,0,0,0,0,0,0,0],
    pop:    [-1,2,4,4,1,-1,-1,0],
    rock:   [4,3,2,0,-1,1,3,4],
    vocal:  [-2,-1,1,3,4,3,1,0],
    bass:   [7,6,4,1,0,0,0,0],
    treble: [0,0,0,0,1,3,6,7],
  };
  const g = P[name] || P.flat;
  g.forEach((v,i)=>eqApply(i,v));
  $$('.eqslider').forEach((el,i)=>{ el.value = g[i]; });
}
function eqLabels(){
  const e = $('#eqlabels');
  if(e) e.innerHTML = EQ_LABELS.map((l,i)=>`<span>${l}<br><b>${eqGains[i]>0?'+':''}${eqGains[i]}</b></span>`).join('');
}

function eqInit(){
  const box = $('#eqsliders');
  if(!box) return;
  box.innerHTML = EQ_FREQS.map((f,i)=>
    `<div class="eqcol">
       <input type="range" class="eqslider" min="-12" max="12" step="1"
              value="${eqGains[i]||0}" data-i="${i}">
     </div>`).join('');
  $$('.eqslider').forEach(el=>{
    el.oninput = ()=>eqApply(+el.dataset.i, el.value);
  });
  eqLabels();
  const off = $('#eqoff');
  if(off){
    off.checked = eqBypass;
    off.onchange = ()=>{
      eqBypass = off.checked;
      localStorage.setItem('m3_eq_off', eqBypass ? '1' : '0');
      eqFilters.forEach((bq,i)=>{ if(bq) bq.gain.value = eqBypass ? 0 : (eqGains[i]||0); });
    };
  }
}
function eqOpen(){ document.body.classList.add('ov'); $('#eqpanel').classList.add('on'); eqInit(); }
function eqClose(){ document.body.classList.remove('ov'); $('#eqpanel').classList.remove('on'); }

function drawWave(){
  if(!waveCtx) return;
  const W = waveCanvas.width, H = waveCanvas.height;
  waveCtx.clearRect(0,0,W,H);
  const bars = 64;
  const bw = W / bars;

  if(analyser && !audio.paused){
    analyser.getByteFrequencyData(freqData);
    // 取前 64 个频点，低→高
    for(let i=0;i<bars;i++){
      const v = freqData[i] / 255;
      const h = Math.max(2, v * H * 0.95);
      const x = i * bw;
      const g = waveCtx.createLinearGradient(0, H-h, 0, H);
      g.addColorStop(0, 'rgba(124,92,255,0.95)');
      g.addColorStop(1, 'rgba(78,161,255,0.35)');
      waveCtx.fillStyle = g;
      waveCtx.fillRect(x+1, H-h, bw-2, h);
    }
  }else{
    // 暂停时画一条静态低幅波形
    const t = Date.now()/900;
    for(let i=0;i<bars;i++){
      const h = 2 + Math.abs(Math.sin(i*0.3 + t)) * (H*0.12);
      waveCtx.fillStyle = 'rgba(139,147,165,0.35)';
      waveCtx.fillRect(i*bw+1, H-h, bw-2, h);
    }
  }
  waveRAF = requestAnimationFrame(drawWave);
}

function startWave(){
  if(waveRAF) return;
  drawWave();
}
function stopWave(){
  if(waveRAF){ cancelAnimationFrame(waveRAF); waveRAF=0; }
  if(waveCtx) waveCtx.clearRect(0,0,waveCanvas.width,waveCanvas.height);
}

/* 自适应 canvas 宽度 */
function fitWave(){
  const r = waveCanvas.getBoundingClientRect();
  if(r.width && waveCanvas.width !== Math.round(r.width)){
    waveCanvas.width = Math.round(r.width);
  }
}
window.addEventListener('resize', fitWave);
audio.addEventListener('timeupdate', ()=>{ _saveQueue(false); });   // 播放中节流存进度

function fmtT(s){if(!isFinite(s))return '--:--';s=Math.max(0,Math.floor(s));return (Math.floor(s/60)+'').padStart(2,'0')+':'+(s%60+'').padStart(2,'0');}

let _qLastSave = 0;
function _saveQueue(force){
  if(!force && Date.now()-_qLastSave < 5000) return;   // 节流: 5s 一次
  _qLastSave = Date.now();
  try{ localStorage.setItem('m3_queue', JSON.stringify({
    rel: curRel, idx: playIdx, t: audio.currentTime|0,
    title: $('#ptitle').textContent, artist: $('#partist').textContent,
    list: playList
  })); }catch(e){ /* 队列超 localStorage 配额(约5MB)时静默放弃, 不影响播放 */ }
}
function play(rel, title, artist, list, idx){
  curRel=rel; playList=list||[]; playIdx=(idx==null?-1:idx);
  player.classList.add('on');
  fitWave();
  $('#ptitle').textContent=title||rel.split(/[\\\\/]/).pop();
  $('#partist').textContent=artist||'';

  // 音频图只在首次创建（CORS 下 MediaElementSource 只能建一次）
  ensureAudioGraph();
  if(actx && actx.state === 'suspended') actx.resume();

  audio.src='/api/stream?rel='+encodeURIComponent(rel);
  _saveQueue(true);   // 换歌即存队列(不节流: 换歌是关键点)
  // 保留速度设置（切歌后 audio 属性会重置）
  try{ audio.playbackRate = playRate; }catch(e){}
  audio.play().then(()=>{
    playing=true; setPlayIcon(true);
    startWave();
  }).catch(e=>{
    setMsg($('#msg'),'播放失败: '+e.message,'bad');
  });

  // 封面
  $('#pcov').innerHTML='♪';
  fetch('/api/cover?rel='+encodeURIComponent(rel)).then(r=>{
    if(r.ok) return r.blob();
    throw 0;
  }).then(b=>{
    $('#pcov').innerHTML='<img src="'+URL.createObjectURL(b)+'" alt="">';
  }).catch(()=>{});

  // 记历史（异步，不阻塞）
  fetch('/api/history?add='+encodeURIComponent(rel)
        +'&title='+encodeURIComponent(title||'')
        +'&artists='+encodeURIComponent(artist||'')).catch(()=>{});

  // 统计：播满 30 秒才算一次有效播放（避免误点计入）
  playRecorded = false;
  playStart = Date.now();

  // 同步到播放列表（已在列表里就只更新 current）
  const exist = (plData.items||[]).findIndex(x=>x.rel===rel);
  if(exist<0){
    fetch('/api/playlist?act=add&rel='+encodeURIComponent(rel)
          +'&title='+encodeURIComponent(title||'')
          +'&artists='+encodeURIComponent(artist||''))
      .then(r=>r.json()).then(d=>{ plData=d; plRender(); }).catch(()=>{});
  }else{
    plData.current = exist;
    fetch('/api/playlist?act=current&idx='+exist).catch(()=>{});
    plRender();
  }

  // 歌词：如果面板开着就加载新歌的
  if($('#lyrics').classList.contains('on')){
    lyLoad(rel, title);
  }else{
    lyLines = []; lyCur = -1;   // 关着就不预载，省流量
  }

  $$('tbody tr').forEach(tr=>tr.classList.remove('playing'));
}

$('#ptoggle').onclick=()=>{
  if(!curRel)return;
  if(audio.paused){
    audio.play().then(()=>{ setPlayIcon(true); startWave(); });
  }else{
    audio.pause(); setPlayIcon(false); stopWave();
  }
};
$('#pprev').onclick=()=>{
  if(audio.currentTime > 3){ audio.currentTime = 0; return; }
  playNext(-1);
};
$('#pnext').onclick=()=>{ playNext(1); };

function applyMode(){
  const el = $('#pmode');
  if(el){ el.innerHTML = MODE_SVG[playMode] || MODE_SVG.list; el.title = '播放模式：' + MODE_NAME[playMode]; }
  localStorage.setItem('m3_mode', playMode);
}
$('#pmode').onclick=()=>{
  const order = ['list','one','shuffle','seq'];
  const i = order.indexOf(playMode);
  playMode = order[(i+1) % order.length];
  applyMode();
};

/* 播放速度 */
function applyRate(){
  audio.playbackRate = playRate;
  try{ audio.preservesPitch = true; }catch(e){}
  try{ audio.mozPreservesPitch = true; }catch(e){}
  try{ audio.webkitPreservesPitch = true; }catch(e){}
  const el = $('#prate');
  if(el){
    el.textContent = (playRate === Math.floor(playRate) ? playRate.toFixed(0) : playRate) + 'x';
    el.title = '播放速度 ' + playRate + 'x（点击切换）';
    el.style.color = (playRate !== 1) ? 'var(--acc)' : '';
  }
  localStorage.setItem('m3_rate', String(playRate));
}
$('#prate').onclick=()=>{
  const i = RATES.indexOf(playRate);
  playRate = RATES[(i + 1) % RATES.length];
  applyRate();
};
$('#pclose').onclick=()=>{
  audio.pause(); audio.src=''; player.classList.remove('on');
  setPlayIcon(false); curRel=''; stopWave();
};
audio.ontimeupdate=()=>{
  const p=audio.currentTime/(audio.duration||1)*100;
  pbar.firstElementChild.style.width=Math.min(100,p)+'%';
  pbar.setAttribute('aria-valuenow', Math.round(Math.min(100,Math.max(0,p))));
  lySync();
  // 播满 30 秒记一次统计
  if(!playRecorded && curRel && audio.currentTime >= 30){
    playRecorded = true;
    const secs = (audio.duration && isFinite(audio.duration)) ? audio.duration : audio.currentTime;
    fetch('/api/stats?act=record'
          +'&rel='+encodeURIComponent(curRel)
          +'&title='+encodeURIComponent($('#ptitle').textContent||'')
          +'&artists='+encodeURIComponent($('#partist').textContent||'')
          +'&seconds='+Math.round(secs)).catch(()=>{});
  }
};
/* 按当前模式决定播哪首 */
function pickNext(dir){
  dir = dir || 1;
  const n = playList.length;
  if(!n) return -1;
  if(playMode === 'one' && dir > 0) return playIdx;   // 单曲循环
  if(playMode === 'shuffle' && n > 1){
    let i = playIdx;
    for(let k=0;k<12 && i===playIdx;k++) i = Math.floor(Math.random()*n);
    return i;
  }
  let i = playIdx + dir;
  if(i >= n) i = (playMode === 'seq') ? -1 : 0;   // 顺序模式到底就停
  if(i < 0) i = (playMode === 'seq') ? -1 : n-1;
  return i;
}
function playNext(dir){
  const i = pickNext(dir);
  if(i < 0 || !playList[i]){ setPlayIcon(false); stopWave(); return; }
  const t = playList[i];
  play(t.rel, t.title||t.name, t.artists||'', playList, i);
}
audio.onended=()=>{
  if(playMode === 'one'){ audio.currentTime = 0; audio.play(); return; }
  playNext(1);
};
audio.onpause=()=>{ setPlayIcon(false); };
audio.onplay =()=>{ setPlayIcon(true); };
pbar.onclick=e=>{
  if(!audio.duration)return;
  const r=pbar.getBoundingClientRect();
  audio.currentTime=(e.clientX-r.left)/r.width*audio.duration;
};

/* ---------- 播放列表抽屉 ---------- */
let plData = {items:[], current:-1};
let dragFrom = -1;

async function plLoad(){
  try{
    plData = await (await fetch('/api/playlist')).json();
    plRender();
  }catch(e){}
}
function plRender(){
  const items = plData.items||[];
  $('#plcount').textContent = `(${items.length})`;
  if(!items.length){
    $('#plbody').innerHTML = '<div class="n" style="padding:18px;text-align:center">播放列表为空<br>点曲库里的卡片开始</div>';
    return;
  }
  $('#plbody').innerHTML = items.map((x,i)=>`
    <div class="plitem ${i===plData.current?'on':''}" data-i="${i}" draggable="true">
      <span class="idx">${i+1}</span>
      <span class="txt">
        <div class="t1">${esc(x.title||x.rel.split(/[\\\\/]/).pop())}</div>
        <div class="t2">${esc(x.artists||'')}</div>
      </span>
      <span class="del" data-del="${i}" title="移除" role="button" aria-label="移除">✕</span>
    </div>`).join('');
  bindPlItems();
}
function bindPlItems(){
  $$('.plitem').forEach(el=>{
    const i = +el.dataset.i;

    el.onclick = (e)=>{
      if(e.target.dataset.del!==undefined) return;
      plPlay(i);
    };
    // 删除
    const del = el.querySelector('.del');
    if(del) del.onclick = async(e)=>{
      e.stopPropagation();
      const rel = plData.items[i].rel;
      plData = await (await fetch('/api/playlist?act=remove&rel='+encodeURIComponent(rel))).json();
      plRender();
    };
    // 拖拽
    el.ondragstart = (e)=>{
      dragFrom = i;
      el.classList.add('drag');
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', String(i));
    };
    el.ondragend = ()=>{ el.classList.remove('drag'); $$('.plitem').forEach(x=>x.classList.remove('over')); };
    el.ondragover = (e)=>{ e.preventDefault(); el.classList.add('over'); };
    el.ondragleave = ()=>{ el.classList.remove('over'); };
    el.ondrop = async(e)=>{
      e.preventDefault();
      el.classList.remove('over');
      const to = i;
      if(dragFrom<0 || dragFrom===to) return;
      plData = await (await fetch(`/api/playlist?act=move&from=${dragFrom}&to=${to}`)).json();
      dragFrom = -1;
      plRender();
    };
  });
}
async function plPlay(i){
  const it = (plData.items||[])[i];
  if(!it) return;
  plData.current = i;
  fetch('/api/playlist?act=current&idx='+i).catch(()=>{});
  play(it.rel, it.title, it.artists, plData.items, i);
  plRender();
}
function plOpen(){ document.body.classList.add('ov'); $('#plist').classList.add('on'); $('#plmask').classList.add('on'); plLoad(); }
function plClose(){ document.body.classList.remove('ov'); $('#plist').classList.remove('on'); $('#plmask').classList.remove('on'); }
$('#plopen').onclick = plOpen;
$('#plclose').onclick = plClose;
$('#plmask').onclick = plClose;
$('#plclear').onclick = async()=>{
  if(!confirm('清空播放列表？')) return;
  plData = await (await fetch('/api/playlist?act=clear')).json();
  plRender();
};

/* ---------- 歌词 ---------- */
let lyLines = [];     // [{t:秒, s:'文本'}]
let lyCur = -1;

function parseLRC(text){
  if(!text) return [];
  const out = [];
  const re = /\[(\d{1,2}):(\d{1,2})(?:[.:](\d{1,3}))?\]/g;
  text.split(/\r?\n/).forEach(raw=>{
    const line = raw.trim();
    if(!line) return;
    // 跳过元信息 [ti:] [ar:] [al:] [by:] [offset:]
    if(/^\[(ti|ar|al|by|offset|re|ve):/i.test(line)) return;
    const times = [];
    let m;
    re.lastIndex = 0;
    while((m = re.exec(line)) !== null){
      const mm = +m[1], ss = +m[2];
      let frac = m[3] ? +('0.' + m[3]) : 0;
      times.push(mm*60 + ss + frac);
    }
    if(!times.length) return;
    const txt = line.replace(re, '').trim();
    if(!txt) return;
    times.forEach(t=>out.push({t, s: txt}));
  });
  out.sort((a,b)=>a.t-b.t);
  return out;
}

function lyRender(){
  const box = $('#lybody');
  if(!lyLines.length){
    box.innerHTML = '<div class="lyempty">这首歌没有内嵌歌词<br><span class="n">下载时会自动写入 ID3 USLT</span></div>';
    return;
  }
  box.innerHTML = lyLines.map((x,i)=>
    `<div class="lyline" data-i="${i}">${esc(x.s)}</div>`).join('');
  $$('.lyline').forEach(el=>{
    el.onclick = ()=>{
      const i = +el.dataset.i;
      if(lyLines[i]) audio.currentTime = lyLines[i].t;
    };
  });
  box.scrollTop = 0;
  lyCur = -1;
  lySync();
}

function lySync(){
  if(!lyLines.length) return;
  const t = audio.currentTime + 0.25;   // 稍微提前，视觉更跟手
  // 二分找最后一条 t <= 当前时间
  let lo = 0, hi = lyLines.length - 1, idx = -1;
  while(lo <= hi){
    const mid = (lo+hi) >> 1;
    if(lyLines[mid].t <= t){ idx = mid; lo = mid+1; }
    else hi = mid-1;
  }
  if(idx === lyCur) return;
  lyCur = idx;
  $$('.lyline').forEach((el,i)=>{
    el.classList.toggle('cur', i===idx);
    el.classList.toggle('near', Math.abs(i-idx)===1 && idx>=0);
  });
  const cur = $$('.lyline')[idx];
  if(cur){
    const box = $('#lybody');
    const top = cur.offsetTop - box.clientHeight/2 + cur.offsetHeight/2;
    box.scrollTo({top: Math.max(0, top), behavior:'smooth'});
  }
}

async function lyLoad(rel, title){
  lyLines = []; lyCur = -1;
  $('#lytitle').textContent = title || '歌词';
  $('#lybody').innerHTML = '<div class="lyempty">加载中…</div>';
  let txt = '';
  // ① 先读内嵌
  try{
    const d = await (await fetch('/api/tags?rel='+encodeURIComponent(rel))).json();
    txt = d.lyric || '';
  }catch(e){}
  // ② 内嵌没有就联网补
  if(txt.replace(/\[\d[^\]]*\]/g,'').trim().length < 40){
    $('#lybody').innerHTML = '<div class="lyempty">内嵌无歌词，正在联网搜索…</div>';
    try{
      const d2 = await (await fetch('/api/lyric?rel='+encodeURIComponent(rel))).json();
      if(d2.lyric) txt = d2.lyric;
    }catch(e){}
  }
  lyLines = parseLRC(txt || '');
  lyRender();
}

function lyOpen(){
  document.body.classList.add('ov'); $('#lyrics').classList.add('on');
  if(curRel){ lyLoad(curRel, $('#ptitle').textContent); return; }
  $('#lybody').innerHTML = '<div class="lyempty" style="padding-top:14vh">'+
    '<div style="font-size:30px;opacity:.4;letter-spacing:4px">♪</div>'+
    '<div style="margin-top:10px;color:var(--fg);font-size:14px">还没开始播放</div>'+
    '<div style="margin-top:6px;font-size:12.5px;line-height:1.8">先在搜索 / 曲库点一首歌<br>播放时歌词逐行高亮 · 点词可跳转进度</div>'+
    '<div style="margin-top:10px;font-size:11.5px;color:#9a938a">没内嵌歌词时点右上「手动取词」联网补</div></div>';
}
function lyClose(){ document.body.classList.remove('ov'); $('#lyrics').classList.remove('on'); }
$('#plyr').onclick = lyOpen;
$('#lyclose').onclick = lyClose;
$('#peq').onclick = ()=>{ if($('#eqpanel').classList.contains('on')) eqClose(); else eqOpen(); };
$('#eqclose').onclick = eqClose;

/* 手动取词：列各源同名候选（B站没词时从 QQ/网易选） */
let lyCands = [];
async function lyFetchList(){
  const box = $('#lycands');
  if(!box) return;
  const title = $('#lytitle').textContent || $('#ptitle').textContent || '';
  let artists = $('#partist').textContent || '';
  box.innerHTML = '<div class="lyempty">搜索各源同名候选…</div>';
  try{
    const d = await (await fetch(
      `/api/lyric-fetch?act=candidates&title=${encodeURIComponent(title)}`
      + `&artist=${encodeURIComponent(artists)}&sources=qq,netease&limit=6`
    )).json();
    lyCands = d.candidates || [];
    if(!lyCands.length){ box.innerHTML = '<div class="lyempty">没找到同名候选，换个歌名试试</div>'; return; }
    box.innerHTML = lyCands.map((c,i)=>`
      <div class="lycand" data-i="${i}">
        <span class="lcsrc">${esc(c.source)}</span>
        <span class="lct">${esc(c.title)}<div class="lcn">${esc(c.artists||'')} · ${fmtDur(c.duration)} · 相似 ${c.score}</div></span>
        <button class="ghost sm" data-pick="${i}">用这首</button>
      </div>`).join('');
    box.querySelectorAll('[data-pick]').forEach(b=>{
      b.onclick = ()=>lyPick(+b.dataset.pick);
    });
  }catch(e){ box.innerHTML = '<div class="lyempty">搜索失败: '+esc(String(e))+'</div>'; }
}
async function lyPick(i){
  const c = lyCands[i]; if(!c || !curRel) return;
  const box = $('#lycands');
  box.innerHTML = '<div class="lyempty">拉取歌词中…</div>';
  try{
    const u = new URL('/api/lyric-fetch', location.origin);
    u.searchParams.set('act','pick'); u.searchParams.set('source',c.source);
    u.searchParams.set('sid', c.sid); u.searchParams.set('rel', curRel);
    u.searchParams.set('write','1');
    const d = await (await fetch(u)).json();
    if(d.ok && d.lyric){
      lyLines = parseLRC(d.lyric); lyRender();
      box.innerHTML = '<div class="lyok">已写入 ID3：'+esc(c.source)+' · '+esc(c.title)+'</div>';
      setTimeout(()=>{ const b=$('#lyfetch'); if(b) b.style.display=''; }, 1500);
    }else{
      box.innerHTML = '<div class="lyempty">取词失败：'+esc(d.msg||'无效歌词')+'</div>';
    }
  }catch(e){ box.innerHTML = '<div class="lyempty">失败: '+esc(String(e))+'</div>'; }
}
const _lyBtn = $('#lyfetch');
if(_lyBtn) _lyBtn.onclick = lyFetchList;

/* ---------- 音量 ---------- */
const volEl = $('#pvol');
const savedVol = localStorage.getItem('m3_vol');
if(savedVol !== null){
  volEl.value = savedVol;
  audio.volume = (+savedVol)/100;
}
volEl.oninput = ()=>{
  const v = +volEl.value;
  audio.volume = v/100;
  localStorage.setItem('m3_vol', String(v));
};

/* ---------- 快捷键 ---------- */
document.addEventListener('keydown', (e)=>{
  // 输入框里不拦截
  const tag = (e.target.tagName||'').toLowerCase();
  if(tag==='input' || tag==='textarea') return;

  switch(e.key){
    case ' ':
      if(curRel){ e.preventDefault(); $('#ptoggle').click(); }
      break;
    case 'ArrowLeft':
      if(curRel && audio.duration){ e.preventDefault(); audio.currentTime = Math.max(0, audio.currentTime-5); }
      break;
    case 'ArrowRight':
      if(curRel && audio.duration){ e.preventDefault(); audio.currentTime = Math.min(audio.duration, audio.currentTime+5); }
      break;
    case 'ArrowUp':
      e.preventDefault();
      volEl.value = Math.min(100, +volEl.value + 5);
      audio.volume = volEl.value/100; localStorage.setItem('m3_vol', volEl.value);
      $('#pvolBox').classList.add('on');
      break;
    case 'ArrowDown':
      e.preventDefault();
      volEl.value = Math.max(0, +volEl.value - 5);
      audio.volume = volEl.value/100; localStorage.setItem('m3_vol', volEl.value);
      $('#pvolBox').classList.add('on');
      break;
    case 'Escape':
      if($('#lyrics').classList.contains('on')) lyClose();
      else if($('#eqpanel').classList.contains('on')) eqClose();
      else if($('#plist').classList.contains('on')) plClose();
      break;
    case 'e': case 'E':
      if($('#eqpanel').classList.contains('on')) eqClose(); else eqOpen();
      break;
    case '[': case '{':
      { const i = RATES.indexOf(playRate); if(i > 0){ playRate = RATES[i-1]; applyRate(); } }
      break;
    case ']': case '}':
      { const i = RATES.indexOf(playRate); if(i >= 0 && i < RATES.length-1){ playRate = RATES[i+1]; applyRate(); } }
      break;
    case 'l': case 'L':
      if(curRel) lyOpen();
      break;
    case 'n': case 'N':
      if(curRel) $('#pnext').click();
      break;
    case 'p': case 'P':
      if(curRel) $('#pprev').click();
      break;
  }
});

/* ---------- 搜索 ---------- */
let last=[];
/* 冷启动/0结果空态: 可点示例词直接搜 (const DEMO_WORDS 定义必须在调用之前 — TDZ) */
const DEMO_WORDS = ['周杰伦 晴天', '五月天 突然好想你', '稻香', '起风了', 'Alan Walker Fade'];
function _demo(kw){ $('#q').value = kw; doSearch(); }
function emptyRows(title, sub){
  return `<div class="empty"><div class="eic">⌕</div><div class="et">${esc(title)}</div>`+
    `<div class="es">${esc(sub)}</div>`+
    `<div class="eh">试试这些：</div>`+
    `<div class="eact">${DEMO_WORDS.map(w=>`<button class="ghost sm" onclick="_demo(this.textContent)">${esc(w)}</button>`).join('')}</div></div>`;
}
$('#tb').innerHTML = `<tr><td colspan="7">${emptyRows('搜一首歌开始','支持 QQ音乐 / 网易云 / B站三源 · 勾「含B站」扩到视频源')}</td></tr>`;
async function doSearch(){
  const q=$('#q').value.trim(); if(!q)return;
  $('#go').disabled=true; setMsg($('#msg'),'搜索中…'); skTable(6);
  try{
    if(searchMode==='all')         return await doSearchAll(q);
    if(searchMode==='artist')      return await doSearchArtist(q);
    else if(searchMode==='mv')     return await doSearchMV(q);
    const src=$('#bili').checked?'qq,netease,bilibili':'qq,netease';
    const d=await (await fetch(`/api/search?q=${encodeURIComponent(q)}&sources=${src}&limit=15`)).json();
    if(d.error){setMsg($('#msg'),'错误: '+d.error,'bad');return;}
    last=(d.items||[]).map(t=>Object.assign({type:'song', duration:t.duration_s}, t));
    renderRows(last, false);
    setMsg($('#msg'),`共 ${last.length} 条 · 0.8以上可直接下`);
  }catch(e){setMsg($('#msg'),'失败: '+e,'bad');}
  finally{$('#go').disabled=false;}
}
/* 全部模式：歌曲+歌手曲+MV 三路并发，一组表格分组展示（rows 带 type） */
async function doSearchAll(q){
  setMsg($('#msg'),'并发搜索中（歌曲 / 歌手曲目 / B站MV）…');
  const src=$('#bili').checked?'qq,netease,bilibili':'qq,netease';
  const [rSong, rArtist, rMV] = await Promise.allSettled([
    fetch(`/api/search?q=${encodeURIComponent(q)}&sources=${src}&limit=12`).then(r=>r.json()),
    fetch(`/api/artists?name=${encodeURIComponent(q)}&limit=12`).then(r=>r.json()),
    $('#bili').checked ? fetch(`/api/mv?act=search&q=${encodeURIComponent(q)}&limit=6`).then(r=>r.json()) : Promise.resolve({items:[]}),
  ]);
  const song  = (rSong.status==='fulfilled' && rSong.value.items) || [];
  const art   = (rArtist.status==='fulfilled' && rArtist.value.items) || [];
  const mv    = (rMV.status==='fulfilled' && rMV.value.items) || [];
  const seen = new Set(); last = [];
  const push=(type, arr, map)=>{ (arr||[]).forEach(t=>{
      const k = type+'|'+(t.title||'')+'|'+(t.artists||t.bvid||'');
      if(seen.has(k)) return; seen.add(k); last.push(Object.assign({type}, map(t)));
  });};
  push('song', song, t=>({title:t.title, artists:t.artists, source:t.source, duration:t.duration_s, score:t.score}));
  // 歌手曲去重（与 song 撞车的不再列）
  push('artist', art, t=>({title:t.title, artists:t.artists, source:t.source, duration:t.duration, score:t.score}));
  push('mv', mv, t=>({title:t.title, artists:t.artists, source:'bilibili', duration:t.duration, score:null, bvid:t.bvid, page_url:t.page_url}));
  renderRows(last, true);
  setMsg($('#msg'), `歌曲 ${song.length} · 歌手曲 ${art.length} · MV ${mv.length} · 共 ${last.length} 条（已跨组去重）`);
}
/* 歌手模式：/api/artists，纯歌手名搜索 */
async function doSearchArtist(q){
  setMsg($('#msg'),'按歌手搜「'+q+'」…');
  const d=await (await fetch(`/api/artists?name=${encodeURIComponent(q)}&limit=30`)).json();
  if(d.error){setMsg($('#msg'),'错误: '+d.error,'bad');return;}
  last=(d.items||[]).map(t=>Object.assign({type:'artist'}, t));
  renderRows(last, false);
  const names=[...new Set(last.map(t=>t.artists).filter(Boolean))];
  setMsg($('#msg'),`歌手「${q}」 ${last.length} 首 · 歌手: ${names.slice(0,3).join(' / ')}${names.length>3?' 等'+names.length+'位':''}`);
}
/* 统一表格渲染（带分组标签与按类型下载）；fmtDur 复用统计页已定义的 */
const TYPE_TAG = {song:'曲', artist:'歌手', mv:'MV'};
function renderRows(rows, grouped){
  if(!rows || !rows.length){
    $('#tb').innerHTML = `<tr><td colspan="7">${emptyRows('没有匹配结果','换个关键词，或勾「含B站」扩到三源 / 点下方示例词试搜')}</td></tr>`;
    return;
  }
  $('#tb').innerHTML = rows.map((t,i)=>{
    const tag = grouped ? `<span class="gtag g-${t.type}">${TYPE_TAG[t.type]||''}</span>` : '';
    const isMV = t.type==='mv';
    const score = (t.score===null||t.score===undefined) ? '—'
      : `<span class="sc ${scCls(t.score)}">${Number(t.score).toFixed(2)}</span>`;
    const btn = isMV
      ? `<button class="ghost sm" onclick="dlMV(${i})" title="下载MV" aria-label="下载MV">⬇</button>`
      : `<button class="ghost sm" onclick="dlOne(${i})" title="下载" aria-label="下载">⬇</button>`;
    const pv = isMV ? `<button class="ghost sm" onclick="previewBig(${i})" title="看大图" aria-label="看大图">⛶</button>`
      : `<button class="ghost sm" onclick="previewOne(${i})" title="在线试听" aria-label="在线试听">▶</button>`;
    const fv = `<button class="ghost sm" onclick="favAdd(${i})" title="加入收藏" aria-label="加入收藏">★</button>`;
    return `<tr id="r${i}">
      <td><input type="checkbox" class="rsel" data-i="${i}"></td>
      <td>${i+1}</td><td>${score}</td>
      <td class="n">${fmtDur(t.duration)}</td>
      <td><span class="src ${srcCls(t.source)}">${t.source}</span></td>
      <td>${tag}${esc(t.title)}<div class="n">${esc(t.artists||'-')}${t.bvid?' · '+esc(t.bvid):''}</div></td>
      <td class="rowops">${pv}${fv}${btn}</td></tr>`;
  }).join('');
  $$('#tb .rsel').forEach(c=>c.onchange=()=>markPick(c));
}
function markPick(c){
  const tr = document.getElementById('r'+c.dataset.i);
  if(tr) tr.classList.toggle('picked', c.checked);
  syncSelCount();
}
function pickedIdx(){
  return $$('#tb .rsel').filter(c=>c.checked).map(c=>+c.dataset.i).sort((a,b)=>a-b);
}
function syncSelCount(){
  const n = pickedIdx().length;
  setMsg($('#msg'), n? ('已选 '+n+' 首 · 可「批量下载所选」或「加入收藏」') : '');
}
$('#selall').onclick = ()=>{ $$('#tb .rsel').forEach(c=>{c.checked=true; markPick(c);}); };
$('#selnone').onclick = ()=>{ $$('#tb .rsel').forEach(c=>{c.checked=false; markPick(c);}); };
$('#selallh').onchange = e=>{
  $$('#tb .rsel').forEach(c=>{c.checked=e.target.checked; markPick(c);});
};

/* ---------- 预听（不下载，浏览器直连在线流） ---------- */
let pvAudio = null;
function ensurePvAudio(){
  if(pvAudio) return pvAudio;
  pvAudio = new Audio();
  pvAudio.preload = 'none';
  return pvAudio;
}
async function previewOne(i){
  const t = last[i]; if(!t) return;
  if(t.type==='mv'){ previewBig(i); return; }
  setMsg($('#msg'), '取预听链: '+(t.title||'')+' …');
  try{
    const u = new URL('/api/preview', location.origin);
    u.searchParams.set('q', $('#q').value.trim());
    u.searchParams.set('title', t.title||'');
    u.searchParams.set('artists', t.artists||'');
    u.searchParams.set('sources', $('#bili').checked?'qq,netease,bilibili':'qq,netease');
    const d = await (await fetch(u)).json();
    if(!d.ok){ setMsg($('#msg'), d.log||'取链失败','bad'); return; }
    const a = ensurePvAudio();
    a.crossOrigin = 'anonymous';
    a.src = d.proxy || d.url;   // 走本机代理，绕 CDN 防盗链/跨域
    a.play().catch(()=>{});
    showPvBar(d.title, d.artists);
    /* 缓存反馈双段: 搜索段(search_ms) + 全程(total_ms); 取链命中再标「取链缓存」 */
    let tag = '';
    if(d.search_ms != null){
      tag = (d.cached ? '搜索缓存 ' : '搜索冷查 ')
        + (d.search_ms/1000).toFixed(1)+'s'
        + (d.url_cached ? ' · 取链缓存' : '')
        + ' / 全程 '+(d.total_ms/1000).toFixed(1)+'s';
    }
    setMsg($('#msg'), '正在试听（未下载，仅在线流）: '+d.title+' · '+tag, 'ok');
  }catch(e){ setMsg($('#msg'),'试听失败: '+e,'bad'); }
}
function showPvBar(title, artists){
  let bar = document.getElementById('pvbar');
  if(!bar){
    bar = document.createElement('div');
    bar.className = 'pvbox'; bar.id = 'pvbar';
    bar.innerHTML = '<audio controls style="flex:1;height:38px"></audio>'
      + '<button class="ghost sm" id="pvstop">停</button>';
    $('#msg').insertAdjacentElement('afterend', bar);
    bar.querySelector('#pvstop').onclick = ()=>{
      const au = bar.querySelector('audio');
      if(au){ au.pause(); au.removeAttribute('src'); au.load(); }
      bar.remove();
    };
  }
  const au = bar.querySelector('audio');
  if(au && title) au.title = title + (artists? ' - '+artists : '');
}

/* ---------- 大图灯箱（封面/封面曲库图） ---------- */
async function previewBig(i){
  const t = last[i]; if(!t) return;
  let cover = t.cover_url || '';
  if(!cover && t.title){
    try{
      const r = await (await fetch('/api/lyric-fetch?act=candidates&title='+encodeURIComponent(t.title)
        +'&artist='+encodeURIComponent(t.artists||'')+'&sources=qq,netease&limit=1')).json();
      const c = (r.candidates||[])[0];
      if(c && c.cover_url) cover = c.cover_url;
    }catch(e){}
  }
  const img = $('#lbimg');
  $('#lbcap').textContent = (t.title||'') + (t.artists? ' — '+t.artists : '');
  if(cover){ img.src = cover; $('#lightbox').classList.add('on'); }
  else setMsg($('#msg'),'没找到封面图（候选无 cover_url）','bad');
}
$('#lbclose').onclick = e=>{ e.stopPropagation(); $('#lightbox').classList.remove('on'); };
$('#lightbox').onclick = e=>{ if(e.target.id==='lightbox') $('#lightbox').classList.remove('on'); };
document.addEventListener('keydown', e=>{ if(e.key==='Escape') $('#lightbox').classList.remove('on'); });

/* ---------- 收藏 ---------- */
async function favAdd(i){
  const t = last[i]; if(!t) return;
  try{
    const q = new URLSearchParams({act:'add', title:t.title||'', artists:t.artists||'',
      source:t.source||'', duration:String(t.duration||''), q:$('#q').value.trim(),
      n:String(i+1), rel:t.rel||''});
    const d = await (await fetch('/api/favs?'+q)).json();
    setMsg($('#msg'), (d.added? '★ 已收藏' : '已在收藏里')+'（'+d.count+' 首）','ok');
    favLoad();
  }catch(e){ setMsg($('#msg'),'收藏失败: '+e,'bad'); }
}
$('#bulkdl').onclick = async ()=>{
  const idx = pickedIdx();
  if(!idx.length){ setMsg($('#msg'),'先勾选要下载的曲目','bad'); return; }
  const kw = $('#q').value.trim();
  if(!kw){ setMsg($('#msg'),'搜索词为空','bad'); return; }
  setMsg($('#msg'), '已提交 '+idx.length+' 首下载任务 →「批量」页进度');
  for(const i of idx){
    const t = last[i]; if(!t || t.type==='mv') continue;
    const exact = t.title?('&title='+encodeURIComponent(t.title)+'&artists='+encodeURIComponent(t.artists||'')):'';
    const src = $('#bili').checked?'qq,netease,bilibili':'qq,netease';
    fetch(`/api/get?q=${encodeURIComponent(kw)}&n=${i+1}&force=0&sources=${src}${exact}`)
      .then(r=>r.json()).catch(()=>{});
  }
  loadStat();
};
$('#tofav').onclick = async ()=>{
  const idx = pickedIdx();
  if(!idx.length){ setMsg($('#msg'),'先勾选','bad'); return; }
  const rows = idx.map(i=>last[i]).filter(Boolean).map(t=>({
    title:t.title||'', artists:t.artists||'', source:t.source||'',
    duration:String(t.duration||''), q:$('#q').value.trim(),
  }));
  try{
    const d = await (await fetch('/api/favs?act=add_multi&items='+encodeURIComponent(JSON.stringify(rows)))).json();
    setMsg($('#msg'), '★ 收藏 +'+d.added+'（共 '+d.count+' 首）','ok');
    favLoad();
  }catch(e){ setMsg($('#msg'),'收藏失败: '+e,'bad'); }
};
$('#bysong').onclick = ()=>{
  const q = $('#q').value.trim(); if(!q) return;
  setTab('q');
  const ta = $('#bkws');
  ta.value = (ta.value? ta.value+'\n' : '') + q;
  setMsg($('#msg'),'已加入批量关键词: '+q,'ok');
};

/* ---------- 歌单链接下载（多行 URL，交后端解析为任务） ---------- */
$('#linkgo').onclick = async ()=>{
  const raw = $('#linkin').value.trim(); if(!raw){ setMsg($('#msg'),'粘贴歌单链接','bad'); return; }
  const urls = raw.split(/[\r\n,]+/).map(x=>x.trim()).filter(Boolean);
  const bvRe = /(BV[0-9A-Za-z]{10})/g;
  const bvids = [];
  urls.forEach(u=>{ let m; while((m = bvRe.exec(u))){ if(!bvids.includes(m[1])) bvids.push(m[1]); } });
  const httpUrls = urls.filter(u=>/^https?:\/\//.test(u));
  try{
    // 1) QQ/网易/B站 歌单页（http 链接）
    if(httpUrls.length){
      setMsg($('#msg'),'解析歌单页…（约 3-8 秒）');
      for(const u of httpUrls){
        const r = await (await fetch('/api/plimport?act=parse&url='+encodeURIComponent(u))).json();
        if(!r.ok){ setMsg($('#msg'),'解析失败: '+(r.error||''),'bad'); continue; }
        setMsg($('#msg'), '「'+(r.title||u.slice(0,40))+'」 '+r.count+' 首 · 启动批量下载…','ok');
        const d = await (await fetch('/api/plimport?act=download&url='+encodeURIComponent(u))).json();
        if(!d.ok){ setMsg($('#msg'),'启动失败: '+(d.error||''),'bad'); continue; }
        setTab('q');
        if(typeof subscribe==='function') subscribe(d.job_id, d.total);
      }
      return;
    }
    // 2) 含 BV 的链接（B站视频列表）
    if(!bvids.length){ setMsg($('#msg'),'链接里没有 BV 号或歌单页 URL','bad'); return; }
    setMsg($('#msg'),'已解析 '+bvids.length+' 个 BV，启动歌单下载…');
    const u = new URL('/api/mv', location.origin);
    u.searchParams.set('act','playlist');
    u.searchParams.set('bvids', bvids.join(','));
    const d = await (await fetch(u)).json();
    if(d.error){ setMsg($('#msg'),d.error,'bad'); return; }
    setMsg($('#msg'),'歌单下载已启动（'+d.total+' 个）→「批量」页看进度','ok');
    setTab('q');
    if(typeof subscribe==='function') subscribe(d.job_id, d.total);
  }catch(e){ setMsg($('#msg'),'失败: '+e,'bad'); }
};

/* ---------- 收藏页渲染 ---------- */
async function favLoad(){
  try{
    const d = await (await fetch('/api/favs')).json();
    const items = d.items||[];
    $('#favcount').textContent = '共 '+items.length+' 首';
    window._favItems = items.map(x=>({rel:x.rel||'', title:x.title, artists:x.artists,
      source:x.source, duration:+x.duration||0, q:x.q, n:x.n}));
    if(!items.length){
      $('#favlist').innerHTML = emptyBox('★', '还没有收藏', '在搜索结果或曲库卡片上点 ★ 加入', '收藏跨页保留，刷新不丢');
      return;
    }
    $('#favlist').innerHTML = items.map((x,i)=>`
      <div class="favrow">
        <div class="ftxt">
          <div class="ft1">${esc(x.title||x.rel||'')}</div>
          <div class="ft2">${esc(x.artists||'')} ${x.source? ' · '+esc(x.source):''} ${x.at? ' · '+esc(x.at):''}</div>
        </div>
        <div class="fops">
          <button class="ghost sm" onclick="favPlay(${i})">播放</button>
          <button class="ghost sm" onclick="favDl1(${i})">下载</button>
          <button class="ghost sm" onclick="favDel('${esc(x.key||'')}')" aria-label="移除收藏">✕</button>
        </div>
      </div>`).join('');
  }catch(e){ setMsg($('#favmsg'),'加载失败: '+e,'bad'); }
}
async function favDel(key){
  await fetch('/api/favs?act=remove&key='+encodeURIComponent(key));
  favLoad();
}
function favPlay(i){
  const x = (window._favItems||[])[i];
  if(x && x.rel) play(x.rel, x.title, x.artists, window._favItems, i);
  else setMsg($('#favmsg'),'这一首还没下载，先「下载」');
}
async function favDl1(i){
  const x = (window._favItems||[])[i]; if(!x) return;
  if(x.rel){ setMsg($('#favmsg'),'已在曲库: '+x.rel); return; }
  const q = x.q || x.title || '';
  if(!q){ setMsg($('#favmsg'),'缺关键词','bad'); return; }
  setMsg($('#favmsg'),'下载中: '+(x.title||q)+' …');
  const exact = x.title?('&title='+encodeURIComponent(x.title)+'&artists='+encodeURIComponent(x.artists||'')):'';
  try{
    const d = await (await fetch(`/api/get?q=${encodeURIComponent(q)}&n=${x.n||1}&force=0&sources=qq,netease,bilibili${exact}`)).json();
    setMsg($('#favmsg'), d.log||JSON.stringify(d), d.ok?'ok':'bad');
    if(d.ok) favLoad();
  }catch(e){ setMsg($('#favmsg'),'失败: '+e,'bad'); }
}
async function libAct(act, params){
  const u = new URL('/api/lib', location.origin);
  u.searchParams.set('act', act);
  Object.entries(params||{}).forEach(([k,v])=>u.searchParams.set(k,v));
  return await (await fetch(u)).json();
}
$('#mkdir').onclick = async ()=>{
  const name = prompt('新文件夹名（相对曲库根，如 投稿/我的收藏）：');
  if(!name) return;
  try{
    const r = await libAct('new', {sub:name});
    setMsg($('#bmsg'), r.ok? ('已创建 '+r.rel) : ('创建失败: '+(r.error||'')), r.ok?'ok':'bad');
    if(r.ok){ try{ await _loadChipsOnly(); }catch(e){} if(curSub) openDir(curSub); }
  }catch(e){ setMsg($('#bmsg'),'创建失败: '+e,'bad'); }
};
$('#redir').onclick = async ()=>{
  if(!curSub){ setMsg($('#bmsg'),'先点开一个分类再改名','bad'); return; }
  const nn = prompt('「'+curSub+'」改名为（相对曲库根）：', curSub);
  if(!nn || nn===curSub) return;
  try{
    const r = await libAct('rename', {sub:curSub, new:nn});
    setMsg($('#bmsg'), r.ok? ('已改名 -> '+r.rel) : ('改名失败: '+(r.error||'')), r.ok?'ok':'bad');
    if(r.ok){ curSub=r.rel; try{ await _loadChipsOnly(); }catch(e){} openDir(r.rel); }
  }catch(e){ setMsg($('#bmsg'),'改名失败: '+e,'bad'); }
};
$('#favreload').onclick = favLoad;
$('#favdlall').onclick = async ()=>{
  const items = (window._favItems||[]).filter(x=>!x.rel && (x.q||x.title));
  if(!items.length){ setMsg($('#favmsg'),'收藏里没有待下载项','bad'); return; }
  setMsg($('#favmsg'),'开始下载 '+items.length+' 首…');
  for(const x of items){ await favDl1((window._favItems||[]).indexOf(x)); }
};
$('#favexport').onclick = ()=>{
  const items = window._favItems||[];
  if(!items.length){ setMsg($('#favmsg'),'收藏为空','bad'); return; }
  const lines = ['#EXTM3U'];
  items.forEach(x=>{
    const name = [x.artists, x.title].filter(Boolean).join(' - ');
    lines.push('#EXTINF:'+(Math.round(x.duration||-1))+','+name);
    lines.push(x.rel || ((x.q||x.title||'')+(x.source? ' ('+x.source+')':'')));
  });
  const blob = new Blob([lines.join('\n')], {type:'audio/x-mpegurl'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'favs.m3u8';
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
  setMsg($('#favmsg'),'已导出 '+items.length+' 首 -> favs.m3u8','ok');
};
$('#favexpjson').onclick = ()=>{
  const items = window._favItems||[];
  if(!items.length){ setMsg($('#favmsg'),'收藏为空','bad'); return; }
  const blob = new Blob([JSON.stringify(items, null, 1)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'favs.json';
  a.click();
  setTimeout(()=>URL.revokeObjectURL(a.href), 4000);
  setMsg($('#favmsg'),'已导出 '+items.length+' 首 → favs.json（含关键词/来源/时长，跨设备可还原）','ok');
};
$('#favimp').onclick = ()=>$('#favimpfile').click();
$('#favimpfile').onchange = async (e)=>{
  const f = e.target.files[0]; if(!f) return;
  try{
    const items = JSON.parse(await f.text());
    if(!Array.isArray(items) || !items.length){ setMsg($('#favmsg'),'JSON 里没有曲目数组','bad'); return; }
    const d = await (await fetch('/api/favs', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({act:'import', items})})).json();
    setMsg($('#favmsg'), '导入完成：新增 '+(d.added||0)+'，共 '+d.count+' 首', 'ok');
    favLoad();
  }catch(err){ setMsg($('#favmsg'),'导入失败: '+err,'bad'); }
  e.target.value = '';
};
$('#favclear').onclick = async ()=>{
  if(!confirm('清空收藏歌单？')) return;
  await fetch('/api/favs?act=clear'); favLoad();
};

/* MV 模式：搜 B 站视频当 MV 源，点下载出视频文件 */
async function doSearchMV(q){
  setMsg($('#msg'),'搜 B站 MV 候选…');
  const d=await (await fetch(`/api/mv?act=search&q=${encodeURIComponent(q)}&limit=8`)).json();
  if(d.error){setMsg($('#msg'),'错误: '+d.error,'bad');return;}
  last=(d.items||[]).map(t=>Object.assign({type:'mv'}, t));
  renderRows(last, false);
  setMsg($('#msg'),`B站 MV 候选 ${last.length} 条 · 点「下载MV」存为视频文件`);
}
async function dlMV(i){
  const t=last[i]; if(!t)return;
  setMsg($('#msg'),'启动 MV 下载: '+t.title+' …');
  try{
    const u=new URL('/api/mv',location.origin);
    u.searchParams.set('act','download'); u.searchParams.set('bvid',t.bvid);
    u.searchParams.set('title',t.title); u.searchParams.set('artists',t.artists||'');
    u.searchParams.set('sub','投稿\\B站');
    const d=await (await fetch(u)).json();
    if(d.error){setMsg($('#msg'),'错误: '+d.error,'bad');return;}
    setMsg($('#msg'),'MV 下载已启动，进度在「批量」页任务卡');
    setTab('q');
    if(typeof subscribe==='function') subscribe(d.job_id, 1);   // 复用批量页 SSE 卡片
  }catch(e){setMsg($('#msg'),'失败: '+e,'bad');}
}
async function dlOne(i){
  const q=$('#q').value.trim(); if(!q||!last[i])return;
  const t=last[i];
  if(searchMode==='mv') return dlMV(i);
  if(t.type==='mv') return dlMV(i);
  const f=$('#force').checked?'1':'0';
  setMsg($('#msg'),'下载中: '+(t.title||'')+' …');
  try{
    // 精确标题（歌手模式歌名不在关键词里，靠二次搜索选不准）
    const exact=t.title?`&title=${encodeURIComponent(t.title)}&artists=${encodeURIComponent(t.artists||'')}`:'';
    const src=$('#bili').checked?'qq,netease,bilibili':'qq,netease';
    let d = await (await fetch(`/api/get?q=${encodeURIComponent(q)}&n=${i+1}&force=${f}&sources=${src}${exact}`)).json();
    if(!d.ok){
      // vkey 瞬时抖动（实测 0.1s fail）→ 隔 1.5s 自动重试一次
      setMsg($('#msg'), '首次取链失败，1.5s 后重试…');
      await new Promise(r=>setTimeout(r,1500));
      d = await (await fetch(`/api/get?q=${encodeURIComponent(q)}&n=${i+1}&force=${f}&sources=${src}${exact}`)).json();
    }
    setMsg($('#msg'), d.log||JSON.stringify(d), d.ok?'ok':'bad');
    loadStat();
  }catch(e){setMsg($('#msg'),'失败: '+e,'bad');}
}
$('#go').onclick=doSearch;
$('#q').onkeydown=e=>{if(e.key==='Enter')doSearch();};
$('#top1').onclick=()=>dlOne(0);
/* 搜索模式切换 */
let searchMode = localStorage.getItem('m3_sm') || 'all';
/* 任务跟踪：MV 等后台 job 的进度浮层（挂在批量页日志区） */
function setTab(p){
  const t = document.querySelector(`.tab[data-p="${p}"]`);
  if(t) t.click();
}
let _watchTimer = 0;
const SM_TIP = {
  all:'一次同时搜：歌曲（QQ+网易+B站）+ 歌手曲目 + B站 MV，分组展示',
  song:'歌名模式：自动打分去重，按匹配度排序',
  artist:'歌手模式：纯歌手名搜全部曲目，按歌手命中的排前',
  mv:'MV 模式：搜 B站视频当 MV 源，下载存为 mp4',
};
function applySM(){
  $$('#smode span').forEach(x=>{ const on = x.dataset.sm===searchMode;
    x.classList.toggle('on', on); x.setAttribute('role','radio'); x.setAttribute('aria-checked', on); });
  $('#q').placeholder = searchMode==='all' ? '一个词全搜：晴天 周杰伦'
    : searchMode==='song' ? '歌名 歌手，如：晴天 周杰伦'
    : searchMode==='artist' ? '歌手名，如：周杰伦 / 洛天依'
    : '歌名+MV，如：海阔天空 Beyond MV';
  $('#smodetip').textContent = SM_TIP[searchMode] || '';
  localStorage.setItem('m3_sm', searchMode);
}
$$('#smode span').forEach(x=>x.onclick=()=>{ searchMode=x.dataset.sm; applySM(); });
applySM();

/* ---------- 曲库 ---------- */
let curSub='';
async function _loadChipsOnly(){
  const d=await (await fetch('/api/ls')).json();
  $('#chips').innerHTML=(d.dirs||[]).map(x=>
    `<span class="chip" data-n="${esc(x.name)}" onclick="openDir('${esc(x.name)}')">${esc(x.name)} <span class="n">${x.count}</span></span>`).join('');
  chipsRefreshActive();
}
async function loadChips(){
  const d=await (await fetch('/api/ls')).json();
  $('#chips').innerHTML=(d.dirs||[]).map(x=>
    `<span class="chip" data-n="${esc(x.name)}" onclick="openDir('${esc(x.name)}')">${esc(x.name)} <span class="n">${x.count}</span></span>`).join('');
}
/* loadChips 只负责渲染分类片，绝不再回调 openDir（死循环抖动根因）。
   当前分类的高亮由 openDir 里的 chipsRefreshActive() 就地更新。 */
function chipsRefreshActive(){
  $$('#chips .chip').forEach(el=>{
    const nm = el.textContent.replace(/\s*\d+\s*$/,'').trim();
    el.classList.toggle('on', nm === curSub || el.dataset.n === curSub);
  });
}
/* 分批渲染：500 首一次性 innerHTML 会卡 1~2 秒，
   改成每批 60 条 + IntersectionObserver 滚到底就续下一批 */
const BATCH = 60;
let _renderJob = null;
let viewMode = localStorage.getItem('m3_view') || 'grid';

function applyViewMode(m){
  viewMode = m;
  localStorage.setItem('m3_view', m);
  $$('.vtog span').forEach(s=>s.classList.toggle('on', s.dataset.v===m));
  const g = $('#grid');
  g.className = (m==='list') ? 'listview' : 'grid';
  if(_renderJob) drawMoreBatch();
}
$$('.vtog span').forEach(s=>s.onclick=()=>applyViewMode(s.dataset.v));

function renderGridBatch(items, sub){
  const grid = $('#grid');
  grid.innerHTML = '';
  grid.className = (viewMode==='list') ? 'listview' : 'grid';
  window._curList = items;
  let shown = 0;

  const sentinel = document.createElement('div');
  sentinel.id = 'gsentinel';
  sentinel.style.cssText = 'height:1px;width:100%';

  _renderJob = {sub: sub||'_', items, sentinel, get shown(){return shown;},
                set shown(v){shown=v;}};

  window.drawMoreBatch = function(){
    const end = Math.min(shown + BATCH, items.length);
    const frag = document.createDocumentFragment();
    for(let i=shown;i<end;i++){
      const t = items[i];
      if(viewMode === 'list'){
        const row = document.createElement('div');
        row.className = 'lrow';
        row.innerHTML = `
          <div class="lcov" data-rel="${esc(t.rel)}">♪</div>
          <div class="ltxt">
            <div class="lt1">${esc(t.title||t.rel.split(/[\\\\/]/).pop())}</div>
            <div class="lt2">${esc(t.artists||'')}</div>
          </div>
          <div class="lsz">${t.size!==undefined?mb(t.size):''}</div>`;
        row.onclick = ()=>play(t.rel, t.title, t.artists, items, i);
        frag.appendChild(row);
      }else{
        const div = document.createElement('div');
        div.className = 'card';
        div.innerHTML = `
          <div class="cardcov" data-rel="${esc(t.rel)}">♪</div>
          <div class="cardbody">
            <div class="cardtitle">${esc(t.title||t.rel.split(/[\\\\/]/).pop())}</div>
            <div class="cardartist">${esc(t.artists||'')}${t.size!==undefined?' · '+mb(t.size):''}</div>
          </div>
          <div class="cardops">
            <button class="cop" title="改名" data-act="ren" aria-label="改名">✎</button>
            <button class="cop" title="删除" data-act="del" aria-label="删除">×</button>
          </div>`;
        div.querySelectorAll('.cop').forEach(b=>{
          b.onclick = (ev)=>{ ev.stopPropagation();
            b.dataset.act==='del' ? trkDelete(t.rel, t.title) : trkRename(t.rel, t); };
        });
        div.onclick = ()=>play(t.rel, t.title, t.artists, items, i);
        frag.appendChild(div);
      }
    }
    if(sentinel.parentNode) sentinel.remove();
    grid.appendChild(frag);          // 子节点迁入 grid 后 frag 变空
    shown = end;
    if(shown < items.length) grid.appendChild(sentinel);
    loadCoversFor(grid);             // 必须观察 grid：frag 此时已空（原 loadCoversFor(frag) 恒 0 张 → 封面全 ♪）
    setMsg($('#bmsg'), `${sub||'结果'} · 已显示 ${shown}/${items.length}`);
  };

  window.drawMoreBatch();

  if('IntersectionObserver' in window && !window._gridIO){
    window._gridIO = new IntersectionObserver((es)=>{
      if(es.some(e=>e.isIntersecting) && window.drawMoreBatch) window.drawMoreBatch();
    }, {rootMargin:'320px'});
  }
  if(window._gridIO){
    const watch = ()=>{
      const s = document.getElementById('gsentinel');
      if(s && !s._observed){ s._observed = true; window._gridIO.observe(s); }
    };
    watch();
    if(!window._gridMO){
      window._gridMO = new MutationObserver(watch);
      window._gridMO.observe(grid, {childList:true});
    }
  }
}

let _covIO = ('IntersectionObserver' in window)
  ? new IntersectionObserver(es=>{
      es.forEach(e=>{ if(e.isIntersecting){ _loadOne(e.target); _covIO.unobserve(e.target); } });
    }, {rootMargin:'200px'}) : null;
function _loadOne(el){
  const rel = el.dataset.rel; if(!rel || el.dataset.done) return;
  el.dataset.done = '1';
  fetch('/api/cover?rel='+encodeURIComponent(rel)).then(r=>{
    if(r.ok) return r.blob(); throw 0;
  }).then(b=>{
    el.innerHTML = '<img loading="lazy" src="'+URL.createObjectURL(b)+'" alt="">';
  }).catch(()=>{ el.dataset.done=''; });
}
function loadCoversFor(container){
  container.querySelectorAll('.cardcov,.lcov').forEach(el=>{
    if(!el.dataset.rel) return;
    if(_covIO) _covIO.observe(el); else _loadOne(el);
  });
}

async function trkDelete(rel, title){
  if(!confirm('删除《'+(title||rel)+'》？（先 dry 预览，确认才真删）')) return;
  try{
    let r = await (await fetch('/api/track?act=delete&rel='+encodeURIComponent(rel)+'&dry=1')).json();
    setMsg($('#bmsg'),'将删除: '+(r.removed||[]).join(', ')||'无','bad');
    if(!confirm('确认真删？文件将移到回收站外的永久删除。')) return;
    r = await (await fetch('/api/track?act=delete&rel='+encodeURIComponent(rel)+'&dry=0')).json();
    setMsg($('#bmsg'), r.ok? '已删除 1 首' : '删除失败', r.ok?'ok':'bad');
    if(r.ok && curSub) openDir(curSub);
  }catch(e){ setMsg($('#bmsg'),'删除失败: '+e,'bad'); }
}
async function trkRename(rel, t){
  const cur = t.title||rel.split(/[\\/]/).pop();
  let nn = prompt('新文件名（含 .mp3）：', cur);
  if(!nn) return;
  if(!/\.mp3$/i.test(nn)) nn += '.mp3';
  if(/[\\/:*?"<>|]/.test(nn.replace(/\.mp3$/i,''))){ setMsg($('#bmsg'),'含非法字符 : * ? " < > |','bad'); return; }
  try{
    const r = await (await fetch('/api/track?act=rename&rel='+encodeURIComponent(rel)+'&new='+encodeURIComponent(nn))).json();
    setMsg($('#bmsg'), r.ok? '已改名 → '+r.rel : ('改名失败: '+(r.error||'')), r.ok?'ok':'bad');
    if(r.ok && curSub) openDir(curSub);
  }catch(e){ setMsg($('#bmsg'),'改名失败: '+e,'bad'); }
}
function skGrid(n){
  const g=$('#grid');
  g.className='skg';
  g.innerHTML = Array.from({length:n},()=>'<div class="skc"><div class="a sk"></div><div class="b sk"></div><div class="c sk"></div></div>').join('');
}
function skTable(n){
  $('#tb').innerHTML = Array.from({length:n},()=>'<tr><td colspan="7"><div class="sk skrow"></div></td></tr>').join('');
}
function emptyBox(icon, title, sub, hint, acts){
  return `<div class="empty">
    <div class="eic">${icon}</div>
    <div class="et">${esc(title)}</div>
    <div class="es">${esc(sub)}</div>
    ${hint?`<div class="eh">${esc(hint)}</div>`:''}
    ${acts?`<div class="eact">${acts}</div>`:''}
  </div>`;
}
const PAGE = 400;               // 曲库分页：每页 400，触底续拉（归档 4708 全可见）
let _libTotal = 0;
async function _libPage(sub, offset){
  const d = await (await fetch(`/api/ls?sub=${encodeURIComponent(sub)}&limit=${PAGE}&offset=${offset}&id3=1`)).json();
  return {items: d.items||[], got: (d.items||[]).length, dirs: d.dirs||[]};   // dirs 必须透传, 否则 subDirs 恒 null 下钻不画
}
function renderCrumbs(sub){
  const el = $('#crumbs'); if(!el) return;
  if(!sub){ el.innerHTML = '<span class="n">全部目录</span>'; return; }
  const parts = String(sub).split(/[\\/]+/).filter(Boolean);
  let acc = '';
  const seg = parts.map((p,i)=>{
    acc = acc ? acc + '\\' + p : p;
    const raw = acc, last = (i === parts.length-1);
    return (i? '<span class="cs">›</span>' : '') +
      (last ? `<b class="cb cur">${esc(p)}</b>`
            : `<a class="cb" href="javascript:void(0)" onclick="openDir('${esc(raw)}')">${esc(p)}</a>`);
  }).join('');
  el.innerHTML = '<a class="cb" href="javascript:void(0)" onclick="openDir(\'\')">曲库</a>' + seg;
}
async function openDir(sub, keepScroll){
  const same = (curSub===sub);
  curSub=sub;
  renderCrumbs(sub);
  _libTotal = 0;
  // 分类片缺失才拉；已有则只地高亮 —— 不再 loadChips(它会重画全表)
  if(!document.querySelector('#chips .chip')) { try{ await _loadChipsOnly(); }catch(e){} }
  else chipsRefreshActive();
  setMsg($('#bmsg'),'加载中…'); if(!keepScroll) skGrid(12);   // 骨架替代空白
  try{
    // 分页拉满：每页 400 顺序续拉，直到拿完（后端 offset 分页已验证）
    let items = [], off = 0, subDirs = null;
    while(true){
      const pg = await _libPage(sub, off);
      items = items.concat(pg.items);
      if(off === 0) subDirs = pg.dirs || [];
      if(pg.got < PAGE) break;
      off += pg.got;
      setMsg($('#bmsg'), sub+' · 已加载 '+items.length+' 首…');
      if(off > 8000) break;      // 安全阀
    }
    /* 子目录下钻: 首轮 dirs 重画 chips(+返回上级); 根层由 loadChips 管 */
    if(subDirs && subDirs.length){
      $('#chips').innerHTML =
        '<span class="chip" data-n="" onclick="openDir(\'\')">⤴ 返回上级</span>' +
        subDirs.map(x=>
          `<span class="chip" data-n="${esc(sub?sub+'\\'+x.name:x.name)}" onclick="openDir('${esc(sub?sub+'\\'+x.name:x.name)}')">${esc(x.name)} <span class="n">${x.count}</span></span>`).join('');
    }
    _libTotal = items.length;
    if(!items.length){
      $('#grid').innerHTML = emptyBox('♪', '这个分类还没有歌曲',
        '先用「搜索」页搜一首下载，或点上面的分类片换一个。',
        '已下载的文件会按来源自动归到 投稿/ 下的子目录',
        '<button class="ghost sm" onclick="setTab(\'s\')">去搜索</button>');
      setMsg($('#bmsg'),'空分类'); return;
    }
    renderGridBatch(items, sub);
    setMsg($('#bmsg'), sub+' · 共 '+items.length+' 首');
  }catch(e){setMsg($('#bmsg'),'失败: '+e,'bad');}
}
$('#reload').onclick=loadChips;
$('#fq').onkeydown=e=>{if(e.key==='Enter')doFind();};
$('#fgo').onclick=doFind;
async function doFind(){
  const q=$('#fq').value.trim(); if(!q)return;
  try{
    const d=await (await fetch(`/api/find?q=${encodeURIComponent(q)}&limit=200`)).json();
    const items=(d.items||[]).map(t=>({rel:t.rel, title:t.name, artists:'', size:t.size}));
    renderGridBatch(items, '命中');
  }catch(e){setMsg($('#bmsg'),'失败: '+e,'bad');}
}

/* ---------- 统计 ---------- */
let stBy = 'count';
let stTab = 'songs';   // songs | artists
let stData = [];

function fmtDur(s){
  s = Math.round(s||0);
  const h = Math.floor(s/3600), m = Math.floor((s%3600)/60), sec = s%60;
  if(h) return h+'h'+m+'m';
  if(m) return m+'m'+sec+'s';
  return sec+'s';
}

async function stLoad(){
  setMsg($('#stmsg'),'加载中…');
  try{
    const sum = await (await fetch('/api/stats')).json();
    $('#stcards').innerHTML = `
      <div class="statcard"><div class="k">总播放</div><div class="v">${sum.total_plays||0}<span class="u">次</span></div></div>
      <div class="statcard"><div class="k">累计时长</div><div class="v">${fmtDur(sum.total_seconds)}</div></div>
      <div class="statcard"><div class="k">不重复曲目</div><div class="v">${sum.unique_songs||0}<span class="u">首</span></div></div>
      <div class="statcard"><div class="k">不重复歌手</div><div class="v">${sum.unique_artists||0}<span class="u">位</span></div></div>`;
    $('#sttabs').innerHTML = `
      <span class="chip ${stTab==='songs'?'on':''}" onclick="stSetTab('songs')">曲目排行</span>
      <span class="chip ${stTab==='artists'?'on':''}" onclick="stSetTab('artists')">歌手排行</span>`;
    await stTable();
    setMsg($('#stmsg'), sum.total_plays ? '' : '还没有播放记录，播满 30 秒就会记录');
  }catch(e){ setMsg($('#stmsg'),'失败: '+e,'bad'); }
}
async function stTable(){
  try{
    const u = (stTab==='artists')
      ? '/api/stats?act=artists&limit=50'
      : `/api/stats?act=top&by=${stBy}&limit=50`;
    const d = await (await fetch(u)).json();
    stData = d.items||[];
    if(stTab==='artists'){
      $('#sttb').innerHTML = stData.map((x,i)=>`<tr>
        <td>${i+1}</td><td>${esc(x.artists)}</td>
        <td class="sc hi">${x.count}</td><td class="n">${fmtDur(x.seconds)}</td><td></td></tr>`).join('');
    }else{
      $('#sttb').innerHTML = stData.map((x,i)=>`<tr>
        <td>${i+1}</td>
        <td>${esc(x.title||x.rel.split(/[\\\\/]/).pop())}<div class="n">${esc(x.artists||'')}</div></td>
        <td class="sc hi">${x.count}</td><td class="n">${fmtDur(x.seconds)}</td>
        <td><button class="ghost sm" onclick="stPlay(${i})">播放</button></td></tr>`).join('');
    }
  }catch(e){}
}
function stSetTab(t){ stTab=t; stLoad(); }
function stPlay(i){
  const x = stData[i]; if(!x) return;
  play(x.rel, x.title, x.artists);
}
$$('.vtog span[data-sv]').forEach(s=>s.onclick=()=>{
  $$('.vtog span[data-sv]').forEach(x=>x.classList.remove('on'));
  s.classList.add('on'); stBy = s.dataset.sv; stTable();
});
$('#streload').onclick = stLoad;
$('#stclear').onclick = async()=>{
  if(!confirm('清空全部播放统计？')) return;
  await fetch('/api/stats?act=clear');
  stLoad();
};

/* ---------- 库健康检查 ---------- */
async function doHealth(){
  const deep = $('#hdeep').checked;
  const sub = curSub || '';
  const HB = 400;   // 分批大小：每片 400 首，避免 136s 单请求挂死
  setMsg($('#hmsg2'), deep ? '深度扫描分批中（读 ID3，每片 400 首）…' : '扫描中…');
  $('#hresult').innerHTML = '';
  try{
    // —— 分批循环拉取并聚合 ——
    let off = 0, d = null, acc = {}, accDetail = {}, accSize = 0, doneTotal = 0, parts = [];
    let round = 0, t0 = Date.now();
    while(true){
      round++;
      const u = `/api/health?deep=${deep?1:0}&sub=${encodeURIComponent(sub)}&offset=${off}&batch=${HB}`;
      const part = await (await fetch(u)).json();
      if(part.error){ setMsg($('#hmsg2'), '错误: '+part.error, 'bad'); return; }
      d = part; parts.push(part);
      // 聚合 summary / detail
      for(const [k,v] of Object.entries(part.summary||{})){
        if(k==='重复') { acc[k] = v; continue; }   // 后端每片给全库真值 -> 覆盖(累加 13 片=44122 假数)
        acc[k] = (acc[k]||0) + v;
      }
      for(const [k,arr] of Object.entries(part.detail||{})){
        if(k==='dups'){ accDetail[k] = arr; continue; }   // dups 后端每片给全库真值 -> 覆盖
        (accDetail[k] = accDetail[k]||[]).push(...(arr||[]));
      }
      accSize += part.total_size_mb||0;
      doneTotal += part.total||0;
      const elapsed = Math.round((Date.now()-t0)/1000);
      if(part.more){
        setMsg($('#hmsg2'),
          `扫描进度 ${doneTotal}/${part.total_all} 首（${elapsed}s，片${round}，本片健康分 ${part.score}）…`);
        off += HB;
        continue;
      }
      break;
    }
    // 按累计英文 counts 重算全库分（acc 是中文键 summary，取英文键恒 0 -> 会算成 100，必须用 counts）
    const T = Math.max(1, d.total_all || doneTotal);
    const cc = {};
    for(const part2 of parts) for(const [k,v] of Object.entries(part2.counts||{})){
      if(k==='dups') continue;      // dups 后端每片给全库真值 -> 取末片，累加会翻倍
      cc[k]=(cc[k]||0)+v;
    }
    cc.dups = ((parts[parts.length-1]||{}).counts||{}).dups || 0;
    const _pen = (cc.bad_name||0)/T*30 + (cc.tiny||0)/T*25
      + (cc.dups||0)/T*20 + (cc.no_artist||0)/T*10
      + (cc.no_lyric ? cc.no_lyric/T*15 : 0);
    const sc2 = Math.max(0, Math.round((100 - _pen)*10)/10);
    d = Object.assign({}, d, {
      total: d.total_all || doneTotal,
      summary: acc,
      detail: accDetail,
      total_size_mb: Math.round(accSize*10)/10,
      score: sc2,
    });
    const sc = d.score;
    const cls = sc>=90?'ok':(sc>=70?'':'bad');
    setMsg($('#hmsg2'),
      `共 ${d.total} 首 / ${d.total_size_mb} MB · 健康分 ${sc}/100${d.deep?'（深度·分批完成）':'（快速）'}`, cls);
    /* 健康分 hero(破格1处): 全库核心指标给超大数字 + 小标签(前端准则:大数字配小标签) */
    const heroCls = sc>=90?'hero-ok':(sc>=70?'hero-mid':'hero-bad');
    const heroHTML = `<div class="healthhero ${heroCls}" role="img" aria-label="全库健康分 ${sc} 分（满分 100）">
      <div class="hk">全库健康分</div>
      <div class="hv"><b>${sc}</b><span class="hden">/100</span></div>
      <div class="hmeta">${d.deep?'深度扫描':'快速扫描'} · ${d.total} 首 · ${d.total_size_mb} MB</div>
    </div>`;
    // 卡片
    const cards = Object.entries(d.summary||{}).map(([k,v])=>
      `<div class="statcard"><div class="k">${esc(k)}</div><div class="v" style="${v?'color:var(--warn);-webkit-text-fill-color:var(--warn)':''}">${v}</div></div>`
    ).join('');
    // 明细
    const blocks = [];
    for(const k in (d.detail||{})) if(Array.isArray(d.detail[k]) && d.detail[k].length>60) d.detail[k]=d.detail[k].slice(0,60);
    window._healthNoCover = (d.detail && d.detail.no_cover) || [];
  window._healthNoLyric = (d.detail && d.detail.no_lyric) || [];
  window._health = d;   // 补歌词/补封面按钮共用这份明细
    const LABEL = {no_lyric:'缺歌词', no_cover:'无封面', bad_name:'命名异常',
                   no_artist:'无歌手', tiny:'文件过小', huge:'文件过大', dups:'重复'};
    for(const k in LABEL){
      const arr = (d.detail||{})[k] || [];
      if(!arr.length) continue;
      const rows = arr.map(x=>{
        if(k==='dups') return `<div class="mono">${esc(x.key)}<br>&nbsp;&nbsp;A: ${esc(x.a||'')}<br>&nbsp;&nbsp;B: ${esc(x.b||'')}</div>`;
        if(k==='bad_name') return `<div class="mono">${esc(x.rel||'')} <span class="n">(${esc(x.why||'')})</span></div>`;
        if(k==='tiny'||k==='huge') return `<div class="mono">${esc(x.rel||'')} <span class="n">${x.size||x.duration||''}</span></div>`;
        return `<div class="mono">${esc(x.rel||'')}</div>`;
      }).join('');
      blocks.push(`<div class="jobcard"><div class="jobtitle" style="margin-bottom:6px">${LABEL[k]} (${arr.length})</div>${rows}</div>`);
    }
    $('#hresult').innerHTML = heroHTML + `<div class="statgrid">${cards}</div>` + blocks.join('');
  }catch(e){ setMsg($('#hmsg2'), '失败: '+e, 'bad'); }
}
$('#hscan').onclick = doHealth;

/* 对健康检查里「缺歌词」列表逐首补歌词（同 hfixcover 模式） */
$('#hfixlyric').onclick = async ()=>{
  const list = (window._healthNoLyric = window._healthNoLyric || []);
  const full = (window._health && window._health.detail && window._health.detail.no_lyric) || [];
  const arr = list.length ? list : full;
  if(!arr.length){ setMsg($('#hmsg2'), '先跑一次健康检查，才有「缺歌词」列表', 'bad'); return; }
  if(!confirm('对 '+arr.length+' 首逐首联网补歌词？（约 '+Math.ceil(arr.length*0.7)+'s，实测 0.64s/首）')) return;
  const _t0 = Date.now();
  let ok=0, miss=0; const why={};
  for(let i=0;i<arr.length;i++){
    const rel = arr[i];
    setMsg($('#hmsg2'), `补歌词 ${i+1}/${arr.length} · 成功${ok} 失败${miss} · ${String(rel).split(/[\\/]/).pop()}`);
    try{
      const r = await (await fetch(`/api/lyric-fetch?act=fill&rel=${encodeURIComponent(rel)}&write=1`)).json();
      if(r.ok){ ok++; }
      else { miss++; const w=(r.msg||'未知').replace(/（.*/,'').slice(0,14); why[w]=(why[w]||0)+1; }
    }catch(e){ miss++; why['网络异常']=(why['网络异常']||0)+1; }
  }
  const _s = Math.round((Date.now()-_t0)/1000);
  const whyTxt = Object.entries(why).sort((a,b)=>b[1]-a[1]).map(([k,v])=>`${k}×${v}`).join(' · ');
  setMsg($('#hmsg2'), `补歌词完成：成功 ${ok} / 失败 ${miss}（${_s}s，${(arr.length/Math.max(1,_s)).toFixed(1)} 首/s）` + (whyTxt?' — '+whyTxt:''), ok ? 'ok' : 'bad');
};

/* 对健康检查里「无封面」列表逐首补封面 */
$('#hfixcover').onclick = async()=>{
  const list = (window._healthNoCover || []);
  if(!list.length){
    setMsg($('#hmsg2'), '先跑一次深度健康检查，才有「无封面」列表', 'bad');
    return;
  }
  const btn = $('#hfixcover');
  btn.disabled = true;
  const _t0 = Date.now();
  let ok = 0, miss = 0;
  for(let i=0;i<list.length;i++){
    const rel = list[i].rel;
    setMsg($('#hmsg2'), `补封面 ${i+1}/${list.length} · 成功${ok} 失败${miss} · ${rel.split(/[\\\\/]/).pop()}`);
    try{
      const d = await (await fetch('/api/coverfill?rel='+encodeURIComponent(rel)+'&write=1')).json();
      if(d.ok && d.bytes) ok++; else if(d.ok) miss++;  // ok 但 bytes=0（已内嵌/embedded）不计成功也不算失败
      else miss++;
    }catch(e){ miss++; }
  }
  btn.disabled = false;
  const _s = Math.round((Date.now()-_t0)/1000);
  setMsg($('#hmsg2'), `补封面完成：成功 ${ok} / 失败 ${miss}（${_s}s，${(list.length/Math.max(1,_s)).toFixed(1)} 首/s）`, ok ? 'ok' : 'bad');
  doHealth();   // 重扫
};

/* ID3 双缺批量修复：dry 预览 → 确认 → 写回 TIT2/TPE1 */
$('#hfixmeta').onclick = async ()=>{
  const HB = 500;  // 每片 500 首（全库读 ID3 分批，避免单请求 >120s 超时）
  /* 快估先行: 500 采样外推(首片读ID3 ~3-30s)。估 0 -> 直接收尾, 不跑 ~236s 全扫; 估 >0 -> 确认精确全扫 */
  try{
    setMsg($('#hmsg2'), '快速估算（500 采样外推）…');
    const e = await (await fetch(`/api/fixmeta?dry=1&offset=0&batch=${HB}&estimate=1`)).json();
    if(e.error){ setMsg($('#hmsg2'), '错误: '+e.error, 'bad'); return; }
    const est = e.todo_est || 0;
    if(!est){
      setMsg($('#hmsg2'), `估算：没有 ID3 双缺曲目（500 采样外推 0 / ${e.total_all} 首 · ${e.sample_seconds}s）`, 'ok');
      return;
    }
    const mins = Math.max(1, Math.round((e.total_all / 500) * e.sample_seconds / 60));
    if(!confirm(`估算约 ${est} 首 ID3 双缺（500 采样外推 / ${e.total_all} 首）。\n精确全扫约需 ${mins} 分钟（逐首读 ID3）。开始？`)) return;
  }catch(err){ setMsg($('#hmsg2'),'估算失败: '+err,'bad'); return; }
  setMsg($('#hmsg2'), '扫描 ID3 双缺（分批 500/片）…');
  let off=0, todo=0, scanned=0, total=0, ex='', d=null;
  try{
    while(true){
      d = await (await fetch(`/api/fixmeta?dry=1&offset=${off}&batch=${HB}`)).json();
      if(d.error){ setMsg($('#hmsg2'), '错误: '+d.error, 'bad'); return; }
      scanned += d.scanned; todo += d.todo; total = d.total_all;
      if(!ex && (d.items||[]).length) ex = d.items.slice(0,5).map(x=>x.title+' ← '+x.artist).join(' | ');
      if(!d.more) break;
      off += HB;
      setMsg($('#hmsg2'), `扫描进度 ${scanned}/${total} · 待修 ${todo}…`);
    }
  }catch(e){ setMsg($('#hmsg2'), '扫描失败: '+e, 'bad'); return; }
  if(!todo){ setMsg($('#hmsg2'), '没有 ID3 双缺曲目（全扫 '+scanned+' 首）', 'ok'); return; }
  if(!confirm('扫描 '+scanned+' 首，发现 '+todo+' 首 ID3 双缺。\n写入（歌名←文件名，歌手←父目录）：\n'+ex+'\n\n确认写入？')) return;
  setMsg($('#hmsg2'), '写入 '+todo+' 首 ID3…');
  let written=0, wtodo=0;
  try{
    off=0;
    while(true){
      const r = await (await fetch(`/api/fixmeta?dry=0&offset=${off}&batch=${HB}`)).json();
      written += r.written; wtodo += r.todo;
      if(!r.more) break;
      off += HB;
      setMsg($('#hmsg2'), `写入进度 ${off}/${total} · 已修 ${written}…`);
    }
    setMsg($('#hmsg2'), '修ID3完成：扫描 '+scanned+' · 修复 '+written+'/'+wtodo+' 首', written?'ok':'bad');
  }catch(e){ setMsg($('#hmsg2'), '失败: '+e, 'bad'); }
};

/* 数字滚动: 仅维护统计 5 卡的一次编排(前端准则—动效只留一处回应"值已载入"); reduced-motion 直接落值 */
function countUp(el, to, ms){
  to = +to || 0;
  const reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce || !to || ms<=0){ el.textContent = to; return; }
  const t0 = performance.now();
  const step = (t)=>{
    const k = Math.min(1, (t - t0) / ms);
    const e = 1 - Math.pow(1 - k, 3);          // ease-out cubic
    el.textContent = Math.round(to * e);
    if(k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
/* ---------- 维护守护 ---------- */
/* 浮层 toast: 跑到全库完成等关键回执, 右下角 4s 自动消 */
function _toast(msg, kind){
  let t=document.getElementById('__toast__');
  if(!t){ t=document.createElement('div'); t.id='__toast__';
    t.style.cssText='position:fixed;right:16px;bottom:16px;z-index:9999;max-width:320px;padding:10px 14px;border-radius:6px;font-size:13px;box-shadow:0 2px 10px rgba(0,0,0,.15);display:flex;align-items:center;gap:8px';
    document.body.appendChild(t); }
  const col = kind==='ok' ? 'var(--ok)' : (kind==='bad' ? 'var(--bad)' : 'var(--acc)');
  t.style.background='#fff'; t.style.color=col; t.style.borderColor=col; t.style.border='1px solid '+col;
  t.textContent=msg; t.style.opacity='1';
  clearTimeout(t.__tt__);
  t.__tt__=setTimeout(()=>{ t.style.opacity='0'; t.style.transition='opacity .4s'; setTimeout(()=>{ t.textContent=''; },400); }, 4000);
}
async function mtRun(){
  const btn = $('#mtrun');
  btn.disabled = true;
  const b = +$('#mtbatch').value || 20;
  const sub = curSub || '';
  const t0 = Date.now();
  const FULL = $('#mtfull').checked;   /* 跑到全库: 循环到 done(忽略 N) */
  const N = FULL ? 999999 : Math.max(1, Math.min(50, +$('#mtruns').value || 1));
  /* 跑中 spinner: 按钮文字加转圈, 反馈不空等 */
  const _lab = btn.textContent;
  const _spin = '<span class="spin" style="display:inline-block;width:11px;height:11px;border:2px solid var(--line);border-top-color:var(--acc);border-radius:50%;margin-right:6px;vertical-align:-1px;animation:spin .7s linear infinite"></span>';
  let ticks=0;
  const setSpin=(i)=>{ btn.innerHTML = _spin + (FULL ? `跑到全库 第 ${i} 轮…` : (N>1 ? `连跑 ${i}/${N}…` : '跑中…')); };
  let doneMsg='';
  let FULL_DONE=false;
  let ticksFirstMs=0;
  try{
    for(let i=1;i<=N;i++){
      setSpin(i);
      const _elapsed=Math.round((Date.now()-t0)/100)/10;
      /* 跑到全库: 首 tick 实测后外推预估(首 tick 冷启动, 实测 perTick) */
      let estTxt='';
      if(FULL && i>1){
        const perTick = Math.max(0.5, _elapsed/(i-1)); // 前 i-1 个 tick 平均
        const totalTicks = Math.ceil(5188 / b);
        estTxt = ` · 已 ${_elapsed}s / 预计约 ${Math.max(1,Math.round(perTick*(totalTicks-i+1)/60))} 分钟剩`;
      } else if(FULL && i===1 && ticksFirstMs>0){
        const totalTicks = Math.ceil(5188 / b);
        estTxt = ` · 预计全库约 ${Math.max(1,Math.round(ticksFirstMs/1000*totalTicks/60))} 分钟`;
      }
      setMsg($('#mtmsg'), `${FULL?'跑到全库 · 第 '+i+' 轮':'跑第 '+i+'/'+N+' 轮'}（每轮 ${b} 首${sub?' · '+sub:''}）… 已耗时 ${_elapsed}s${estTxt}`);
      const u = `/api/maintain?act=tick&batch=${b}&sub=${encodeURIComponent(sub)}`
        + `&lyric=${$('#mtlyric').checked?1:0}`
        + `&cover=${$('#mtcover').checked?1:0}`
        + `&clean=${$('#mtclean').checked?1:0}`;
      const _t1=Date.now();
      const r = await (await fetch(u)).json();
      if(i===1){ ticksFirstMs = Date.now()-_t1; }
      if(r.error){ setMsg($('#mtmsg'), `第 ${i} 轮错误: ${r.error}`, 'bad'); return; }
      ticks=i;
      doneMsg = `第 ${i} 轮：扫描 ${r.scanned} 首 · 歌词 +${r.lyric_ok}/-${r.lyric_miss} · 封面 +${r.cover_ok}/-${r.cover_miss} · 清理 ${r.cleaned}` + (r.done ? ' · 已跑完一圈' : '');
      if(r.done){ if(FULL){ setMsg($('#mtmsg'), `跑到全库完成 · 共 ${i} 轮 · `+doneMsg, 'ok'); _toast('跑到全库完成 · 共 '+i+' 轮 · 已挂自动刷看 9 卡', 'ok'); if(typeof _mtAutoRefTimer==='undefined'||_mtAutoRefTimer===null){ if(typeof mtAutoRef==='function') mtAutoRef(); } FULL_DONE=true; break; } if(i<N){ doneMsg += '（下一圈）'; } }
    }
    if(!(FULL_DONE || doneMsg)) setMsg($('#mtmsg'), (N>1?`连跑 ${N} 轮完成 · `:'') + doneMsg, 'ok');
    /* 本批补了什么即时回显(拉 maintain status recent 最新几条, 不等 5 卡重拉) */
    try{
      const st2 = await (await fetch('/api/maintain')).json();
      const rc = (st2.recent||[]).slice(0,3);
      if(rc.length){
        const ago=(t)=>{ if(!t) return ''; const s=(Date.now()/1000 - t); if(s<60) return '刚刚'; if(s<3600) return Math.round(s/60)+' 分钟前'; if(s<86400) return Math.round(s/3600)+' 小时前'; return Math.round(s/86400)+' 天前'; };
        let el = $('#mtlast');
        if(!el){ el = document.createElement('div'); el.id='mtlast'; el.className='n'; el.style.cssText='margin-top:4px;font-size:12px;color:var(--dim)'; $('#mtmsg').insertAdjacentElement('afterend', el); }
        el.innerHTML = '本批补: ' + rc.map(x=>(x.what==='lyric'?'歌词':'封面')+' <a href="javascript:void(0)" data-jn="'+esc(x.name)+'" style="color:var(--acc);text-decoration:underline">'+esc(x.name)+'</a><span style="color:var(--dim)">（'+ago(x.at)+'）</span>').join(' · ');
        el.querySelectorAll('a[data-jn]').forEach(a=>{ a.onclick=()=>{ location.hash='#/lib'; const q=(window._findInput||document.querySelector('#findq')); if(q){ q.value=a.dataset.jn; } history.replaceState(null,'','#lib'); if(window._libLoad) window._libLoad(); }; });
      }
    }catch(e){}
    await mtStat();
  }catch(e){ setMsg($('#mtmsg'), '失败: '+e, 'bad'); }
  finally{
    btn.disabled = false;
    const _dt = Math.round((Date.now()-t0)/100)/10;
    btn.textContent = _lab;
    setMsg($('#mtmsg'), (N>1?`连跑 ${N} 轮`:'') + `完成，耗时 ${_dt} s`, 'ok');
  }
}
/* 最近补入条目点击定位: 切曲库 tab + #fq 填文件名(去扩展名) -> doFind() 命中高亮 (全局, HTML onclick 调) */
function _mtLoc(el){
  const name=(el&&el.dataset.name)||''; if(!name) return;
  setTab('b');
  const fq=$('#fq'); if(fq){ fq.value=name; if(typeof doFind==='function'){
    const p=doFind();
    /* 命中后高亮首条结果: doFind 是 async, 渲染完取 #grid 首项 outline 闪烁 3 次 + 滚到顶, 不淹没在 200 结果里 */
    const _flash=()=>{ const g=$('#grid'); const first=g&&(g.querySelector('.card')||g.firstElementChild);
      if(first){ first.scrollIntoView({block:'center'}); let n=0; const iv=setInterval(()=>{ n++;
        first.style.outline=(n%2)?'2px solid var(--acc)':'none'; first.style.outlineOffset='2px';
        if(n>=7){ clearInterval(iv); first.style.outline=''; first.style.outlineOffset=''; } },180); } };
    if(p&&p.then) p.then(_flash).catch(function(){}); else setTimeout(_flash,300);
  } }
}
/* 折叠「看状态」区: 藏 #mtresult(卡片+进度+最近补入+跳日志全在此), 记忆到 localStorage._mtFold, 按钮 ▾/▸ 切换 */
function mtFold(){
  const r=$('#mtresult'); if(!r) return;
  let hid=(localStorage.getItem('_mtFold')==='1');
  hid=!hid;
  try{ localStorage.setItem('_mtFold', hid?'1':'0'); }catch(e){}
  r.style.display=hid?'none':'';
  const b=$('#mtfold'); if(b) b.textContent=hid?'▸ 展开':'▾ 折叠';
}
/* 载入时按记忆恢复折叠态 */
(function(){ try{ if(localStorage.getItem('_mtFold')==='1'){ const r=$('#mtresult'); if(r) r.style.display='none'; const b=$('#mtfold'); if(b) b.textContent='▸ 展开'; } }catch(e){} })();
async function mtStat(){
  try{
    /* 看状态时间戳: 落 localStorage, 「看状态」旁显「上次看 N 分钟前」 */
    const _agoV=(t)=>{ if(!t) return ''; const s=(Date.now()-t)/1000; if(s<60) return '刚刚'; if(s<3600) return Math.round(s/60)+' 分钟前'; if(s<86400) return Math.round(s/3600)+' 小时前'; return Math.round(s/86400)+' 天前'; };
    let _prevView=0; try{ _prevView=+localStorage.getItem('_mtViewAt')||0; }catch(e){}
    try{ localStorage.setItem('_mtViewAt', String(Date.now())); }catch(e){}
    const s = await (await fetch('/api/maintain')).json();
    const t = s.totals || {};
    /* 快照对比: _mtLast 落 localStorage(跨刷新也保留上次), 本次 delta 高亮「+N/-N」(清缓存后封面- N 也见) */
    let prev = {};
    try{ prev = JSON.parse(localStorage.getItem('_mtLast')||'{}') || {}; }catch(e){ prev = {}; }
    const delta = (k)=>{ const c=t[k]||0, p=(prev[k]===undefined?0:prev[k]); const d=c-p; return d>0?'+'+d:(d<0?String(d):''); };
    window._mtLast = { lyric:t.lyric||0, cover:t.cover||0, clean:t.clean||0, runs:s.runs||0 };
    try{ localStorage.setItem('_mtLast', JSON.stringify(window._mtLast)); }catch(e){}
    /* ID3 卡语义: 0 已修 + 全库 0 双缺 -> 显示"已核"(muted, 非"缺 0 张"); 有修过 -> 原绿字数字 */
    let id3v = t.meta_fixed || 0, id3label = 'ID3已修', id3style = '', id3title = '';
    if(!id3v){
      /* 快估 60s 窗口缓存: 首调冷读 ID3 ~26s, 同窗口内复用免再卡 */
      let e = null;
      try{
        const _c = window._id3estCache;
        if(_c && Date.now() - _c.t < 60000) e = _c.d;
        else {
          e = await (await fetch('/api/fixmeta?dry=1&offset=0&batch=500&estimate=1')).json();
          window._id3estCache = { t: Date.now(), d: e };
        }
        if(e.estimate && !(e.todo_est || 0)){
          id3v = '已核'; id3label = `ID3 双缺（${e.total_all||''} 首）`; id3style = 'color:var(--dim)';
          id3title = `500 采样外推 0 双缺 / ${e.total_all} 首 · 采样 ${e.sample_seconds}s（悬停看证据）`;
        }
      }catch(e){}
    } else {
      id3style = 'color:var(--ok);-webkit-text-fill-color:var(--ok)';
      id3title = `累计已写回 ${id3v} 首 ID3 双缺（标题←文件名 · 歌手←父目录）`;
    }
    /* 迷你 sparkline: 近 8 次趋势(SVG polyline, 不引库), 挂「已跑轮次/累计补歌词/累计补封面」卡 */
    let _sparkSeq=0;
    const _sparkSvg = (tr, color, label)=>{ if(!tr||tr.length<2) return ''; const w=110,h=22, max=Math.max.apply(null,tr), min=Math.min.apply(null,tr); const rng=(max-min)||1; const yOf=v=>Math.round((h-((v-min)/rng)*h)*100); const pts=tr.map((v,i)=>((i/(tr.length-1))*w).toFixed(1)+','+(h-((v-min)/rng)*h).toFixed(1)).join(' '); const tt=label? label+' 近 '+tr.length+' 次: '+tr.join(' → ') : '近 '+tr.length+' 次: '+tr.join(' → ');
      /* 圆点用 HTML 绝对定位(不随 svg preserveAspectRatio=none 拉伸成正圆), 首点 left=0 末点 left=100% */
      const _dot=(topPct,leftPct,size)=>`<span style="position:absolute;left:${leftPct}%;top:${topPct}%;width:${size}px;height:${size}px;margin:${-size/2}px 0 0 ${-size/2}px;border-radius:50%;background:${color}"></span>`;
      /* 末点值标签: 最新值数字, 悬在末点圆点上方(transform 上移不占布局, 不随 svg 拉伸) */
      const _lastVal=tr[tr.length-1];
      const _valLabel=`<span style="position:absolute;left:100%;top:${yOf(_lastVal)}%;transform:translate(-50%,-160%);font-size:10px;font-weight:600;color:${color};white-space:nowrap">${_lastVal}</span>`;
      /* 折线下面积渐变填充: 折线点 + 底边两点闭合成 polygon, linearGradient 纵向(顶透明->底 color@0.16), 每卡唯一 gid 免多卡冲突 */
      const _gid='spk'+(++_sparkSeq);
      const _area=pts+' '+w+','+h+' 0,'+h;
      /* 面积/渐变用 CSS 变量色时, linearGradient 的 stop 需具体色 - 传 color 可能是 var(), stop-color 支持 var() */
      return `<div class="mtspark" data-tr='${encodeURIComponent(JSON.stringify({t:tr,c:color,l:label||''}))}' style="position:relative;cursor:crosshair" title="${tt}"><svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" style="width:100%;height:22px;display:block"><defs><linearGradient id="${_gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${color}" stop-opacity="0"></stop><stop offset="1" stop-color="${color}" stop-opacity="0.18"></stop></linearGradient></defs><title>${tt}</title><polygon points="${_area}" fill="url(#${_gid})" stroke="none"/><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/></svg>${_dot(yOf(tr[0]),0,4)}${_dot(yOf(_lastVal),100,6)}${_valLabel}<span class="mtspark-hover" style="position:absolute;left:-99px;top:0;width:8px;height:8px;margin:-4px 0 0 -4px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 0 4px rgba(0,0,0,.3);display:none;pointer-events:none"></span><span class="mtspark-hoverlbl" style="position:absolute;left:-99px;top:-14px;font-size:10px;font-weight:600;color:${color};white-space:nowrap;display:none;pointer-events:none"></span></div>`; };
    const _runSpark = _sparkSvg((s.trend||[]).slice(-8), (s.runs||0)>=400?'var(--ok)':'var(--acc)', '已跑轮次');
    const _lyrSpark = _sparkSvg(((s.cum_trend||[]).slice(-8)).map(o=>o.lyric), 'var(--acc)', '累计歌词');
    const _covSpark = _sparkSvg(((s.cum_trend||[]).slice(-8)).map(o=>o.cover), 'var(--acc)', '累计封面');
    $('#mtresult').innerHTML = `
      <div class="statgrid mtgrid">
        <div class="statcard" title="${(()=>{const ms=(s.runs||0)>=400?450:400;return '维护 tick 累计；里程碑 '+(ms===450?'400/450':'350/400')+'，下一里程碑 '+ms+' 还差 '+Math.max(0,ms-(s.runs||0));})()}"><div class="k">已跑轮次</div><div class="v" style="${(s.runs||0)>=300?'color:var(--ok);-webkit-text-fill-color:var(--ok)':''}">${s.runs||0}</div><div style="height:3px;background:var(--line);border-radius:2px;margin-top:6px;overflow:hidden"><div style="height:100%;width:${(()=>{const ms=(s.runs||0)>=400?450:400;return Math.min(100,Math.round((s.runs||0)/ms*100));})()}%;background:${(s.runs||0)>=400?'var(--ok)':'var(--acc)'};border-radius:2px"></div></div>${_runSpark}</div>
        <div class="statcard" title="维护累计补歌词条数(命中缓存+补全)；点看状态重拉${delta('lyric')?'，本次 '+delta('lyric'):''}"><div class="k">累计补歌词</div><div class="v">${t.lyric||0}${delta('lyric')?`<span style="font-size:11px;color:${delta('lyric')[0]==='+'?'var(--ok)':'var(--bad)'};margin-left:6px">${delta('lyric')}</span>`:''}</div>${_lyrSpark}</div>
        <div class="statcard" title="维护累计补封面条数(缓存+抓取)；点看状态重拉${delta('cover')?'，本次 '+delta('cover'):''}"><div class="k">累计补封面</div><div class="v">${t.cover||0}${delta('cover')?`<span style="font-size:11px;color:${delta('cover')[0]==='+'?'var(--ok)':'var(--bad)'};margin-left:6px">${delta('cover')}</span>`:''}</div>${_covSpark}</div>
        <div class="statcard" title="维护累计清理的临时/过期缓存条目${delta('clean')?'，本次 '+delta('clean'):''}"><div class="k">累计清理</div><div class="v">${t.clean||0}${delta('clean')?`<span style="font-size:11px;color:${delta('clean')[0]==='+'?'var(--ok)':'var(--bad)'};margin-left:6px">${delta('clean')}</span>`:''}</div></div>
        <div class="statcard" title="${esc(id3title)}"><div class="k">${id3label}</div><div class="v" style="${id3style}">${id3v}</div></div>
      </div>
      <div class="n" style="margin-top:8px">上次运行: ${esc(s.last_run_str||'从未')}${_prevView?' · 看状态于 '+_agoV(_prevView):''}</div>`;
    /* 缓存快照: 双缓存(图免解 ID3 / lrc 免联网) + 清空按钮, 挂 5 卡下方 */
    try{
      const c = await (await fetch('/api/cache')).json();
      const cv = c.covers||{}, ly = c.lyrics||{}, pv = c.previews||{};
      const mbC = ((+cv.bytes||0)/1048576).toFixed(1), lbL = ((+ly.bytes||0)/1048576).toFixed(1), mbP = ((+pv.bytes||0)/1048576).toFixed(1);
      const totCache = ((+cv.bytes||0) + (+ly.bytes||0) + (+pv.bytes||0)) / 1048576;
      /* 第 6 卡「缓存」: 三缓存总条数 + 取链命中数 */
      const totFiles = ((+cv.files||0) + (+ly.files||0) + (+pv.files||0));
      $('#mtresult .statgrid').insertAdjacentHTML('beforeend',
        `<div class="statcard" title="封面 ${cv.files||0} + 歌词 ${ly.files||0} + 取链 ${pv.files||0}；取链累计命中 ${pv.hits||0}/${pv.calls||0}（命中率 ${pv.hit_rate||0}%，命中落盘重启不归 0）"><div class="k">缓存（三合·命中 ${pv.hits||0}）</div><div class="v">${totFiles}</div></div>`+
        `<div class="statcard" title="取链缓存命中率 = 命中 ${pv.hits||0} / 调用 ${pv.calls||0}（命中免 get_url 联网, 走本地 _cache/qq_*.json TTL 1800s）"><div class="k">取链命中率</div><div class="v" style="${(pv.hit_rate||0)>=80?'color:var(--ok);-webkit-text-fill-color:var(--ok)':(pv.calls||0)>=20?'color:var(--warn);-webkit-text-fill-color:var(--warn)':''}">${pv.hit_rate||0}%</div></div>`);
      /* 第 8 卡「异常率」: 拉日志 200 行, 数异常行(miss/失败/超时/error/Exception)占比, 红 >5% */
      try{
        const lg = await (await fetch('/api/maintain?act=log&n=200')).json();
        const lls = lg.lines||[];
        const bad = lls.filter(l=>/miss|失败|超时|error|Exception|无封面/i.test(l)).length;
        const rate = lls.length ? Math.round(bad/lls.length*100) : 0;
        const _rateSpark = _sparkSvg((s.rate_trend||[]).slice(-8), 'var(--bad)', '异常率(本轮miss%)');
        $('#mtresult .statgrid').insertAdjacentHTML('beforeend',
          `<div class="statcard" data-jumplog="异常" style="cursor:pointer" title="维护日志(近 200 行)异常占比 = 异常 ${bad} / ${lls.length}；异常含 miss/失败/超时/error/无封面，>5% 变红；点我看日志"><div class="k">异常率（日志 ${lls.length} 行）</div><div class="v" style="${rate>5?'color:var(--bad);-webkit-text-fill-color:var(--bad)':rate>0?'color:var(--warn);-webkit-text-fill-color:var(--warn)':'color:var(--ok);-webkit-text-fill-color:var(--ok)'}">${rate}%</div>${_rateSpark}</div>`);
        /* 第 10 卡「本批耗时」: 本轮 tick 用时(s) + 近 8 次耗时趋势(sparkline 复用), 看每批是否变慢(网络/磁盘拖慢) */
        {
          const _durT = (s.dur_trend||[]);
          const _dur = _durT.length ? _durT[_durT.length-1] : 0;
          const _durSpark = _sparkSvg(_durT.slice(-8), 'var(--muted)', '本批耗时(s)');
          $('#mtresult .statgrid').insertAdjacentHTML('beforeend',
            `<div class="statcard" title="最新一批 tick 用时(秒)；下方折线=近 8 批耗时趋势(变长=网络/磁盘拖慢)"><div class="k">本批耗时（近 8 批）</div><div class="v">${_dur?_dur+'s':'-'}</div>${_durSpark}</div>`);
        }
        /* 「下一批预计」: 网格下方一行提示 - 按 dur_trend 均值守估算下一批耗时 + 全库剩余曲目需几批跑完 */
        {
          const _durT = (s.dur_trend||[]);
          const _avg = _durT.length ? _durT.reduce((a,b)=>a+b,0)/_durT.length : 0;
          const _nTotal = s.n_total||0;
          const _batch = 20;
          /* 已扫进度 = cursor 在全库里的位置; 估算剩余 = n_total - 已扫. 简化: 用 runs 平均推进(全库 batch=20 每 runs 推 20 首) */
          const _scannedEst = (s.runs||0);   /* runs 计数即 tick 轮数, 每轮推 batch 首 */
          const _remaining = Math.max(0, _nTotal - _scannedEst*0);   /* 保守: 只报全库总量(断点续传真实进度见 cursor) */
          const _batchesLeft = Math.ceil((_nTotal)/_batch);
          const _estTotal = _avg ? (_batchesLeft*_avg) : 0;
          const _estStr = _avg ? ('下一批 ~'+_avg.toFixed(1)+'s ｜ 全库 '+_nTotal+' 首 ≈ '+_batchesLeft+' 批 ≈ '+(_estTotal>=60?Math.round(_estTotal/60)+' 分 '+Math.round(_estTotal%60)+' 秒':_estTotal.toFixed(0)+' 秒')) : '（无耗时样本）';
          $('#mtresult').insertAdjacentHTML('beforeend',
            `<div style="margin-top:8px;font-size:12px;color:var(--muted)" id="mtnextest" title="按近 8 批 tick 平均耗时无损估算; 全库批数=ceil(总曲目/20); 断点续传真实进度见「已跑轮次」cursor">${_estStr}</div>`);
        }
        /* 全库进度条: runs*20/n_total (已跑轮数×每批20首 / 全库总量), 封顶 100%, 纯 CSS 无库 */
        {
          const _scanned = Math.min((s.runs||0)*20, s.n_total||1);
          const _pct = s.n_total ? Math.min(100, Math.round(_scanned*100/(s.n_total))) : 0;
          const _done = _pct>=100;
          const _pc = _done?'var(--ok)':'var(--acc)';
          const _ptxt = _done?'全库已扫完 ✓':'全库进度';
          $('#mtresult').insertAdjacentHTML('beforeend',
            `<div style="margin-top:6px" id="mtprog" title="全库维护进度 = 已跑轮次×20 / 全库总量; 封顶100%(断点续传后重头算)"><div style="font-size:12px;color:var(--muted);margin-bottom:4px">${_ptxt} <b style="color:${_pc}">${_pct}%</b>（已扫约 ${_scanned} / ${s.n_total||'-'} 首）</div><div style="height:8px;background:var(--bg2);border-radius:4px;overflow:hidden"><div style="height:8px;width:${_pct}%;background:${_pc};border-radius:4px;transition:width .3s"></div></div></div>`);
        }
        /* 最近补入列表: state.recent(近5条 {what,name,at}) - 看刚补了哪首歌词/封面 + 时间, 非卡片(挂#mtresult尾随mtStat重建幂等) */
        {
          const _rec = s.recent||[];
          const _wAgo = t=>{ if(!t) return ''; const s2=(Date.now()-t*1000)/1000; if(s2<60) return Math.floor(s2)+'秒前'; if(s2<3600) return Math.floor(s2/60)+'分前'; if(s2<86400) return Math.floor(s2/3600)+'时前'; return Math.floor(s2/86400)+'天前'; };
          const _wIcon = w=> w==='lyric'?'歌词':'封面';
          const _wColor = w=> w==='lyric'?'var(--acc)':'var(--ok)';
          /* 点击定位: 切曲库 tab + #fq 填文件名(去扩展名) -> doFind() 命中高亮 */
          const _loc = r=>{ setTab('b'); const fq=$('#fq'); if(fq){ fq.value=(r.name||'').replace(/\.[^.]+$/,''); if(typeof doFind==='function') doFind(); } };
          const _rowHTML = r=>`<div style="display:flex;justify-content:space-between;gap:10px;padding:3px 0;border-bottom:1px dashed var(--line);font-size:12px;cursor:pointer" onclick="_mtLoc(this)" data-name="${(r.name||'').replace(/"/g,'&quot;')}" title="点击去曲库搜这首"><span style="color:${_wColor(r.what)};font-weight:600">${_wIcon(r.what)}</span><span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink)">${(r.name||'').replace(/</g,'&lt;')}</span><span style="color:var(--muted);white-space:nowrap">${_wAgo(r.at)}</span></div>`;
          /* 类型筛选: 全部/歌词/封面 三段, 按 what 过滤 recent(近5条), 显计数 */
          const _cnt = (w)=> w?'':(_rec.filter(r=>r.what===w).length);
          const _nLyric = _rec.filter(r=>r.what==='lyric').length, _nCov = _rec.filter(r=>r.what==='cover').length;
          const _rowsAll = _rec.length ? _rec.map(_rowHTML).join('') : '<div style="font-size:12px;color:var(--muted);padding:4px 0">（暂无补入记录）</div>';
          const _rowsLyric = _rec.filter(r=>r.what==='lyric').length ? _rec.filter(r=>r.what==='lyric').map(_rowHTML).join('') : '<div style="font-size:12px;color:var(--muted);padding:4px 0">（近 5 条无歌词补入）</div>';
          const _rowsCov = _rec.filter(r=>r.what==='cover').length ? _rec.filter(r=>r.what==='cover').map(_rowHTML).join('') : '<div style="font-size:12px;color:var(--muted);padding:4px 0">（近 5 条无封面补入）</div>';
          $('#mtresult').insertAdjacentHTML('beforeend',
            `<div style="margin-top:10px" id="mtrecent" title="最近补入歌词/封面(近 5 条, 来自维护 tick; 类型色: 歌词=accent 封面=ok; 可按类型筛)"><div style="font-size:12px;color:var(--muted);margin-bottom:4px;display:flex;align-items:center;gap:8px;flex-wrap:wrap">最近补入（近 5 条）<span style="display:inline-flex;gap:4px" id="mtrf"><button type="button" class="ghost sm" data-mf="all" style="padding:1px 7px;font-size:11px;cursor:pointer;background:var(--acc);color:#fff;border-color:var(--acc)">全部 ${_rec.length}</button><button type="button" class="ghost sm" data-mf="lyric" style="padding:1px 7px;font-size:11px;cursor:pointer">歌词 ${_nLyric}</button><button type="button" class="ghost sm" data-mf="cover" style="padding:1px 7px;font-size:11px;cursor:pointer">封面 ${_nCov}</button></span></div><div class="mtrecent-rows" data-mf="all">${_rowsAll}</div><div class="mtrecent-rows" data-mf="lyric" style="display:none">${_rowsLyric}</div><div class="mtrecent-rows" data-mf="cover" style="display:none">${_rowsCov}</div></div>`);
          /* 筛选 tab 切换: 事件委托到 #mtrf(随 mtStat 重建), 切当前 data-mf 行, 高亮选中 tab */
          document.querySelectorAll('#mtrf button').forEach(bn=>{
            bn.onclick=()=>{ document.querySelectorAll('#mtrf button').forEach(x=>{ x.style.background=''; x.style.color=''; x.style.borderColor=''; });
              bn.style.background='var(--acc)'; bn.style.color='#fff'; bn.style.borderColor='var(--acc)';
              const mf=bn.dataset.mf;
              document.querySelectorAll('#mtrecent .mtrecent-rows').forEach(rr=>{ rr.style.display=(rr.dataset.mf===mf)?'':'none'; }); };
          });
        }
        /* 异常率卡点击 -> 跳日志区 + 过滤填「异常」+ 红字 */
        document.querySelectorAll('#mtresult .statcard[data-jumplog]').forEach(card=>{
          card.onclick=()=>{ const f=document.querySelector('#mtlogfilter');
            if(f){ f.value=card.dataset.jumplog; }
            /* 跳日志时停自动刷(否则 mtStat 重铺 #mtresult 会把跳的日志闪掉), 给提示 */
            if(typeof _mtAutoRefTimer!=='undefined' && _mtAutoRefTimer!==null){ mtAutoRef(); }
            /* 追加日志区到 #mtresult 尾(不清 8 卡) + 过滤 + 滚到 */
            const box=document.getElementById('mtjumplog');
            if(!box){ const d=document.createElement('div'); d.id='mtjumplog'; d.style.cssText='margin-top:10px'; document.querySelector('#mtresult').appendChild(d); }
            if(typeof mtLogDraw==='function'){
              /* 临时把 mtLogDraw 的输出容器指到 box */
              const _mtresult=document.getElementById('mtresult');
              /* 直接拉日志填 box */
              fetch('/api/maintain?act=log&n=200').then(r=>r.json()).then(d=>{
                let lines=d.lines||[]; const kw=((f.value||'').trim());
                if(kw){ lines=lines.filter(l=>l.indexOf(kw)>=0); }
                box.innerHTML = lines.length ? `<div class="joblog" style="max-height:300px">${lines.map(l=>{
                  const e=l.replace(/</g,'&lt;');
                  /* 异常率卡跳「异常」: 含异常词的命中行染红 */
                  return /miss|失败|超时|error|Exception|无封面/i.test(l) ? '<span style="color:var(--bad)">'+e+'</span>' : e;
                }).join('\n')}</div>` : '<div class="n">无匹配日志</div>';
                /* 滚到第一条红字异常行(不是日志顶) */
                const firstBad=box.querySelector('.joblog span[style*="var(--bad)"]');
                if(firstBad){ firstBad.scrollIntoView({behavior:'smooth',block:'center'}); }
                else{ box.scrollIntoView({behavior:'smooth',block:'center'}); }
              }).catch(()=>{});
            }
            setMsg($('#mtmsg'), `已跳日志 + 过滤「${card.dataset.jumplog}」`, 'ok');
          };
        });
      }catch(e){}
      /* 第 9 卡「本轮补 N」: 最近一次 tick 的 lyric_ok+cover_ok(从 s.last), 刷新重拉 */
      try{
        const last=s.last||{};
        const lastN=(last.lyric_ok||0)+(last.cover_ok||0);
        const agoT=(t)=>{ if(!t) return ''; const sec=(Date.now()/1000 - t); if(sec<60) return '刚刚'; if(sec<3600) return Math.round(sec/60)+' 分钟前'; if(sec<86400) return Math.round(sec/3600)+' 小时前'; return Math.round(sec/86400)+' 天前'; };
        $('#mtresult .statgrid').insertAdjacentHTML('beforeend',
          `<div class="statcard" title="最近一次维护 tick 的即时补数 = 歌词 +${last.lyric_ok||0} · 封面 +${last.cover_ok||0}（${last.at?agoT(last.at):'尚未跑 tick'}；点刷新重拉）"><div class="k">本轮补（最新 tick）</div><div class="v" style="${lastN>0?'color:var(--ok);-webkit-text-fill-color:var(--ok)':'color:var(--dim);-webkit-text-fill-color:var(--dim)'}">${lastN}<span style="font-size:11px;color:var(--dim);margin-left:6px">${last.at?agoT(last.at):'待跑'}</span></div></div>`);
      }catch(e){}
      /* 全库体积: 优先吃 health tab 已扫的 window._health, 免每次重扫 */
      let libMB = 0, libCount = 0;
      if(window._health && window._health.total_size_mb){ libMB = +window._health.total_size_mb; libCount = window._health.total_all||0; }
        try{
          const hz = await (await fetch('/api/health')).json();
          libMB = (+hz.total_size_mb||0); libCount = hz.total_all||0;
          window._health = window._health || hz;
        }catch(e){}
      const ratio = (libMB > 0) ? (totCache / libMB * 100).toFixed(1) : '0';
      $('#mtresult').insertAdjacentHTML('beforeend',
        `<div class="n" style="margin-top:6px;display:flex;gap:14px;align-items:center;flex-wrap:wrap">`+
        `封面缓存 <b>${cv.files||0}</b> 张 · ${mbC} MB &nbsp; 歌词缓存 <b>${ly.files||0}</b> 条 · ${lbL} MB &nbsp; 取链缓存 <b>${pv.files||0}</b> 条 · ${mbP} MB`+
        ` <button class="ghost sm" id="mtcacheclr" title="清空封面+歌词+取链缓存(文件保留在库, 只清 _cache)">清缓存</button>`+
        `</div>`+
        `<div class="n" style="margin-top:4px;color:var(--dim)">缓存共 ${totCache.toFixed(1)} MB · 占全库 ${libMB?libMB.toFixed(0):'-'} MB ${libMB>=1024?'（≈'+(libMB/1024).toFixed(1)+' GB）':''} / ${libCount||'-'} 首的 <b>${ratio}%</b> · 取链命中 <b>${pv.hits||0}</b>/${pv.calls||0}（命中率 <b>${pv.hit_rate||0}%</b>，清缓存连同命中计数一起清）</div>`);
      $('#mtcacheclr').onclick = async ()=>{
        const btn = $('#mtcacheclr');
        if(!confirm('清空封面('+cv.files+' 张)+歌词('+ly.files+' 条)+取链('+(pv.files||0)+' 条)缓存？\n文件本身不动, 下次访问会重建。')) return;
        btn.disabled = true;
        try{
          const r = await (await fetch('/api/cache?clear_all=1')).json();
          setMsg($('#mtmsg'), `已清缓存: 封面 ${r.cleared_covers||0} · 歌词 ${r.cleared_lyrics||0} · 取链 ${r.cleared_previews||0} · 命中计数${r.cleared_hits?'已清':''}`, 'ok');
          await mtStat();
          /* 清缓存后清 localStorage._mtLast 基准(在 mtStat 之后, 否则被其 setItem 写回) */
          try{ localStorage.removeItem('_mtLast'); }catch(e){}
        }catch(e2){ setMsg($('#mtmsg'),'清缓存失败: '+e2,'bad'); }
        finally{ btn.disabled = false; }
      };
    }catch(e){}
    /* 数字滚动: 5 卡值 0→终值 单次编排(500ms, reduced-motion 直落) */
    $('#mtresult').querySelectorAll('.statcard .v').forEach(v=>{
      const raw = String(v.textContent).replace(/,/g,'');
      /* 非数值卡(如"已核")跳过滚动, 直保 */
      if(/^\d+$/.test(raw)) countUp(v, parseInt(raw,10), 500);
    });
    /* 最近补的 N 首(歌词/封面, 来自 maintain recent, 保最近 5; 带相对时间) */
    try{
      const rc = s.recent||[];
      if(rc.length){
        const ago=(t)=>{ if(!t) return ''; const s=(Date.now()/1000 - t); if(s<60) return '刚刚'; if(s<3600) return Math.round(s/60)+' 分钟前'; if(s<86400) return Math.round(s/3600)+' 小时前'; return Math.round(s/86400)+' 天前'; };
        const rl = rc.slice(0,5).map(x=>`<span class="n">${x.what==='lyric'?'歌词':'封面'} · ${esc(x.name||'')}<span style="color:var(--dim)">（${ago(x.at)}）</span></span>`).join(' &nbsp;');
        $('#mtresult').insertAdjacentHTML('beforeend', `<div class="n" style="margin-top:6px;color:var(--dim)">最近补: ${rl}</div>`);
      }
    }catch(e){}
  }catch(e){}
}
let _mtlogTimer=null;
function _kwsHtml(k){ return k.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }
async function mtLogDraw(){
  const d = await (await fetch('/api/maintain?act=log&n=200')).json();
  let lines = d.lines || [];
  const kw = ((document.querySelector('#mtlogfilter')||{}).value||'').trim();
  if(kw){ lines = lines.filter(l=>l.indexOf(kw)>=0); }
  const escL = s=>s.replace(/[&<>"]/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const paint = l=>{ let e=escL(l);
    /* 异常行红字: 含 miss/error/Exception/失败/超时 的行 -> 整行红色 */
    if(/miss|error|Exception|失败|超时|无封面/i.test(l) && !kw){ e='<span style="color:var(--bad)">'+e+'</span>'; }
    if(kw){ e=e.replace(_kwsHtml(kw), '<mark style="background:#ffe9a8">$&</mark>'); }
    return e; };
  $('#mtresult').innerHTML = lines.length
    ? `<div class="joblog" style="max-height:320px">${lines.map(paint).join('\n')}</div>`
    : `<div class="n">${kw?'无匹配「'+escL(kw)+'」的日志':'日志为空'}</div>`;
  return lines.length;
}
async function mtLog(){
  setMsg($('#mtmsg'), '读日志…');
  try{
    await mtLogDraw();
    setMsg($('#mtmsg'), `共 ${($('#mtresult').querySelectorAll('.joblog div').length||0)} 行`);
  }catch(e){ setMsg($('#mtmsg'), '失败: '+e, 'bad'); }
}
/* sparkline hover: 委托 mousemove 命中 .mtspark, 按 X 定位最近点, 显高亮圆点+值(纯JS不引库) */
(function(){
  document.addEventListener('mousemove', function(e){
    const box=e.target.closest && e.target.closest('.mtspark');
    if(!box){ document.querySelectorAll('.mtspark-hover,.mtspark-hoverlbl').forEach(function(x){x.style.display='none';}); return; }
    const raw=box.dataset.tr; if(!raw) return;
    let d; try{ d=JSON.parse(decodeURIComponent(raw)); }catch(e2){ return; }
    const t=d.t||[]; if(t.length<2) return;
    const r=box.getBoundingClientRect();
    const frac=Math.max(0,Math.min(1,(e.clientX-r.left)/r.width));
    const idx=Math.round(frac*(t.length-1));
    const max=Math.max.apply(null,t), min=Math.min.apply(null,t), rng=(max-min)||1;
    const yPct=Math.round((22-((t[idx]-min)/rng)*22)*100);
    const hov=box.querySelector('.mtspark-hover'), lbl=box.querySelector('.mtspark-hoverlbl');
    if(hov){ hov.style.display='block'; hov.style.left=(idx/(t.length-1)*100)+'%'; hov.style.top=yPct+'%'; }
    if(lbl){ lbl.style.display='block'; lbl.style.left=(idx/(t.length-1)*100)+'%'; lbl.style.top='-2px'; lbl.textContent=t[idx]; }
  }, {passive:true});
  document.addEventListener('mouseout', function(e){
    const box=e.target.closest && e.target.closest('.mtspark');
    if(box && !(e.relatedTarget && box.contains(e.relatedTarget))){
      const h=box.querySelector('.mtspark-hover'), l=box.querySelector('.mtspark-hoverlbl');
      if(h)h.style.display='none'; if(l)l.style.display='none';
    }
  }, {passive:true});
})();
/* 自动刷 9 卡: 每 5s 调 mtStat(跑维护/跑到全库时挂着, 实时看累计/delta/本轮补变化), 再点停 */
let _mtAutoRefTimer=null;
function mtAutoRef(){
  const btn=document.getElementById('mtautoref');
  if(_mtAutoRefTimer){ clearInterval(_mtAutoRefTimer); _mtAutoRefTimer=null; if(btn){ btn.classList.remove('on'); btn.style.background=''; btn.style.borderColor=''; } setMsg($('#mtmsg'), '自动刷已停', 'ok'); return; }
  if(btn){ btn.classList.add('on'); btn.style.background='var(--acc)'; btn.style.borderColor='var(--acc)'; }
  setMsg($('#mtmsg'), '自动刷 · 每 5s 重拉 9 卡…');
  mtStat().catch(()=>{});
  _mtAutoRefTimer=setInterval(()=>{ mtStat().catch(()=>{}); }, 5000);
}
function mtLogLive(){
  if(_mtlogTimer){ clearInterval(_mtlogTimer); _mtlogTimer=null; setMsg($('#mtmsg'), '实时日志已停', 'ok'); return; }
  setMsg($('#mtmsg'), '实时日志 · 每 2s 刷新…');
  mtLogDraw().catch(()=>{});
  _mtlogTimer=setInterval(()=>{ mtLogDraw().catch(()=>{}); }, 2000);
}
$('#mtrun').onclick = mtRun;
$('#mtstat').onclick = mtStat;
/* 刷新: 只重拉 8 卡(保留已跳日志容器, 不重铺整区) */
$('#mtrefresh').onclick = async()=>{
  const hadJump = !!document.querySelector('#mtjumplog');
  setMsg($('#mtmsg'), '刷新…');
  try{ await mtStat(); if(hadJump && !document.querySelector('#mtjumplog')){ document.querySelector('#mtresult .statcard[data-jumplog]') && document.querySelector('#mtresult .statcard[data-jumplog]').click(); } setMsg($('#mtmsg'), '已刷新', 'ok'); }
  catch(e){ setMsg($('#mtmsg'), '刷新失败: '+e, 'bad'); }
};
$('#mtlog').onclick = mtLog;
$('#mtloglive').onclick = mtLogLive;
/* 导出日志: 拉全量 act=log&n=500, 下载 maintain.log 快照 */
$('#mtlogexport').onclick = async()=>{
  setMsg($('#mtmsg'), '导出日志…');
  try{
    const d = await (await fetch('/api/maintain?act=log&n=500')).json();
    const lines = (d.lines||[]).join('\n');
    const blob = new Blob([lines || '(日志为空)'], {type:'text/plain;charset=utf-8'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'maintain.log.' + new Date().toISOString().slice(0,10) + '.txt';
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(a.href), 1000);
    setMsg($('#mtmsg'), `已导出 ${(d.lines||[]).length} 行日志`, 'ok');
  }catch(e){ setMsg($('#mtmsg'), '导出失败: '+e, 'bad'); }
};
document.addEventListener('input', e=>{ if(e.target && e.target.id==='mtlogfilter'){ if($('#mtresult .joblog')) mtLogDraw().catch(()=>{}); } });
/* 日志预设 chip: 一键填过滤框(歌词/封面/异常/全部) + 重绘 */
document.querySelectorAll('[data-lf]').forEach(c=>{
  c.onclick=()=>{ const f=document.querySelector('#mtlogfilter'); if(!f) return; f.value=c.dataset.lf;
    if($('#mtresult .joblog')) mtLogDraw().catch(()=>{}); };
});
$('#mtreset').onclick = async()=>{
  let cur='未知';
  try{ const st=await (await fetch('/api/maintain')).json(); cur=(st.cursor&&st.cursor._all)?st.cursor._all.split('\\').slice(-2).join('\\'):'(无)'; }catch(e){}
  if(!confirm(`重置断点游标？\n\n当前断点: ${cur}\n重置后果: 下次「跑维护」从头扫全库(已补的不会重补, 只重扫一遍 5188 首定位)。\n\n确认重置？`)) return;
  await fetch('/api/maintain?act=reset');
  setMsg($('#mtmsg'), '断点已重置', 'ok');
  mtStat();
};

/* ---------- 设置弹窗（音质/登录/赠金） ---------- */
let CFG = {};
let _opener = null;
async function cfgLoad(){
  try{ CFG = await (await fetch('/api/config')).json(); }catch(e){ CFG = {}; }
  $('#creditv').textContent = (CFG.credit_balance!=null)? CFG.credit_balance : 100;
  if(CFG.qq_quality_order) $('#qquality').value = CFG.qq_quality_order.join(',');
  $('#qqcookie').value = CFG.qq_cookie || '';
  $('#destsub').value = CFG.dest_sub || '';
  $('#necookie').value = CFG.netease_cookie || '';
}
function setOpen(){ _opener=document.activeElement; document.body.classList.add('ov');
  $('#setmodal').classList.add('on'); cfgLoad();
  const f=$('#setmodal').querySelector('input,button,select'); if(f) setTimeout(()=>f.focus(),30); }
function setClose(){ document.body.classList.remove('ov'); $('#setmodal').classList.remove('on');
  if(_opener && _opener.focus) _opener.focus(); }
$('#btnset').onclick = setOpen;
$('#setclose').onclick = setClose;
$('#setclose2').onclick = setClose;
$('#setmodal').onclick = e=>{ if(e.target.id==='setmodal') setClose(); };
$('#creditset').onclick = ()=>{
  const n = parseInt($('#creditin').value, 10);
  if(isNaN(n)){ setMsg($('#setmsg'),'赠金要填整数（可负=欠费）','bad'); return; }
  $('#creditv').textContent = (parseInt($('#creditv').textContent,10)||0) + n;
  $('#creditin').value='';
  setMsg($('#setmsg'),'赠金已调 '+(n>0?'+':'')+n+'，点「保存设置」生效');
};
$('#setsave').onclick = async ()=>{
  const body = {
    qq_quality_order: $('#qquality').value.split(',').map(Number),
    qq_cookie: $('#qqcookie').value.trim(),
    netease_cookie: $('#necookie').value.trim(),
    credit_balance: parseInt($('#creditv').textContent, 10) || 0,
    dest_sub: $('#destsub').value.trim(),
  };
  try{
    const r = await (await fetch('/api/config', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)})).json();
    setMsg($('#setmsg'), r.ok===false ? ('保存失败: '+(r.error||'')) : '已保存并生效 ✓');
    if(r.ok!==false) applyCredits();
  }catch(e){ setMsg($('#setmsg'),'保存失败: '+e,'bad'); }
};
function applyCredits(){ /* 充数达标时高亮 */ }
document.addEventListener('keydown', e=>{
  if(e.key==='Escape' && $('#setmodal').classList.contains('on')) setClose();
});

/* ---------- 关于弹窗 ---------- */
const REPO_URL = 'https://github.com/qingshanjiluo/music3';

async function aboutOpen(){ _opener=document.activeElement; document.body.classList.add('ov');
  $('#aboutmodal').classList.add('on');
  const f=$('#aboutmodal').querySelector('button,a'); if(f) setTimeout(()=>f.focus(),30);
  /* 动态计数: 坑/轮/提交数从 README+git 实时算, 免硬编码 46 */
  try{
    const d = await (await fetch('/api/about')).json();
    if(d.pits){ $('#mnotePits').textContent = d.pits; $('#mnoteRounds').textContent = d.rounds||'—'; $('#mnoteCommits').textContent = d.commits||'—'; }
  }catch(e){}
}
function aboutClose(){ document.body.classList.remove('ov'); $('#aboutmodal').classList.remove('on');
  if(_opener && _opener.focus) _opener.focus(); }

async function copyText(t, btn){
  let ok = false;
  try{
    if(navigator.clipboard && window.isSecureContext){
      await navigator.clipboard.writeText(t); ok = true;
    }
  }catch(e){}
  if(!ok){
    // http 非安全上下文降级：临时 textarea + execCommand
    const ta = document.createElement('textarea');
    ta.value = t;
    ta.style.cssText = 'position:fixed;left:-9999px;top:0';
    document.body.appendChild(ta);
    ta.select();
    try{ ok = document.execCommand('copy'); }catch(e){}
    ta.remove();
  }
  if(btn){
    const old = btn.textContent;
    btn.textContent = ok ? '已复制' : '失败';
    setTimeout(()=>{ btn.textContent = old; }, 1200);
  }
  return ok;
}

$('#btnabout').onclick = aboutOpen;
$('#mclose').onclick = aboutClose;
$('#aboutmodal').onclick = (e)=>{
  if(e.target.id === 'aboutmodal') aboutClose();
};
$('#openrepo').onclick = ()=>window.open(REPO_URL, '_blank', 'noopener');
$('#copywx').onclick = ()=>{
  copyText('andyloveanny', $('#copywx'));
};
$$('.copybtn').forEach(b=>{
  b.onclick = ()=>copyText(b.dataset.copy || '', b);
});
document.addEventListener('keydown', (e)=>{
  if(e.key === 'Escape' && $('#aboutmodal').classList.contains('on')) aboutClose();
});

/* ---------- 导出 ---------- */function doExport(fmt, src, fast){
  const sub = (src === 'lib' && curSub) ? curSub : '';
  let u = `/api/export?fmt=${fmt}&src=${src}&sub=${encodeURIComponent(sub)}`;
  if(fmt === 'index' && fast !== undefined) u += '&fast=' + (fast ? 1 : 0);
  const a = document.createElement('a');
  a.href = u;
  a.download = '';
  document.body.appendChild(a);
  a.click();
  a.remove();
  const extra = (fmt==='index') ? (fast===0 ? '（含时长，约 2 分钟）' : '（快速，约 3 秒）') : '';
  setMsg($('#dmsg'), '正在导出 ' + fmt + extra + (sub ? '（' + sub + '）' : '（全库）') + '…');
}

/* 相对时间: 刚刚/N分钟前/N小时前/昨天/N天前/N个月前; title 挂绝对时间(简洁性: 首读少一步心算) */
function relTime(at){
  if(!at) return '';
  const d = new Date(String(at).replace(' ', 'T'));
  if(isNaN(d)) return String(at).replace(/^\d{4}-/, '');
  const s = Math.max(0, (Date.now() - d.getTime()) / 1000);
  let txt;
  if(s < 60) txt = '刚刚';
  else if(s < 3600) txt = Math.floor(s/60) + ' 分钟前';
  else if(s < 86400 && d.getDate() === new Date().getDate()) txt = Math.floor(s/3600) + ' 小时前';
  else if(s < 172800) txt = '昨天';
  else if(s < 2592000) txt = Math.floor(s/86400) + ' 天前';
  else if(s < 31536000) txt = Math.floor(s/2592000) + ' 个月前';
  else txt = Math.floor(s/31536000) + ' 年前';
  return txt;
}
function absTime(at){ try{ return new Date(String(at).replace(' ','T')).toLocaleString(); }catch(e){ return at||''; } }
/* ---------- 历史 ---------- */
async function loadHistory(){
  setMsg($('#hmsg'),'加载中…');
  try{
    const d = await (await fetch('/api/history?limit=200')).json();
    const items = d.items||[];
    window._histList = items.map(x=>({rel:x.rel, title:x.title, artists:x.artists}));
    $('#hcount').textContent = `共 ${items.length} 条`;
    $('#htb').innerHTML = items.map((x,i)=>`<tr>
      <td>${i+1}</td>
      <td>${esc(x.title||x.rel.split(/[\\\\/]/).pop())}</td>
      <td class="n">${esc(x.artists||'')}</td>
      <td class="n"><span title="${esc(absTime(x.at))}">${esc(relTime(x.at))}</span></td>
      <td><button class="ghost sm" onclick="playHist(${i})">播放</button></td>
    </tr>`).join('');
    setMsg($('#hmsg'), items.length? '' : '还没有播放记录');
  }catch(e){ setMsg($('#hmsg'),'失败: '+e,'bad'); }
}
function playHist(i){
  const L = window._histList||[];
  const t = L[i]; if(!t) return;
  play(t.rel, t.title, t.artists, L, i);
}
$('#hreload').onclick = loadHistory;
$('#hclear').onclick = async()=>{
  if(!confirm('清空全部播放历史？')) return;
  await fetch('/api/history?clear=1');
  loadHistory();
};

/* ---------- 批量（SSE） ---------- */
let es=null, curJob='';
$('#bstart').onclick=async()=>{
  const raw=$('#bkws').value.trim();
  if(!raw)return;
  const kws=raw.split(/[\n,，]+/).map(s=>s.trim()).filter(Boolean);
  if(!kws.length)return;
  $('#bstop').disabled=false;
  setMsg($('#msg'),'');
  $('#jobbox').innerHTML='';
  try{
    const r=await fetch('/api/queue',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({keywords:kws, n:+$('#bn').value||1, workers:+$('#bw').value||3, bili:$('#bbili').checked, dest:($('#bdest').value||'').trim()})
    });
    const d=await r.json();
    if(d.error){alert('错误: '+d.error);return;}
    curJob=d.job;
    subscribe(d.job, kws.length);
  }catch(e){alert('失败: '+e);}
};
$('#bstop').onclick=async()=>{
  if(!curJob)return;
  await fetch('/api/job/cancel?id='+curJob);
  $('#bstop').disabled=true;
};
$('#bclear').onclick=()=>{
  if(es){es.close();es=null;}
  curJob=null;
  $('#bstop').disabled=true;
  $('#jobbox').innerHTML=emptyBox('⇩','队列已清空','在上方填写关键词后点「开始下载」','支持多行 / 逗号分隔多个关键词','<button class="ghost sm" onclick="_focusKw()">填关键词</button>');
};
function _focusKw(){ const e=$('#bkws'); if(e){ e.focus(); e.scrollIntoView({block:'center'}); } }
/* 批量页冷启动空态 */
$('#jobbox').innerHTML=emptyBox('⇩','还没有下载任务','多行或逗号分隔关键词 → 每词下载几首 → 点「开始下载」','下载进度、成功/跳过/失败实时显示在这张卡片上','<button class="ghost sm" onclick="_focusKw()">填关键词</button>');
function subscribe(jid, total){
  if(es){es.close();es=null;}
  const card=document.createElement('div');
  card.className='jobcard'; card.id='jc-'+jid;
  card.innerHTML=`<div class="jobhead">
      <div class="jobtitle">批量下载 · ${jid}</div>
      <div class="n" id="js-${jid}">连接中…</div>
    </div>
    <div class="pbar2"><i id="jp-${jid}"></i></div>
    <div class="jobmeta">
      <span>进度 <b id="jd-${jid}">0</b>/<b id="jt-${jid}">${total}</b></span>
      <span>成功 <b id="jo-${jid}" style="color:var(--ok)">0</b></span>
      <span>跳过 <b id="jk-${jid}">0</b></span>
      <span>失败 <b id="jf-${jid}" style="color:var(--bad)">0</b></span>
    </div>
    <div class="joblog" id="jl-${jid}"></div>`;
  $('#jobbox').prepend(card);

  es=new EventSource('/api/job/sse?id='+jid);
  es.addEventListener('progress',ev=>{
    const s=JSON.parse(ev.data);
    const tot=s.total||1;
    $('#jd-'+jid).textContent=s.done;
    $('#jt-'+jid).textContent=s.total;
    $('#jo-'+jid).textContent=s.ok;
    $('#jk-'+jid).textContent=s.skip;
    $('#jf-'+jid).textContent=s.fail;
    $('#jp-'+jid).style.width=Math.min(100,(s.done/tot)*100)+'%';
    if(s.lines) $('#jl-'+jid).textContent=s.lines.slice(-40).join('\\n');
    $('#js-'+jid).textContent=s.state==='running'?'运行中':s.state;
    $('#jl-'+jid).scrollTop=$('#jl-'+jid).scrollHeight;
  });
  es.addEventListener('done',ev=>{
    const d=JSON.parse(ev.data);
    $('#js-'+jid).textContent=d.state==='done'?'完成':d.state;
    $('#jp-'+jid).style.width='100%';
    $('#bstop').disabled=true;
    es.close(); es=null;
    loadStat();
  });
  es.onerror=()=>{ $('#js-'+jid).textContent='连接断开'; };
}

/* ---------- 清理 ---------- */
$('#dlist').innerHTML=emptyBox('⌕','还没扫描','选一种比对方式 → 点「扫描重复」','会找出重复组与临时残留文件，删除前先预览');
$('#scan').onclick=async()=>{
  const by=document.querySelector('input[name=by]:checked').value;
  setMsg($('#dmsg'),'扫描中…'); $('#dlist').innerHTML='';
  try{
    const d=await (await fetch(`/api/dup?by=${by}&top=15`)).json();
    setMsg($('#dmsg'),`重复组 ${d.dup_groups} · 临时残留 ${d.tmp_files}`);
    $('#dlist').innerHTML = (d.sample||[]).length
      ? (d.sample||[]).map(g=>
      `<div class="jobcard"><div class="mono" style="color:var(--fg);margin-bottom:5px">${esc(g.key)}</div>`+
      g.paths.map(p=>`<div class="mono" style="padding-left:12px">${esc(p)}</div>`).join('')+`</div>`).join('')
      : emptyBox('✓', '没有重复曲目', `按「${by}」比对全库，暂无重复组`, `临时残留 ${d.tmp_files} 个`);
  }catch(e){setMsg($('#dmsg'),'失败: '+e,'bad');}
};

/* ---------- 状态 ---------- */
async function loadStat(){
  try{
    const d=await (await fetch('/api/stat')).json();
    /* 信息密度: 标题栏只给"全库规模"单一总数, 逐目录细节归曲库页(原 dump 全 key 太密) */
    const total=Object.values(d).reduce((a,b)=>a+(+b||0),0);
    $('.sub').textContent='B站 / 网易云 / QQ音乐 · 全库 '+total+' 首';
  }catch(e){}
}
loadStat();
/* 恢复视图偏好 + 预载播放列表 + 初始化均衡器 + 播放模式 */
applyViewMode(viewMode);
plLoad();
eqInit();
applyMode();
applyRate();

/* 恢复上次播放队列(暂停态, 不自动播——浏览器 autoplay 策略 + 用户预期) */
(function restoreQueue(){
  try{
    const q = JSON.parse(localStorage.getItem('m3_queue') || 'null');
    if(!q || !q.rel) return;
    curRel=q.rel; playList=q.list||[]; playIdx=(q.idx==null?-1:q.idx);
    $('#ptitle').textContent = q.title || q.rel.split(/[\\/]/).pop();
    $('#partist').textContent = q.artist || '';
    player.classList.add('on');   // 常驻占位: 未播时 .player:not(.on) 降透明度, 这里点亮
    audio.src = '/api/stream?rel=' + encodeURIComponent(q.rel);
    try{ audio.playbackRate = playRate; }catch(e){}
    if(q.t > 0) audio.addEventListener('loadedmetadata', ()=>{
      try{ audio.currentTime = q.t; }catch(e){}
    }, {once:true});
    setMsg($('#msg'), '已恢复上次队列 · 第 '+((playIdx<0?1:playIdx+1))+' 首（共 '+playList.length+' 首）· 点 ▶ 续播', 'ok');
    fitWave();
  }catch(e){}
})();

/* PWA：注册 service worker */
if('serviceWorker' in navigator && location.protocol === 'http:' || location.protocol === 'https:'){
  navigator.serviceWorker.register('/sw.js').catch(()=>{});
}
</script></body></html>
"""


def _mv_worker(jid, track, dest_dir):
    """MV 下载工作线程（走 jobs 记进度/日志，前端可 SSE 跟）。"""
    from . import jobs, src_bili, downloader

    jobs.log(jid, "开始下载 %s - %s" % (track.artists, track.title))
    try:
        ok, msg, path = src_bili.download_video(track, dest_dir)
    except Exception as e:
        jobs.log(jid, "异常 %r" % (e,))
        jobs.finish(jid, "error", str(e))
        return
    if ok:
        dur = downloader.duration_of(path) if path else 0
        try:
            from . import stats, config as _cfg
            from .covercache import history_add

            _root = _cfg.get("root") or r"D:\音乐"
            rel = os.path.relpath(path, _root).replace("\\", "/")
            stats.record(rel, track.title, track.artists, float(dur or 0))
            history_add(rel, track.title, track.artists)
        except Exception:
            pass
        jobs.log(jid, "完成: %s (%s)" % (os.path.basename(path or ""), msg))
        jobs.finish(jid, "done")
    else:
        jobs.log(jid, "失败: %s" % msg)
        jobs.finish(jid, "error", str(msg))


class Handler(BaseHTTPRequestHandler):
    server_version = "music3/1.0"

    def log_message(self, fmt, *args):
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)

        def g(k, d=""):
            return (qs.get(k) or [d])[0]

        try:
            if u.path in ("/", "/index.html"):
                return self._send(200, PAGE, "text/html; charset=utf-8")

            # ---- PWA 静态资源 ----
            if u.path in ("/manifest.json", "/sw.js", "/icon.svg"):
                import mimetypes

                from . import config as _cfg2

                webdir = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web"
                )
                fp = os.path.join(webdir, u.path.lstrip("/"))
                if not os.path.exists(fp):
                    return self._send(404, {"error": "not found"})
                ctype = mimetypes.guess_type(fp)[0] or "application/octet-stream"
                if u.path == "/sw.js":
                    ctype = "application/javascript; charset=utf-8"
                    # SW 不能被浏览器缓存，否则更新不生效
                    with open(fp, "rb") as f:
                        data = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                    self.send_header("Service-Worker-Allowed", "/")
                    self.end_headers()
                    self.wfile.write(data)
                    return
                with open(fp, "rb") as f:
                    data = f.read()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "public, max-age=600")
                self.end_headers()
                self.wfile.write(data)
                return

            if u.path == "/api/stat":
                return self._send(200, library.count())

            # ---- 任务列表 ----
            if u.path == "/api/jobs":
                from . import jobs

                return self._send(200, {"jobs": jobs.list_jobs(int(g("limit", "20")))})

            # ---- 单任务快照 ----
            if u.path == "/api/job":
                from . import jobs

                jid = g("id").strip()
                snap = jobs.get(jid)
                if not snap:
                    return self._send(404, {"error": "unknown job"})
                return self._send(200, snap)

            # ---- 取消任务 ----
            if u.path == "/api/job/cancel":
                from . import jobs

                ok = jobs.cancel(g("id").strip())
                return self._send(200, {"ok": ok})

            # ---- SSE 实时进度流 ----
            if u.path == "/api/job/sse":
                from . import jobs

                jid = g("id").strip()
                if not jobs.get(jid):
                    return self._send(404, {"error": "unknown job"})
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("X-Accel-Buffering", "no")
                self.end_headers()
                last_ver = -1
                idle = 0
                try:
                    while True:
                        snap = jobs.get(jid)
                        if snap is None:
                            self.wfile.write(
                                b"event: error\ndata: {\"error\":\"gone\"}\n\n"
                            )
                            self.wfile.flush()
                            return
                        if snap["version"] != last_ver:
                            last_ver = snap["version"]
                            self.wfile.write(
                                (
                                    "event: progress\ndata: "
                                    + json.dumps(snap, ensure_ascii=False)
                                    + "\n\n"
                                ).encode("utf-8")
                            )
                            self.wfile.flush()
                            idle = 0
                        else:
                            idle += 1
                            if idle % 20 == 0:
                                self.wfile.write(b": keepalive\n\n")
                                self.wfile.flush()
                        if snap["state"] != "running":
                            self.wfile.write(
                                (
                                    "event: done\ndata: "
                                    + json.dumps(
                                        {
                                            "state": snap["state"],
                                            "ok": snap["ok"],
                                            "skip": snap["skip"],
                                            "fail": snap["fail"],
                                        },
                                        ensure_ascii=False,
                                    )
                                    + "\n\n"
                                ).encode("utf-8")
                            )
                            self.wfile.flush()
                            return
                        time.sleep(0.5)
                except Exception:
                    return

            # ---- 试听：音频流（支持 Range，可拖进度条） ----
            if u.path == "/api/stream":
                from . import stream as _stream

                rel = g("rel", "")
                full = _stream.safe_join(library.DEFAULT_ROOT, rel)
                if not full:
                    return self._send(400, {"error": "invalid path"})
                return _stream.send_file(self, full, "audio/mpeg")

            # ---- 下载单曲到浏览器（带附件头） ----
            if u.path == "/api/file":
                from . import stream as _stream

                rel = g("rel", "")
                full = _stream.safe_join(library.DEFAULT_ROOT, rel)
                if not full:
                    return self._send(400, {"error": "invalid path"})
                name = os.path.basename(full)
                return _stream.send_file(self, full, "audio/mpeg", download_name=name)

            # ---- 封面（带磁盘缓存） ----
            if u.path == "/api/cover":
                from . import stream as _stream, covercache

                rel = g("rel", "")
                full = _stream.safe_join(library.DEFAULT_ROOT, rel)
                if not full:
                    return self._send(400, {"error": "invalid path"})
                data, mime = covercache.get_cover(full)
                if not data:
                    return self._send(404, {"error": "no cover"})
                return _stream.send_bytes(self, data, mime or "image/jpeg")

            # ---- 维护守护 ----
            if u.path == "/api/maintain":
                from . import maintain as _mt

                act = g("act", "")
                if act == "tick":
                    r = _mt.tick(
                        batch=int(g("batch", "20")),
                        sub=g("sub", ""),
                        do_lyric=(g("lyric", "1") == "1"),
                        do_cover=(g("cover", "1") == "1"),
                        do_clean=(g("clean", "1") == "1"),
                        write_id3=(g("write", "1") == "1"),
                        dry=(g("dry", "0") == "1"),
                    )
                    return self._send(200, r)
                if act == "reset":
                    _mt.reset_cursor()
                    return self._send(200, {"ok": True})
                if act == "log":
                    return self._send(
                        200, {"lines": _mt.tail_log(int(g("n", "80")))}
                    )
                return self._send(200, _mt.status())

            # ---- 封面补全 ----
            if u.path == "/api/coverfill":
                from . import coverfill, stream as _stream

                rel = g("rel", "")
                if rel:
                    full = _stream.safe_join(library.DEFAULT_ROOT, rel)
                    if not full:
                        return self._send(400, {"error": "invalid path"})
                    r = coverfill.fill_one(
                        full, write_id3=(g("write", "0") == "1")
                    )
                    d, m = coverfill.get_cached(full)
                    # 缓存失效，清掉封面缓存让前端重新拉
                    try:
                        from . import covercache

                        covercache.cover_cache_clear()
                    except Exception:
                        pass
                    return self._send(200, {
                        "rel": rel,
                        "ok": bool(r.get("ok")),
                        "source": r.get("source") or "",
                        "bytes": len(d) if d else 0,
                        "wrote": bool(r.get("wrote")),
                    })
                if g("clear", "0") == "1":
                    n = coverfill.cache_clear()
                    return self._send(200, {"cleared": n})
                return self._send(200, coverfill.cache_stats())

            # ---- 库健康检查 ----
            if u.path == "/api/health":
                from . import health

                deep = g("deep", "0") == "1"
                lim = int(g("limit", "0")) or None
                dlim = int(g("detail_limit", "30") or 30)   # 每类明细条数上限（默认30防页面爆，清单导出传99999）
                off = int(g("offset", "0") or 0)
                batch = int(g("batch", "0") or 0)
                r = health.scan(library.DEFAULT_ROOT, g("sub", ""), limit=lim, deep=deep,
                                 offset=off, batch=batch)
                # 明细太多会撑爆响应，只带前 30 条
                slim = {}
                for k in ("no_lyric", "no_cover", "bad_name", "no_artist", "tiny", "huge", "dups"):
                    slim[k] = (r.get(k) or [])[:max(1, min(dlim, 200000))]
                return self._send(200, {
                    "total": r["total"],
                    "total_all": r["total_all"],
                    "offset": r["offset"],
                    "batch": r["batch"],
                    "more": r["more"],
                    "total_size_mb": round(r["total_size_mb"], 1),
                    "score": r["score"],
                    "summary": r["summary"],
                    "counts": r.get("counts") or {},
                    "detail": slim,
                    "deep": deep,
                })

            # ---- 导出（直接下载文件） ----
            if u.path == "/api/export":
                from . import export as _export, browse as _browse

                fmt = g("fmt", "m3u8").lower()
                sub = g("sub", "")
                src = g("src", "lib")   # lib | playlist

                if src == "playlist":
                    from . import playlist as _pl

                    d = _pl.get()
                    paths = []
                    for it in d.get("items") or []:
                        p = os.path.join(library.DEFAULT_ROOT, it["rel"].replace("/", os.sep))
                        if os.path.exists(p):
                            paths.append(p)
                else:
                    paths = [t["path"] for t in _browse.list_tracks(library.DEFAULT_ROOT, sub, limit=1000000)]

                if fmt == "index":
                    import json as _j

                    text = _j.dumps(
                        _export.library_index(
                            library.DEFAULT_ROOT, sub,
                            fast=(g("fast", "1") == "1"),
                        ),
                        ensure_ascii=False, indent=1,
                    )
                    name = "music3_index.json"
                    ctype = "application/json; charset=utf-8"
                elif fmt == "json":
                    text = _export.to_json(paths, library.DEFAULT_ROOT, include_lyric=(g("detail", "0") == "1"))
                    name = "music3_playlist.json"
                    ctype = "application/json; charset=utf-8"
                elif fmt == "csv":
                    text = _export.to_csv(paths, library.DEFAULT_ROOT)
                    name = "music3_playlist.csv"
                    ctype = "text/csv; charset=utf-8"
                else:
                    text = _export.to_m3u8(paths, library.DEFAULT_ROOT)
                    name = "music3_playlist.m3u8"
                    ctype = "audio/x-mpegurl; charset=utf-8"

                data = text.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                import urllib.parse as _up

                self.send_header(
                    "Content-Disposition",
                    "attachment; filename*=UTF-8''%s" % _up.quote(name),
                )
                self.end_headers()
                self.wfile.write(data)
                return

            # ---- 歌词补全 ----
            if u.path == "/api/lyric":
                from . import lyricfill, stream as _stream

                rel = g("rel", "")
                if rel:
                    full = _stream.safe_join(library.DEFAULT_ROOT, rel)
                    if not full:
                        return self._send(400, {"error": "invalid path"})
                    # 先看缓存
                    ly = lyricfill.get_cached(full)
                    if ly:
                        return self._send(
                            200, {"rel": rel, "lyric": ly, "source": "cache"}
                        )
                    r = lyricfill.fill_one(full, write_id3=(g("write", "0") == "1"))
                    ly = lyricfill.get_cached(full)
                    return self._send(
                        200,
                        {"rel": rel, "lyric": ly, "source": r.get("source") or "",
                         "ok": bool(ly)},
                    )
                # 缓存管理
                if g("clear", "0") == "1":
                    n = lyricfill.cache_clear()
                    return self._send(200, {"cleared": n})
                return self._send(200, lyricfill.cache_stats())

            # ---- 预听代理：转发在线音频流（带 Referer/UA，绕 CDN 防盗链）----
            if u.path == "/api/pvstream":
                import requests as _rq
                from . import stream as _st2
                url = g("url", "")
                if not url.startswith(("http://", "https://")):
                    return self._send(400, {"error": "bad url"})
                host = urlparse(url).netloc.lower()
                # SSRF 白名单：只放行三家音乐源的 CDN
                ALLOW = (".qq.com", ".gtimg.cn", ".music.163.com", ".126.net",
                         ".163.com", ".bilibili.com", ".bilivideo.com")
                if not any(host.endswith(x) or host == x.strip(".") for x in ALLOW):
                    return self._send(403, {"error": "host not allowed: %s" % host})
                hds = {"Referer": "https://y.qq.com/", "User-Agent": "Mozilla/5.0",
                       "Accept": "*/*"}
                if self.headers.get("Range"):
                    hds["Range"] = self.headers.get("Range")
                try:
                    resp = _rq.get(url, headers=hds, stream=True, timeout=20)
                except Exception as e:
                    return self._send(502, {"error": repr(e)})
                self.send_response(resp.status_code)
                ct = resp.headers.get("Content-Type") or "audio/mpeg"
                self.send_header("Content-Type", ct)
                cl = resp.headers.get("Content-Length")
                if cl:
                    self.send_header("Content-Length", cl)
                for hh in ("Content-Range", "Accept-Ranges"):
                    if resp.headers.get(hh):
                        self.send_header(hh, resp.headers.get(hh))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    for chunk in resp.iter_content(65536):
                        if chunk:
                            self.wfile.write(chunk)
                except Exception:
                    pass
                return

            # ---- 预览试听：取在线直链，返回 URL 给浏览器 <audio> 直连 ----
            global _PV_HITS
            if u.path == "/api/preview":
                import time as _pt
                from . import config as _cfg
                _pv_t0 = _pt.time()
                kw = g("q", "").strip()
                n = int(g("n", "1"))
                srcs = [x.strip() for x in g("sources", "qq,netease").split(",") if x.strip()]
                bili = "bilibili" in srcs
                res = router.search(kw, sources=srcs, limit=15, bili=bili, use_cache=True)
                _pv_search_ms = round((_pt.time() - _pv_t0) * 1000)   # 只算 router.search 段
                _pv_cached = (_pv_search_ms < 300)   # 搜索缓存命中特征: 远快于冷查(~1.5s)
                if not res:
                    return self._send(200, {"ok": False, "log": "无结果"})
                t = None
                et = g("title", "")
                if et:
                    from .models import norm as _norm
                    want_t = _norm(et)
                    want_a = _norm(g("artists", ""))
                    for c in res:
                        if _norm(c.title) == want_t and (not want_a or want_a in _norm(c.artists) or _norm(c.artists) in want_a):
                            t = c
                            break
                if t is None:
                    t = res[min(n, len(res)) - 1]
                import json as _json
                import time as _t2
                from . import config as _cfg2
                _PV_DIR = _cfg2.get("cache_dir") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache", "previews")
                _PV_TTL = 1800  # 取链有效期(vkey 直链一般 30min 内)
                _pv_on_call()   # 取链调用累计(落盘, 命中率分母)
                _pvkey = "%s_%s" % (t.source, t.track_id)
                _pvf = os.path.join(_PV_DIR, _pvkey + ".json")
                url = ext = None
                _url_cached = False
                if os.path.exists(_pvf):
                    try:
                        _pj = _json.load(open(_pvf, encoding="utf-8"))
                        if _pj.get("exp", 0) > _t2.time() and _pj.get("url"):
                            url, ext = _pj["url"], _pj.get("ext", "mp3")
                            _url_cached = True
                            _pv_on_hit()   # 命中计数(落盘累计, 重启不归 0)
                    except Exception:
                        pass
                if url is None and not _url_cached:
                    if t.source == "qq":
                        from . import src_qq
                        url, ext, _q = src_qq.get_url(
                            t.track_id,
                            quality_order=_cfg.get("qq_quality_order") or None,
                        )
                        if not url:
                            alt = downloader._cross_source_url(t)
                            if alt:
                                url, ext = alt[0], alt[1]
                    elif t.source == "netease":
                        from . import src_netease
                        url, ext, _q = src_netease.get_url(t.track_id, expect_sec=t.duration_s)
                    else:
                        return self._send(200, {"ok": False, "log": "B站暂不支持在线预听，用「下载MV」"})
                if url:
                    try:
                        os.makedirs(_PV_DIR, exist_ok=True)
                        _json.dump({"url": url, "ext": ext, "exp": _t2.time() + _PV_TTL},
                                   open(_pvf, "w", encoding="utf-8"))
                    except Exception:
                        pass
                if not url:
                    return self._send(200, {"ok": False, "log": "取链失败（vkey 过期？换一首）"})
                proxy = "/api/pvstream?url=" + _urlquote(url, safe="")
                _pv_total_ms = round((_pt.time() - _pv_t0) * 1000)
                return self._send(200, {"ok": True, "url": url, "proxy": proxy,
                                       "title": t.title, "artists": t.artists,
                                       "ext": ext or "mp3",
                                       "search_ms": _pv_search_ms,
                                       "total_ms": _pv_total_ms,
                                       "cached": _pv_cached,
                                       "url_cached": _url_cached})

            # ---- 曲库文件夹管理：新建/改名/删除（限 DEFAULT_ROOT 内）----
            if u.path == "/api/lib":
                act = g("act", "")
                root = os.path.abspath(library.DEFAULT_ROOT)

                def _safe(rel):
                    rel = (rel or "").strip().replace("/", os.sep).replace("\\", os.sep)
                    if not rel or rel in (os.sep, "."):
                        return None
                    full = os.path.abspath(os.path.join(root, rel))
                    if not full.startswith(root + os.sep):
                        return None
                    return full

                if act == "new":
                    full = _safe(g("sub", ""))
                    if full is None:
                        return self._send(400, {"error": "path escape"})
                    if os.path.exists(full):
                        return self._send(409, {"error": "exists"})
                    try:
                        os.makedirs(full, exist_ok=True)
                    except Exception as e:
                        return self._send(500, {"error": repr(e)})
                    return self._send(200, {"ok": True, "rel": g("sub")})
                if act == "rename":
                    sp, dp = _safe(g("sub", "")), _safe(g("new", ""))
                    if sp is None or dp is None:
                        return self._send(400, {"error": "path escape"})
                    if not os.path.isdir(sp):
                        return self._send(404, {"error": "source not found"})
                    if os.path.exists(dp):
                        return self._send(409, {"error": "target exists"})
                    try:
                        os.rename(sp, dp)
                    except Exception as e:
                        return self._send(500, {"error": repr(e)})
                    return self._send(200, {"ok": True, "rel": g("new")})
                if act == "rm":
                    full = _safe(g("sub", ""))
                    if full is None:
                        return self._send(400, {"error": "path escape"})
                    if not os.path.isdir(full):
                        return self._send(404, {"error": "not found"})
                    left = [x for x in os.listdir(full) if not x.startswith(".")]
                    if left:
                        return self._send(409, {"error": "not empty (%d)" % len(left)})
                    try:
                        os.rmdir(full)
                    except Exception as e:
                        return self._send(500, {"error": repr(e)})
                    return self._send(200, {"ok": True})
                return self._send(400, {"error": "unknown act"})

            # ---- 曲目删除 / 改名（browse 已有能力，补端点）----
            if u.path == "/api/fixmeta":
                # ID3 双缺批量修复：title=清洗文件名，artist=非通用父目录 → 写回 TIT2/TPE1
                import time as _tm
                from . import tagger as _tg, lyricfill as _lf2, browse as _br, tagreader as _tr2
                sub = g("sub", "")
                dry = g("dry", "1") == "1"
                estimate = g("estimate", "") == "1"
                _t0 = _tm.time()
                off = int(g("offset", "0") or 0)
                batch = int(g("batch", "0") or 0)
                _all = _br.list_tracks(library.DEFAULT_ROOT, sub, limit=1000000)
                total_all = len(_all)
                # 快估模式: 只读前 500 首(首片采样), 外推全库估计(避免 236s 全扫)
                if estimate and off == 0:
                    off, batch = 0, min(batch or 500, 500)
                tracks = _all[off: off + batch] if batch > 0 else _all
                todo = []
                for t in tracks:
                    try:
                        tg = _tr2.read_tags(t["path"])
                        if not (tg.get("title") or "").strip() and not (tg.get("artists") or "").strip():
                            a2, ti, src2 = _lf2.guess_meta(t["path"])
                            if ti and len(ti) >= 2:
                                todo.append({"path": t["path"], "rel": t["rel"],
                                             "artist": a2, "title": ti, "src": src2})
                    except Exception:
                        continue
                results = {"scanned": len(tracks), "todo": len(todo),
                           "written": 0, "dry": dry, "items": todo[:40],
                           "total_all": total_all, "offset": off, "batch": batch,
                           "more": (off + len(tracks)) < total_all,
                           "sample_seconds": round(_tm.time() - _t0, 1)}
                if estimate:
                    # 外推: 采样 todo 密度 × 全库规模(采样取首片, 有目录偏差 -> 文案标「约」)
                    results["estimate"] = True
                    results["todo_est"] = (
                        int(round(len(todo) * total_all / max(len(tracks), 1)))
                        if len(tracks) else 0)
                if not dry:
                    for it in todo:
                        try:
                            if _tg.tag(it["path"], title=it["title"], artists=it["artist"]):
                                results["written"] += 1
                        except Exception:
                            pass
                    if results["written"]:
                        try:
                            from . import maintain as _mt2
                            _st2b = _mt2._read_state()
                            _st2b["totals"]["meta_fixed"] = _st2b["totals"].get("meta_fixed", 0) + results["written"]
                            _mt2._write_state(_st2b)
                        except Exception:
                            pass
                return self._send(200, results)

            if u.path == "/api/track":
                from . import browse as _br, stream as _st3
                act = g("act", "")
                rel = g("rel", "")
                full = _st3.safe_join(library.DEFAULT_ROOT, rel)
                if act == "delete":
                    if not full:
                        return self._send(400, {"error": "invalid path"})
                    dry = g("dry", "1") == "1"
                    removed, skipped = _br.delete([full], library.DEFAULT_ROOT, dry=dry)
                    return self._send(200, {"ok": bool(removed), "dry": dry,
                                            "removed": [os.path.relpath(x, library.DEFAULT_ROOT).replace(chr(92),"/") for x in removed],
                                            "skipped": [[a, b] for a, b in skipped]})
                if act == "rename":
                    # 新名字替换旧文件（同目录）
                    new = g("new", "").strip()
                    if not full or not new or "/" in new or "\\" in new or not new.endswith(".mp3"):
                        return self._send(400, {"error": "invalid new name"})
                    if not os.path.exists(full):
                        return self._send(404, {"error": "not found"})
                    dst = os.path.join(os.path.dirname(full), new)
                    if os.path.exists(dst):
                        return self._send(409, {"error": "target exists"})
                    try:
                        os.rename(full, dst)
                    except Exception as e:
                        return self._send(500, {"error": repr(e)})
                    return self._send(200, {"ok": True,
                                            "rel": os.path.relpath(dst, library.DEFAULT_ROOT).replace(chr(92), "/")})
                return self._send(400, {"error": "unknown act"})

            # ---- 歌单链接导入（QQ/网易/B站 歌单页 → 标题表 → 打分下载）----
            if u.path == "/api/plimport":
                from . import playlistimport as _pli, jobs as _jobs3, library as _lib
                import threading
                url = g("url", "").strip()
                act = g("act", "parse")
                okp, payload, ptitle = _pli.parse_url(url)
                if not okp:
                    return self._send(200, {"ok": False, "error": payload, "title": ptitle})
                if act == "parse":
                    return self._send(200, {"ok": True, "title": ptitle, "count": len(payload),
                                            "items": payload})
                # act=download：逐曲交给搜索打分下载（异步 job）
                sub = g("sub") or "投稿\\QQ音乐"
                dest = os.path.join(_lib.DEFAULT_ROOT, sub)
                os.makedirs(dest, exist_ok=True)
                sources = "qq,netease,bilibili"
                jid = _jobs3.create("pl-import", total=len(payload),
                                    meta={"n": len(payload), "title": ptitle})
                _jobs3.log(jid, "歌单导入 %s · %d 首 → %s" % (ptitle or url, len(payload), sub))
                def worker():
                    okc = 0
                    for i, it in enumerate(payload):
                        kw = (it.get("title") or it.get("raw") or "").strip()
                        if not kw:
                            continue
                        try:
                            res = router.search(kw, sources=sources, limit=5, bili=True)
                            if not res:
                                _jobs3.log(jid, "[%d] %s 无结果" % (i+1, kw[:40]))
                            else:
                                tr = res[0]
                                ok, msg, _p = downloader.download(tr, dest)
                                okc += 1 if ok else 0
                                _jobs3.log(jid, "[%d] %s -> %s" % (i+1, kw[:40],
                                            "OK" if ok else msg[:50]))
                        except Exception as e:
                            _jobs3.log(jid, "[%d] 异常 %r" % (i+1, e))
                        _jobs3.log(jid, "")  # 进度心跳
                        if _jobs3.get(jid, 0).get("cancel"):
                            _jobs3.finish(jid, "canceled")
                            return
                    _jobs3.finish(jid, "done" if okc else "error",
                                   "" if okc else "0 首成功")
                threading.Thread(target=worker, daemon=True).start()
                return self._send(200, {"ok": True, "job_id": jid, "total": len(payload),
                                        "title": ptitle})

            # ---- 收藏歌单 ----
            if u.path == "/api/favs":
                from . import favs
                act = g("act", "")
                if act == "add":
                    from . import favs as _f
                    item = {
                        "title": g("title", ""), "artists": g("artists", ""),
                        "source": g("source", ""), "duration": g("duration", ""),
                        "q": g("q", ""), "n": g("n", "1"),
                        "rel": g("rel", ""),
                    }
                    items, added = _f.add(item)
                    return self._send(200, {"ok": True, "added": added, "count": len(items)})
                if act == "add_multi":
                    import json as _j
                    try:
                        rows = _j.loads(g("items", "[]"))
                    except Exception:
                        rows = []
                    items, added = favs.add_many(rows)
                    return self._send(200, {"ok": True, "added": added, "count": len(items)})
                if act == "remove":
                    return self._send(200, {"items": favs.remove(g("key", ""))})
                if act == "clear":
                    return self._send(200, {"items": favs.clear()})
                return self._send(200, {"items": favs.list_items()})

            # ---- 配置读写（音质/登录/赠金） ----
            if u.path == "/api/config":
                from . import config as _cfg
                from . import src_qq as _sq, src_netease as _sn

                if self.command == "POST":
                    try:
                        ln = int(self.headers.get("Content-Length") or 0)
                        body = json.loads(self.rfile.read(ln).decode("utf-8") or "{}")
                        d = _cfg.load(reload=True)
                        changed = False
                        for k in ("qq_quality_order", "qq_cookie", "netease_cookie", "credit_balance", "dest_sub"):
                            if k in body:
                                d[k] = body[k]
                                changed = True
                        if changed:
                            _cfg.save(d)
                            _sq.apply_login(d.get("qq_cookie", ""))
                            _sn.apply_login(d.get("netease_cookie", ""))
                        return self._send(200, {"ok": True})
                    except Exception as e:
                        return self._send(400, {"error": repr(e)})
                d = _cfg.load(reload=True)
                return self._send(200, {
                    "qq_quality_order": d.get("qq_quality_order", [14, 11, 10, 8, 4]),
                    "qq_cookie": d.get("qq_cookie", ""),
                    "netease_cookie": d.get("netease_cookie", ""),
                    "credit_balance": d.get("credit_balance", 100),
                    "credit_spent": d.get("credit_spent", 0),
                    "dest_sub": d.get("dest_sub", ""),
                    # 服务进程实际生效的登录态（单例 session 的 Cookie 头）
                    "qq_cookie_active": bool(_sq._S.headers.get("Cookie")),
                    "netease_cookie_active": bool(_sn._S.headers.get("Cookie")),
                })

            # ---- 手动歌词：多源候选 + 按点拉取 ----
            if u.path == "/api/lyric-fetch":
                from . import lyricfill, stream as _stream

                act = g("act", "")
                if act == "fill":
                    # 按 rel 整曲补词（走 maintain 验证过的 fill_one 管线）
                    rel = g("rel", "")
                    full = _stream.safe_join(library.DEFAULT_ROOT, rel) if rel else None
                    if not full:
                        return self._send(400, {"error": "invalid rel"})
                    r = lyricfill.fill_one(full, write_id3=(g("write", "1") == "1"))
                    return self._send(200, {
                        "ok": bool(r.get("ok")), "source": r.get("source") or "",
                        "msg": r.get("msg") or ("ok" if r.get("ok") else "无词"),
                        "rel": rel,
                    })
                if act == "pick":
                    # 用户点选某源某 id 拉词并落盘
                    src = g("source", "")
                    sid = g("sid", "")
                    rel = g("rel", "")
                    ly, msg = lyricfill.fetch_lyric(src, sid)
                    if ly and rel:
                        full = _stream.safe_join(library.DEFAULT_ROOT, rel)
                        if full:
                            # 同步缓存 + 可选写回 ID3
                            lyricfill.save_cached(full, ly)
                            if g("write", "1") == "1":
                                try:
                                    from . import tagger

                                    tagger.tag(full, lyric=ly)
                                except Exception:
                                    pass
                            # 封面缓存同步失效（mtime 变了）
                            try:
                                from . import covercache

                                covercache.cover_cache_clear()
                            except Exception:
                                pass
                    return self._send(
                        200, {"ok": bool(ly), "lyric": ly, "msg": msg, "source": src}
                    )
                # act=candidates：列出各源同名候选（B站/网易/QQ 都可作为词源）
                cands = lyricfill.find_candidates(
                    g("title", ""), g("artist", ""),
                    tuple(x for x in g("sources", "netease,qq").split(",") if x),
                    limit=int(g("limit", "6")),
                )
                return self._send(200, {"candidates": cands})

            # ---- 歌手搜索 ----
            if u.path == "/api/artists":
                from . import artist as _artist

                name = g("name", "")
                if not name:
                    return self._send(400, {"error": "missing name"})
                srcs = tuple(
                    x for x in g("sources", "qq,netease").split(",") if x
                )
                try:
                    # 纯歌手名搜歌名不匹配 → 分只有 ~0.05，必须放行 min_score
                    ts = _artist.artist_tracks(
                        name,
                        per_source=int(g("limit", "30")),
                        sources=list(srcs),
                        min_score=float(g("min_score", "0.04")),
                    )
                except Exception as e:
                    return self._send(500, {"error": repr(e)})
                # 歌手命中的排前面，去重
                from .models import norm

                nn = norm(name)
                seen = set()
                rows = []
                for t in ts:
                    k = (norm(t.title), norm(t.artists), t.source)
                    if k in seen:
                        continue
                    seen.add(k)
                    hit = 1 if (nn and nn in norm(t.artists)) else 0
                    rows.append({
                        "title": t.title, "artists": t.artists,
                        "source": t.source, "duration": round(float(t.duration_s or 0), 1),
                        "score": round(float(t.score or 0), 3),
                        "page_url": t.page_url or "",
                        "_hit": hit,
                    })
                rows.sort(key=lambda r: (-r["_hit"], -r["score"]))
                for r in rows:
                    r.pop("_hit", None)
                return self._send(200, {"name": name, "items": rows})

            # ---- MV 视频 ----
            if u.path == "/api/mv":
                from . import src_bili

                act = g("act", "")
                if act == "download":
                    # 下载指定 BV 为视频（异步 job）
                    from . import jobs, library as _lib, queue as _q  # noqa
                    from .models import Track
                    from . import config as _cfg
                    import threading

                    bvid = g("bvid", "")
                    if not bvid:
                        return self._send(400, {"error": "missing bvid"})
                    sub = g("sub") or "投稿\\B站"
                    dest = os.path.join(library.DEFAULT_ROOT, sub)
                    tr = Track(
                        source="bilibili", track_id=bvid,
                        title=g("title") or bvid, artists=g("artists") or "",
                        page_url="https://www.bilibili.com/video/" + bvid,
                    )
                    jid = jobs.create("mv", meta={"bvid": bvid, "title": tr.title})
                    threading.Thread(
                        target=_mv_worker, args=(jid, tr, dest), daemon=True
                    ).start()
                    return self._send(200, {"job_id": jid})
                if act == "playlist":
                    from . import jobs as _jobs2  # 局部导入（该分支此前未 import）
                    bvids = [x.strip() for x in g("bvids", "").split(",") if x.strip()]
                    if not bvids:
                        return self._send(400, {"error": "missing bvids"})
                    sub = g("sub") or "投稿\\B站"
                    dest = os.path.join(library.DEFAULT_ROOT, sub)
                    jid = _jobs2.create("mv-batch", total=len(bvids),
                                      meta={"n": len(bvids)})
                    _jobs2.log(jid, "歌单下载 %d 个 B 站视频" % len(bvids))
                    from .models import Track
                    import threading

                    def batch():
                        okc = 0
                        for bv in bvids:
                            tr = Track(
                                source="bilibili", track_id=bv, title=bv,
                                artists="",
                                page_url="https://www.bilibili.com/video/" + bv,
                            )
                            try:
                                from . import src_bili as _sb
                                o2, m2, _p = _sb.download_video(tr, dest)
                                if o2:
                                    okc += 1
                                _jobs2.log(jid, "%s -> %s" % (bv, "OK" if o2 else str(m2)[:60]))
                            except Exception as e:
                                _jobs2.log(jid, "%s 异常 %r" % (bv, e))
                        _jobs2.finish(jid, "done" if okc else "error",
                                    "" if okc else "0 个成功")
                    threading.Thread(target=batch, daemon=True).start()
                    return self._send(200, {"job_id": jid, "total": len(bvids)})
                # act=search：列 MV 候选
                cands = src_bili.search_mv(g("q", ""), limit=int(g("limit", "8")))
                rows = [{
                    "bvid": c.track_id, "title": c.title, "artists": c.artists,
                    "duration": round(float(c.duration_s or 0), 1),
                    "page_url": c.page_url or "",
                } for c in cands]
                return self._send(200, {"items": rows, "q": g("q", "")})

            # ---- 播放列表（可拖拽排序） ----
            if u.path == "/api/playlist":
                from . import playlist

                act = g("act", "")
                if act == "add":
                    return self._send(
                        200,
                        playlist.add(
                            g("rel", ""), g("title", ""), g("artists", "")
                        ),
                    )
                if act == "set":
                    items = []
                    raw = g("items", "")
                    if raw:
                        try:
                            items = json.loads(raw)
                        except Exception:
                            items = []
                    return self._send(
                        200, playlist.set_items(items, g("current", None) or None)
                    )
                if act == "move":
                    return self._send(
                        200, playlist.move(g("from", "0"), g("to", "0"))
                    )
                if act == "remove":
                    return self._send(200, playlist.remove(g("rel", "")))
                if act == "clear":
                    return self._send(200, playlist.clear())
                if act == "current":
                    return self._send(200, playlist.set_current(g("idx", "0")))
                return self._send(200, playlist.get())

            # ---- 播放统计 ----
            if u.path == "/api/stats":
                from . import stats

                act = g("act", "")
                if act == "clear":
                    stats.clear()
                    return self._send(200, {"ok": True})
                if act == "record":
                    stats.record(
                        g("rel", ""), g("title", ""), g("artists", ""),
                        float(g("seconds", "0") or 0),
                    )
                    return self._send(200, {"ok": True})
                if act == "artists":
                    return self._send(
                        200, {"items": stats.top_artists(int(g("limit", "30")))}
                    )
                if act == "top":
                    return self._send(
                        200,
                        {
                            "items": stats.top(
                                g("by", "count"), int(g("limit", "50"))
                            )
                        },
                    )
                return self._send(200, stats.summary())

            # ---- 播放历史 ----
            if u.path == "/api/history":
                from . import covercache

                add = g("add", "")
                if add:
                    covercache.history_add(
                        add, g("title", ""), g("artists", "")
                    )
                if g("clear", "") == "1":
                    covercache.history_clear()
                rm = g("remove", "")
                if rm:
                    covercache.history_remove(rm)
                return self._send(
                    200,
                    {"items": covercache.history_list(int(g("limit", "100")))},
                )

            # ---- 封面缓存管理 ----
            if u.path == "/api/about":
                # 动态计数: 扫 README 累加坑(含×N)+轮数 + git commit 数, 免硬编码 46
                import re as _re
                _pits = 0
                _rounds = 0
                _commits = 0
                _rd = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "README.md")
                try:
                    if os.path.exists(_rd):
                        _txt = open(_rd, "r", encoding="utf-8").read()
                        _rounds = len(_re.findall(r"^## 第\d+轮", _txt, _re.M))
                        for _m in _re.finditer(r"\*\*坑[^*]*\*\*(×\d+)?[:：]", _txt):
                            _pits += int(_m.group(1)[1:]) if _m.group(1) else 1
                except Exception:
                    pass
                try:
                    import subprocess
                    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    _r = subprocess.run(["git", "rev-list", "--count", "HEAD"],
                                        cwd=_root, capture_output=True, text=True, timeout=15)
                    _commits = int((_r.stdout or "").strip() or 0)
                except Exception:
                    _commits = 0
                return self._send(200, {"pits": _pits, "rounds": _rounds, "commits": _commits})

            if u.path == "/api/cache":
                import glob as _glob
                from . import config as _cfg3, covercache, lyricfill

                _cd = _cfg3.get("cache_dir") or os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cache")
                # 取链缓存: _cache 根下 qq_*.json / netease_*.json(TTL 1800s)
                def _pv_stats():
                    fn = 0
                    bz = 0
                    for pat in ("qq_*.json", "netease_*.json"):
                        for f in _glob.glob(os.path.join(_cd, pat)):
                            try:
                                fn += 1
                                bz += os.path.getsize(f)
                            except Exception:
                                pass
                    _pv_flush_hits()   # 读时落一次脏, 保 /api/cache 报准
                    _pv_flush_calls()
                    _rate = min(100, round(_PV_HITS / _PV_CALLS * 100)) if _PV_CALLS else 0
                    return {"files": fn, "bytes": bz, "hits": _PV_HITS, "calls": _PV_CALLS, "hit_rate": _rate}

                if g("clear_all", "") == "1":
                    n1 = covercache.cover_cache_clear()
                    n2 = lyricfill.cache_clear()
                    n3 = 0
                    for pat in ("qq_*.json", "netease_*.json"):
                        for f in _glob.glob(os.path.join(_cd, pat)):
                            try:
                                os.remove(f); n3 += 1
                            except Exception:
                                pass
                    _pv_reset_hits()   # 清缓存连命中计数一起清(删 pv_hits.json + 内存归 0)
                    return self._send(200, {"cleared_covers": n1, "cleared_lyrics": n2, "cleared_previews": n3, "cleared_hits": 1})
                if g("clear", "") == "1":
                    n = covercache.cover_cache_clear()
                    return self._send(200, {"cleared": n})
                # 三缓存: covers(图) + lyrics(lrc) + previews(取链, 命中免 get_url)
                return self._send(200, {
                    "covers": covercache.cover_cache_stats(),
                    "lyrics": lyricfill.cache_stats(),
                    "previews": _pv_stats(),
                })

            # ---- 标签（标题/歌手/时长/歌词） ----
            if u.path == "/api/tags":
                from . import stream as _stream, tagreader

                rel = g("rel", "")
                full = _stream.safe_join(library.DEFAULT_ROOT, rel)
                if not full:
                    return self._send(400, {"error": "invalid path"})
                t = tagreader.read_tags(full)
                t["rel"] = rel
                t["exists"] = os.path.exists(full)
                return self._send(200, t)

            if u.path == "/api/ls":
                from . import browse

                sub = g("sub", "")
                # 始终带 dirs: 空 sub=根层, 非空=该层子目录(原只空 sub 给 dirs -> UI 无法下钻)
                dirs = browse.list_dirs(os.path.join(library.DEFAULT_ROOT, sub) if sub else library.DEFAULT_ROOT)
                if not sub:
                    return self._send(200, {"dirs": dirs})
                rows = browse.list_tracks(
                    library.DEFAULT_ROOT,
                    sub,
                    limit=int(g("limit", "200")),
                    offset=int(g("offset", "0")),
                    read_id3=g("id3", "0") == "1",
                )
                return self._send(200, {"sub": sub, "count": len(rows), "items": rows, "dirs": dirs})

            if u.path == "/api/find":
                from . import browse

                kw = g("q").strip()
                if not kw:
                    return self._send(400, {"error": "q required"})
                hits = browse.find(library.DEFAULT_ROOT, kw, limit=int(g("limit", "50")))
                return self._send(200, {"keyword": kw, "count": len(hits), "items": hits})

            if u.path == "/api/dup":
                from . import dedup

                dups = dedup.find_dups(
                    library.DEFAULT_ROOT, by=g("by", "name")
                )
                tmp = dedup.find_tmp(library.DEFAULT_ROOT)
                return self._send(
                    200,
                    {
                        "dup_groups": len(dups),
                        "sample": [
                            {"key": k, "paths": v} for k, v in dups[: int(g("top", "10"))]
                        ],
                        "tmp_files": len(tmp),
                    },
                )

            if u.path == "/api/search":
                kw = g("q").strip()
                if not kw:
                    return self._send(400, {"error": "q required"})
                srcs = [s.strip() for s in g("sources", "qq,netease").split(",") if s.strip()]
                lim = int(g("limit", "15"))
                bili = "bilibili" in srcs
                res = router.search(kw, sources=srcs, limit=lim, bili=bili)
                return self._send(
                    200, {"keyword": kw, "items": [t.to_dict() for t in res]}
                )

            if u.path == "/api/get":
                kw = g("q").strip()
                if not kw:
                    return self._send(400, {"error": "q required"})
                n = int(g("n", "1"))
                force = g("force", "0") == "1"
                exact_title = g("title", "")
                srcs = [s.strip() for s in g("sources", "qq,netease").split(",") if s.strip()]
                bili = "bilibili" in srcs
                res = router.search(kw, sources=srcs, limit=15, bili=bili)
                if not res:
                    return self._send(200, {"ok": False, "log": "无结果"})
                # 前端给了精确标题（歌手模式关键词只是歌手名）→ 用它选
                t = None
                if exact_title:
                    from .models import norm as _norm

                    et, ea = _norm(exact_title), _norm(g("artists", ""))
                    for c in res:
                        if _norm(c.title) == et and (not ea or _norm(c.artists) == ea or ea in _norm(c.artists)):
                            t = c
                            break
                if t is None:
                    t = res[min(n, len(res)) - 1]
                idx = library.scan()
                old = library.exists(t.title, t.artists, idx)
                if old and not force:
                    return self._send(
                        200,
                        {"ok": True, "log": "已存在: %s" % old, "path": old},
                    )
                d = library.dest_dir(t.source)
                from . import config as _cfgG
                _ds = g("dest", "") or (_cfgG.load().get("dest_sub") or "")
                if _ds:
                    _root_abs = os.path.abspath(library.DEFAULT_ROOT)
                    _cand = os.path.abspath(os.path.join(_root_abs, _ds))
                    if _cand.startswith(_root_abs + os.sep):
                        os.makedirs(_cand, exist_ok=True)
                        d = _cand
                ok, m, path = downloader.download(t, d)
                return self._send(
                    200,
                    {
                        "ok": ok,
                        "log": "%s | %s\n%s" % ("OK" if ok else "FAIL", m, path or ""),
                        "path": path or "",
                    },
                )

            return self._send(404, {"error": "not found"})
        except Exception as e:
            return self._send(500, {"error": repr(e)})

    def do_POST(self):
        u = urlparse(self.path)
        try:
            ln = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(ln).decode("utf-8") if ln else "{}"
            body = json.loads(raw or "{}")
        except Exception:
            return self._send(400, {"error": "bad json"})

        if u.path == "/api/favs" and body.get("act") == "import":
            from . import favs as _favs2
            items = body.get("items")
            if not isinstance(items, list) or not items:
                return self._send(400, {"error": "items required"})
            merged, added = _favs2.add_many(items)
            return self._send(200, {"ok": True, "added": added, "count": len(merged)})

        if u.path == "/api/config":
            from . import config as _cfg
            from . import src_qq as _sq, src_netease as _sn

            d = _cfg.load(reload=True)
            for k in ("qq_quality_order", "qq_cookie", "netease_cookie", "credit_balance", "dest_sub"):
                if k in body:
                    d[k] = body[k]
            if _cfg.save(d):
                _sq.apply_login(d.get("qq_cookie", ""))
                _sn.apply_login(d.get("netease_cookie", ""))
                return self._send(200, {"ok": True})
            return self._send(500, {"error": "save failed"})

        if u.path in ("/api/batch", "/api/queue"):
            kws = body.get("keywords") or []
            if isinstance(kws, str):
                kws = [k.strip() for k in kws.splitlines() if k.strip()]
            if not kws:
                return self._send(400, {"error": "keywords required"})
            n = int(body.get("n", 1))
            workers = int(body.get("workers", 3))
            bili = bool(body.get("bili", False))
            force = bool(body.get("force", False))
            retries = int(body.get("retries", 2))
            dest = str(body.get("dest") or "").strip().replace("/", os.sep)
            root = library.DEFAULT_ROOT
            if dest:
                cand = os.path.abspath(os.path.join(library.DEFAULT_ROOT, dest))
                if cand.startswith(os.path.abspath(library.DEFAULT_ROOT) + os.sep):
                    root = cand
                else:
                    return self._send(400, {"error": "dest outside library"})
            sources = body.get("sources") or (["qq", "netease", "bilibili"] if bili else ["qq", "netease"])

            from . import jobs

            jid = jobs.create("queue", total=len(kws), meta={"n": n, "workers": workers})
            jobs.log(jid, "任务创建：%d 个关键词，并发 %d" % (len(kws), workers))

            def work():
                from . import queue as q

                try:
                    st = q.run(
                        kws,
                        workers=workers,
                        per_kw=n,
                        sources=sources,
                        bili=bili,
                        retries=retries,
                        force=force,
                        job_id=jid,
                        root=root,
                    )
                    jobs.log(
                        jid,
                        "完成: 成功%(ok)d / 跳过%(skip)d / 失败%(fail)d / 共%(total)d" % st,
                    )
                    jobs.finish(jid, "done")
                except Exception as e:
                    jobs.log(jid, "异常: %r" % (e,))
                    jobs.finish(jid, "error", repr(e))

            threading.Thread(target=work, daemon=True).start()
            return self._send(200, {"job": jid, "total": len(kws)})

        return self._send(404, {"error": "not found"})


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("music3 web -> http://%s:%d" % (HOST, PORT), flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
