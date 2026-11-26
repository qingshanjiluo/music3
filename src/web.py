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
/* 维护页 10 卡: 容器宽驱动 auto-fill(桌面 4 列 ~ 窄屏 2 列 ~ 超宽 5 列), 卡片 min 220px 保证 sparkline 不挤 */
.mtgrid{grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
/* 趋势 sparkline 容器: 卡内 100% 宽 + 等高 22px + 底部对齐(挂趋势卡时折线对齐) */
.mtspark{display:block;width:100%;height:22px;margin-top:6px;overflow:hidden;position:relative}
.mtspark svg{display:block;width:100%;height:22px}
@media(max-width:640px){.mtgrid{grid-template-columns:repeat(2,1fr)}.mtgrid .statcard:nth-child(5),.mtgrid .statcard:nth-child(9){grid-column:auto}}
/* 11 卡窄屏折叠: .mtgrid.fold 时只显前 5 卡, 后 6 卡(#mtcards 展开后 .fold 移除)默认隐 */
.mtgrid.fold .statcard:nth-child(n+6){display:none}
#mtcards{display:inline-flex;align-items:center;gap:4px;font-size:12px;color:var(--acc);cursor:pointer;margin-top:6px;padding:2px 8px;background:var(--bg2);border-radius:10px}
#mtcards:hover{background:var(--panel);border-color:var(--acc)}
/* sparkline 末点值标开关: body._nosplabel 时末点值标 .mtspark-lastval 全隐, 窄屏免挤(记 localStorage._mtSparkLabel=0) */
body._nosplabel .mtspark-lastval{display:none}
/* 维护卡 hover 抬升: 悬停看 title 详情有视觉锚点(轻抬1px+阴影+边框 accent), 与曲库卡同语言, 作用域限维护区 */
#mtresult .statcard{transition:transform .15s ease,box-shadow .15s ease,border-color .15s ease}
#mtresult .statcard:hover{transform:translateY(-1px);box-shadow:0 4px 14px rgba(0,0,0,.10);border-color:var(--acc)}
.statcard{
  background:var(--panel);border:1px solid var(--line);border-radius:var(--radius);
  padding:14px 16px;
}
/* 维护卡片 hover 微交互: 抬升 + 阴影 + 末点圆点放大(#mtresult 作用域, 不影响曲库/批量卡片) */
#mtresult .statcard{transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease}
#mtresult .statcard:hover{transform:translateY(-2px);box-shadow:0 6px 18px -8px rgba(0,0,0,.25);border-color:var(--acc)}
#mtresult .statcard:hover .mtspark .mtspark-hover{transition:width .12s ease,height .12s ease}
/* 实时日志新行淡闪: joblog-line background 过渡(新行标黄 1.2s 后清, 平滑淡出) */
.joblog-line{transition:background .3s ease}
/* 日志行含歌名(mp3 基名)时整行可点跳曲库: data-name 有值则 pointer + hover accent 底 + 左侧竖条 */
.joblog-line[data-name]{cursor:pointer}
.joblog-line[data-name]:hover{background:var(--bg2);border-left:2px solid var(--acc);padding-left:8px;margin-left:-10px}
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
    <div id="mtrunprog" style="display:none;width:120px;height:6px;background:var(--bg2);border-radius:3px;overflow:hidden;margin-left:8px;vertical-align:middle" title="本轮进度 (i/N)"><div id="mtrunprogin" style="width:0;height:6px;background:var(--acc);border-radius:3px;transition:width .3s"></div></div>
    <svg id="mtrundonut" viewBox="0 0 36 36" width="30" height="30" style="display:none;vertical-align:middle;margin-left:4px" title="本轮完成度环 (i/N)"><circle cx="18" cy="18" r="14" fill="none" stroke="var(--bg2)" stroke-width="4"/><circle id="mtrundonutc" cx="18" cy="18" r="14" fill="none" stroke="var(--acc)" stroke-width="4" stroke-linecap="round" stroke-dasharray="87.96" stroke-dashoffset="87.96" transform="rotate(-90 18 18)" style="transition:stroke-dashoffset .3s"/><text id="mtrundonuttx" x="18" y="21" text-anchor="middle" font-size="9" font-weight="700" fill="var(--acc)" transform="rotate(90 18 18)">0%</text></svg>
    <span id="mtrunprogtx" style="display:none;font-size:11px;color:var(--acc);font-weight:600;margin-left:6px"></span>
    <button class="ghost" id="mtstat">看状态<span id="mtdotStat" class="mtrun-dot" style="display:inline-block;width:7px;height:7px;border-radius:50%;margin-left:6px;vertical-align:middle;background:var(--dim)" title="自动刷 5s 运行指示"></span></button>
    <button class="ghost sm" id="mtrefresh" title="只重拉 8 卡数据(不重铺日志区)">刷新</button>
    <button class="ghost" id="mtlog">看日志<span id="mtdotLog" class="mtrun-dot" style="display:inline-block;width:7px;height:7px;border-radius:50%;margin-left:6px;vertical-align:middle;background:var(--dim)" title="实时日志运行指示"></span></button>
    <button class="ghost sm" id="mtloglive" title="每 2s 刷新日志(跑维护时挂上)">实时日志</button>
    <button class="ghost sm" id="mtautoref" title="每 5s 自动重拉 9 卡(跑维护/跑到全库时挂着, 实时看累计/delta/本轮补变化)" onclick="mtAutoRef()">自动刷 5s</button>
    <button type="button" id="mtkeyhint" title="键盘快捷: Space 暂停/续跑 · Esc 取消 · Enter 跳双图(维护 tab 激活 + 焦点非输入框时生效)" style="padding:2px 8px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:help;line-height:16px;position:relative">⌨ 键</button>
    <div id="mtkeyhintdetail" style="display:none;position:absolute;z-index:60;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:6px 10px;font-size:11px;color:var(--ink);line-height:1.7;box-shadow:0 2px 8px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none"></div>
    <button type="button" id="mtkeyhintcopy" title="复制键盘流触发记录(三键最近触发时间戳+触发顺序串, 贴工单/记录使用习惯, 与R169/R189/R191/R192复制出口同语言)" style="display:none;padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 复制触发记录</button>
    <button type="button" id="mtguardcopy" title="一键全复制维护守护区(双指标逐轮明细+状态详情+全库完成详情+键盘流触发记录四段, 维护守护区数据一键全留存/全贴工单, 与R189/R191/R192/R195单点复制同语言但全量)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 全复制</button>
    <button type="button" id="mtguardsnap" title="维护守护区四段数据快照可视化(双指标逐轮柱状+状态色带+完成徽标+键盘流顺序条内联SVG, 一眼看维护守护区四段当前全貌, 与R158双图区快照语言同)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">▣ 快照</button>
    <button type="button" id="mtguardsnappng" title="维护守护区四段快照PNG导出(#mtguardsnapd内联SVG转canvas下载music3_维护守护全记录_快照_ts.png, 四段全貌快照可存档/可分享, 与R158双图区PNG快照同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⬇ 快照PNG</button>
    <button type="button" id="mtguardpanel" title="维护守护区能力/出口总览(三键状态灯+四段数据+各复制出口+快照/PNG出口内联SVG总览面板, 维护守护区能力/出口全景图, 一眼知有哪些入口/能力免分散找)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">▤ 总览</button>
    <button type="button" id="mtguardpanelpng" title="维护守护区总览PNG导出(#mtguardpaneld内联SVG转canvas下载music3_维护守护总览_ts.png, 能力/出口全景图PNG存档/可分享, 与R158/R198PNG导出同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⬇ 总览PNG</button>
    <button type="button" id="mtguardpanelcopy" title="维护守护区总览文本复制(能力/出口分块+各出口标位+三键状态/四段数据当前值文本到剪贴板, 总览可文本留存/贴工单, 与R169/R189/R191/R192/R195/R196复制出口同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 总览复制</button>
    <button type="button" id="mtguardpanelfold" title="折叠/展开维护守护区总览面板(_mtGuardPanelFold折叠标志切显/隐, 总览面板常驻可折叠省高不8s自动隐, 与R159折叠双图区语言同)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">▾ 折叠总览</button>
    <button type="button" id="mtguardfoldall" title="折叠/展开维护守护区全浮层(_mtGuardFoldAll折叠标志切显/隐#mtstatebardtl状态详情/#mtmetsumdetail逐轮明细/#mtkeyhintdetail三键提示/_mtguardsnapd四段快照/_mtguardpaneld总览面板, 一键折叠/展开维护守护区全浮层省高, 与R159折叠双图区/R202折叠总览面板语言同)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⊘ 折叠全浮层</button>
    <button type="button" id="mtguardfoldstat" title="维护守护区三域折叠态总览(双图区_mtMetFold/总览面板_mtGuardPanelFold/全浮层_mtGuardFoldAll三域折叠/展开态色带+localStorage记忆标位内联SVG, 三域折叠态一眼全貌免逐点各折叠钮, 与R197四段快照/R199总览面板语言同)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">▣ 折叠总览</button>
    <button type="button" id="mtguardfoldstatpng" title="三域折叠态PNG导出(#mtguardfoldstatd内联SVG转canvas下载music3_维护守护三域折叠态_ts.png, 三域折叠态全貌PNG存档/可分享, 与R158/R198/R200PNG导出同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⬇ 折叠态PNG</button>
    <button type="button" id="mtguardfoldstatcopy" title="三域折叠态文本复制(三域折叠/展开+localStorage记忆值文本到剪贴板, 三域折叠态可文本留存/贴工单, 与R196/R201复制出口同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 折叠态复制</button>
    <button type="button" id="mtguardfoldctl" title="维护守护区折叠全链路总控(三域折叠钮#mtmetfold/_mtguardpanelfold/_mtguardfoldall+折叠联动R206+折叠记忆R204/R205localStorage+三域折叠态总览R207+折叠态PNG/文本R208全折叠出口一张折叠全链路图, 折叠域能力/出口全景图免分散找, 与R199总览面板语言同)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">▤ 折叠全链路</button>
    <button type="button" id="mtguardfoldctlpng" title="折叠全链路PNG导出(#mtguardfoldctld内联SVG转canvas下载music3_维护守护折叠全链路_ts.png, 折叠域全链路PNG存档/可分享, 与R158/R198/R200/R208PNG导出同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⬇ 全链路PNG</button>
    <button type="button" id="mtguardfoldctscopy" title="折叠全链路文本复制(五块分块+各折叠出口标位文本到剪贴板, 折叠全链路可文本留存/贴工单, 与R196/R201/R208复制出口同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 全链路复制</button>
    <button type="button" id="mtguardfoldreset" title="重置维护守护区全折叠记忆(localStorage._mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll/_mtGuardFoldCtl全清0+全折叠出口#mtmetfold/_mtguardpanelfold/_mtguardfoldall/_mtguardfoldctl文案/display恢复展开态, 维护守护区全折叠记忆一键复位)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">↺ 重置折叠</button>
    <button type="button" id="mtguardfoldresetcopy" title="全折叠记忆重置详情复制(4键localStorage复位值+4window标志复位值+4折叠钮文案复位+6浮层display复位+重置时间戳到剪贴板, 全折叠记忆重置详情可文本留存/贴工单, 与R196/R201/R208复制出口同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 重置复制</button>
    <button type="button" id="mtallfoldcopy" title="全折叠域5域折叠态一键复制(R232, 全折叠域5域/5键/5标志/5折叠钮/7浮层当前态文本到剪贴板, 全折叠域5域折叠态一键留存/贴工单, 免逐点各面板/出口, 与R222-R231补全折叠域字段同域)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 全折叠域复制</button>
    <button type="button" id="mtallfoldpng" title="全折叠域5域折叠态PNG快照(R233, 全折叠域5域/5键/5标志/5折叠钮/7浮层当前态内联SVG转canvas下载music3_全折叠域5域折叠态_ts.png, 全折叠域5域折叠态PNG存档/可分享, 与R232全折叠域5域折叠态一键复制同域)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⬇ 全折叠域PNG</button>
    <button type="button" id="mtallfoldstat" title="全折叠域5域折叠态总控浮层(R234, 全折叠域5域/5键/5标志/5折叠钮/7浮层当前态内联SVG浮层, 8s自动隐+折叠记忆localStorage._mtGuardAllFoldStat, 全折叠域5域折叠态一眼全貌+跨会话折叠记忆, 与R232/R233全折叠域5域折叠态一键复制/PNG快照同域)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">▣ 全折叠域浮层</button>
    <div id="mtallfoldstatd" style="display:none;position:absolute;z-index:70;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:6px;box-shadow:0 2px 10px rgba(0,0,0,.12)"></div>
    <button type="button" id="mtguardfoldresetpng" title="全折叠记忆重置详情PNG导出(4键+4标志+4折叠钮+6浮层复位状态SVG转canvas下载music3_全折叠记忆重置详情_ts.png, 全折叠记忆重置详情PNG存档/贴工单, 与R158/R198/R200/R208PNG导出同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⬇ 重置PNG</button>
    <button type="button" id="mtguardalldomain" title="维护守护区全折叠域总控面板(四折叠记忆localStorage键+四折叠出口+全折叠重置/详情复制/详情PNG+全浮层复位出口一张全折叠域总控图, 全折叠域能力/出口全景图免分散找, 与R209折叠全链路总控同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">▣ 全折叠域</button>
    <button type="button" id="mtguardalldomainpng" title="全折叠域总控面板PNG导出(#mtguardalldomains内联SVG转canvas下载music3_全折叠域总控_ts.png, 全折叠域总控面板PNG存档/可分享, 与R158/R198/R200/R208PNG导出同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⬇ 全折叠PNG</button>
    <button type="button" id="mtguardalldomaincopy" title="全折叠域总控文本复制(六块分块+各折叠出口标位文本到剪贴板, 全折叠域总控可文本留存/贴工单, 与R196/R201/R208复制出口同语言)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 全折叠复制</button>
    <div id="mtguardfoldctld" style="display:none;position:absolute;z-index:70;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:10px;color:var(--ink);box-shadow:0 2px 8px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none"></div>
    <div id="mtguardalldomains" style="display:none;position:absolute;z-index:70;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:10px;color:var(--ink);box-shadow:0 2px 8px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none"></div>
    <div id="mtguardfoldstatd" style="display:none;position:absolute;z-index:70;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:10px;color:var(--ink);box-shadow:0 2px 8px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none"></div>
    <div id="mtguardpaneld" style="display:none;position:absolute;z-index:70;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:10px;color:var(--ink);box-shadow:0 2px 8px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none"></div>
    <div id="mtguardsnapd" style="display:none;position:absolute;z-index:70;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:10px;color:var(--ink);box-shadow:0 2px 8px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none"></div>
    <button class="ghost sm" id="mtlogexport" title="导出当前日志(maintain.log 全量)">导出日志</button>
    <button class="ghost sm" id="mtlogcopy" title="复制当前日志到剪贴板(含行号, 贴 issue/分享方便)" onclick="mtLogCopy()">复制日志</button>
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
  <span id="mtlivebadge" style="display:none;margin-top:4px;font-size:11px;color:var(--ok);font-weight:600;position:relative;cursor:default"></span>
  <button type="button" id="mtlivebadgedonecopy" title="复制全库维护完成详情(贴工单/记录维护日志, 与R169/R189/R191复制出口同语言)" style="display:none;margin-left:6px;padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 复制完成</button>
  <div id="mtlivedetail" style="display:none;position:absolute;z-index:60;margin-top:2px;background:var(--bg2);border:1px solid var(--line);border-radius:6px;padding:5px 9px;font-size:11px;color:var(--ink);line-height:1.6;box-shadow:0 2px 8px rgba(0,0,0,.08);white-space:nowrap"><button type="button" id="mtlivedetailcopy" title="复制当前轮双指标详情(贴工单/记录维护日志)" style="pointer-events:auto;padding:0 6px;margin-left:8px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 复制</button></div>
  <div id="mtstatebar" style="height:3px;width:100%;background:var(--line);border-radius:2px;overflow:hidden;position:relative" title="维护状态色带: 绿跑中 / 黄暂停 / 红取消 / 灰完成"></div>
  <div id="mtstatebardtl" style="display:none;position:absolute;z-index:60;background:var(--bg2);border:1px solid var(--line);border-radius:5px;padding:3px 9px;font-size:10px;color:var(--ink);line-height:1.5;box-shadow:0 1px 5px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none;top:6px;left:0"></div><button type="button" id="mtstatebardtlcopy" title="复制维护状态详情(贴工单/记录维护日志, 与R169详情复制/R189逐轮明细复制同「复制出口」)" style="display:none;padding:0 6px;margin-top:2px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">⧉ 复制状态</button>
  <div style="margin-top:4px"><button type="button" id="mtmetfold" title="折叠/展开维护趋势条(耗时折线+补入柱状+汇总, 窄屏省高)" style="padding:0 8px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">▾ 折趋势</button></div>
  <div id="mtmetfoldwrap">
  <div id="mthistspark" style="display:none;margin-top:4px;align-items:center;gap:6px;font-size:11px;color:var(--dim)"><span id="mthistlabel">近 10 次跑维护耗时</span><span id="mthistsvg" style="display:inline-block;width:110px;height:22px;vertical-align:middle"></span><button type="button" id="mthistexport" title="导出跑维护耗时历史为 CSV(近10次, 换设备带历史走)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">↓ 导出</button><button type="button" id="mthistpng" title="折线快照存 PNG(看趋势截图分享, 离屏canvas重绘折线区)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">⊡ 快照</button><button type="button" id="mthistimport" title="导入跑维护耗时历史 CSV(R147 导的回填, 换设备/清历史后把旧 CSV 导回来)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">↑ 导入</button><button type="button" id="mthistreset" title="重置基线(清耗时历史+记当前为0s起算点, 看趋势重定0点)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">⟲ 重置</button><button type="button" id="mthistclear" title="清空跑维护耗时历史(重新计基线, 折线隐)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">✕ 清历史</button></div>
  <div id="mtdeltabar" style="display:none;margin-top:4px;align-items:center;gap:6px;font-size:11px;color:var(--dim)"><span id="mtdeltaLabel">近 10 次跑维护补入量</span><span id="mtdeltaSvg" style="display:inline-block;width:110px;height:22px;vertical-align:middle"></span><span id="mtpairlbl" style="font-size:10px;color:var(--acc);font-weight:600;display:none"></span><button type="button" id="mtdeltaclear" title="清空补入量历史(重计补入基线, 柱状隐)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">✕ 清补入</button><span id="mtmetsum" style="font-size:10px;color:var(--dim);display:none;position:relative"></span><button type="button" id="mtmetsumdetailcopy" title="复制双指标逐轮明细(贴工单/记录维护日志, 与R169详情复制同「复制出口」)" style="display:none;padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px;vertical-align:middle">⧉ 复制</button><div id="mtmetsumdetail" style="display:none;position:absolute;z-index:60;background:var(--bg2);border:1px solid var(--line);border-radius:5px;padding:4px 9px;font-size:10px;color:var(--ink);line-height:1.5;box-shadow:0 2px 6px rgba(0,0,0,.08);white-space:nowrap;pointer-events:none;max-width:280px"></div><button type="button" id="mtmetclear" title="一键全清维护趋势区(耗时+补入量+基线三键一起清, 三图归零)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">⊗ 全清</button><button type="button" id="mtmetpng" title="双指标趋势区快照存 PNG(耗时折线+补入柱状+汇总一张, 整区趋势图存档/贴issue)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">⊡ 快照</button><button type="button" id="mtmetcsv" title="双指标趋势数据导出 CSV(序号,耗时(s),补入量 双列, Excel横评哪次耗时高+补入少, 与R160 PNG互补:PNG走图CSV走数据)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">↓ 双表</button><button type="button" id="mtmetimport" title="导入双指标趋势 CSV(R161 导的回填, 双列 耗时+补入量, 换设备/全清后把双指标带回来)" style="padding:0 6px;font-size:10px;color:var(--dim);background:var(--bg2);border:1px solid var(--line);border-radius:4px;cursor:pointer;line-height:16px">↑ 双表</button></div>
  </div>
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
/* 轮数/批量输入夹取: 手输 0/负/超大值自动夹到合法范围(mtruns 1-50, mtbatch 1-100), 防落 ||默认 */
(function(){ const clip=(id,lo,hi,def)=>{ const el=document.getElementById(id); if(!el) return; el.addEventListener('change',()=>{ let v=Math.round(+el.value); if(isNaN(v)||v<lo) v=lo; if(v>hi) v=hi; el.value=v; }); }; clip('mtruns',1,50,1); clip('mtbatch',1,100,20); })();
/* 本轮进度条: 跑多轮(N>1)时 #mtrunprog 显 i/N, 每轮 update; 跑完/单轮/全库隐; 扫一眼跑到第几轮/还剩多少 */
function _mtProg(i, total, hide){
  const bar=$('#mtrunprog'), fill=$('#mtrunprogin'), tx=$('#mtrunprogtx');
  const don=$('#mtrundonut'), donc=$('#mtrundonutc'), dontx=$('#mtrundonuttx');
  if(hide || (total && total<=1)){ if(bar) bar.style.display='none'; if(tx) tx.style.display='none'; if(fill) fill.style.width='0'; if(don) don.style.display='none'; if(donc) donc.setAttribute('stroke-dashoffset','87.96'); return; }
  if(bar) bar.style.display=''; if(tx) tx.style.display='';
  const pct=Math.min(100, Math.round(i*100/Math.max(1,total)));
  if(fill) fill.style.width=pct+'%';
  if(tx) tx.textContent=i+'/'+total+' 轮';
  /* donut 环: i/N 完成度(与进度条同 pct), r=14 周长 2πr≈87.96, dashoffset 按 (100-pct)% */
  if(don) don.style.display='';
  if(donc) donc.setAttribute('stroke-dashoffset', (87.96*(1-pct/100)).toFixed(2));
  if(dontx) dontx.textContent=pct+'%';
}
/* 取消本轮跑标志: 跑多轮中点「取消」(按钮变红) 置 true, 循环下一轮 break(已跑的轮不回滚, 断点已写); 跑完/取消后按钮回「跑一轮」 */
let _mtAborted=false;
window._mtAborted=_mtAborted; /* R184 挂 window 供 mtStateBarDraw 读取消同态 */
let _mtRunning=false; /* R180 跑维护中标志: Space 暂停需跑维护中才触, document 监听判(块级挂全局 window 可访问) */
window._mtRunning=_mtRunning;
window._mtLiveInfo=null; /* R185 跑中实时信息: mtRun 每轮 tick 存 {i,N,back,dur}, #mtstatebar hover 显状态详情(第i/N轮·本轮回+X·本轮耗Ys) */
async function mtRun(){
  const btn = $('#mtrun');
  _mtAborted=false;
  window._mtAborted=false; /* R184 复位取消标志同步 window */
  _mtRunning=true; window._mtRunning=true; /* R180 跑维护中, Space 暂停判 */
  /* 跑中: 按钮变「取消」(点即跳出, 不 disabled 才能点); 跑完/取消后回「跑一轮」 */
  btn.disabled = false;
  btn.textContent = '取消';
  btn.style.background='var(--bad)';
  const _runOrig=btn.onclick;
  btn.onclick = ()=>{ _mtAborted=true; };
  const b = +$('#mtbatch').value || 20;
  const sub = curSub || '';
  const t0 = Date.now();
  /* 跑前基线快照: 拉 maintain status (cum_trend 末值 + runs) 记 _mtRunBefore, 跑完对比算本次增量(补多少/扫多少); 与 R143 复盘 toast 互补(R143 跑完事后拉, R152 跑前快照跑后对比) */
  let _mtBefore=null;
  try{ const _bf=await (await fetch('/api/maintain')).json(); const _ct=(typeof _bf.cum_trend!=='undefined'&&_bf.cum_trend)||[]; _mtBefore={lyr:_ct.length?(_ct[_ct.length-1].lyric||0):0, cov:_ct.length?(_ct[_ct.length-1].cover||0):0, runs:_bf.runs||0}; try{ localStorage.setItem('_mtRunBefore', JSON.stringify(_mtBefore)); }catch(e){} }catch(e){}
  const FULL = $('#mtfull').checked;   /* 跑到全库: 循环到 done(忽略 N) */
  const N = FULL ? 999999 : Math.max(1, Math.min(50, +$('#mtruns').value || 1));
  /* 跑中 spinner: 按钮文字加转圈, 反馈不空等 */
  const _lab = '取消';
  const _spin = '<span class="spin" style="display:inline-block;width:11px;height:11px;border:2px solid var(--line);border-top-color:#fff;border-radius:50%;margin-right:6px;vertical-align:-1px;animation:spin .7s linear infinite"></span>';
  let ticks=0;
  const setSpin=(i)=>{ btn.innerHTML = _spin + (FULL ? `跑到全库 第 ${i} 轮… 取消` : (N>1 ? `连跑 ${i}/${N}… 取消` : '跑中… 取消')); };
  const _mtUnaborted=()=>{ btn.disabled=true; btn.textContent='跑一轮'; btn.style.background=''; btn.onclick=_runOrig; _mtProg(0,N,true); };
  let doneMsg='';
  let FULL_DONE=false;
  let ticksFirstMs=0;
  let _mtTotalDur=0; /* R167 累计耗时累加器: 每轮 tick 后累加本轮耗, hover #mtlivebadge 详情显累计 */
  let _mtPaused=false; /* R180 暂停态: Space 键暂停跑维护循环(循环顶挂起不跑 tick), 再 Space 续跑; 区别于取消(_mtAborted 回滚断点); 挂 window 供 document 监听读写 */
  window._mtPaused=_mtPaused;
  try{
    for(let i=1;i<=N;i++){
      if(_mtAborted){ setMsg($('#mtmsg'), '已取消 · 跑到第 '+Math.min(i, N)+' 轮（已跑的轮不回滚，断点已写）', 'ok'); _mtUnaborted(); break; }
      /* 暂停检查(R180): window._mtPaused 时循环顶挂起不跑 tick, await setTimeout 轮询 window._mtPaused=false 才续跑(Space 暂停/续跑, 跑中全库挂起不等跑完/不取消) */
      if(window._mtPaused){
        setMsg($('#mtmsg'), '暂停中 · 按 Space 续跑（已跑的 '+Math.max(0,i-1)+' 轮不回滚）', 'warn');
        const _run=$('#mtrun'); if(_run){ _run.textContent='暂停中 · 按 Space 续跑'; _run.style.background='var(--warn)'; _run.style.color='#fff'; _run.style.borderColor='var(--warn)'; }
        while(window._mtPaused){ await new Promise(r=>setTimeout(r,300)); if(_mtAborted){ break; } } /* 轮询暂停态, 续跑(_mtPaused=false)或取消(_mtAborted)才跳出 */
        if(_mtAborted){ setMsg($('#mtmsg'), '已取消 · 跑到第 '+Math.min(i, N)+' 轮（已跑的轮不回滚，断点已写）', 'ok'); _mtUnaborted(); break; }
        _mtUnpausedBtn(); /* 续跑恢复 #mtrun 态 */
      }
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
      } else if(!FULL && N>1 && i>1){
        /* 非全库跑多轮 ETA: 前 i-1 轮均耗 _elapsed/(i-1) × 剩 (N-i) 轮, 实时外推剩多少秒(扫一眼还有多久跑完, 与全库 estTxt 同直觉) */
        const _perTick=Math.max(0.5, _elapsed/(i-1));
        estTxt = ` · 剩 ${N-i} 轮 ≈ 约 ${Math.max(1,Math.round(_perTick*(N-i)))}s`;
      }
      setMsg($('#mtmsg'), `${FULL?'跑到全库 · 第 '+i+' 轮':'跑第 '+i+'/'+N+' 轮'}（每轮 ${b} 首${sub?' · '+sub:''}）… 已耗时 ${_elapsed}s${estTxt}`);
      if(!FULL){ _mtProg(i, N, false); }  /* 本轮进度: 跑多轮显 i/N, 全库(N=999999)不显进度条 */
      const u = `/api/maintain?act=tick&batch=${b}&sub=${encodeURIComponent(sub)}`
        + `&lyric=${$('#mtlyric').checked?1:0}`
        + `&cover=${$('#mtcover').checked?1:0}`
        + `&clean=${$('#mtclean').checked?1:0}`;
      const _t1=Date.now();
      const r = await (await fetch(u)).json();
      if(i===1){ ticksFirstMs = Date.now()-_t1; }
      if(r.error){ setMsg($('#mtmsg'), `第 ${i} 轮错误: ${r.error}`, 'bad'); _mtUnaborted(); _mtProg(0, N, true); return; }
      ticks=i;
      doneMsg = `第 ${i} 轮：扫描 ${r.scanned} 首 · 歌词 +${r.lyric_ok}/-${r.lyric_miss} · 封面 +${r.cover_ok}/-${r.cover_miss} · 清理 ${r.cleaned}` + (r.done ? ' · 已跑完一圈' : '');
      /* 每轮 tick 后推 _mtRunDelta(本轮补入量 r.lyric_ok+r.cover_ok, 逐轮累计) -> 取消(R140 跑到第i轮)时已推轮保留不回滚, 补入量历史不虚; 与 R140「已跑的轮不回滚」同「不回滚」直觉 */
      try{ const _rd=(r.lyric_ok||0)+(r.cover_ok||0); let _dr=[]; try{ _dr=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){} _dr.push(_rd); _dr=_dr.slice(-10); localStorage.setItem('_mtRunDelta', JSON.stringify(_dr)); if(typeof mtRunDeltaDraw==='function'){ mtRunDeltaDraw(); } if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); } }catch(e){}
      /* 每轮 tick 后推 _mtRunHist 本轮耗时((Date.now()-_t1)/100, 逐轮实时耗时趋势) -> 与 R164 每轮推补入量对称(双指标跑中实时), 取消时已推轮保留 */
      try{ const _rdur=Math.round((Date.now()-_t1)/100)/10; let _rh=[]; try{ _rh=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){} _rh.push(_rdur); _rh=_rh.slice(-10); localStorage.setItem('_mtRunHist', JSON.stringify(_rh)); if(typeof mtRunHistDraw==='function'){ mtRunHistDraw(); } if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); } }catch(e){}
      /* 跑中双指标实时徽标(R166): 每轮 tick 后刷「跑中·第i/N轮·本轮回+X·本轮耗Ys」, 扫一眼当前跑双指标实况 */
      _mtTotalDur=Math.round((_mtTotalDur+(Date.now()-_t1))/100)/10;
      try{ if(typeof mtLiveBadge==='function'){ mtLiveBadge(i, N, (r.lyric_ok||0)+(r.cover_ok||0), Math.round((Date.now()-_t1)/100)/10, r.lyric_ok||0, r.cover_ok||0, _mtTotalDur, N); } }catch(e){}
      /* 跑中每轮 tick 自动跟最新轮(R173): 双图区在视口内时 #mtdelthover/#mtpairlbl 自动跟到本轮, 跑中滚动看双图趋势最新柱逐轮推进免手 hover */
      try{ if(typeof mtFocusLatest==='function' && $('#mtdeltabar') && $('#mtdeltabar').style.display!=='none'){ const _db=$('#mtdeltabar').getBoundingClientRect(); if(_db.bottom>0 && _db.top<window.innerHeight){ mtFocusLatest(); } } }catch(e){}
      if(typeof mtStateBarDraw==='function'){ mtStateBarDraw(); } /* R184 跑中每轮 tick 同步指示条(绿跑中, 暂停挂起时不 tick 停在上轮色) */
      window._mtLiveInfo={i:i, N:N, back:(r.lyric_ok||0)+(r.cover_ok||0), dur:Math.round((Date.now()-_t1)/100)/10}; /* R185 跑中实时信息: #mtstatebar hover 显状态详情(第i/N轮·本轮回+X·本轮耗Ys) */
      if(r.done){ if(FULL){ setMsg($('#mtmsg'), `跑到全库完成 · 共 ${i} 轮 · `+doneMsg, 'ok'); _toast('跑到全库完成 · 共 '+i+' 轮 · 已挂自动刷看 9 卡 · 点双图区汇总跳双图看趋势', 'ok'); if(typeof _mtAutoRefTimer==='undefined'||_mtAutoRefTimer===null){ if(typeof mtAutoRef==='function') mtAutoRef(); } FULL_DONE=true; break; } if(i<N){ doneMsg += '（下一圈）'; } }
    }
    _mtProg(N, N, !(FULL_DONE||doneMsg)); /* 跑完/全库完成隐进度条(非全库 N/N 跑完也隐, 跑中才显) */
    _mtUnaborted(); /* 跑完恢复「跑一轮」按钮态(跑中是「取消」红) */
    if(FULL_DONE){ /* 全库跑完完成态(R187): #mtlivebadge 显「已跑完·共N轮·耗时Xs」绿--ok(不Hide, 全库收尾看徽标完成态), 与 #mtstatebar 完成灰双路知全库收尾 */
      if(typeof mtLiveBadgeDone==='function'){ mtLiveBadgeDone(N, _mtTotalDur); }
    } else {
      if(typeof mtLiveBadgeHide==='function'){ mtLiveBadgeHide(); } /* 非全库跑完/取消隐跑中双指标实时徽标(R166) */
    }
    /* 跑维护历史: 本次耗时(dur)推 localStorage._mtRunHist(近10次), 顶栏 #mtmsg 下挂小 sparkline(近几次跑耗时趋势, 跨维护会话粒度看越来越快/变慢, 与 R126 dur_trend 同 sparkline 语言但跨「跑维护」粒度) */
    try{
      const _hDur=Math.round((Date.now()-t0)/100)/10;
      let _h=[]; try{ _h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
      _h.push(_hDur); _h=_h.slice(-10);
      localStorage.setItem('_mtRunHist', JSON.stringify(_h));
      mtRunHistDraw();
    }catch(e){}
    if(!(FULL_DONE || doneMsg)) setMsg($('#mtmsg'), (N>1?`连跑 ${N} 轮完成 · `:'') + doneMsg, 'ok');
    /* 跑完 toast 汇报本轮结果(右上角停留6s, 不遮挡卡片): 非全库普通跑完也给, 全库完成另有专属 toast */
    if(!FULL_DONE && doneMsg){ const _tm='跑完 '+(N>1?N:'1')+' 轮 · '+doneMsg+' · 点双图区汇总（#mtmetsum）跳双图看趋势 + 聚焦最新轮'; _toast(_tm, 'ok'); }
    /* R180 跑完/取消复位: 跑维护中标志置 false(Space 暂停不再触) + 暂停态复位(下次跑不继承暂停) */
    _mtRunning=false; window._mtRunning=false; window._mtPaused=false;
    if(typeof mtStateBarDraw==='function'){ mtStateBarDraw(); } /* R184 跑完/取消同步指示条(取消红/完成灰) */
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
      /* 跑完结果复盘: 本轮补入 delta(cum_trend 相邻差) + ETA 实际 vs 估算偏差, 扫一眼这轮补了多少/估得准不准(与 R124 delta 徽标 + R141 ETA 同「结果复盘」直觉) */
      if(!FULL_DONE && doneMsg){
        const _ct=st2.cum_trend||[]; let _delta='';
        if(_ct.length>=2){
          const _prev=_ct[_ct.length-2], _cur=_ct[_ct.length-1];
          const _dLy=(_cur.lyric||0)-(_prev.lyric||0), _dCv=(_cur.cover||0)-(_prev.cover||0), _dT=_dLy+_dCv;
          _delta=` 本轮 +${_dT}（歌词 ${_dLy} 封面 ${_dCv}）`;
        }
        /* ETA 偏差: 实际总耗时 vs 跑中估的「约 Xs/轮×N 轮」(R141 estTxt 同算法, 复盘估得准不准) */
        const _actualS=Math.round((Date.now()-t0)/100)/10;
        let _etaTxt='';
        if(N>1 && !FULL && ticks>=1){
          const _perTick=Math.max(0.5,_actualS/Math.max(1,ticks-1||1));
          const _est=Math.round(_perTick*Math.max(1,N-ticks));
          _etaTxt=` · 实测 ${_actualS}s${ticks<N?`（估剩 ${_est}s）`:''}`;
        }
        if(_delta || _etaTxt){ _toast('复盘: '+(_delta||'')+_etaTxt, 'ok'); }
        /* 跑前基线对比(R152): _mtBefore(跑前记的 cum_trend 末值+runs) vs st2(跑后) -> 本次跑补多少/扫多少, 与 R143 复盘(事后拉)互补 */
        if(_mtBefore && st2){
          const _ct2=st2.cum_trend||[];
          const _curL=_ct2.length?(_ct2[_ct2.length-1].lyric||0):0;
          const _curC=_ct2.length?(_ct2[_ct2.length-1].cover||0):0;
          const _dL=_curL-(_mtBefore.lyr||0), _dC=_curC-(_mtBefore.cov||0);
          const _dR=(st2.runs||0)-(_mtBefore.runs||0);
          const _snap='本次跑: 补 +' + _dL + ' 歌词 / +' + _dC + ' 封面（跑前 ' + (_mtBefore.lyr||0) + '/' + (_mtBefore.cov||0) + '）· runs ' + (_mtBefore.runs||0) + '→' + (st2.runs||0) + (_dR>0?'（'+_dR+' 轮）':'');
          _toast(_snap, 'ok');
          /* 推 _mtRunDelta(近10次每次跑补入增量), R153 mini 条形图看横评哪次跑高效 */
          try{ let _dd=[]; try{ _dd=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){} _dd.push(_dL+_dC); _dd=_dd.slice(-10); localStorage.setItem('_mtRunDelta', JSON.stringify(_dd)); mtRunDeltaDraw(); }catch(_){}
        }
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
/* 小结点击跳卡: 点「异常率/本批耗时/累计歌词/封面」滚到对应 .statcard + 闪一下, 双向定位(小结↔卡片) */
function _mtJump(sel){
  const m=s=>document.querySelector(s);
  /* lyr/cov: 累计补歌词/封面卡(按 .k 文本定位, 非固定 nth-child); rate: 异常率卡; dur: 本批耗时卡; runs: 已跑轮次卡; prog: 全库进度条(#mtprog, 非卡) */
  let el;
  if(sel==='lyr') el=[...document.querySelectorAll('#mtresult .statcard')].find(c=>{const k=c.querySelector('.k'); return k&&k.textContent.indexOf('累计补歌词')>=0;});
  else if(sel==='cov') el=[...document.querySelectorAll('#mtresult .statcard')].find(c=>{const k=c.querySelector('.k'); return k&&k.textContent.indexOf('累计补封面')>=0;});
  else if(sel==='dur') el=[...document.querySelectorAll('#mtresult .statcard')].find(c=>{const k=c.querySelector('.k'); return k&&k.textContent.indexOf('本批耗时')>=0;});
  else if(sel==='runs') el=[...document.querySelectorAll('#mtresult .statcard')].find(c=>{const k=c.querySelector('.k'); return k&&k.textContent.indexOf('已跑轮次')>=0;});
  else if(sel==='prog') el=document.querySelector('#mtprog');
  else el=m('#mtresult .statcard[data-jumplog="异常"]');
  if(!el) return;
  el.scrollIntoView({block:'center',behavior:'auto'});
  /* 目标卡常亮 4s(outline 3px + 左侧 accent 竖条 inset shadow, 定位更醒目), 不是闪 3 次看不清落哪张 */
  if(el._mtHiT) clearTimeout(el._mtHiT);
  el.style.outline='3px solid var(--acc)'; el.style.outlineOffset='2px';
  el.style.boxShadow='inset 4px 0 0 var(--acc)';
  el._mtHiT=setTimeout(()=>{ el.style.outline=''; el.style.outlineOffset=''; el.style.boxShadow=''; el._mtHiT=null; },4000);
}
/* 小结里 data-jumpto 链接绑 _mtJump (mtStat 重建后重新绑, 非 passive 才能 preventDefault) */
document.addEventListener('click', function(e){
  const a=e.target.closest && e.target.closest('#mtdigest a[data-jumpto]');
  if(a){ e.preventDefault(); _mtJump(a.dataset.jumpto); }
});
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
      const _valLabel=`<span class="mtspark-lastval" style="position:absolute;left:100%;top:${yOf(_lastVal)}%;transform:translate(-50%,-160%);font-size:10px;font-weight:600;color:${color};white-space:nowrap">${_lastVal}</span>`;
      /* 折线下面积渐变填充: 折线点 + 底边两点闭合成 polygon, linearGradient 纵向(顶透明->底 color@0.16), 每卡唯一 gid 免多卡冲突 */
      const _gid='spk'+(++_sparkSeq);
      const _area=pts+' '+w+','+h+' 0,'+h;
      /* 面积/渐变用 CSS 变量色时, linearGradient 的 stop 需具体色 - 传 color 可能是 var(), stop-color 支持 var() */
      return `<div class="mtspark" data-tr='${encodeURIComponent(JSON.stringify({t:tr,c:color,l:label||''}))}' style="position:relative;cursor:crosshair" title="${tt}"><svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" style="width:100%;height:22px;display:block"><defs><linearGradient id="${_gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${color}" stop-opacity="0"></stop><stop offset="1" stop-color="${color}" stop-opacity="0.18"></stop></linearGradient></defs><title>${tt}</title><polygon points="${_area}" fill="url(#${_gid})" stroke="none"/><polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round"/></svg>${_dot(yOf(tr[0]),0,4)}${_dot(yOf(_lastVal),100,6)}${_valLabel}<span class="mtspark-hover" style="position:absolute;left:-99px;top:0;width:8px;height:8px;margin:-4px 0 0 -4px;border-radius:50%;background:${color};border:2px solid #fff;box-shadow:0 0 4px rgba(0,0,0,.3);display:none;pointer-events:none"></span><span class="mtspark-hoverlbl" style="position:absolute;left:-99px;top:-14px;font-size:10px;font-weight:600;color:${color};white-space:nowrap;display:none;pointer-events:none"></span></div>`; };
    const _runSpark = _sparkSvg((s.trend||[]).slice(-8), (s.runs||0)>=400?'var(--ok)':'var(--acc)', '已跑轮次');
    const _lyrSpark = _sparkSvg(((s.cum_trend||[]).slice(-8)).map(o=>o.lyric), 'var(--acc)', '累计歌词');
    const _covSpark = _sparkSvg(((s.cum_trend||[]).slice(-8)).map(o=>o.cover), 'var(--acc)', '累计封面');
    /* 维护小结: 一行汇总本轮关键(补歌词/补封面/已跑/全库/异常率/本批耗时), 挂卡片网格上方, 扫一眼全貌不用逐卡读 */
    const _last=s.last||{}, _dLy=_last.lyric_ok||0, _dCv=_last.cover_ok||0, _dSc=_last.scanned||0;
    /* 本轮补入 delta 徽标: 上轮补入 = cum_trend 相邻差(cum_trend[末] - cum_trend[末-1]), delta = 本轮 - 上轮(升+N绿, 降/平dim) */
    const _ct=(s.cum_trend||[]);
    const _prevLy = (_ct.length>=2) ? Math.max(0,(_ct[_ct.length-1].lyric||0)-(_ct[_ct.length-2].lyric||0)) : 0;
    const _prevCv = (_ct.length>=2) ? Math.max(0,(_ct[_ct.length-1].cover||0)-(_ct[_ct.length-2].cover||0)) : 0;
    const _deltaLy=_dLy-_prevLy, _deltaCv=_dCv-_prevCv;
    const _deltaCls=d=> d>0?'var(--ok)':(d<0?'var(--bad)':'var(--dim)');
    const _deltaBadge=(d,lbl)=>{ const sign=d>0?'+':''; return `<span id="${lbl}" title="与上一轮比(上轮补 ${d>0?_prevLy:_prevCv} 条)" style="font-size:11px;font-weight:600;color:${_deltaCls(d)};margin-left:6px">${sign}${d}</span>`; };
    const _prog=s.n_total?Math.min(100,Math.round(Math.min((s.runs||0)*20,s.n_total)*100/s.n_total)):0;
    /* 异常率/本批耗时: 取 rate_trend/dur_trend 末位(本轮), 异常率>0 变红提示 */
    const _rateArr=s.rate_trend||[], _durArr=s.dur_trend||[];
    const _rate=_rateArr.length?_rateArr[_rateArr.length-1]:0;
    const _dur=_durArr.length?_durArr[_durArr.length-1]:0;
    const _rateCol=_rate>0?'var(--bad)':'var(--ok)';
    /* 累计歌词/封面: 用 t.totals(累计, 非本轮 _dLy), 也包 <a data-jumpto=lyr/cov> 跳对应累计卡 */
    const _cumLy=t.lyric||0, _cumCv=t.cover||0;
    const _jumpLy=`<a href="javascript:void(0)" data-jumpto="lyr" style="color:var(--acc);text-decoration:underline dotted;font-weight:600" title="点击跳「累计补歌词」卡">${_cumLy}</a>`;
    const _jumpCv=`<a href="javascript:void(0)" data-jumpto="cov" style="color:var(--acc);text-decoration:underline dotted;font-weight:600" title="点击跳「累计补封面」卡">${_cumCv}</a>`;
    const _done2=_prog>=100;
    const _jumpRuns=`<a href="javascript:void(0)" data-jumpto="runs" style="color:var(--ink);text-decoration:underline dotted;font-weight:700" title="点击跳「已跑轮次」卡">${s.runs||0}</a>`;
    const _jumpProg=`<a href="javascript:void(0)" data-jumpto="prog" style="color:${_done2?'var(--ok)':'var(--acc)'};text-decoration:underline dotted;font-weight:700" title="点击跳「全库进度条」">${_prog}%</a>`;
    const _jumpRate=`<a href="javascript:void(0)" data-jumpto="rate" style="color:${_rateCol};text-decoration:underline dotted;font-weight:600" title="点击跳「异常率」卡">${_rate}%</a>`;
    const _jumpDur=_dur?`<a href="javascript:void(0)" data-jumpto="dur" style="color:var(--acc);text-decoration:underline dotted;font-weight:600" title="点击跳「本批耗时」卡">${_dur}s</a>`:`<span style="color:var(--muted)">-</span>`;
    const _digest=`累计 歌词 ${_jumpLy} + 封面 ${_jumpCv}（本轮补 ${_dLy}${_deltaBadge(_deltaLy,'mtdeltaLy')}+${_dCv}${_deltaBadge(_deltaCv,'mtdeltaCv')}，扫 ${_dSc} 首）｜ 异常率 ${_jumpRate} ｜ 本批 ${_jumpDur} ｜ 已跑 ${_jumpRuns} 轮 ｜ 全库进度 ${_jumpProg} ｜ ${esc(s.last_run_str||'从未运行')}`;
    /* 本轮补入 mini 横滑条: recent 近 5 条 pill, 横向滚 + 溢出省略, 扫一眼刚补了啥(不展开最近补入区), 点 pill 跳曲库
       (用内联判 what, 不复用 _wIcon/_wColor——它们在 #mtrecent 块定义, 此时 _recBar 还没执行到, 避免 TDZ) */
    const _recBar=(()=>{ const rr=s.recent||[]; if(!rr.length) return '';
      const _wI=w=> w==='lyric'?'歌词':'封面', _wC=w=> w==='lyric'?'var(--acc)':'var(--ok)';
      const _pill=r=>`<span style="display:inline-flex;align-items:center;gap:5px;padding:3px 9px;background:var(--bg2);border-radius:12px;font-size:12px;white-space:nowrap;cursor:pointer" onclick="_mtLoc(this)" data-name="${(r.name||'').replace(/"/g,'&quot;')}" title="${_wI(r.what)} · 点击去曲库搜这首"><span style="color:${_wC(r.what)};font-weight:600">${_wI(r.what)}</span><span style="max-width:160px;overflow:hidden;text-overflow:ellipsis;color:var(--ink)">${(r.name||'').replace(/</g,'&lt;')}</span></span>`;
      return `<div id="mtrecentbar" style="display:flex;gap:6px;overflow-x:auto;white-space:nowrap;padding:2px 0 4px;margin-bottom:10px" title="本轮补入近 5 条(横滑看全, 点 pill 跳曲库)"><span style="font-size:11px;color:var(--dim);align-self:center;flex:0 0 auto">本轮补入</span>${rr.map(_pill).join('')}</div>`; })();
    $('#mtresult').innerHTML = `
      <div id="mtdigest" style="font-size:13px;font-weight:600;color:var(--ink);margin-bottom:8px;padding:8px 12px;background:var(--panel);border:1px solid var(--line);border-radius:var(--radius)" title="维护小结: 本轮补入(歌词/封面)+ 累计轮次 + 全库进度; 挂卡片网格上方扫一眼全貌">${_digest}</div>
      ${_recBar}
      <button type="button" id="mtcards" onclick="mtCardsFold()" title="窄屏折叠: 默认前 5 卡, 展开全部 11 卡 / 收起" style="display:${_recBar?'':'none'}">▾ 展开全部卡片</button>
      <button type="button" id="mtspklabel" onclick="mtSparkLabelToggle()" title="sparkline 末点值标开/关: 关则各卡折线末点数字隐(窄屏免挤), 记 localStorage">末点值标: 开</button>
      <div class="statgrid mtgrid" id="mtcardgrid">
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
        /* 5% 警戒线: rate_trend 值域 0..max, 阈值 5% 在 sparkline 高度的相对位置 (max<=5 时贴底, >5 按 5/max 定位); 超阈值(rate>5)标 ⚠ */
        const _rMax = Math.max(5, ...((s.rate_trend||[]).slice(-8)));
        const _thrTop = Math.max(0, Math.round(44 - (5/_rMax)*44)); /* sparkline 高 44, 阈值 5% 的 top 偏移 */
        const _over = rate>5;
        /* 左轴数值刻度: 0(贴底) / 5(=警戒线 _thrTop) / 10(若值域内), 按 _rMax 值域定位, 扫状态定位异常率相对量级 */
        const _t10 = _rMax>=10 ? Math.round(44 - (10/_rMax)*44) : -1;
        const _tick = (top, v, warn)=> `<div style="position:absolute;left:-16px;top:${top}px;font-size:8px;color:${warn?'var(--bad)':'var(--dim)'};transform:translateY(-50%)">${v}</div>`;
        $('#mtresult .statgrid').insertAdjacentHTML('beforeend',
          `<div class="statcard" data-jumplog="异常" style="cursor:pointer" title="维护日志(近 200 行)异常占比 = 异常 ${bad} / ${lls.length}；异常含 miss/失败/超时/error/无封面，>5% 变红；点我看日志"><div class="k">异常率（日志 ${lls.length} 行）${_over?' <span style="color:var(--bad);font-size:10px">⚠ 超 5% 警戒</span>':''}</div><div class="v" style="${rate>5?'color:var(--bad);-webkit-text-fill-color:var(--bad)':rate>0?'color:var(--warn);-webkit-text-fill-color:var(--warn)':'color:var(--ok);-webkit-text-fill-color:var(--ok)'}">${rate}%</div><div style="position:relative;padding-left:18px">${_rateSpark}<div style="position:absolute;left:18px;right:0;top:${_thrTop}px;height:0;border-top:1px dashed ${_over?'var(--bad)':'var(--dim)'}" title="5% 警戒线(异常率越过即超阈值)"></div>${_tick(_thrTop,'5',_over)}${_tick(44,'0',false)}${_t10>=0?_tick(_t10,'10',false):''}<div style="position:absolute;right:2px;top:${_thrTop-11}px;font-size:9px;color:var(--dim)">5%</div></div></div>`);
        /* 第 10 卡「本批耗时」: 本轮 tick 用时(s) + 近 8 次耗时趋势(sparkline 复用), 看每批是否变慢(网络/磁盘拖慢)
           耗时异常标记: 末位 _dur 超 mean(dur_trend)+2σ 时卡头标「⚠ 本批变慢」(本批显著慢于近期, 提示网络/磁盘拖慢某批) */
        {
          const _durT = (s.dur_trend||[]);
          const _dur = _durT.length ? _durT[_durT.length-1] : 0;
          /* 均值 + 2σ 警戒: _slow = 末位 > mean + 2*std (dur_trend 不足 3 条时不判异常, 样本太少) */
          const _dArr=_durT.slice(-8).filter(x=>typeof x==='number');
          const _dMean=_dArr.length?_dArr.reduce((a,b)=>a+b,0)/_dArr.length:0;
          const _dStd=_dArr.length>=3?Math.sqrt(_dArr.reduce((a,b)=>a+(b-_dMean)*(b-_dMean),0)/_dArr.length):0;
          const _slow=_dArr.length>=3 && _dur>_dMean+2*_dStd;
          const _durSpark = _sparkSvg(_durT.slice(-8), _slow?'var(--warn)':'var(--muted)', '本批耗时(s)');
          $('#mtresult .statgrid').insertAdjacentHTML('beforeend',
            `<div class="statcard" title="最新一批 tick 用时(秒)；下方折线=近 8 批耗时趋势(变长=网络/磁盘拖慢); 超均值+2σ 标「本批变慢」"><div class="k">本批耗时（近 8 批）${_slow?' <span style="color:var(--warn);font-size:10px">⚠ 本批变慢(超均值+2σ)</span>':''}</div><div class="v" style="${_slow?'color:var(--warn);-webkit-text-fill-color:var(--warn)':''}">${_dur?_dur+'s':'-'}</div>${_durSpark}</div>`);
        }
        /* 第 11 卡「补入速率」: cum_trend 每批增量(lyric+cover 相邻差)近 8 点 sparkline, 看补入速度是否稳定/掉速 */
        {
          const _ct=(s.cum_trend||[]);
          /* 每批增量速率 = 相邻累计差(lyric+cover), 取末 8 批; 末位=本批, 看速度是否掉(掉=源慢/网络波动/已补完) */
          const _rateArr=[];
          for(let i=1;i<_ct.length;i++){ _rateArr.push((_ct[i].lyric||0)+(_ct[i].cover||0)-((_ct[i-1].lyric||0)+(_ct[i-1].cover||0))); }
          const _rShow=_rateArr.slice(-8);
          const _rLast=_rShow.length?_rShow[_rShow.length-1]:0;
          /* 掉速标记: 末位 < 近 4 批均值的一半 (本批补入明显变慢, 提示源慢/网络波动/该库补完) */
          const _rAvg=_rShow.length>=4?_rShow.slice(-4).reduce((a,b)=>a+b,0)/Math.min(4,_rShow.length):0;
          const _rSlow=_rShow.length>=4 && _rLast<_rAvg/2;
          const _rateSpark=_sparkSvg(_rShow, _rSlow?'var(--warn)':'var(--ok)', '补入速率(首/批)');
          $('#mtresult .statgrid').insertAdjacentHTML('beforeend',
            `<div class="statcard" title="每批补入速率 = 相邻批累计补入差(歌词+封面, 首/批); 下方折线=近 8 批补入速度(掉速=源慢/网络波动/该库已补完)"><div class="k">补入速率（近 8 批）${_rSlow?' <span style="color:var(--warn);font-size:10px">⚠ 掉速</span>':''}</div><div class="v" style="${_rSlow?'color:var(--warn);-webkit-text-fill-color:var(--warn)':''}">${_rShow.length?_rLast+' 首/批':'-'}</div>${_rateSpark}</div>`);
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
        /* 全库进度: runs*20/n_total (已跑轮数×每批20首 / 全库总量), 封顶 100%, 纯 CSS/SVG 无库
           donut 环(完成度直觉) + 进度条并排: 环心显百分比, 环按完成度填色(accent->ok) */
        {
          const _scanned = Math.min((s.runs||0)*20, s.n_total||1);
          const _pct = s.n_total ? Math.min(100, Math.round(_scanned*100/(s.n_total))) : 0;
          const _done = _pct>=100;
          const _pc = _done?'var(--ok)':'var(--acc)';
          const _ptxt = _done?'全库已扫完 ✓':'全库进度';
          /* 预计跑完全库还需 N 分钟: 按 dur_trend 末位本批耗时(_perTick)×剩轮数 外推; 完成时显「已扫完」 */
          const _perTick = (s.dur_trend && s.dur_trend.length) ? Math.max(0.5, s.dur_trend[s.dur_trend.length-1]) : 10;
          const _left = _done ? 0 : Math.ceil((s.n_total - _scanned)/20);
          const _etaMin = _done ? 0 : Math.max(1, Math.round(_perTick*_left/60));
          const _etaTxt = _done ? '全库已扫完 ✓' : ('预计还需约 <b style="color:'+_pc+'">'+_etaMin+'</b> 分钟 · 剩 '+_left+' 批 · 每批约 '+Math.round(_perTick)+'s');
          /* donut: SVG circle r=26 (周长 2πr≈163.4), stroke-dasharray 163.4, dashoffset 按 (100-pct)% 缩 */
          const _C = 2*Math.PI*26;
          const _off = _C*(1-_pct/100);
          const _donut = `<svg id="mtdonut" viewBox="0 0 60 60" width="56" height="56" style="flex:0 0 auto;transform:rotate(-90deg)" title="全库完成度环 (已扫 ${_scanned}/${s.n_total||'-'} 首)"><circle cx="30" cy="30" r="26" fill="none" stroke="var(--bg2)" stroke-width="6"/><circle cx="30" cy="30" r="26" fill="none" stroke="${_pc}" stroke-width="6" stroke-linecap="round" stroke-dasharray="${_C}" stroke-dashoffset="${_off}" style="transition:stroke-dashoffset .4s ease"/><text x="30" y="33" text-anchor="middle" font-size="13" font-weight="700" fill="${_pc}" style="transform:rotate(90deg);transform-origin:30px 30px">${_pct}%</text></svg>`;
          $('#mtresult').insertAdjacentHTML('beforeend',
            `<div style="margin-top:6px;display:flex;gap:14px;align-items:center" id="mtprog" title="全库维护进度 = 已跑轮次×20 / 全库总量; 封顶100%(断点续传后重头算)">${_donut}<div style="flex:1"><div style="font-size:12px;color:var(--muted);margin-bottom:4px">${_ptxt} <b style="color:${_pc}">${_pct}%</b>（已扫约 ${_scanned} / ${s.n_total||'-'} 首）</div><div style="height:8px;background:var(--bg2);border-radius:4px;overflow:hidden"><div style="height:8px;width:${_pct}%;background:${_pc};border-radius:4px;transition:width .3s"></div></div><div id="mteta" style="font-size:11px;color:var(--dim);margin-top:4px">${_etaTxt}</div></div></div>`);
          /* 断点位置可视化: cursor._all 相对路径尾 2 段(去盘符前缀) + 全库已扫位置标记, 扫状态一眼看到断点在哪首 */
          const _curPath = (s.cursor && s.cursor._all) ? s.cursor._all : '';
          const _rel = _curPath.replace(/^[A-Za-z]:\\+[^\\]*\\?/, ''); /* 去盘符+第一层(D:\音乐\), 留相对路径 */
          const _tail = _rel ? _rel.split('\\').slice(-2).join('\\') : '';
          const _cursorHtml = _tail
            ? `<div id="mtcursor" style="margin-top:6px;font-size:11px;color:var(--dim);padding:6px 10px;background:var(--panel);border:1px dashed var(--line);border-radius:var(--radius)" title="断点续传游标: 下次「跑维护」从这里继续扫(已补的不重补, 只重扫定位)"><span style="color:var(--muted)">断点续传游标</span> <b style="color:var(--acc);font-family:ui-monospace,Consolas,monospace">${esc(_tail)}</b><span style="color:var(--dim);margin-left:8px">· 已扫约 ${_scanned} / ${s.n_total||'-'} 首 · 下次跑维护从此处续</span></div>`
            : `<div id="mtcursor" style="margin-top:6px;font-size:11px;color:var(--dim);padding:6px 10px;background:var(--panel);border:1px dashed var(--line);border-radius:var(--radius)" title="断点已重置/未设置, 下次跑维护从头扫全库">断点未设置（下次跑维护从头扫全库）</div>`;
          $('#mtresult').insertAdjacentHTML('beforeend', _cursorHtml);
          /* 累计歌词/封面占比双段条: t.lyric vs t.cover 累计补入数, 双段条(歌词=accent, 封面=ok)看哪类补得多, 与 donut 完成度同「比例」直觉 */
          {
            const _mLy = (t && t.lyric)||0, _mCv=(t && t.cover)||0;
            const _mTot = _mLy+_mCv;
            const _mLyPct = _mTot?Math.round(_mLy*100/_mTot):0, _mCvPct=_mTot?100-_mLyPct:0;
            $('#mtresult').insertAdjacentHTML('beforeend',
              `<div id="mtmixbar" style="margin-top:6px" title="累计补入占比: 歌词 vs 封面(看哪类补得多)"><div style="display:flex;justify-content:space-between;font-size:11px;color:var(--dim);margin-bottom:3px"><span><b style="color:var(--acc)">歌词 ${_mLy}</b>（${_mLyPct}%）</span><span><b style="color:var(--ok)">封面 ${_mCv}</b>（${_mCvPct}%）</span></div><div style="height:8px;background:var(--bg2);border-radius:4px;overflow:hidden;display:flex"><div style="height:8px;width:${_mLyPct}%;background:var(--acc);transition:width .3s"></div><div style="height:8px;width:${_mCvPct}%;background:var(--ok);transition:width .3s"></div></div></div>`);
          }
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
          /* 筛选 tab 切换: 事件委托到 #mtrf(随 mtStat 重建), 切当前 data-mf 行, 高亮选中 tab; 记 localStorage._mtRf(重开维护 tab 恢复上次筛选) */
          const _mtRfApply=mf=>{ document.querySelectorAll('#mtrf button').forEach(x=>{ x.style.background=''; x.style.color=''; x.style.borderColor=''; });
            document.querySelectorAll('#mtrecent .mtrecent-rows').forEach(rr=>{ rr.style.display=(rr.dataset.mf===mf)?'':'none'; });
            const sel=document.querySelector('#mtrf button[data-mf="'+mf+'"]'); if(sel){ sel.style.background='var(--acc)'; sel.style.color='#fff'; sel.style.borderColor='var(--acc)'; } };
          document.querySelectorAll('#mtrf button').forEach(bn=>{
            bn.onclick=()=>{ const mf=bn.dataset.mf; _mtRfApply(mf); try{ localStorage.setItem('_mtRf', mf); }catch(e){} };
          });
          /* 载入: 按 localStorage._mtRf 恢复上次筛选(缺省 all), 重开维护 tab 不丢筛选 */
          try{ const _rm=localStorage.getItem('_mtRf'); if(_rm){ _mtRfApply(_rm); } }catch(e){}
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
  /* 11 卡窄屏折叠统一点控: #mtcardgrid + 后 6 卡铺完后按 _mtCards + 窄屏定 .fold */
  applyMtFold();
}
let _mtlogTimer=null;
let _mtLogLastLines=[];   /* 上次 mtLogDraw 的日志行, 实时刷新时对比找新增行淡闪 */
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
  /* 新增行检测: 与上次 _mtLogLastLines 比, 尾部多出的行是新日志(实时刷新才淡闪, kw 过滤态不闪) */
  const _isNew = i=>{ if(kw) return false; const prevLen=_mtLogLastLines.length; if(prevLen>=lines.length) return false; return i>=(lines.length-(lines.length-prevLen)) && _mtLogLastLines.indexOf(lines[i])<0; };
  const _isNewIdx = ()=>{ if(kw) return []; const _prevLen=_mtLogLastLines.length; if(_prevLen>=lines.length) return []; return lines.slice(lines.length-Math.min(50,lines.length-_prevLen)).map((l,idx)=>lines.length-(lines.length-_prevLen)+idx).filter(i=>_mtLogLastLines.indexOf(lines[i])<0); };
  /* 日志区摘要: 总行数 + 异常行数(miss/error/失败/超时/无封面) + 歌词/封面补入行数, 扫日志先有全貌(kw 态用过滤后行)
     异常/歌词补/封面补 数包 <a data-lf> 点击填 #mtlogfilter 过滤(异常->miss, 歌词补->歌词, 封面补->封面), 摘要↔过滤联动 */
  const _isBad = l=>/miss|error|Exception|失败|超时|无封面/i.test(l);
  const _nTotal = lines.length;
  const _nBad = lines.filter(_isBad).length;
  const _nLy = lines.filter(l=>/歌词/.test(l) && !_isBad(l)).length;
  const _nCv = lines.filter(l=>/封面/.test(l) && !_isBad(l)).length;
  const _lfLink = (v, label, n)=> `<a href="javascript:void(0)" data-lf="${escL(v)}" style="color:var(--acc);text-decoration:underline dotted;font-weight:600" title="点击过滤含「${escL(v)}」的日志行">${label} ${n}</a>`;
  const _logStat = `<div id="mtlogstat" style="font-size:11px;color:var(--dim);margin-bottom:4px">${kw?('（匹配 <b style="color:var(--acc)">'+_nTotal+'</b> 行 · 过滤 '+escL(kw)+' <a href="javascript:void(0)" data-lf="" style="color:var(--acc);text-decoration:underline" title="清除过滤">清除</a>）'):''}共 ${_nTotal} 行 ｜ ${_lfLink('miss','异常',_nBad)} ｜ ${_lfLink('歌词','歌词补',_nLy)} · ${_lfLink('封面','封面补',_nCv)}</div>`;
  /* 实时刷新自动滚底: 重铺前记旧日志是否贴底(sticky), 重铺后若贴底则滚到底看最新; 手动上翻过则不抢 */
  const _oldJl=document.querySelector('#mtjoblog');
  const _sticky = _oldJl ? (_oldJl.scrollTop+_oldJl.clientHeight >= _oldJl.scrollHeight-8) : true;
  $('#mtresult').innerHTML = lines.length
    ? `<div id="mtlogwrap" style="position:relative">${_logStat}<div class="joblog" id="mtjoblog" style="max-height:320px;overflow:auto;font-family:ui-monospace,Consolas,monospace">${lines.map((l,i)=>{ const _mp3=(l.match(/([\u4e00-\u9fa5A-Za-z0-9 ._-]+\.mp3)/)||[])[1]||''; const _nm=_mp3.replace(/\.mp3$/i,'').trim(); const _dn=_nm?(' data-name="'+_nm.replace(/"/g,'&quot;')+'" title="点击去曲库搜这首：'+escL(_nm)+'"'):''; return '<div class="joblog-line" data-i="'+i+'"'+_dn+' style="padding:0 2px;'+(_isNew(i)?'background:#fff3d6;':'')+'"><span class="lineno" style="display:inline-block;width:34px;min-width:34px;color:var(--dim);text-align:right;margin-right:8px;user-select:none;opacity:.6">'+(i+1)+':</span>'+paint(l)+'</div>'; }).join('')}</div><button type="button" id="mtlogtop" onclick="mtLogTop()" style="position:absolute;right:10px;bottom:10px;width:30px;height:30px;border-radius:50%;background:var(--panel);border:1px solid var(--acc);color:var(--acc);cursor:pointer;display:none;font-size:14px;line-height:1;z-index:2" title="日志滚到顶">↑</button></div>`
    : `<div class="n">${kw?'无匹配「'+escL(kw)+'」的日志':'日志为空'}</div>`;
  /* 重铺后若刷新前贴底, 自动滚底(实时日志看最新; 首次打开无旧日志 _sticky=true 也滚底) */
  const _newJl=document.querySelector('#mtjoblog');
  if(_newJl && _sticky){ _newJl.scrollTop=_newJl.scrollHeight; }
  _mtLogLastLines=lines.slice();
  /* 新行淡闪 1.2s 后清(实时刷新时有新日志滚进, 高亮提示; 1.2s 后背景淡出) */
  const _newIdx=_isNewIdx();
  if(_newIdx.length){ setTimeout(()=>{ document.querySelectorAll('#mtjoblog .joblog-line').forEach(el=>{ el.style.background=''; }); },1200); }
  /* 滚到顶悬浮钮: 日志滚过 40px 显, 点滚顶 */
  const _jl=$('#mtjoblog'); if(_jl){ _jl.onscroll=()=>{ const b=$('#mtlogtop'); if(b) b.style.display=(_jl.scrollTop>40)?'':'none'; }; }
  return lines.length;
}
/* 日志滚到顶: 点 #mtlogtop 上箭头, 滚日志回顶 + 隐按钮 */
function mtLogTop(){ const j=$('#mtjoblog'); if(j){ j.scrollTop=0; j.onscroll&&j.onscroll(); const b=$('#mtlogtop'); if(b) b.style.display='none'; } }
/* 日志复制到剪贴板: 取 #mtjoblog 当前可见行(行号+正文), 贴 issue/分享; 优先 clipboard API, 降级 execCommand */
function mtLogCopy(){
  const j=$('#mtjoblog'); if(!j){ _toast('日志还没加载，先点「看日志」','bad'); return; }
  const lines=[...j.querySelectorAll('.joblog-line')];
  if(!lines.length){ _toast('日志为空','bad'); return; }
  /* 复制内容 = 行号 + 正文(去 lineno span, 只 .joblog-line 文本), 保留过滤态(只复制当前显示的过滤结果) */
  const txt=lines.map(el=>el.textContent).join('\n');
  /* 过滤态标记: #mtlogfilter 有值时复制的是「命中行」, toast 带(过滤 X)+ #mtlogcopy 钮 title 动态标, 贴 issue 精准 */
  const f=document.querySelector('#mtlogfilter'), kw=f?(f.value||'').trim():'';
  const _cbtn=document.querySelector('#mtlogcopy');
  const done=()=>{ _toast('已复制 '+lines.length+' 行日志到剪贴板'+(kw?'（过滤「'+kw+'」）':''),'ok'); if(_cbtn){ _cbtn.textContent='复制日志'+(kw?'（已过滤 '+lines.length+' 行）':''); } };
  if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(txt).then(done).catch(()=>{ const ta=document.createElement('textarea'); ta.value=txt; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); done(); }); }
  else { const ta=document.createElement('textarea'); ta.value=txt; document.body.appendChild(ta); ta.select(); document.execCommand('copy'); ta.remove(); done(); }
}
/* 日志摘要 data-lf 点击快速过滤: 填 #mtlogfilter + 触发 input(mtLogDraw 重过滤), 摘要↔过滤联动(全局委托, mtLogDraw 重铺后自动生效) */
document.addEventListener('click', function(e){
  const a=e.target.closest && e.target.closest('#mtlogstat a[data-lf]');
  if(!a) return;
  e.preventDefault();
  const f=document.querySelector('#mtlogfilter');
  if(f){ f.value=a.dataset.lf||''; f.dispatchEvent(new Event('input',{bubbles:true})); }
});
/* 日志行含歌名(data-name)点击跳曲库: #mtjoblog 行整行可点 -> _mtLoc(填 #fq + doFind + 闪首项), 日志发现异常曲名直接跳核对(全局委托, mtLogDraw 重铺后自动生效) */
document.addEventListener('click', function(e){
  const row=e.target.closest && e.target.closest('#mtjoblog .joblog-line[data-name]');
  if(!row) return;
  _mtLoc(row);
}, false);
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
/* 子视图运行指示小点: #mtdotStat(自动刷)/#mtdotLog(实时日志) 开=绿脉动 关=灰, 扫一眼知道哪条在跑 */
function _mtDot(id, on){ const d=document.getElementById(id); if(!d) return; d.style.background=on?'var(--ok)':'var(--dim)'; d.style.boxShadow=on?'0 0 0 3px rgba(47,125,85,.25)':'none'; d.style.transition='background .3s ease,box-shadow .3s ease'; }
function mtAutoRef(){
  const btn=document.getElementById('mtautoref');
  if(_mtAutoRefTimer){ clearInterval(_mtAutoRefTimer); _mtAutoRefTimer=null; if(btn){ btn.classList.remove('on'); btn.style.background=''; btn.style.borderColor=''; } _mtDot('mtdotStat', false); setMsg($('#mtmsg'), '自动刷已停', 'ok'); try{ localStorage.setItem('_mtAuto','0'); }catch(e){} return; }
  if(btn){ btn.classList.add('on'); btn.style.background='var(--acc)'; btn.style.borderColor='var(--acc)'; }
  _mtDot('mtdotStat', true);
  setMsg($('#mtmsg'), '自动刷 · 每 5s 重拉 9 卡…');
  mtStat().catch(()=>{});
  _mtAutoRefTimer=setInterval(()=>{ mtStat().catch(()=>{}); }, 5000);
  try{ localStorage.setItem('_mtAuto','1'); }catch(e){}
}
/* 载入时恢复自动刷状态: localStorage._mtAuto==1 则自动挂(刷新页面后免再手动点「自动刷 5s」) */
(function(){ try{ if(localStorage.getItem('_mtAuto')==='1'){ document.addEventListener('DOMContentLoaded', function(){ mtAutoRef(); }); } }catch(e){} })();
function mtLogLive(){
  if(_mtlogTimer){ clearInterval(_mtlogTimer); _mtlogTimer=null; _mtDot('mtdotLog', false); setMsg($('#mtmsg'), '实时日志已停', 'ok'); return; }
  _mtDot('mtdotLog', true);
  setMsg($('#mtmsg'), '实时日志 · 每 2s 刷新…');
  mtLogDraw().catch(()=>{});
  _mtlogTimer=setInterval(()=>{ mtLogDraw().catch(()=>{}); }, 2000);
}
/* 跑维护历史 sparkline: #mtmsg 下小折线(近10次跑耗时, 跨维护会话粒度, 看越来越快/变慢; 与 R126 dur_trend 同 sparkline 语言但跨「跑维护」粒度) */
function mtRunHistDraw(){
  let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  const wrap=$('#mthistspark'), svg=$('#mthistsvg'), lbl=$('#mthistlabel');
  if(!wrap) return;
  /* _mtRunHist 空但有基线(R150 重置记的 _mtRunHistBase): 不 return, 显基线标签态(无折线, 看距基线多久); 无历史无基线才隐 */
  const _hasBase=!!(function(){ try{ return localStorage.getItem('_mtRunHistBase'); }catch(_){ return null; } })();
  if(!h.length && !_hasBase){ wrap.style.display='none'; return; }
  wrap.style.display='flex';
  if(!h.length){ /* 基线标签态: 无折线, 标签显「基线 <ts> · 距基线 X」 */
    const lbl0=$('#mthistlabel'); const svg0=$('#mthistsvg'); if(svg0){ svg0.innerHTML=''; }
    const base=localStorage.getItem('_mtRunHistBase');
    const d=Math.max(0,Date.now()-(+base)); const hh=Math.floor(d/3600000), mm=Math.floor(d/60000)%60, ss=Math.floor(d/1000)%60;
    const dt=hh>0?(hh+'h '+mm+'m'):(mm>0?(mm+'m '+ss+'s'):(ss+'s'));
    const bts=new Date(+base).toISOString().replace('T',' ').slice(5,16);
    if(lbl0){ lbl0.textContent='基线 '+bts+' · 距基线 '+dt+'（还没跑维护，下次跑维护从 0s 起算）'; }
    return;
  }
  const w=110, hgt=22, pad=2;
  const mx=Math.max.apply(null,h), mn=Math.min.apply(null,h), rng=Math.max(1e-3, mx-mn);
  const pts=h.map((v,i)=>{ const x=h.length>1? i/(h.length-1)*w : w/2; const y=pad+(1-(v-mn)/rng)*(hgt-2*pad); return x.toFixed(1)+','+y.toFixed(1); }).join(' ');
  const area=pts+' '+w+','+hgt+' 0,'+hgt;
  const avg=Math.round((h.reduce((a,c)=>a+c,0)/h.length)*10)/10;
  lbl.textContent='近 '+h.length+' 次跑维护耗时 · 均值 '+avg+'s';
  svg.innerHTML='<div class="mthistbox" data-hh="'+encodeURIComponent(JSON.stringify(h))+'" style="position:relative;width:110px;height:22px"><svg viewBox="0 0 '+w+' '+hgt+'" preserveAspectRatio="none" style="width:110px;height:22px;display:block"><defs><linearGradient id="mthistg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="var(--acc)" stop-opacity="0"></stop><stop offset="1" stop-color="var(--acc)" stop-opacity="0.18"></stop></linearGradient></defs><polygon points="'+area+'" fill="url(#mthistg)"/><polyline points="'+pts+'" fill="none" stroke="var(--acc)" stroke-width="1.5" stroke-linecap="round"/></svg><span id="mthisthover" style="position:absolute;left:-99px;top:0;width:8px;height:8px;margin:-4px 0 0 -4px;border-radius:50%;background:var(--acc);border:2px solid #fff;box-shadow:0 0 4px rgba(0,0,0,.3);display:none;pointer-events:none"></span><span id="mthisthovlbl" style="position:absolute;left:-99px;top:-14px;font-size:10px;font-weight:600;color:var(--acc);white-space:nowrap;display:none;pointer-events:none"></span></div>';
  /* 基线附注: R150 重置记的 _mtRunHistBase, 有基线时 #mthistlabel 附「基线 <ts> · 距基线 X」(看趋势重定0点后随时知道距基线多久补X) */
  try{ const base=localStorage.getItem('_mtRunHistBase'); if(base){ const d=Math.max(0,Date.now()-(+base)); const hh=Math.floor(d/3600000), mm=Math.floor(d/60000)%60, ss=Math.floor(d/1000)%60; const dt=hh>0?(hh+'h '+mm+'m'):(mm>0?(mm+'m '+ss+'s'):(ss+'s')); const bts=new Date(+base).toISOString().replace('T',' ').slice(5,16); lbl.textContent+= ' · 基线 '+bts+' · 距基线 '+dt; } }catch(e){}
  if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); }
}
/* 跑维护历史折线 hover 数值跟随: document 捕获 mousemove/mouseout, 命中 #mthistbox 按 x 定位最近点, 显该次耗时(与 R134 维护卡 sparkline hover 同「hover 看值」直觉, 顶栏小折线也能扫单次耗时) */
document.addEventListener('mousemove', function(e){
  const box=e.target.closest && e.target.closest('#mthistspark .mthistbox');
  if(!box){ const d1=document.getElementById('mthisthover'), l1=document.getElementById('mthisthovlbl'); if(d1) d1.style.display='none'; if(l1) l1.style.display='none'; return; }
  const raw=box.getAttribute('data-hh'); if(!raw) return;
  let h=[]; try{ h=JSON.parse(decodeURIComponent(raw)); }catch(_){ return; }
  const r=box.getBoundingClientRect(), pad=2, hgt=22;
  const mx=Math.max.apply(null,h), mn=Math.min.apply(null,h), rng=Math.max(1e-3, mx-mn);
  const frac=Math.min(1,Math.max(0,(e.clientX-r.left)/r.width));
  const idx=Math.round(frac*(h.length-1));
  const val=h[idx];
  const y=pad+(1-(val-mn)/rng)*(hgt-2*pad);
  const dot=document.getElementById('mthisthover'), lbl=document.getElementById('mthisthovlbl');
  if(dot){ dot.style.display='block'; dot.style.left=(frac*100)+'%'; dot.style.top=y+'px'; }
  if(lbl){ lbl.style.display='block'; lbl.style.left=(frac*100)+'%'; lbl.style.top=(y-10)+'px'; lbl.textContent=val+'s'; }
  /* 双图联动(R155): 命中耗时折线同 frac, 同时点亮补入柱状第 idx 柱(#mtdelthover/#mtdelthovlbl), 扫一眼「耗时 Xs + 补入 +Y」配对 */
  try{ const db=document.querySelector('#mtdeltabar .mtdeltabox'); if(db && db.getAttribute('data-hd')){ let dd=[]; try{ dd=JSON.parse(decodeURIComponent(db.getAttribute('data-hd'))); }catch(_){}
    if(dd.length){ const didx=Math.round(frac*(dd.length-1)); const dmx=Math.max.apply(null,dd)||1; const dy=20-Math.max(2,Math.round(dd[didx]/dmx*18));
      const ddot=document.getElementById('mtdelthover'), dlbl=document.getElementById('mtdelthovlbl');
      if(ddot){ ddot.style.display='block'; ddot.style.left=(frac*100)+'%'; ddot.style.top=dy+'px'; }
      if(dlbl){ dlbl.style.display='block'; dlbl.style.left=(frac*100)+'%'; dlbl.style.top=(dy-10)+'px'; dlbl.textContent='+'+dd[didx]; } } } }catch(_){}
  /* 配对值合并标签(R156): 命中耗时折线同frac, #mtpairlbl 显「第N次跑·耗时Xs·补入+Y」(两指标一行汇总, 扫一眼这次跑整体) */
  try{ const _pb=document.querySelector('#mtdeltabar .mtdeltabox'); if(_pb && _pb.getAttribute('data-hd')){ let _pd=[]; try{ _pd=JSON.parse(decodeURIComponent(_pb.getAttribute('data-hd'))); }catch(_){}
    if(_pd.length){ const _pi=Math.round(frac*(_pd.length-1)); const _pmx=Math.max.apply(null,_pd)||1; const _pdd=_pd[_pi];
      const pl=document.getElementById('mtpairlbl'); if(pl){ pl.style.display='inline-block'; pl.textContent='第 '+(_pi+1)+' 次跑 · 耗时 '+val+'s · 补入 +'+_pdd; } } } }catch(_){}
}, true);
document.addEventListener('mouseout', function(e){
  const box=e.target.closest && e.target.closest('#mthistspark .mthistbox');
  if(box){ const d1=document.getElementById('mthisthover'), l1=document.getElementById('mthisthovlbl'); if(d1) d1.style.display='none'; if(l1) l1.style.display='none';
    const pl=document.getElementById('mtpairlbl'); if(pl) pl.style.display='none'; }
}, true);
/* 载入: 按 _mtRunHist 画跑维护历史 sparkline(跨会话, 重开还在) */
(function(){ if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', function(){ mtRunHistDraw(); }); } else { mtRunHistDraw(); } })();
/* 补入量 mini 条形图: #mtdeltabar 小柱状(近10次每次跑补入量, 横评哪次跑高效, 与 R144 耗时折线同区双指标); 跑完推 _mtRunDelta, 载入也画 */
function mtRunDeltaDraw(){
  let d=[]; try{ d=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  const wrap=$('#mtdeltabar'), svg=$('#mtdeltaSvg'), lbl=$('#mtdeltaLabel');
  if(!wrap) return;
  if(!d.length){ wrap.style.display='none'; return; }
  wrap.style.display='flex';
  const mx=Math.max.apply(null,d)||1;
  const n=d.length;
  const bars=d.map((v,i)=>{ const bh=Math.max(2, Math.round(v/mx*18)); const bw=Math.floor(90/n)-1; return '<rect x="'+(i*(Math.floor(90/n)))+1+'" y="'+(20-bh)+'" width="'+bw+'" height="'+bh+'" rx="1" fill="var(--ok)" opacity="'+(v>0?0.85:0.3)+'"/>'; }).join('');
  const total=d.reduce((a,c)=>a+c,0);
  lbl.textContent='近 '+n+' 次跑维护补入 · 合计 +'+total+'（绿=补入, 空=没补到）';
  svg.innerHTML='<div class="mtdeltabox" data-hd="'+encodeURIComponent(JSON.stringify(d))+'" style="position:relative;width:110px;height:22px"><svg viewBox="0 0 100 22" preserveAspectRatio="none" style="width:110px;height:22px;display:block"><line x1="0" y1="20" x2="100" y2="20" stroke="var(--line)" stroke-width="1"/>'+bars+'</svg><span id="mtdelthover" style="position:absolute;left:-99px;top:0;width:7px;height:7px;margin:-3px 0 0 -3px;border-radius:50%;background:var(--ok);border:2px solid #fff;box-shadow:0 0 4px rgba(0,0,0,.3);display:none;pointer-events:none"></span><span id="mtdelthovlbl" style="position:absolute;left:-99px;top:-14px;font-size:10px;font-weight:600;color:var(--ok);white-space:nowrap;display:none;pointer-events:none"></span></div>';
  if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); }
}
/* 补入量柱状 hover 数值跟随: document 捕获 mousemove/mouseout, 命中 #mtdeltabar .mtdeltabox 按 x 定位最近柱, 显该次补入量+X(与 R145 历史折线 hover 同「hover 看值」直觉, 顶栏柱状也能扫单次补入) */
document.addEventListener('mousemove', function(e){
  const box=e.target.closest && e.target.closest('#mtdeltabar .mtdeltabox');
  if(!box){ const d1=document.getElementById('mtdelthover'), l1=document.getElementById('mtdelthovlbl'); if(d1) d1.style.display='none'; if(l1) l1.style.display='none'; return; }
  const raw=box.getAttribute('data-hd'); if(!raw) return;
  let d=[]; try{ d=JSON.parse(decodeURIComponent(raw)); }catch(_){ return; }
  const r=box.getBoundingClientRect();
  const frac=Math.min(1,Math.max(0,(e.clientX-r.left)/r.width));
  const idx=Math.round(frac*(d.length-1));
  const mx=Math.max.apply(null,d)||1;
  const y=20-Math.max(2,Math.round(d[idx]/mx*18));
  const dot=document.getElementById('mtdelthover'), lbl=document.getElementById('mtdelthovlbl');
  if(dot){ dot.style.display='block'; dot.style.left=(frac*100)+'%'; dot.style.top=y+'px'; }
  if(lbl){ lbl.style.display='block'; lbl.style.left=(frac*100)+'%'; lbl.style.top=(y-10)+'px'; lbl.textContent='+'+d[idx]; }
  /* 双图联动(R155): 命中补入柱状同 frac, 同时点亮耗时折线第 idx 点(#mthisthover/#mthisthovlbl), 扫一眼「耗时 Xs + 补入 +Y」配对 */
  try{ const hb=document.querySelector('#mthistspark .mthistbox'); if(hb && hb.getAttribute('data-hh')){ let hh=[]; try{ hh=JSON.parse(decodeURIComponent(hb.getAttribute('data-hh'))); }catch(_){}
    if(hh.length){ const hpad=2, hhgt=22; const hmx=Math.max.apply(null,hh), hmn=Math.min.apply(null,hh), hrng=Math.max(1e-3,hmx-hmn); const hidx=Math.round(frac*(hh.length-1)); const hy=hpad+(1-(hh[hidx]-hmn)/hrng)*(hhgt-2*hpad);
      const hdot=document.getElementById('mthisthover'), hlbl=document.getElementById('mthisthovlbl');
      if(hdot){ hdot.style.display='block'; hdot.style.left=(frac*100)+'%'; hdot.style.top=hy+'px'; }
      if(hlbl){ hlbl.style.display='block'; hlbl.style.left=(frac*100)+'%'; hlbl.style.top=(hy-10)+'px'; hlbl.textContent=hh[hidx]+'s'; } } } }catch(_){}
  /* 配对值合并标签(R156): 命中补入柱状同frac, #mtpairlbl 显「第N次跑·耗时Xs·补入+Y」(两指标一行汇总, 扫一眼这次跑整体) */
  try{ const _hb=document.querySelector('#mthistspark .mthistbox'); if(_hb && _hb.getAttribute('data-hh')){ let _hh=[]; try{ _hh=JSON.parse(decodeURIComponent(_hb.getAttribute('data-hh'))); }catch(_){}
    if(_hh.length){ const _hi=Math.round(frac*(_hh.length-1)); const _hv=_hh[_hi]; const _pvd=d[idx];
      const pl=document.getElementById('mtpairlbl'); if(pl){ pl.style.display='inline-block'; pl.textContent='第 '+(_hi+1)+' 次跑 · 耗时 '+_hv+'s · 补入 +'+_pvd; } } } }catch(_){}
}, true);
document.addEventListener('mouseout', function(e){
  const box=e.target.closest && e.target.closest('#mtdeltabar .mtdeltabox');
  if(box){ const d1=document.getElementById('mtdelthover'), l1=document.getElementById('mtdelthovlbl'); if(d1) d1.style.display='none'; if(l1) l1.style.display='none';
    const pl=document.getElementById('mtpairlbl'); if(pl) pl.style.display='none'; }
}, true);
/* 载入: 按 _mtRunDelta 画补入量 mini 条形图(跨会话, 重开还在) */
(function(){ if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', function(){ mtRunDeltaDraw(); }); } else { mtRunDeltaDraw(); } })();
/* 清空补入量历史: 清 localStorage._mtRunDelta + mtRunDeltaDraw 重画(空->#mtdeltabar 隐) + toast; 看补入趋势久了重计基线(与 R146 清耗时历史对称的「补入量历史可清可留」) */
function mtRunDeltaClear(){
  try{ localStorage.removeItem('_mtRunDelta'); }catch(e){}
  mtRunDeltaDraw();
  if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); }
  _toast('补入量历史已清空 · 重新计基线', 'ok');
}
(function(){ const c=$('#mtdeltaclear'); if(c){ c.onclick=mtRunDeltaClear; } })();
/* 载入: 按 _mtRunHist+_mtRunDelta 画双指标一行汇总(跨会话, 重开还在) */
(function(){ if(document.readyState==='loading'){ document.addEventListener('DOMContentLoaded', function(){ if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); } }); } else { if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); } } })();
/* 一键全清维护趋势区(R159): _mtRunHist(耗时)+_mtRunDelta(补入量)+_mtRunHistBase(基线)三键一起清 + mtRunHistDraw/mtRunDeltaDraw/mtMetSumDraw 重画隐 -> 维护区趋势区一键归零; 与 R146清耗时/R157清补入/R150重置基线三钮分工, 全清要连点三次时一键归零 */
function mtMetClear(){
  try{ localStorage.removeItem('_mtRunHist'); localStorage.removeItem('_mtRunDelta'); localStorage.removeItem('_mtRunHistBase'); }catch(e){}
  mtRunHistDraw();
  mtRunDeltaDraw();
  if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); }
  _toast('维护趋势区已全清（耗时 + 补入量 + 基线 · 重新计基线）', 'ok');
}
(function(){ const c=$('#mtmetclear'); if(c){ c.onclick=mtMetClear; } })();
/* 双指标趋势区快照存 PNG(R160): 离屏 canvas 画 耗时折线+补入柱状+汇总标签(整区一张) -> download; 整区趋势图存档/贴issue/分享, 与 R148 单折线 PNG 互补(R148 单图 R160 双指标整区) */
function mtMetPng(){
  let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  let d=[]; try{ d=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  if(!h.length && !d.length){ _toast('无维护趋势可快照（先跑一次维护）', 'bad'); return; }
  const W=520, H=230, padL=14, padR=14;
  const c=document.createElement('canvas'); c.width=W; c.height=H;
  const g=c.getContext('2d');
  g.fillStyle='#fff'; g.fillRect(0,0,W,H);
  g.font='13px ui-sans-serif,system-ui,sans-serif'; g.fillStyle='#5a5a5f';
  g.fillText('维护趋势 · '+(new Date().toISOString().replace('T',' ').slice(0,16))+' 时', padL, 20);
  /* 上: 耗时折线(h), 下: 补入柱状(d), 各占 60px */
  function drawLine(y0, vals, color){
    if(!vals.length) return;
    const mx=Math.max.apply(null,vals), mn=Math.min.apply(null,vals), rng=Math.max(1e-3,mx-mn);
    const iw=W-padL-padR;
    const pts=vals.map((v,i)=>{ const x=padL+(vals.length>1? i/(vals.length-1):0.5)*iw; const y=y0+(1-(v-mn)/rng)*50; return [x,y]; });
    g.beginPath(); g.moveTo(pts[0][0],y0); pts.forEach(p=>g.lineTo(p[0],p[1])); g.lineTo(pts[pts.length-1][0],y0); g.closePath();
    g.fillStyle=color.replace(')',',0.12)').replace('rgb','rgba'); g.fill();
    g.beginPath(); g.moveTo(pts[0][0],pts[0][1]); pts.forEach(p=>g.lineTo(p[0],p[1])); g.strokeStyle=color; g.lineWidth=2; g.stroke();
    pts.forEach(p=>{ g.beginPath(); g.arc(p[0],p[1],3,0,Math.PI*2); g.fillStyle=color; g.fill(); });
    g.fillStyle='#9a9aa0'; g.font='10px ui-sans-serif,system-ui,sans-serif';
    g.fillText('近 '+vals.length+' 次', padL, y0+62);
  }
  function drawBar(y0, vals, color){
    if(!vals.length) return;
    const mx=Math.max.apply(null,vals)||1;
    const iw=W-padL-padR, bw=Math.floor(iw/vals.length)-1;
    vals.forEach((v,i)=>{ const bh=Math.max(2,Math.round(v/mx*50)); g.fillStyle=color; g.globalAlpha=(v>0?0.85:0.3);
      g.fillRect(padL+i*(Math.floor(iw/vals.length))+1, y0+bh, bw, 50-bh); g.globalAlpha=1; });
    g.fillStyle='#9a9aa0'; g.font='10px ui-sans-serif,system-ui,sans-serif';
    g.fillText('近 '+vals.length+' 次 · 合计 +'+(vals.reduce((a,c)=>a+c,0)), padL, y0+62);
  }
  if(h.length){ g.strokeStyle='#e4e4ea'; g.lineWidth=1; g.beginPath(); g.moveTo(padL,30); g.lineTo(W-padR,30); g.stroke(); drawLine(32, h, 'rgb(196,56,31)'); }
  if(d.length){ drawBar(h.length?96:32, d, 'rgb(47,125,85)'); }
  /* R229 双图区PNG快照补全折叠域5键当前态(canvas底栏5键色带, 自含全折叠域当前态, 与R222-R228补全折叠域字段同域) */
  const _fl5m=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  const _kn5m=['Met','Pan','All','Ctl','Dom'];
  const _cw5m=Math.floor((W-padL-padR)/5)-2;
  g.fillStyle='#5a5a5f'; g.font='10px ui-sans-serif,system-ui,sans-serif';
  g.fillText('全折叠域5键当前态', padL, H-40);
  for(let _i=0;_i<5;_i++){
    const _sx=padL+_i*(Math.floor((W-padL-padR)/5));
    g.fillStyle=(_fl5m[_i]==='0')?'rgb(47,125,85)':'rgb(163,38,26)';
    g.fillRect(_sx, H-34, _cw5m, 12);
    g.fillStyle='#fff'; g.font='8px ui-sans-serif,system-ui,sans-serif';
    g.fillText(_kn5m[_i]+'='+_fl5m[_i], _sx+1, H-24);
  }
  /* 汇总标签 */
  const sum=$('#mtmetsum'); if(sum && sum.style.display!=='none' && sum.textContent){ g.fillStyle='#c4381f'; g.font='11px ui-sans-serif,system-ui,sans-serif'; g.fillText(sum.textContent, padL, H-8); }
  const url=c.toDataURL('image/png');
  const a=document.createElement('a'); a.href=url; a.download='music3_trend_'+Date.now()+'.png';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(()=>URL.revokeObjectURL(url), 3000);
  _toast('已导出双指标趋势快照（PNG）', 'ok');
}
(function(){ const x=$('#mtmetpng'); if(x){ x.onclick=mtMetPng; } })();
/* 双指标趋势数据导出 CSV(R161): _mtRunHist(耗时)+_mtRunDelta(补入量) 双列 序号,耗时(s),补入量 -> BOM CSV 下载; Excel 横评哪次耗时高+补入少, 与 R160 双指标 PNG 互补(PNG 走图 CSV 走双列数据) */
function mtMetCsv(){
  let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  let d=[]; try{ d=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  if(!h.length && !d.length){ _toast('无维护趋势可导出（先跑一次维护）', 'bad'); return; }
  const n=Math.max(h.length, d.length);
  const ts=new Date().toISOString().replace('T',' ').slice(0,19);
  const lines=['#music3 双指标趋势数据（近 '+n+' 次 · 导出 '+ts+'）','序号,耗时(s),补入量'];
  for(let i=0;i<n;i++){ lines.push((i+1)+','+(i<h.length?h[i]:'—')+','+(i<d.length?d[i]:'—')); }
  const csv='\ufeff'+lines.join('\n');
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url; a.download='music3_trend_data_'+Date.now()+'.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(()=>URL.revokeObjectURL(url), 3000);
  _toast('已导出双指标趋势数据 '+n+' 行（CSV）', 'ok');
}
(function(){ const c=$('#mtmetcsv'); if(c){ c.onclick=mtMetCsv; } })();
/* 导入双指标趋势 CSV(R162): 文件选择框选 R161 导的双列 CSV(序号,耗时(s),补入量) -> 解析双列 -> 重填 _mtRunHist(耗时末10)+_mtRunDelta(补入末10) + 双图重画 + toast; 换设备/全清后把双指标带回来(与 R161 导出对称 R149 耗时单列扩展成双列) */
function mtMetImport(){
  const inp=document.createElement('input');
  inp.type='file'; inp.accept='.csv,text/csv';
  inp.onchange=function(ev){
    const f=ev.target.files[0]; if(!f) return;
    const rd=new FileReader();
    rd.onload=function(){
      try{
        const txt=String(rd.result||'').replace(/^\ufeff/,'');
        const rows=txt.split(/\r?\n/).filter(x=>x && x.indexOf('#')!==0);
        const hv=[], dv=[];
        rows.forEach(r=>{
          const c=r.split(',');
          const t1=parseFloat(c[1]), t2=parseFloat(c[2]);
          if(c.length>=2 && !isNaN(t1) && t1>0){ hv.push(t1); }
          if(c.length>=3 && !isNaN(t2) && t2>=0){ dv.push(t2); }
          /* 表头 序号,耗时(s),补入量: parseFloat('耗时(s)')=NaN 自动跳, 数据行 t1/t2 数值 */
        });
        if(!hv.length && !dv.length){ _toast('CSV 无有效双指标行（需 序号,耗时(s),补入量）', 'bad'); return; }
        localStorage.setItem('_mtRunHist', JSON.stringify(hv.slice(-10)));
        localStorage.setItem('_mtRunDelta', JSON.stringify(dv.slice(-10)));
        mtRunHistDraw(); mtRunDeltaDraw();
        if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); }
        _toast('已导入双指标趋势 '+hv.length+' 耗时 / '+dv.length+' 补入（CSV）', 'ok');
      }catch(e){ _toast('导入失败: '+e, 'bad'); }
    };
    rd.readAsText(f, 'utf-8');
  };
  inp.click();
}
(function(){ const im=$('#mtmetimport'); if(im){ im.onclick=mtMetImport; } })();
/* 折叠/展开维护趋势条(R163): #mtmetfold 钮切 #mtmetfoldwrap(#mthistspark+#mtdeltabar 双图区) 显隐, 记 localStorage._mtMetFold, 窄屏省高; 与 R135末点值标开关/R137筛选持久化「记状态可管」对称 */
function mtMetFold(){
  const wrap=$('#mtmetfoldwrap'), btn=$('#mtmetfold');
  if(!wrap || !btn) return;
  const folded = wrap.style.display !== 'none';
  wrap.style.display = folded ? 'none' : 'block';
  btn.textContent = folded ? '▸ 展趋势' : '▾ 折趋势';
  try{ localStorage.setItem('_mtMetFold', folded ? '1' : '0'); }catch(e){}
}
/* 折叠钮双击快捷(R177): #mtmetfold dblclick -> 展开 #mtmetfoldwrap(若折叠)+ 双图区在视口内 mtFocusLatest 聚焦最新轮, 双击=展开+聚焦连击一次到位(免展开后再点跳双图), 与 R171 单点跳双图同「趋势条可管」但连击快捷 */
function mtMetFoldDbl(){
  const wrap=$('#mtmetfoldwrap'), btn=$('#mtmetfold');
  if(wrap && wrap.style.display==='none'){ wrap.style.display='block'; try{ localStorage.setItem('_mtMetFold','0'); }catch(e){} if(btn){ btn.textContent='▾ 折趋势'; } }
  /* 双图区在视口内才聚焦(折叠刚展开可能在视口外, getBoundingClientRect 与视口交才聚焦) */
  try{
    if(!wrap) return;
    const r=wrap.getBoundingClientRect();
    if(r.bottom>0 && r.top<window.innerHeight){ if(typeof mtFocusLatest==='function'){ mtFocusLatest(); } }
  }catch(e){}
}
(function(){
  const btn=$('#mtmetfold'); if(btn){ btn.onclick=mtMetFold; btn.addEventListener('dblclick', mtMetFoldDbl); }
  /* 载入恢复折叠态 */
  try{
    const f=localStorage.getItem('_mtMetFold');
    const wrap=$('#mtmetfoldwrap');
    if(f==='1' && wrap){ wrap.style.display='none'; if(btn){ btn.textContent='▸ 展趋势'; } }
  }catch(e){}
})();
/* 跑中双指标实时徽标(R166): #mtlivebadge 显「跑中·第i/N轮·本轮回+X·本轮耗Ys」, 跑中每轮 tick 后刷新, 跑完/取消隐; 扫一眼当前跑双指标实况, 与 R155 双图 hover 配对同「双指标配对」语言但跑中实时 */
function mtLiveBadge(i, N, back, dur, lyr, cov, totalDur, totalN){
  const el=$('#mtlivebadge'); if(!el) return;
  /* 暂停/续跑同态(R182): 读 window._mtPaused(Space 暂停/续跑), 暂停时 #mtlivebadge 黄 --warn + 文案前缀「已暂停 ·」, 续跑回绿 --ok 跑中态; 跑中看徽标知道挂起/恢复, 与 #mtrun 黄「暂停中」同态 */
  const _paused=(typeof window._mtPaused!=='undefined' && window._mtPaused);
  el.textContent=(_paused?'已暂停 · ':'跑中 · ')+'第 '+i+'/'+(N>100000?'∞':N)+' 轮 · 本轮回 +'+back+' · 本轮耗 '+dur+'s';
  el.style.color=_paused?'var(--warn)':'var(--ok)';
  el.style.display='inline-block';
  /* 详情(R167): hover #mtlivebadge 展开 #mtlivedetail(补入拆歌词/封面 + 累计耗时 + 总进度), data-dtl 存详情 */
  if(lyr!==undefined){
    const _Ndisp=(totalN&&totalN>100000?'∞':(totalN||N));
    let _dtl='本轮回 +'+back+'（歌词 +'+(lyr||0)+' / 封面 +'+(cov||0)+'）· 本轮耗 '+dur+'s · 累计 '+(totalDur!==undefined?totalDur:'-')+'s · 跑到 '+i+'/'+_Ndisp;
    /* 双轨联动(R170): 自动刷 5s 开(_mtAutoRefTimer 非空)时, 详情补「· 自动刷 5s 中(下次 ≤5s)」-- 跑维护+自动刷 9 卡双轨看细, 扫一眼下轮自动刷何时到 */
    try{ if(typeof _mtAutoRefTimer!=='undefined' && _mtAutoRefTimer){ _dtl+=' · 自动刷 5s 中（下次 ≤5s）'; } }catch(e){}
    /* R230 跑中详情补全折叠域5键当前态(自含全折叠域当前态, 与R222-R229补全折叠域字段同域) */
    _dtl+=' · [全折叠域当前态] _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold='+(localStorage.getItem('_mtGuardPanelFold')||'0')+' · _mtGuardFoldAll='+(localStorage.getItem('_mtGuardFoldAll')||'0')+' · _mtGuardFoldCtl='+(localStorage.getItem('_mtGuardFoldCtl')||'0')+' · _mtGuardAllDomain='+(localStorage.getItem('_mtGuardAllDomain')||'0');
    el.setAttribute('data-dtl',_dtl);
    el.style.cursor='help';
  }
}
function mtLiveBadgeHide(){ const el=$('#mtlivebadge'); if(el){ el.style.display='none'; el.textContent=''; } const d=$('#mtlivedetail'); if(d){ d.style.display='none'; d.textContent=''; } const _c=$('#mtlivebadgedonecopy'); if(_c){ _c.style.display='none'; } window._mtLiveDoneInfo=null; /* R192 隐完成态复制钮+清完成态信息 */ }
/* 全库跑完完成态徽标(R187): #mtlivebadge 显「已跑完 · 共 N 轮 · 耗时 Xs」绿--ok, 全库 FULL_DONE 跑完看徽标完成态(区别于跑中每轮刷跑中态, 全库收尾固定显完成), 与 #mtstatebar 完成灰双路知全库收尾 */
function mtLiveBadgeDone(N, totalDur){
  const el=$('#mtlivebadge'); if(!el) return;
  el.textContent='已跑完 · 共 '+N+' 轮 · 耗时 '+totalDur+'s';
  el.style.color='var(--ok)';
  el.style.display='inline-block';
  const d=$('#mtlivedetail'); if(d){ d.textContent='全库维护完成 · 共 '+N+' 轮 · 累计耗时 '+totalDur+'s · 点双图区汇总跳双图看趋势'; d.style.display='none'; }
  window._mtLiveDoneInfo={N:N, totalDur:totalDur}; /* R192 完成态信息存 window, 复制读 */
  const _c=$('#mtlivebadgedonecopy'); if(_c){ _c.style.display='inline-block'; } /* R192 完成态显复制钮 */
}
/* 全库维护完成详情复制(R192): #mtlivebadgedonecopy 点 -> 复制「#music3 全库维护完成·<ts>·共N轮·耗时Xs」到剪贴板(navigator.clipboard,_copyFallback降级), 贴工单/记录维护日志完成态可留存, 与R169/R189/R191复制出口同语言 */
function mtLiveBadgeDoneCopy(){
  const li=window._mtLiveDoneInfo;
  if(!li){ if(typeof _toast==='function'){ _toast('无全库维护完成详情可复制（先跑全库维护）', 'bad'); } return; }
  let _txt='#music3 全库维护完成 · '+new Date().toLocaleString()+'\n共 '+li.N+' 轮 · 耗时 '+li.totalDur+'s';
  /* R230 全库完成详情补全折叠域5键当前态(自含全折叠域当前态, 与R222-R229补全折叠域字段同域) */
  _txt+='\n[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold='+(localStorage.getItem('_mtGuardPanelFold')||'0')+' · _mtGuardFoldAll='+(localStorage.getItem('_mtGuardFoldAll')||'0')+' · _mtGuardFoldCtl='+(localStorage.getItem('_mtGuardFoldCtl')||'0')+' · _mtGuardAllDomain='+(localStorage.getItem('_mtGuardAllDomain')||'0');
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制全库维护完成详情（共 '+li.N+' 轮 · 耗时 '+li.totalDur+'s）', 'ok'); } }).catch(function(){ _copyFallback(_txt); });
  } else { _copyFallback(_txt); }
}
(function(){ const c=$('#mtlivebadgedonecopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtLiveBadgeDoneCopy(); }); } })();
/* 聚焦最新轮双指标(R172/R173 共用): #mtdeltabar 末柱点亮 #mtdelthover + #mtpairlbl 显配对(第N次·耗时Xs·补入+Y), 读 _mtRunHist 末位耗时+_mtRunDelta 末位补入; 跳双图(R172)/跑中每轮 tick 在视口内(R173) 都调 */
function mtFocusLatest(){
  try{
    let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
    let d=[]; try{ d=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
    if(!h.length && !d.length){ return; }
    const n=Math.max(h.length, d.length);
    const lastIdx=n-1;
    const dEl=$('#mtdelthover'), pair=$('#mtpairlbl');
    const hv=h[lastIdx], dv=d.length?d[d.length-1]:null;
    if(pair){ pair.textContent='第 '+(lastIdx+1)+' 次 · 耗时 '+(hv!==undefined?hv:'-')+'s · 补入 '+(dv!==null?'+'+dv:'-'); pair.style.display='inline-block'; }
    if(dEl && dv!==null && d.length){ const mx=Math.max.apply(null,d.concat([1])); const top=(20-Math.round(dv/mx*18))-1; dEl.style.display='block'; dEl.style.top=top+'px'; dEl.style.left='100%'; }
  }catch(e){}
}
/* 汇总标签点击跳双图(R174): #mtmetsum onclick -> 展开 #mtmetfoldwrap(若折叠)+ scrollIntoView 双图区 + mtFocusLatest 聚焦最新轮, 汇总入口跳双图(非跑中也能从汇总看双图趋势), 与 R171 徽标跳双图同「趋势条可管」但汇总入口 */
function mtMetSumJump(){
  const wrap=$('#mtmetfoldwrap');
  if(wrap && wrap.style.display==='none'){ wrap.style.display='block'; try{ localStorage.setItem('_mtMetFold','0'); }catch(e){} const bf=$('#mtmetfold'); if(bf){ bf.textContent='▾ 折趋势'; } }
  const tgt=$('#mthistspark'); if(tgt){ tgt.scrollIntoView({behavior:'smooth', block:'center'}); }
  setTimeout(function(){ if(typeof mtFocusLatest==='function'){ mtFocusLatest(); } }, 400);
}
(function(){ const ms=$('#mtmetsum'); if(ms){ ms.addEventListener('click', mtMetSumJump); ms.style.cursor='pointer'; ms.title='点我看双图趋势 + 聚焦最新轮'; } })();
/* 徽标点击跳双图区(R171): #mtlivebadge onclick -> 展开 #mtmetfoldwrap(若 R163 折叠)+ scrollIntoView 滚到双图区(#mthistspark), 跑中扫一眼当前轮后直接看双图趋势(耗时折线/补入柱状), 徽标->双图跳转与 R163 折叠开关同「趋势条可管」语言 */
function mtLiveBadgeJump(){
  const wrap=$('#mtmetfoldwrap');
  if(wrap && wrap.style.display==='none'){ wrap.style.display='block'; try{ localStorage.setItem('_mtMetFold','0'); }catch(e){} const bf=$('#mtmetfold'); if(bf){ bf.textContent='▾ 折趋势'; } }
  const tgt=$('#mthistspark'); if(tgt){ tgt.scrollIntoView({behavior:'smooth', block:'center'}); }
  /* 跳双图后自动聚焦最新轮(R172): 滚势停后调 mtFocusLatest(末柱高亮+配对最新轮), 免手 hover */
  setTimeout(function(){ if(typeof mtFocusLatest==='function'){ mtFocusLatest(); } }, 400);
}
(function(){ const j=$('#mtlivebadge'); if(j){ j.addEventListener('click', mtLiveBadgeJump); } })();
/* 徽标右键快捷取消跑维护(R176): #mtlivebadge contextmenu -> _mtAborted=true + #mtrun 取消红态同步 + toast, 跑中看徽标双指标时右键即取消免手点 #mtrun, 与 R140 取消「已跑的轮不回滚」同直觉 */
(function(){
  const j=$('#mtlivebadge'); if(!j){ return; }
  j.addEventListener('contextmenu', function(ev){
    ev.preventDefault(); /* 不弹系统右键菜单 */
    if(typeof _mtAborted!=='undefined'){ _mtAborted=true; } /* 跳出 mtRun 循环下一轮 abort 检查 */
    const run=$('#mtrun');
    if(run){ /* 取消红态同步: 跑中是「取消」红, 右键取消同红态 */ run.textContent='取消'; run.style.background='var(--bad)'; run.style.color='#fff'; run.style.borderColor='var(--bad)'; }
    if(typeof _toast==='function'){ _toast('已发取消 · 跑到下一轮生效（已跑的轮不回滚）', 'ok'); }
  });
  /* 右键取消提示 */
  j.title=(j.title?j.title+' · 右键取消跑维护':'右键取消跑维护');
})();
/* 跑中 Esc 键盘快捷取消(R178): document keydown(Escape) + 维护 tab 激活 -> _mtAborted=true + #mtrun 取消红态同步 + toast, 跑中看徽标/看双图时按 Esc 即取消免手点/免右键(键盘路径, 与 R176 右键取消同「已跑的轮不回滚」直觉) */
(function(){
  document.addEventListener('keydown', function(e){
    /* 维护 tab 激活判(其他 tab 不触键盘快捷, 不挡全局) */
    const activeTab=document.querySelector('.tab.on[data-p="d"], .tab.active[data-p="d"]');
    if(!activeTab){ return; }
    /* 焦点在输入框/可编辑区时不触(不挡用户输入) */
    const tag=(document.activeElement && document.activeElement.tagName||'').toLowerCase();
    if(tag==='input'||tag==='textarea'||(document.activeElement&&document.activeElement.isContentEditable)){ return; }
    if(e.key==='Escape'){
      if(typeof _mtAborted!=='undefined'){ _mtAborted=true; window._mtAborted=true; } /* 跑中下一轮 abort 检查跳出 + 挂 window 供 mtStateBarDraw(R184) 读同态 */
      const run=$('#mtrun');
      if(run){ run.textContent='取消'; run.style.background='var(--bad)'; run.style.color='#fff'; run.style.borderColor='var(--bad)'; }
      if(typeof _toast==='function'){ _toast('已取消 · 跑到下一轮生效（Esc · 已跑的轮不回滚）', 'ok'); }
      if(typeof mtStateBarDraw==='function'){ mtStateBarDraw(); } /* R184 取消同步指示条红 */
      if(!window._mtKeyLog){ window._mtKeyLog={}; } window._mtKeyLog.esc=new Date().toLocaleTimeString(); /* R193 Esc 触发记录 */
      if(!window._mtKeyLogOrder){ window._mtKeyLogOrder=[]; } window._mtKeyLogOrder.push('Esc'); if(window._mtKeyLogOrder.length>10){ window._mtKeyLogOrder.shift(); } /* R194 触发顺序记录(保留最近10次) */
    }
    /* Enter 跳双图(R179): 维护 tab 激活 + 焦点非输入框 -> mtLiveBadgeJump(跳双图+mtFocusLatest聚焦最新轮), 跑中看徽标手放键盘按 Enter 即跳双图免移开手点, 与 R171 点击跳双图同「趋势条可管」但键盘路径 */
    if(e.key==='Enter'){
      e.preventDefault(); /* 挡全局 Enter(表单提交等), 维护区 Enter 只做跳双图 */
      if(typeof mtLiveBadgeJump==='function'){ mtLiveBadgeJump(); }
      if(typeof _toast==='function'){ _toast('已跳双图区 · 聚焦最新轮（Enter）', 'ok'); }
      if(!window._mtKeyLog){ window._mtKeyLog={}; } window._mtKeyLog.enter=new Date().toLocaleTimeString(); /* R193 Enter 触发记录 */
      if(!window._mtKeyLogOrder){ window._mtKeyLogOrder=[]; } window._mtKeyLogOrder.push('Enter'); if(window._mtKeyLogOrder.length>10){ window._mtKeyLogOrder.shift(); } /* R194 触发顺序记录 */
    }
    /* Space 暂停/续跑(R180): 维护 tab 激活 + 焦点非输入框 + 跑维护中(window._mtRunning) -> window._mtPaused 切换(暂停/续跑)+ #mtrun 黄态 + toast, 跑中全库挂起不等跑完/不取消 */
    if(e.key===' '){
      e.preventDefault(); /* 挡全局 Space(滚动等), 维护区 Space 只做暂停/续跑 */
      if(!window._mtKeyLog){ window._mtKeyLog={}; } window._mtKeyLog.space=new Date().toLocaleTimeString(); /* R193 Space 触发记录(R194: 移到 !running return 前, 非跑维护中也记 Space 按下) */
      if(!window._mtKeyLogOrder){ window._mtKeyLogOrder=[]; } window._mtKeyLogOrder.push('Space'); if(window._mtKeyLogOrder.length>10){ window._mtKeyLogOrder.shift(); } /* R194 触发顺序记录 */
      if(!window._mtRunning){ if(typeof _toast==='function'){ _toast('Space 暂停需跑维护中（先点「跑一轮」）', 'bad'); } return; }
      if(window._mtPaused===false){
        window._mtPaused=true; /* 暂停: 循环顶挂起 */
        const run=$('#mtrun'); if(run){ run.textContent='暂停中 · 按 Space 续跑'; run.style.background='var(--warn)'; run.style.color='#fff'; run.style.borderColor='var(--warn)'; }
        if(typeof _toast==='function'){ _toast('已暂停 · 按 Space 续跑（已跑的轮不回滚）', 'ok'); }
      } else {
        window._mtPaused=false; /* 续跑: 循环顶轮询跳出 */
        const run=$('#mtrun'); if(run){ run.textContent='取消'; run.style.background='var(--bad)'; run.style.color='#fff'; run.style.borderColor='var(--bad)'; }
        if(typeof _toast==='function'){ _toast('已续跑 · 维护继续', 'ok'); }
      }
      if(typeof mtStateBarDraw==='function'){ mtStateBarDraw(); } /* R184 暂停/续跑同步指示条(暂停黄/续跑回跑中绿) */
    }
  });
})();
/* 续跑恢复 #mtrun 态(R180): 暂停检查跳出(续跑/取消)后恢复 #mtrun 跑中态, 循环顶暂停检查调用 */
function _mtUnpausedBtn(){
  const run=$('#mtrun'); if(!run) return;
  const _r=typeof window._mtRunning!=='undefined' && window._mtRunning;
  run.textContent=_r?'取消':'跑一轮';
  run.style.background=_r?'var(--bad)':''; run.style.color=_r?'#fff':''; run.style.borderColor=_r?'var(--bad)':'';
}
/* 键盘三键提示浮层(R181): #mtkeyhint hover -> #mtkeyhintdetail 显「Space 暂停/续跑 · Esc 取消 · Enter 跳双图+聚焦最新轮」(维护 tab 激活+焦点非输入框时生效), 键盘流三操作可发现性(免记/免试错), 与 R178/R179/R180 三键盘操作对称 */
(function(){
  const k=$('#mtkeyhint'), d=$('#mtkeyhintdetail'), cp=$('#mtkeyhintcopy');
  if(!k || !d) return;
  /* 三键状态灯(R186): 读 window._mtRunning/_mtPaused 实时显三键当前可触/不可触/暂停色点, hover 看三键可触状态随跑维护态变 */
  function _keyDot(_on, _warn){
    /* 色点: 可触绿 / 暂停黄 / 不可触灰, 内联 span */
    if(_warn){ return '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--warn);margin-right:2px"></span>'; }
    if(_on){ return '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--ok);margin-right:2px"></span>'; }
    return '<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:var(--line);margin-right:2px"></span>';
  }
  k.addEventListener('mouseenter', function(){
    const _run=(typeof window._mtRunning!=='undefined' && window._mtRunning);
    const _ps=(typeof window._mtPaused!=='undefined' && window._mtPaused);
    const _ab=(typeof window._mtAborted!=='undefined' && window._mtAborted);
    /* 三键可触: Space 需跑维护中且未取消(_run&&!_ab); 暂停态 Space 可续跑(黄); Esc 需跑中未取消(_run&&!_ab); Enter 非取消即触(跳双图, 非跑中也触但无跑中详情=可触) */
    const _spCan=_run&&!_ab;                 /* Space 可触(暂停或续跑), 暂停态显黄(续跑) */
    const _esCan=_run&&!_ab;                 /* Esc 可触(取消跑维护中) */
    const _enCan=!_ab;                       /* Enter 可触(跳双图, 非取消即触) */
    /* 最近触发时间(R193): 读 window._mtKeyLog(各键操作后更新), 逐键补「最近 <ts>」/未用过 */
    const _kl=window._mtKeyLog||{};
    const _spT=_kl.space?('最近 '+_kl.space):'未用过';
    const _esT=_kl.esc?('最近 '+_kl.esc):'未用过';
    const _enT=_kl.enter?('最近 '+_kl.enter):'未用过';
    /* 触发顺序回放(R194): 读 window._mtKeyLogOrder(最近10次三键触发顺序), 补「触发顺序：Esc→Space→Enter→…」 */
    const _ko=window._mtKeyLogOrder||[];
    const _order=_ko.length?('触发顺序：'+_ko.join('→')):'无触发顺序（未用过）';
    const _html=_keyDot(_spCan, _ps&&_spCan)+'Space 暂停/续跑 · '+_spT+'<br>'
      +_keyDot(_esCan, false)+'Esc 取消 · '+_esT+'<br>'
      +_keyDot(_enCan, false)+'Enter 跳双图 + 聚焦最新轮 · '+_enT+'<br>'
      +'<span style="color:var(--dim)">'+_order+'</span><br>'
      /* R227 键盘流触发记录补全折叠域5键当前态(自含全折叠域当前态, 与R222/R223/R224/R225/R226补全折叠域字段同域) */
      +'<span style="color:var(--dim)">[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold='+(localStorage.getItem('_mtGuardPanelFold')||'0')+' · _mtGuardFoldAll='+(localStorage.getItem('_mtGuardFoldAll')||'0')+' · _mtGuardFoldCtl='+(localStorage.getItem('_mtGuardFoldCtl')||'0')+' · _mtGuardAllDomain='+(localStorage.getItem('_mtGuardAllDomain')||'0')+'</span>';
    d.innerHTML=_html; d.style.display='block';
    if(cp){ const _hasRec=_kl.space||_kl.esc||_kl.enter||_ko.length; cp.style.display=_hasRec?'inline-block':'none'; } /* R195 copy 跟触发记录: 有触发记录才显 */
    /* 视口跟随定位(R168 同 getBoundingClientRect + flip): #mtkeyhint 下方浮层, 靠右/靠底不溢出 */
    const r=k.getBoundingClientRect();
    d.style.position='absolute';
    const dw=d.offsetWidth, dh=d.offsetHeight;
    let lx=r.left, rx=window.innerWidth-8;
    if(r.left+dw>rx){ lx=Math.max(8, r.right-dw); }
    d.style.left=lx+'px';
    let ty=r.bottom+2;
    if(ty+dh>window.innerHeight-8){ ty=Math.max(8, r.top-dh-2); }
    d.style.top=ty+'px';
  });
  k.addEventListener('mouseleave', function(){ d.style.display='none'; d.innerHTML=''; if(cp){ cp.style.display='none'; } }); /* R195 离隐 copy, 跟浮层 hover 态 */
})();
/* 键盘流触发记录复制(R195): #mtkeyhintcopy 点 -> 复制「#music3 键盘流触发记录·<ts>」+三键最近触发时间戳+触发顺序串到剪贴板(navigator.clipboard,_copyFallback降级), 贴工单/记录键盘流使用习惯, 与R169/R189/R191/R192复制出口同语言 */
function mtKeyHintCopy(){
  const _kl=window._mtKeyLog||{};
  const _ko=window._mtKeyLogOrder||[];
  if(!_kl.space && !_kl.esc && !_kl.enter && !_ko.length){ if(typeof _toast==='function'){ _toast('无键盘流触发记录可复制（未用过三键）', 'bad'); } return; }
  let _lines='#music3 键盘流触发记录 · '+new Date().toLocaleString()+'\n';
  _lines+='Space 暂停/续跑 · '+(_kl.space?('最近 '+_kl.space):'未用过')+'\n';
  _lines+='Esc 取消 · '+(_kl.esc?('最近 '+_kl.esc):'未用过')+'\n';
  _lines+='Enter 跳双图 + 聚焦最新轮 · '+(_kl.enter?('最近 '+_kl.enter):'未用过')+'\n';
  _lines+=_ko.length?('触发顺序：'+_ko.join('→')):'无触发顺序（未用过）';
  /* R227 键盘流触发记录补全折叠域5键当前态(自含全折叠域当前态, 与R222/R223/R224/R225/R226补全折叠域字段同域) */
  _lines+='\n[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold='+(localStorage.getItem('_mtGuardPanelFold')||'0')+' · _mtGuardFoldAll='+(localStorage.getItem('_mtGuardFoldAll')||'0')+' · _mtGuardFoldCtl='+(localStorage.getItem('_mtGuardFoldCtl')||'0')+' · _mtGuardAllDomain='+(localStorage.getItem('_mtGuardAllDomain')||'0');
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制键盘流触发记录', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ const c=$('#mtkeyhintcopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtKeyHintCopy(); }); } })();
/* 维护守护区一键全复制(R196): #mtguardcopy 点 -> 拼「#music3 维护守护全记录·<ts>」+双指标逐轮明细段(localStorage._mtRunHist/_mtRunDelta)+状态详情段(window._mtLiveInfo+三标志)+全库完成段(window._mtLiveDoneInfo)+键盘流触发段(window._mtKeyLog/_mtKeyLogOrder)四段拼到剪贴板(navigator.clipboard,_copyFallback降级), 维护守护区数据一键全留存/全贴工单, 与R189/R191/R192/R195单点复制同语言但全量 */
function mtGuardCopy(){
  let _all='#music3 维护守护全记录 · '+new Date().toLocaleString()+'\n';
  /* 段1: 双指标逐轮明细(读 localStorage._mtRunHist/_mtRunDelta, 同 R189) */
  let _h=[]; try{ _h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  let _b=[]; try{ _b=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  const _n=Math.max(_h.length, _b.length);
  _all+='[双指标逐轮明细] '+( _n?('近 '+_n+' 次'):'无')+'\n';
  if(_n){
    for(let _k=0; _k<_n; _k++){
      const _hv=_h.length?_h[_k]:'-', _bv=_b.length?_b[_k]:'-';
      _all+='第 '+(_n-1-_k)+' 次 '+(typeof _hv==='number'?_hv+'s':'—')+' · 补入 '+(typeof _bv==='number'?('+'+_bv):'—')+'\n';
    }
  }
  /* 段2: 状态详情(读 window._mtLiveInfo + 三标志, 同 R191) */
  const _li=window._mtLiveInfo;
  let _st='维护完成 / 未跑';
  if(typeof window._mtAborted!=='undefined' && window._mtAborted){ _st='已取消 · '+( _li?('第 '+_li.i+'/'+( _li.N>100000?'∞':_li.N)+' 轮 · 本轮回 +'+_li.back+' · 本轮耗 '+_li.dur+'s'):'跑到断点'); }
  else if(typeof window._mtPaused!=='undefined' && window._mtPaused){ _st='已暂停 · '+( _li?('第 '+_li.i+'/'+( _li.N>100000?'∞':_li.N)+' 轮 · 本轮回 +'+_li.back+' · 本轮耗 '+_li.dur+'s'):''); }
  else if(typeof window._mtRunning!=='undefined' && window._mtRunning){ _st='跑中 · '+( _li?('第 '+_li.i+'/'+( _li.N>100000?'∞':_li.N)+' 轮 · 本轮回 +'+_li.back+' · 本轮耗 '+_li.dur+'s'):''); }
  _all+='\n[状态详情] '+_st+'\n';
  /* 段3: 全库完成详情(读 window._mtLiveDoneInfo, 同 R192) */
  const _done=window._mtLiveDoneInfo;
  _all+='[全库完成详情] '+( _done?('共 '+_done.N+' 轮 · 耗时 '+_done.totalDur+'s'):'无（未全库跑完 / 已复位）')+'\n';
  /* 段4: 键盘流触发记录(读 window._mtKeyLog/_mtKeyLogOrder, 同 R195) */
  const _kl=window._mtKeyLog||{}, _ko=window._mtKeyLogOrder||[];
  _all+='[键盘流触发记录]\n';
  _all+='Space 暂停/续跑 · '+(_kl.space?('最近 '+_kl.space):'未用过')+'\n';
  _all+='Esc 取消 · '+(_kl.esc?('最近 '+_kl.esc):'未用过')+'\n';
  _all+='Enter 跳双图 + 聚焦最新轮 · '+(_kl.enter?('最近 '+_kl.enter):'未用过')+'\n';
  _all+=_ko.length?('触发顺序：'+_ko.join('→')):'无触发顺序（未用过）';
  /* R222 段5: 全折叠域当前态(读5键localStorage+5标志window+5折叠钮文案+7浮层display, 维护守护全记录自含全折叠域当前态, 与R219/R220/R221全折叠域字段同域) */
  const _fl5=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  const _wl5=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain];
  const _btns5=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain'];
  const _floors5=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains'];
  _all+='\n[全折叠域当前态]\n';
  _all+='localStorage 5键: _mtMetFold='+_fl5[0]+' · _mtGuardPanelFold='+_fl5[1]+' · _mtGuardFoldAll='+_fl5[2]+' · _mtGuardFoldCtl='+_fl5[3]+' · _mtGuardAllDomain='+_fl5[4]+'\n';
  _all+='window 5标志: _mtMetFold='+_wl5[0]+' · _mtGuardPanelFold='+_wl5[1]+' · _mtGuardFoldAll='+_wl5[2]+' · _mtGuardFoldCtl='+_wl5[3]+' · _mtGuardAllDomain='+_wl5[4]+'\n';
  for(let _i=0;_i<5;_i++){ const _bb=document.getElementById(_btns5[_i]); _all+=_btns5[_i]+'='+(_bb?_bb.textContent:'无')+'\n'; }
  for(let _i=0;_i<7;_i++){ const _ff=document.getElementById(_floors5[_i]); _all+=_floors5[_i]+'='+(_ff?_ff.style.display:'无')+'\n'; }
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_all).then(function(){ if(typeof _toast==='function'){ _toast('已复制维护守护全记录（四段）', 'ok'); } }).catch(function(){ _copyFallback(_all); });
  } else { _copyFallback(_all); }
}
(function(){ const c=$('#mtguardcopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardCopy(); }); } })();
/* 维护守护区四段数据快照可视化(R197): #mtguardsnap 点 -> 拼内联SVG快照(双指标逐轮柱状localStorage._mtRunHist/_mtRunDelta+状态色带window._mtRunning/_mtPaused/_mtAborted四态+完成徽标window._mtLiveDoneInfo+键盘流顺序条window._mtKeyLogOrder)显#mtguardsnapd浮层, 一眼看维护守护区四段当前全貌, 文本全量复制(R196)+可视化全貌双路 */
function mtGuardSnap(){
  const d=$('#mtguardsnapd'); if(!d) return;
  let _h=[]; try{ _h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  let _b=[]; try{ _b=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  const _n=Math.max(_h.length, _b.length);
  const _W=360, _H=210, _pads=8;
  let _svg='<svg width="'+_W+'" height="'+_H+'" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">';
  /* 段1: 双指标逐轮柱状(顶部 40px, 近N次耗时柱) */
  _svg+='<text x="'+_pads+'" y="12" font-size="9" fill="var(--dim)">双指标逐轮 · 近'+_n+'次</text>';
  if(_n){
    const _max=Math.max.apply(null,_h.concat([1]));
    const _bw=Math.min(14, Math.floor((_W-_pads*2)/_n)-2), _gap=Math.floor((_W-_pads*2)/_n);
    for(let _i=0;_i<_n;_i++){
      const _v=_h.length?_h[_i]:0, _bb=_b.length?_b[_i]:0;
      const _bh=Math.round(_v/_max*28), _bbh=Math.round(_bb/Math.max(1,_bb)*_bb); /* 耗时柱(绿)+补入柱(橙) 并列 */
      const _x=_pads+_i*_gap;
      _svg+='<rect x="'+_x+'" y="'+(38-_bh)+'" width="'+Math.max(2,_bw/2)+'" height="'+_bh+'" fill="var(--ok)" rx="1"/>'; /* 耗时柱 */
      _svg+='<rect x="'+(_x+_bw/2)+'" y="'+(38-_bb)+'" width="'+Math.max(2,_bw/2)+'" height="'+_bb+'" fill="#c4381f" rx="1" opacity=".55"/>'; /* 补入柱 */
    }
  } else { _svg+='<text x="'+(_pads+4)+'" y="30" font-size="9" fill="var(--dim)">无双指标历史</text>'; }
  /* 段2: 状态色带(40-58px, 四态色带) */
  const _sc=(typeof window._mtAborted!=='undefined'&&window._mtAborted)?'var(--bad)':(typeof window._mtPaused!=='undefined'&&window._mtPaused)?'var(--warn)':(typeof window._mtRunning!=='undefined'&&window._mtRunning)?'var(--ok)':'var(--line)';
  _svg+='<text x="'+_pads+'" y="52" font-size="9" fill="var(--dim)">状态</text>';
  _svg+='<rect x="46" y="46" width="'+(_W-46-_pads)+'" height="6" rx="3" fill="'+_sc+'"/>';
  /* 段3: 完成徽标(62-80px) */
  const _done=window._mtLiveDoneInfo;
  _svg+='<text x="'+_pads+'" y="72" font-size="9" fill="var(--dim)">全库完成</text>';
  if(_done){ _svg+='<rect x="46" y="64" width="120" height="14" rx="3" fill="var(--ok)" opacity=".15"/><text x="52" y="74" font-size="9" fill="var(--ok)">共'+_done.N+'轮 · '+_done.totalDur+'s</text>'; }
  else { _svg+='<text x="46" y="74" font-size="9" fill="var(--dim)">无（未全库跑完 / 已复位）</text>'; }
  /* 段4: 键盘流顺序条(84-130px, 最近10次三键色点序列) */
  const _ko=window._mtKeyLogOrder||[];
  _svg+='<text x="'+_pads+'" y="94" font-size="9" fill="var(--dim)">键盘流顺序'+(_ko.length?(' · '+_ko.length+'次'):'')+'</text>';
  const _kc={'Space':'var(--warn)','Esc':'var(--bad)','Enter':'var(--ok)'};
  if(_ko.length){
    const _cw=Math.min(24, Math.floor((_W-_pads*2)/_ko.length)-2);
    for(let _i=0;_i<_ko.length;_i++){
      const _x=_pads+_i*(Math.floor((_W-_pads*2)/_ko.length));
      _svg+='<rect x="'+_x+'" y="100" width="'+_cw+'" height="14" rx="2" fill="var(--bg2)" stroke="var(--line)"/><text x="'+(_x+2)+'" y="110" font-size="8" fill="'+(_kc[_ko[_i]]||'var(--ink)')+'">'+_ko[_i]+'</text>';
    }
  } else { _svg+='<text x="'+_pads+'" y="110" font-size="9" fill="var(--dim)">未用过</text>'; }
  /* R222 段5: 全折叠域当前态(5键localStorage色带, 维护守护全记录快照自含全折叠域当前态, 与R219/R220/R221全折叠域字段同域) */
  _svg+='<text x="'+_pads+'" y="130" font-size="9" fill="var(--dim)">全折叠域 5键</text>';
  const _fl5s=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  const _knames=['_mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain'];
  const _scw=Math.min(52, Math.floor((_W-_pads*2)/5)-2);
  for(let _i=0;_i<5;_i++){
    const _sx=_pads+_i*(Math.floor((_W-_pads*2)/5));
    const _scol=(_fl5s[_i]==='0')?'var(--ok)':'var(--bad)';
    _svg+='<rect x="'+_sx+'" y="136" width="'+_scw+'" height="14" rx="2" fill="var(--bg2)" stroke="'+_scol+'"/><text x="'+(_sx+2)+'" y="146" font-size="7" fill="'+_scol+'">'+_knames[_i].replace('_mt','')+'='+_fl5s[_i]+'</text>';
  }
  /* 时间戳 */
  _svg+='<text x="'+_pads+'" y="'+(_H-4)+'" font-size="8" fill="var(--dim)">'+new Date().toLocaleString()+'</text>';
  _svg+='</svg>';
  d.innerHTML=_svg;
  d.style.display='block';
  /* 视口跟随定位(R168 同 getBoundingClientRect + flip): #mtguardsnap 下方浮层 */
  const r=document.getElementById('mtguardsnap').getBoundingClientRect();
  d.style.position='absolute';
  d.style.left=r.left+'px';
  d.style.top=(r.bottom+2)+'px';
  /* 3s 自动隐 */
  clearTimeout(window._mtGuardSnapT);
  window._mtGuardSnapT=setTimeout(function(){ d.style.display='none'; }, 6000);
}
(function(){ const c=$('#mtguardsnap'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardSnap(); }); } })();
/* 维护守护区四段快照PNG导出(R198): #mtguardsnappng 点 -> 读 #mtguardsnapd 内联SVG(若无则先 mtGuardSnap 生成), canvas 转 PNG 下载「music3_维护守护全记录_快照_<ts>.png」, 四段全貌快照可存档/可分享, 与R158双图区PNG快照(_mtmetpng)语言同 */
function mtGuardSnapPng(){
  const d=$('#mtguardsnapd'); if(!d) return;
  /* #mtguardsnapd 无 SVG(未点过 #mtguardsnap)则先生成 */
  if(!d.innerHTML || d.innerHTML.indexOf('<svg')<0){ if(typeof mtGuardSnap==='function'){ mtGuardSnap(); } }
  const svg=d.querySelector('svg');
  if(!svg){ if(typeof _toast==='function'){ _toast('无维护守护区四段快照可导出（维护守护区数据空）', 'bad'); } return; }
  const _W=svg.getAttribute('width')||360, _H=svg.getAttribute('height')||150;
  const _svgStr=new XMLSerializer().serializeToString(svg);
  const _b64=btoa(unescape(encodeURIComponent(_svgStr)));
  const _img=new Image();
  _img.onload=function(){
    const _cv=document.createElement('canvas'); _cv.width=Number(_W); _cv.height=Number(_H);
    const _cx=_cv.getContext('2d');
    _cx.fillStyle='#f7f5f0'; _cx.fillRect(0,0,_cv.width,_cv.height); /* 浅色底(R158 同, 透明底 PNG 贴工单看不清) */
    _cx.drawImage(_img,0,0);
    try{
      _cv.toBlob(function(blob){
        if(!blob){ _fallbackCopy(); return; }
        const _url=URL.createObjectURL(blob);
        const _a=document.createElement('a');
        _a.href=_url; _a.download='music3_维护守护全记录_快照_'+new Date().toISOString().replace(/[:.]/g,'-')+'.png';
        document.body.appendChild(_a); _a.click(); document.body.removeChild(_a);
        setTimeout(function(){ URL.revokeObjectURL(_url); }, 4000);
        if(typeof _toast==='function'){ _toast('已下载维护守护区四段快照 PNG', 'ok'); }
      },'image/png');
    }catch(_){ _fallbackCopy(); }
    function _fallbackCopy(){ /* toBlob/canvas 不可用降级: 复制 SVG 源码到剪贴板 */
      const _txt='#music3 维护守护全记录 快照 SVG\n'+_svgStr;
      if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制维护守护区四段快照 SVG（PNG 导出不可用降级）', 'ok'); } }).catch(function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败且复制降级失败', 'bad'); } }); }
      else { if(typeof _toast==='function'){ _toast('PNG 导出失败（canvas 不可用）', 'bad'); } }
    }
  };
  _img.onerror=function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败（SVG 渲染不可用）', 'bad'); } };
  _img.src='data:image/svg+xml;base64,'+_b64;
}
(function(){ const c=$('#mtguardsnappng'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardSnapPng(); }); } })();
/* 维护守护区能力/出口总览(R199): #mtguardpanel 点 -> 拼内联SVG总览面板(三键状态灯+四段数据源+各复制出口+快照/PNG出口分块标位), 显#mtguardpaneld浮层, 维护守护区能力/出口全景图一眼知有哪些入口/能力免分散找 */
function mtGuardPanel(){
  const d=$('#mtguardpaneld'); if(!d) return;
  const _W=400, _H=270, _p=10;
  const _run=(typeof window._mtRunning!=='undefined' && window._mtRunning);
  const _ps=(typeof window._mtPaused!=='undefined' && window._mtPaused);
  const _ab=(typeof window._mtAborted!=='undefined' && window._mtAborted);
  let _svg='<svg width="'+_W+'" height="'+_H+'" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">';
  _svg+='<text x="'+_p+'" y="14" font-size="10" font-weight="600" fill="var(--ink)">维护守护区能力 / 出口总览</text>';
  /* 块1: 三键状态灯(R186) + 触发记录(R193/R194) */
  _svg+='<rect x="'+_p+'" y="22" width="180" height="54" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="36" font-size="9" fill="var(--dim)">三键状态灯 + 触发记录</text>';
  const _dots=[['Space',_run&&!_ab,_ps],['Esc',_run&&!_ab,false],['Enter',!_ab,false]];
  let _di=0;
  for(let _i=0;_i<3;_i++){
    const _dn=_dots[_i][0], _can=_dots[_i][1], _warn=_dots[_i][2];
    const _x=_p+8+_i*60, _y=44;
    const _col=_warn?'var(--warn)':(_can?'var(--ok)':'var(--line)');
    _svg+='<circle cx="'+(_x+4)+'" cy="'+(_y+4)+'" r="4" fill="'+_col+'"/>';
    _svg+='<text x="'+(_x+12)+'" y="'+(_y+8)+'" font-size="9" fill="var(--ink)">'+_dn+'</text>';
    _di++;
  }
  const _kl=window._mtKeyLog||{}, _ko=window._mtKeyLogOrder||[];
  _svg+='<text x="'+(_p+6)+'" y="70" font-size="8" fill="var(--dim)">'+(_ko.length?('触发记录·最近'+_ko.length+'次'):'无触发记录')+'</text>';
  /* 块2: 四段数据源(R188/R184/R187/R194) */
  _svg+='<rect x="'+(_p+190)+'" y="22" width="180" height="54" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+196)+'" y="36" font-size="9" fill="var(--dim)">四段数据源</text>';
  let _h=[]; try{ _h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  const _segs=[
    ['双指标逐轮', _h.length?('近'+_h.length+'次'):'无', 'var(--ok)'],
    ['状态', _ab?'取消':(_ps?'暂停':(_run?'跑中':'完成/未跑')), _ab?'var(--bad)':(_ps?'var(--warn)':(_run?'var(--ok)':'var(--line)'))],
    ['全库完成', window._mtLiveDoneInfo?('共'+window._mtLiveDoneInfo.N+'轮'):'无', 'var(--ok)'],
    ['键盘流', _ko.length?('最近'+_ko.length+'次'):'无', 'var(--ink)']
  ];
  for(let _i=0;_i<4;_i++){
    const _sy=44+_i*9;
    _svg+='<text x="'+(_p+196)+'" y="'+(_sy+4)+'" font-size="8" fill="var(--dim)">'+_segs[_i][0]+'：'+_segs[_i][1]+'</text>';
  }
  /* 块3: 复制出口(R189/R191/R192/R195/R196) */
  _svg+='<rect x="'+_p+'" y="84" width="180" height="54" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="98" font-size="9" fill="var(--dim)">复制出口</text>';
  const _copies=['⧉ 双指标逐轮明细','⧉ 状态详情','⧉ 全库完成详情','⧉ 键盘流触发记录','⧉ 全复制(四段)'];
  for(let _i=0;_i<5;_i++){
    _svg+='<text x="'+(_p+8)+'" y="'+(108+_i*8)+'" font-size="8" fill="var(--ink)">'+_copies[_i]+'</text>';
  }
  /* 块4: 快照/PNG出口(R197/R198) */
  _svg+='<rect x="'+(_p+190)+'" y="84" width="180" height="54" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+196)+'" y="98" font-size="9" fill="var(--dim)">快照 / PNG 出口</text>';
  const _snaps=['▣ 四段快照(内联SVG)','⬇ 快照PNG(下载)','▤ 总览(本面板)'];
  for(let _i=0;_i<3;_i++){
    _svg+='<text x="'+(_p+198)+'" y="'+(108+_i*8)+'" font-size="8" fill="var(--ink)">'+_snaps[_i]+'</text>';
  }
  /* 块5: 键盘三操作(R178/R179/R180) + 状态同态(R182-R184) */
  _svg+='<rect x="'+_p+'" y="146" width="180" height="54" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="160" font-size="9" fill="var(--dim)">键盘三操作 + 状态同态</text>';
  const _ops=['Space 暂停/续跑(R180)','Esc 取消(R178)','Enter 跳双图(R179)','徽标暂停同态(R182)','汇总同态(R183)','指示条同态(R184)'];
  for(let _i=0;_i<6;_i++){
    _svg+='<text x="'+(_p+8)+'" y="'+(170+_i*7)+'" font-size="7" fill="var(--dim)">'+_ops[_i]+'</text>';
  }
  /* 块6: 全库 ∞ + 完成态(R166/R187) */
  _svg+='<rect x="'+(_p+190)+'" y="146" width="180" height="54" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+196)+'" y="160" font-size="9" fill="var(--dim)">全库 ∞ + 完成态</text>';
  const _full=['全库∞(R166, N>100000)','完成态徽标(R187)','全库完成详情(R187)'];
  for(let _i=0;_i<3;_i++){
    _svg+='<text x="'+(_p+198)+'" y="'+(170+_i*7)+'" font-size="7" fill="var(--dim)">'+_full[_i]+'</text>';
  }
  /* R223 块7: 全折叠域当前态(5键localStorage色带+5折叠钮+7浮层, 能力/出口总览自含全折叠域当前态, 与R222维护守护全记录补全折叠域字段同域) */
  _svg+='<rect x="'+_p+'" y="208" width="360" height="48" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="222" font-size="9" fill="var(--dim)">全折叠域当前态</text>';
  const _fl7=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  const _kn7=['Met','Pan','All','Ctl','Dom'];
  const _cw7=Math.floor((360-12)/5)-2;
  for(let _i=0;_i<5;_i++){
    const _sx=_p+6+_i*(Math.floor((360-12)/5));
    const _scol=(_fl7[_i]==='0')?'var(--ok)':'var(--bad)';
    _svg+='<rect x="'+_sx+'" y="228" width="'+_cw7+'" height="14" rx="2" fill="var(--bg2)" stroke="'+_scol+'"/><text x="'+(_sx+2)+'" y="238" font-size="7" fill="'+_scol+'">'+_kn7[_i]+'='+_fl7[_i]+'</text>';
  }
  const _btns7=['#mtmetfold','#mtguardpanelfold','#mtguardfoldall','#mtguardfoldctl','#mtguardalldomain'];
  for(let _i=0;_i<5;_i++){ const _bb=document.getElementById(_btns7[_i]); _svg+='<text x="'+(_p+6+_i*72)+'" y="252" font-size="6" fill="var(--dim)">'+_btns7[_i].replace('#','=')+(_bb?_bb.textContent:'无')+'</text>'; }
  const _floors7=['paneld','ctl d','statd','sbdtl','msd','khd','alld'];
  _svg+='<text x="'+_p+'" y="'+(_H-4)+'" font-size="8" fill="var(--dim)">'+new Date().toLocaleString()+'</text>';
  _svg+='</svg>';
  d.innerHTML=_svg; d.style.display='block';
  const r=document.getElementById('mtguardpanel').getBoundingClientRect();
  d.style.position='absolute'; d.style.left=r.left+'px'; d.style.top=(r.bottom+2)+'px';
  /* R202: 折叠态(_mtGuardPanelFold)不8s自动隐, 展开态才8s自动隐 — 折叠总览常驻省高, 展开总览临时看8s隐 */
  if(!window._mtGuardPanelFold){ clearTimeout(window._mtGuardPanelT); window._mtGuardPanelT=setTimeout(function(){ d.style.display='none'; }, 8000); }
}
(function(){ const c=$('#mtguardpanelfold'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); /* R202 折叠/展开总览面板 */
  /* R205: 惰性初始化读 localStorage._mtGuardPanelFold, 总览面板折叠态跨会话留存(刷新恢复, 与R159双图区/R204全浮层折叠记忆语言同) */
  if(window._mtGuardPanelFold===undefined){
    let _init=false; try{ _init=(localStorage.getItem('_mtGuardPanelFold')==='1'); }catch(_){}
    window._mtGuardPanelFold=_init;
  }
  window._mtGuardPanelFold=!window._mtGuardPanelFold;
  c.textContent=window._mtGuardPanelFold?'▸ 展开总览':'▾ 折叠总览';
  /* R205: 折叠态存 localStorage, 刷新恢复 */
  try{ localStorage.setItem('_mtGuardPanelFold', window._mtGuardPanelFold?'1':'0'); }catch(_){}
  const d=$('#mtguardpaneld');
  if(window._mtGuardPanelFold){ /* 折叠: 隐总览面板 */
    if(d){ d.style.display='none'; } clearTimeout(window._mtGuardPanelT);
  } else { /* 展开: 显总览面板(拼当前总览SVG) */
    if(typeof mtGuardPanel==='function'){ mtGuardPanel(); }
  }
  if(typeof _toast==='function'){ _toast(window._mtGuardPanelFold?'已折叠维护守护区总览面板':'已展开维护守护区总览面板', 'ok'); }
}); } })();
/* R205: 总览面板折叠态初始同步(读 localStorage._mtGuardPanelFold 惰性初始化 window._mtGuardPanelFold + 文案/总览面板display随初始折叠态, 刷新恢复总览面板折叠/展开态) */
(function(){
  if(window._mtGuardPanelFold===undefined){
    let _init=false; try{ _init=(localStorage.getItem('_mtGuardPanelFold')==='1'); }catch(_){}
    window._mtGuardPanelFold=_init;
  }
  const c=$('#mtguardpanelfold');
  if(c){ c.textContent=window._mtGuardPanelFold?'▸ 展开总览':'▾ 折叠总览'; }
  const d=$('#mtguardpaneld');
  if(d && window._mtGuardPanelFold){ d.style.display='none'; } /* 刷新恢复折叠态隐总览面板 */
})();
/* 维护守护区全浮层折叠(R203): #mtguardfoldall 点 -> 切 window._mtGuardFoldAll 折叠标志, 折叠/展开维护守护区全浮层(#mtstatebardtl状态详情/#mtmetsumdetail逐轮明细/_mtkeyhintdetail三键提示/_mtguardsnapd四段快照/_mtguardpaneld总览面板display切), 一键折叠/展开维护守护区全浮层省高, 与R159折叠双图区/R202折叠总览面板语言同; R204 折叠态存 localStorage._mtGuardFoldAll 刷新恢复 */
(function(){ const c=$('#mtguardfoldall'); if(!c) return;
  /* R204: 惰性初始化读 localStorage._mtGuardFoldAll, 折叠态跨会话留存(刷新恢复折叠/展开态, 与R159双图区折叠localStorage._mtMetFold记忆语言同) */
  if(window._mtGuardFoldAll===undefined){
    let _init=false; try{ _init=(localStorage.getItem('_mtGuardFoldAll')==='1'); }catch(_){}
    window._mtGuardFoldAll=_init;
  }
  /* 初始折叠态同步: 文案 + 全浮层display */
  c.textContent=window._mtGuardFoldAll?'◎ 展开全浮层':'⊘ 折叠全浮层';
  const _allFolds=['mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardsnapd','mtguardpaneld'];
  if(window._mtGuardFoldAll){ /* 刷新恢复折叠态: 隐全浮层 */
    for(let _i=0; _i<_allFolds.length; _i++){ const _el=document.getElementById(_allFolds[_i]); if(_el){ _el.style.display='none'; } }
  }
  c.addEventListener('click', function(e){ e.stopPropagation();
    if(window._mtGuardFoldAll===undefined){ window._mtGuardFoldAll=false; }
    window._mtGuardFoldAll=!window._mtGuardFoldAll;
    c.textContent=window._mtGuardFoldAll?'◎ 展开全浮层':'⊘ 折叠全浮层';
    /* R204: 折叠态存 localStorage, 刷新恢复 */
    try{ localStorage.setItem('_mtGuardFoldAll', window._mtGuardFoldAll?'1':'0'); }catch(_){}
    if(window._mtGuardFoldAll){ /* 折叠: 隐全浮层 */
      for(let _i=0; _i<_allFolds.length; _i++){ const _el=document.getElementById(_allFolds[_i]); if(_el){ _el.style.display='none'; } }
      clearTimeout(window._mtGuardPanelT); /* 清总览面板8s定时, 不残留自动显 */
      clearTimeout(window._mtGuardSnapT); /* 清四段快照6s定时 */
      /* R206: 全浮层折叠联动总览面板折叠(全浮层含#mtguardpaneld总览面板, _mtGuardPanelFold强制true+#mtguardpanelfold文案切, 两折叠域联动一致省高) */
      if(window._mtGuardPanelFold===undefined){
        let _pfInit=false; try{ _pfInit=(localStorage.getItem('_mtGuardPanelFold')==='1'); }catch(_){}
        window._mtGuardPanelFold=_pfInit;
      }
      window._mtGuardPanelFold=true; /* 全浮层折叠态强制总览面板折叠 */
      try{ localStorage.setItem('_mtGuardPanelFold','1'); }catch(_){}
      const _pfBtn=document.getElementById('mtguardpanelfold');
      if(_pfBtn){ _pfBtn.textContent='▸ 展开总览'; } /* 文案切, 全浮层折叠时总览面板折叠 */
    } else { /* 展开态: 恢复总览面板自身localStorage折叠态(R206, 全浮层展开时总览面板跟自身localStorage不强制展开) */
      if(window._mtGuardPanelFold===undefined){
        let _pfInit=false; try{ _pfInit=(localStorage.getItem('_mtGuardPanelFold')==='1'); }catch(_){}
        window._mtGuardPanelFold=_pfInit;
      }
      /* 全浮层展开: 若总览面板localStorage折叠态, 隐#mtguardpaneld; 否则恢复自身 */
      const _pfState=(localStorage.getItem('_mtGuardPanelFold')==='1');
      window._mtGuardPanelFold=_pfState;
      const _pfBtn=document.getElementById('mtguardpanelfold');
      if(_pfBtn){ _pfBtn.textContent=_pfState?'▸ 展开总览':'▾ 折叠总览'; }
      const _pd=document.getElementById('mtguardpaneld');
      if(_pd){ _pd.style.display=_pfState?'none':'block'; if(!_pfState && _pd.innerHTML && _pd.innerHTML.indexOf('<svg')<0 && typeof mtGuardPanel==='function'){ /* 展开态总览面板空则拼当前总览SVG */ } }
      if(_pfState){ /* 总览面板自身折叠态: 不显总览面板, 不触发8s */ }
      else { /* 总览面板自身展开态: 若总览面板有内容且当前显, 走mtGuardPanel8s自动隐 */ }
    }
    if(typeof _toast==='function'){ _toast(window._mtGuardFoldAll?'已折叠维护守护区全浮层':'已展开维护守护区全浮层', 'ok'); }
  });
})();
/* 维护守护区三域折叠态总览(R207): #mtguardfoldstat 点 -> 读三域折叠标志(window._mtMetFold双图区/R159+window._mtGuardPanelFold总览面板/R202+window._mtGuardFoldAll全浮层/R204)+localStorage记忆(_mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll), 拼内联SVG三域折叠态图(三域折叠/展开色带+localStorage记忆标位), 显#mtguardfoldstatd浮层, 三域折叠态一眼全貌免逐点各折叠钮, 与R197四段快照/R199总览面板语言同 */
function mtGuardFoldStat(){
  const d=$('#mtguardfoldstatd'); if(!d) return;
  /* 全折叠域5域折叠标志惰性读(window标志+localStorage记忆, 跨会话恢复; R224三域->全折叠域5域加折叠全链路/全折叠域总控面板) */
  let _metFold=false; try{ _metFold=(localStorage.getItem('_mtMetFold')==='1'); }catch(_){}
  let _pfFold=false; try{ _pfFold=(localStorage.getItem('_mtGuardPanelFold')==='1'); }catch(_){}
  let _allFold=false; try{ _allFold=(localStorage.getItem('_mtGuardFoldAll')==='1'); }catch(_){}
  let _ctlFold=false; try{ _ctlFold=(localStorage.getItem('_mtGuardFoldCtl')==='1'); }catch(_){}
  let _domFold=false; try{ _domFold=(localStorage.getItem('_mtGuardAllDomain')==='1'); }catch(_){}
  const _W=340, _H=200, _p=10;
  let _svg='<svg width="'+_W+'" height="'+_H+'" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">';
  _svg+='<text x="'+_p+'" y="14" font-size="10" font-weight="600" fill="var(--ink)">维护守护区全折叠域5域折叠态总览</text>';
  /* 全折叠域5域: 双图区/总览面板/全浮层/折叠全链路/全折叠域总控面板, 各域折叠色带+localStorage记忆标位 */
  const _domains=[
    {name:'双图区', btn:'#mtmetfold', fold:_metFold, lsKey:'_mtMetFold'},
    {name:'总览面板', btn:'#mtguardpanelfold', fold:_pfFold, lsKey:'_mtGuardPanelFold'},
    {name:'全浮层', btn:'#mtguardfoldall', fold:_allFold, lsKey:'_mtGuardFoldAll'},
    {name:'折叠全链路', btn:'#mtguardfoldctl', fold:_ctlFold, lsKey:'_mtGuardFoldCtl'},
    {name:'全折叠域总控', btn:'#mtguardalldomain', fold:_domFold, lsKey:'_mtGuardAllDomain'}
  ];
  for(let _i=0;_i<5;_i++){
    const _dm=_domains[_i];
    const _y=26+_i*34;
    const _col=_dm.fold?'var(--warn)':'var(--ok)'; /* 折叠黄/展开绿 */
    _svg+='<text x="'+_p+'" y="'+(_y+4)+'" font-size="9" fill="var(--dim)">'+_dm.name+' ('+_dm.btn+')</text>';
    _svg+='<rect x="'+(_p+80)+'" y="'+_y+'" width="120" height="10" rx="5" fill="'+_col+'"/>'; /* 折叠色带 */
    _svg+='<text x="'+(_p+208)+'" y="'+(_y+9)+'" font-size="9" fill="'+_col+'">'+(_dm.fold?'折叠':'展开')+'</text>';
    _svg+='<text x="'+_p+'" y="'+(_y+18)+'" font-size="8" fill="var(--dim)">localStorage '+_dm.lsKey+' = '+(_dm.fold?'1':'0')+'</text>';
  }
  /* 时间戳 */
  _svg+='<text x="'+_p+'" y="'+(_H-4)+'" font-size="8" fill="var(--dim)">'+new Date().toLocaleString()+'</text>';
  _svg+='</svg>';
  d.innerHTML=_svg; d.style.display='block';
  const r=document.getElementById('mtguardfoldstat').getBoundingClientRect();
  d.style.position='absolute'; d.style.left=r.left+'px'; d.style.top=(r.bottom+2)+'px';
  clearTimeout(window._mtGuardFoldStatT);
  window._mtGuardFoldStatT=setTimeout(function(){ d.style.display='none'; }, 8000);
}
(function(){ const c=$('#mtguardfoldstat'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardFoldStat(); }); } })();
/* 三域折叠态PNG导出(R208): #mtguardfoldstatpng 点 -> 读 #mtguardfoldstatd 内联SVG(若无则先 mtGuardFoldStat 生成), canvas 转 PNG 下载「music3_维护守护三域折叠态_<ts>.png」, 三域折叠态全貌PNG存档/可分享, 与R158/R198/R200PNG导出同语言 */
function mtGuardFoldStatPng(){
  const d=$('#mtguardfoldstatd'); if(!d) return;
  if(!d.innerHTML || d.innerHTML.indexOf('<svg')<0){ if(typeof mtGuardFoldStat==='function'){ mtGuardFoldStat(); } }
  const svg=d.querySelector('svg');
  if(!svg){ if(typeof _toast==='function'){ _toast('无三域折叠态总览可导出（折叠态总览空）', 'bad'); } return; }
  const _W=svg.getAttribute('width')||340, _H=svg.getAttribute('height')||140;
  const _svgStr=new XMLSerializer().serializeToString(svg);
  const _b64=btoa(unescape(encodeURIComponent(_svgStr)));
  const _img=new Image();
  _img.onload=function(){
    const _cv=document.createElement('canvas'); _cv.width=Number(_W); _cv.height=Number(_H);
    const _cx=_cv.getContext('2d');
    _cx.fillStyle='#f7f5f0'; _cx.fillRect(0,0,_cv.width,_cv.height);
    _cx.drawImage(_img,0,0);
    try{
      _cv.toBlob(function(blob){
        if(!blob){ _fallbackCopy(); return; }
        const _url=URL.createObjectURL(blob);
        const _a=document.createElement('a');
        _a.href=_url; _a.download='music3_维护守护三域折叠态_'+new Date().toISOString().replace(/[:.]/g,'-')+'.png';
        document.body.appendChild(_a); _a.click(); document.body.removeChild(_a);
        setTimeout(function(){ URL.revokeObjectURL(_url); }, 4000);
        if(typeof _toast==='function'){ _toast('已下载三域折叠态 PNG', 'ok'); }
      },'image/png');
    }catch(_){ _fallbackCopy(); }
    function _fallbackCopy(){
      const _txt='#music3 三域折叠态 SVG\n'+_svgStr;
      if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制三域折叠态 SVG（PNG 导出不可用降级）', 'ok'); } }).catch(function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败且复制降级失败', 'bad'); } }); }
      else { if(typeof _toast==='function'){ _toast('PNG 导出失败（canvas 不可用）', 'bad'); } }
    }
  };
  _img.onerror=function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败（SVG 渲染不可用）', 'bad'); } };
  _img.src='data:image/svg+xml;base64,'+_b64;
}
(function(){ const c=$('#mtguardfoldstatpng'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardFoldStatPng(); }); } })();
/* 三域折叠态文本复制(R208): #mtguardfoldstatcopy 点 -> 读三域localStorage折叠记忆(_mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll)拼三域折叠态文本(三域折叠/展开+localStorage记忆值)到剪贴板, 三域折叠态可文本留存/贴工单, 与R196/R201复制出口同语言 */
function mtGuardFoldStatCopy(){
  let _metFold=false; try{ _metFold=(localStorage.getItem('_mtMetFold')==='1'); }catch(_){}
  let _pfFold=false; try{ _pfFold=(localStorage.getItem('_mtGuardPanelFold')==='1'); }catch(_){}
  let _allFold=false; try{ _allFold=(localStorage.getItem('_mtGuardFoldAll')==='1'); }catch(_){}
  let _ctlFold2=false; try{ _ctlFold2=(localStorage.getItem('_mtGuardFoldCtl')==='1'); }catch(_){}
  let _domFold2=false; try{ _domFold2=(localStorage.getItem('_mtGuardAllDomain')==='1'); }catch(_){}
  let _lines='#music3 全折叠域5域折叠态总览 · '+new Date().toLocaleString()+'\n';
  _lines+='[双图区 #mtmetfold] · ' +(_metFold?'折叠':'展开')+' · localStorage _mtMetFold=' +(_metFold?'1':'0')+'\n';
  _lines+='[总览面板 #mtguardpanelfold] · ' +(_pfFold?'折叠':'展开')+' · localStorage _mtGuardPanelFold=' +(_pfFold?'1':'0')+'\n';
  _lines+='[全浮层 #mtguardfoldall] · ' +(_allFold?'折叠':'展开')+' · localStorage _mtGuardFoldAll=' +(_allFold?'1':'0')+'\n';
  _lines+='[折叠全链路 #mtguardfoldctl] · ' +(_ctlFold2?'折叠':'展开')+' · localStorage _mtGuardFoldCtl=' +(_ctlFold2?'1':'0')+'\n';
  _lines+='[全折叠域总控 #mtguardalldomain] · ' +(_domFold2?'折叠':'展开')+' · localStorage _mtGuardAllDomain=' +(_domFold2?'1':'0')+'\n';
  /* R224 全折叠域5域总览自含全折叠域当前态(5键/5标志/5折叠钮/7浮层, 与R222/R223补全折叠域字段同域) */
  const _flc2=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  _lines+='[全折叠域当前态] localStorage 5键: _mtMetFold='+_flc2[0]+' · _mtGuardPanelFold='+_flc2[1]+' · _mtGuardFoldAll='+_flc2[2]+' · _mtGuardFoldCtl='+_flc2[3]+' · _mtGuardAllDomain='+_flc2[4]+'\n';
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制全折叠域5域折叠态文本', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ const c=$('#mtguardfoldstatcopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardFoldStatCopy(); }); } })();
/* 维护守护区折叠全链路总控(R209): #mtguardfoldctl 点 -> 拼内联SVG折叠全链路面板(三域折叠钮+折叠联动R206+折叠记忆R204/R205localStorage+三域折叠态总览R207+折叠态PNG/文本R208全折叠出口分块标位), 显#mtguardfoldctld浮层, 折叠域能力/出口全景图免分散找, 与R199总览面板语言同 */
function mtGuardFoldCtl(){
  const d=$('#mtguardfoldctld'); if(!d) return;
  const _W=400, _H=236, _p=10;
  let _svg='<svg width="'+_W+'" height="'+_H+'" xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif">';
  _svg+='<text x="'+_p+'" y="14" font-size="10" font-weight="600" fill="var(--ink)">维护守护区折叠全链路总控（全折叠域5域）</text>';
  /* 块1: 全折叠域5域折叠钮(R225三域->全折叠域5域加折叠全链路/全折叠域总控面板) */
  _svg+='<rect x="'+_p+'" y="22" width="180" height="66" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="36" font-size="9" fill="var(--dim)">全折叠域5域折叠钮</text>';
  const _fbtns=['#mtmetfold 双图区(R159)','#mtguardpanelfold 总览面板(R202)','#mtguardfoldall 全浮层(R203)','#mtguardfoldctl 折叠全链路(R209)','#mtguardalldomain 全折叠域(R216)'];
  for(let _i=0;_i<5;_i++){ _svg+='<text x="'+(_p+8)+'" y="'+(48+_i*9)+'" font-size="8" fill="var(--ink)">'+_fbtns[_i]+'</text>'; }
  /* 块2: 折叠联动 */
  _svg+='<rect x="'+(_p+190)+'" y="22" width="180" height="48" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+196)+'" y="36" font-size="9" fill="var(--dim)">折叠联动 (R206)</text>';
  _svg+='<text x="'+(_p+198)+'" y="48" font-size="8" fill="var(--ink)">全浮层折叠态强制总览面板折叠</text>';
  _svg+='<text x="'+(_p+198)+'" y="58" font-size="8" fill="var(--ink)">_mtGuardFoldAll→_mtGuardPanelFold</text>';
  _svg+='<text x="'+(_p+198)+'" y="68" font-size="8" fill="var(--dim)">展开态恢复自身localStorage值</text>';
  /* 块3: 折叠记忆(R225三域->全折叠域5域加折叠全链路/全折叠域总控面板) */
  _svg+='<rect x="'+_p+'" y="94" width="180" height="66" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="108" font-size="9" fill="var(--dim)">折叠记忆 (R204/R205)</text>';
  _svg+='<text x="'+(_p+8)+'" y="120" font-size="8" fill="var(--ink)">localStorage _mtGuardFoldAll(全浮层)</text>';
  _svg+='<text x="'+(_p+8)+'" y="130" font-size="8" fill="var(--ink)">localStorage _mtGuardPanelFold(总览)</text>';
  _svg+='<text x="'+(_p+8)+'" y="140" font-size="8" fill="var(--ink)">localStorage _mtMetFold(双图区)</text>';
  _svg+='<text x="'+(_p+8)+'" y="150" font-size="8" fill="var(--ink)">localStorage _mtGuardFoldCtl(全链路)</text>';
  _svg+='<text x="'+(_p+8)+'" y="156" font-size="8" fill="var(--ink)">localStorage _mtGuardAllDomain(全折叠域)</text>';
  /* 块4: 全折叠域5域折叠态总览(R225三域->全折叠域5域加折叠全链路/全折叠域总控面板) */
  _svg+='<rect x="'+(_p+190)+'" y="94" width="180" height="66" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+196)+'" y="108" font-size="9" fill="var(--dim)">全折叠域5域折叠态总览 (R207/R224)</text>';
  _svg+='<text x="'+(_p+198)+'" y="120" font-size="8" fill="var(--ink)">▣ #mtguardfoldstat 全折叠域5域SVG</text>';
  _svg+='<text x="'+(_p+198)+'" y="130" font-size="8" fill="var(--ink)">_mtguardfoldstatd 内联SVG色带</text>';
  _svg+='<text x="'+(_p+198)+'" y="140" font-size="8" fill="var(--dim)">R224三域->全折叠域5域</text>';
  /* 块5: 全折叠域5键当前态(R225补5键/5标志/5折叠钮/7浮层当前态, 与R222/R223/R224补全折叠域字段同域) */
  _svg+='<rect x="'+_p+'" y="166" width="360" height="48" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="180" font-size="9" fill="var(--dim)">全折叠域当前态 (R222/R223/R224同域)</text>';
  const _fl5c=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  const _kn5c=['Met','Pan','All','Ctl','Dom'];
  const _cw5c=Math.floor((360-12)/5)-2;
  for(let _i=0;_i<5;_i++){
    const _sx=_p+6+_i*(Math.floor((360-12)/5));
    const _scol=(_fl5c[_i]==='0')?'var(--ok)':'var(--bad)';
    _svg+='<rect x="'+_sx+'" y="188" width="'+_cw5c+'" height="14" rx="2" fill="var(--bg2)" stroke="'+_scol+'"/><text x="'+(_sx+2)+'" y="198" font-size="7" fill="'+_scol+'">'+_kn5c[_i]+'='+_fl5c[_i]+'</text>';
  }
  /* 块6: 折叠态 PNG / 文本 */
  _svg+='<rect x="'+_p+'" y="220" width="360" height="12" rx="4" fill="var(--bg2)" stroke="var(--line)"/>';
  _svg+='<text x="'+(_p+6)+'" y="229" font-size="8" fill="var(--ink)">⬇ #mtguardfoldstatpng · ⧉ #mtguardfoldstatcopy · ⬇ #mtguardfoldctlpng · ⧉ #mtguardfoldctlcopy</text>';
  /* 时间戳 */
  _svg+='<text x="'+_p+'" y="'+(_H-4)+'" font-size="8" fill="var(--dim)">'+new Date().toLocaleString()+'</text>';
  _svg+='</svg>';
  d.innerHTML=_svg; d.style.display='block';
  const r=document.getElementById('mtguardfoldctl').getBoundingClientRect();
  d.style.position='absolute'; d.style.left=r.left+'px'; d.style.top=(r.bottom+2)+'px';
  /* R211: 折叠态(window._mtGuardFoldCtl)不8s自动隐, 展开态才8s自动隐 — 折叠全链路面板常驻省高, 展开态临时看8s隐, 与R204/R205折叠记忆语言同 */
  if(window._mtGuardFoldCtl===undefined){
    let _init=false; try{ _init=(localStorage.getItem('_mtGuardFoldCtl')==='1'); }catch(_){}
    window._mtGuardFoldCtl=_init;
  }
  if(!window._mtGuardFoldCtl){ clearTimeout(window._mtGuardFoldCtlT); window._mtGuardFoldCtlT=setTimeout(function(){ d.style.display='none'; }, 8000); }
}
/* R211: #mtguardfoldctl 点切折叠记忆态(window._mtGuardFoldCtl+localStorage._mtGuardFoldCtl), 折叠态常驻省高/展开态8s自动隐, 与R204/R205折叠记忆语言同 */
(function(){ const c=$('#mtguardfoldctl'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation();
  if(window._mtGuardFoldCtl===undefined){
    let _init=false; try{ _init=(localStorage.getItem('_mtGuardFoldCtl')==='1'); }catch(_){}
    window._mtGuardFoldCtl=_init;
  }
  /* 折叠态点切展开(拼面板+8s自动隐), 展开态点切折叠(隐面板常驻) */
  if(window._mtGuardFoldCtl){ /* 当前折叠态, 切展开: 拼面板显, 不常驻(展开态8s自动隐) */
    window._mtGuardFoldCtl=false;
    try{ localStorage.setItem('_mtGuardFoldCtl','0'); }catch(_){}
    c.textContent='▤ 折叠全链路';
    if(typeof mtGuardFoldCtl==='function'){ mtGuardFoldCtl(); } /* mtGuardFoldCtl展开态8s自动隐 */
  } else { /* 当前展开态, 切折叠: 隐面板常驻 */
    window._mtGuardFoldCtl=true;
    try{ localStorage.setItem('_mtGuardFoldCtl','1'); }catch(_){}
    c.textContent='▸ 展开全链路';
    const d=$('#mtguardfoldctld'); if(d){ d.style.display='none'; }
    clearTimeout(window._mtGuardFoldCtlT); /* 折叠态清8s定时, 不残留自动显 */
  }
  if(typeof _toast==='function'){ _toast(window._mtGuardFoldCtl?'已折叠维护守护区折叠全链路':'已展开维护守护区折叠全链路', 'ok'); }
}); } })();
/* R211: 折叠全链路面板折叠态初始同步(读localStorage._mtGuardFoldCtl惰性初始化window._mtGuardFoldCtl+文案/面板display随初始折叠态, 刷新恢复折叠/展开态) */
(function(){
  if(window._mtGuardFoldCtl===undefined){
    let _init=false; try{ _init=(localStorage.getItem('_mtGuardFoldCtl')==='1'); }catch(_){}
    window._mtGuardFoldCtl=_init;
  }
  const c=$('#mtguardfoldctl');
  if(c){ c.textContent=window._mtGuardFoldCtl?'▸ 展开全链路':'▤ 折叠全链路'; }
  const d=$('#mtguardfoldctld');
  if(d && window._mtGuardFoldCtl){ d.style.display='none'; } /* 刷新恢复折叠态隐面板 */
})();
/* 折叠全链路PNG导出(R210): #mtguardfoldctlpng 点 -> 读 #mtguardfoldctld 内联SVG(若无则先 mtGuardFoldCtl 生成), canvas 转 PNG 下载「music3_维护守护折叠全链路_<ts>.png」, 折叠域全链路PNG存档/可分享, 与R158/R198/R200/R208PNG导出同语言 */
function mtGuardFoldCtlPng(){
  const d=$('#mtguardfoldctld'); if(!d) return;
  if(!d.innerHTML || d.innerHTML.indexOf('<svg')<0){ if(typeof mtGuardFoldCtl==='function'){ mtGuardFoldCtl(); } }
  const svg=d.querySelector('svg');
  if(!svg){ if(typeof _toast==='function'){ _toast('无折叠全链路总控可导出（全链路面板空）', 'bad'); } return; }
  const _W=svg.getAttribute('width')||400, _H=svg.getAttribute('height')||180;
  const _svgStr=new XMLSerializer().serializeToString(svg);
  const _b64=btoa(unescape(encodeURIComponent(_svgStr)));
  const _img=new Image();
  _img.onload=function(){
    const _cv=document.createElement('canvas'); _cv.width=Number(_W); _cv.height=Number(_H);
    const _cx=_cv.getContext('2d');
    _cx.fillStyle='#f7f5f0'; _cx.fillRect(0,0,_cv.width,_cv.height);
    _cx.drawImage(_img,0,0);
    try{
      _cv.toBlob(function(blob){
        if(!blob){ _fallbackCopy(); return; }
        const _url=URL.createObjectURL(blob);
        const _a=document.createElement('a');
        _a.href=_url; _a.download='music3_维护守护折叠全链路_'+new Date().toISOString().replace(/[:.]/g,'-')+'.png';
        document.body.appendChild(_a); _a.click(); document.body.removeChild(_a);
        setTimeout(function(){ URL.revokeObjectURL(_url); }, 4000);
        if(typeof _toast==='function'){ _toast('已下载折叠全链路 PNG', 'ok'); }
      },'image/png');
    }catch(_){ _fallbackCopy(); }
    function _fallbackCopy(){
      const _txt='#music3 折叠全链路 SVG\n'+_svgStr;
      if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制折叠全链路 SVG（PNG 导出不可用降级）', 'ok'); } }).catch(function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败且复制降级失败', 'bad'); } }); }
      else { if(typeof _toast==='function'){ _toast('PNG 导出失败（canvas 不可用）', 'bad'); } }
    }
  };
  _img.onerror=function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败（SVG 渲染不可用）', 'bad'); } };
  _img.src='data:image/svg+xml;base64,'+_b64;
}
(function(){ const c=$('#mtguardfoldctlpng'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardFoldCtlPng(); }); } })();
/* 折叠全链路文本复制(R210): #mtguardfoldctscopy 点 -> 读折叠全链路五块(三域折叠钮+折叠联动R206+折叠记忆R204/R205+三域折叠态总览R207+折叠态PNG/文本R208)拼全链路文本到剪贴板, 折叠全链路可文本留存/贴工单, 与R196/R201/R208复制出口同语言 */
function mtGuardFoldCtlCopy(){
  let _lines='#music3 维护守护区折叠全链路总控 · '+new Date().toLocaleString()+'\n';
  _lines+='\n[全折叠域5域折叠钮]\n';
  _lines+='#mtmetfold 双图区(R159) · #mtguardpanelfold 总览面板(R202) · #mtguardfoldall 全浮层(R203) · #mtguardfoldctl 折叠全链路(R209) · #mtguardalldomain 全折叠域(R216)\n';
  _lines+='\n[折叠联动 (R206)]\n';
  _lines+='全浮层折叠态强制总览面板折叠(_mtGuardFoldAll→_mtGuardPanelFold) · 展开态恢复自身localStorage值\n';
  _lines+='\n[折叠记忆 (R204/R205)]\n';
  let _g1='', _g2='', _g3='', _g4='', _g5='';
  try{ _g1=localStorage.getItem('_mtGuardFoldAll')||'0'; _g2=localStorage.getItem('_mtGuardPanelFold')||'0'; _g3=localStorage.getItem('_mtMetFold')||'0'; _g4=localStorage.getItem('_mtGuardFoldCtl')||'0'; _g5=localStorage.getItem('_mtGuardAllDomain')||'0'; }catch(_){}
  _lines+='localStorage _mtGuardFoldAll='+_g1+' · _mtGuardPanelFold='+_g2+' · _mtMetFold='+_g3+' · _mtGuardFoldCtl='+_g4+' · _mtGuardAllDomain='+_g5+'\n';
  _lines+='\n[全折叠域5域折叠态总览 (R207/R224)]\n';
  _lines+='▣ #mtguardfoldstat 全折叠域5域折叠态SVG · #mtguardfoldstatd 内联SVG色带\n';
  _lines+='\n[全折叠域当前态 (R222/R223/R224同域)]\n';
  _lines+='localStorage 5键: _mtMetFold='+_g3+' · _mtGuardPanelFold='+_g2+' · _mtGuardFoldAll='+_g1+' · _mtGuardFoldCtl='+_g4+' · _mtGuardAllDomain='+_g5+'\n';
  _lines+='\n[折叠态 PNG / 文本 (R208)]\n';
  _lines+='⬇ #mtguardfoldstatpng PNG导出 · ⧉ #mtguardfoldstatcopy 文本复制\n';
  _lines+='\n[折叠全链路 (R209/R210)]\n';
  _lines+='▤ #mtguardfoldctl 全链路总控 · ⬇ #mtguardfoldctlpng 全链路PNG · ⧉ #mtguardfoldctscopy 全链路复制\n';
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制折叠全链路文本', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ const c=$('#mtguardfoldctscopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardFoldCtlCopy(); }); } })();
/* R212 全折叠记忆一键重置: #mtguardfoldreset 点->清localStorage._mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll/_mtGuardFoldCtl全'0'+window标志全false+全折叠出口文案/display恢复展开态, 维护守护区全折叠记忆一键复位 */
function mtGuardFoldReset(){
  try{ localStorage.setItem('_mtMetFold','0'); localStorage.setItem('_mtGuardPanelFold','0'); localStorage.setItem('_mtGuardFoldAll','0'); localStorage.setItem('_mtGuardFoldCtl','0'); }catch(_){}
  window._mtMetFold=false; window._mtGuardPanelFold=false; window._mtGuardFoldAll=false; window._mtGuardFoldCtl=false;
  const _resetBtns=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl'];
  const _expandTxt={'mtmetfold':'▾ 折叠双图区','mtguardpanelfold':'▾ 折叠总览','mtguardfoldall':'⊘ 折叠全浮层','mtguardfoldctl':'▤ 折叠全链路'};
  for(let _i=0;_i<4;_i++){ const _b=document.getElementById(_resetBtns[_i]); if(_b && _expandTxt[_resetBtns[_i]]){ _b.textContent=_expandTxt[_resetBtns[_i]]; } }
  const _pfD=document.getElementById('mtguardpaneld'); if(_pfD){ _pfD.style.display='none'; }
  const _ctlD=document.getElementById('mtguardfoldctld'); if(_ctlD){ _ctlD.style.display='none'; }
  /* R213: 全折叠记忆重置联动全浮层display复位(三域折叠态总览#mtguardfoldstatd+状态详情#mtstatebardtl+逐轮明细#mtmetsumdetail+三键提示#mtkeyhintdetail全浮层display复位默认态, 全折叠记忆一键复位后全浮层全复位) */
  const _fsD=document.getElementById('mtguardfoldstatd'); if(_fsD){ _fsD.style.display='none'; }
  const _sbD=document.getElementById('mtstatebardtl'); if(_sbD){ _sbD.style.display='none'; }
  const _msD=document.getElementById('mtmetsumdetail'); if(_msD){ _msD.style.display='none'; }
  const _khD=document.getElementById('mtkeyhintdetail'); if(_khD){ _khD.style.display='none'; }
  /* R219: 全折叠记忆重置联动全折叠域总控面板折叠记忆复位(localStorage._mtGuardAllDomain清'0'+window._mtGuardAllDomain复位false+#mtguardalldomain文案/#mtguardalldomains display复位展开态, 全折叠记忆一键复位后全折叠域总控面板折叠记忆全复位) */
  try{ localStorage.setItem('_mtGuardAllDomain','0'); }catch(_){}
  window._mtGuardAllDomain=false;
  const _ad=document.getElementById('mtguardalldomain'); if(_ad){ _ad.textContent='▣ 全折叠域'; }
  const _adD=document.getElementById('mtguardalldomains'); if(_adD){ _adD.style.display='none'; }
  clearTimeout(window._mtGuardAllDomainT);
  /* R235: 全折叠记忆重置联动全折叠域5域折叠态总控浮层折叠记忆复位(localStorage._mtGuardAllFoldStat清'0'+window._mtGuardAllFoldStat复位false+#mtallfoldstat文案/#mtallfoldstatd display复位展开态, 全折叠记忆一键复位后全折叠域6键全复位) */
  try{ localStorage.setItem('_mtGuardAllFoldStat','0'); }catch(_){}
  window._mtGuardAllFoldStat=false;
  const _afs=document.getElementById('mtallfoldstat'); if(_afs){ _afs.textContent='▣ 全折叠域浮层'; }
  const _afsD=document.getElementById('mtallfoldstatd'); if(_afsD){ _afsD.style.display='none'; _afsD.innerHTML=''; } /* R240 全折叠记忆重置联动全折叠域5域折叠态总控浮层重置详情innerHTML清(免全复位后残留旧SVG) */
  clearTimeout(window._mtGuardAllFoldStatT);
  clearTimeout(window._mtGuardPanelT); clearTimeout(window._mtGuardFoldCtlT);
  if(typeof _toast==='function'){ _toast('已重置维护守护区全折叠记忆', 'ok'); }
}
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtguardfoldreset'){ e.stopPropagation(); mtGuardFoldReset(); } }); })();
/* R214 全折叠记忆重置详情复制: #mtguardfoldresetcopy 点->读全折叠记忆重置后各数据源(localStorage4键复位值+window4标志复位值+4折叠钮文案复位+6浮层display复位+重置时间戳)拼重置详情到剪贴板, 全折叠记忆重置详情可文本留存/贴工单, 与R196/R201/R208复制出口同语言 */
function mtGuardFoldResetCopy(){
  let _ls=[localStorage.getItem('_mtMetFold'),localStorage.getItem('_mtGuardPanelFold'),localStorage.getItem('_mtGuardFoldAll'),localStorage.getItem('_mtGuardFoldCtl'),localStorage.getItem('_mtGuardAllDomain'),localStorage.getItem('_mtGuardAllFoldStat')];
  let _w=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
  const _btns=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain','mtallfoldstat'];
  const _floors=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains','mtallfoldstatd'];
  let _lines='#music3 全折叠记忆重置详情 · '+new Date().toLocaleString()+'\n';
  _lines+='[localStorage 6键复位值]\n';
  _lines+=('_mtMetFold='+_ls[0]+' · _mtGuardPanelFold='+_ls[1]+' · _mtGuardFoldAll='+_ls[2]+' · _mtGuardFoldCtl='+_ls[3]+' · _mtGuardAllDomain='+_ls[4]+' · _mtGuardAllFoldStat='+_ls[5])+'\n';
  _lines+='\n[window 6标志复位值]\n';
  _lines+=('_mtMetFold='+_w[0]+' · _mtGuardPanelFold='+_w[1]+' · _mtGuardFoldAll='+_w[2]+' · _mtGuardFoldCtl='+_w[3]+' · _mtGuardAllDomain='+_w[4]+' · _mtGuardAllFoldStat='+_w[5])+'\n';
  _lines+='\n[6折叠钮文案复位]\n';
  for(let _i=0;_i<6;_i++){ const _b=document.getElementById(_btns[_i]); _lines+=_btns[_i]+'='+(_b?_b.textContent:'无')+'\n'; }
  _lines+='\n[8浮层display复位]\n';
  for(let _i=0;_i<8;_i++){ const _f=document.getElementById(_floors[_i]); _lines+=_floors[_i]+'='+(_f?_f.style.display:'无')+'\n'; }
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制全折叠记忆重置详情', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtguardfoldresetcopy'){ e.stopPropagation(); mtGuardFoldResetCopy(); } }); })();
/* R215 全折叠记忆重置详情PNG导出: #mtguardfoldresetpng 点->拼全折叠记忆重置详情内联SVG(4键+4标志+4折叠钮+6浮层复位状态色带+时间戳)canvas转PNG下载「music3_全折叠记忆重置详情_<ts>.png」, toBlob不可用降级复制SVG源码, 与R158/R198/R200/R208PNG导出同语言 */
function mtGuardFoldResetPng(){
  const _ls=[localStorage.getItem('_mtMetFold'),localStorage.getItem('_mtGuardPanelFold'),localStorage.getItem('_mtGuardFoldAll'),localStorage.getItem('_mtGuardFoldCtl'),localStorage.getItem('_mtGuardAllDomain'),localStorage.getItem('_mtGuardAllFoldStat')];
  const _w=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
  const _btns=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain','mtallfoldstat'];
  const _floors=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains','mtallfoldstatd'];
  const _ts=new Date().toLocaleString();
  const _OK='rgb(47,125,85)', _BAD='rgb(163,38,26)', _DIM='rgb(119,112,106)', _ACC='#c4381f';
  const _W=440; let _y=8; const _rows=[];
  _rows.push('<text x="8" y="'+_y+'" font-size="11" fill="'+_ACC+'" font-weight="600">music3 全折叠记忆重置详情 · '+_ts+'</text>'); _y+=18;
  _rows.push('<text x="8" y="'+_y+'" font-size="10" fill="'+_DIM+'">[localStorage 6键复位值]</text>'); _y+=14;
  for(let _i=0;_i<6;_i++){ const _c=(_ls[_i]==='0')?_OK:_BAD; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">_mtMetFold等['+_i+']='+_ls[_i]+'</text>'); _y+=13; }
  _rows.push('<text x="8" y="'+_y+'" font-size="10" fill="'+_DIM+'">[window 6标志复位值]</text>'); _y+=14;
  for(let _i=0;_i<6;_i++){ const _c=(_w[_i]===false)?_OK:_BAD; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">标志['+_i+']='+_w[_i]+'</text>'); _y+=13; }
  _rows.push('<text x="8" y="'+_y+'" font-size="10" fill="'+_DIM+'">[6折叠钮文案复位]</text>'); _y+=14;
  for(let _i=0;_i<6;_i++){ const _b=document.getElementById(_btns[_i]); const _v=_b?_b.textContent:'无'; _rows.push('<text x="8" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_btns[_i]+'='+_v+'</text>'); _y+=12; }
  _rows.push('<text x="8" y="'+_y+'" font-size="10" fill="'+_DIM+'">[8浮层display复位]</text>'); _y+=14;
  for(let _i=0;_i<8;_i++){ const _f=document.getElementById(_floors[_i]); const _v=_f?_f.style.display:'无'; const _c=(_v==='none')?_OK:_DIM; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_floors[_i]+'='+_v+'</text>'); _y+=12; }
  const _H=_y+8;
  const _svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+_W+'" height="'+_H+'">'+_rows.join('')+'</svg>';
  const _svgStr=_svg;
  const _b64=btoa(unescape(encodeURIComponent(_svgStr)));
  const _img=new Image();
  _img.onload=function(){
    const _cv=document.createElement('canvas'); _cv.width=_W; _cv.height=_H;
    const _cx=_cv.getContext('2d');
    _cx.fillStyle='#f7f5f0'; _cx.fillRect(0,0,_cv.width,_cv.height);
    _cx.drawImage(_img,0,0);
    try{
      _cv.toBlob(function(blob){
        if(!blob){ _fallbackCopy(); return; }
        const _url=URL.createObjectURL(blob);
        const _a=document.createElement('a');
        _a.href=_url; _a.download='music3_全折叠记忆重置详情_'+new Date().toISOString().replace(/[:.]/g,'-')+'.png';
        document.body.appendChild(_a); _a.click(); document.body.removeChild(_a);
        setTimeout(function(){ URL.revokeObjectURL(_url); }, 4000);
        if(typeof _toast==='function'){ _toast('已下载全折叠记忆重置详情 PNG', 'ok'); }
      },'image/png');
    }catch(_){ _fallbackCopy(); }
    function _fallbackCopy(){
      const _txt='#music3 全折叠记忆重置详情 SVG\n'+_svgStr;
      if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制全折叠记忆重置详情 SVG（PNG 导出不可用降级）', 'ok'); } }).catch(function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败且复制降级失败', 'bad'); } }); }
      else { if(typeof _toast==='function'){ _toast('PNG 导出失败（canvas 不可用）', 'bad'); } }
    }
  };
  _img.onerror=function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败（SVG 渲染不可用）', 'bad'); } };
  _img.src='data:image/svg+xml;base64,'+_b64;
}
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtguardfoldresetpng'){ e.stopPropagation(); mtGuardFoldResetPng(); } }); })();
/* R216 全折叠域总控面板: #mtguardalldomain 点->拼内联SVG全折叠域总控面板六块(四折叠记忆localStorage键+四折叠出口+全折叠重置+重置详情复制/PNG+全浮层复位+三域折叠态总览), 全折叠域能力/出口全景图免分散找, 与R209折叠全链路总控同语言 */
function mtGuardAllDomain(){
  const _d=document.getElementById('mtguardalldomains'); if(!_d) return;
  const _ls=[localStorage.getItem('_mtMetFold'),localStorage.getItem('_mtGuardPanelFold'),localStorage.getItem('_mtGuardFoldAll'),localStorage.getItem('_mtGuardFoldCtl'),localStorage.getItem('_mtGuardAllDomain')];
  const _btns=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain'];
  const _floors=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains'];
  const _OK='rgb(47,125,85)', _BAD='rgb(163,38,26)', _DIM='rgb(119,112,106)', _ACC='#c4381f', _LN='rgb(226,221,211)';
  const _W=460; let _y=8; const _rows=[];
  _rows.push('<text x="8" y="'+_y+'" font-size="11" fill="'+_ACC+'" font-weight="600">music3 全折叠域总控面板 · '+new Date().toLocaleString()+'</text>'); _y+=18;
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[四折叠记忆 localStorage 键]</text>'); _y+=14;
  for(let _i=0;_i<5;_i++){ const _key=['_mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain'][_i]; const _c=(_ls[_i]==='0')?_OK:_BAD; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_key+'='+_ls[_i]+'</text>'); _y+=13; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[四折叠出口]</text>'); _y+=14;
  for(let _i=0;_i<5;_i++){ const _b=document.getElementById(_btns[_i]); const _v=_b?_b.textContent:'无'; _rows.push('<text x="8" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_btns[_i]+'='+_v+'</text>'); _y+=12; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[全折叠重置]</text>'); _y+=14;
  _rows.push('<text x="8" y="'+_y+'" font-size="9" fill="'+_OK+'">↺ #mtguardfoldreset 全折叠记忆一键复位(清4键+4标志+4折叠钮+全浮层)</text>'); _y+=13;
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[重置详情复制 / PNG]</text>'); _y+=14;
  _rows.push('<text x="8" y="'+_y+'" font-size="9" fill="'+_OK+'">⧉ #mtguardfoldresetcopy 重置详情复制 · ⬇ #mtguardfoldresetpng 重置详情PNG</text>'); _y+=13;
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[全浮层复位]</text>'); _y+=14;
  for(let _i=0;_i<7;_i++){ const _f=document.getElementById(_floors[_i]); const _v=_f?_f.style.display:'无'; const _c=(_v==='none')?_OK:_DIM; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_floors[_i]+'='+_v+'</text>'); _y+=12; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[三域折叠态总览 (R207)]</text>'); _y+=14;
  _rows.push('<text x="8" y="'+_y+'" font-size="9" fill="'+_OK+'">▣ #mtguardfoldstat 三域折叠态SVG · ⬇ #mtguardfoldstatpng · ⧉ #mtguardfoldstatcopy</text>'); _y+=13;
  const _H=_y+8;
  const _svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+_W+'" height="'+_H+'">'+_rows.join('')+'</svg>';
  _d.innerHTML=_svg; _d.style.display='block';
  const _r=document.getElementById('mtguardalldomain').getBoundingClientRect();
  _d.style.position='absolute'; _d.style.left=_r.left+'px'; _d.style.top=(_r.bottom+2)+'px';
  clearTimeout(window._mtGuardAllDomainT);
  if(window._mtGuardAllDomain===undefined){ let _init=false; try{ _init=(localStorage.getItem('_mtGuardAllDomain')==='1'); }catch(_){} window._mtGuardAllDomain=_init; }
  if(!window._mtGuardAllDomain){ _d.style.display='none'; clearTimeout(window._mtGuardAllDomainT); window._mtGuardAllDomainT=setTimeout(function(){ _d.style.display='none'; }, 8000); }
}
/* R218 全折叠域总控面板折叠记忆: #mtguardalldomain 点切折叠记忆态(window._mtGuardAllDomain+localStorage._mtGuardAllDomain), 折叠态常驻省高/展开态8s自动隐, 与R204/R205/R211折叠记忆语言同 */
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtguardalldomain'){ e.stopPropagation();
  if(window._mtGuardAllDomain===undefined){ let _init=false; try{ _init=(localStorage.getItem('_mtGuardAllDomain')==='1'); }catch(_){} window._mtGuardAllDomain=_init; }
  if(window._mtGuardAllDomain){ window._mtGuardAllDomain=false; try{ localStorage.setItem('_mtGuardAllDomain','0'); }catch(_){} document.getElementById('mtguardalldomain').textContent='▣ 全折叠域'; if(typeof mtGuardAllDomain==='function'){ mtGuardAllDomain(); } } else { window._mtGuardAllDomain=true; try{ localStorage.setItem('_mtGuardAllDomain','1'); }catch(_){} document.getElementById('mtguardalldomain').textContent='▸ 展开全折叠域'; const _d=document.getElementById('mtguardalldomains'); if(_d){ _d.style.display='none'; } clearTimeout(window._mtGuardAllDomainT); }
  if(typeof _toast==='function'){ _toast(window._mtGuardAllDomain?'已折叠全折叠域总控':'已展开全折叠域总控', 'ok'); }
  return; } }); })();
/* R218 全折叠域总控面板折叠态初始同步(读localStorage._mtGuardAllDomain惰性初始化+文案/display随初始折叠态, 刷新恢复折叠/展开态) */
(function(){ if(window._mtGuardAllDomain===undefined){ let _init=false; try{ _init=(localStorage.getItem('_mtGuardAllDomain')==='1'); }catch(_){} window._mtGuardAllDomain=_init; } const _c=document.getElementById('mtguardalldomain'); if(_c){ _c.textContent=window._mtGuardAllDomain?'▸ 展开全折叠域':'▣ 全折叠域'; } const _d=document.getElementById('mtguardalldomains'); if(_d && window._mtGuardAllDomain){ _d.style.display='none'; } })();
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtguardalldomain'){ e.stopPropagation(); mtGuardAllDomain(); } }); })();
/* R217 全折叠域总控面板PNG导出: #mtguardalldomainpng 点->读#mtguardalldomains内联SVG(无则先mtGuardAllDomain生成)canvas转PNG下载「music3_全折叠域总控_<ts>.png」, toBlob不可用降级复制SVG源码, 与R158/R198/R200/R208PNG导出同语言 */
function mtGuardAllDomainPng(){
  const _d=document.getElementById('mtguardalldomains'); if(!_d) return;
  if(!_d.innerHTML || _d.innerHTML.indexOf('<svg')<0){ if(typeof mtGuardAllDomain==='function'){ mtGuardAllDomain(); } }
  const _svg=_d.querySelector('svg');
  if(!_svg){ if(typeof _toast==='function'){ _toast('无全折叠域总控面板可导出（全折叠域面板空）', 'bad'); } return; }
  const _W=Number(_svg.getAttribute('width'))||460, _H=Number(_svg.getAttribute('height'))||200;
  const _svgStr=new XMLSerializer().serializeToString(_svg);
  const _b64=btoa(unescape(encodeURIComponent(_svgStr)));
  const _img=new Image();
  _img.onload=function(){
    const _cv=document.createElement('canvas'); _cv.width=_W; _cv.height=_H;
    const _cx=_cv.getContext('2d');
    _cx.fillStyle='#f7f5f0'; _cx.fillRect(0,0,_cv.width,_cv.height);
    _cx.drawImage(_img,0,0);
    try{
      _cv.toBlob(function(blob){
        if(!blob){ _fallbackCopy(); return; }
        const _url=URL.createObjectURL(blob);
        const _a=document.createElement('a');
        _a.href=_url; _a.download='music3_全折叠域总控_'+new Date().toISOString().replace(/[:.]/g,'-')+'.png';
        document.body.appendChild(_a); _a.click(); document.body.removeChild(_a);
        setTimeout(function(){ URL.revokeObjectURL(_url); }, 4000);
        if(typeof _toast==='function'){ _toast('已下载全折叠域总控 PNG', 'ok'); }
      },'image/png');
    }catch(_){ _fallbackCopy(); }
    function _fallbackCopy(){
      const _txt='#music3 全折叠域总控 SVG\n'+_svgStr;
      if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制全折叠域总控 SVG（PNG 导出不可用降级）', 'ok'); } }).catch(function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败且复制降级失败', 'bad'); } }); }
      else { if(typeof _toast==='function'){ _toast('PNG 导出失败（canvas 不可用）', 'bad'); } }
    }
  };
  _img.onerror=function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败（SVG 渲染不可用）', 'bad'); } };
  _img.src='data:image/svg+xml;base64,'+_b64;
}
/* R217 全折叠域总控文本复制: #mtguardalldomaincopy 点->读全折叠域总控六块(四折叠记忆+四折叠出口+全折叠重置+重置详情复制/PNG+全浮层复位+三域折叠态总览)拼总控文本到剪贴板, 全折叠域总控可文本留存/贴工单, 与R201/R208复制出口同语言 */
function mtGuardAllDomainCopy(){
  let _lines='#music3 全折叠域总控 · '+new Date().toLocaleString()+'\n';
  _lines+='[四折叠记忆 localStorage 键]\n';
  const _ls=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  _lines+=('_mtMetFold='+_ls[0]+' · _mtGuardPanelFold='+_ls[1]+' · _mtGuardFoldAll='+_ls[2]+' · _mtGuardFoldCtl='+_ls[3]+' · _mtGuardAllDomain='+_ls[4])+'\n';
  _lines+='\n[四折叠出口]\n';
  const _btns=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain'];
  for(let _i=0;_i<5;_i++){ const _b=document.getElementById(_btns[_i]); _lines+=_btns[_i]+'='+(_b?_b.textContent:'无')+'\n'; }
  _lines+='\n[全折叠重置]\n';
  _lines+='↺ #mtguardfoldreset 全折叠记忆一键复位(清4键+4标志+4折叠钮+全浮层)\n';
  _lines+='\n[重置详情复制 / PNG]\n';
  _lines+='⧉ #mtguardfoldresetcopy 重置详情复制 · ⬇ #mtguardfoldresetpng 重置详情PNG\n';
  _lines+='\n[全浮层复位]\n';
  const _floors=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains'];
  for(let _i=0;_i<7;_i++){ const _f=document.getElementById(_floors[_i]); _lines+=_floors[_i]+'='+(_f?_f.style.display:'无')+'\n'; }
  _lines+='\n[三域折叠态总览 (R207)]\n';
  _lines+='▣ #mtguardfoldstat 三域折叠态SVG · ⬇ #mtguardfoldstatpng · ⧉ #mtguardfoldstatcopy\n';
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制全折叠域总控文本', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtguardalldomainpng'){ e.stopPropagation(); mtGuardAllDomainPng(); } }); })();
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtguardalldomaincopy'){ e.stopPropagation(); mtGuardAllDomainCopy(); } }); })();
/* 全折叠域5域折叠态一键复制(R232): #mtallfoldcopy 点 -> 拼全折叠域5域/5键/5标志/5折叠钮/7浮层当前态到剪贴板(#music3 全折叠域5域折叠态一键复制·<ts>+全折叠域5域+5键localStorage+5标志window+5折叠钮文案+7浮层display), 全折叠域5域折叠态一键留存/贴工单, 免逐点各面板/出口, 与R222-R231补全折叠域字段同域 */
function mtAllFoldCopy(){
  /* R246 全复位检测: 读localStorage6键全'0'+window6标志全false, 全复位时复制文本标题加「· 全复位态」(_mtallfoldcopy全复位后一键复制自含6键复位态总览, 与R244/R245全复位后SVG标题加_·全复位态同域) */
  var _allReset6=true;
  try{ var _k6=['_mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain','_mtGuardAllFoldStat'];
    for(var _k=0;_k<6;_k++){ if((localStorage.getItem(_k6[_k])||'0')!=='0'){ _allReset6=false; break; } }
    var _w6=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
    for(var _w=0;_w<6;_w++){ if(_w6[_w]!==false){ _allReset6=false; break; } }
  }catch(_){ _allReset6=false; }
  var _rTag=_allReset6?' · 全复位态':'';
  let _lines='#music3 全折叠域5域折叠态一键复制'+_rTag+' · '+new Date().toLocaleString()+'\n';
  /* 全折叠域5域(双图区/总览面板/全浮层/折叠全链路/全折叠域总控面板) */
  _lines+='[全折叠域5域]\n';
  const _doms=[['双图区','#mtmetfold','_mtMetFold'],['总览面板','#mtguardpanelfold','_mtGuardPanelFold'],['全浮层','#mtguardfoldall','_mtGuardFoldAll'],['折叠全链路','#mtguardfoldctl','_mtGuardFoldCtl'],['全折叠域总控','#mtguardalldomain','_mtGuardAllDomain'],['全折叠域5域折叠态总控浮层','#mtallfoldstat','_mtGuardAllFoldStat']];
  for(let _i=0;_i<6;_i++){
    const _btn=document.getElementById(_doms[_i][1].replace('#',''));
    let _fold=false; try{ _fold=(localStorage.getItem(_doms[_i][2])==='1'); }catch(_){}
    _lines+=_doms[_i][0]+' ('+_doms[_i][1]+') · '+(_fold?'折叠':'展开')+' · localStorage '+_doms[_i][2]+'='+(_fold?'1':'0')+'\n';
  }
  /* 6键localStorage */
  _lines+='\n[6键 localStorage 当前态]\n';
  const _ls5=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0',localStorage.getItem('_mtGuardAllFoldStat')||'0'];
  _lines+='_mtMetFold='+_ls5[0]+' · _mtGuardPanelFold='+_ls5[1]+' · _mtGuardFoldAll='+_ls5[2]+' · _mtGuardFoldCtl='+_ls5[3]+' · _mtGuardAllDomain='+_ls5[4]+' · _mtGuardAllFoldStat='+_ls5[5]+'\n';
  /* 6标志window */
  _lines+='\n[6标志 window 当前态]\n';
  const _w5=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
  _lines+='_mtMetFold='+_w5[0]+' · _mtGuardPanelFold='+_w5[1]+' · _mtGuardFoldAll='+_w5[2]+' · _mtGuardFoldCtl='+_w5[3]+' · _mtGuardAllDomain='+_w5[4]+' · _mtGuardAllFoldStat='+_w5[5]+'\n';
  /* 6折叠钮文案 */
  _lines+='\n[6折叠钮文案]\n';
  const _btns5=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain','mtallfoldstat'];
  for(let _i=0;_i<6;_i++){ const _b=document.getElementById(_btns5[_i]); _lines+=_btns5[_i]+'='+(_b?_b.textContent:'无')+'\n'; }
  /* 8浮层display */
  _lines+='\n[8浮层 display 当前态]\n';
  const _floors7=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains','mtallfoldstatd'];
  for(let _i=0;_i<8;_i++){ const _f=document.getElementById(_floors7[_i]); _lines+=_floors7[_i]+'='+(_f?_f.style.display:'无')+'\n'; }
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制全折叠域5域折叠态', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtallfoldcopy'){ e.stopPropagation(); mtAllFoldCopy(); } }); })();
/* 全折叠域5域折叠态PNG快照(R233): #mtallfoldpng 点 -> 拼全折叠域5域/5键/5标志/5折叠钮/7浮层当前态内联SVG -> canvas 转 PNG 下载「music3_全折叠域5域折叠态_<ts>.png」, 全折叠域5域折叠态PNG存档/可分享, 与R232全折叠域5域折叠态一键复制同域 */
function mtAllFoldPng(){
  var _OK='rgb(47,125,85)', _BAD='rgb(163,38,26)', _DIM='rgb(119,112,106)', _LN='rgb(226,221,211)', _ACC='#c4381f';
  var _W=420, _y=8, _rows=[];
  /* R245 全复位检测: 读localStorage6键全'0'+window6标志全false, 全复位时PNG标题加「· 全复位态」(_mtallfoldpng全复位后PNG快照自含6键复位态总览, 与R244_mtallfoldstatd浮层全复位后SVG标题加_·全复位态同域) */
  var _allReset6=true;
  try{ var _k6=['_mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain','_mtGuardAllFoldStat'];
    for(var _k=0;_k<6;_k++){ if((localStorage.getItem(_k6[_k])||'0')!=='0'){ _allReset6=false; break; } }
    var _w6=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
    for(var _w=0;_w<6;_w++){ if(_w6[_w]!==false){ _allReset6=false; break; } }
  }catch(_){ _allReset6=false; }
  var _rTag=_allReset6?' · 全复位态':'';
  _rows.push('<text x="8" y="'+_y+'" font-size="11" fill="'+_ACC+'" font-weight="600">music3 全折叠域5域折叠态'+_rTag+' · '+new Date().toLocaleString()+'</text>'); _y+=18;
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[全折叠域5域]</text>'); _y+=14;
  var _doms=[['双图区','_mtMetFold'],['总览面板','_mtGuardPanelFold'],['全浮层','_mtGuardFoldAll'],['折叠全链路','_mtGuardFoldCtl'],['全折叠域总控','_mtGuardAllDomain'],['全折叠域5域折叠态总控浮层','_mtGuardAllFoldStat']];
  for(var _i=0;_i<6;_i++){ var _fv='0'; try{ _fv=(localStorage.getItem(_doms[_i][1])||'0'); }catch(_){} var _c=(_fv==='0')?_OK:_BAD; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_doms[_i][0]+' '+_doms[_i][1]+'='+_fv+'</text>'); _y+=13; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[6标志 window]</text>'); _y+=14;
  var _w5=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
  var _wk=['_mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain','_mtGuardAllFoldStat'];
  for(var _i=0;_i<6;_i++){ var _c=(_w5[_i]===false)?_OK:_BAD; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_wk[_i]+'='+_w5[_i]+'</text>'); _y+=13; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[6折叠钮文案]</text>'); _y+=14;
  var _btns5=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain','mtallfoldstat'];
  for(var _i=0;_i<6;_i++){ var _b=document.getElementById(_btns5[_i]); _rows.push('<text x="8" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_btns5[_i]+'='+(_b?_b.textContent:'无')+'</text>'); _y+=12; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[8浮层 display]</text>'); _y+=14;
  var _floors7=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains','mtallfoldstatd'];
  for(var _i=0;_i<8;_i++){ var _f=document.getElementById(_floors7[_i]); var _v=_f?_f.style.display:'无'; var _c=(_v==='none')?_OK:_DIM; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_floors7[_i]+'='+_v+'</text>'); _y+=12; }
  var _H=_y+8;
  var _svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+_W+'" height="'+_H+'">'+_rows.join('')+'</svg>';
  var _host=document.createElement('div'); _host.style.cssText='position:fixed;left:-9999px;top:0;width:'+_W+'px'; _host.innerHTML=_svg; document.body.appendChild(_host);
  var _imgv=new Image(); var _b64='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(_svg)));
  _imgv.onload=function(){
    var _cv=document.createElement('canvas'); _cv.width=_W; _cv.height=_H;
    var _g=_cv.getContext('2d'); _g.fillStyle='#fff'; _g.fillRect(0,0,_W,_H); _g.drawImage(_imgv,0,0,_W,_H);
    try{ _cv.toBlob(function(_blob){ if(_blob){ var _u=URL.createObjectURL(_blob); var _a=document.createElement('a'); _a.href=_u; _a.download='music3_全折叠域5域折叠态_'+Date.now()+'.png'; document.body.appendChild(_a); _a.click(); setTimeout(function(){ URL.revokeObjectURL(_u); document.body.removeChild(_a); },3000); }
      else if(typeof _toast==='function'){ _toast('PNG 导出不可用（toBlob 不支持）', 'bad'); } document.body.removeChild(_host); }, 'image/png'); }
    catch(_){ if(typeof _toast==='function'){ _toast('PNG 导出失败（canvas 不可用）', 'bad'); } document.body.removeChild(_host); }
  };
  _imgv.onerror=function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败（SVG 渲染不可用）', 'bad'); } document.body.removeChild(_host); };
  _imgv.src=_b64;
}
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtallfoldpng'){ e.stopPropagation(); mtAllFoldPng(); } }); })();
/* 全折叠域5域折叠态总控浮层(R234): #mtallfoldstat 点 -> 拼全折叠域5域/5键/5标志/5折叠钮/7浮层当前态内联SVG显#mtallfoldstatd浮层(8s自动隐+折叠记忆), 全折叠域5域折叠态一眼全貌+跨会话折叠记忆, 与R232/R233全折叠域5域折叠态一键复制/PNG快照同域 */
function mtAllFoldStat(){
  var _d=document.getElementById('mtallfoldstatd'); if(!_d) return;
  var _OK='rgb(47,125,85)', _BAD='rgb(163,38,26)', _DIM='rgb(119,112,106)', _LN='rgb(226,221,211)', _ACC='#c4381f';
  var _W=420, _y=8, _rows=[];
  /* R244 全复位检测: 读localStorage6键全'0'+window6标志全false, 全复位时SVG标题加「· 全复位态」(_mtallfoldstatd浮层自含6键复位态总览, 与R240/R241/R242/R243全复位后innerHTML清/刷新初始同步IIFE/8s自动隐定时/折叠记忆切IIFE清8s自动隐定时同域) */
  var _allReset6=true;
  try{ var _k6=['_mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain','_mtGuardAllFoldStat'];
    for(var _k=0;_k<6;_k++){ if((localStorage.getItem(_k6[_k])||'0')!=='0'){ _allReset6=false; break; } }
    var _w6=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
    for(var _w=0;_w<6;_w++){ if(_w6[_w]!==false){ _allReset6=false; break; } }
  }catch(_){ _allReset6=false; }
  var _rTag=_allReset6?' · 全复位态':'';
  _rows.push('<text x="8" y="'+_y+'" font-size="11" fill="'+_ACC+'" font-weight="600">music3 全折叠域5域折叠态'+_rTag+' · '+new Date().toLocaleString()+'</text>'); _y+=18;
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[全折叠域5域]</text>'); _y+=14;
  var _doms=[['双图区','_mtMetFold'],['总览面板','_mtGuardPanelFold'],['全浮层','_mtGuardFoldAll'],['折叠全链路','_mtGuardFoldCtl'],['全折叠域总控','_mtGuardAllDomain'],['全折叠域5域折叠态总控浮层','_mtGuardAllFoldStat']];
  for(var _i=0;_i<6;_i++){ var _fv='0'; try{ _fv=(localStorage.getItem(_doms[_i][1])||'0'); }catch(_){} var _c=(_fv==='0')?_OK:_BAD; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_doms[_i][0]+' '+_doms[_i][1]+'='+_fv+'</text>'); _y+=13; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[6标志 window]</text>'); _y+=14;
  var _w5=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain,window._mtGuardAllFoldStat];
  var _wk=['_mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain','_mtGuardAllFoldStat'];
  for(var _i=0;_i<6;_i++){ var _c=(_w5[_i]===false)?_OK:_BAD; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_wk[_i]+'='+_w5[_i]+'</text>'); _y+=13; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[6折叠钮文案]</text>'); _y+=14;
  var _btns5=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain','mtallfoldstat'];
  for(var _i=0;_i<6;_i++){ var _b=document.getElementById(_btns5[_i]); _rows.push('<text x="8" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_btns5[_i]+'='+(_b?_b.textContent:'无')+'</text>'); _y+=12; }
  _rows.push('<line x1="8" y1="'+_y+'" x2="'+(_W-8)+'" y2="'+_y+'" stroke="'+_LN+'"/><text x="8" y="'+(_y+14)+'" font-size="10" fill="'+_DIM+'">[8浮层 display]</text>'); _y+=14;
  var _floors7=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains','mtallfoldstatd'];
  for(var _i=0;_i<8;_i++){ var _f=document.getElementById(_floors7[_i]); var _v=_f?_f.style.display:'无'; var _c=(_v==='none')?_OK:_DIM; _rows.push('<rect x="8" y="'+(_y-8)+'" width="8" height="8" rx="2" fill="'+_c+'"/><text x="20" y="'+_y+'" font-size="9" fill="'+_DIM+'">'+_floors7[_i]+'='+_v+'</text>'); _y+=12; }
  var _H=_y+8;
  var _svg='<svg xmlns="http://www.w3.org/2000/svg" width="'+_W+'" height="'+_H+'">'+_rows.join('')+'</svg>';
  _d.innerHTML=_svg; _d.style.display='block';
  var _r=document.getElementById('mtallfoldstat').getBoundingClientRect();
  _d.style.position='absolute'; _d.style.left=_r.left+'px'; _d.style.top=(_r.bottom+2)+'px';
  clearTimeout(window._mtGuardAllFoldStatT);
  if(window._mtGuardAllFoldStat===undefined){ var _init=false; try{ _init=(localStorage.getItem('_mtGuardAllFoldStat')==='1'); }catch(_){} window._mtGuardAllFoldStat=_init; }
  if(!window._mtGuardAllFoldStat){ _d.style.display='none'; clearTimeout(window._mtGuardAllFoldStatT); window._mtGuardAllFoldStatT=setTimeout(function(){ if(_d.innerHTML){ _d.style.display='none'; _d.innerHTML=''; } }, 8000); } /* R242 8s自动隐定时触发前验innerHTML非空(全复位后innerHTML清R240, 8s自动隐不隐空innerHTML浮层免无副作用触发) + R247 8s自动隐定时触发隐display后清innerHTML(免全复位后8s自动隐触发隐浮层后innerHTML残留旧SVG, 与R240/R242全复位后innerHTML清/8s自动隐定时innerHTML非空校验同域) */
}
/* R234 全折叠域5域折叠态总控浮层折叠记忆切IIFE: #mtallfoldstat点切折叠记忆态(window._mtGuardAllFoldStat+localStorage._mtGuardAllFoldStat), 折叠态常驻省高/展开态8s自动隐, 与R218全折叠域总控面板折叠记忆同语言 */
(function(){ document.addEventListener('click', function(e){ if(e.target && e.target.id==='mtallfoldstat'){ e.stopPropagation();
  if(window._mtGuardAllFoldStat===undefined){ var _init=false; try{ _init=(localStorage.getItem('_mtGuardAllFoldStat')==='1'); }catch(_){} window._mtGuardAllFoldStat=_init; }
  if(window._mtGuardAllFoldStat){ window._mtGuardAllFoldStat=false; try{ localStorage.setItem('_mtGuardAllFoldStat','0'); }catch(_){} document.getElementById('mtallfoldstat').textContent='▣ 全折叠域浮层'; if(typeof mtAllFoldStat==='function'){ mtAllFoldStat(); } } else { window._mtGuardAllFoldStat=true; try{ localStorage.setItem('_mtGuardAllFoldStat','1'); }catch(_){} document.getElementById('mtallfoldstat').textContent='▸ 展开全折叠域浮层'; var _d=document.getElementById('mtallfoldstatd'); if(_d){ _d.style.display='none'; } clearTimeout(window._mtGuardAllFoldStatT); }
  if(typeof _toast==='function'){ _toast(window._mtGuardAllFoldStat?'已折叠全折叠域5域折叠态总控浮层':'已展开全折叠域5域折叠态总控浮层', 'ok'); }
} }); })();
/* R234 全折叠域5域折叠态总控浮层折叠态初始同步: 读localStorage._mtGuardAllFoldStat惰性初始化window._mtGuardAllFoldStat+文案/浮层display随初始折叠态, 刷新恢复折叠/展开态 */
(function(){
  if(window._mtGuardAllFoldStat===undefined){ var _init=false; try{ _init=(localStorage.getItem('_mtGuardAllFoldStat')==='1'); }catch(_){} window._mtGuardAllFoldStat=_init; }
  var c=document.getElementById('mtallfoldstat');
  if(c){ c.textContent=window._mtGuardAllFoldStat?'▸ 展开全折叠域浮层':'▣ 全折叠域浮层'; }
  var d=document.getElementById('mtallfoldstatd');
  if(d && window._mtGuardAllFoldStat){ d.style.display='none'; }
})();
(function(){ const c=$('#mtguardpanel'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardPanel(); }); } })();
/* 维护守护区总览PNG导出(R200): #mtguardpanelpng 点 -> 读 #mtguardpaneld 内联SVG(若无则先 mtGuardPanel 生成), canvas 转 PNG 下载「music3_维护守护总览_<ts>.png」, 能力/出口全景图PNG存档/可分享, 与R158/R198PNG导出同语言 */
function mtGuardPanelPng(){
  const d=$('#mtguardpaneld'); if(!d) return;
  if(!d.innerHTML || d.innerHTML.indexOf('<svg')<0){ if(typeof mtGuardPanel==='function'){ mtGuardPanel(); } }
  const svg=d.querySelector('svg');
  if(!svg){ if(typeof _toast==='function'){ _toast('无维护守护区总览可导出（总览面板空）', 'bad'); } return; }
  const _W=svg.getAttribute('width')||400, _H=svg.getAttribute('height')||210;
  const _svgStr=new XMLSerializer().serializeToString(svg);
  const _b64=btoa(unescape(encodeURIComponent(_svgStr)));
  const _img=new Image();
  _img.onload=function(){
    const _cv=document.createElement('canvas'); _cv.width=Number(_W); _cv.height=Number(_H);
    const _cx=_cv.getContext('2d');
    _cx.fillStyle='#f7f5f0'; _cx.fillRect(0,0,_cv.width,_cv.height); /* 浅色底(R158 同, 透明底贴工单看不清) */
    _cx.drawImage(_img,0,0);
    try{
      _cv.toBlob(function(blob){
        if(!blob){ _fallbackCopy(); return; }
        const _url=URL.createObjectURL(blob);
        const _a=document.createElement('a');
        _a.href=_url; _a.download='music3_维护守护总览_'+new Date().toISOString().replace(/[:.]/g,'-')+'.png';
        document.body.appendChild(_a); _a.click(); document.body.removeChild(_a);
        setTimeout(function(){ URL.revokeObjectURL(_url); }, 4000);
        if(typeof _toast==='function'){ _toast('已下载维护守护区总览 PNG', 'ok'); }
      },'image/png');
    }catch(_){ _fallbackCopy(); }
    function _fallbackCopy(){
      const _txt='#music3 维护守护区总览 SVG\n'+_svgStr;
      if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制维护守护区总览 SVG（PNG 导出不可用降级）', 'ok'); } }).catch(function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败且复制降级失败', 'bad'); } }); }
      else { if(typeof _toast==='function'){ _toast('PNG 导出失败（canvas 不可用）', 'bad'); } }
    }
  };
  _img.onerror=function(){ if(typeof _toast==='function'){ _toast('PNG 导出失败（SVG 渲染不可用）', 'bad'); } };
  _img.src='data:image/svg+xml;base64,'+_b64;
}
(function(){ const c=$('#mtguardpanelpng'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardPanelPng(); }); } })();
/* 维护守护区总览文本复制(R201): #mtguardpanelcopy 点 -> 读当前态拼总览文本(能力/出口分块+各出口标位+三键状态/四段数据当前值)到剪贴板, 总览可文本留存/贴工单, 与R169/R189/R191/R192/R195/R196复制出口同语言 */
function mtGuardPanelCopy(){
  const _run=(typeof window._mtRunning!=='undefined' && window._mtRunning);
  const _ps=(typeof window._mtPaused!=='undefined' && window._mtPaused);
  const _ab=(typeof window._mtAborted!=='undefined' && window._mtAborted);
  let _h=[]; try{ _h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  let _b=[]; try{ _b=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  const _kl=window._mtKeyLog||{}, _ko=window._mtKeyLogOrder||[];
  const _done=window._mtLiveDoneInfo;
  const _spCan=_run&&!_ab, _esCan=_run&&!_ab, _enCan=!_ab;
  let _lines='#music3 维护守护区总览 · '+new Date().toLocaleString()+'\n';
  _lines+='[三键状态灯 + 触发记录]\n';
  _lines+='Space 暂停/续跑 · '+(_spCan?'可触':'不可触')+(_ps&&_spCan?'（暂停可续跑）':'')+' · '+(_kl.space?('最近 '+_kl.space):'未用过')+'\n';
  _lines+='Esc 取消 · '+(_esCan?'可触':'不可触')+' · '+(_kl.esc?('最近 '+_kl.esc):'未用过')+'\n';
  _lines+='Enter 跳双图 + 聚焦最新轮 · '+(_enCan?'可触':'不可触')+' · '+(_kl.enter?('最近 '+_kl.enter):'未用过')+'\n';
  _lines+=_ko.length?('触发顺序：'+_ko.join('→')):'无触发顺序（未用过）'+'\n';
  _lines+='\n[四段数据源]\n';
  _lines+='双指标逐轮 · '+(_h.length?('近'+_h.length+'次'):'无')+'\n';
  _lines+='状态 · '+(_ab?'已取消':(_ps?'已暂停':(_run?'跑中':'维护完成 / 未跑')))+'\n';
  _lines+='全库完成 · '+(_done?('共'+_done.N+'轮 · 耗时 '+_done.totalDur+'s'):'无（未全库跑完 / 已复位）')+'\n';
  _lines+='键盘流 · '+(_ko.length?('最近'+_ko.length+'次'):'无')+'\n';
  _lines+='\n[复制出口]\n';
  _lines+='⧉ 双指标逐轮明细(R189) · ⧉ 状态详情(R191) · ⧉ 全库完成详情(R192) · ⧉ 键盘流触发记录(R195) · ⧉ 全复制四段(R196)\n';
  _lines+='\n[快照 / PNG 出口]\n';
  _lines+='▣ 四段快照(R197) · ⬇ 快照PNG(R198) · ▤ 总览(R199) · ⬇ 总览PNG(R200) · ⧉ 总览复制(R201)\n';
  _lines+='\n[键盘三操作 + 状态同态]\n';
  _lines+='Space 暂停/续跑(R180) · Esc 取消(R178) · Enter 跳双图(R179) · 徽标暂停同态(R182) · 汇总同态(R183) · 指示条同态(R184)\n';
  _lines+='\n[全库 ∞ + 完成态]\n';
  _lines+='全库∞(R166, N>100000 显∞) · 完成态徽标(R187) · 全库完成详情(R187)\n';
  /* R223 块7: 全折叠域当前态(5键localStorage+5标志window+5折叠钮+7浮层, 能力/出口总览自含全折叠域当前态, 与R222维护守护全记录补全折叠域字段同域) */
  const _flc=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  const _wlc=[window._mtMetFold,window._mtGuardPanelFold,window._mtGuardFoldAll,window._mtGuardFoldCtl,window._mtGuardAllDomain];
  const _b7=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain'];
  const _f7=['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd','mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains'];
  _lines+='\n[全折叠域当前态]\n';
  _lines+='localStorage 5键: _mtMetFold='+_flc[0]+' · _mtGuardPanelFold='+_flc[1]+' · _mtGuardFoldAll='+_flc[2]+' · _mtGuardFoldCtl='+_flc[3]+' · _mtGuardAllDomain='+_flc[4]+'\n';
  _lines+='window 5标志: _mtMetFold='+_wlc[0]+' · _mtGuardPanelFold='+_wlc[1]+' · _mtGuardFoldAll='+_wlc[2]+' · _mtGuardFoldCtl='+_wlc[3]+' · _mtGuardAllDomain='+_wlc[4]+'\n';
  for(let _i=0;_i<5;_i++){ const _bb=document.getElementById(_b7[_i]); _lines+=_b7[_i]+'='+(_bb?_bb.textContent:'无')+'\n'; }
  for(let _i=0;_i<7;_i++){ const _ff=document.getElementById(_f7[_i]); _lines+=_f7[_i]+'='+(_ff?_ff.style.display:'无')+'\n'; }
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制维护守护区总览文本', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ const c=$('#mtguardpanelcopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtGuardPanelCopy(); }); } })();
/* 跑中徽标 hover 展开详情(R167): #mtlivebadge 悬停 -> #mtlivedetail 显 data-dtl(补入拆歌词/封面+累计耗时+总进度), 移开隐; 跑中看细, 与 R166 一行徽标分工(一行扫一眼/hover 看细) */
(function(){
  const b=$('#mtlivebadge'), d=$('#mtlivedetail');
  if(!b || !d) return;
  b.addEventListener('mouseenter', function(){
    const dtl=b.getAttribute('data-dtl'); if(!dtl){ return; }
    d.textContent=dtl; d.style.display='block';
    /* 视口跟随定位(R168): getBoundingClientRect 视口坐标 + 边缘 flip(右溢出贴左翻_底溢出翻上), 徽标靠右/靠底时浮层不溢出视口 */
    const r=b.getBoundingClientRect();
    d.style.position='fixed';
    /* 先放下方, 量浮层宽 */
    d.style.left='0px'; d.style.top='0px';
    const dw=d.offsetWidth, dh=d.offsetHeight;
    /* 水平: 徽标左对齐, 右溢出(左+宽>视口宽-8)则右贴左翻(右对齐到徽标右沿) */
    let lx=r.left, rx=window.innerWidth-8;
    if(r.left+dw>rx){ lx=Math.max(8, r.right-dw); }
    d.style.left=lx+'px';
    /* 垂直: 默认下方(r.bottom+2), 底溢出(下+高>视口高-8)则翻上方(r.top-高-2) */
    let ty=r.bottom+2;
    if(ty+dh>window.innerHeight-8){ ty=Math.max(8, r.top-dh-2); }
    d.style.top=ty+'px';
  });
  b.addEventListener('mouseleave', function(){ d.style.display='none'; d.textContent=''; });
})();
/* 复制当前轮双指标详情(R169): #mtlivedetailcopy 钮 -> navigator.clipboard 复制 #mtlivebadge 的 data-dtl(本轮回+X歌词a/封面b_本轮耗Ys_累计Zs_跑到W/总轮) + toast; 跑中把当前轮双指标实况贴工单/记录维护日志, 与 R129 日志复制同「复制留档」直觉 */
function mtLiveDetailCopy(){
  const b=$('#mtlivebadge'); if(!b) return;
  const dtl=b.getAttribute('data-dtl');
  if(!dtl){ _toast('无当前轮双指标详情可复制（跑维护中才有）', 'bad'); return; }
  const txt='#music3 维护跑中详情 · '+new Date().toISOString().replace('T',' ').slice(0,16)+'\n'+dtl;
  try{
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(txt).then(()=>{ _toast('已复制当前轮双指标详情', 'ok'); }).catch(()=>{ _copyFallback(txt); }); }
    else{ _copyFallback(txt); }
  }catch(e){ _copyFallback(txt); }
}
function _copyFallback(txt){
  const ta=document.createElement('textarea'); ta.value=txt; ta.style.cssText='position:fixed;left:-999px;top:0';
  document.body.appendChild(ta); ta.select();
  try{ document.execCommand('copy'); _toast('已复制当前轮双指标详情', 'ok'); }catch(e){ _toast('复制失败（浏览器未授权剪贴板）', 'bad'); }
  document.body.removeChild(ta);
}
(function(){ const c=$('#mtlivedetailcopy'); if(c){ c.onclick=mtLiveDetailCopy; } })();
/* 双指标区一行汇总(R158): _mtRunHist+_mtRunDelta 都非空 -> #mtmetsum 显「近N次·耗时均值Xs·补入均值+Y/次·合计+Z」(两指标总体一览, 与 R156 #mtpairlbl 单次配对互补: #mtmetsum 看N次汇总_mtpairlbl 看单次) */
function mtMetSumDraw(){
  let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  let d=[]; try{ d=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  const el=$('#mtmetsum'); if(!el) return;
  if(!h.length && !d.length){ el.style.display='none'; const _c0=$('#mtmetsumdetailcopy'); if(_c0){ _c0.style.display='none'; } return; } /* R189 无数据隐复制钮 */
  const n=Math.max(h.length, d.length);
  const hAvg=h.length? (h.reduce((a,c)=>a+c,0)/h.length).toFixed(1) : '—';
  const dAvg=d.length? Math.round(d.reduce((a,c)=>a+c,0)/d.length) : null;
  const dSum=d.length? d.reduce((a,c)=>a+c,0) : null;
  /* 取消/暂停同态(R183): 读 window._mtAborted(Esc 取消)/window._mtPaused(Space 暂停), 取消红前缀「已取消 ·」/暂停黄前缀「已暂停 ·」, 汇总值保留(已跑轮耗时/补入不丢), 续跑/非取消回无前缀; 跑维护状态看汇总也知道挂起/取消, 与 R182 #mtlivebadge 徽标暂停同态双处同步 */
  let _sumPrefix='';
  if(typeof window._mtAborted!=='undefined' && window._mtAborted){ _sumPrefix='已取消 · '; }
  else if(typeof window._mtPaused!=='undefined' && window._mtPaused){ _sumPrefix='已暂停 · '; }
  let txt=_sumPrefix+'近 '+n+' 次 · 耗时均值 '+(h.length?hAvg+'s':'—');
  if(d.length){ txt+=' · 补入均值 +'+dAvg+'/次 · 合计 +'+dSum; }
  el.textContent=txt;
  /* 同态色(R183): 取消红 --bad / 暂停黄 --warn / 续跑·跑中默认色(继承) */
  if(typeof window._mtAborted!=='undefined' && window._mtAborted){ el.style.color='var(--bad)'; }
  else if(typeof window._mtPaused!=='undefined' && window._mtPaused){ el.style.color='var(--warn)'; }
  else{ el.style.color=''; } /* 默认色继承, 续跑/非取消清 */
  el.style.display='inline-block';
  /* R190: #mtmetsumdetailcopy 跟浮层 hover 态(#mtmetsum mouseenter 有数据显/mouseleave 隐), mtMetSumDraw 不控 copy 显隐(非数据态控, 避免常驻显) */
}
/* 双指标汇总 hover 显逐轮明细(R188): #mtmetsum mouseenter -> #mtmetsumdetail 浮层显近N次每轮耗时+补入明细列表(第1次1.2s+8/第2次0.8s+5/…)+均值/合计, 常驻汇总hover看逐轮明细(与R186三键状态灯hover详情同「hover看逐条」语言), 读 _mtRunHist/_mtRunDelta 逐条拼 */
(function(){
  const el=$('#mtmetsum'), d=$('#mtmetsumdetail'), cp=$('#mtmetsumdetailcopy');
  if(!el || !d) return;
  el.addEventListener('mouseenter', function(){
    let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
    let b=[]; try{ b=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
    const n=Math.max(h.length, b.length);
    if(!n){ d.textContent='无跑维护双指标历史'; if(cp){ cp.style.display='none'; } d.style.display='block'; }
    else{
      let _lines='近 '+n+' 次逐轮明细：';
      for(let _k=0; _k<n; _k++){
        const _hv=h.length?h[_k]:'-';
        const _bv=b.length?b[_k]:'-';
        _lines+='\n第 '+(n-1-_k)+' 次 '+(typeof _hv==='number'?_hv+'s':'—')+' · 补入 '+(typeof _bv==='number'?('+'+_bv):'—');
      }
      const _hAvg=h.length?(h.reduce((a,c)=>a+c,0)/h.length).toFixed(1):'—';
      const _bSum=b.length?b.reduce((a,c)=>a+c,0):0;
      _lines+='\n均值 '+_hAvg+'s/次 · 合计 +'+_bSum;
      /* R226 双图区hover明细补全折叠域5键当前态(与mtMetSumDetailCopy同步, 自含全折叠域当前态) */
      const _fl26h=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
      _lines+='\n[全折叠域当前态] localStorage 5键: _mtMetFold='+_fl26h[0]+' · _mtGuardPanelFold='+_fl26h[1]+' · _mtGuardFoldAll='+_fl26h[2]+' · _mtGuardFoldCtl='+_fl26h[3]+' · _mtGuardAllDomain='+_fl26h[4];
      d.innerHTML=_lines.replace(/\n/g,'<br>');
      if(cp){ cp.style.display='inline-block'; } /* R190 copy 跟浮层 hover 态: 有数据 hover 显浮层时 copy 显, 点 copy 复制免移开找常驻位 */
      d.style.display='block';
    }
    /* 视口跟随定位(R168 同 getBoundingClientRect + flip): #mtmetsum 下方浮层, 靠右/靠底不溢出 */
    const r=el.getBoundingClientRect();
    d.style.position='absolute';
    const dw=d.offsetWidth, dh=d.offsetHeight;
    let lx=r.left, rx=window.innerWidth-8;
    if(r.left+dw>rx){ lx=Math.max(8, r.right-dw); }
    d.style.left=lx+'px';
    let ty=r.bottom+2;
    if(ty+dh>window.innerHeight-8){ ty=Math.max(8, r.top-dh-2); }
    d.style.top=ty+'px';
  });
  el.addEventListener('mouseleave', function(){ d.style.display='none'; d.innerHTML=''; if(cp){ cp.style.display='none'; } /* R190 离隐 copy, 跟浮层 hover 态 */ });
})();
/* 双指标逐轮明细复制(R189): #mtmetsumdetailcopy 点 -> 复制「#music3 双指标逐轮明细·<ts>」+逐轮明细文本到剪贴板(navigator.clipboard, _copyFallback降级), 贴工单/记录维护日志, 与R169详情复制同「复制出口」语言 */
function mtMetSumDetailCopy(){
  let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  let b=[]; try{ b=JSON.parse(localStorage.getItem('_mtRunDelta')||'[]'); }catch(_){}
  const n=Math.max(h.length, b.length);
  if(!n){ if(typeof _toast==='function'){ _toast('无双指标逐轮明细可复制', 'bad'); } return; }
  let _lines='#music3 双指标逐轮明细 · '+new Date().toLocaleString()+'\n';
  for(let _k=0; _k<n; _k++){
    const _hv=h.length?h[_k]:'-';
    const _bv=b.length?b[_k]:'-';
    _lines+='第 '+(n-1-_k)+' 次 '+(typeof _hv==='number'?_hv+'s':'—')+' · 补入 '+(typeof _bv==='number'?('+'+_bv):'—')+'\n';
  }
  const _hAvg=h.length?(h.reduce((a,c)=>a+c,0)/h.length).toFixed(1):'—';
  const _bSum=b.length?b.reduce((a,c)=>a+c,0):0;
  _lines+='均值 '+_hAvg+'s/次 · 合计 +'+_bSum;
  /* R226 双图区明细补全折叠域5键当前态(自含全折叠域当前态, 与R222/R223/R224/R225补全折叠域字段同域) */
  const _fl26=[localStorage.getItem('_mtMetFold')||'0',localStorage.getItem('_mtGuardPanelFold')||'0',localStorage.getItem('_mtGuardFoldAll')||'0',localStorage.getItem('_mtGuardFoldCtl')||'0',localStorage.getItem('_mtGuardAllDomain')||'0'];
  _lines+='\n[全折叠域当前态] localStorage 5键: _mtMetFold='+_fl26[0]+' · _mtGuardPanelFold='+_fl26[1]+' · _mtGuardFoldAll='+_fl26[2]+' · _mtGuardFoldCtl='+_fl26[3]+' · _mtGuardAllDomain='+_fl26[4];
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_lines).then(function(){ if(typeof _toast==='function'){ _toast('已复制双指标逐轮明细（'+n+' 次）', 'ok'); } }).catch(function(){ _copyFallback(_lines); });
  } else { _copyFallback(_lines); }
}
(function(){ const c=$('#mtmetsumdetailcopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtMetSumDetailCopy(); }); } })();
/* 维护状态同态指示条(R184): #mtstatebar 顶栏细色带读 window._mtAborted/_mtPaused/_mtRunning 同态显色(取消红--bad/暂停黄--warn/跑中绿--ok/完成灰--line), 跑维护状态看顶栏一条色带全知(三处同态#mtrun/#mtlivebadge/#mtmetsum收敛到一条带), 与 R182/R183 三处同态双处同步对称 */
function mtStateBarDraw(){
  const bar=$('#mtstatebar'); if(!bar) return;
  if(typeof window._mtAborted!=='undefined' && window._mtAborted){ bar.style.background='var(--bad)'; } /* 取消红 */
  else if(typeof window._mtPaused!=='undefined' && window._mtPaused){ bar.style.background='var(--warn)'; } /* 暂停黄 */
  else if(typeof window._mtRunning!=='undefined' && window._mtRunning){ bar.style.background='var(--ok)'; } /* 跑中绿 */
  else{ bar.style.background='var(--line)'; } /* 完成/非跑默认灰 */
}
/* 指示条 hover 显状态详情(R185): #mtstatebar mouseenter -> #mtstatebardtl 浮层显「跑中·第i/N轮·本轮回+X·本轮耗Ys」/「已暂停·…」/「已取消·…」, 读 window._mtLiveInfo(mtRun 每轮 tick 存)+window._mtPaused/_mtAborted 同态, 色带+hover文字双路知状态(扫顶栏色带+hover看详情) */
(function(){
  const bar=$('#mtstatebar'), d=$('#mtstatebardtl'), cp=$('#mtstatebardtlcopy');
  if(!bar || !d) return;
  bar.addEventListener('mouseenter', function(){
    let _txt='维护状态：';
    const li=window._mtLiveInfo;
    if(typeof window._mtAborted!=='undefined' && window._mtAborted){
      _txt='已取消 · '+(li?('第 '+li.i+'/'+(li.N>100000?'∞':li.N)+' 轮 · 本轮回 +'+li.back+' · 本轮耗 '+li.dur+'s'):'跑到断点');
    } else if(typeof window._mtPaused!=='undefined' && window._mtPaused){
      _txt='已暂停 · '+(li?('第 '+li.i+'/'+(li.N>100000?'∞':li.N)+' 轮 · 本轮回 +'+li.back+' · 本轮耗 '+li.dur+'s'):'');
    } else if(typeof window._mtRunning!=='undefined' && window._mtRunning){
      _txt='跑中 · '+(li?('第 '+li.i+'/'+(li.N>100000?'∞':li.N)+' 轮 · 本轮回 +'+li.back+' · 本轮耗 '+li.dur+'s'):'');
    } else {
      _txt='维护完成 / 未跑（灰）';
    }
    /* R228 状态详情补全折叠域5键当前态(自含全折叠域当前态, 与R222/R223/R224/R225/R226/R227补全折叠域字段同域) */
    _txt+='\n[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold='+(localStorage.getItem('_mtGuardPanelFold')||'0')+' · _mtGuardFoldAll='+(localStorage.getItem('_mtGuardFoldAll')||'0')+' · _mtGuardFoldCtl='+(localStorage.getItem('_mtGuardFoldCtl')||'0')+' · _mtGuardAllDomain='+(localStorage.getItem('_mtGuardAllDomain')||'0');
    d.textContent=_txt; d.style.display='block';
    if(cp){ cp.style.display=(typeof window._mtRunning!=='undefined'&&window._mtRunning)||(typeof window._mtPaused!=='undefined'&&window._mtPaused)||(typeof window._mtAborted!=='undefined'&&window._mtAborted)?'inline-block':'none'; } /* R191 copy 跟 hover 态: 跑中/暂停/取消显, 完成/未跑隐 */
    /* 视口跟随定位(R168 同 getBoundingClientRect + flip): #mtstatebar 下方浮层 */
    const r=bar.getBoundingClientRect();
    d.style.left=r.left+'px';
    d.style.top=(r.bottom+2)+'px';
  });
  bar.addEventListener('mouseleave', function(){ d.style.display='none'; d.textContent=''; if(cp){ cp.style.display='none'; } });
})();
/* 维护状态详情复制(R191): #mtstatebardtlcopy 点 -> 复制「#music3 维护状态·<ts>」+状态详情文本(跑中/暂停/取消+第i/N轮+本轮回+X+本轮耗Ys)到剪贴板(navigator.clipboard,_copyFallback降级), 贴工单/记录维护日志, 与R169详情复制/R189逐轮明细复制同「复制出口」语言 */
function mtStateBarCopy(){
  const li=window._mtLiveInfo;
  let _st='维护完成 / 未跑';
  if(typeof window._mtAborted!=='undefined' && window._mtAborted){ _st='已取消 · '+(li?('第 '+li.i+'/'+(li.N>100000?'∞':li.N)+' 轮 · 本轮回 +'+li.back+' · 本轮耗 '+li.dur+'s'):'跑到断点'); }
  else if(typeof window._mtPaused!=='undefined' && window._mtPaused){ _st='已暂停 · '+(li?('第 '+li.i+'/'+(li.N>100000?'∞':li.N)+' 轮 · 本轮回 +'+li.back+' · 本轮耗 '+li.dur+'s'):''); }
  else if(typeof window._mtRunning!=='undefined' && window._mtRunning){ _st='跑中 · '+(li?('第 '+li.i+'/'+(li.N>100000?'∞':li.N)+' 轮 · 本轮回 +'+li.back+' · 本轮耗 '+li.dur+'s'):''); }
  let _txt='#music3 维护状态 · '+new Date().toLocaleString()+'\n'+_st;
  /* R228 状态详情复制补全折叠域5键当前态(自含全折叠域当前态, 与hover浮层同步) */
  _txt+='\n[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold='+(localStorage.getItem('_mtGuardPanelFold')||'0')+' · _mtGuardFoldAll='+(localStorage.getItem('_mtGuardFoldAll')||'0')+' · _mtGuardFoldCtl='+(localStorage.getItem('_mtGuardFoldCtl')||'0')+' · _mtGuardAllDomain='+(localStorage.getItem('_mtGuardAllDomain')||'0');
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(_txt).then(function(){ if(typeof _toast==='function'){ _toast('已复制维护状态详情', 'ok'); } }).catch(function(){ _copyFallback(_txt); });
  } else { _copyFallback(_txt); }
}
(function(){ const c=$('#mtstatebardtlcopy'); if(c){ c.addEventListener('click', function(e){ e.stopPropagation(); mtStateBarCopy(); }); } })();
/* 清空跑维护历史: 清 localStorage._mtRunHist + mtRunHistDraw 重画(空->#mthistspark 隐) + toast; 看趋势久了重计基线(与 R119 自动刷持久化「可清可留」同「记状态可管」直觉) */
function mtRunHistClear(){
  try{ localStorage.removeItem('_mtRunHist'); }catch(e){}
  mtRunHistDraw();
  if(typeof mtMetSumDraw==='function'){ mtMetSumDraw(); }
  _toast('跑维护耗时历史已清空 · 重新计基线', 'ok');
}
/* 导出跑维护历史 CSV: _mtRunHist 近10次耗时(序号/秒/导出时间) -> Blob 下载; 换设备带历史走/存档复盘(与 R113 日志导出同「导出留档」直觉) */
function mtRunHistExport(){
  let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  if(!h.length){ _toast('无跑维护历史可导出（先跑一次维护）', 'bad'); return; }
  const ts=new Date().toISOString().replace('T',' ').slice(0,19);
  const lines=['#music3 跑维护耗时历史（近 '+h.length+' 次 · 导出 '+ts+'）','序号,耗时(s)'];
  h.forEach((v,i)=>{ lines.push((i+1)+','+v); });
  const csv='\ufeff'+lines.join('\n');
  const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});
  const url=URL.createObjectURL(blob);
  const a=document.createElement('a');
  a.href=url; a.download='music3_run_hist_'+Date.now()+'.csv';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  setTimeout(()=>URL.revokeObjectURL(url), 3000);
  _toast('已导出跑维护历史 '+h.length+' 次（CSV）', 'ok');
}
/* 折线快照存 PNG: 离屏 canvas 重绘 #mthistspark 折线区(背景+折线+均值标签) -> download; 看趋势截图分享(与 R147 CSV 导出互补: CSV 走数据 PNG 走图, 同「导出留档」) */
function mtRunHistPng(){
  let h=[]; try{ h=JSON.parse(localStorage.getItem('_mtRunHist')||'[]'); }catch(_){}
  if(!h.length){ _toast('无跑维护历史可快照（先跑一次维护）', 'bad'); return; }
  const W=480, H=140, pad=24, padTop=28, padBot=22, padL=12, padR=12;
  const c=document.createElement('canvas'); c.width=W; c.height=H;
  const g=c.getContext('2d');
  g.fillStyle='#fff'; g.fillRect(0,0,W,H);
  g.strokeStyle='#e4e4ea'; g.lineWidth=1;
  g.font='12px ui-sans-serif,system-ui,sans-serif';
  const mx=Math.max.apply(null,h), mn=Math.min.apply(null,h), rng=Math.max(1e-3, mx-mn);
  const avg=Math.round((h.reduce((a,v)=>a+v,0)/h.length)*10)/10;
  const iw=W-padL-padR, ih=H-padTop-padBot;
  const X=i=> h.length>1? padL+i/(h.length-1)*iw : padL+iw/2;
  const Y=v=> padTop+(1-(v-mn)/rng)*ih;
  /* 网格线 4 条 */
  g.strokeStyle='#f0f0f2';
  for(let k=0;k<=3;k++){ const gy=padTop+ih*k/3; g.beginPath(); g.moveTo(padL,gy); g.lineTo(W-padR,gy); g.stroke(); }
  /* 面积 */
  g.beginPath(); g.moveTo(X(0),Y(h[0])); for(let i=1;i<h.length;i++){ g.lineTo(X(i),Y(h[i])); }
  g.lineTo(X(h.length-1),H-padBot); g.lineTo(X(0),H-padBot); g.closePath();
  g.fillStyle='rgba(196,56,31,0.12)'; g.fill();
  /* 折线 */
  g.beginPath(); g.moveTo(X(0),Y(h[0])); for(let i=1;i<h.length;i++){ g.lineTo(X(i),Y(h[i])); }
  g.strokeStyle='#c4381f'; g.lineWidth=2; g.lineJoin='round'; g.stroke();
  /* 点 */
  h.forEach((v,i)=>{ g.beginPath(); g.arc(X(i),Y(v),3,0,Math.PI*2); g.fillStyle='#c4381f'; g.fill(); });
  /* 标题 + 均值 + 时间戳 */
  g.fillStyle='#5a5a5f'; g.font='13px ui-sans-serif,system-ui,sans-serif';
  g.fillText('跑维护耗时 · 近 '+h.length+' 次 · 均值 '+avg+'s', padL, 18);
  g.fillStyle='#9a9aa0'; g.font='10px ui-sans-serif,system-ui,sans-serif';
  g.fillText(new Date().toISOString().replace('T',' ').slice(0,16)+' 时', padL, H-8);
  g.fillText('Y 轴 '+(mn).toFixed(1)+'~'+(mx).toFixed(1)+'s', W-padR-g.measureText('Y 轴 '+mn.toFixed(1)+'~'+mx.toFixed(1)+'s').width, H-8);
  const url=c.toDataURL('image/png');
  const a=document.createElement('a'); a.href=url; a.download='music3_run_hist_'+Date.now()+'.png';
  document.body.appendChild(a); a.click(); document.body.removeChild(a);
  _toast('已导出折线快照（PNG）', 'ok');
}
/* 导入跑维护历史 CSV: 文件选择框选 R147 导的 CSV -> 解析数据行(序号,耗时) -> 重填 localStorage._mtRunHist(末10条) + mtRunHistDraw + toast; 换设备/清历史后把旧 CSV 导回来(与 R147 导出对称的「导入还原」闭环) */
function mtRunHistImport(){
  const inp=document.createElement('input');
  inp.type='file'; inp.accept='.csv,text/csv';
  inp.onchange=function(ev){
    const f=ev.target.files[0]; if(!f) return;
    const rd=new FileReader();
    rd.onload=function(){
      try{
        const txt=String(rd.result||'').replace(/^\ufeff/,'');
        const rows=txt.split(/\r?\n/).filter(x=>x && x.indexOf('#')!==0);
        /* 数据行: 序号,耗时(s) (跳表头 序号/耗时); 取末10条耗时列 */
        const vals=[];
        rows.forEach(r=>{
          const c=r.split(',');
          const t=parseFloat(c[1]);
          if(c.length>=2 && !isNaN(t) && t>0){ vals.push(t); }
        });
        if(!vals.length){ _toast('CSV 无有效耗时行（需 序号,耗时(s)）', 'bad'); return; }
        const keep=vals.slice(-10);
        localStorage.setItem('_mtRunHist', JSON.stringify(keep));
        mtRunHistDraw();
        _toast('已导入跑维护历史 '+keep.length+' 次（CSV）', 'ok');
      }catch(e){ _toast('导入失败: '+e, 'bad'); }
    };
    rd.readAsText(f, 'utf-8');
  };
  inp.click();
}
/* 重置基线: 清 _mtRunHist + 记 _mtRunHistBase(当前时间戳, 0s 起算点) + mtRunHistDraw 重画(空->#mthistspark 隐) + toast; 趋势重定 0 点(清历史+记基线, 看距基线多久补X), 与 R146 清历史/R149 导入「基线可管」闭环 */
function mtRunHistReset(){
  try{ localStorage.removeItem('_mtRunHist'); }catch(e){}
  try{ localStorage.setItem('_mtRunHistBase', String(Date.now())); }catch(e){}
  mtRunHistDraw();
  _toast('已重置基线 · 下次跑维护从 0s 起算（基线 '+new Date().toISOString().replace('T',' ').slice(0,16)+'）', 'ok');
}
(function(){ const c=$('#mthistclear'); if(c){ c.onclick=mtRunHistClear; } const x=$('#mthistexport'); if(x){ x.onclick=mtRunHistExport; } const pg=$('#mthistpng'); if(pg){ pg.onclick=mtRunHistPng; } const im=$('#mthistimport'); if(im){ im.onclick=mtRunHistImport; } const rs=$('#mthistreset'); if(rs){ rs.onclick=mtRunHistReset; } })();
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
document.addEventListener('input', e=>{ if(e.target && e.target.id==='mtlogfilter'){ try{ localStorage.setItem('_mtLogF', e.target.value||''); }catch(x){} if($('#mtresult .joblog')) mtLogDraw().catch(()=>{}); } });
/* 日志过滤词持久化: 载入按 localStorage._mtLogF 填回 #mtlogfilter(重开维护 tab 恢复上次过滤, 扫日志不用重设) */
(function(){ try{
  const _lf=localStorage.getItem('_mtLogF');
  const apply=()=>{ const f=document.querySelector('#mtlogfilter'); if(f && _lf){ f.value=_lf; } };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',()=>{ apply(); if($('#mtresult .joblog')) mtLogDraw().catch(()=>{}); });
  else { apply(); }
}catch(e){} })();
/* 日志预设 chip: 一键填过滤框(歌词/封面/异常/全部) + 重绘 */
document.querySelectorAll('[data-lf]').forEach(c=>{
  c.onclick=()=>{ const f=document.querySelector('#mtlogfilter'); if(!f) return; f.value=c.dataset.lf;
    if($('#mtresult .joblog')) mtLogDraw().catch(()=>{}); };
});
/* sparkline 末点值标开关: 切 body._nosplabel(末点值标全隐, 窄屏免挤), 记 localStorage._mtSparkLabel(0=关 1=开, 缺省=开) */
function mtSparkLabelToggle(){
  const off=document.body.classList.toggle('_nosplabel');
  localStorage.setItem('_mtSparkLabel', off?'0':'1');
  const b=$('#mtspklabel'); if(b){ b.textContent='末点值标: '+(off?'关':'开'); }
}
/* 载入: 按 localStorage._mtSparkLabel 应用 body._nosplabel + 按钮初值 */
(function(){ try{
  const off=localStorage.getItem('_mtSparkLabel')==='0';
  if(off) document.body.classList.add('_nosplabel');
  const apply=()=>{ const b=$('#mtspklabel'); if(!b) return; const curOff=document.body.classList.contains('_nosplabel'); b.textContent='末点值标: '+(curOff?'关':'开'); };
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',apply); else apply();
}catch(e){} })();
/* 11 卡窄屏折叠: #mtcards 点切 .fold(前5卡/全11卡); 默认窄屏(clientWidth<1100)+未展开(localStorage._mtCards!=1)折, 宽屏全显 */
function mtCardsFold(){
  const g=$('#mtcardgrid'); if(!g) return;
  const fold=g.classList.toggle('fold');
  localStorage.setItem('_mtCards', fold?'0':'1');
  const b=$('#mtcards'); if(b){ b.innerHTML=(fold?'▾ 展开全部卡片':'▴ 收起卡片'); }
}
/* sparkline hover 数值跟随: #mtspark 容器 mousemove, 按 x 比例定位最近折线点, 亮 hover 点 + 标签(该点值); 移开隐 */
(function(){ try{
  document.addEventListener('mousemove', e=>{
    const sp=e.target.closest ? e.target.closest('.mtspark') : null;
    if(!sp){ return; }
    /* hover 点 + 标签: 每卡各一(mtspark-hover/-lbl), 亮当前卡的 */
    const dot=sp.querySelector('.mtspark-hover'), lbl=sp.querySelector('.mtspark-hoverlbl');
    const tr=JSON.parse(decodeURIComponent(sp.getAttribute('data-tr')||'{}')).t||[];
    if(!tr.length||!dot||!lbl) return;
    const r=sp.getBoundingClientRect();
    const x=Math.max(0,Math.min(r.width, e.clientX-r.left));
    const w=r.width;
    const idx=Math.round((x/w)*(tr.length-1));
    const max=Math.max.apply(null,tr), min=Math.min.apply(null,tr), rng=(max-min)||1;
    const px=(idx/(tr.length-1))*100;
    const py=100-((tr[idx]-min)/rng)*100; /* sparkline 高 22px 内 y% */
    dot.style.left=px+'%'; dot.style.top=py+'%'; /* py = 折线内 y 百分比(顶0 底100), 容器高 ~22px */
    dot.style.display='block';
    lbl.style.left=px+'%'; lbl.style.top='0%';
    lbl.textContent=tr[idx];
    lbl.style.display='block';
  }, true);
  document.addEventListener('mouseout', e=>{
    const sp=e.target.closest ? e.target.closest('.mtspark') : null;
    if(!sp) return;
    const dot=sp.querySelector('.mtspark-hover'), lbl=sp.querySelector('.mtspark-hoverlbl');
    if(dot) dot.style.display='none';
    if(lbl) lbl.style.display='none';
  }, true);
}catch(e){} })();
/* 统一点控: mtStat 铺完 #mtcardgrid + 后 6 卡后调用, 按 localStorage._mtCards + 窄屏决定 .fold(宽屏全显/记1全显; 记0且窄才折) */
function applyMtFold(){
  const g=$('#mtcardgrid'); if(!g) return;
  const narrow=window.innerWidth<1100;
  const wantFold=narrow&&localStorage.getItem('_mtCards')!=='1';
  g.classList.toggle('fold', wantFold);
  const b=$('#mtcards');
  if(b){ b.innerHTML=wantFold?'▾ 展开全部卡片':'▴ 收起卡片'; b.style.display=narrow?'':'none'; }
}
/* 载入: resize 时切窄宽(宽屏全显不折, 窄屏按 _mtCards 恢复) */
(function(){ try{
  window.addEventListener('resize',()=>{ const b=$('#mtcards'); if(!b) return; const g=$('#mtcardgrid'); if(g) g.classList.remove('fold'); b.style.display=(window.innerWidth<1100)?'':'none'; });
}catch(e){} })();
$('#mtreset').onclick = async()=>{
  let cur='未知';
  try{ const st=await (await fetch('/api/maintain')).json(); cur=(st.cursor&&st.cursor._all)?st.cursor._all.split('\\').slice(-2).join('\\'):'(无)'; }catch(e){}
  if(!confirm(`重置断点游标？\n\n当前断点: ${cur}\n重置后果: 下次「跑维护」从头扫全库(已补的不会重补, 只重扫一遍 5188 首定位)。\n\n确认重置？`)) return;
  await fetch('/api/maintain?act=reset');
  setMsg($('#mtmsg'), '断点已重置', 'ok');
  _toast('断点已重置 · 下次跑维护从头扫全库','ok');
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
