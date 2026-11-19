# music3 · 三源音乐下载工具

B站 / 网易云 / QQ音乐（含酷我、千千、咪咕）统一搜索、智能打分、去重下载。落盘对齐 `D:\音乐`。

> **作者**：最中幻想　|　**微信**：andyloveanny
>
> 这个工具从第一行代码到 47 条踩坑记录都是实打实趟出来的。如果你觉得有用，
> 到 GitHub 上点个 ⭐ Star 支持一下——这是最直接的鼓励，也能让更多人看到它。
>
> 有问题、想要新功能、或者只是想聊聊，加微信 `andyloveanny`。

[![Star](https://img.shields.io/badge/⭐_点个_Star-支持一下-yellow)](https://github.com/qingshanjiluo/music3)

## 桌面启动器（推荐入口）

双击桌面 **「music3 音乐工具」** 快捷方式，或 `启动器.bat`：

```
==========================================================
  music3 · 三源音乐工具    B站 / 网易云 / QQ音乐
==========================================================
  服务: ● 运行中  http://127.0.0.1:8420  _归档_封存 4708 / 投稿 468
----------------------------------------------------------
  [服务]
    1) 启动 Web 服务              2) 打开 Web 界面
    3) 停止服务                   4) 查看状态
  [设置]
    5) 修改配置                   c) 环境自检
  [干活]
    6) 搜索与下载                 7) 批量补全（歌词/封面）
    8) 库健康检查                 9) 维护守护
  [工具]
    e) 导出歌单/索引              d) 打开目录
    l) 运行日志                   h) 使用说明 / 学习
----------------------------------------------------------
  q) 退出
```

14 项功能，全部实测通过：

| 键 | 功能 | 实测 |
|---|---|---|
| 1 | 启动 Web 服务（自动等就绪，20s 超时） | ✅ 端口起来，回显曲库数 |
| 2 | 打开 Web 界面（未启动会先拉起） | ✅ |
| 3 | 停止服务（按命令行匹配进程，不误杀） | ✅ |
| 4 | 查看状态（服务/曲库/维护/缓存四段） | ✅ 投稿 468 / 归档 4708 / 5176 首 |
| 5 | 修改配置（18 项可视化编辑，自动备份 `.bak`） | ✅ 改完读回一致 |
| 6 | 搜索与下载（三源并发，只走快源） | ✅ **3.1s 出 26 条**，下载 30.6s |
| 7 | 批量补全歌词/封面 | ✅ |
| 8 | 库健康检查（快速/深度） | ✅ 2000 首 1.0s，健康分 84.8 |
| 9 | 维护守护（1轮/5轮/到完成/看日志） | ✅ |
| e | 导出 m3u8 / CSV / 全库索引 | ✅ 426.7 KB m3u8 |
| d | 打开音乐/程序/缓存目录 | ✅ |
| l | 运行日志（最近 40 行） | ✅ |
| c | 环境自检（14 项依赖/路径/工具/端口） | ✅ 全部通过 |
| h | 使用说明 / 学习（12 条 + 打开 README） | ✅ |

**关键设计**：
- 启动失败时给诊断（python 路径 / run.py 是否存在 / 端口被谁占），不是干等 20 秒报一句"失败"
- 检测到残留进程（占端口但不响应）时先问是否清掉
- 搜索默认只走 `qq / netease / bilibili`——酷我/千千/咪咕 常年 503，会把 3 秒拖成 18 秒
- 中文按东亚双宽计算列宽，两列菜单不会错位

## 快速开始

```powershell
cd F:\tools\music3

python -X utf8 run.py stat                          # 曲库统计
python -X utf8 run.py ls                            # 列分类
python -X utf8 run.py ls "投稿\QQ音乐"              # 列目录曲目
python -X utf8 run.py find "稻香"                   # 模糊查找

python -X utf8 run.py search "晴天 周杰伦"          # 三源搜索
python -X utf8 run.py search "晴天" -s qq,netease --no-bili
python -X utf8 run.py get "晴天 周杰伦"             # 搜+下第一首
python -X utf8 run.py get "洛天依" -s bilibili -n 3 # B站下三首
python -X utf8 run.py dl BV1zs411S7sz               # 按BV号直下

python -X utf8 run.py queue want.txt -n 1 -w 3      # 批量并发队列
python -X utf8 run.py artist "周杰伦" -t 40         # 歌手全量
python -X utf8 run.py dup                            # 查重（只报告）
python -X utf8 run.py rm "稻香"                      # 删曲（只预览）

python -X utf8 run.py web                            # Web 界面 + API
```

双击 `启动Web界面.bat` 也行。

## 命令表

| 命令 | 作用 |
|---|---|
| `search` | 跨源搜索，打分排序 |
| `get` | 搜索并下载前 N 首 |
| `dl` | 按 BV 号直下 B 站 |
| `batch` | 逐条下载（串行） |
| `queue` | 批量并发队列（多线程+重试+多源兜底） |
| `resume` | **续跑上次中断的批量任务** |
| `pending` | **查看未完成/失败的批量任务** |
| `pending-clear` | 清空任务清单 |
| `lyric` | **批量补歌词**（无内嵌歌词时从网易云/QQ 拉，`-w` 写回 ID3） |
| `lyric-cache` | 歌词缓存管理（`--clear`） |
| `export` | **导出**（`-t m3u8/json/csv/index`，`-p` 只导播放列表，`-o` 指定输出） |
| `health` | **库健康检查**（`-d` 读 ID3，`--detail` 列明细） |
| `cover` | **批量补封面**（无内嵌封面时从网易云/QQ 拉，默认写回 ID3） |
| `cover-cache` | 封面缓存管理（`--clear`） |
| `maintain` | **维护守护**（每轮补歌词/封面/清临时，断点续传 + 日志落盘） |
| `fixname` | 修文件名非法字符（默认预览，`--yes` 真改） |
| `artist` | 歌手全量抓取（可带 UP 主 mid） |
| `stat` | 按分类统计曲数 |
| `ls` | 列分类 / 列目录曲目 |
| `find` | 关键词模糊查找 |
| `rm` | 删曲（默认预览，`--yes` 才真删） |
| `dup` | 重复组 + 临时残留检测（`--clean` 真删） |
| `web` | Web 界面与 JSON API |

## Web / API

启动后开 <http://127.0.0.1:8420>，六个标签页：搜索 / 曲库 / 历史 / 统计 / 批量 / 清理。

| 标签 | 功能 |
|---|---|
| 搜索 | 三源搜索、打分表格、单曲下载 |
| 曲库 | 分类片切换、封面网格、**点击卡片直接试听**、网格/列表双视图 |
| 历史 | 播放记录（标题/歌手/时间），一键重播，可清空 |
| 统计 | 总播放/累计时长/曲目排行/歌手排行，播满 30 秒才计一次 |
| 批量 | 多行关键词 + 并发/数量设置 + 实时进度条与日志 |
| 清理 | 重复组扫描（按名/按内容） |

| 端点 | 说明 |
|---|---|
| `GET /` | 可视化界面 |
| `GET /api/search?q=晴天&sources=qq,netease&limit=15` | 搜索结果 |
| `GET /api/get?q=晴天 周杰伦&n=1&sources=qq` | 搜+下第 n 首 |
| `GET /api/stat` | 曲库统计 |
| `GET /api/ls` | 列出根下分类 |
| `GET /api/ls?sub=投稿\QQ音乐&limit=200` | 列子目录曲目 |
| `GET /api/find?q=稻香&limit=50` | 模糊查找 |
| `GET /api/dup?by=name&top=10` | 查重（报告） |
| `GET /api/stream?rel=<相对路径>` | **试听**（支持 Range，可拖进度条） |
| `GET /api/cover?rel=<相对路径>` | 内嵌封面 JPEG |
| `GET /api/tags?rel=<相对路径>` | 标题/歌手/时长/码率/歌词 |
| `GET /api/history` | **播放历史**（`?add=rel&title=&artists=` 追加，`?clear=1` 清空，`?remove=rel` 删单条） |
| `GET /api/maintain` | **维护守护**（`?act=tick&batch=20` / `?act=reset` / `?act=log&n=80`） |
| `GET /api/coverfill` | **封面补全**（`?rel=&write=1` 单首补，`?clear=1` 清缓存） |
| `GET /api/health` | **库健康检查**（`?deep=1` 读 ID3，`?sub=&limit=`） |
| `GET /api/export` | **导出**（`?fmt=m3u8/csv/json/index&src=lib/playlist&sub=&fast=1`） |
| `GET /api/stats` | **播放统计**（总览 / `?act=top&by=count|seconds` / `?act=artists` / `?act=record` / `?act=clear`） |
| `GET /api/lyric` | **歌词补全**（`?rel=` 取/补歌词，`?clear=1` 清缓存） |
| `GET /api/playlist` | **播放列表**（`?act=add/set/move/remove/clear/current`，支持拖拽排序） |
| `GET /api/cache` | **封面缓存统计**（`?clear=1` 清空） |
| `GET /api/file?rel=<相对路径>` | 下载单曲到浏览器（附件头） |
| `POST /api/queue` `{"keywords":[...],"n":1,"workers":3}` | **批量下载**（返回 job_id） |
| `GET /api/jobs` | 任务列表 |
| `GET /api/job?id=<job_id>` | 任务快照（含日志） |
| `GET /api/job/sse?id=<job_id>` | **SSE 实时进度流** |
| `GET /api/job/cancel?id=<job_id>` | 取消任务 |
| `POST /api/batch` | 旧接口，等同 `/api/queue` |

AI / 脚本直接调 `/api/search` + `/api/get` 即可，无需界面。
需要实时进度就 `POST /api/queue` 拿 `job_id`，再 `GET /api/job/sse?id=...` 订阅。

### Web 界面

五个标签页：

| 标签 | 功能 |
|---|---|
| 搜索 | 三源搜索、打分表格、单曲下载 |
| 曲库 | 分类片切换、封面网格、**点击卡片直接试听** |
| **历史** | **播放记录（标题/歌手/时间），一键重播，可清空** |
| **统计** | **总播放/累计时长/曲目排行/歌手排行，播满 30 秒才计一次** |
| 批量 | 多行关键词 + 并发/数量设置 + **实时进度条与日志** |
| 清理 | 重复组扫描（按名/按内容） |

**底部常驻播放器**：封面缩略图 + 标题 + 音量条/歌词/列表/上一首/播放暂停/下一首/关闭 + 可点击进度条 + 自动连播 + **实时频谱波形**（Web Audio `AnalyserNode`，64 根柱状，暂停时降为静态低幅波形）。

**歌词全屏面板**（「词」按钮或 `L` 键）：解析内嵌 LRC，随播放时间高亮当前行（二分查找定位，`+0.25s` 视觉提前量），上下行淡显，自动平滑滚动居中，点任意行可跳转。

**播放列表抽屉**（☰ 按钮）：从右侧滑出，可**拖拽排序**（HTML5 drag & drop）、点播、单条移除、清空。落盘 `_cache/playlist.json`，切页面不丢。

**曲库两种视图**：网格（封面大图）/ 列表（紧凑带封面缩略图），选择记在 `localStorage.m3_view`。**分批渲染**：每批 60 条 + `IntersectionObserver` 滚到底自动续批，500 首不再卡。

**封面磁盘缓存**：从 mp3 解 APIC 很慢（30~190ms），缓存到 `_cache/covers/<md5>.jpg` 后 2~24ms。用「路径+大小+mtime」做 key，文件换了自动失效；没封面的也记 `.none` 标记，避免反复解 ID3。

**PWA 可安装**：`manifest.json` + `sw.js`。页面/静态资源走 stale-while-revalidate，音频流走 network-first，其他 API 不缓存。手机浏览器「添加到主屏幕」后即为独立 App，离线也能打开界面并重播已缓存的封面。

**8 段均衡器**（「EQ」按钮或 `E` 键）：60/170/350/1k/3.5k/5k/10k/16k Hz，`BiquadFilterNode` peaking 串联在 `MediaElementSource → Analyser → destination` 之间。6 个预设（平直/流行/摇滚/人声/重低音/高音），拖动即生效，配置存 `localStorage.m3_eq`。旁通开关保留配置只归零。

### 快捷键

| 键 | 动作 |
|---|---|
| `空格` | 播放 / 暂停 |
| `←` `→` | 后退 / 前进 5 秒 |
| `↑` `↓` | 音量 +5 / -5（记忆在 `localStorage.m3_vol`） |
| `L` | 打开歌词面板 |
| `E` | 打开均衡器 |
| `[` `]` | 播放速度 −/+（0.5→2.0x） |
| `N` / `P` | 下一首 / 上一首 |
| `Esc` | 关闭歌词 / 均衡器 / 播放列表面板 |

输入框内不拦截快捷键。

## 目录结构

```
F:\tools\music3\
├── run.py              统一入口（23 条命令）
├── launcher.py         桌面启动器（14 项菜单功能）
├── 启动器.bat          启动器包装（双击入口）
├── 启动Web界面.bat     直接起 Web（旧入口，仍可用）
├── music3.ico          多尺寸图标（16/32/48/64/128/256）
├── config.json         全部可调参数
├── README.md
├── want.txt            批量清单模板
├── web\                PWA 静态资源
│   ├── manifest.json
│   ├── sw.js
│   └── icon.svg
└── src\
    ├── config.py       配置加载（json + 环境变量）
    ├── models.py       Track 模型 + 繁简归一 + 文件名安全化
    ├── src_bili.py     B站适配器（**官方 API 搜索** + yt-dlp 下载）
    ├── src_qq.py       QQ 快速通道（搜索/取链分离 + 死链校验）
    ├── src_netease.py  网易云快速通道（搜索/取链分离 + 试听识别）
    ├── src_musicdl.py  酷我/千千/咪咕（musicdl 小众源）
    ├── router.py       跨源并发搜索 + 打分 + 去重
    ├── downloader.py   直链下载 + ffmpeg 转 mp3 + ffprobe 校验 + 现取直链
    ├── tagger.py       ID3 标签 + 封面 + 歌词内嵌
    ├── tagreader.py    读已有 mp3 的标签/封面/歌词
    ├── stream.py       音频流（Range）+ 封面字节 + 安全路径
    ├── covercache.py   **封面磁盘缓存 + 播放历史**
    ├── playlist.py     **播放列表（拖拽排序 + 持久化）**
    ├── lyricfill.py    **歌词补全（网易云/QQ 搜索 + 占位过滤）**
    ├── stats.py        **播放统计（次数/时长/歌手排行）**
    ├── export.py       **导出 m3u8/CSV/JSON/全库索引**
    ├── health.py       **库健康检查（7项指标 + 打分 + 修名）**
    ├── coverfill.py    **封面补全（网易云/QQ 搜索 + 写回 APIC）**
    ├── maintain.py     **维护守护（断点续传 + 日志轮转）**
    ├── library.py      曲库扫描 / 查重 / 落盘路径
    ├── browse.py       曲库浏览 / 模糊查找 / 删除
    ├── dedup.py        重复组检测（保留优先级）
    ├── queue.py        并发队列 + 重试 + 中断恢复
    ├── persist.py      **任务清单落盘（原子写）**
    ├── jobs.py         任务中心（SSE 进度）
    ├── cache.py        搜索缓存（30min TTL）
    ├── artist.py       歌手全量 / UP 主投稿抓取
    ├── cli.py          命令行
    └── web.py          Web 界面 + JSON API
```

落盘：`D:\音乐\投稿\{B站|网易云|QQ音乐|酷我|千千|咪咕}\<歌手> - <歌名>.mp3`

## 踩过的坑（全部已修）

**1. B站 Hi-Res 轨必须绕过。** 默认音轨 `100026` 是无损，本机 ffmpeg 转 mp3 会失败并留 0 字节文件。强制：
```python
AUDIO_FMT = "30216/30280/30232/bestaudio"   # 30216=256k AAC
```

**2. B站 412 风控。** 短时连发请求被拒（`HTTP Error 412`）。搜索内置 4 次退避重试（20/40/60s）。

**3. yt-dlp 中文输出乱码。** Windows 默认 cp936 输出，Python 按 utf-8 读会变乱码并写进文件名。必须加 `--encoding utf-8`。

**4. 时长校验不能用文件大小。** 官方短曲 14s/22s 只有 280KB，`>1MB` 会误杀。改用 ffprobe 读时长，窗口 8~1500s、大小下限 150KB。

**5. 繁简/日文汉字归一。** 曲库混用「千本樱 / 千本櫻 / 千本桜」，查重与打分前统一映射到简体。

**6. musicdl 源名必须是类名。** `'netease'` 会 `AssertionError`，要写 `'NeteaseMusicClient'`。字段是 `song_name`/`singers`/`identifier`/`file_size_bytes`/`duration_s`，`download_url` 是 dict 取 `['download_url']` 和 `['ext']`。

**7. `init_music_clients_cfg` 必须按源类名嵌套。** 结构是 `{源类名: {键: 值}}`，给顶层键会被静默忽略（musicdl 只做 `update(init_cfg.get(源类名, {}))`）。

**8. 不要用 dup2 重定向 fd2 静音 rich。** rich 的 Console 持有 fd 句柄，来回 dup2 会让它失效。进度条噪声只能忍，或用 `disable_print: True`。

**9. musicdl 会不规则返回空。** 同 IP 连续搜索触发服务端限流，表现是 `n=0,0,20` 这种不规则结果，不是代码 bug。已在 `src_musicdl.search` 内置空结果退避重试，`queue` 再加多源兜底。

**10. 不走系统代理。** 所有 HTTP 与子进程都清空 `HTTP_PROXY/HTTPS_PROXY/ALL_PROXY`，`requests.Session.trust_env = False`。

**11. 去重不能盲删。** `投稿` 是在用曲库，`_归档_封存` 是存档。`dedup._keep_rank()` 强制投稿文件优先保留，避免把正在用的版本删掉。

**12. 绝不要用守护线程 + `join(timeout)` 做硬超时。** 超时后线程仍活着并持有 rich 的 Live 单例，下一次调用必然抛 `LiveError: Only one live display may be active at once`。实测把 60s 硬超时加进去后，musicdl 从「100s 能搜到」变成「永远搜不到」。`_call_timeout` 现在直接 `return fn()`，老实等。

**13. 也不要 patch `rich.live.Live` 成空壳。** 实测换成 `_NullLive` 后 musicdl 内部流程卡死（缺 `console` 属性直接 AttributeError，补上后又要 `add_task`/`refresh`，补全后仍超时）。进度条噪声的代价远小于功能不可用。

**14. musicdl 搜索本身就要 2-4 分钟，不是 bug。** QQ 源每条结果都要单独请求 vkey，`search_size_per_source=8` 实测 223s，`=20` 要 378s。

**15. 已解决它：走快速通道。** QQ 见 `src/src_qq.py`，网易云见 `src/src_netease.py`——搜索与取直链分离。搜索只打元数据接口（1 秒），直链只在下载时按 id 现取。实测 QQ 223s → 1.2s，网易云 154s → 1.0s。**不要再退回 musicdl 搜 QQ/网易云。**

**16. `api.vkeys.cn` 的新旧端点不要混。** `/v2/music/tencent` 返回 `code:500`；正确是 `/music/tencent/song/link`，质量参数是数字 ID（14=PREMIUM_MASTER_2_0, 11=HI_RES, 10=SQ_LOSSLESS, 8=HQ, 4=STANDARD），不是 `"320"`/`"flac"` 字符串。

**17. 改完代码必须彻底重启 Web，还要清 `.pyc`。** 旧进程不会热加载模块，`__pycache__` 里的旧字节码也不会自动失效。表现为「代码改了但行为没变」。正确顺序：
```powershell
Get-ChildItem -Recurse src\__pycache__ -Filter *.pyc | Remove-Item -Force
Get-NetTCPConnection -LocalPort 8420 | % { Stop-Process -Id $_.OwningProcess -Force }
Start-Sleep 3
# 确认端口空了再启动
Start-Process python -ArgumentList "-X","utf8","run.py","web"
```

**18. 网易云官方 outer url 对版权曲只给 30 秒试听。** `music.163.com/song/media/outer/url?id=X.mp3` 返回 Content-Type 正常、帧头正常，但时长只有 30s。必须校验时长：
```python
src_netease.get_url(sid, expect_sec=track.duration_s)
```
内部用 ffprobe 量下载到的临时文件，差异 > max(15s, 15%) 就判为试听片段，换镜像。实测 Beyond《海阔天空》outer=30s，镜像②=239.6s 无损。

**19. 用 Content-Length + 位速估算时长不可靠。** VBR 编码下误差极大（实测算出 0.0s）。必须真下载到临时文件用 ffprobe 量。

**20. 未登录网易云搜不到部分大厂原唱。** 周杰伦《七里香》只能搜到翻唱，这是版权限制不是接口问题。要原唱走 QQ 源。Beyond《海阔天空》、洛天依等则正常。

**21. B站 412 不是 IP 限流，是缺 cookie。** 新建 Session 直接打 `api.bilibili.com/x/web-interface/search/type` 必 412。做 `GET https://www.bilibili.com/` 拿 `buvid3`/`b_nut` 后就正常。成功率 100%，不用重试退避。

**22. vkeys 会给失效 vkey（404）。** `api.vkeys.cn` 返回的直链有时是死的，直接下载报 `404 Client Error`。取链后必须校验：Range GET 前 1KB，检查 `Content-Type` 是 audio 或帧头是 mp3/flac 魔数。不通过就换下一档音质。实测 5 条里 1 条是死链。

**23. 队列状态落盘要原子替换。** `json.dump` 直接写目标文件，进程被杀会留半截 JSON 导致下次读不出来。必须临时文件 + `os.replace()`。

**24. `createMediaElementSource` 同一 audio 元素只能建一次。** 重复调用抛 `InvalidStateError`。波形要用全局单例 `AudioContext` + `AnalyserNode`，切歌只换 `audio.src`，不重建音频图。

**25. 停 Web 进程要按命令行匹配，不能只看端口。** `Get-NetTCPConnection -LocalPort 8420` 有时拿到 PID=0（子进程），停不掉真正的监听进程。正确做法：
```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -like '*run.py*web*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```
而且杀完要**确认端口释放**再启动，否则新进程起不来、旧页面继续被服务，表现为「代码改了但页面没变」。

**26. 大列表一次性 innerHTML 会卡。** 500 个卡片带封面一起插入 DOM，主线程阻塞 1~2 秒，页面「假死」。改分批：每批 60 条 + `IntersectionObserver` 观察哨兵元素（`rootMargin:320px` 提前触发），滚到底才续下一批。首屏只在 60 个节点上做布局。

**27. 拖拽排序要修正 current 指针。** `move(frm,to)` 之后：
- `cur == frm` → `cur = to`
- `frm < cur <= to` → `cur -= 1`
- `to <= cur < frm` → `cur += 1`

漏了这三种情况，拖完正在播放的那条会错位到别的歌。

**28. Python 里写 JS 正则必须用 raw string。** `PAGE = """..."""` 里的 JS 含有 `\[`、`\d`、`\s`，Python 会当转义序列并抛 `SyntaxWarning: invalid escape sequence`。全部改成 `PAGE = r"""..."""`。

**29. Service Worker 不能被浏览器缓存。** `sw.js` 必须回 `Cache-Control: no-cache, no-store, must-revalidate`，否则改了 SW 逻辑用户永远拿到旧版。同时加 `Service-Worker-Allowed: /` 允许根作用域注册。

**30. 「纯音乐无填词」是假歌词。** QQ/网易云对有版权争议或纯音乐的曲目会返回 `[00:00:00]此歌曲为没有填词的纯音乐，请您欣赏`——格式合法、有 LRC 时间戳，直接当成功会把缓存污染成空壳。必须做真伪校验：去时间戳后正文 < 40 字、或命中「纯音乐/没有填词/暂无歌词/instrumental」黑名单且总长 < 120 字，判为无效并继续试下一个源。已缓存过的占位歌词也要自动作废。

**31. QQ 的 vkey 会大面积失效（404）。** `api.vkeys.cn` 对某些歌（王菲《红豆》、买辣椒也用券《起风了》）所有音质档都返回失效 vkey。`get_url` 里的 Range 校验会全部拒绝，此时不能直接放弃——加 `_cross_source_url()` 跨源兜底：按「歌名+歌手」在另一源重搜，匹配分 ≥ 0.7 就取那边的链接。实测这两首歌兜底到网易云后都成功下载，且顺带拿到歌词。

**32. 均衡器必须插在 MediaElementSource 和 Analyser 之间。** 音频图链路是 `srcNode → EQ[0] → EQ[1] → … → EQ[7] → analyser → destination`。如果 `srcNode` 直连 `analyser` 再想改 EQ，得断开重连，容易漏。建图时一次性串好 8 个 filter，改增益只改 `bq.gain.value`，不动连接。

**33. 全库导出要提供「不读 ID3」的快速模式。** 5176 首逐个解析 ID3 读时长要 111 秒，用户等不了。`library_index(fast=True)` 只取文件大小不解析标签，2.9 秒完成（38 倍）。代价是 `total_hours` 为 0、`duration` 全 0，聚合统计仍准确（按文件数）。

**34. CSV 要带 UTF-8 BOM，否则 Excel 打开中文乱码。** `csv.writer` 直接写 UTF-8 无 BOM，Excel 会按 GBK 解码，歌名全变问号。开头加 `\ufeff` 即可。

**35. `audio.playbackRate` 在切歌后被重置。** 改 `audio.src` 后浏览器把 rate 恢复成 1，所以 `play()` 里每次都要重新赋值 `audio.playbackRate = playRate`。另外要设 `preservesPitch = true`，否则变速会变调（松鼠音）。Safari 用 `webkitPreservesPitch`，Firefox 用 `mozPreservesPitch`，三个都设上。

**36. 写 ID3 会改文件 mtime，封面缓存要跟着失效。** `covercache` 的 key 是「路径+大小+mtime」，补完封面后 mtime 变了，旧 key 失效，但旧缓存文件还在。表现为「前端刷新还是显示无封面」。补完要调 `covercache.cover_cache_clear()`（`/api/coverfill` 已自动做），或让前端加 `?t=<时间戳>` 破缓存。

**37. 封面补全必须 `delall("APIC")` 再 add。** 有些 mp3 里有多张 APIC（不同 type：封面/艺人/碟片），直接 add 会叠加。先 `tags.delall("APIC")` 清干净再加一张 type=3（front cover）。

**38. 守护循环的游标要记「完整文件路径」而不是「第 N 首」。** 用索引当游标，中途文件增删就错位；用路径当游标，`paths.index(last)` 找不到时从头开始，找到就 +1，天然容错。跑到底自动回到开头形成循环。

**39. 日志要轮转，否则日志文件无限增长。** 单文件超 1MB 就 `os.replace` 成 `.log.1`（旧的 `.log.1` 先删）。不轮转的话跑几个月就几个 GB。

**40. `library.count()` 返回整本字典，不是单个数字。** 签名是 `count(root=DEFAULT_ROOT)`，返回 `{"投稿": 468, "_归档_封存": 4708}`。写成 `count(root, "投稿")` 会抛 `TypeError: count() takes from 0 to 1 positional arguments but 2 were given`。

**41. 终端两列菜单必须按显示宽度算，不能用 `%-24s`。** Python 的格式化按字符数补空格，但中文在终端占 2 列，`"1) 启动 Web 服务"`（9 个中文+若干 ASCII）实际宽 20 列却被当成 14 字符，第二列就往前挤。要写 `unicodedata.east_asian_width(ch) in ("W","F")` 判宽再补。

**42. 交互式搜索不能用 `sources=None`。** 会连带跑酷我/千千/咪咕三个常年 503 的源，每次重试 5s+，3 秒的搜索被拖成 18 秒。交互场景要显式传 `sources=["qq","netease","bilibili"]`。

**43. 启动子进程失败时不能只报「未就绪」。** 用户双击后看到「20 秒内未监听端口」完全无法自救。要打诊断：python 路径、run.py 是否存在、端口被谁占、以及可以直接复制粘贴的排查命令。另外启动前先扫一遍残留进程（命令行含 `run.py web` 的 python），占着端口但不响应的要先问是否清掉。

**44. `.bat` 文件含中文会撕裂成命令（双击启动失败的元凶）。** `chcp 65001` 只改控制台 I/O 码页，**改不了 cmd.exe 解析 .bat 文件本身所用的码页**。简体中文 Windows 上 cmd 按 GBK 读批处理，`title music3 三源音乐工具` 的 UTF-8 字节被拆开后：

```
'音乐工具' is not recognized as an internal or external command
'CODING' is not recognized as an internal or external command
'tf8' is not recognized as an internal or external command
```

后两条是被连带撕碎的**下一行** `set PYTHONIOENCODING=utf-8`。修法：`.bat` 全 ASCII，中文窗口标题在 Python 侧用 `SetConsoleTitleW`（宽字符 API，不受码页影响）。交付前跑 `python -X utf8 check_bat.py` 自检。

**45. 含中文的 .bat 不一定报错，但一定乱码。** `title` / `echo` 接受任意字符串参数，中文被 GBK 解码后仍是合法参数，所以只是标题和回显变乱码、不报错；但一旦内容里恰好有 `(` `&` `|` 等字节被误读成控制符，就会撕裂成命令并连带破坏后续行。这种不确定性最高，所以规则是「一律纯 ASCII」，不留侥幸。

**46. `input()` 在 stdin 耗尽时抛 `EOFError`，满屏 traceback。** 触发场景：用户按 Ctrl+Z、双击后被脚本管道调用、父进程关掉 stdin。双击交互时遇不到，一遇到就是 `EOFError: EOF when reading a line` + 调用栈。包一层 `ask()`：`try: input(prompt) except (EOFError, KeyboardInterrupt): return ""`，把 `""` 当「取消/退出」处理。实测三种极端输入（`echo q` / 空 stdin / `< nul`）均零 Traceback。

## 歌词补全

库内实测 **463/467 首没有内嵌歌词**，播放器的歌词面板因此经常空着。`lyricfill` 解决这个问题：

```powershell
# 单个文件试
python -X utf8 run.py lyric -f "D:\音乐\投稿\QQ音乐\周杰伦 - 花海.mp3" -v

# 某个分类全补
python -X utf8 run.py lyric 投稿\洛天依 -v

# 全库补，并把歌词写回 mp3 的 ID3 USLT（任何播放器都能看到）
python -X utf8 run.py lyric -w -l 100

# 看缓存 / 清缓存
python -X utf8 run.py lyric-cache
python -X utf8 run.py lyric-cache --clear
```

流程：
1. 读内嵌歌词，已有 > 80 字就跳过
2. 查 `_cache/lyrics/<md5>.lrc` 缓存
3. 从文件名解析「歌手 - 歌名」（剥离 `(Live)` `[Remix]` `feat.` `4K` 等噪声）
4. 网易云搜 → 打分 ≥ 0.55 才取歌词 → `_is_real_lyric()` 验真 → 通过则用
5. 网易云不行换 QQ（含 base64 解码）
6. 结果写缓存；`-w` 时同时写回 ID3

前端「词」面板在检测到内嵌歌词不足 40 字时，会自动调 `/api/lyric` 联网补，用户无感。

实测效果：

| 曲目 | 来源 | 歌词字数 |
|---|---|---|
| 花海 - 周杰伦 | qq | 1005 |
| DOTA税 - 洛天依 | qq | 1990 |
| 万神纪 - 凤凰传奇 | netease | 2866 |
| 东京不太热 - 封茗囧菌 | netease | 1572 |

## 播放统计

播满 30 秒才计一次（避免误点刷榜），独立累加器落盘 `_cache/stats.json`——不依赖只保留 500 条的播放历史，不会因为裁剪而丢数据。

统计页显示：总播放次数 / 累计时长 / 不重复曲目 / 不重复歌手，下方可切「曲目排行」「歌手排行」，排行支持按次数或按时长排序。

实测：
```
总播放      7 次
累计时长    1830.0 秒
不重复曲目  4 首
不重复歌手  3 位

曲目排行：稻香 3次 669s / 七里香 2次 598s / 千本樱 1次 / 起风了 1次
歌手排行：周杰伦 5次 1267s / 洛天依 1次 / 买辣椒也用券 1次
```

## 导出

```powershell
# 曲库某分类 → m3u8（相对路径，foobar2000 / VLC / 手机播放器通用）
python -X utf8 run.py export "投稿\QQ音乐" -t m3u8 -o out.m3u8

# 全部格式
python -X utf8 run.py export -t csv   -o lib.csv      # Excel 直接开（UTF-8 BOM）
python -X utf8 run.py export -t json  -o lib.json     # 带 detail 时含歌词/封面标记
python -X utf8 run.py export -t index -o index.json   # 全库索引 + 歌手聚合

# 只导当前播放列表
python -X utf8 run.py export -p -t m3u8 -o now.m3u8
```

Web 界面在「清理」页底部有导出按钮组。

| 格式 | 用途 | 5176 首耗时 |
|---|---|---|
| m3u8 | 播放器通用歌单 | <1s |
| CSV | Excel 表格 | <1s |
| JSON | 程序处理 | <1s |
| index（快） | 全库索引，不读 ID3 时长 | **2.9s** |
| index（含时长） | 全库索引，全量解析 | 111s |

全库实测：**5176 首 / 31921.1 MB / 153 位歌手**。

## 播放模式

播放器左侧 `🔁` 按钮循环切换，选择记在 `localStorage.m3_mode`：

| 模式 | 图标 | 行为 |
|---|---|---|
| 列表循环 | 🔁 | 播完最后一首回到第一首 |
| 单曲循环 | 🔂 | 同一首反复播 |
| 随机 | 🔀 | 随机选下一首（避开当前这首） |
| 顺序播放 | ➡ | 播完最后一首停止 |

## 播放速度

播放器 `1x` 按钮循环切换 0.5 / 0.75 / 1.0 / 1.25 / 1.5 / 2.0，或用 `[` `]` 快捷键。非 1x 时按钮变蓝提示。

```javascript
audio.playbackRate = playRate;
audio.preservesPitch = true;   // 变速不变调
```

**关键**：`audio.playbackRate` 在切歌（改 `audio.src`）后会重置回 1，所以 `play()` 里每次都要重新赋值。配置存 `localStorage.m3_rate`。

## 库健康检查

```powershell
python -X utf8 run.py health                        # 全库快速扫描（不读 ID3）
python -X utf8 run.py health 投稿\洛天依 --detail    # 某分类 + 明细
python -X utf8 run.py health -d --detail            # 读 ID3（准，慢）
python -X utf8 run.py fixname                        # 预览要改的文件名
python -X utf8 run.py fixname --yes                  # 真改
```

7 项指标 + 0~100 健康分：

| 指标 | 判据 |
|---|---|
| 缺歌词 | 内嵌歌词 < 40 字（需 `-d`） |
| 无封面 | ID3 无 APIC（需 `-d`） |
| 重复 | 归一化「歌手\|歌名」碰撞 |
| 命名异常 | 含 `<>:"\|?*` / 超 120 字 / 疑似「未命名/副本」 |
| 无歌手 | 文件名没有 `歌手 - ` 前缀 |
| 文件过小 | < 150KB（需 `-d` 时按时长 < 8s 判） |
| 文件过大 | > 80MB（需 `-d` 时按时长 > 30min 判） |

打分：`100 - (命名异常×30 + 过小×25 + 重复×20 + 无歌手×10 + 缺歌词×15) / 总数`

实测：
```
全库 5176 首 / 31921.1 MB / 健康分 77.1 / 快速模式 1.59s
投稿\QQ音乐 6 首：快速 100 分，深度 95 分（2 首缺歌词+无封面）
```

Web「清理」页顶部有「健康检查」按钮 + 「读 ID3」开关，结果以卡片 + 明细列表展示，旁边还有「补封面」按钮可一键对「无封面」列表逐首联网补。

## 封面补全

抽查投稿区 40 首，**36 首没有内嵌封面（90%）**。播放在手机 / 车载 / foobar 里全是占位图，体验差。

```powershell
python -X utf8 run.py cover -f "D:\音乐\投稿\QQ音乐\三亩地 - 城南花已开.mp3" -v
python -X utf8 run.py cover 投稿\洛天依 -v          # 某分类
python -X utf8 run.py cover -l 50                   # 全库前 50 首
python -X utf8 run.py cover --no-write              # 只下载缓存，不改文件
python -X utf8 run.py cover-cache [--clear]
```

流程（复用 `lyricfill` 的命名解析与打分）：
1. 已有内嵌封面 → 跳过
2. 查 `_cache/fetched_covers/<md5>.jpg` 缓存
3. 网易云搜 → 打分 ≥ 0.55 → 取 `al.picUrl` 下载
4. 网易云不行 → QQ 搜 → 取 `y.gtimg.cn/music/photo_new/T002R800x800M000{album_mid}.jpg`
5. 下载成功 → 写缓存；默认同时 `tags.delall("APIC")` + 新增 APIC 写回 ID3

实测：

| 曲目 | 来源 | 封面 |
|---|---|---|
| 三亩地 - 城南花已开 | netease | 39934 B JPEG |
| 买辣椒也用券 - 起风了 | embedded | 已有，跳过 |
| 周杰伦 - 七里香 | embedded | 已有，跳过 |

写回后验证：`APIC bytes: 39934 mime: image/jpeg`，音频时长/码率不受影响。

**注意**：写 ID3 会改文件 mtime，封面读缓存（`covercache`）的 key 含 mtime，所以补完要清一次 `covercache`，否则前端仍拿到旧的「无封面」结果。`/api/coverfill` 已自动处理。

## 维护守护

投稿区实测 **116/120 缺歌词、115/120 无封面**。一次性全补会跑很久，所以做成「一次一小批 + 断点续传」的守护循环。

```powershell
# 跑一轮（默认 20 首）
python -X utf8 run.py maintain

# 跑 10 轮，间隔 30s
python -X utf8 run.py maintain -r 10 -g 30

# 跑到跑完全库为止（-r 0）
python -X utf8 run.py maintain -r 0

# 只看状态 + 最近日志
python -X utf8 run.py maintain --status --tail 20

# 只补封面不补歌词 / 不动文件
python -X utf8 run.py maintain --no-lyric --no-write

# 重置断点，下次从头扫
python -X utf8 run.py maintain --reset
```

单轮做的事：
1. **清临时文件**（`.tmp_*` / `.dl_*` / `*.part`）
2. **补歌词**：内嵌歌词不足 40 字 → 联网搜 → 写 ID3 USLT
3. **补封面**：无 APIC → 网易云/QQ 搜 → 写 ID3 APIC

**断点续传**：`_cache/maintain_state.json` 记 `cursor[子目录] = 上一个处理完的文件路径`，下次从它后面继续；跑到底自动回到开头。

**日志落盘**：`_cache/maintain.log`，单文件超 1MB 自动轮转为 `.log.1`。

**累计统计**：`totals.{lyric,cover,clean}` 只增不减，能看到历史上补了多少。

实测（`--status --tail`）：
```
已跑 1 轮，上次 2026-11-19 10:38:41
累计: 歌词 0 / 封面 0 / 清理 0
断点:
  投稿\QQ音乐 -> 周杰伦 - 七里香.mp3
日志行数: 3

最近 5 行:
  2026-11-19 10:38:30 本轮处理 3 首（从第 1 首开始，共 6）
  2026-11-19 10:38:41 [1/3] 歌词- 三亩地 - 城南花已开.mp3
  2026-11-19 10:38:41 本轮完成: 歌词+0 歌词-1 封面+0 封面-0 清理0
```

Web「清理」页有「维护守护」面板：跑一轮 / 看状态 / 看日志 / 重置断点，每轮首数可调，三项功能可勾选开关，结果以 4 张统计卡展示。

## 打分规则

```
歌名完全匹配   +0.50    歌名包含 +0.40    字覆盖率 × 0.40
歌手完全/包含  +0.40    歌名内含歌手 +0.15
标题含歌手但无歌名 -0.15

减分（轻，-0.25）：翻唱/片段/试听/铃声/dj版/remix/live版/女声/升调/slowed…
减分（重，-0.50）：伴奏/beat/instrumental/karaoke/纯音乐/midi/八音盒
二创减分（-0.20）：致敬/二创/搬运/合集/混剪/串烧/电台/节目
时长：<30s -0.30；>900s -0.10；60~600s +0.05

源权重：qq 1.00 / netease 0.98 / kuwo 0.90 / qianqian 0.85 / migu 0.80 / bilibili 0.70
```

实测样例：

| 标题 | 歌手 | 分数 |
|---|---|---|
| 七里香 | 周杰伦 | 0.93 |
| 七里香 (Live) | 周杰伦 | 0.85 |
| 周杰伦《七里香》Pop Rap Beat | BFH beats | 0.10 |
| 七里香 (伴奏) | 周杰伦 | 0.34 |
| 七里香 (女声版) | 吉拉朵 | 0.20 |

0.80 以上可直下；0.5~0.8 需过目；<0.5 多为翻唱变体。

## 配置

改 `config.json` 即可，无需动代码：

```json
{
 "root": "D:\\音乐",
 "sources": ["qq", "netease", "bilibili"],
 "workers": 3,
 "retries": 2,
 "tag_cover": true,
 "tag_lyric": true,
 "valid_min_sec": 8,
 "valid_max_sec": 1500
}
```

环境变量 `MUSIC3_ROOT` 可覆盖根目录。

## 已验收

| 项 | 结果 |
|---|---|
| QQ 音乐下载转 mp3 | ✅ 周杰伦-晴天 269.7s / 242kbps |
| 网易云搜索+直链 | ✅ 返回 8 条含 flac 真链 |
| B站搜索+下载 | ✅ 达拉崩吧 5510KB，中文名正确 |
| 跨源打分排序 | ✅ 七里香-周杰伦 0.93 第一，Pop Beat 版 0.10 |
| 封面+歌词内嵌 | ✅ 951KB JPEG + 1470 字歌词 |
| 并发队列 | ✅ 稻香 1/1 成功 |
| 空结果重试 | ✅ 0→13→14 自愈 |
| 曲库扫描 | ✅ 5178 首（封存 4708 + 投稿 466） |
| 网页试听 `/api/stream` | ✅ HTTP 206, `Content-Range: bytes 0-1023/7571710` |
| 封面接口 `/api/cover` | ✅ 78888 字节 JPEG |
| 标签接口 `/api/tags` | ✅ 稻香/周杰伦/223.5s/267kbps/1057字歌词 |
| SSE 实时进度 | ✅ job 创建、日志推送、状态流转 |
| 新前端 | ✅ 21522 字节，四标签页 + 播放器条 + 响应式 |
| **QQ 快速通道搜索** | ✅ **1.2s**（原 223s，提速 185 倍） |
| **QQ 快速通道下载** | ✅ 七里香 299.2s / 271kbps / 封面 157KB / 歌词 903 字 |
| **网易云快速通道搜索** | ✅ **1.0s**（原 154s，提速 150 倍） |
| **网易云快速通道下载** | ✅ 海阔天空 239.56s / 260kbps / 封面 121KB / 歌词 786 字 |
| **网易云 30s 试听识别** | ✅ outer=30s 被拒，改用镜像②拿到 239.6s 完整版 |
| **B站 API 搜索** | ✅ **0.34~2.29s**（原 yt-dlp 15s，提速 7~50 倍） |
| **B站 412 根治** | ✅ 先访问首页拿 buvid3 cookie，不再 412 |
| **三源并发** | ✅ qq+netease+bilibili **1.54s**，27 条结果 |
| **队列中断恢复** | ✅ pending/resume/pending-clear 三命令，只跑剩余任务 |
| **QQ 死链检测** | ✅ Range GET 前 1KB 校验，404 死链自动换档（5 条中 4 条可用） |
| **Web `/api/search`** | ✅ 1.38s |
| **Web `/api/get`** | ✅ 4.63s 落盘 `D:\音乐\投稿\QQ音乐\买辣椒也用券 - 起风了.mp3` |
| **波形可视化** | ✅ Web Audio `AnalyserNode`，64 柱实时频谱，暂停降为静态波形 |
| **播放历史** | ✅ `/api/history` 落盘去重置顶，500 条上限，前端独立标签页 |
| **封面磁盘缓存** | ✅ 首次 30~190ms → 缓存 2~24ms（快 4-10 倍） |
| **上一首/下一首** | ✅ 播放器新增 ⏮ ⏭ |
| **播放列表抽屉** | ✅ 拖拽排序（HTML5 DnD）、点播、删除、清空，落盘持久 |
| **分批渲染** | ✅ 每批 60 条 + IntersectionObserver，500 首不卡 |
| **网格/列表视图** | ✅ 切换记忆在 localStorage |
| **歌词滚动** | ✅ LRC 解析 48 行，二分查找同步，点行跳转 |
| **快捷键** | ✅ 空格/←→/↑↓/L/N/P/Esc，音量记忆 |
| **PWA** | ✅ manifest+sw+icon 三端点 200，可安装到桌面 |
| **歌词补全** | ✅ 库内 463/467 首缺歌词，实测花海 1005字 / DOTA税 1990字 / 万神纪 2866字 |
| **播放统计** | ✅ 7 次 1830s，稻香3次居首，周杰伦5次居首 |
| **下载自动补歌词** | ✅ 海阔天空 990字 / 红豆 883字 / 起风了 1678字，落盘即写入 ID3 |
| **跨源取链兜底** | ✅ QQ vkey 全失效时自动换网易云，红豆+起风了均成功 |
| **8段均衡器** | ✅ BiquadFilter 串联，6预设，配置持久化 |
| **导出** | ✅ m3u8/CSV/JSON/索引四格式，index 快模式 2.9s（原 111s） |
| **播放模式** | ✅ 列表循环/单曲循环/随机/顺序，图标+记忆 |
| **播放速度** | ✅ 0.5/0.75/1/1.25/1.5/2x，`[` `]` 快捷键，记忆 |
| **库健康检查** | ✅ 全库 5176 首 1.59s 出分（77.1），7 项指标 + 明细 |
| **封面补全** | ✅ 抽查 36/40 缺封面，城南花已开补得 39934B JPEG 并写回 APIC |
| **维护守护** | ✅ 断点续传（cursor 记录到文件级）、日志轮转、累计统计 |
| 全量编译 | ✅ exit 0 |

## 性能实测

### 提速前后对比

| 场景 | 旧（musicdl 全走） | 新（快速通道） | 提速 |
|---|---|---|---|
| QQ 搜索 | 223s | **1.2s** | 185× |
| 网易云搜索 | 154s | **1.0s** | 150× |
| **B站搜索** | **15s** | **0.3~2.3s** | **7~50×** |
| **三源并发（qq+ne+哔哩）** | ~250s | **1.54s** | **160×** |
| 双源（qq+ne） | ~250s | 1.41s | 180× |
| Web `/api/search`（三源） | 60s+ | **1.54s** | 39× |
| Web `/api/get`（搜索+下载落盘） | — | 4.63s | — |
| 搜索缓存命中 | <50ms | <50ms | — |

### 提速原理

musicdl 的 QQ/网易云源之所以慢，是因为它对**每一条搜索结果**都要：
1. 调第三方镜像取 vkey 直链
2. 用 HEAD 校验链接有效性
3. 失败的再换下一档音质重试

20 条结果就要做 20×N 次网络往返。

新方案把两件事拆开：

```
src_qq.search(kw)       # 只打搜索接口 → 1s，返回元数据
src_netease.search(kw)  # 只打 cloudsearch/pc → 1s
        ↓
[用户/程序挑选]
        ↓
src_qq.get_url(mid)     # 只为选中的那首取直链 → 1~2s
src_netease.get_url(id) # 同上 → 0.1~11s（含时长校验）
        ↓
downloader.download()
```

### 各源接口细节（已实测确认）

**QQ 音乐**

| 项 | 值 |
|---|---|
| 搜索端点 | `https://u.y.qq.com/cgi-bin/musics.fcg` |
| 签名 | 复用 `QQMusicClientUtils.sign()`（zzc：SHA1 → 索引位 → 33 字节 XOR → base64 → 前缀 "zzc"） |
| 取直链 | `https://api.vkeys.cn/music/tencent/song/link?mid=..&quality=14` |
| 质量 ID | 14=PREMIUM_MASTER_2_0 / 11=HI_RES / 10=SQ_LOSSLESS / 8=HQ / 4=STANDARD |
| 封面 | `https://y.gtimg.cn/music/photo_new/T002R800x800M000{album_mid}.jpg` |
| 歌词 | `https://api.vkeys.cn/v2/music/tencent/lyric?mid={mid}` |

**网易云音乐**

| 项 | 值 |
|---|---|
| 搜索端点 | `https://music.163.com/api/cloudsearch/pc`（POST，`s`/`type=1`/`limit`/`offset`） |
| 官方直链 | `https://music.163.com/song/media/outer/url?id={id}.mp3`（**版权曲只给 30s 试听**） |
| 镜像① | `https://musicapi.haitangw.net/music/wy.php?id=..&level=standard`（0.3s） |
| 镜像② | `https://nextmusic.toubiec.cn/api/getMusicUrl` POST（1~3s，能拿无损） |
| 质量档 | lossless / exhigh / higher / standard |
| 封面 | 搜索结果里的 `al.picUrl` |
| 歌词 | `https://music.163.com/api/song/lyric?id=..&lv=1&tv=1` |

**B站（本轮解决）**

| 项 | 值 |
|---|---|
| 搜索端点 | `https://api.bilibili.com/x/web-interface/search/type`（GET，`search_type=video`） |
| **前置** | **必须先 `GET https://www.bilibili.com/` 拿 `buvid3` cookie，否则 412** |
| 返回字段 | `bvid` / `title`(带 `<em>` 高亮需清洗) / `author` / `duration`("4:10") / `pic` / `play` / `pubdate` |
| 下载 | 仍用 yt-dlp（音视频分离 + ffmpeg 转码） |
| 格式 | `-f 30216/30280/30232/bestaudio` 绕开 Hi-Res |

### ⚠️ B站 412 的真因

之前一直报 `HTTP Error 412: Precondition Failed`，以为是 IP 限流。实际是 **缺 cookie**：
新建 `requests.Session()` 直接打 `search/type` 必 412；先 `GET https://www.bilibili.com/`
拿到 `buvid3` / `b_nut` 后再打就正常。

对比：yt-dlp 搜索 15s（起子进程 + 逐条抓详情页），API 搜索 0.3~2.3s。
首次调用要拿 cookie 约 2s，之后同进程内 0.3s。

官方 `outer/url` 对大厂版权曲（如周杰伦）**只返回 30 秒试听**，但 Content-Type 和帧头都是正常音频，肉眼看不出来。

`src_netease.get_url(sid, expect_sec=track.duration_s)` 会做时长校验：
1. 先探 outer url，下载前 6MB 到临时文件，ffprobe 读时长
2. 时长与搜索结果的 `dt` 差异 > max(15s, 15%) → 判定是试听片段，弃用
3. 依次尝试镜像①②，找到时长匹配的才返回

实测：海阔天空（Beyond）outer 只给 30s，镜像② 给 239.6s 无损完整版。

### 各源耗时基线

| 源 | 单次搜索 | 说明 |
|---|---|---|
| QQ（快速通道） | 1~2s | 只取元数据 |
| 网易云（快速通道） | 0.2~1.2s | 只取元数据 |
| B站（API） | 0.3~2.3s | 首调用拿 cookie 约 2s，之后 0.3s |
| B站（yt-dlp 旧路） | 15s | 起子进程 + 逐条抓详情，412 时 +8s |
| QQ（musicdl 旧路） | 223s（size=8）/ 378s（size=20） | 每条都取 vkey |
| 网易云（musicdl 旧路） | 154s | 同上 |
| 搜索缓存命中 | <50ms | 30 分钟 TTL |

### 队列中断恢复

批量下载会把任务清单落盘到 `<root>/.music3_pending.json`（原子替换写，进程被杀不留半截文件）。

```powershell
# 跑批量（中途 Ctrl+C / 断电 / 崩了都行）
python -X utf8 run.py queue want.txt -n 1 -w 3

# 看还剩什么没跑完
python -X utf8 run.py pending

# 接着跑（自动跳过已完成的）
python -X utf8 run.py resume -w 3

# 不要了，清空
python -X utf8 run.py pending-clear
```

清单结构：
```json
{
 "meta": {"n": 1, "sources": ["qq","netease"], "bili": false, "workers": 3},
 "tasks": [
  {"kw": "晴天 周杰伦", "state": "done", "path": "D:\\音乐\\...", "err": ""},
  {"kw": "稻香 周杰伦", "state": "pending", "tries": 0}
 ]
}
```
`state` 三态：`pending` / `done` / `fail`。每完成一条立即刷盘。
| Web 三标签页 | ✅ 8960 字节，6 端点全通 |
| 全量编译 | ✅ exit 0 |

---

## 关于作者

| | |
|---|---|
| **作者** | 最中幻想 |
| **微信** | `andyloveanny` |
| **GitHub** | [qingshanjiluo/music3](https://github.com/qingshanjiluo/music3) |

这个工具是给自建曲库用的：`D:\音乐` 下 5176 首 mp3，横跨 B站投稿、网易云、QQ音乐、酷我、千千、咪咕六个来源。三源搜索原本一次要等 150~220 秒，拆成「搜索只拿元数据、下载才取直链」两步后压到 1~3 秒。中间踩的坑全写在上面「踩过的坑」里，共 46 条，都是真实报错原文，不是猜的。

如果它帮你省了时间：

- **点个 ⭐ Star** —— 最直接的鼓励，也让更多人能找到它
- **加微信** `andyloveanny` —— 提需求、报 bug、聊实现都行
- **提 Issue / PR** —— 欢迎，看到会回

### 常见问题

**Q：为什么网易云搜不到周杰伦原唱？**
A：未登录状态下大厂原唱受限，只有翻唱。要原唱走 QQ 源——这是版权限制，不是接口问题。

**Q：QQ 报 `qq no url (mid=...)`？**
A：vkey 失效。工具会自动跨源兜底换网易云；如果那边也不行，换一首或换源。

**Q：为什么歌词/封面补全是空的？**
A：纯音乐没有真歌词（接口会返回「此歌曲为没有填词的纯音乐」占位文本，已做真伪过滤）。封面补全需要曲名匹配度 ≥ 0.55，太冷门的搜不到。

**Q：要跑多久？**
A：全库 5176 首补歌词+封面，单首约 3~4 秒（含网络），约 5~6 小时。断点续传，随时可停。

---

<sub>如果这个项目对你有帮助，请给个 ⭐ Star 支持一下 —— 作者：最中幻想（微信 andyloveanny）</sub>
