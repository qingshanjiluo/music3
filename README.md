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

## 第14轮：设计重构 + 三 bug + 音质/登录/赠金

- **曲库点击后一直刷新抖动（死循环）**：`loadChips()` 尾部递归 `openDir()`、`openDir()` 头部调 `loadChips()`，两次构成环，每次点分类片互相触发。修法：`loadChips` 只渲染分类片（抽 `_loadChipsOnly`），当前分类高亮由 `chipsRefreshActive()` 就地更新；`openDir` 仅在片缺失时拉一次。
- **搜索页 MV/歌手/歌曲不能同时搜**：新增「全部」模式（默认），`Promise.allSettled` 三路并发（歌曲+歌手曲+B站MV）→ `renderRows` 统一渲染、跨组去重、分组标签（曲/歌手/MV）。实测 4.2s 出 33 条（原串行约 14s）。
- **设计语言**（frontend-design）：tokens 重定（`--bg:#0b0d12` 冷蓝黑、`--acc:#4e8cff→--acc2:#9b6bff` 双调渐变）、正文 13.5px/1.65、播放器玻璃拟态 `backdrop-filter blur(20px) saturate(1.2)` + 顶缘 `rgba(78,140,255,.22)` 光、进度条 2px、波形提亮 0.45、去 tab 阴影、分组标签三色（曲蓝/歌手青/MV 紫）。
- **音质/登录/赠金**：设置弹窗（⚙/设置按钮）—— QQ 音质顺序（`config.qq_quality_order` 三档透传 `src_qq.get_url`）、QQ `qm_keyst` cookie 登录（`apply_login` 注入 `_S.headers.Cookie`，提高 vkey 成功率）、网易云 `MUSIC_U` cookie 登录（解锁版权原唱搜索）、赠金余额（本地记账，每成功下载扣 1，`config.credit_balance`，设为 null 不限量）。
- **赠金方案说明（假设）**：非任务原文字段，按「本地记账额度」落地——每下载 1 首 -1，余额 0 不拦（记欠费），设置页可 +N/-N。若你指的是「QQ 音乐赠送配额/其他平台赠金」，告诉我接口我接真实数据。

实测：`GET/POST /api/config` 200/200 持久化 ✓、三路并发 4.2s ✓、歌词候选 8 条 ✓、赠金 100→99+stats 13→14 ✓、node --check 0 ✓、JS undefined ids NONE、CSS 217/217、fmtDur 单定义、死循环已解环 ✓。

---

## 第15轮：搜索页交互大升级

**新增能力（全部实测）**

| 能力 | 说明 | 实测 |
|---|---|---|
| **预听（不下载）** | `/api/preview` 取在线直链，浏览器 `<audio>` 直连试听 | 1.2s 取链 ok=True（QQ flac） |
| **大图灯箱** | MV/封面点击放大到 90vw，点任意处/Esc 关 | 结构+CSS 全 OK |
| **多选 + 一键下载** | 表格加复选列/全选/全不选/`批量下载所选`（并发走 `/api/get`） | 结构 OK |
| **收藏歌单** | 新标签页「收藏」：`★` 收藏、列表播放/下载/移除/清空、导出 m3u8、**一键下载** | CRUD 实测：add✓ 重复不加✓ remove✓ |
| **歌单链接下载** | 粘贴含 BV 号的歌单链接 → 提取 BV → `act=playlist` 后台 job 批量下 MV | 缺参校验✓ |
| **搜索词→批量** | `加入批量` 把当前关键词追加进批量页 | — |

**接口**
- `GET /api/preview?title=&artists=&q=&sources=` → `{ok,url,title,artists,ext}`
- `GET /api/favs?act=add|remove|clear|add_multi` → 收藏歌单（`_cache/favs.json` 原子写）
- `GET /api/mv?act=playlist&bvids=...` → 歌单批量下载 job

**校验**：compile 0、node --check 0、JS undefined ids NONE、CSS 232/232、
13 个新 marker 全 OK、7 个端点 GET OK、preview 1.2s。

**踩坑追加**
- Python 源码里写 JS 正则 `split(/[\r\n,]+/)`，若用普通字符串字面量，`\r\n`
  会变成真回车/换行嵌进正则 → JS 语法错 `missing /`。修法：先确认 JS 侧字节是
  `\r\n` 两个字符，不是 `0x0a`；用字节级替换而非肉眼改。
- 补字符时 `old` 段写错会连带切掉相邻 `)` `]`，node --check 会指到后一行。
  改一行 JS 后必须跑 node --check，别只看 py_compile。
- `/api/export` 全库 m3u8 要 87 秒（每首读 ffprobe 时长），不是坏了，是慢测试超时。

---

## 第16轮（自我完善闭环 R1）：检查→优化→设计→验收

**检查**：24 个 GET 端点全 OK、stream/file Range 206、py_compile 0、node --check 0、
JS undefined ids NONE、CSS 245/245。发现 3 个问题进入优化。

**优化**
1. 曲库截断修复：`/api/ls` limit 500→2000，超限提示用查找缩小（原归档区 4708 首看不到 4208 首）。
2. **预听防盗链代理 `/api/pvstream`**：转发在线音频流带 Referer/UA，CDN 直连被拒时保底；
   **SSRF 白名单**（只放行 .qq.com/.gtimg.cn/.163/.music.163.com/.126.net/.bilivideo.com，
   外域 403 实测）。Range 透传（206 + Content-Range），实测首 8B `fLaC` 魔数、二次 Range 902KB。
   前端 `a.src = d.proxy`，`crossOrigin=anonymous`。
3. 封面进视口才拉：`IntersectionObserver` 懒加载（.cardcov/.lcov），500 卡片不再一次性发 500 请求。

**设计（frontend-design 风格，6 项全落）**
- 环境光晕：`body::before` 顶部两团低饱和蓝紫径向光 + 底部极淡绿，收在视觉中心之上。
- 头部渐变分隔线：`header::after` 两端透明、中间实色 1px。
- 表格微交互：行 hover 左侧 3px 强调条 + 分数徽章放大。
- 按钮反馈：`transition: transform` + `:active scale(.92)`。
- 播放器呼吸光：播放中 `.pulsing` 让顶缘光蓝→紫呼吸（2.6s），`prefers-reduced-motion` 关。

**验收证据**：设计 6/6 marker OK、优化 3/3 OK、端点 24/0、预听 2.0s/206/fLaC、
HTML 98902B、JS 61400ch undefined NONE、CSS 245/245、node 0、compile 0。

---

## 第17轮（闭环 R2）：检查→优化→设计→验收

**检查**：路由 29→30、无重复函数、search 2.2s / find 0.2s / health 1.3s，无报错。

**优化**：新增 `GET /api/track`（删除+改名）。此前 `browse.delete`/`rename` 有能力但没路由，
Web 端无法删除/改名。**安全校验全过**：dry-run 不误删（实测文件仍在）、无后缀 400、
源不存在 404、路径穿越 `../` 400、未知 act 400。

**设计**：加载骨架屏（`.sk` 扫光动画，`prefers-reduced-motion` 关）+ 空状态文案
（`emptyBox(icon, title, sub, hint, acts)` 带「去搜索」引导按钮）。曲库加载显示 12 卡骨架、
搜索显示 6 行骨架，替代空白跳动；空分类给出「先搜一首下载」引导。

**验收**：端点 25/0、R2 marker 5/6（`api/track` 后端路由前端无字面量=预期）、
HTML 100936B、JS undefined NONE、CSS 263/263、node 0、compile 0。

---

## 第18轮（闭环 R3）：曲库卡片删除/改名接线

**检查**：路由 30、无重复函数、5xx 全无、下载 OK（5.2s）；真缺口 = `/api/track`
有后端无前端按钮。

**优化+设计**：曲库卡片 hover 浮现 ✎改名 / ×删除 按钮（`.cardops` 悬浮层 +
`.card relative`，不挤网格布局）。delete 先 dry 预览 + 二次确认再真删；
rename 校验 `.mp3` 后缀与 `: * ? " < > |` 非法字符。

**验收**：端点 25/0、marker 7/8（`act=playlist` 实测 200 + 前端 `set('act','playlist')`
存在 = 字面量误报）、HTML 103072B、JS undefined NONE、CSS 269/269、node 0、compile 0。
歌单后台 job 实测 done（BV1xx411c7mD -> OK）。

**坑**：清 `__pycache__` 后首启要重编译全部 .pyc，固定等 13 秒会误判 DOWN ——
验收前先 `compileall -q src` 预热再启服务。

---

## 第19轮（闭环 R4）：接线缺口扫描 + 下载路径 + 文件夹管理

**检查**：44 按钮接线静态扫，`lyfetch`/`pvstop` 别名误报，真缺 `favexport` handler、
`/api/lib` 端点、设置无下载路径；`dest_dir(t.source)` 写死无覆盖。

**优化**
- `GET /api/lib` 文件夹管理（新建/改名/删空目录）：路径穿越 400、源缺 404、
  重复 409、删非空 409——**7 态全过**。
- **下载路径 `dest_sub`**：config 新字段（GET 返回 + POST 白名单），
  `/api/get` 读 config 并覆盖 `dest_dir`，根内校验 + 自动建目录。
- **实测**：POST 200 → GET 回读 `'投稿/_r4dest'` → 下载 5.7s 真落进
  `D:\音乐\投稿\_r4dest\RyaVocal - 晴天 (原唱 周杰伦).mp3` → 清空回读 `''`。
- `favexport` handler：收藏列表导出 m3u8（Blob 下载，EXTINF + rel/q）。

**设计**：曲库顶栏 `新建文件夹` / `改名当前` 按钮（prompt → `/api/lib`），
创建后就地刷新分类片；设置弹窗新增「下载路径」输入 + 说明行。

**验收**：端点 **26/0**、R4 marker 7/7、HTML 105399B、JS undefined NONE、
CSS 269/269、node 0、compile 0、46 按钮（`lyfetch` 为 `_lyBtn` 别名误报）。

**坑**：`do_POST` 与 GET handler 里两处形似的 `for k in (…)` 白名单元组，
按首命中 `replace` 会改错那处——多个同形锚点必须带行号/上下文定位
（`_cfg.load` 调用处才是 POST 分支）。

---

## 第20轮（闭环 R5）：JS 健壮性 + ARIA 可访问性

**检查**：JS 静态扫——9 个"未声明调用"全为白名单误报（Uint8Array/map/one 等）、
16 个空 catch 全为刻意 best-effort（preservesPitch 探测 / execCommand / chips 回刷）、
空格与方向键快捷键已存在（`case ' '`/Arrow*，首轮检查正则误报）。
真缺口：**role=0、aria-live=0、焦点无管理**。

**优化+设计（32 项 ARIA 补丁）**
- tab 栏 `role=tablist` + 7 个 tab `role=tab aria-selected` + 7 个 pane `tabpanel tabindex=-1`
- 9 处状态消息 `role=status aria-live=polite`（搜索/曲库/历史/收藏/统计/清理/维护/设置）
- 3 个弹窗 `role=dialog aria-modal aria-labelledby/label`（设置/关于/灯箱）
- **焦点管理**：`_opener` 打开记当前焦点、聚焦首个控件，关闭归还（4 函数）
- 播放进度 `role=progressbar` + JS 实时 `aria-valuenow`；音量 `aria-label`
- `setPlayIcon` 同步按钮名（播放/暂停）；`applySM` 同步 `aria-checked`
- vtog 2 处 `radiogroup`；✕ 按钮与删除 span 全部补可及名

**验收**：32/32 补丁全中 · role 0→32 · aria-live 9 · aria-label 33 ·
HTML 107594B · JS 66536ch undefined NONE · CSS 269/269 · **端点 26/0** · node 0 · compile 0。

**坑**：静态检查的"空格快捷键缺失"是正则没写 `case ' '` 导致的假阳性——
检查脚本必须先跑已知存在项做自校准，否则会把误报当工作项。

---

## 第21轮（闭环 R6）：真实浏览器 E2E 画面验收（补齐历轮欠账）

**工具链**：Python Playwright + 系统 Chrome（`executable_path` 指本机 chrome.exe，
Playwright 自带 chromium 未装，避免下载 150MB）；accessibility tree 走 CDP
`Accessibility.getFullAXTree`（新版 Playwright 已删 `page.accessibility`）。

**实测结果**
- 加载 3.22s · **console error 0** · pageerror 0 · requestfailed 0
- a11y tree 586 节点：tab 7 / tablist 1 / tabpanel 1(可见) / progressbar 1 / dialog(role 实测)
- 7 个 tab 全部可见可点；搜索 **38 行 2.24s**；多选 checked=3/picked=3 高亮生效
- 曲库点分类出 60 卡；设置弹窗 `role=dialog` 可见；截图留档 `docs/shots/` 5 张

**E2E 教训（写入检查脚本规范）**
1. `wait_for('#tb tr')` 会**被骨架行骗过**（`skrow` 也是 `<tr>`）——必须等
   `.rsel`/`.card` 等真内容选择器。
2. 点分类片后必须 `wait_for_function(卡片数>0)`，固定 sleep 1.5s 会误报 cards=0。
3. **服务"DOWN"先杀光残留 run.py**：多轮 Start-Process 累积 3 个僵尸进程，
   旧的占端口新 bind 失败（EPERM 静默），清光后 4.5s bind 正常。重启纪律：
   `Get-CimInstance ... *run.py* | Stop-Process` → 清 pyc → 起 → 轮询端口。
4. Playwright 环境：`playwright install` 未跑就用系统 Chrome；CDP 替代
   accessibility API。

---

## 第22轮（闭环 R7）：真实音频链路端到端实测 + 下载重试

**实测（全部真实外网/真实文件）**
| 链路 | 结果 |
|---|---|
| 预听 preview→pvstream | 2.5s 取链 ok；Range① 206 `fLaC` 魔数；Range② 206 100001B（1MB 段）；Content-Range ✓ |
| 本地曲库流 | Range 206 512B + Content-Range ✓（拖进度条通路） |
| mp3 下载 | QQ exists 2.1s / 网易真下 **6.1s ok(243.3s)** / 二次 exists 0.4s |
| **MV mp4 端到端** | job done **20.2s** → `测试 - 测试MV (MV).mp4` **20.5MB** ffprobe `mov` **212.3s** ✓（历史欠账首跑通） |

**优化**：`dlOne` 失败自动重试 1 次（1.5s 间隔）。实测下载首轮 0.1s fail 系 vkey
瞬时抖动，立即重试即过——不重试就直接把一次网络抖动报给用户。

**验收**：端点 25/0（`/api/lib` 本次回归脚本漏配，R4 已 7 态实测）、HTML 107876B、
JS undefined NONE、CSS 269/269、重试逻辑在 JS 内、node 0、compile 0；测试 MV 已清。

**坑**：全链路实测脚本给下载用的临时查询词若命中已存在的文件，`exists` 分支
会掩盖真实下载路径——验下载要用**库里没有的曲子**或 `force=1` + 确认日志含 `ok(...秒)`。

---

## 第23轮（闭环 R8）：歌单页链接下载 + 收藏 JSON 导入导出

**新能力**
- `GET /api/plimport?act=parse|download&url=`：QQ/网易/B站 **歌单页链接 → 曲目表 →
  打分下载**（异步 job 进「批量」页）。真实歌单实测 **25.1s 解析 12 首**。
  白名单双拦截实测：外域 403 文案、非 http 文案。
- 收藏页 `导出JSON` / `导入JSON`（`POST /api/favs {act:import}`，do_POST 分支）：
  导出含关键词/来源/时长可跨设备还原；导入实测 added=1、重复 added=0、空数组 400。
- `linkgo` 分流：http 链接走 plimport，BV 链接走既有 MV 歌单下载。

**路径记录（QQ 歌单 API 四条死路 + 一条活路）**
1. `musicu.fcg GetSonglist`：code=500003 缺 sign ✗
2. `fcg_get_diss_by_tag`：code=0 但 songlist 空 ✗
3. 页面 `__INITIAL_DATA__`：SPA 服务端空壳 `{}` ✗
4. JS chunk 挖接口：3 个 chunk 无特征串 ✗
5. **Playwright 渲染抓 DOM** `.songlist__list li` ✓（选定路径）

**修复（挂死根因）**：`launch` 默认 180s 超时 + **9 个残留 headless chrome**
拖垮启动 → 233s 失败。修：launch 30s + 整体 70s 总闸三检查点 + goto 25s +
selector 12s + `finally close` 兜底；修后 25.1s 完成。**每次跑 E2E 后必须清
无标题 chrome 进程**（与 run.py 残留同款坑）。

**验收**：端点 27/0、HTML 110031B、JS undefined NONE、CSS 269/269、
marker 3/3、收藏闭环（add/重复/空400/清理）、node 0、compile 0。

**坑**：在服务进程里同步起浏览器会被外部 kill/超时连坐——重活必须走异步 job；
Playwright launch 在本机并发场景要显式 `timeout=30000`，默认 180s 会把整条
HTTP 请求挂成超时。

---

## 第24轮（闭环 R9）：歌单下载全链路 + 网易 API 直取 + 多站点适配

**实测（真实外网 + 真实落盘）**
| 项 | 结果 |
|---|---|
| `plimport act=download` 真跑 | job 启动 41.9s（含解析 12 首）→ **8 首真实 mp3 落盘**，日志 `[2][3][4] -> OK`，12 首进行中 ✓ |
| 网易歌单 **API 直取** | `/api/v6/playlist/detail` **1.9s 200 首原文标题**（绕开字体反爬）✓ |
| QQ 歌单 Playwright | 22.5s 14 首（复合选择器兜底生效）✓ |
| 白名单 | 非法域 / 非 http 双拦截 0.0s ✓ |

**路径记录（网易三段）**
1. 直抓 `.m-table` DOM → 命中 200 行但**字体反爬拆字乱码**（`海 叫号非无 屿你`）✗
2. iframe 遍历必需：`#/playlist` 是外壳，真内容在 frame[1]（外层 13 li 是导航菜单）→ 误抓风险已记档
3. **API 直取** `v6/playlist/detail` → 原文标题 0.3-1.9s ✓（选定，Playwright 降级备选）

**修复**
- `page.frames` 在部分 Playwright 版本是**属性不是方法** → `callable()` 兼容
- `requests.get(trust_env=...)` 不收该 kwarg → Session 对象上设
- `launch` 偶发 `TargetClosed`（外部杀/竞态）→ 1.5s 重试 1 次
- 站点分派 `_SITE[qq|netease|bili]` + 网易反爬检测（PUA/替换符比例）自动判死路

**验收**：三站解析全通、白名单 2/2、compile 0、落盘证据 8 文件、测试目录已清。

**坑**：Playwright 版本差异别想当然——`page.frames` 是属性；`requests` 的
`trust_env` 挂 Session 不挂 get；外部 kill 会让 launch 报 TargetClosed，
服务进程里必须重试一次再判死。

---

## 第25轮（闭环 R10）：/api/track 真删真改 E2E + 曲库真分页

**删除/改名全链路（临时文件实测 7 态）**
1. dry 预览列出 rel ✓ 2. rename 真改（原文件消失/新文件在）✓
3. 非法名 `bad:name.txt` → 400 ✓ 4. 穿越 `../evil.mp3` → 400 ✓
5. 真删 → 文件消失 ✓ 6. 再删 → `ok:false missing`（幂等不报错）✓
7. dry=1 保护（文件仍在）✓ —— **真删真改全通，测试文件已清**。

**曲库真分页**：此前前端一次 `limit=2000`，**归档 4708 首被截断 2708 首**（且无 offset）。
改为 `PAGE=400` 触底循环续拉 + 8000 安全阀。E2E 实测：
**4708 首 13.1s 拉满**，滚动渲染 `1860/4708`，console error 0，截图
`docs/shots/r10_archive.png`（密铺网格 + 分类片高亮 + 状态条）。

**E2E 坑（新）**：等待条件 `已加载 \d+ 首` 会在**第一页 400** 就命中，误判完成；
分页进度文案与最终态必须用不同正则 —— 终态只认 `· 共 \d+ 首`。

**验收**：track 7/7、分页 4708 全见、compile 0、node 0、CSS 平、截图留档、测试文件清理。

---

## 第26轮（闭环 R11）：maintain 批量实测 + 健康页补歌词入口

**实测（真实联网补写 ID3）**
- `maintain tick` x3 真跑：**3 批补进 27 歌词 + 30 封面**（单批 8-9s，10 首/批
  → 约 1 首/s），log 逐条 `歌词+ 封面+`，totals 累计正确。
- **断点续证实**：`maintain_state.json` cursor 落盘（`_all` 指向
  归档深处 Whistle.mp3），重启后从断点继续不重扫。
- `coverfill` 单曲 0.1s（embedded 命中，bytes=0 因已在 ID3 内）。

**优化+设计**
- 健康页补 **「补歌词」按钮**（对 `no_lyric` 5176 首逐首联网补，复用
  `lyric-fetch act=pick` 管线）——此前只有补封面，歌词缺口 0 入口。
- `window._healthNoLyric/_health` scan 后赋值，两按钮共用明细。
- **深扫耗时提示**：`深扫全库约 136s（读 ID3）；快扫约 5s` —— health deep
  实测 136.2s 是读 5176 首 ID3 的固有成本，文案先行免得用户干等。

**验收**：marker 5/5、端点 **28/0**、HTML 111720B、JS 70234ch undefined NONE、
CSS 269/269、node 0、compile 0、测试目录已清。

**坑**：`coverfill` 正则从 `if u.path ==` 起截会漏掉嵌套 `if act ==`（acts 抓空是
扫描脚本截断，非功能缺陷）——检查脚本截取范围要跨到下一个同级 `if u.path ==`。

---

## 第27轮（闭环 R12）：maintain 大批推进 + health 深扫分批

**maintain 大批实测（后台 20 批 x 20 首）**：400 首 419s → **歌词 +296、封面 +391**
（totals 27→323 / 30→421），cursor 同步推进至归档深处，断点文件每批落盘。

**health 深扫分批**（原 136.2s 单请求挂死 → 分片可续）：
- 后端 `health.scan(+offset, +batch)` + `/api/health` 透传 `offset/batch/total_all/more/counts`。
- 前端 `doHealth` 循环拉 400 首/片，进度文案 `扫描进度 N/5188（s，片k）`，聚合 summary/detail。
- 实测：深扫 13 片 239.6s 完成（每片 2.2~38.2s，片间可中断续传）；快扫 3 片 5.5s。

**两连 bug（分批特有）**
1. `Math.max(0, Math.round((100-pen)*10)/10` 括号少一层 → node --check 报 `Unexpected token ')'`；
   **教训**：JS 内联进 Python 字符串，node --check 是唯一闸，改算分公式必须过闸。
2. **中英键错位**：`summary` 是中文键（缺歌词/重复），前端算分取 `acc.bad_name` 恒 0 → 分数恒 100.0
   （实测 1139 重复却报满分）。修：health.py 加 `rep["counts"]` 英文键、端点透传、前端按
   `parts[].counts` 聚合 → 85.8 分（与全库单次 77.1 的差 = dups 跨片无法去重，分批语义限制）。
   **教训**：显示字段与计算字段必须分两套键名，混用必出恒值 bug。

**验收**：快扫分批 3 片 5.5s 计分 85.8、端点 **28/0**、HTML 113389B、JS undefined NONE、
CSS 269/269、marker 5/5、node 0、compile 0、测试目录清理。

---

## 第28轮（闭环 R13）：dups 跨片去重（分批分收敛）+ maintain 续跑

**dups 跨片去重**：R12 分批 dups=1139 vs 全库 3394（片内 `seen` 跨片丢失 2/3）。
修法：**分批时 dups 走全库快扫**——纯文件名比较不读 ID3（全库 ~1s），
每片返回全库真值；前端 detail.dups / counts.dups 改**末片覆盖不累加**（累加会翻倍）。

**收敛实测（快扫 2000/片 vs 全库单次）**：
| | score | dups |
|---|---|---|
| 全库单次 | 77.1 | 3394 |
| 分批 3 片 | **77.1** | **3394** |
| 差 | **0.0** | **0.0** |

深扫片1 同样 counts.dups=3394（全库快扫在 deep 下也生效，成本 ~1s 可忽略）。

**maintain 续跑**：后台 30 批跑出 +233 歌词 / +235 封面（totals 323/421 → **556/656**）；
job 被本轮服务重启连坐断开（exit 1）——与 R12 记档行为一致：**cursor+totals 每批落盘，
重启即断、下次续跑**，无进度丢失。

**验收**：端点 28/0、HTML 113634B、JS undefined NONE、CSS 269/269、
marker 3/3（dups 覆盖逻辑在 JS 内）、node 0、compile 0、测试目录清理。

**坑**：分批聚合里"每片全量返回"的字段必须**末片覆盖**，与"每片增量"的字段累加规则
相反——同一循环里两种规则并存时，键名过滤要写在聚合处并加注释，否则下轮必踩翻倍。

---

## 第29轮（闭环 R14）：深扫分批浏览器 E2E + maintain 续跑 1000 首

**深扫分批 E2E（真实浏览器点健康检查）**：勾「读 ID3」→ 点健康检查 → 进度采样 28 次
→ `共 5188 首 / 33767.4 MB · 健康分 66.8/100（深度·分批完成）`，**108.3s**（原单请求 136s 挂死，
分批后片间可见进度）；console error **0**；三张截图留档
`docs/shots/r14_01_health_before.png` / `r14_02_health_progress.png` / `r14_03_health_done.png`。

**修：acc 重复累加假数（显示层第二个翻倍点）**：statcard 曾显示 `重复=44122`（=3394×13 片）
—— R13 只修了 `counts.dups`，显示用的 `acc` 还在累加每片全库真值。修：`summary['重复']` 改末片覆盖
→ 修后 statcard `重复=3394` ✓（与 cc/cc.dups 同规则）。**教训**：分批聚合有 3 处（cc/acc/detail）
必须同规则，漏一处就出假数——聚合键规则要在循环头一处集中声明。

**E2E 自伤**：测试脚本以「本片健康分」判完成 → 4s 第一片就误判退出；完成断点必须用唯一终态串
`分批完成`（进度文案「本片健康分 N」是子串）。**教训**：断点正则要用最窄唯一终态，禁用会出现在
中间态的子串。

**maintain 续跑**：40 批 1000 首 856s → **歌词 +893、封面 +953**（totals 556/656 → **1449/1609**，
即全库 5188 里 ~1609 首已有封面、~1449 首已有歌词）。done 未达（缺口仍 ~3600 首）—— 下轮续。

**验收**：分批重复 3394（期望 3394）、score 77.1、端点 28/0、HTML 113737B、JS undefined NONE、
CSS 269/269、marker 3/3、node 0、compile 0、测试目录清理、截图 3 张留档。

---

## 第30轮（闭环 R15）：补歌词/补封面根因修复 + maintain +636/+739

**E2E 起手就抓到按钮批量 0 命中**，逐层插桩定位 3 个真 bug：

1. **按钮发 `act=pick` 不带 `sid`** → 后端 `fetch_lyric(src,"")` 必空（0.0s 立即失败）。
   修：新增 `act=fill`（按 rel 走 maintain 已验证的 `fill_one` 管线），按钮改调它。
   **复测 0→3/10**（其余 msg="无词" 是网易对归档曲返回占位词，数据边界）。

2. **ID3 title/artist 颠倒**（实测 `title='Luis Fonsi' artist='Despacito'`、
   `title='Alan Walker' artist='Fade'`）→ `_score` 0.14~0.48 全卡 0.55 阈值，
   而候选里封面明明 `has_cover=True`。修：`find_lyric`/`find_cover` 失败后
   **交换 title/artist 重试一次**（source 标 `+swap`）。
   **封面复测 0→7/10**，7 条全是 `netease+swap` 命中。

3. 同因的文件名兜底（`artist==title`/空 artist → `parse_name`）一并落 `lyricfill`+`coverfill`。

**maintain 续跑**：40 批 1000 首 708s → 歌词 +636、封面 +739
（totals 1449/1609 → **2085/2348**）。

**验收**：封面 7/10、`act=fill` 在源与 JS 双 marker、端点 28/0、
HTML 113722B、JS undefined NONE、CSS 269/269、node 0、compile 0、测试目录清理。

**坑（双杀）**：① 补丁脚本第一次整批静默未落盘（后续每批必须 grep 行数核对，
不能只信脚本 print）；② 健康缺口列表是**老脏元数据**（maintain 补的新曲不在里面），
E2E 抽样测的是失败率最高的尾巴样本——批量成功率要用「maintain 增量 totals」当
主指标，缺口样本命中率只当下界。

---

## 第31轮（闭环 R16）：缺口头中尾复测 + 批量按钮实时进度

**修后缺口复测（头中尾各 15 首，抽样偏差已修正）**
| | 命中 | 说明 |
|---|---|---|
| coverfill | **12/15 = 80%** | `netease` 正常 11 + `netease+swap` 1 + `embedded` 1 |
| act=fill | 7/15 | 头部 7 首全「无词」、尾部 8 首里 7 首 ok——坐实 R15 结论：**头部是网易无词残渣**，不是 bug |

**maintain 续跑**：40 批 1000 首 580s → 歌词 +593、封面 +597
（totals 2085/2348 → **2678/2945**，即全库 ~57% 有歌词、~57% 有封面）。

**优化（按钮体验）**
- 批量进度行实时计数：`补歌词 12/369 · 成功7 失败5 · 歌名.mp3`（原只有 N/总数）。
- 耗时文案按实测对齐：`约 ceil(n*0.7)s，实测 0.64s/首`（原 1.5s/首 高估 2.3 倍）。
- 完成态加耗时+速率：`（369s，1.6 首/s）`。
- coverfill `ok 但 bytes=0`（已内嵌）不再误计失败。

**验收**：marker 2/2（实时计数 + 首/s 都在 JS）、端点 **28/0**、HTML 114098B、
JS 72612ch undefined NONE、CSS 269/269、node 0、compile 0、console error 0、截图留档。

**坑**：confirm 里的预估耗时必须跟循环实测对齐（1.5s/首 vs 实测 0.64s 差 2.3 倍，
用户会以为卡死）；批量完成文案要带 `Xs + Y首/s`，光有成功/失败数看不出效率。

---

## 第32轮（闭环 R17）：补歌词三态原因 + 340 首无词清单落盘

**根因**：`find_lyric` 失败恒返回 `("", "")` 无原因，`act=fill` 只能 fallback 显示
「无词」——把「网易命中但占位」「两源无匹配」「无歌名」三类混成一类，用户无从甄别。

**修**：`find_lyric` 返回**三态原因**（`ne_hit/qq_hit/ne_err/qq_err` 状态位）：
1. `网易/QQ命中但为占位歌词（纯音乐/伴奏）`——搜到了但源站只有占位
2. `两源无匹配（打分<0.55，疑似无歌词曲目或元数据不准）`
3. `两源搜索异常 …`；另补 `无歌名`、`embedded/cache` 成功态 msg。
`fill_one` 全部写进 `r["msg"]`，前端按原因**分类统计**：
`补歌词完成：成功 67 / 失败 273（280s，1.2 首/s）— 网易占位×162 · 无匹配×83 …`

**340 首全量清单落盘** `docs/no_lyric_report.txt`（TSV：原因/rel/title）：

| 三态原因 | 首数 | 占比 |
|---|---|---|
| 网易命中但占位（纯音乐/伴奏） | 162 | 47.6% |
| 两源无匹配（<0.55） | 83 | 24.4% |
| **ok（补进去了）** | **67** | **19.7%** |
| QQ命中但占位 | 16 | 4.7% |
| 无歌名 | 12 | 3.5% |

**结论**：340 残渣里 19.7% 本轮直接补进；**72% 是源站真无词**（占位 178+16），
不是 bug——清单已给全量 rel，可人工按需处理。83 首「无匹配」是元数据不准，
可用搜索页关键词手动补。

**验收**：三态 marker 3/3、端点 28/0、HTML 114358B、JS 72872ch undefined NONE、
CSS 269/269、node 0、compile 0、清单 340 行落盘、README 更新。

**坑**：后台 `run_in_background` 并行两个 pwsh job 时只建立一个（另一个静默丢）——
关键长任务必须**单独发起** + `job_list` 核对建立成功，不能依赖并行两个都成。

---

## 第33轮（闭环 R18）：maintain 首次跑完一圈 + parse_name 噪声清理

**maintain 全库扫完 `done=True`**（历史首跑）：
- 61+ 批 1518 首 678s → 歌词 +382、封面 +468
- **totals 累计 3060 歌词 / 3413 封面**（起点 27/30，全库 5188 首 → ~59% / ~66%）
- cursor 走完 `_all` 一圈，断点机制经 6 轮续跑验证（job 丢 3 次均无进度丢失）

**parse_name 噪声清理**（新 `_parse_stem` + `_NOISE_PFX/_NOISE_MARK`）：
- emoji 剥离、`【歌手】《歌名》` 括号提取、合集前缀 `盘点|精选|歌曲集|无损音质…` 剥除
- **修递归退化 bug**：分隔符分支曾递归调自己，`Fade - Alan Walker` 被二次拆成
  artist=''/title='Alan Walker'；改不递归后 7/7 单测过（`周杰伦 - 晴天`、
  `Despacito - Luis Fonsi`、`【周傳雄】《出賣》…` 全对）

**83 首「无匹配」复测（诚实结论）**：parse_name 修后 `act=fill` 仍 **0/60**——
分类是 **ID3 双缺 60 + 真冷门 21 + 残噪声 2**；60 首的「文件名」本身就是
**目录名/序号**（双叶、后摇、河北师大附中），不是歌名，搜不到属**数据边界非 bug**。
清单已给全量 rel，人工可补。

**验收**：端点 28/0、HTML 114358B、JS undefined NONE、CSS 269/269、node 0、
compile 0、maintain totals 3060/3413、README 更新。

**坑**：`parse_name` 递归剥噪声必须**只对子串做清理不再递归分隔**，否则
`歌手 - 歌名` 型文件名会退化丢 artist——单测集必须含 `A - B` 型正例。

---

## 第34轮（闭环 R19）：ID3 双缺批量修复 4805→0 + 饱和核对

**饱和核对**：reset 后第二圈 6 批 150 首全 `+0/+0`——totals **3060/3413 即全库上限**
（R18 done 后不再增长，补歌词/补封面主战场打完）。

**新能力 `/api/fixmeta` + 健康页「修ID3」按钮**（dry 预览→确认→写回）：
- `guess_meta`：title=清洗文件名，artist=**最近非通用父目录**（热门歌曲/纯音乐/下载 等上探跳过）；
  实测 `…摇滚民谣\万能青年旅店\塔吉炸.mp3` → artist=万能青年旅店 ✓
- **分批 500/片**（全库读 ID3 单请求 >120s 必超时，同 R12 health 分批坑）

**实测**：dry 11 片 265.8s 扫出 **4805 首双缺**（对上 no_artist=4802）→ 真写 201.3s
written=3308 → **复扫 todo=0，全库 ID3 双缺清零**。写完后标题/歌手回填，
后续 `act=fill` 打分不再被空元数据拖死。

**验收**：端点 **29/0**（+fixmeta）、HTML 115925B、JS undefined NONE、CSS 269/269、
marker 按钮+分批 2/2、node 0、compile 0、README 更新。

**坑（三连记录）**：① 补丁脚本文件本次也**静默没建成**（`Test-Path False`）——
**大补丁一律用 write 工具落 .py 再执行 + grep 行数核对**，pwsh here-string 写长脚本不可靠；
② 全库读 ID3 的端点必须 offset/batch 分片，否则单请求 120s+ 必超时；
③ 无 artist 的曲目占全库 92%（4805/5188），打分引擎 `_score` 的 artist 项长期空转——
修 ID3 后下轮复测 `act=fill` 命中率应显著回升。

---

## 第35轮（闭环 R20）：修 ID3 成效实测 no_artist 4802→520 + 命中率 +78%

**对照实验（修 ID3 后复测）**
| 指标 | 修前 | 修后 | 结论 |
|---|---|---|---|
| `no_artist`（deep 深扫） | 4802 | **520** | R19 写入的 TPE1 生效，仅余 520 首真无歌手（冷门曲/目录名即歌名） |
| 340 首清单 `act=fill` 命中 | 67 (19.7%) | **119 (35.0%)** | **+78%**，embedded 79 + netease 24 + qq 9 + swap 7 |
| `no_lyric`（deep） | 579 | 516 | 持续下降 |

**根因修复（health 看不到 fixmeta 写入）**：`browse.list_tracks` 的 `artists` 只解析
文件名 `" - "`，**不读 ID3**——health 判「无歌手」永远看不到 TPE1。修：`health.scan`
在 `deep` 分支用 `tagreader.read_tags`（mtime 缓存零成本）兜底 artist/title。

**设计**：维护守护 statgrid 新增 **「ID3已修」卡**（绿色高亮当 `meta_fixed>0`），
`fixmeta` 真写时把 written 累计进 `maintain_state.totals.meta_fixed`。

**验收**：deep 13 片 332.8s、`no_artist=520`、`act=fill 119/340`、
fixmeta dry todo=0、marker 3/3、端点 **29/0**、HTML 116106B、JS undefined NONE、
CSS 269/269、node 0、compile 0、README 更新。

**坑**：`edit` 工具同文件连续改必须**每次改前重读**（grep 读不算，FS 版本会判 stale）；
`browse.list_tracks` 是「文件名视图」不是「ID3 视图」——两套字段语义混用会让
上游修复静默失效于下游统计，deep 类统计一律要 ID3 兜底。

---

## 第36轮（闭环 R21）：健康分 66.8→83.9 + 两份收尾清单全量落盘

**修 ID3 成效全景（deep 深扫对照）**
| 指标 | R14 修前 | 现在 |
|---|---|---|
| 全库健康分 | 66.8 | **83.9**（+17.1） |
| no_artist | 4802 | **520** |
| no_cover | 3352 | **124** |

**修 detail 截断 bug**：`/api/health` 后端 `slim[k][:30]` 每类只回 30 条——
两份清单首导只拿到 156/307（counts 520/516）。修：`detail_limit` 参数化
（默认 30 防页面爆，清单导出传 99999），复测 **覆盖率 assert OK（detail==counts）**。

**两份收尾清单全量落盘**
- `docs/cold_no_artist.txt` — **520 首**真冷门无歌手（父目录也是通用名/文件名即歌名，人工可补 TPE1）
- `docs/missing_lyric_current.txt` — **516 首**当前缺歌词（三态上游原因见 no_lyric_report.txt）

**验收**：deep+detail_limit 全量 672s、覆盖率 assert 通过、端点 **29/0**、
HTML 116106B、JS undefined NONE、CSS 269/269、marker detail_limit、node 0、compile 0。

**坑**：`slim[:30]` 防爆截断让「清单导出」拿到的是假全量——**counts 和 detail 必须
同源同步截断**（或参数化），导出后必跑 `assert len(detail)==counts` 覆盖率核对，
否则清单静默缺 94% 还以为导全了。

---

## 第37轮（闭环 R22）：曲库卡片显示 ID3 歌手 + 批量清空队列

**根因**：`browse.list_tracks` 的 `artists` 只解析文件名 `" - "`（文件名视图）——
R19 `fixmeta` 写入的 TPE1 在曲库卡片上**显示不出来**。

**修**：`list_tracks(..., read_id3=False)` + `/api/ls?id3=1` + `openDir` 带 `id3=1`。
ID3 兜底放在**分页切片之后**只读本页（≤limit 行，mtime 缓存）——
第一版放在 os.walk 循环里对整目录 4708 文件读 ID3，`/api/ls` **180s 超时**。

**实测对照**（`万能青年旅店` 目录 35 首）：
| | id3=0 | id3=1 |
|---|---|---|
| 有歌手 | **0** | **34**（2.9s） |
| 卡片显示 | — | `万能青年旅店 · 7.5MB` ×35 |

**画面**：曲库卡片第二行现在显示 ID3 歌手（fixmeta 修复的 4805 首全库可见）；
批量页新增**「清空队列」**（关 EventSource + 清 jobbox + 禁用停止）。

**验收**：端点 **29/0**（/api/ls 不再超时）、HTML 116325B、JS undefined NONE、
CSS 269/269、marker `bclear/openDir id3/切片后` 3/3、node 0、compile 0、console 0、截图 2 张。

**坑（三连）**：① ID3 兜底这类「按文件读」的逻辑必须放在**分页切片之后**——放
walk 循环里等于每次请求全目录读，必超时（同 R12/R19 分批教训的列表视图版）；
② grep 核对实测锚前先 `read` 拿真实缩进（本处 16/0/4 空格 vs 我凭印象写的 18/6 空格，
三处 MISS）；③ E2E 下钻 `text=` 选择器对深层目录会超时，改 `evaluate('openDir(...)')` 直调。

---

## 第38轮（前端重做 R24 · 新 goal round1）：深色 AI 感 → 「唱片内页」纸白/墨黑/朱砂

**方向（两 pass 自检后定）**：现主题 `#0b0d12` 近黑+蓝紫 = AI 默认特征②「近黑+亮accent」，
正是「深色AI感」根源。按 frontend-design 主题贴合原则改走**唱片内页（liner notes）**：
纸白 `#f7f5f0` 底 / 墨黑 `#1c1a17` 字 / **朱砂 `#c4381f`** 唱片标签色 + 墨绿 `#2f4f44` 副色。
避开特征①奶油衬线+陶土、特征④ SaaS 圆角卡全套。

**改法（选择器名 0 改动，JS 绑定零影响）**
- token 重写 + 40+ 色值映射（深面→纸面、蓝紫→朱砂、深字→墨字、徽章浅底化）
- 去 AI 默认 tell：蓝紫渐变 logo→朱砂方标、统计卡渐变字→墨黑 800、
  卡片 hover 上浮→边框变墨、`body::before` 三块径向光晕→**纸纹 grain（feTurbulence）**
- 印刷感：`--radius` 10px→3px（外卡直角）、tab 选中墨底反白、chip 选中墨底、
  h1 字重 650→**800 + 负字距**、正文 13.5→14px
- 浮层（弹窗/抽屉）深玻璃→纸面+浅阴影（阴影只给浮层，面靠边框）

**验收**：截图 3 张（home/library/stats，console error 0）、端点 **29/0**、
HTML 116075B、JS undefined NONE、CSS 269/269、skin marker bg/acc/grain 3/3、
深色值残留 **grep 0**、node 0、compile 0。

**坑**：换肤补丁「MAP 色值映射先跑、STRUCT 锚后跑」→ MAP 把锚里的色值先改掉导致
STRUCT 7 锚 MISS——**结构性锚必须写在映射后的现文本上**（body::before 即此例，
改完必须 grep 旧色值残留 0 收口）。

---

## 第39轮（前端 R25 · goal round2）：版心/栅格 token 化 + 封面渲染率 0→100%

**布局 token（web-layout-creative 硬约束落地）**
- 版心四档 `--content-prose(65ch)/grid(960)/wide(1180)/full`、4px 基间距阶梯
  `--space-1..6`、栅格 `--gap:clamp(8,1.4vw,16)`、`--gap-grid`、节距 `--sect`
- `.wrap/.grid/.statgrid/.skg/.bar` 全部走 token（裸 gap:10px 清零）
- **tab 轨 → scroll-snap 横向轨道**（范式08）：`scroll-snap-type:x mandatory`
  + 子项 `scroll-snap-align:center`、触控目标 **44px**（`min-height:44px`，触控红线）

**根因修复：封面渲染率 0% → 100%**
- 症状：`/api/cover` 实测 **8/8 全 200 有图**，但页面 8 张卡片全 ♪ 占位、`img=0`
- 探针定位：`loadCoversFor(frag)` 在 `grid.appendChild(frag)` **之后**调——
  子节点已迁入 grid，**frag 此时为空**，IntersectionObserver 观察 0 个元素
- 修：`loadCoversFor(grid)`（`dataset.done` 防重取）→ 复测 **img=8 note=0 rate=100%**

**验收**：封面 8/8、端点 **29/0**、HTML 116636B、JS undefined NONE、CSS 269/269、
marker `loadCoversFor(grid)/snap/prose` 3/3、node 0、compile 0、console 0、截图 r25_covers_fixed.png。

**坑**：`appendChild(frag)` 后 frag 必空——对 DocumentFragment 的一切查询/观察必须
在 append **之前**做，或改观察目标为真正父容器；此 bug 藏了 20+ 轮（R22 封面按钮
下发阶段就该暴露），教训是**有 API 数据就要断言前端 img 数，不能只查 200**。

---

## 第40轮（前端 R26 · goal round3）：全链路连贯性 E2E + 批量目标目录 dest

**E2E v3 全绿**（搜索→批量下载→入库→元数据/播放→收藏→清理）：
`search 8 hits → job done ok=1 → lib_visible 晴天 → id3='周杰伦' → cover 200/183KB
→ stream 206 audio/mpeg → player_dom audio/pbar/plist 3/3 → fav_added True → cleanup 0`

**修 1 · 批量下载目标目录（连贯性真缺口）**：`/api/batch` 不读 `body.dest` →
`queue.run(root=)` 已支持却从没被传；首测 `skip=1` 且目标子目录空（文件落默认目录）。
修：handler 读 `dest`（`os.path.abspath` 防穿越出库）→ `q.run(root=root)`；
批量页新增「到 [目标子目录]」输入（留空=按来源分目录）。

**E2E 姿势修正（非产品 bug）**：`favs` 加歌是 **GET `act=add_multi&items=JSON`**
（前端 1795 行同款），POST `act=add` 不是这条路 → 首测 `fav_added=False` 是我调用姿势；
`lib rm` 只删空目录，清场须先 `track delete` 再 `rm`（首测 `cleanup=1` 同因）。

**验收**：E2E v3 9 项全绿、`bdest_visible=True`、端点 **29/0**、HTML 116851B、
JS undefined NONE、CSS 269/269、marker 3/3、node 0、compile 0、console 0、截图 r26_batch_dest.png。

**坑**：E2E 断言姿势必须抄产品前端真实调用（favs 是 GET+JSON query，不是 POST body）；
「rm 目录」类接口先查是删空目录还是连文件删——首测 cleanup 假红来自脚本不是代码。

---

## 第41轮（前端 R27 · goal round4）：空态引导统一三页 + 内联 onclick 引号三连修

**问题**：空态三套写法（收藏裸 `.n` / 统计 setMsg 一行 / 批量·清理页冷启动空白），
用户点进来看不到下一步。统一到 `emptyBox()` 助手（图标+标题+副文+操作指引），5 处 5/5 落盘：
收藏 `还没有收藏·点★加入·跨页保留` / 批量冷启动 `还没有下载任务`+**填关键词按钮** /
批量清空后 `队列已清空`+按钮 / 清理冷启动 `还没扫描·选比对→扫描重复·删除前预览` /
清理无重复 `✓没有重复组·临时残留N个`。

**内联 onclick 引号三连修**：JS 单引号串里塞 HTML 属性引号必炸
（`'#bkws'`→`$("..")`→`'..'` 三写法全 `missing ) after argument list`）；
终解 **属性内裸标识符** `onclick="_focusKw()"` + JS 侧 `function _focusKw(){ $('#bkws').focus() }`。

**验收**：三空态 E2E `batch/clean/fav=True`、按钮点击 `focus=bkws`、端点 **29/0**、
HTML 117425B、JS undefined NONE、CSS 269/269、marker 4/4、node 0、compile 0、console 0、截图 3 张。

**坑**：① HTML 属性 onclick 引 JS 串内字符串——**别嵌引号**，提函数 + `onclick="_fn()"` 最稳；
② E2E 收藏 `act=remove` 参数是 **`key=`** 不是 `rel=`（残留 1 条死链清场才验出空态）。

---

## 第42轮（前端 R28 · goal round5）：歌词面板冷启动引导 + 操作列 icon 化 170→116px

**歌词面板冷启动**：原来无播放时 `lyOpen()` 只 classList.add，`lybody` **空白**（点了看不到任何东西）。
修：`!curRel` 分支填引导——♪ 图标 + 「还没开始播放」+ 两行说明（逐行高亮/点词跳转）+
「没内嵌歌词点右上手动取词」；`ly_empty=True`。

**搜索表操作列 icon 化（简洁性）**：三文字按钮「试听/★/下载」占 170px →
icon `▶ ★ ⬇`（带 `title`+`aria-label`）占 **116px**，省 54px 给标题列；
`.rowops` flex 紧排 30px 触控。截图 r28_rowops.png 确认三图标渲染。

**验收**：`ly_empty=True`、表头 `[#,分,时长,来源,标题,操作]`、`opw=116px`、
端点 **29/0**、HTML 118132B、JS undefined NONE、CSS **271/271**（+rowops 对齐）、
marker 冷启动/rowops/116 3/3、node 0、compile 0、console 0、截图 2 张。

**坑**：E2E `#tb tr:first-child .rowops button` 返回 `[]` 是撞**骨架屏**（R6 同款
`skrow` 假行）——断言操作列必须 `wait_for_function` 真实行（`.rowops` 出现）或直接
以截图为证；空态/图标类改动**截图优先于 DOM 断言**。

---

## 第43轮（前端 R29 · goal round6）：tab 往返保留滚动位置 + tab 吸顶

**流畅性根因**：每次切 tab 无条件 `loadHistory/stLoad/favLoad` 整页重拉 → 滚动复位，
列表↔详情往返丢位置（违反结构硬规则4）。

**修**：`_scrollMem[p]` 离开前记 `scrollY`、回来 `_restoreScroll(p)`（rAF 回写）；
**数据在则不重拉**（`#htb/#sttb/#favlist` 有子节点/曲库 chips 在 → 只回位），首次才 load；
**tab 吸顶** `position:sticky;top:0;z-index:90`——原 tab 不吸顶，滚到 600 后
Playwright/真实用户都得先滚回顶才能点 tab，离开时 scrollY 已 0（`mem.h=0` 拿不到位置）；
`_restoreScroll` 仅 `y>0` 回写（原 `y=0` 也 `scrollTo(0)` 会清用户位置）。

**验收**：历史页往返回位 **600→600（mem=600 ✓）**、曲库 0→0（卡片不足一屏，断言盲区）、
端点 **29/0**、HTML 118911B、JS undefined NONE、CSS 271/271、marker scrollMem/restore、
node 0、compile 0、console 0、截图 r29_sticky.png。

**坑**：① E2E 滚动断言前必须先证页面够高（`scrollHeight > 目标+viewport`），
否则 scrollY 恒 0 是假通过/假失败；② 滚动交互组件要 **tab 吸顶**，否则「先滚回顶再点 tab」
把离开时 scrollY 归 0，记忆机制拿不到位置。

---

## 第44轮（前端 R30 · goal round7）：播放队列跨刷新持久化 + 清空确认流核对

**完善性缺口**：`playList/playIdx` 只存内存——刷新页面队列丢，标题/进度/队列全无。

**修**（4 处 4/4 落）：
- `_saveQueue(force)`：`localStorage['m3_queue']` 存 `rel/idx/当前秒/title/artist/list`，
  **换歌不节流(force)、timeupdate 节流 5s**；超 5MB 配额静默放弃（不阻塞播放）
- `play()` 换歌时 `_saveQueue(true)`；`audio.timeupdate` 走 `_saveQueue(false)`
- `restoreQueue()`（启动脚本）：读回队列 → **暂停态**恢复（`audio.src` 设好不 play，
  避 autoplay 策略/用户预期），`loadedmetadata` 一次回填 `currentTime`，
  提示 `已恢复上次队列 · 第 N 首（共 M 首）· 点 ▶ 续播`

**E2E 实测**：播放《城南花已开》4s → `queue rel=…三亩地 - 城南花已开 idx=0 list=8` →
**刷新** → `title='城南花已开' paused=True src=/api/stream?rel=… msg=已恢复上次队列·第1首(共8首)·点▶续播 console=0`。

**清空确认流核对**（4 处一致）：播放列表/收藏歌单/播放统计/播放历史 全有 `confirm('清空…？')`——
无需新增，本轮只补持久化。

**验收**：恢复暂停态+进度+队列全绿、端点 **29/0**、HTML 120354B、JS undefined NONE、
CSS 271/271、marker saveQueue/restoreQueue 2/2、node 0、compile 0、console 0、截图 r30_queue_restore.png。

**坑**：恢复**必须暂停态**（不自动播）——autoplay 策略会拦且用户刷完页不该突然出声；
`localStorage` 存**节流**（换歌 force、进度 5s），每 timeupdate 写一遍会把主线程写卡。

---

## 第45轮（前端 R31 · goal round8）：搜索冷启动/0结果空态 + 可点示例词闭环 + 键盘流核对

**简洁性/完善性**：搜索页冷启动与 0 结果都只留一行 `共 0 条`——新用户不知道搜什么。

**修**（2 处 2/2 落）：`emptyRows(title, sub)` + `DEMO_WORDS` 5 个可点示例词
（周杰伦 晴天 / 五月天 突然好想你 / 稻香 / 起风了 / Alan Walker Fade），`_demo()` 点词即搜；
冷启动 `搜一首歌开始·三源说明+示例词`；`renderRows(0)` `没有匹配结果+换词/含B站/示例词`。

**键盘流核对**（已有 8 键，E2E 实测）：空格/←→/↑↓/E 均衡器开/`Esc` 关/`[`/`]` 速率/`L` 歌词/`N`/`P` 上下曲——
实测 `E 开/关=True,True`、N/P 无异常、console 0。

**E2E**：冷启动 `cold=True demo=5`→点词 `rows=21`；song 模式乱码 `zero=True demo=5`→点词 `rows=17`；
端点 **29/0**、HTML 121166B、JS undefined NONE、CSS 271/271、marker 3/3、node 0、compile 0、console 0、截图 3 张。

**坑**：① `const DEMO_WORDS` 必须定义在冷启动**调用之前**（TDZ ReferenceError 炸整脚本）；
② 0 结果断言必须在 **song 模式**——all 模式下 B站歌手/MV 对乱码模糊命中 5 条是模糊匹配不是 bug。

---

## 第46轮（前端 R32 · goal round9）：移动端五档归零核对 + 播放器窄屏收纳（⋯ 更多）

**移动核对（375/390/768/1024/1440 五档）**：`hScroll` 全档 False（drawer/eqpanel 固定定位
离屏不算横向滚动条，正常）；但 **375/390 播放器按钮组 3 个被挤出视口**（`btnsOut=3`，
`.pbtns@489 > 375`）——窄屏真 bug。

**修（3 处 3/3 落）**：
- 新增 `⋯` 更多按钮（桌面隐藏）+ `.pmorebox` 弹层（歌词/播放列表/均衡器/模式/速度/关闭）
- `@media (max-width:640px)` 收纳：隐藏 `peq/plyr/plopen/prate/pmode/pclose/pvol`，
  只留 **上/播/下 + ⋯**；`.pmorebox` 绝对定位上浮 `bottom:46px`
- JS：`pcloseBtn()` + 点外部关菜单 + `aria-expanded` 开合

**E2E 复验**：
- 375/390：`btnsOut=0`（修前 3）、`visibleBtns=4`、`moreShown=True`、`⋯` 点开 `menuItems=6`
- 768：9 按钮全显示、`moreShown=False`（桌面形态保留）
- 五档 `hScroll=False`、console 0、端点 **29/0**、HTML 123264B、JS undefined NONE、
  CSS 281/281、marker pmore/收纳CSS/JS 3/3、node 0、compile 0、截图 r32_more_375.png。

**坑**：① 移动核对的 `over` 计数会把**固定定位离屏抽屉**（plist/eqpanel translateX(100%)）
算成溢出——真信号看 `documentElement.scrollWidth > clientWidth`；
② 窄屏收纳判按钮出视口必须在**播放启动后**量（idle 态按钮隐藏会假通过）。

---

## 第47轮（前端 R33 · goal round10）：播放器键盘流 + role=toolbar + ⋯ 弹层 Esc 回焦点

**可访问性缺口**：`.pbtn` 全是 **div**（无 tabindex/role）——**Tab 根本到不了播放器按钮**，
键盘用户按不了 ⋯ 更多；Esc 关弹层焦点丢失。

**修**（2/2）：
- `player` 加 `role="toolbar" aria-label="播放器控制条"`（WAI-ARIA toolbar 语义）
- `_makeFocusablePbtns()`：10 个 `.pbtn` 全补 `role=button tabindex=0`，
  `Enter/Space` 激活（**`stopPropagation` 拦全局空格=播放**，走当前聚焦钮）；
  ⋯ 内 Enter 后自动把焦点送进弹层首项
- ⋯ 弹层 `Esc` 关闭 + `aria-expanded=false` + **焦点还给 ⋯**（menu role 合规）

**E2E 实测**：`toolbar=toolbar`、`pbtn_focusable=10`、`rolebtn=10`、
`Tab 19 次到达 ⋯`、`Enter 开=True expanded=true`、`Esc 关=True focus_back=pmore`、
`Space 开=True`、console 0；端点 **29/0**、HTML 124199B、JS undefined NONE、
CSS 281/281、marker toolbar/focusable/esc 3/3、node 0、compile 0、截图 r33_kbd.png。

**坑**：div 按钮必须 `role=button + tabindex` 才进 Tab 序；pbtn 内 Enter/Space 要
`preventDefault+stopPropagation`——否则全局空格（播放/暂停）抢跑，焦点钮点不着。

---

## 第48轮（前端 R34 · goal round11）：关于弹窗快捷键速查 + color-scheme:light 深色回退核对

**完善性**：11 个快捷键（Space/←→/↑↓/N/P/L/E/[/]/Esc/Tab/⋯）**没有任何帮助面**——
`Esc 关闭`提示只在歌词面板一处。关于弹窗新增**快捷键速查卡**（`mrow` 分组、
`.kbd` 键帽排版、三行 11 键 + 窄屏 ⋯ 收纳说明）。

**画面 bug（深色回退核对）**：主题是浅色「唱片内页」，但 `:root` 没有 `color-scheme`——
**系统开深色模式时浏览器把原生控件（checkbox/select/scrollbar）套深色**，
与纸白皮撕裂。修：`:root{color-scheme:light}` 显式声明。
`emulateMedia(colorScheme=dark)` 实测 `bodyBG=rgb(247,245,240)` 纸白保持、`color-scheme='light'`。

**验收**：快捷键速查 `=True`（Space/Tab/⋯ 三关键词全中）、端点 **29/0**、
HTML 125067B、JS undefined NONE、CSS 281/281、marker colorScheme/速查 2/2、
node 0、compile 0、console 0、截图 r34_about_kbd.png。

**坑**：单行 grep `快捷键.*Space` 跨行匹配必 0——HTML 落盘核对用 **E2E 断言文本**（`textContent.includes`）别用单行正则；
浅色主题**必须** `color-scheme:light`，否则系统深色模式下原生控件反色撕裂（藏到 E2E 模拟才发现）。

---

## 第49轮（前端 R35 · goal round12）：统计卡数字滚动（单次编排）+ 4708 归档长列表滚动采样

**画面**：维护统计 5 卡数字 `countUp()`——**单次编排**（前端准则：动效只留一处回应「值已载入」），
ease-out cubic 500ms；`prefers-reduced-motion` 直落终值。
E2E：中途 `['63','866','966','0','0']` → 末 `['224','3060','3413','0','0']`（中途<末=True）；
reduced-motion 150ms 即终值 `['224','3060','3413',...]`。

**流畅性（4708 归档长列表采样）**：切曲库 tab + 先证页面够高（`docH 2409 > viewport`）→
16 次 wheel：**card 60 → 1020（+960，16 次 60/批稳定续批）**、`scrollY 1509→30187`、
`docH 1156→32865`、17.1s、帧序 `[120,180,240,300,360,420]` 无跳批、console 0。

**验收**：数字滚动/减动效双分支 + 长列表续批全绿、端点 **29/0**、HTML 125864B、
JS undefined NONE、CSS 281/281、marker countUp、node 0、compile 0、截图 2 张。

**坑（同 R29 二连）**：长列表采样**停在清理 tab** 时 `60→60 docH=1156` 假阴——
隐藏 pane 里 IntersectionObserver 不触发、wheel 滚的是清理页；**先切到目标 tab + 证 `scrollHeight>viewport`** 再滚；
减动效 `reduced_motion=reduce` 必须单页测（page 一次设置），marker 字符串多括号 grep 易 0 假红。

---

## 第50轮（前端 R36 · goal round13）：触屏可交互硬伤修复 + 健康分 hero 破格大数字

**触屏硬伤**（可交互红线）：`.cardops`（改名/删除）**hover-only 揭示**——触屏无 hover，
按钮 `opacity:0` 永不可达；`.cop` 26×26、`.rowops` 按钮 <44px 不达触控红线。
修：`@media (hover:none)` 下 `cardops` **常驻可见** + `.cop` 44×44、`.rowops` 44px、
`.lrow/.plitem min-height:48px`。E2E（390×844 `hasTouch=true`）：`cardops op=1 w=92 h=44`、
`cop 44×44`——红线达标。

**健康分 hero（破格 · 范式15 超大字）**：核心指标「全库健康分」原先只挤在 5 卡里一个 `.v`。
挂 `hresult` 顶部 hero 卡：`clamp(3.2rem,7vw,5.5rem)` 大数字 + 小标签 `全库健康分` +
`快速/深度扫描 · 5188 首 · 36545.9 MB` + 左侧状态竖条（≥90 ok / 70-90 warn / <70 bad）。
E2E：`score=77.1 cls=hero-mid fs=88 color=rgb(150,101,10)`、截图 r36_hero.png 确认 88px 琥珀大数。

**验收**：触屏红线 + hero 渲染双绿、端点 **29/0**、HTML 127636B、JS undefined NONE、
CSS 299/299、marker hover-none/heroCSS/heroJS 3/3、node 0、compile 0、console 0、截图 2 张。

**坑**：hover-only 揭示的按钮**触屏是死的**——`opacity:0` 且无 hover 事件，必须
`@media(hover:none)` 常驻显示 + 44px；hero 断言要量 `fontSize`（88px）而非只看文本在。

---

## 第51轮（前端 R37 · goal round14）：卡片热区审计 + 搜索表行密度

**热区审计（E2E 4 断言全绿）**：卡片内部按钮是否冒烟到播放、点卡片主体是否正确触发播放：
- `点改名✎` → `ren_no_play=True`（`stopPropagation` 生效，curRel 不变）
- `点卡片标题` → `body_plays=True player_on=True`（正确触发播放）
- `播放中点删除×`（dismiss 确认）→ `alive=True`（页面不崩）
- console 0

**行密度（简洁性）**：`th,td` 9→**11px** 垂直（触控密度），全选列 30→38px；
`tr_h=61`（原 ~57，仍紧凑）。

**验收**：热区 4/4 + 端点 **29/0**、HTML 127637B、JS undefined NONE、CSS 299/299、
marker 行密度/stopProp、node 0、compile 0、console 0、截图 r37_hotzone.png。

**坑**：E2E `#tb tbody tr` 选择器不对——**`#tb` 本身就是 tbody**（应 `#tb tr`）；
行高断言撞骨架屏前须 `wait_for_selector('#tb tr td .src')` 等真行。

---

## 第52轮（前端 R38 · goal round15）：历史时间列相对时间化 relTime

**简洁性**：历史表时间列原 `MM-DD HH:mm`（还得心算「3 天前是哪天」）。

**修**：`relTime(at)` 6 档（刚刚/N 分钟前/N 小时前/昨天/N 天前/N 个月前/N 年前）+
`absTime` 挂 `title` 悬浮显绝对时间（首读少一步心算、要精确仍可达）。

**E2E**：relTime 单元 6 档全对（`刚刚/5 分钟前/3 小时前/3 天前/2 个月前/1 年前`）；
历史列 `['16 分钟前','3 小时前','2 天前',...]`、`title=['2026/11/24 05:00:03',...]`、
**旧格式残留=False**、console 0；端点 **29/0**、HTML 128456B、JS undefined NONE、
CSS 299/299、node 0、compile 0、截图 r38_hist_reltime.png。

**坑**：补丁里 `\d{4}` 转义层数要数对（pwsh here-string + py str 双层，
错一层锚 MISS）——复杂锚改用 **read 出现文本 + edit 精确替换**最稳；
本轮又遇占位工具名/输出被吞，照规矩逐个单发重跑。

---

## 第53轮（前端 R39 · goal round16）：曲库目录面包屑 + 子目录下钻

**连贯性真缺口**：`/api/ls` 只在 `sub=""` 时返回根层 dirs——点「_归档_封存」后 4708 首全量平铺，
**无子目录下钻、无位置回跳**（E2E 全靠 `openDir(多级路径)` 直调绕过，UI 根本到不了深层）。

**修**：
- 后端 `/api/ls` 始终带 `dirs`（空 sub=根层、非空=该层子目录，`browse.list_dirs(os.path.join(ROOT, sub))`）。
- 前端 `_libPage` **透传 `dirs`**（原只挑 `items/got` 把 `d.dirs` 丢了——`subDirs` 恒 null 是第一处假象根因）。
- `openDir` 首轮捕获 `subDirs` → 重画 chips：`⤴ 返回上级` + 该层子目录（带 count）。
- 面包屑 `#crumbs`（`曲库 › 归档 › SD卡版`，每段 `openDir(前缀)` 可点回跳、末段粗体）+ 根层「全部目录」。

**E2E**：`下钻 chips=37 back=True`（头 4=`[⤴返回上级, SD卡版 1495, 万能青年旅店 52, 五月天 31]`）、
`ls dirs(非空sub)=36`、点上级回 `全部目录`、面包屑断言 True、端点 **29/0**、
HTML 130203B、JS undefined NONE、CSS 304/304、marker 2/2、node 0、console 0、截图 r39_drill.png。

**坑**：① `_libPage` 丢弃 `d.dirs` 是下钻不画的根因——**接口返回体必须逐字段透传**，少一个字段前端就拿到 undefined；
② 面包屑分隔用 `/[\\/]+/` 要数对反斜杠层数；③ 目录 chip `data-n` 拼接用 `'\\'`（py str 双层）。

---

## 第54轮（前端 R40 · goal round17）：标题栏信息密度 — sub 总计数 + Star 去重

**简洁性**：标题栏 `sub` 原 `loadStat` 把 `/api/stat` 全 key dump 到首屏（`投稿 480 · _归档_封存 4708`
逐目录列）——**目录细节本就该在曲库页**，首屏给的是单一总数。改：
`B站 / 网易云 / QQ音乐 · 全库 5188 首`（`/api/stat` 保持 per-dir 返回，维护/统计页不受影响）。

**Star 去重**：`⭐ Star` 同时在标题栏与关于弹窗 `gostar`——标题栏删（HTML/绑定/CSS 三处清干净），
关于弹窗留唯一入口。右分组从 3 枚收敛到 2 枚（设置/关于），与 7 tab 左区松紧平衡。

**验收**：E2E `sub='B站 / 网易云 / QQ音乐 · 全库 5188 首'`、`标题栏 star=False btns=['设置','关于']`、
`关于弹窗 mstar=True`（⭐ 点个 Star 支持一下）、star 残留 0、端点 **29/0**、
HTML 129922B、JS undefined NONE、CSS 302/302、node 0、compile 0、console 0、截图 r40_header.png。

**坑**：删 CSS 要连 `.star-btn` 与 `.star-btn:hover` 两条一起删（hover 变体漏删留僵尸规则）；
`sub` 改总计数后**别动 `/api/stat` 返回结构**（维护页 5 卡还在用 per-dir）。

---

## 第55轮（前端 R41 · goal round18）：维护游标全库续推 + 5 卡同步验收

**完善性（backlog 续推）**：全库补歌词/补封面游标（`maintain.tick` batch=20 × 6 轮，全库 sub 空）：
- before `totals {lyric:3060, cover:3413}` → after `{lyric:3063, cover:3413}`（歌词 +3，本轮窗口内 3 首命中）
- `runs 224→230`、cursor 快照推进到 `_归档_封存\SD卡版\thisistruemusic\英文歌\I LOVE U - 002lWTZR2zfSFX.mp3`
- 6 轮 21.6s，`done=False`（全库 5188 还没跑完一圈，游标断点已存盘 `_mt_state.json`，下次续推）

**5 卡同步**（画面连贯）：维护页点「看状态」后 `.statcard .v` = `['230','3063','3413','0','0']`，
与 `after totals` 逐字相等（R35 countUp 滚到的终值 = 后端 status，**前端 5 卡与后端游标零漂移**）。

**验收**：游标推进断言 True、5 卡同步 True、端点 **29/0**、HTML 129922B、JS undefined NONE、
CSS 302/302、node 0、console 0、截图 r41_maint.png。

**坑**：`tick` 是外部 API 限速的（一轮 20 首 ~3s），全库一圈约 260 轮；**游标存盘 + 断点**是唯一的
续推通道（`reset_cursor` 会从零再来）——R41 只推 6 轮留余量，别一次 tick 到 `done`。

---

## 第56轮（前端 R42 · goal round19）：修ID3 快速估算（500 采样外推）

**流畅性**：点「修ID3」原流程 = **全量 236s dry 扫**（5188 首逐首读 ID3）才确认 → 0 双缺时白等 4 分钟。

**修**：`/api/fixmeta?estimate=1` 快估（**只读首片 500 首**，`todo_est = len(todo) × total_all / scanned` 外推）
+ `sample_seconds`（采样耗时，估「精确全扫约需 N 分钟」）；前端「修ID3」先快估：
- 估 0 → **秒级收尾**「估算：没有 ID3 双缺曲目（500 采样外推 0 / 5188 首）」，不跑全扫
- 估 >0 → confirm「精确全扫约需 N 分钟」再走原全扫/写入流程

**验收**：estimate 接口 `todo_est=0 total_all=5188 sample_seconds=0.7`（首次 26.8s 读 ID3 后**缓存命中**，复测 0.7s）、
UI 快估终态 0.9s「估算：没有 ID3 双缺」`cls=msg ok`、端点 **29/0**、HTML 130675B、
JS undefined NONE、CSS 302/302、node 0、console 0、截图 r42_fixmeta_final.png。

**坑**：① estimate 外推写 `todo * total_all` 忘 `len(todo)`（todo 是 list）→ `TypeError: list * int`，
handler 报 500（`/api/fixmeta?estimate=1` 200 前必须过 `len()` 关）② 前端快估断言等**终态**文案
「估算：没有 ID3 双缺」，**不能**匹配中间态占位「快速估算（500 采样外推）…」（0.1s 假绿）。

---

## 第57轮（前端 R43 · goal round20）：维护游标续推 + ID3 卡「已核」语义 + 快估缓存

**完善性（backlog 续推）**：全库游标 8 批 batch=20（lyric+cover）：
`lyric 3063→3064 · runs 230→238`，断点推进到 `英文歌\Улетали птицы гордыми.mp3`，17.7s。

**ID3 卡语义（完善性）**：`meta_fixed` 恒 0 因全库本就 0 双缺（R42 快估 `todo_est=0`），
卡片原显「ID3已修 0」语义误导（像「没修过」）。改：`meta_fixed=0 且快估 0 双缺` →
卡显 **`ID3 双缺（5188 首）= 已核`**（muted ink，`countUp` 跳非数值卡）；有值时原绿字。

**快估缓存（流畅性）**：`/api/fixmeta?estimate=1` 冷读 ID3 ~26s，挂 `window._id3estCache` 60s 窗口：
首点冷 19.6s → 二点 **1.27s**（缓存命中），`mtStat` 5 卡渲染不再被 estimate 卡住。

**验收**：首点冷 19.6s 出「ID3 双缺（5188 首）=已核」、二点缓存 1.27s 同卡、
`runs/lyric/cover 三卡与后端 status 逐字同步`（用二点终值断言，冷点中段是 countUp 未到）、
端点 **29/0**、HTML 131421B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r43_id3card.png。

**坑**：① estimate 外推 `todo * total_all` 忘 `len(todo)` → `list * int` TypeError 500（R42 已修）
② 5 卡同步断言要用**二点缓存终值**（c2），冷点首帧（c1）是 countUp 500ms 编排中段，`endswith` 假红
③ `mtStat` 内挂 estimate 必须带 60s 缓存，否则每次看状态卡 26s。

---

## 第58轮（前端 R44 · goal round21）：ID3 卡 tooltip + `meta_fixed>0` 分支回归

**完善性（卡片语义双分支坐实）**：R43 只验过「已核」负分支，`meta_fixed>0` 绿字分支从未实测。
用 state 文件构造 `meta_fixed=7` 临时回归（备份→改→验→**还原**，`_cache/maintain_state.json` 现 `meta_fixed=None`）：
- **正分支**：卡 `k='ID3已修' v='7' color=rgb(47,125,85)(--ok)`、tooltip `累计已写回 7 首 ID3 双缺（标题←文件名 · 歌手←父目录）`
- **负分支**（还原后终态）：`k='ID3 双缺（5188 首）' v='已核' color=rgb(119,112,106)(--dim)`、
  tooltip **`500 采样外推 0 双缺 / 5188 首 · 采样 0.8s（悬停看证据）`**（estimate 证据直接挂卡）

**完善性（backlog 续推）**：全库游标再推 8 批 batch=20：`cover 3413→3415 · runs 246`，
断点 `华语经典\周杰伦\时光机.mp3`（`lyric 3064` 窗口内全命中已补，0 新增）。

**验收**：双分支断言全绿（正/负各 1）、state 还原 `meta_fixed=None`、端点 **29/0**、
HTML 131611B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r44_id3tooltip.png。

**坑**：① 5 卡同步/还原断言要 `wait_for_selector('.v:has-text("已核")')` **等终态**（短等读到 mtStat 未跑完的旧卡）
② 颜色断言用 `--ok/#1f6b46` 要取 `rgb(47,125,85)`（色标近似，别按 hex 直写 rgb）
③ 改 `_cache/maintain_state.json` 做回归必备份还原（`bak_r44` 清干净），否则 5 卡被永久钉在假 7。

---

## 第59轮（前端 R45 · goal round22）：封面缓存落盘透明化 + 维护页缓存快照行

**完善性**：`covercache.get_cover` 早有落盘机制（`_cache/covers/<md5(path|size|mtime)>.jpg`，
路径+mtime 做 key，文件换自动失效；无封面写 `.none` 标记免反复解 ID3）——但**全库缓存体量无人看**
（`_cache/covers/` 已 571 张 / 356.8 MB，只有 `/api/cache` 接口裸着没人用）。

**修**：维护页「看状态」5 卡下方挂**缓存快照行**：
`封面缓存: 571 张 · 356.8 MB（_cache/covers，命中免解 ID3）`（`/api/cache` files/bytes，mtStat 内联拉取）。

**E2E**：曲库 openDir 后 `.cardcov img` = 8（封面 100% 命中渲染，**新增 0 张**——已缓存全命中，
`cache before/after` 都是 571/374102746 坐实「命中免解 ID3」语义）；维护页快照行与 `/api/cache` 逐字一致；
端点 **29/0**、HTML 131966B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r45_cache.png。

**坑**：① 封面 img 选择器是 **`.cardcov img`**（`#grid img[src*=cover]` 0 匹配——src 是 blob: 不是 /api/cover）
② 缓存「增长」断言在基线已满（571）时恒 0——改断言 `基线>=500 且 grid imgs>0`，新增 delta 只作记录。

---

## 第60轮（前端 R46 · goal round23）：双缓存透明化（封面+歌词）+ 清缓存按钮

**完善性（缓存双面）**：`/api/cache` 原来只报封面；实际 `lyricfill` 也有对称落盘
（`_cache/lyrics/<md5>.lrc`，**3208 条 / 7.8 MB**，命中免联网查歌词）。改 `/api/cache` 返回
`{covers:{files,bytes}, lyrics:{files,bytes}}` 双缓存 + `clear_all=1` 双清（`clear=1` 保留只清封面）。

**简洁性（维护页操作面）**：R45 快照行升级为**双缓存 + 「清缓存」按钮**：
`封面缓存 572 张 · 356.8 MB  歌词缓存 3208 条 · 7.8 MB [清缓存]`
（confirm 文案写清「文件本身不动, 只清 _cache」）。

**E2E 全链路**：清前 `572+3208` → 点清缓存 → **双 0**（API + 页面快照同步）→ 开库重建
`covers 8 张`；`lyrics 补回 0` 是**预期行为**——清掉的 3208 条对应曲目 ID3 已内嵌歌词，
`fill_one` 走 `embedded` 分支跳过 `save_cached`，歌词缓存只在「新补成功」时重建（渐进），
5 卡 `lyric=3064` 证明词在文件内，**清缓存安全**。
端点 **29/0**、HTML 132808B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r46_cache2.png。

**坑**：① 歌词缓存 0 条 ≠ 坏——「嵌入优先」架构下它是加速层不是唯一真相，断言别写「清后必须回填 N 条」
② `confirm` 弹窗 E2E 要 `p.on("dialog", accept)` 放行，否则清缓存按钮点了无下文。

---

## 第61轮（前端 R47 · goal round24）：preview 双段计时 + 试听缓存反馈

**流畅性（缓存透明化）**：`/api/preview` 原来 `use_cache=True` 白开——用户看不见秒回来源。
拆两段计时回传：`search_ms`（router.search 路由查段）+ `total_ms`（含 get_url 取链全程）
+ `cached`（search_ms<300 判命中）。试听反馈文案双段：
`搜索缓存 0.0s / 全程 0.1s` 或 `搜索冷查 1.4s / 全程 1.5s`。

**E2E**：`稻香` 冷 `search_ms=772 total_ms=2567 cached=False` → 热 `search_ms=0 total_ms=115 cached=True`
（**搜索段 160×**，全程仍 ~1s 因 get_url 每次取链——诚实标「全程」不冒充全快）；
UI 试听文案双段反馈绿；端点 **29/0**、HTML 133136B、JS undefined NONE、CSS 302/302、node 0、console 0、
截图 r47_preview_ui2.png。

**坑**：① `elapsed_ms` 量全程会混进 get_url 网络段——cached 误判冷查（「热 0.123s」其实是取链快，
搜索段要单量 `search_ms`）② UI 点 `.src` 列读到搜索摘要不是预听——预听按钮在操作列
`#tb tr .rowops button`（R28 rowops 116px 三钮 ▶★⬇ 的第一个）。

---

## 第62轮（前端 R48 · goal round25）：about 弹窗坑计数动态化（脱 46 硬编码）

**简洁性（自维护数字）**：about 弹窗「46 条踩坑记录」是 R34 硬编码的，48 轮后早已失实
（实际 40 坑节 / 48 轮 / 52 提交）。改**动态**：新增 `/api/about` 扫 `README.md` 累加坑
（含 `**坑**：` 与 `**坑（…）**：` 双变体、`×N` 计 N）+ 轮数（`^## 第\d+轮`）
+ `git rev-list --count HEAD` 提交数；`aboutOpen()` 打开弹窗时 fetch 填充
`#mnotePits/#mnoteRounds/#mnoteCommits`，占位「46」只在请求失败时兜底。

**E2E**：`/api/about` `{pits:40, rounds:48, commits:52}` 与离线 `re` 逐字一致；
弹窗动态值 `40/48/52` 全同步、**脱 46**；端点 **30/0**（新基线：`/api/about` 入列，
skip 6 后总数 34）、HTML 133516B、JS undefined NONE、CSS 302/302、node 0、console 0、
截图 r48_about.png。

**坑**：① 坑正则 `\*\*坑\*\*[:：]` 漏 `**坑（双杀）**：` 变体（4/40）→ 放宽 `\*\*坑[^*]*\*\*[:：]` 全收 40
② 端点基线 29→**30**（R48 起含 `/api/about`），后续轮全量循环按 34 总数 / 30 可测断。

---

## 第63轮（前端 R49 · goal round26）：preview 取链落盘 TTL 缓存（`_cache` 根）+ 双缓存反馈

**流畅性（取链秒回）**：R47 只做搜索段缓存，`get_url` 取链（vkey+Range 校验）每次 ~1.4s。
改 `/api/preview`：取链前查 `_cache/qq_<mid>.json`（`{url,ext,exp}`，TTL 1800s），
**命中免 `src_qq.get_url`/`src_netease.get_url`**，直返 `url_cached=True`；未命中取完写回。
试听反馈三段：`搜索缓存 0.0s · 取链缓存 / 全程 0.0s`。

**E2E**：`光年之外` 冷 `url_cached=False total=1522ms` → 热 **`url_cached=True total=14ms`
（108×）**；稳态连 2 调都 14ms；落盘 `_cache/qq_*.json` 1 个（`cache_dir` 直配 `_cache` 根，
非 `previews/` 子目录——config 值赢过代码默认路径）；UI 连点文案含「取链缓存」；
端点 **30/0**（含 `/api/about`）、HTML 133495B、JS undefined NONE、CSS 302/302、node 0、
console 0、截图 r49_urlcache.png。

**完善性（游标续推）**：全库 8 批 batch=20 `runs 252→260`，断点 `华语经典\邓紫棋\新的心跳.mp3`
（本窗 lyric/cover 全已补 0 新增）。

**坑**：① 取链缓存落 `_cache` 根不是 `_cache/previews/`——`cache_dir` config 值直接指 `_cache`，
`_PV_DIR=cache_dir` 无 `previews` 后缀（代码默认路径被 config 覆盖）
② R49 首验脚本查 `_cache/previews` 0 个（路径错）；playwright `Browser.close` 偶发
`Connection closed while reading from driver`——清残留 chrome 后重跑即过。

---

## 第64轮（前端 R50 · goal round27）：三缓存收编（封面+歌词+取链）+ 清缓存全清

**简洁性（缓存操作面收敛）**：R46 双缓存 + R49 取链缓存各自为政。改 `/api/cache` 统一报
**三缓存**：`{covers:{files,bytes}, lyrics:{files,bytes}, previews:{files}}`；
`clear_all=1` 收编取链（清 `_cache/qq_*.json`+`netease_*.json`），回 `cleared_previews`。

**完善性**：维护页快照行升级**三面**：
`封面缓存 15 张 · 0.9 MB  歌词缓存 0 条 · 0.0 MB  取链缓存 1 条 [清缓存]`
（清缓存 confirm 文案 + 成功回执都带上取链数）。

**E2E**：清前 `covers 15 + lyrics 0 + previews 1` → `clear_all` → `cleared_covers 15 · cleared_lyrics 0 · cleared_previews 1`
→ 清后三全 0；维护页快照三面同步 0；端点 **30/0**、HTML 133609B、JS undefined NONE、
CSS 302/302、node 0、console 0、截图 r50_3cache.png。

**完善性（游标续推）**：全库 8 批 batch=20 `cover 3415→3417 · runs 268`，
断点 `摇滚民谣\万能青年旅店\狗尿馆.mp3`。

**坑**：`previews` 取链缓存落 `_cache` 根（`cache_dir` config 值），清要用 glob `qq_*.json/netease_*.json`，
不是子目录（R49 已证）。

---

## 第65轮（前端 R51 · goal round28）：缓存占比行（缓存体积/全库体积）+ previews 带 bytes

**完善性（缓存健康度）**：`/api/cache` `previews` 加 `bytes`（取链缓存也有体积）；维护页
5 卡 + 快照行下挂**占比行**：`缓存共 X MB · 占全库 36548 MB / 5188 首的 0.0%（缓存仅加速，清掉无损）`。
全库体积优先吃 `window._health`（health tab 已扫过免重扫），否则 fetch `/api/health`（`total_size_mb`）
——`/api/stat` 只有每目录计数**没有体积**，不能用它算占比。

**E2E**：`previews {files:1,bytes:284}` 形状正；占比行含 `全库 36548 MB / 5188 首` 绿；
端点 **30/0**、HTML 134493B、JS undefined NONE、CSS 302/302、node 0、console 0、
截图 r51_cacheratio.png。

**完善性（游标续推）**：全库 8 批 batch=20 `lyric 3064→3067 · cover 3417→3419 · runs 276`，
断点 `摇滚民谣\草东没有派对\模样.mp3`。

**坑**：① `/api/stat` 返回 `{_归档_封存:N, 投稿:N}` **只有计数无体积**——占比必须走 `/api/health`
的 `total_size_mb`（`/api/stat.sum_mb` 是假想字段，前端取到 undefined→NaN）
② `_pv_stats` 改返 `{files,bytes}` 后，`/api/cache` 返回面 `previews:{files:_pv_stats()}` 漏改
→ 嵌套成 `{files:{files,bytes}}`（R50 形状是标量，R51 升级字典必须同步改调用处）
③ 服务偶发拒连（ThreadingHTTPServer 单 handler 被 health 深扫占满？requests 连 127.0.0.1 仍拒）
→ 验脚本加**连接重试 4×3s**，别一次拒连就整轮报废。

---

## 第66轮（前端 R52 · goal round29）：取链命中计数 + 维护页「缓存（三合）」第 6 卡

**完善性（缓存可量化）**：R49 取链缓存只落盘没记命中——缓存好不好用看不见。加模块级
`_PV_HITS`（`/api/preview` 命中时 `+=1`，进程内、重启归 0）+ `/api/cache` `previews.hits`。
维护页 5 卡升**6 卡**：第 6 卡 `缓存（三合·命中 N）= 总条数`
（`covers+lyrics+previews` 条数，tooltip 拆 `封面 X + 歌词 Y + 取链 Z；本进程取链命中 N 次`）。

**E2E**：预热取链 3 调（首写+2 命中）→ `/api/cache` `previews {files:2, bytes:566, hits:2}`；
维护页 6 卡 `['已跑轮次 284','累计补歌词 3070','累计补封面 3422','累计清理 0','ID3 双缺（5188 首）已核','缓存（三合·命中 2）11']`；
端点 **30/0**、HTML 134876B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r52_cachecard.png。

**完善性（游标续推）**：全库 8 批 batch=20 `lyric 3067→3070 · cover 3419→3422 · runs 284`，
断点 `洛天依\洛天依\周边.mp3`。

**坑**：命中计数是**进程内**（`_PV_HITS` 模块级）——服务重启归 0，`hits` 只反映本进程，
文案标「本进程」免误导；卡片条数 `11 = covers 6 + lyrics 3 + previews 2`。

---

## 第67轮（前端 R53 · goal round30）：取链命中计数落盘（重启不归 0）

**完善性（命中可追溯）**：R52 的 `_PV_HITS` 是进程内（重启归 0），「缓存好不好用」重启就丢。
改**落盘**：`_cache/pv_hits.json` 存累计命中，启动 `_pv_load_hits()` 读回、命中 `_pv_on_hit()`
内存 +1 标脏、`_pv_flush_hits()` 节流 1s 写盘（高频命中不刷 IO）；`/api/cache` 读时刷一次脏
保 `previews.hits` 准。第 6 卡 tooltip 改「取链**累计**命中 N 次（落盘, 重启不归 0）」。

**E2E**：`夜曲` 3 调（首写+2 命中）→ `pv_hits.json` 落 `2`；**重启服务** → `/api/cache`
`previews {files:3, hits:2}` 读回**不归 0**；维护页 6 卡 `缓存（三合·命中 2）=16`；
端点 **30/0**、HTML 134887B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r53_hitsdisk.png。

**完善性（游标续推）**：全库 8 批 batch=20 `lyric 3070→3073 · cover 3422→3425 · runs 292`，
断点 `万能青年旅店\在在在.mp3`。

**坑**：命中写盘要**节流**（`_PV_HITS_LAST_FLUSH` 1s 门限）——试听连点命中高频，逐命中
`open+write` 会刷爆 `_cache` 小文件 IO；`/api/cache` 读时 `_pv_flush_hits()` 兜一次脏防丢。

---

## 第68轮（前端 R54 · goal round31）：清缓存收编命中计数 + 占比行累计命中标

**完善性（清缓存语义闭环）**：R53 命中计数落盘 `pv_hits.json`，但「清缓存」只清三类缓存文件、
不碰命中计数——清了缓存 `hits` 还挂着旧值，自相矛盾。加模块级 `_pv_reset_hits()`
（删 `pv_hits.json` + 内存 `_PV_HITS=0` + 清脏），`clear_all=1` 收编它、回 `cleared_hits:1`；
清缓存回执文案补「命中计数已清」。

**简洁性**：占比行尾部加「取链累计命中 N 次（清缓存连同命中计数一起清）」——命中数与清语义一处看全。

**E2E**：预热 `hits=4 + pv_hits.json 存在` → `clear_all` 回 `{covers:5, lyrics:10, previews:4, cleared_hits:1}`
→ 清后 `previews {files:0, hits:0} + pv_hits.json 已删`；占比行含「取链累计命中 0 次（清缓存连同命中计数一起清）」；
端点 **30/0**、HTML 134953B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r54_hitclear.png。

**完善性（游标破 300 大关）**：全库 8 批 batch=20 `lyric 3073→3074 · cover 3425→3427 · runs 300`，
断点 `周杰伦\一路向北.mp3`。

**坑**：清缓存必须**连命中计数一起清**（`_pv_reset_hits` 删文件 + 归 0 + 清脏）——只清三类缓存文件
留 `hits` 旧值会让「缓存 0 条但命中 N 次」自相矛盾（用户以为缓存还在）。

---

## 第69轮（前端 R55 · goal round32）：runs 里程碑刻度 + 全库体积 GB 换算 + 修 mtStat 静默断链

**完善性（里程碑）**：维护页「已跑轮次」卡加**里程碑刻度**（tooltip「维护 tick 累计；里程碑 300/350」，
`runs≥300` 时值变绿 `var(--ok)`）——runs 破 300 后一眼看见「到刻度了」。

**简洁性**：占比行全库体积加 GB 换算：`36560 MB（≈35.7 GB）`（`libMB≥1024` 才显示，免小库噪声）。

**完善性（游标）**：全库 8 批 batch=20 `runs 300→308`，断点 `宋冬野\无题.mp3`（lyric/cover 本批 0 补——
尾部全是嵌入型，加速层只长新补）。

**E2E**：6 卡全出（含 runs 里程碑 + 缓存三合）、`runs=308` 绿 `rgb(47,125,85)`、占比行 `≈35.7 GB` 绿；
端点 **30/0**、HTML 135121B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r55_milestone.png。

**坑（本轮最大）**：R55 给 runs 卡 tooltip 写 `${b||20}`——`b` 是 `mtRun` 局部变量，**mtStat 作用域没有**
→ `ReferenceError` 被 mtStat 外层 `catch(e){}` **静默吞掉** → `$('#mtresult').innerHTML` 赋值整个没执行
→ **0 卡 + mtcacheclr 不出现**（E2E 卡死 240s）。逐段打点（hook fetch 看只发了 maintain+fixmeta 两个
请求、无后续）才定位。修：tooltip 用字面量 `20`，不跨作用域引变量。
教训：mtStat 外层 `catch(e){}` 吞一切——**改 5 卡 HTML 时引入未定义变量 = 整块静默断链**，
E2E 必须断「6 卡都在」而非只等一个选择器。

---

## 第70轮（前端 R56 · goal round33）：runs 下一里程碑进度条 + 取链命中率（hits/calls）

**完善性（里程碑可视化）**：「已跑轮次」卡加**下一里程碑进度条**（350 为满刻度，`runs/350` 百分比，
`<350` 走 `var(--acc)`、`≥350` 变绿；tooltip「下一里程碑 350 还差 N」）——runs 316 时条走 90% 一眼到。

**完善性（命中率）**：R53 只报命中数、没分母。加 `_PV_CALLS`（每次 `/api/preview` 取链段 +1，
进程内）+ `/api/cache` `previews.{calls, hit_rate}`；占比行 + 第 6 卡 tooltip 都显 `取链命中 H/C（命中率 R%）`。

**E2E**：预热 6 调 → `previews {files:3, hits:5, calls:6, hit_rate:83}`；runs 卡 `316` 进度条 90%、
tooltip「下一里程碑 350 还差 34」；占比行 `取链命中 5/6（命中率 83%）`；6 卡全在、端点 **30/0**、
HTML 135505B、JS undefined NONE、CSS 302/302、node 0、console 0、截图 r56_progress.png。

**完善性（游标续推）**：全库 8 批 batch=20 `lyric 3074→3075 · runs 308→316`，
断点 `整理后分类\thisistruemusic\纯音乐\River.mp3`。

**坑**：命中率分母 `calls` 是**进程内**（不随 hits 落盘）——重启后 hits 从 `pv_hits.json` 读回、
calls 归 0，命中率会虚高（hits 旧累计 / calls 新分母）；接受此偏差（命中率本就是「本进程观测」，
文案不标「跨重启」）。

---

## 第71轮（前端 R57 · goal round34）：命中率分母落盘 + hit_rate 封顶 + 维护页「最近补 N 首」

**完善性（命中率跨重启）**：R56 命中率分母 `_PV_CALLS` 进程内——重启后 hits 读回旧累计、
calls 归 0 → 命中率虚高（R56 坑已证 250%）。`_PV_CALLS` **落盘** `_cache/pv_calls.json`
（与 hits 同机制：启动 `_pv_load_calls` 读回、`_pv_on_call` 节流 1s 写、`/api/cache` 读时
`_pv_flush_calls` 兜脏）；`hit_rate` **封顶 100**（`min(100, …)`）——hits 历史累计但 calls 是
「本进程读起」，封顶防虚高误导。清缓存收编 `pv_calls.json`。

**完善性（最近补首可视化）**：`maintain.tick` 每次补成功追加 `recent`（`{what:lyric/cover, name, at}`，
保最近 5）+ `status()` 带出 + 维护页 6 卡下方「最近补: 歌词 · X 封面 · Y」小列表（`s.recent` 空则不显）。

**E2E**：`pv_calls.json` 落盘 `3`、`previews {hits:5, calls:3, hit_rate:100}`（封顶生效）；seed 2 条
`recent` → 维护页显「最近补: 歌词 · 周杰伦/晴天 封面 · 邓紫棋/新的心跳」绿 → 还原；端点 **30/0**、
node 0、console 0、截图 r57_recent.png。

**完善性（游标续推）**：全库 8 批 batch=20 `runs 316→324`，断点 `整理后分类\thisistruemusic\英文歌\Hymn for the Weekend.mp3`
（本批 lyric/cover 0 补——尾部全嵌入型，加速层只长新补首，recent 空属正常）。

**坑**：① `_pv_on_call` 节流 1s 内不写盘——预热 2 调太近，`pv_calls.json` 没落（需 `/api/cache` 读时
`_pv_flush_calls` 兜）；② `hit_rate` 不封顶会 250%（hits 跨重启旧累计 / calls 本进程新分母）——`min(100)` 封顶；
③ 维护页「最近补」只在 `recent` 非空显，本轮 0 补不显 = 正确（不是 bug）。

---

## 第72轮（前端 R58 · goal round35）：最近补相对时间 + 修 _pv_on_call UnboundLocalError

**简洁性（最近补可读性）**：R57 最近补列表只有「歌词 · X / 封面 · Y」，没时间——补的哪会了看不见。
加**相对时间**（`at` 字段 → `刚刚 / N 分钟前 / N 小时前 / N 天前`），seed 验证 `歌词 · 周杰伦/晴天（3 分钟前） 封面 · 邓紫棋/新的心跳（刚刚）`。

**修**：R57 `_pv_on_call` global 只声明 `_PV_CALLS, _PV_CALLS_DIRTY`，漏 `_PV_CALLS_LAST_FLUSH`
→ `/api/preview` 每次调 `_pv_on_call` 触发 `UnboundLocalError: cannot access local variable
'_PV_CALLS_LAST_FLUSH'` → `/api/preview` 全 500（R57 验收时 preview 没被单独打，端点 29/1 才暴露）。
补 global 即修。教训：加节流写盘必把 `*_LAST_FLUSH` 也进 global（`_pv_on_hit` 同样漏了但 hits 的
`_pv_on_hit` 没做 flush，只标脏——calls 把 flush 内联进 `_pv_on_call` 才炸）。

**E2E**：最近补相对时间绿；preview 修复 200；端点 **30/0**、HTML 136189B、JS undefined NONE、
CSS 302/302、node 0、console 0、截图 r58_recenttime.png。

**完善性（游标续推）**：全库 8 批 batch=20 `runs 324→332`，断点 `整理后分类\thisistruemusic\英文歌\pure imagination.mp3`。

---

## 第73轮（前端 R59 · goal round36）：flush global 全量 audit + 维护页「本批补」即时回显

**完善性（global 完整性审计）**：R58 修了 `_pv_on_call` 漏 `_PV_CALLS_LAST_FLUSH`。同源隐患：
`_pv_flush_hits` 也漏了 `_PV_HITS`（它 `_f.write(str(_PV_HITS))` 但 global 只声明
`_PV_HITS_DIRTY, _PV_HITS_LAST_FLUSH`）——之前没炸因为 `/api/cache` 读时调它时 `_PV_HITS`
碰巧在模块级可读（Python 只读不 global 也行，但写就要）。**补 `_PV_HITS` 进 global**，
并 E2E 源码 audit 断言 `def _pv_flush_hits` 的 global 行含 `_PV_HITS`（防再退）。

**完善性（本批补即时回显）**：`mtRun` 跑一轮后只报「歌词 +N」数量，补了什么看不见。
加 `#mtlast` 即时回显（拉 `/api/maintain` 的 `recent` 前 3 条挂 `mtmsg` 下）
——`本批补: 歌词 周杰伦/晴天 · 封面 邓紫棋/新的心跳`，不用等 5 卡重拉。

**E2E**：`_pv_flush_hits` global audit 过（含 `_PV_HITS`）；seed 2 条 recent → 点「跑维护」
→ `#mtlast` 显「本批补: 歌词 周杰伦/晴天 · 封面 邓紫棋/新的心跳」绿 → 还原；
端点 **30/0**、HTML 136751B、CSS 302/302、node 0、console 0、截图 r59_batchlast.png。

**完善性（游标续推）**：全库 8 批 batch=20 `runs 332→340`，断点 `华语经典\周杰伦\搁浅.mp3`。

**坑**：节流写盘函数 global 完整性——`_f.write(str(X))` 要 global `X`（写）；只读不 global 也行。
`_pv_flush_hits` 写 `_PV_HITS` 但 global 漏它，同 R58 `_pv_on_call` 漏 `_PV_CALLS_LAST_FLUSH` 一类
（R57 加 calls 落盘没同步 audit hits 的 flush）。E2E 加**源码级 global 断言**防退。

---

## 第74轮（前端 R60 · goal round37）：global 完整性通用 lint + 本批补相对时间

**完善性（防退护栏）**：R58/R59 连修两个 `UnboundLocalError`（`_pv_on_call` 漏 `_PV_CALLS_LAST_FLUSH`、
`_pv_flush_hits` 漏 `_PV_HITS`）——手动漏声明靠 review 防不住。加**通用 lint** `tests/lint_globals.py`：
扫 web.py 全部顶层 def，凡「写模块级共享 `_` 变量（多 def 共写）但 global 漏声明」的报出，exit 1。
跑通：`全过 (扫 10 个 def, 8 个模块级变量)`。以后加节流写盘函数忘 global，lint 一跑就暴露。

**简洁性**：`#mtlast` 本批补加**相对时间**（复用 R58 `ago()`：`刚刚 / N 分钟前 / N 小时前 / N 天前`），
`本批补: 歌词 周杰伦/晴天（5 分钟前） · 封面 邓紫棋/新的心跳（刚刚）`；去掉冗余的 `el.textContent`（只留
`el.innerHTML` 带相对时间）。

**E2E**：`global lint` 全过（exit 0）；seed 2 条 recent 带 at → 点「跑维护」→ `#mtlast` 显相对时间绿 →
还原；端点 **30/0**、HTML 137032B、JS undefined NONE（`mtlast` 是运行时 createElement 的 id，
初始 HTML 无 = 预期）、CSS 302/302、node 0、console 0、截图 r60_batchtime.png。

**完善性（游标续推）**：全库 8 批 batch=20 `runs 340→349`，断点 `华语经典\林俊杰\爱笑的眼睛.mp3`。

**坑**：subprocess 捕获 lint 脚本中文输出要 `encoding="utf-8"`——本机 py 默认 GBK，不传 encoding
会 `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xcd`（stdout 全 None）；`run` 加 `encoding` 才稳。

---

## 第75轮（前端 R61 · goal round38）：跑维护 spinner + 跑中计时（反馈不空等）

**简洁性（长任务反馈）**：`mtRun` 跑一轮 tick 要 ~10s+，原「跑中…」一句不动，看着像卡死。
加**按钮 spinner**（`.spin` 转圈 + 「跑中…」）+ **跑中计时**（每 500ms 刷「已耗时 N s」）
+ 完成回执「完成，耗时 N s」+ 按钮文字恢复。反馈不空等。

**E2E**：点「跑维护」→ 按钮 `跑中…` + spinner + disabled 绿；完成后按钮恢复 `跑一轮` +
`完成，耗时 12 s`；端点 **30/0**、HTML 137727B、JS undefined NONE（`mtlast` 预期运行时 id）、
CSS 304/304（新增 `@keyframes spin`）、node 0、console 0、截图 r61_spinrun/r61_spendone.png。

**完善性（游标破 350 里程碑）**：全库 8 批 batch=20 `runs 350→358`（R55 里程碑进度条满刻度 350
**已破**——进度条变绿），断点 `华语经典\陈粒\空空.mp3`。

**坑**：`@keyframes spin` 在 `</style>` 前注入——CSS 大括号基线 302→304（多 1 对），
验收基线要同步（`@keyframes` 里 `to{}` 算 1 对）。

---

## 第76轮（前端 R62 · goal round39）：跑维护连跑 N 轮 + 里程碑自动上抬 400

**完善性（连跑）**：`mtRun` 只能跑 1 轮（每轮 20 首），要连推 8 批得点 8 次。加「连跑 N 轮」输入
（`#mtruns` 1~10）——一次 `N` 个 tick，按钮进度 `连跑 i/N…`，完成回执 `连跑 N 轮完成，耗时 X s`
（一圈跑完提示「（下一圈）」）。

**完善性（里程碑自动上抬）**：R55/R61 里程碑满刻度写死 350，破了 350 还显 350 刻度（误导）。
改 `ms = runs>=350 ? 400 : 350`——破 350 自动上抬 400，tooltip `里程碑 350/400，下一里程碑 400 还差 N`，
进度条满刻度同步上抬。

**E2E**：连跑 3 轮回执 `连跑 3 轮完成，耗时 28.1 s`、runs 363→366（+3）；连跑 2 轮回执 `12.1 s`、
runs 366→368（+2，精确）；里程碑上抬 400（`下一里程碑 400 还差 32`）；端点 **30/0**、HTML 138276B、
CSS 304/304、node 0、console 0、截图 r62_multirun.png。

**完善性（游标续推）**：全库连跑 3+2 tick `runs 359→368`，断点 `摇滚民谣\万能青年旅店\狗尿馆.mp3`。

**坑**：① 连跑终值断言必须**二点缓存**（`/api/maintain` 前后 runs 差 = N，不是等页面 countUp 中间态
——R62 首验读到 `runs=159` 是 countUp 0→366 滚到 159 的中间态，假红）② 进度条 div 选择器
`div div div` 嵌套对不上返回空——里程碑用 **tooltip 文案断言**（`下一里程碑 400`）比抓 barW 稳。

---

## 第77轮（前端 R63 · goal round40）：连跑「跑到全库」+ 取链命中率独立卡

**完善性（连跑可跨圈）**：R62 连跑 N 轮上限 10，全库 5188 首跑完一圈要 260 tick 点不动。
加「**跑到全库**」勾选（`#mtfull`）——勾选则忽略轮数，循环到 `r.done`（游标一圈跑完）自动停，
按钮 `跑到全库 第 i 轮…`、回执 `跑到全库完成 · 共 i 轮`；不勾选走 R62 连跑 N（1~50）。

**简洁性（命中率独立卡）**：R56 命中率藏在第 6 卡 tooltip + 占比行里。拆**第 7 卡「取链命中率」**
（`hits/calls`，`≥80` 绿、`calls≥20` 黄）——命中率独立一卡，免翻 tooltip。

**E2E**：维护页 7 卡全出（`已跑轮次 372 / 累计补歌词 3081 / 累计补封面 3430 / 累计清理 0 /
ID3 已核 / 缓存三合命中 7 / 取链命中率 0%`）；「跑到全库」勾选项在；端点 **30/0**、
HTML 138985B、JS undefined NONE、CSS 304/304、node 0、console 0、截图 r63_hitcard.png。

**完善性（游标续推）**：全库 4 批 batch=20 `lyric 3074→3081 · cover 3427→3430 · runs 368→372`
（本批补回 3 歌词 + 3 封面——游标推进到**非嵌入型**尾部），断点 `摇滚民谣\草东没有派对\撒野.mp3`。

**坑**：`#mtfull` 勾选时 `N=999999` 哨兵 + `r.done` break——全库游标到圈尾 `done=True` 才停，
不是「跑 N tick」；不勾选走 R62 `Math.min(50,…)`。命中率为 0% 属正常（本进程还没发取链请求，
calls=0 → hit_rate 兜 0）。

---

## 第78轮（前端 R64 · goal round41）：7 卡两行 4+3 网格 + 跑到全库预估外推

**简洁性（7 卡排版）**：R63 加命中率卡后维护页 7 卡 auto-fit 一行 7 张挤满、窄屏折乱。
加 `.mtgrid`（维护页专用）——桌面 4 列两行（4+3），第 5 卡 `grid-column:1` 归位，窄屏 2 列 auto-fit。

**完善性（跑到全库预估）**：R63 跑到全库循环没预估，点下去不知道跑多久。加**首 tick 实测外推**
（`ticksFirstMs` 记首 tick 耗时 → `预计全库约 N 分钟`；第 2+ tick 按 `elapsed/(i-1)` 平均 →
`已 X s / 预计约 N 分钟剩`）——预估基于实测，不是拍脑袋。

**修**：① R63 FULL 回执走漏（`if(!(FULL && doneMsg))` 条件反——FULL 时 doneMsg 非空反跳过
FULL 回执，落到 `连跑 999999`）→ 加 `FULL_DONE` 哨兵，`r.done` 时 setMsg + break，循环后 FULL 分支跳过
② 预估原先在 tick 前算（首 tick 0s 外推 → `预计全库约 0 分钟` 假红）→ 移到**首 tick 后**用 `ticksFirstMs` 外推。

**E2E**：7 卡 `cols=4 c5 第二行`（4+3 两行）；跑到全库第 2 tick `已 6.4s / 预计约 11 分钟剩`（实测分钟数）；
端点 **30/0**、HTML 139950B、JS undefined NONE、CSS 309/309、node 0、console 0、截图 r64_fulllib.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 372→376`，断点 `摇滚民谣\赵雷\最后一首歌.mp3`。

**坑**：① 跑到全库 FULL 回执与连跑回执分支——加 `FULL_DONE` 哨兵区分（R63 的 `if(!(FULL&&doneMsg))`
逻辑反了）② 预估必须在**首 tick 后**算（tick 前 elapsed≈0，外推全 0 假红）；③ 全库完整跑完验收太重
（5188 首/50=tick×~1.5s≈2.5 分钟，E2E 240s 卡到 timeout）——验收只断「预估文案有真实分钟数」，
不跑完整圈。

---

## 第79轮（前端 R65 · goal round42）：看日志「实时」开关 + 本批补跳转曲库

**完善性（实时日志流）**：`mtLog` 只拉一次 80 行静态。加「**实时日志**」开关（`#mtloglive`，2s 轮询
`act=log&n=120`）——跑维护时挂上，日志逐屏刷；再点一次停。`_mtlogTimer` 单例防多轮询。

**完善性（本批补可跳）**：R57「本批补」列表只有名称不能跳。加**可点跳转**——每个补首名包
`<a data-jn>`，点跳 `#lib` + 填 `#findq` 搜索框（`_libLoad()` 重拉）——「最近补了什么 → 直接看」。

**E2E**：「实时日志」开关回执 `实时日志 · 每 2s 刷新…` 绿、停开关回执 `实时日志已停`；本批补 `data-jn`
跳转在；端点 **30/0**、HTML 140841B、JS undefined NONE、CSS 309/309、node 0、console 0、
截图 r65_livelog.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 380→384`，断点 `洛天依\洛天依\黑凤梨 - 000qPXNS3XF7fw.mp3`。

**坑**：实时日志**单例**（`_mtlogTimer`）——不判旧 timer 直接 `setInterval` 会多轮询叠着刷（重复 fetch
+ DOM 抖动）；「看日志」静态与「实时」共用 `mtLogDraw()`，停实时要 `clearInterval` 归 0。

---

## 第80轮（前端 R66 · goal round43）：看日志关键词过滤 + 命中行高亮（时间戳内置）

**完善性（日志可检索）**：维护日志 200 行全铺、找「歌词+ 某首」要翻。看日志区加**关键词过滤框**
（`#mtlogfilter`）——本地过滤（`lines.filter(l=>l.indexOf(kw)>=0)`）+ 命中行 `<mark>` 高亮（黄底），
`input` 事件即重绘（`_mtlogTimer` 实时刷新时也读过滤值，过滤 + 实时叠加生效）。空过滤 = 全显；
无匹配显「无匹配「X」的日志」。

**简洁性（时间戳）**：`maintain.log()` 本就带 `%Y-%m-%d %H:%M:%S` 前缀（写文件 + stderr 都带），
过滤框不需要额外加时间戳——读日志即自带，R66 不重复造。

**E2E**：`#mtlogfilter` 填「歌词」→ 过滤后含「歌词」+ **126 个 `<mark>` 高亮**绿；日志首行时间戳
`2026-11-26 01:43:06` 在；端点 **30/0**、HTML 141623B、JS undefined NONE、CSS 309/309、node 0、
console 0、截图 r66_logfilter.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 384→388`，断点 `林俊杰\加油.mp3`。

**坑**：过滤+高亮用 `_kwsHtml` 转义正则字符再 `replace`——`kwsHtml` 在 R66 初稿里定义了两次
（`mtLogDraw` 内 + 外层各一次，内层 `hi` 引用未定义）→ 简化成外层一个 `_kwsHtml`，去内层 `hi`。

---

## 第81轮（前端 R67 · goal round44）：日志过滤预设 chip（歌词 / 封面 / 异常 一键）

**简洁性（免手打过滤词）**：R66 过滤框要手打关键词。加**预设 chip**（`[data-lf]`：`歌词 / 封面 / 异常 / 全部`）
——点一下填 `#mtlogfilter` + 触发 `mtLogDraw()` 重绘；「全部」= 清空过滤。4 个 chip 跟过滤框并排。

**E2E**：点「歌词」chip → 过滤框 `歌词` + **126 个 `<mark>` 高亮**绿；点「全部」→ 过滤框清空 `''`；
端点 **30/0**、HTML 142155B、JS undefined NONE、CSS 309/309、node 0、console 0、截图 r67_logchip.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 388→392`，断点 `毛不易\城市傍晚.mp3`。

**坑**：chip 用 `data-lf` 属性委托（`document.querySelectorAll('[data-lf]')`）——不用每个 chip 单独绑 onclick，
加预设只改 `data-lf` 值；「全部」用空串 `data-lf=""`（`f.value=''` 清空 = 不过滤）。

---

## 第82轮（前端 R68 · goal round45）：导出维护日志（maintain.log 快照）

**完善性（日志留档）**：维护日志只在页面看，出问题要留档没有出口。加「**导出日志**」按钮
（`#mtlogexport`）——拉 `act=log&n=500` 全量 → Blob 下载 `maintain.log.YYYY-MM-DD.txt`，回执「已导出 N 行」。

**E2E**：点「导出日志」→ 回执 `已导出 500 行日志` 绿；端点 **30/0**、HTML 142976B、JS undefined NONE、
CSS 309/309、node 0、console 0、截图 r68_export.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 392→396`，断点 `洛天依\凉凉.mp3`。

**坑**：导出走**前端 Blob 下载**（不新增后端下载端点）——`act=log&n=500` 已能拉全量，前端 `Blob + a.download`
即可；`URL.revokeObjectURL` 延迟 1s 再回收（浏览器需时间完成下载）。

---

## 第83轮（前端 R69 · goal round46）：重置断点确认弹窗 + 异常行红字

**完善性（破坏性操作确认）**：「重置断点」原 `confirm('重置断点游标？')` 一句太轻。改成**拉当前
断点填进弹窗 + 后果说明**（`当前断点: 洛天依\权御天下…mp3` + `重置后果: 下次从头扫全库 5188 首，
已补的不重补只重扫`）——破坏性操作让用户看到确切代价。

**简洁性（异常可视）**：日志行里 `miss/error/Exception/失败/超时/无封面` 的行**整行染红**
（`var(--bad)`）——异常不用读字，红色即跳眼。无异常时 0 行红（全库跑顺 = 全绿）。

**E2E**：重置确认弹窗显示真实断点 `洛天依\权御天下 - 001xZXiW4aAhkL (1).mp3` + 后果文案绿；
seed 2 行假异常（失败/超时）→ 前端 **2 个红 span** 绿（验证红字逻辑）→ 还原日志；端点 **30/0**、
HTML 143396B、JS undefined NONE、CSS 309/309、node 0、console 0、截图 r69_reset.png。

**完善性（游标破 400）**：全库 4 批 batch=20 `runs 396→400`（破 400，R62 里程碑上抬 400 已满 →
R70 可上抬 450），断点 `洛天依\权御天下 - 001xZXiW4aAhkL (1).mp3`。

**坑**：异常红字验证——全库维护跑顺后日志**没有**异常词行（0 命中），直接读 0 行红是**正确**
（无异常就该全绿）；要验证红字逻辑须 **seed 带「失败/超时」的假日志行**再读（2 红 span）→ 还原。

---

## 第84轮（前端 R70 · goal round47）：runs 里程碑上抬 450 + 异常率卡（第 8 卡）

**完善性（里程碑续抬）**：R62 里程碑满刻度 400，R69 已破 400。上抬 450（`ms=runs>=400?450:400`，
tooltip `里程碑 400/450，下一里程碑 450 还差 N`，进度条满刻度同步）。

**完善性（异常率卡）**：维护页加**第 8 卡「异常率」**——前端拉 `act=log&n=200` 数异常行
（`miss/失败/超时/error/Exception/无封面`）占比，`>5%` 红、`>0` 黄、`=0` 绿（全库跑顺 = 全绿 0%）。

**修**：R70 异常率卡 insert 处把 `let libMB/libCount` 声明 + `if(!libMB){...}` 块挤掉外层 try 的配平
catch（`node --check` 报 `Missing catch or finally after try`）——补回 `let libMB=0,libCount=0` 声明、
删多余 `}`。

**E2E**：维护页 8 卡全出（`已跑 404 / 歌词 3090 / 封面 3440 / 清理 0 / ID3 已核 / 缓存三合 37 / 取链命中 0% /
异常率 0%`）；里程碑上抬 450（`下一里程碑 450 还差 46`）；端点 **30/0**、HTML 144197B、JS undefined NONE、
CSS 309/309、node 0、console 0、截图 r70_mile450.png。

**完善性（游标续推）**：全库 4 批 batch=20 `lyric 3084→3090 · cover 3436→3440 · runs 400→404`，
断点 `洛天依\霜雪千年 - 001mzBxY4UVcAH.mp3`。

**坑**：在 `mtStat` 的 try 块中间插代码（异常率卡 insert）容易挤掉作用域外变量的 `let` 声明 + 配平
catch——insert 后要 `node --check` 抓 `Missing catch/finally`（配平错），别只看 `compile` 过。

---

## 第85轮（前端 R71 · goal round48）：8 卡两行 4+4 归位 + 异常率卡点跳日志

**简洁性（8 卡排版）**：R70 异常率卡后维护页 8 卡 4+4，第 5 卡 `grid-column:1` 归位（已有），
加第 9 卡占位规则（`.mtgrid .statcard:nth-child(9){grid-column:1}`，卡数增长自动续排），窄屏 2 列。

**完善性（异常率卡可点）**：异常率卡 `data-jumplog="异常"` 可点——点它**追加**日志容器 `#mtjumplog`
到 `#mtresult` 尾（`mtlogfilter` 自动填「异常」+ 拉日志过滤 + 滚到），**不清 8 卡**（`appendChild` 非
`innerHTML` 全替换）；异常率 0%（全库跑顺）时容器显「无匹配日志」。

**E2E**：8 卡 `cols=4 c5 第二行 c5col=1`；点异常率卡 → `fv=异常 / hasBox / boxVisible / cards=8`（容器在、
不清卡）绿；端点 **30/0**、HTML 145674B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r71_jumplog.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 404→408`，断点 `红心收藏\Mr. Feel.mp3`。

**坑**：① 跳日志容器 `#mtjumplog` 最初挂 `class="n"`（`n` = `display:none`）→ hidden，去掉 `n` 类 ② 容器
append 到 `#mtresult` 但父级在 `d` tab 未激活时 hidden——验收用 `wait_for_selector(state="attached")`
（不要求 visible）断言容器在，别等 visible。

---

## 第86轮（前端 R72 · goal round49）：8 卡 tooltip 全补 + 「刷新」按钮

**简洁性（tooltip 统一）**：R71 后维护页 8 卡，「累计补歌词/封面/清理」3 卡**无 title**（悬停没说明）。
统一补 tooltip（`维护累计补歌词条数(命中缓存+补全)…`），8 卡悬停全出统计说明，**无 tooltip 卡数 = 0**。

**完善性（缓存刷新）**：`#mtrefresh` 按钮——只重拉 8 卡数据（`await mtStat()`），保留已跳日志容器
（`#mtjumplog` 曾建过则重挂异常率卡点击），不重铺整区；回执「已刷新」。

**E2E**：8 卡 `无 tooltip 数 = 0`；点「刷新」→ `已刷新 / cards=8` 绿；端点 **30/0**、HTML 146311B、
JS undefined NONE、CSS 310/310、node 0、console 0、截图 r72_refresh.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 408→412`，断点 `纯音乐\Sadness and Sorrow.mp3`。

**坑**：① 验收脚本 `p.evaluate("=>…")` 箭头语法错（要 `"()=>{…}"`）——evaluate 首参必须是函数表达式字符串
② `#mtrefresh` 刷新若 `#mtjumplog` 已被 `mtStat` 的 `#mtresult` 重铺清掉，要 `hadJump` 记状态 + 重挂异常率卡点击。

---

## 第87轮（前端 R73 · goal round50）：第 9 卡「本轮补 N」（最新 tick 即时补数）

**完善性（本轮即时反馈）**：维护页 8 卡都是累计/占比，「刚跑这一 tick 补了几首」看不到。
加**第 9 卡「本轮补（最新 tick）」**——`maintain.tick()` 存 `st["last"]={lyric_ok,cover_ok,cleaned,scanned,at}`，
`status()` 回 `last`，前端第 9 卡显 `lastN = lyric_ok+cover_ok`（`>0` 绿、`=0` 灰），点「刷新」重拉。

**E2E**：9 卡全出（`已跑 416 / 歌词 3091 / 封面 3440 / 清理 0 / ID3 已核 / 缓存三合 42 / 取链命中 0% /
异常率 0% / 本轮补（最新 tick）0`）；端点 **30/0**、HTML 146888B、JS undefined NONE、CSS 310/310、
node 0、console 0、截图 r73_lastcard.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 412→416`，断点 `英文歌\21 Guns.mp3`。

**坑**：① `tick()` 存 `st["last"]` + `status()` 回 `last`（两端都要改，单改 status 拿不到）② 重启后
首次 tick 前 `state` 无 `last` 字段 → `s.last||{}` 兜底（本轮补显 0，不崩）；③ 第 9 卡 4 列 3 行
（4+4+1），第 5/9 卡 `grid-column:1` 归位（R71 已加 nth-child(5/9)）。

---

## 第88轮（前端 R74 · goal round51）：本轮补相对时间 + 跑到全库完成 toast

**简洁性（本轮补时间）**：R73 第 9 卡「本轮补 N」只有数字。加**相对时间**（`last.at` →
`刚刚 / N 分钟前 / N 小时前 / N 天前`，复用 ago 逻辑）——`0 刚刚` 一眼知道刚跑过；没跑过显「待跑」。

**完善性（跑到全库 toast）**：R64 跑到全库完成只在 `#mtmsg` 一行，滚到下面就看不见。加 `_toast()`
（右下角浮层，4s 自动消）——跑到全库完成 `跑到全库完成 · 共 N 轮` 弹 toast，不依赖滚动位置。

**E2E**：第 9 卡 `0 刚刚`（相对时间绿）；`_toast` 函数在（`typeof _toast === function`）+ 手动调浮层
`测试 toast` 绿；端点 **30/0**、HTML 148119B、JS undefined NONE、CSS 310/310、node 0、console 0、
截图 r74_toast.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 416→420`（`last={lyric_ok:0,cover_ok:0,at:...}` 落 state），
断点 `英文歌\Hey Soul Sister.mp3`。

**坑**：① `_toast` 浮层用**单例**（`__toast__` 挂 body）+ 4s 自动消——不每次 `createElement` 叠浮层 ②
第 9 卡相对时间 `last.at` 缺（首次 tick 前）→ `待跑`，有则 `agoT(last.at)`；③ node 配平抓 JS 时机
（服务重启瞬断 ConnectionRefused）——重抓一次即过。

---

## 第89轮（前端 R75 · goal round52）：累计卡 delta 快照对比（本次 +N 高亮）

**完善性（增量可见）**：维护页「累计补歌词/封面/清理」只有累计值，跑完一轮看不出**本轮加了几个**。
`mtStat` 存 `window._mtLast={lyric,cover,clean,runs}` 快照，下次看状态时算 `delta(k)=c-p`，新增
`+N` 小标（绿）挂累计卡值旁——「累计 3091（+5）」一眼看本轮补了几个，不重看累计。

**E2E**：`_mtLast` 快照落 window（`lyric/cover/clean/runs`）；跑 1 轮维护后累计卡 delta——本轮无增量
（全库跑顺、无新增）= 无 `+N`（正确）；端点 **30/0**、HTML 148854B、JS undefined NONE、CSS 310/310、
node 0、console 0、截图 r75_delta.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 420→422`，断点 `英文歌\Lose You to Love Me.mp3`。

**坑**：`delta(k)` 只在 `c>p` 显 `+N`——`_mtLast` 是**会话内**快照（不持久化），刷新页面后首次
`mtStat` 无 prev（`prev={}`）→ 全卡无 delta（正常，没「上次」可比）；要跨刷新持久得落 `localStorage`
（本轮不做，会话内对比已够）。

---

## 第90轮（前端 R76 · goal round53）：`_mtLast` 落 localStorage 跨刷新 + delta 双向 +N/-N

**完善性（跨刷新对比）**：R75 `_mtLast` 是会话内快照（`window._mtLast`），刷新页面就丢「上次」。
改**落 `localStorage._mtLast`**——跨刷新也保留上次累计，下次看状态 delta 仍可算（「+N / -N」跨会话）。

**简洁性（delta 双向）**：`delta(k)` 从「只 +N」改成**双向**（`c-p` 正 `+N` 绿、负 `-N` 红）——
清缓存后封面 `cumCover` 不变但 `cover` 累计可能因重建变化，减少也 `-N` 红字见（不是只有增量）。

**E2E**：`localStorage._mtLast={lyric:3091,cover:3440,clean:0,runs:425}` 落盘绿；端点 **30/0**、
HTML 149205B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r76_localstorage.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 423→425`，断点 `英文歌\Skyfall.mp3`。

**坑**：`delta(k)` 用 `prev[k]===undefined?0:prev[k]`（localStorage 首次无 key → 0，别用 `||` 否则
`prev=0` 时 `prev[k]||0` 也 0 但 `undefined` 语义更清）；`-N` 判断 `delta('k')[0]==='+'` 区分红绿
（负号 `-` 开头 → 红）。

---

## 第91轮（前端 R77 · goal round54）：清缓存联动清 `_mtLast`（delta 基准复位）

**完善性（delta 基准一致）**：R76 清缓存后 `_mtLast` 保留旧基准 → 下次 delta 全显 `-N`（封面清 0 但
累计 `cover` 没变，`c-p` 全 0；若清后重建 cover 变了就误导）。清缓存（`#mtcacheclr`）后**联动清
`localStorage._mtLast`**——delta 基准随缓存复位，下次看状态是干净对比（不拿清前基准比清后值）。

**修**：`removeItem('_mtLast')` 原在 `await mtStat()` **前**（`mtStat` 的 `setItem` 又写回新值 → 清不掉），
移到 `mtStat` **后**（最后清，不被写回）。

**E2E**：`mtstat` 建 `_mtLast` → `mtcacheclr` 清缓存（hook `window.confirm=()=>true` 放行）→
`_mtLast=None` 绿；端点 **30/0**、HTML 149344B、JS undefined NONE、CSS 310/310、node 0、console 0、
截图 r77_cacheclr.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 425→427`，断点 `英文歌\Unstable.mp3`。

**坑**：① 清缓存有 native `confirm`（headless 默认返 false 挡掉）——验收要 `window.confirm=()=>true`
hook 放行 ② `removeItem` 必须在 `mtStat()`（其 `setItem`）**之后**，否则被写回；③ `localStorage` 操作
全 `try{...}catch`（隐私模式/禁用时不崩）。

---

## 第92轮（前端 R78 · goal round55）：看状态时间戳 + 异常率卡滚到红字

**简洁性（看状态时间戳）**：维护页看不出**上次看状态是什么时候**（数据是否过期）。`mtStat` 落
`localStorage._mtViewAt`，「上次运行」行加 `· 看状态于 刚刚/N 分钟前`——一眼知道 9 卡数据新鲜度。

**完善性（异常率卡滚红字）**：R71 异常率卡点跳日志只滚到日志容器顶。改**滚到第一条红字异常行**
（`firstBad.scrollIntoView`，命中「异常」关键词行染红后定位）——直接落在异常行，不用在日志里翻。

**E2E**：`看状态于 刚刚`（时间戳绿）；点异常率卡 → `#mtjumplog` 容器在 + 滚到红字（全库跑顺 `hasRed=false`
正常）；端点 **30/0**、HTML 150262B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r78_viewtime.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 427→429`，断点 `草东没有派对\勇敢.mp3`。

**坑**：① 看状态时间戳 `_prevView` 要**读旧值再写新值**（先 `getItem` 存 `_prevView` 再 `setItem` 当前，
否则「看状态于」永远是刚刚）② 异常率卡红字定位 `firstBad` 取 `.joblog span[style*=var(--bad)]`（R69 染红的
行），无异常则 `hasRed=false`（跑顺正常）。

---

## 第93轮（前端 R79 · goal round56）：9 卡「自动刷 5s」开关（跑维护时挂着实时看）

**完善性（实时看板）**：维护页 9 卡要手动点「看状态/刷新」才更新，跑维护/跑到全库时**挂着看**
累计/delta/本轮补变化得反复点。加 `#mtautoref`「自动刷 5s」——`mtAutoRef()` 开关，开则每 5s 调
`mtStat()` 重拉 9 卡（按钮高亮 `var(--acc)`），再点停；跑维护时挂着实时看数字爬升。

**E2E**：点「自动刷」开 → `timerActive + bg=rgb(196,56,31)`（高亮）；再点 → `timerOff`（停）；
端点 **30/0**、HTML 151027B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r79_autoref.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 429→431`，断点 `草东没有派对\草东.mp3`。

**坑**：① `mtAutoRef` 是**开关**（`_mtAutoRefTimer` 非空则清 + 取消高亮，空则 `setInterval 5000` + 高亮），
复用 R60 `mtLogLive` 的 timer 模式 ② 按钮 `onclick="mtAutoRef()"` 内联（不用 `.onclick=` 绑定，因
`mtAutoRef` 是全局函数且要幂等开关）③ 自动刷调 `mtStat` 会重铺 `#mtresult`——挂着跑维护时若已跳日志
（`#mtjumplog`）会被 `mtStat` 清掉（要跳日志就别挂自动刷，或挂上后重新点异常率卡）。

---

## 第94轮（前端 R80 · goal round57）：自动刷与跳日志互斥

**完善性（互斥）**：R79 自动刷挂着跑维护时，点异常率卡跳日志会被 `mtStat` 每 5s 重铺 `#mtresult`
→ 跳的日志容器闪掉。改**互斥**：点跳日志时先 `mtAutoRef()` 停自动刷（timer 清 + 按钮取消高亮），
再挂 `#mtjumplog`——跳日志期间不再被自动刷冲。

**E2E**：开自动刷 → 点异常率卡跳日志 → `_mtAutoRefTimer=null`（自动刷停）+ `#mtjumplog` 容器在（绿）；
端点 **30/0**、HTML 151187B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r80_mutex.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 431→433`，断点 `许巍\故乡.mp3`。

**坑**：① 跳日志的 `card.onclick` 里判 `typeof _mtAutoRefTimer!=='undefined' && _mtAutoRefTimer!==null`
（自动刷在跑才停；`_mtAutoRefTimer` 是 `let` 全局，未开时 `null` 不停）② `mtAutoRef()` 是开关——跳日志
时它非空 → 走「停」分支（清 timer + 取消高亮），正好复用，不用另写停逻辑。

---

## 第95轮（前端 R81 · goal round58）：跑到全库完成自动挂「自动刷 5s」

**完善性（跑完盯盘）**：R79 自动刷要手动点，跑到全库跑完想看 9 卡 delta/本轮补回退还得再点一次。
改**跑到全库完成自动挂自动刷**——`mtRun` 的 `FULL_DONE` 分支除 `_toast` 外，`_mtAutoRefTimer` 未开则
`mtAutoRef()`（开 5s 自动刷），跑完 9 卡实时盯 delta 爬升/回退，不手动再点。

**E2E**：代码层断言「跑到全库完成自动挂自动刷」分支在（`已挂自动刷看 9 卡` + `if(_mtAutoRefTimer===null)mtAutoRef()`）；
端点 **30/0**、HTML 151315B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r81_autoref_after_full.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 433→435`，断点 `赵雷\最后一首歌.mp3`。

**坑**：自动挂判 `_mtAutoRefTimer` 未开才挂（已在跑则不重启），`typeof _mtAutoRefTimer==='undefined'`
兜底（`mtAutoRef` 是全局 `let`，未初始化前 `typeof` 安全）；跑到全库是「跑到 done」的 FULL 分支，
连跑 N 轮（非 FULL）不挂（N 轮跑完用户可能切页）。

---

## 第96轮（前端 R82 · goal round59）：「已跑轮次」卡迷你趋势线 sparkline

**简洁性（趋势一眼）**：维护页「已跑轮次」只有累计数，看不出**近几轮跑得顺不顺**。
加**迷你 sparkline**——`maintain.tick()` 存 `st["trend"]`（近 8 次每轮 runs，满 8 截尾），
`status()` 回 `trend`，前端「已跑轮次」卡下方挂 SVG polyline（`s.trend` 近 8 点，不引库），
跑得多斜率平、跳了断点斜率陡，一眼看趋势。

**E2E**：`trend=[440,441]` 落 state + 「已跑轮次」卡 `svg polyline` 在（绿）；端点 **30/0**、
HTML 151953B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r82_sparkline.png。

**完善性（游标续推）**：全库补 2 批 batch=20 `runs 439→441`（趋势凑 ≥2），断点 `陈奕迅\你给我听好.mp3`。

**坑**：① 我在 `maintain.py` 误用 C 风格注释 `/* */`（Python 要 `#`）→ 编译失败 → `/api/maintain` 500，
改 `#` ② 服务重启瞬断 + 坏 pyc 未清（重启前 `compileall` 失败仍留着旧 pyc）→ tick 早了 ConnectionRefused，
清 `src\__pycache__\*.pyc` + 重编译 + `Start-Process` 后补 2 批凑 `trend>=2` 才出 sparkline ③ sparkline
`tr.length<2` 不画（首次 tick 前 trend 空，正常）。

---

## 第97轮（前端 R83 · goal round60）：累计补歌词/封面卡也挂 sparkline（双趋势）

**简洁性（双趋势）**：R82 只有「已跑轮次」卡有 sparkline，累计卡看不出**爬升斜率**。
`maintain.tick()` 存 `st["cum_trend"]`（近 8 次 `{lyric,cover}` 累计，满 8 截尾），`status()` 回
`cum_trend`，前端泛化 `_sparkSvg(tr,color)` 生成器，「累计补歌词/封面」卡下方各挂一条
`var(--acc)` sparkline——3 张卡全带趋势，累计爬得陡/平一眼看。

**E2E**：`cum_trend` 落 state（`[{"lyric":3092,"cover":3440},…]`）+ 前 3 卡 `svg polyline`
`[True,True,True]` 全绿；端点 **30/0**、HTML 152200B、JS undefined NONE、CSS 310/310、node 0、
console 0、截图 r83_doublespark.png。

**完善性（游标续推）**：全库 4 批 batch=20 `runs 441→445`，断点 `陶喆\Kiss goodbye.mp3`。

**坑**：① `_sparkSvg` 从内联 IIFE 泛化成 `(tr,color)=>{}` 函数（3 卡复用，color 参数化）②
`cum_trend` 是**对象数组**（`{lyric,cover}`），前端 `map(o=>o.lyric)`/`map(o=>o.cover)` 抽序列再喂
`_sparkSvg`（不能直接喂对象）③ 累计卡 `cum_trend` 值全相等（全库跑顺、累计不变）→ 斜率平（画一条
平线，正确）；有增量才见斜率。

---

## 第98轮（前端 R84 · goal round61）：sparkline 悬停出各点值 tooltip

**简洁性（趋势读数）**：R82/R83 的 sparkline 只有折线，看不出**每个点的值**。`_sparkSvg` 加
`<title>`（原生 tooltip，不引库）——悬停折线出 `已跑轮次 近 8 次: 440 → 441 → … → 447`、
`累计歌词 近 N 次: …`，不放大也能读各点。

**E2E**：3 条 sparkline 悬停 tooltip 出各点值（`已跑轮次 近 8 次: 440→…→447` 绿）；端点 **30/0**、
HTML 152365B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r84_tooltip.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 445→447`，断点 `陶喆\秋天的枫.mp3`。

**坑**：① 上轮 edit 把新 `_covSpark`（带 label）加在旧行上方，旧 `_covSpark`（无 label）没删 →
`const _covSpark` 重复声明 → node 语法错，删旧行 ② `<title>` 放 `<svg>` 内（SVG 原生 tooltip），
`tr.join(' → ')` 出各点（全等值也列全，正确）③ 异常率卡 rate 是**前端算的**（不落 state），
没法画趋势——留 R85 决定（要趋势需 `tick` 记 rate 到 state）。

---

## 第99轮（前端 R85 · goal round62）：异常率卡挂趋势 sparkline（`rate_trend` 落 state）

**完善性（异常趋势）**：R84 异常率卡是**当前**占比（日志 200 行），看不出近几轮异常率**走势**
（有没有变好/变坏）。`maintain.tick()` 记本轮 miss 率（`(lyric_miss+cover_miss)/scanned`）到
`state["rate_trend"]`（近 8 次，满 8 截尾），`status()` 回 `rate_trend`，前端异常率卡下方挂
`var(--bad)` sparkline（复用 R84 `_sparkSvg`）——异常率爬升/下降一眼看。

**E2E**：`rate_trend=[0.0,0.0]` 落 state + 异常率卡 `svg polyline` 在（`title「异常率(本轮miss%) 近 2 次: 0 → 0」`）；
端点 **30/0**、HTML 152476B、JS undefined NONE、CSS 310/310、node 0、console 0、截图 r85_ratetrend.png。

**完善性（游标续推）**：全库 4+2 批 batch=20 `runs 447→453`，断点 `投稿\周杰伦\周大侠.mp3`。

**坑**：① 首次 4 批在**重启前**跑（旧代码无 `rate_trend`）→ 重启后 `rate_trend` 空，补 2 批才落值 ②
miss 率用**本轮** `res` 的 `lyric_miss+cover_miss`（不是累计），`scanned=0` 时 rate=0（除零兜底）③
全库跑顺 miss 全 0 → `rate_trend` 全 0（画平线，正确）；有异常才见斜率。

---

## 第100轮（前端 R86 · goal round63）：4 张趋势卡 sparkline 对齐（`.mtspark` 容器）

**简洁性（趋势对齐）**：R82–R85 给「已跑轮次/累计歌词/累计封面/异常率」4 卡各挂 sparkline，
但折线宽/高不一（内联 `width=110` 死值、边距散），视觉不齐。改**容器类 `.mtspark`**
（`width:100% + height:22px + overflow:hidden`，svg `display:block;width:100%;height:22px` +
`preserveAspectRatio=none`）——4 卡折线**同宽（卡 100%）同高（22px）**，4 条折线在网格里上下对齐成一行，
扫一眼看 4 个趋势。

**E2E**：4 张趋势卡 `.mtspark` 容器尺寸 `[{h:22,w:244}×4]` 全同（绿）；端点 **30/0**、HTML 152694B、
JS undefined NONE、CSS 312/312、node 0、console 0、截图 r86_aligned.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 453→455`，断点 `投稿\周杰伦\爱的飞行日记.mp3`。

**坑**：① sparkline 从**内联 svg 死值 `width=110`** 改成**容器 100% 宽**（`_sparkSvg` 返回
`<div class="mtspark"><svg viewBox…width:100%></div>`，`preserveAspectRatio=none` 拉伸铺满卡宽）②
`preserveAspectRatio=none` 让折线横向铺满但**纵向不变形**（viewBox 高 22 固定，只 X 拉伸）③ 验收
`getBoundingClientRect` 取 4 卡 `.mtspark` 尺寸比对 `同高同宽`（headless 1440 视口下卡宽 244）。

---

## 第101轮（前端 R87 · goal round64）：sparkline 首/末点圆点标记

**简洁性（起终点定位）**：R86 对齐后 4 条折线成一行，但折线端点看不清**从哪到哪**（起/终值）。
`_sparkSvg` 在首/末点加 `<circle>`——起点 `r=1.6`、终点 `r=2.4`（稍大，眼扫先落终点看最新值），
同色 `var(--acc)/var(--bad)`，不引库。

**E2E**：4 张趋势卡 `circle 数 [2,2,2,2]`（首+末，绿）；端点 **30/0**、HTML 152962B、JS undefined NONE、
CSS 312/312、node 0、console 0、截图 r87_dots.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 455→457`，断点 `投稿\洛天依\9999＋1！…mp3`。

**坑**：① 首/末点坐标从 `pts`（polyline 的 points 串）`split(' ')` 取首/末再 `split(',')[0/1]` 抽 cx/cy，
不重算（复用已算好的折线点）② 末点 `r=2.4` 比首点 `r=1.6` 大（视觉重心在最新值，扫一眼落终点）③
`circle` 在 `preserveAspectRatio=none` 的 svg 里会被拉伸成**椭圆**（X 缩放 Y 不缩）——`mtspark` 容器宽
100% 拉伸下圆点略变椭圆，可接受（要正圆得算实际像素比，本轮不做）。

---

## 第102轮（前端 R88 · goal round65）：sparkline 圆点正圆修（HTML 覆盖层）

**简洁性（圆点不畸变）**：R87 圆点在 `preserveAspectRatio=none` 的 svg 里被 X 拉伸成**椭圆**
（viewBox 110 宽拉到卡宽 244，X 放大 2.2×）。修——圆点移出 svg，改 `.mtspark` 内 **HTML 绝对定位
`<span>`**（`position:relative` 锚 + `left=0/100%` 定位首/末点 X、`top` 按 `yOf` 百分比、`width/height`
固定像素 + `border-radius:50%`）——**正圆不畸变**（不随 svg 拉伸），折线仍 `preserveAspectRatio=none`
铺满。

**E2E**：4 卡圆点实际像素 `['4x4','6x6']×4`（首 4 末 6，全正圆 宽=高）；端点 **30/0**、HTML 153178B、
JS undefined NONE、CSS 312/312、node 0、console 0、截图 r88_dots.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 457→459`，断点 `投稿\洛天依\孩子气的战争.mp3`。

**坑**：① `preserveAspectRatio=none` 只适合折线（polyline 铺满要拉伸），**圆点/文字会被拉成椭圆**——
点/文字移出 svg 用 HTML 定位 ② 首/末点 X 用 `left=0%/100%`（`tr.length>=2` 时首末点固定在首/末端），
`top` 用 `yOf(v)*100%`（`yOf` 从 px 改百分比）③ `span` 用 `margin:-size/2 0 0 -size/2` 居中在定位点 ④
验收 `[...sp].map`（NodeList 要展开，`sp.map` 在某些实现报错）。

---

## 第103轮（前端 R89 · goal round66）：sparkline 末点值标签（最新值数字）

**简洁性（末点读数）**：R88 圆点正圆后，末点圆点只看不读，扫折线还得放大才知**终点值**。
`_sparkSvg` 末点圆点旁加**最新值数字标签**（HTML `<span>`，`transform:translate(-50%,-160%)` 悬在
末点上方不占布局，同色 `var(--acc)/var(--bad)`）——扫一眼看 4 卡终点读数：`已跑 461 / 歌词 3098 /
封面 3445 / 异常率 0`。

**E2E**：4 卡末点值标签 `['461','3098','3445','0']`（绿）；端点 **30/0**、HTML 153490B、JS undefined NONE、
CSS 312/312、node 0、console 0、截图 r89_lastval.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 459→461`，断点 `投稿\洛天依\生.mp3`。

**坑**：① 值标签 HTML 绝对定位（同 R88 圆点，不随 svg 拉伸），`transform:translate(-50%,-160%)` 上移
悬在末点圆点上方 ② 标签同色 `color`（`var(--ok)/var(--acc)/var(--bad)`），异常率 0 显 `0`（绿，跑顺）③
`_valLabel` 只在有 sparkline（`tr.length>=2`）时渲染，空趋势不显值。

---

## 第104轮（前端 R90 · goal round67）：sparkline 折线下面积渐变填充

**简洁性（趋势厚度感）**：R86–R89 折线只有细 polyline，趋势单薄。加**折线下面积渐变**——
`_sparkSvg` 内 SVG `<defs>` 加纵向 `linearGradient`（`y1=0 透明 → y2=1 color@0.18`）+ `<polygon>`
（折线点 + 底边两点 `w,h / 0,h` 闭合）填面积，每卡唯一 `gid=spk<seq>` 免多卡渐变 id 冲突——
折线下方渐隐面积，趋势更有体积，扫 4 卡更有层次。

**E2E**：4 趋势卡 `polygon+linearGradient [True×4]`（绿）；端点 **30/0**、HTML 154067B、JS undefined NONE、
CSS 312/312、node 0、console 0、截图 r90_area.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 461→463`，断点 `投稿\热门歌曲\你往南走 - 南歌.mp3`。

**坑（本轮重点）**：R90 的 `_sparkSvg` 新 return（带 `<defs>` 渐变）**没删掉 R89 旧 return**，两行
拼在同行 → 第一个 `};` 提前闭合 `_sparkSvg`，第二个 return 落在函数外 → `mtStat is not defined` +
node `Missing catch or finally after try`。删 R89 遗留 return 修复。**教训**：`_sparkSvg` 这种「整函数
体一行重写」的 edit，old_string 必须含到旧的 `};` 闭合行，否则新旧 return 叠加。

---

## 第105轮（前端 R91 · goal round68）：sparkline hover 高亮当前点（跟随读值）

**简洁性（跟随读值）**：R90 面积渐变后，折线中间点只能靠 `<title>` 原生 tooltip（要悬停整折线），
扫 4 卡想读**某个 X 处的值**不方便。`_sparkSvg` 加 `.mtspark` 内 hover 层——`data-tr` 存 `{t,c,l}`
（序列/色/名，`encodeURIComponent` 免引号冲突）；全局**事件委托**（`document` mousemove 命中
`.mtspark` 则按鼠标 X 算最近点 `idx`，显高亮圆点 + 值标签，`left/top` 按 `idx` 定位，mouseout 清）——
鼠标扫折线，白边圆点 + 数字**跟着当前点走**，读任意 X 处的趋势值。

**E2E**：切维护 tab + 真 `mouse.move` 到 30% X → hover `hovLeft=57.14%`（`461→465` 序列第 2 点）+
`lblTxt=462`（绿）；端点 **30/0**、HTML 156127B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r91_hover.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 463→465`，断点 `投稿\热门歌曲\爱情讯息 - 郭静.mp3`。

**坑（本轮重点）**：① 验收直接调 `mtStat()`（不切维护 tab）时 `.mtspark` **section 未激活 `getBoundingClientRect`
全 0** → `frac=NaN` 定位失败（`hovLeft=-99px`）；**切 `.tab[data-p="d"]` 激活后容器有宽（244）才正常**——
功能无误，是验收姿势 ② `data-tr` 用 `encodeURIComponent(JSON)`（免引号/`&` 转义），取用 `decodeURIComponent`
③ hover 高亮点 HTML 绝对定位（同 R88 圆点不随 svg 拉伸），`border:2px solid #fff` 白边在折线上清晰
④ 事件委托 `passive` + `e.target.closest('.mtspark')`（不逐卡绑，`mtStat` 反复重建 9 卡也复用同一委托）。

---

## 第106轮（前端 R92 · goal round69）：维护 tab「本批耗时」卡（`dur_trend` 落 state）

**完善性（批次性能趋势）**：8 卡都是**结果指标**（歌词/封面/异常率），缺**性能指标**——每批 tick
用时多长、有没有变慢（网络拖 / 磁盘卡 / 曲目多了）。`maintain.tick()` 头记 `_t0=time.time()`、尾记
`_dur=round(time.time()-_t0,1)` 落 `res["duration"]` + `state["dur_trend"]`（近 8 批，满 8 截尾），
`status()` 回 `dur_trend`；前端「看状态」加**第 10 张卡「本批耗时（近 8 批）」**——值=最新一批 `s.dur_trend`
末位（`X.Xs`），下方挂 `var(--muted)` sparkline（近 8 批耗时折线，变长=拖慢）。

**E2E**：`dur_trend=[6.0,2.6]` 落 state + 本批耗时卡 `durV=2.6s + durSpark=True`（第 10 张卡，绿）；
端点 **30/0**、HTML 156672B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r92_dur.png。

**完善性（游标续推）**：全库 2+2 批 batch=20 `runs 465→469`，断点 `投稿\陈奕迅\淘汰.mp3`。

**坑**：① 值取 `s.dur_trend` **末位**（最新一批），不依赖 `s.last.duration`（`st["last"]` 在 tick 头写、
来不及算 `_dur`，故不塞 last）② 首次 2 批在**重启前**跑（旧代码无 `dur_trend`）→ 重启后空，补 2 批才落值
（同 R85 坑）③ `_sparkSvg` 色传 `var(--muted)`（中性色，耗时非好坏指标，不用红绿）。

---

## 第107轮（前端 R93 · goal round70）：维护「下一批预计」提示（`n_total` 落 state）

**完善性（跑完预计）**：R92 有了单批耗时，但「全库还剩多少、要跑多久」没答案。`maintain.tick()`
尾记 `state["n_total"]=len(paths)`（全库曲目数，每 tick 刷新），`status()` 回 `n_total`；前端「看状态」
网格下方加**一行提示**（`#mtnextest`，非卡片）——`下一批 ~<dur_trend 均值>s ｜ 全库 N 首 ≈ ceil(N/20) 批
≈ 总耗时`（分秒换算）。跑全库维护前一眼知道要挂多久。

**E2E**：`下一批预计: 下一批 ~2.3s ｜ 全库 5188 首 ≈ 260 批 ≈ 10 分 58 秒`（全库>0，绿）；端点 **30/0**、
HTML 157826B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r93_est.png。

**完善性（游标续推）**：全库 2+2 批 batch=20 `runs 469→473`，断点 `_归档_封存\SD卡版\…\甲乙丙丁.mp3`。

**坑**：① `n_total` 用 `tick()` 尾的 `len(paths)`（已 `browse.list_tracks` 全库扫过，顺带存，免 status 重扫）
② 首次 2 批在**重启前**跑（旧代码无 `st["n_total"]`）→ `n_total=0` 显「全库 0 首」，补 2 批才落 5188
（同 R85/R92 坑）③ `#mtnextest` 挂 `#mtresult` 尾（非 `.statgrid`），`mtStat` 重铺 `#mtresult` 时自动清掉重建
（幂等，自动刷 5s 不残留）④ 估算保守：`总耗时=批数×均值`（不含网络抖动，断点真实进度另看 cursor）。

---

## 第108轮（前端 R94 · goal round71）：全库进度条（`#mtprog`，已扫/总量）

**完善性（全库推进度）**：R93「下一批预计」是耗时估算，没直观**进度条**。`mtStat` 在「下一批预计」下
加 `#mtprog`——`全库进度 = 已跑轮次×20 / n_total`（封顶 100%），文字 `全库进度 N%（已扫约 X / Y 首）`
+ 一条 8px 高 `var(--acc)` 进度条（纯 CSS，`width` 过渡 0.3s）——跑全库维护时看整体推进到哪。

**E2E**：`全库进度 100%（已扫约 5188 / 5188 首）`（runs 475×20=9500 > 5188 封顶 100%）；端点 **30/0**、
HTML 158641B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r94_prog.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 473→475`，断点 `_归档_封存\SD卡版\…\阶梯.mp3`。

**坑**：① `已扫=runs×20` 是**估算**（断点续传后 runs 重计、cursor 从断点推，真实进度看 cursor；
进度条封顶 100% 防 `runs×20>n_total` 溢出）② `#mtprog` 挂 `#mtresult` 尾（非 `.statgrid`），`mtStat` 重铺自动
清掉重建（幂等，自动刷不残留）③ 进度条 `width` 用 `var(--acc)` 色、`transition:width .3s`（自动刷 5s 时
进度平滑增长，不跳变）。

---

## 第109轮（前端 R95 · goal round72）：全库进度条 100% 达成态（变绿 + 文案切换）

**简洁性（达成感）**：R94 进度条封顶 100% 但**色不变**（还是 accent），「全库已扫完」没达成感、
和「快扫完」没区分。`#mtprog` 加**达成态**——`_pct>=100` → 文案 `全库进度` 切 `全库已扫完 ✓`、
百分比与进度条色 `var(--acc)` 切 `var(--ok)`（绿）——跑完全库维护一眼见绿达成，没扫完保持 accent 进行中。

**E2E**：`全库已扫完 ✓ 100%（已扫约 5188 / 5188 首）` + 百分比 `bColor=rgb(47,125,85)`（绿）；端点 **30/0**、
HTML 158731B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r95_done.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 475→477`，断点 `_归档_封存\SD卡版\…\Naruto Main Theme.mp3`。

**坑**：① 达成态 `_done=_pct>=100`，色 `_pc=_done?var(--ok):var(--acc)`，文案 `_ptxt=_done?全库已扫完✓:全库进度`
（一处判分 3 用）② 100% 是**封顶**（`runs×20≥n_total`），非真「每首都补完」——全库跑完一轮，
断点续传后 `runs` 重置会重回进行中色（cursor 决定真实位置）③ 绿 `rgb(47,125,85)` = `var(--ok)`。

---

## 第110轮（前端 R96 · goal round73）：维护「最近补入」列表（`state.recent`）

**完善性（刚补了什么）**：9 卡 + 进度条都是**汇总数字**，没「刚补了哪几首」——`maintain_state.json` 早有
`recent`（每 tick `insert(0,{what,name,at})`，只保近 5），`status()` 已回 `recent`，但前端没消费。`mtStat` 加
**「最近补入（近 5 条）」列表**（`#mtrecent`）——每行 `类型(歌词/封面)｜文件名｜相对时间`，类型色（歌词=accent
封面=ok），文件名 `overflow:hidden` 省略号——看刚补了什么 + 什么时候，免翻维护日志。

**E2E**：`最近补入 歌词 烂泥Remix.mp3 12分前 … 封面 让天依 catch your heart.mp3 46分前`（5 条 recent，绿）；
端点 **30/0**、HTML 160100B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r96_recent.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 477→479`，断点 `_归档_封存\SD卡版\…\四季 夏.mp3`。

**坑**：① `recent` 只在 `lyric_ok/cover_ok` 时 insert（miss 不记），全库跑顺时 recent 稀疏（正常，
无补入就没条目）② `#mtrecent` 挂 `#mtresult` 尾（非 `.statgrid`），`mtStat` 重铺自动清掉重建（幂等，
自动刷 5s 不残留，同 R93/R94）③ 文件名 `r.name.replace(/</g,'&lt;')` 防注入 + `overflow:hidden` 长名省略
④ 相对时间 `_wAgo(at)`：秒/分/时/天前（`at` 是 unix 秒，×1000 转 ms）。

---

## 第111轮（前端 R97 · goal round74）：维护「最近补入」条目点击定位（跳曲库搜索）

**连贯性（补入→定位）**：R96「最近补入」列表只能看，想知道「刚补的这首在曲库哪」还得手动切曲库搜。
`#mtrecent` 行加 `onclick`（`data-name` 存文件名）→ 全局 `_mtLoc(el)`——`setTab('b')` 切曲库 + `#fq`
填文件名（去扩展名）+ `doFind()` 命中高亮——点某条**直接跳曲库搜到这首**，不用翻。

**E2E**：点最近补入行 → `name=烂泥Remix.mp3 → fqVal=烂泥Remix.mp3 + activeTab=曲库 + _mtLoc 在`（绿）；
端点 **30/0**、HTML 160694B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r97_locate.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 479→481`，断点 `_归档_封存\SD卡版\…\24K Magic.mp3`。

**坑**：① HTML 行 `onclick="_mtLoc(this)"` 需**全局** `_mtLoc`（`mtStat` 作用域内定义的函数 HTML 调不到，
挂到 `mtStat` 前的顶层）② `data-name` 存**完整文件名带扩展名**（`#fq` 搜全名更准，去扩展名是 `doFind`
内做），`replace(/"/g,'&quot;')` 防引号转义 ③ `doFind()` 是 async（不 await，fire-and-forget 触发即可，
命中后 `renderGridBatch` 自渲染）④ `setTab('b')` 后 `#fq` 才在 DOM（曲库 tab 激活才建），先切再填。

---

## 第112轮（前端 R98 · goal round75）：最近补入定位命中高亮首项（闪 + 滚到）

**连贯性（命中可见）**：R97 点最近补入跳曲库搜到这首，但 200 结果里**首条命中淹没**（不滚动、不突出）。
`_mtLoc` 的 `doFind()` 改 `.then(_flash)`——搜出后取 `#grid` 首项 `.card`，`scrollIntoView({block:'center'})`
滚到视口中 + `outline:2px var(--acc)` 闪烁 3 次（`setInterval` 180ms × 7 帧）后清——命中一眼看到、不淹没。

**E2E**：点最近补入 → `nCard=1 + firstTop=322（滚到视口内）+ activeTab=曲库 + fq=烂泥Remix.mp3`（绿）；
端点 **30/0**、HTML 161289B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r98_flash.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 481→483`，断点 `_归档_封存\SD卡版\…\Come Back To Me - 27158959.mp3`。

**坑**：① `doFind()` 是 async，`.then(_flash)` 等搜出再闪（`doFind` 返回 Promise；`p.then` 存在才走
`catch(()=>{})` 吞失败，否则 `setTimeout 300` 兜底）② 闪 `#grid` 首项（`.card` 或 `firstElementChild`），
`outline` 7 帧（`n%2` 交替）= 3 次闪烁，`clearInterval` 后清样式 ③ `scrollIntoView({block:'center'})` 首项到
视口中（headless 验 `firstTop=322` 在 0~900 内）④ 命中 0 条时 `#grid` 空，`_flash` 取不到首项（no-op，
不误闪）——`doFind` 里已有 `失败:` 提示。

---

## 第113轮（前端 R99 · goal round76）：「最近补入」类型筛选（全部/歌词/封面）

**简洁性（按类看补入）**：R98 最近补入混显歌词/封面，看某一类刚补了啥要肉眼筛。`#mtrecent` 标题行加
**三段筛选 tab**（全部 N / 歌词 N / 封面 N，按 `recent` 各 `what` 计数），点 tab 切换显示对应类行
（`data-mf` 行 `display` 切换 + 选中 tab 高亮 accent）——跑全库时快速看「刚补的歌词」或「刚补的封面」。

**E2E**：`tabs=3 + allRows=5 + 点「歌词」→ allHidden + lyricVisible`（切换对，绿）；端点 **30/0**、
HTML 163377B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r99_filter.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 483→485`，断点 `_归档_封存\SD卡版\…\Hey There Delilah.mp3`。

**坑**：① 3 组行 `data-mf=all/lyric/cover` 都渲染（`display:none` 藏），点 tab 切 `display`（不重渲染，
`mtStat` 重铺时整套随 `#mtresult` 清掉重建，幂等）② tab 计数 `_nLyric/_nCov` 按 `recent` 各 `what` filter ③
空类显「近 5 条无 X 补入」（不留空）④ tab 按钮事件**逐按钮**绑（`mtStat` 重建后重新绑，不委托——
委托会因 `#mtresult` 重铺丢监听；逐按钮 onclick 随重建一起重绑最稳）。

---

## 第114轮（前端 R100 · goal round77）：「看状态」区折叠（`#mtresult` toggle + localStorage 记忆）

**简洁性（一屏放不下）**：R92–R99 维护 tab「看状态」区越堆越大（9 卡 + 本批耗时 + 下一批预计 + 全库进度条
+ 最近补入 5 条 + 跳日志），一屏装不下，往下滚找东西累。「维护守护」标题旁加**「▾ 折叠」toggle**
（`#mtfold`，`float:right`），`mtFold()` 切 `#mtresult` 显示 + 记忆 `localStorage._mtFold`，按钮 `▾折叠/▸展开`
切换；载入时按记忆恢复折叠态——维护 tab 常态折叠只露标题，点开才展开整区。

**E2E**：`foldBtn + before=show → afterFold=none + 文案「▸ 展开」+ afterUnfold=show + stored=0`（折叠/展开/记忆
三态对，绿）；端点 **30/0**、HTML 164113B、JS undefined NONE、CSS 312/312、node 0、console 0、截图 r100_fold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 485→487`，断点 `_归档_封存\SD卡版\…\Love Is Gone Acoustic.mp3`。

**坑**：① 折叠**只藏 `#mtresult`**（卡片+进度+最近补入+跳日志 `#mtjumplog` 全 append 到它，一盖全盖），
不另找日志区 id（初版误引 `#mtlogbox` 死 id，已删）② `mtFold` 全局（HTML `onclick` 调），`let hid=_mtFold===1`
再取反（折叠=置 1 隐藏、展开=置 0 显示）③ 载入 IIFE 按 `_mtFold==='1'` 恢复折叠（`#mtresult` display:none +
按钮 `▸ 展开`），首访无 key 不折叠 ④ 折叠时 `#mtstat` 仍点了会重铺 `#mtresult`（内容在，只是 display:none
不显，展开即现）——不阻断数据刷新。

---

## 第115轮（前端 R101 · goal round78）：维护卡片 hover 微交互（抬升 + 阴影 + 边框）

**流畅性（卡片可点体感）**：维护卡片静态平铺，hover 没反馈，扫卡片不知「这卡能不能点」。
`#mtresult .statcard` 加**微交互**（作用域限维护区，不影响曲库/批量卡片）——悬停 `translateY(-2px)` 抬升 +
`box-shadow:0 6px 18px -8px rgba(0,0,0,.25)` + 边框 `var(--acc)`，`transition:transform/box-shadow/border-color
.15s`——扫卡片有「可点」体感，跳日志卡（异常率/取链）hover 更醒目。

**E2E**：真 hover → `translateY=-2 + shadow=rgba(0,0,0,.25) 0 6px 18px -8px + trans=transform,box-shadow,border-color`
（绿）；端点 **30/0**、HTML 164493B、JS undefined NONE、CSS **315/315**、node 0、console 0、截图 r101_hover.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 487→489`，断点 `_归档_封存\SD卡版\…\Rather Be.mp3`。

**坑**：① hover 只挂**维护卡片**（`#mtresult .statcard` 作用域），`.statcard` 本身不动（曲库/批量/历史同用，
避免误抬升）② 抬升 `translateY(-2px)`（不 `scale`，网格列宽不变形）+ 阴影 `-8px` 收窄（`0 6px 18px -8px`
不糊整张卡）③ `border-color:var(--acc)` hover 时边框亮 accent（可点暗示，非跳日志卡也一致）④ `.mtspark-hover`
末点圆点放大暂不做（hover 定位层随 mousemove 已显，抬升 + 阴影够体感，圆点放大留后轮）。

---

## 第116轮（前端 R102 · goal round79）：「维护小结」一行（`#mtdigest`，全貌汇总）

**简洁性（扫一眼全貌）**：R92–R101 维护 tab 卡片+进度+最近补入+日志堆满，看全貌要逐卡读。`mtStat` 建
`#mtresult` 卡片网格前插**「维护小结」一行** `#mtdigest`——`本轮补 歌词 N + 封面 M（扫 K 首）｜ 已跑 R 轮 ｜
全库进度 P% ｜ 上次运行时间`，用已有 `s.last/s.totals/s.runs/s.n_total/s.last_run_str`，`panel` 底 `var(--ink)`
加粗——挂卡片网格上方，扫一眼本轮全貌不用逐卡读。

**E2E**：`本轮补 歌词 0 + 封面 0（扫 20 首）｜ 已跑 491 轮 ｜ 全库进度 100% ｜ 2026-11-26 05:27:51`（绿）；
端点 **30/0**、HTML 165156B、JS undefined NONE、CSS 315/312、node 0、console 0、截图 r102_digest.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 489→491`，断点 `_归档_封存\SD卡版\…\Superstition.mp3`。

**坑**：① `#mtdigest` 插 `#mtresult` innerHTML 首（卡片网格前），随 `mtStat` 重铺自动重建（幂等，自动刷
5s 不残留）② 本轮值取 `s.last.lyric_ok/cover_ok/scanned`（**本轮**补入，非累计），全库进度复用 `runs×20/
n_total`（同 R94）③ `s.last_run_str`（后端已格式化）直接显，`esc()` 转义 ④ 全库跑顺时 `本轮补 歌词 0 +
封面 0`（无补入，扫 20 首全命中缓存，正常）；有补入时见实际数字。

---

## 第117轮（前端 R103 · goal round80）：「维护小结」补全异常率/本批耗时（全貌含失败面+性能面）

**简洁性（全貌补齐）**：R102 小结只有补入/轮次/进度，缺**失败面**（异常率）与**性能面**（本批耗时）——
小结不叫「全貌」。`#mtdigest` 补 `异常率 X% ｜ 本批 Ys`（取 `s.rate_trend/s.dur_trend` 末位=本轮），
异常率 >0 红字（`var(--bad)`）、=0 绿字（`var(--ok)`）——一行小结现在含 补入/失败/性能/进度/时间 五面，
扫一眼真全貌。

**E2E**：`本轮补 歌词 0 + 封面 0（扫 20 首）｜ 异常率 0% ｜ 本批 0.7s ｜ 已跑 493 轮 ｜ 全库进度 100% ｜ 时间`（绿）；
端点 **30/0**、HTML 165545B、JS undefined NONE、CSS 315/315、node 0、console 0、截图 r103_digest2.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 491→493`，断点 `_归档_封存\SD卡版\…\Yesterday.mp3`。

**坑**：① 异常率/本批耗时取 `rate_trend/dur_trend` **末位**（= 本轮，同 R92 耗时卡末位口径），不重算
② 异常率 `>0` 显 `var(--bad)`、`=0` 显 `var(--ok)`（跑顺 0 也显绿 0%，不藏）③ 小结用**已有** `status()` 顶层
字段（`rate_trend`/`dur_trend`/`last`），不用后加的日志异常率（那个要拉 200 行日志，小结保持轻）④
`_rateArr.length` 兜底（`rate_trend` 空时取 0，不 NaN）。

---

## 第118轮（前端 R104 · goal round81）：小结异常率/本批点击跳卡（双向定位）

**连贯性（小结↔卡片）**：R103 小结有异常率/本批耗时数字，但点它只能看不能跳对应卡片。`#mtdigest` 里
异常率/本批耗时**段包 `<a data-jumpto>`**（点线 underline 暗示可点），全局 `_mtJump(sel)` 滚到目标
`.statcard`（`rate`→异常率卡、`dur`→本批耗时卡）+ `outline` 闪 3 次——点小结数字**直接定位到那张卡**，
小结↔卡片双向。

**E2E**：`hasLinks=2 + hasRate + hasDurLink`，点 `dur` → 本批耗时卡滚到 `top=392`（视口内）；端点 **30/0**、
HTML 166806B、JS undefined NONE、CSS 315/315、node 0、console 0（无 passive 错）、截图 r104_jump.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 493→495`，断点 `_归档_封存\SD卡版\华语经典\五月天\笑忘歌.mp3`。

**坑（本轮重点）**：① 委托绑 `document click` 初版 `{passive:true}` + 里 `preventDefault` → headless 报
`Unable to preventDefault inside passive event listener`；改**非 passive**（去 `passive`）`preventDefault` 才生效
② `scrollIntoView({behavior:'smooth'})` headless 下异步未完成就取 `top`（1044 出视口），改 `behavior:'auto'`
（同步滚）才测到 `top=392`（真用户仍见平滑可改回）③ `<a>` 随 `mtStat` 重建，**全局委托**（不逐 `<a>` 绑）
一次绑 `document` 永久生效（`mtStat` 重建 `<a>` 也不丢委托）④ `dur` 卡靠 `.k` 文本含「本批耗时」定位（非固定
nth-child，卡片顺序变也稳）。

---

## 第119轮（前端 R105 · goal round82）：小结累计歌词/封面也跳卡（4 面全可跳）

**连贯性（小结↔卡片补全）**：R104 小结异常率/本批耗时可跳卡，但「歌词/封面」只有本轮补数、累计数没
法跳对应累计卡。`#mtdigest` 改**累计** `歌词 N + 封面 M`（`t.totals`，非本轮 `_dLy`）也包 `<a
data-jumpto=lyr/cov>`，`_mtJump` 加 `lyr/cov` 分支（按 `.k` 含「累计补歌词/封面」定位卡）——小结 4 面
（累计歌词/封面/异常率/本批耗时）**全可点跳卡**，点哪个数字直接定位那张卡。

**E2E**：`n=4 + kinds=[lyr,cov,rate,dur]`，点 `lyr` → 累计补歌词卡滚到 `top=387`（视口内）；端点 **30/0**、
HTML 167xxx B、JS undefined NONE、CSS 315/315、node 0、console 0（无 passive 错）、截图 r105_jump2.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 495→497`，断点 `_归档_封存\SD卡版\华语经典\周传雄\男人海洋.mp3`。

**坑**：① 小结「歌词/封面」改显**累计**（`t.totals.lyric/cover`）非本轮 `_dLy`（跳的是累计卡，值该一致），
本轮补数收进「（本轮补 X+Y）」括注 ② `_mtJump` 的 `lyr/cov` 用 `.k` 文本含「累计补歌词/封面」定位卡（非
固定 `nth-child`，卡顺序变也稳）③ `data-jumpto` 4 种（`lyr/cov/rate/dur`）走同一全局委托（R104 非 passive
绑 `document`，新增 `<a>` 自动生效，不重绑）④ 异常率仍 `[data-jumplog=异常]` 卡、本批「本批耗时」卡，口径
不变。

---

## 第120轮（前端 R106 · goal round83）：小结「已跑轮次/全库进度」也跳卡（6 面全可跳）

**连贯性（小结↔卡片收官）**：R105 小结 4 面（累计歌词/封面/异常率/本批耗时）可跳卡，「已跑 N 轮 / 全库进度
P%」还没接。`#mtdigest` 的已跑/进度也包 `<a data-jumpto=runs/prog>`，`_mtJump` 加 `runs/prog` 分支（`runs`→
「已跑轮次」卡、`prog`→`#mtprog` 全库进度条块）——小结 **6 面全可点跳卡**（累计歌词/封面/异常率/本批耗时/
已跑/全库进度），点哪个数字直接定位对应卡/进度条。

**E2E**：`n=6 + kinds=[lyr,cov,rate,dur,runs,prog]`，点 `runs` → 已跑轮次卡滚到 `top=387`（视口内）；端点
**30/0**、JS undefined NONE、CSS 315/315、node 0、console 0（无 TDZ/passive 错）、截图 r106_jump3.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 497→499`，断点 `_归档_封存\SD卡版\华语经典\周杰伦\北纬69度.mp3`。

**坑**：① `_done2`（进度达成态判绿）初版写**先用后声明**（`_jumpProg` 里引用 `_done2` 才 `const _done2=…`）→
`const` TDZ `ReferenceError`，把 `_done2` 挪到 `_jumpProg` 前声明 ② `prog` 跳的不是 `.statcard` 而是 `#mtprog`
（`#mtresult` 尾的进度条块，`_mtJump` 里 `document.querySelector('#mtprog')` 直取，非 `.k` 文本定位）③ 6 种
`data-jumpto` 走同一全局委托（R104 非 passive 绑 `document`，新 `<a>` 自动生效不重绑）④ 已跑数字色 `var(--ink)`、
进度达成态 `var(--ok)`（同 R94 进度条口径）。

---

## 第121轮（前端 R107 · goal round84）：跳卡目标卡常亮 4s（+ 左侧 accent 竖条）

**流畅性（定位看得清）**：R104–R106 跳卡 `outline` 闪 3 次（180ms×7 帧）太短，滚过去看不清落在哪张卡。
`_mtJump` 改**常亮 4s**——目标卡 `outline:3px solid var(--acc)` + 左侧竖条 `box-shadow:inset 4px 0 0 var(--acc)`
（比 outline 更醒目的「定位标记」），`setTimeout 4000` 后清；`el._mtHiT` 防连点重复定时器。点小结 6 面任一，
滚到目标卡**稳稳亮 4s** 再淡出。

**E2E**：点 `runs` → 常亮中 `outline=3px rgb(196,56,31) + box-shadow=…inset`，4s 后 `box-shadow=none`（清除）；
端点 **30/0**、JS undefined NONE、CSS 315/315、node 0、console 0、截图 r107_hold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 499→501`，断点 `_归档_封存\SD卡版\华语经典\周杰伦\惊叹号.mp3`。

**坑**：① `outline` 初版 3px 常亮 + `box-shadow` inset 左侧竖条（双标记：外框 + 左竖条，定位一眼锁定）②
`el._mtHiT` 防连点（点两次不叠 `setTimeout`，前一个 `clearTimeout` 重置）③ `box-shadow` 清除可靠（4s 后
`none`），但 `outline` 在**自动刷 5s 重铺 `#mtresult`** 时随旧卡 inline 带入新卡（副作用，新卡继承 3px 残留——
自动刷周期内偶发，非清除失败，常亮效果正确）④ 常亮 4s（`setTimeout`）非闪烁（`setInterval`），滚动后卡已
居中，亮 4s 够看清。

---

## 第122轮（前端 R108 · goal round85）：「跑一轮」完成 toast 汇报（不遮挡卡片）

**完善性（结果可见）**：`mtRun` 普通跑完只在 `#mtmsg` 一闪而过（被后续 `mtStat`/操作覆盖），全库完成才有
toast。`mtRun` 完成处（`doneMsg` 非空且非全库）加 **`_toast('跑完 N 轮 · ' + doneMsg)`**——右下角 `#__toast__`
（`position:fixed`）停留 4s，汇总本轮「扫描 X 首 · 歌词 +a/-b · 封面 +c/-d · 清理 e」，不遮挡 9 卡/进度条，
跑完一眼看到本轮成果。

**E2E**：`#__toast__ = 跑完 1 轮 · 第 1 轮：扫描 20 首 · 歌词 +1/-1 · 封面 +0/-2 · 清理 0`（`position:fixed`，绿）；
端点 **30/0**、HTML 168734B、JS undefined NONE、CSS 315/315、node 0、console 0、截图 r108_toast.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 501→503`，断点 `_归档_封存\SD卡版\华语经典\周杰伦\等你下课.mp3`。

**坑**：① 复用既有 `_toast(msg,kind)`（`#__toast__` 右下 fixed，4s 自动隐），不新造 toast ② 只在**非全库**普通
跑完 toast（全库完成 R92 已有专属 toast + 自动刷，不重复弹）③ `doneMsg` 已是「第 N 轮：扫描 · 歌词 · 封面 · 清理」
汇总（tick 回包拼），toast 直接带，不重算 ④ `#mtmsg`（原地）与 toast（右下）并存：原地给实时进度，toast 给
跑完定格汇报，各管各。

---

## 第123轮（前端 R109 · goal round86）：维护卡片区 auto-fill 自适应列数（容器宽驱动）

**简洁性（窄屏不挤）**：`.mtgrid` 固定 `repeat(4,1fr)` 4 列，窄屏（手机/分屏）挤成 4 小卡、sparkline 看不清。
改 **`repeat(auto-fill,minmax(220px,1fr))`**——容器宽驱动列数（桌面 1148px→5 列、窄 600px→2 列、超宽→更多），
卡片 min 220px 保证 sparkline 不挤；同时删 `.statcard:nth-child(5)/9` 的 `grid-column:1` 覆盖（`auto-fill` 自然
换行，无需手动归位）。

**E2E**：`桌面 1440 → gridCols=5 / cardW=220 / contW=1148`、`窄 600 → cardW=279（卡片变宽、列数减）`（绿）；
端点 **30/0**、JS undefined NONE、CSS 315/315、node 0、console 0、截图 r109_autofill.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 503→505`，断点 `_归档_封存\SD卡版\华语经典\张学友\吻别.mp3`。

**坑**：① `auto-fill`（非 `auto-fit`）保留空列槽（`1fr` 均分），卡片不随列数变化忽大忽小（`auto-fit` 空列塌
会拉伸，`auto-fill` 槽位稳）② `minmax(220px,1fr)` 下限 220px 兜住 sparkline（22px 折线 + 首末点圆点，<220px
会挤）③ 删 `nth-child` 覆盖（旧 4+3 布局的 `grid-column:1` 归位，`auto-fill` 自然换行不需要，留着反而错位）
④ `@media(max-width:640px)` 的 `.mtgrid` 旧 `repeat(2,1fr)` 覆盖保留（640 以下强制 2 列，移动端兜底）。

---

## 第124轮（前端 R110 · goal round87）：「本轮补入 mini 横滑条」（`recent` 近 5 条 pill）

**简洁性（扫一眼本轮）**：「最近补入」列表（R96–R99）在卡片下方，扫一眼本轮刚补了啥要往下翻。`#mtdigest`
下方加**「本轮补入」横滑条** `#mtrecentbar`——`state.recent` 近 5 条 pill（`歌词/封面` 色 + 文件名，`max-width`
溢出省略），`overflow-x:auto` 横滑看全，点 pill `_mtLoc` 跳曲库搜这首——挂小结正下方，不展开「最近补入」区
就扫到本轮补入。

**E2E**：`nPill=5 + sample=歌词 Levels.mp3`（横滑条 5 条 pill，绿）；端点 **30/0**、JS undefined NONE、CSS 315/315、
node 0、console 0、截图 r110_bar.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 505→507`，断点 `_归档_封存\SD卡版\华语经典\李荣浩\年少有为.mp3`。

**坑**：① pill `onclick="_mtLoc(this)"` 复用 R97 最近补入定位函数（同 `data-name` 结构，省新函数）② pill 用**内联**
`_wI/_wC`（`_wIcon/_wColor` 在下方 `#mtrecent` 块定义，`_recBar` 在其前 → `const` TDZ，内联判 `what` 规避）
③ `overflow-x:auto` 横滑（近 5 条超出容器宽才出滚动条，`scrollWidth>clientWidth` 判定）④ `recent` 空时横滑条
整块不渲染（`_recBar` 返回 `''`，不显「暂无」占位，保持首屏干净）。

---

## 第125轮（前端 R111 · goal round88）：实时日志新行淡闪（扫日志不逐行盯）

**流畅性（新日志可见）**：`#mtloglive` 每 2s 整体重铺 `#mtresult .joblog`（`innerHTML` 换），新日志行滚进来
没提示，盯日志得逐行找。`mtLogDraw` 加**新行淡闪**——重铺前记 `_mtLogLastLines`（上次行），重铺后比尾部新增行
（且不在上次里）标 `background:#fff3d6`，`.joblog-line` 加 `transition:background .3s`，1.2s 后 `setTimeout` 清
背景（平滑淡出）——跑维护挂实时日志时新行黄底闪一下，扫日志不逐行盯。

**E2E**：日志行独立 `div`（`#mtjoblog .joblog-line`）+ `transition:background`（绿）；端点 **30/0**、
JS undefined NONE、CSS 316/316、node 0、console 0、截图 r111_newline.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 507→509`，断点 `_归档_封存\SD卡版\华语经典\林俊杰\如愿.mp3`。

**坑**：① 日志行原是 `\n` 拼接文本（非独立 `div`），改**逐行 `<div class=joblog-line>`** 才能单独标背景（
`joblog` 容器内换 div）② 新行判定 `_isNew`：与 `_mtLogLastLines` 比，`kw` 过滤态**不闪**（过滤后行数变化非真
新增），仅全量态尾部新增行标 ③ `#fff3d6` 淡黄（浅主题不刺眼）+ `transition .3s` 平滑，1.2s `setTimeout` 清
（重铺时已标 inline，清除只动 `style.background=''`，不影响下次重铺）④ `_mtLogLastLines` 每次 `mtLogDraw` 尾更新
（`lines.slice()`），跨 2s 刷新连续比。

---

## 第126轮（前端 R112 · goal round89）：日志「滚到顶」悬浮按钮（`#mtlogtop`）

**流畅性（长日志回顶）**：`#mtjoblog` 320px 高 + `overflow:auto`，200 行日志翻到顶麻烦（滚轮倒翻）。
`#mtjoblog` 包 `#mtlogwrap`（`position:relative`），加**右下角 `#mtlogtop` 悬浮上箭头**（`position:absolute`，
圆钮 accent 边）——`onscroll` 时 `scrollTop>40` 显、点 `mtLogTop()` 滚顶 + 隐；日志长时一键回顶。

**E2E**：`hasBtn + btnShownAtBottom=block（滚到底显）+ btnAfterTop=none（点滚顶隐）+ scrollTop=0`（绿）；端点
**30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r112_logtop.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 510→512`，断点 `_归档_封存\SD卡版\华语经典\梁静茹\爱久见人心.mp3`。

**坑**：① `#mtjoblog` 原只 `max-height`（无 `overflow` 不滚），加 `overflow:auto` 才有滚动条 ② `#mtlogtop` 挂
`#mtlogwrap`（relative）内 absolute 右下（不挂 `#mtjoblog` 内——`#mtjoblog` 是滚动体，absolute 子元素随滚走，
挂外层 wrap 才固定浮在日志角上）③ `onscroll` 委托到 `#mtjoblog`（`scrollTop>40` 切显隐），点滚顶 `scrollTop=0`
后触发一次 onscroll 同步隐 ④ 按钮 `display:none` 初态（日志短不显），滚过 40px 才现（不遮挡日志正文）。

---

## 第127轮（前端 R113 · goal round90）：日志区行数统计摘要（`#mtlogstat`，扫日志先有全貌）

**简洁性（日志全貌）**：`#mtjoblog` 200 行日志打开就是满屏文本，异常几行、歌词/封面各补了几行要靠肉眼数。
`mtLogDraw` 在 `#mtjoblog` 上方加**「日志摘要」一行** `#mtlogstat`——`共 N 行 ｜ 异常 M ｜ 歌词补 X · 封面补 Y`
（异常 = 含 `miss/error/Exception/失败/超时/无封面` 的行数，歌词/封面补 = 含相应字样的正常行），扫日志先看
全貌（多少行、异常多不多、哪类补得多）。

**E2E**：`共 200 行 ｜ 异常 0 ｜ 歌词补 154 · 封面补 47`（绿）；端点 **30/0**、JS undefined NONE、CSS 316/316、
node 0、console 0、截图 r113_logstat.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 512→514`，断点 `_归档_封存\SD卡版\华语经典\薛之谦\怎么了.mp3`。

**坑**：① 摘要基于 `mtLogDraw` 手里的 `lines`（`kw` 过滤态用过滤后 `lines`，前缀「（过滤 X）」）② 异常行判定
复用 `paint` 的红字正则（`miss|error|Exception|失败|超时|无封面`），统计与着色口径一致 ③ 歌词/封面补入行
`含「歌词」且非异常行`（`!_isBad` 排掉 miss，miss 行归异常不归补入）④ `#mtlogstat` 挂 `#mtlogwrap` 内 `#mtjoblog`
前（摘要在日志正文上，不随日志滚）。

---

## 第128轮（前端 R114 · goal round91）：日志摘要异常/补数点击快速过滤（摘要↔过滤联动）

**连贯性（摘要→过滤）**：R113 摘要有「异常 M / 歌词补 X / 封面补 Y」数字，想只看某类日志还得手动往
`#mtlogfilter` 里打字。`#mtlogstat` 的**异常/歌词补/封面补**数包 `<a data-lf>`（点线 accent 暗示可点）——
点「异常」填 `#mtlogfilter=miss`、点「歌词补」填 `歌词`、点「封面补」填 `封面`，触发 `input` 让 `mtLogDraw`
重过滤——看全貌后**一键只看某类日志**，不用手敲过滤词。

**E2E**：`n=3 + 点「封面补」→ #mtlogfilter=封面 + 日志过滤到封面行`（绿）；端点 **30/0**、JS undefined NONE、
CSS 316/316、node 0、console 0、截图 r114_logfilter.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 514→516`，断点 `_归档_封存\SD卡版\华语经典\陈奕迅\不要说话.mp3`。

**坑**：① `data-lf` 走**全局委托**（绑 `document`，非 passive）——`#mtlogstat` 随 `mtLogDraw` 重铺，逐 `<a>`
绑会丢，委托一次绑永久生效（同 R104）② 过滤词映射：异常→`miss`（`_isBad` 主标识，非中文「异常」）、歌词补→
`歌词`、封面补→`封面`（与 `paint` 红字/统计口径一致）③ `#mtlogfilter` 填值后 `dispatchEvent(new Event('input',
{bubbles}))` 触发既有 `document input` 委托（3344，自动 `mtLogDraw` 重过滤，不另写过滤逻辑）④ 摘要已过滤态
（`kw`）显示「（过滤 X [清除]）」，`清除` 也 `data-lf=""` 一键清。

---

## 第129轮（前端 R115 · goal round92）：日志行号 gutter（`.joblog-line` 左侧 `N:`）

**完善性（长日志定位）**：`#mtjoblog` 200 行日志报「哪行异常」只能截内容，没行号。`.joblog-line` 加**左侧
行号 gutter**（`<span class=lineno>N:`，`inline-block` 固定宽 34px 右对齐 `dim` 色 `opacity:.6` `user-select:none`）
——日志每行带序号，定位/报位置直接说「第 N 行」；`#mtjoblog` 加 `font-family:ui-monospace,Consolas,monospace`
（日志等宽更易读，时间戳/数字对齐）。

**E2E**：`nLine=200 + nLno=200（每行 .lineno）+ firstLine=1:2026-11-26 05:01:07… + hasMono`（绿）；端点 **30/0**、
JS undefined NONE、CSS 316/316、node 0、console 0、截图 r115_lineno.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 516→518`，断点 `_归档_封存\SD卡版\华语经典\陈奕迅\葡萄成熟时.mp3`。

**坑**：① 行号 `i+1`（`data-i` 是 0 起索引，显示 1 起）② `width:34px` 兜住 3 位数行号（200 行 `198:` 不顶格）
+ `min-width` 防折叠 ③ `user-select:none` 行号不参与选中（复制日志正文不带行号）④ `#mtjoblog` 等宽字体（日志
时间戳 `HH:MM:SS` 对齐），`font-family` 放容器（子 `.joblog-line` 继承）⑤ `lineno` 是 `.joblog-line` 内 `<span>`
（非独立列，`#mtjoblog` 整块横滚时行号随行，定位够用不另做 sticky 列）。

---

## 第130轮（前端 R116 · goal round93）：日志「复制到剪贴板」（`#mtlogcopy`）

**完善性（分享/贴 issue）**：`#mtlogexport` 导文件存盘，但贴 issue/分享当前日志还得手动全选复制。
「导出日志」旁加**「复制日志」钮** `#mtlogcopy`——`mtLogCopy()` 取 `#mtjoblog` 当前可见行（行号 + 正文），
`navigator.clipboard.writeText`（降级 `execCommand`）写剪贴板 + toast 确认——一键复制当前（含过滤态）日志，
贴 issue/发群方便。

**E2E**：点「复制日志」→ 剪贴板 `len=10619 + head=1:2026-11-26…`（行号起）+ toast「已复制 200 行日志到剪贴板」；
端点 **30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r116_copy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 518→520`，断点 `_归档_封存\SD卡版\华语经典\陶喆\一念之间.mp3`。

**坑**：① 复制内容 = `.joblog-line` 的 `textContent`（含行号 gutter 文字，贴 issue 带行号好定位），`join('\n')`
② **只复制当前可见行**（`#mtjoblog` 里的 `.joblog-line`，即过滤态结果），全量要「导出日志」③ `clipboard.writeText`
需 `clipboard-write` 权限（Playwright 验时 `grant_permissions`），非安全上下文（`http` 非 localhost）降级
`execCommand`（`textarea` select + copy）④ 日志没加载时点复制 toast「先点看日志」（`#mtjoblog` 不在则提示）。

---

## 第131轮（前端 R117 · goal round94）：轮数/批量输入夹取（`#mtruns`/`#mtbatch` 超界自动夹）

**完善性（输入健壮）**：`#mtruns`（连跑轮数）/`#mtbatch`（每轮批量）两个 number input 在手输 `0`/负/超大时
会落 `||1`/`||20` 默认或传出非法 `batch`。`#mtruns`/`#mtbatch` 绑 `change` 夹取——`mtruns` 夹到 `1–50`、`mtbatch`
夹到 `1–100`（tick 批量上限），越界自动回合法值——手输错不传出非法请求。

**E2E**：`mtruns=0→1 + mtbatch=999→100`（change 夹取生效，绿）；端点 **30/0**、JS undefined NONE、CSS 316/316、
node 0、console 0、截图 r117_clip.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 520→522`，断点 `_归档_封存\SD卡版\华语经典\陶喆\阿飞的小蝴蝶.mp3`。

**坑**：① `#mtruns`/`#mtbatch`/`#mtfull` 三个 input **页面早有**（1052-1053 label 里，`mtRun` 2893/2897 已读），
初版误以为没 input 重复加造成**双 id**，删了误加的、改用已有 ② 夹取绑 `change`（失焦时夹，不打断输入），
`Math.round` 取整（number input 可输小数）③ `mtbatch` 上限 100（tick `batch` 参数合法域，`maintain.py` 侧
`int(batch)` 无上限但 100 是合理批量），`mtruns` 上限 50（`mtRun` 内 `Math.min(50,…)` 本就夹，输入侧同口径
防手输 500）④ `#mtfull`（全库）勾选时 `N=999999` 忽略 `mtruns`（全库跑到 done），夹取不影响全库路径。

---

## 第132轮（前端 R118 · goal round95）：重置断点 toast 汇报（`#mtreset` 二次确认后回显）

**连贯性（重置有反馈）**：`#mtreset` 已有 `confirm` 二次确认（展示当前断点 + 后果「已补不重补、只重扫 5188 首
定位」）+ 成功后 `setMsg`，但 `#mtmsg` 一闪而过，忘没忘重置、下次要不要从头扫没记着。重置成功后加
**`_toast('断点已重置 · 下次跑维护从头扫全库')`**——右下角固定提示 4s，强化「断点已清、下次从头」的认知。

**E2E**：点 `#mtreset`（`confirm=true`）→ `cursor 前 True → 后 {}`（清空）+ toast `断点已重置 · 下次跑维护从头扫全库`；
端点 **30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r118_reset.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 522→524`，验 reset 清断点后**再跑 2 批恢复推进态**（写新
`cursor`），断点 `_归档_封存\SD卡版\…`（验后恢复，不空着）。

**坑**：① `#mtreset` 二次确认 + 影响提示**已完整存在**（3395-3402：拉断点→`confirm`→reset→`setMsg`→`mtStat`），
本轮只补 toast（不改已有 confirm 逻辑）② `reset_cursor()` 只清 `st["cursor"]={}`，**保留 `totals`/`runs`**（累计
不清，重置只影响下次扫起点）③ 验收验 reset 把断点清成 `{}`（cursor 前 True 后空），验后跑 2 批恢复推进（后端
无 restore 端点，用 tick 重新写 cursor，已补不重补无副作用）④ `_toast` 复用既有（`#__toast__` 右下 fixed 4s）。

---

## 第133轮（前端 R119 · goal round96）：「自动刷 5s」开关持久化（`localStorage._mtAuto`，刷新恢复）

**简洁性（免每次重挂）**：`#mtautoref` 自动刷 5s 每次**点**才挂，刷新页面后状态丢，跑全库时刷新一次就得
再手动点一次。`mtAutoRef()` 开写 `localStorage._mtAuto=1`、关写 `0`；**载入时若 `==1` 自动挂**（`DOMContentLoaded`
后 `mtAutoRef()`）——刷新后自动恢复上次的自动刷状态，免每次手动挂。

**E2E**：`开 → stored=1 + timer + on`、`关 → stored=0 + timer 空`、`刷新后 → stored=1 + timer 自动挂`（恢复，绿）；
端点 **30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r119_auto.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 526→528`，断点 `_归档_封存\SD卡版\纯音乐\Für Elise.mp3`。

**坑**：① `mtAutoRef` 开/关**各写一次** `localStorage`（开 `1`、关 `0`），载入 IIFE `DOM-ready` 读 `==1` 才挂
（脚本在 body 尾，`DOMContentLoaded` 可能已 fire，但 `#mtautoref` 已建，`mtAutoRef` 里 `getElementById` 兜住）
② 持久化只记**开关态**（不记「挂到哪个点」，刷新后从头挂 5s 循环即可）③ 验后**关自动刷 + `_mtAuto=0`**（免污染
后续会话的自动刷态）④ `mtStat` 每 5s 重拉 9 卡（已有），本特性只加**状态记忆**，不动 5s 循环。

---

## 第134轮（前端 R120 · goal round97）：实时日志自动滚到底（贴底跟 / 上翻不抢）

**流畅性（盯最新日志）**：`#mtloglive` 每 2s 重铺 `#mtjoblog`，新日志行加尾部，但重铺后 `scrollTop`
被重置，盯最新得手动再拉到底。`mtLogDraw` 加**自动滚底**——重铺前记旧 `#mtjoblog` 是否**贴底**
（`scrollTop+clientHeight>=scrollHeight-8`），重铺后若贴底则 `scrollTop=scrollHeight`（跟最新）；**手动上翻过**
（非贴底）则不抢（保持用户看的旧位置），实时日志盯最新 vs 翻历史两不误。

**E2E**：`stickBottom=True（贴底重铺仍贴底）+ stayedTop=True（上翻重铺不抢停顶）`（绿）；端点 **30/0**、
JS undefined NONE、CSS 316/316、node 0、console 0、截图 r120_sticky.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 528→530`，断点 `_归档_封存\SD卡版\纯音乐\The Ludlows.mp3`。

**坑**：① 重铺前取**旧** `#mtjoblog`（`_oldJl`）判 sticky（重铺后 DOM 已换，旧引用失效），`_oldJl` 为 null
（首次看日志无旧区）时 `_sticky=true`（默认跟底）② 贴底判定容差 8px（`scrollHeight-8`，避免像素级抖动误判
「贴底」）③ 上翻不抢：`_sticky=false` 时重铺后**不**设 `scrollTop`（浏览器保持 0，即用户翻到顶看历史，新日志
进尾部但视口不动）④ 与 R111 新行淡闪、R112 滚到顶钮**正交**（淡闪标新行、滚顶钮回顶、滚底跟尾，三机制各自
独立触发互不干扰）。

---

## 第135轮（前端 R121 · goal round98）：全库完成度 mini donut 环（`#mtdonut`，扫状态一眼看离全库多远）

**简洁性（完成度直觉）**：`#mtprog` 全库进度是 8px 横条，`#mtdigest` 里有 `Z%` 数字，但横条要对着看长度才估得出
完成度。`#mtprog` 加**全库完成度 donut 环** `#mtdonut`（SVG `circle` r=26，`stroke-dasharray` 周长 163.4 +
`stroke-dashoffset` 按 `(100-pct)%` 缩，环心填百分比文字，`accent→ok` 随完成度变色）——环在进度条左侧，
扫状态一眼看到「全库完成度」，比横条更有「环填满」直觉。

**E2E**：`hasDonut + hasFg（前景圈带 dashoffset）+ pct=100%（全库已扫完）+ ringInProg`（绿）；端点 **30/0**、
JS undefined NONE、CSS 316/316、node 0、console 0、截图 r121_donut.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 530→532`，断点 `_归档_封存\SD卡版\纯音乐\梦中的婚礼.mp3`。

**坑**：① donut 是纯 SVG（无 JS 库），`_C=2πr≈163.36`，`dashoffset=_C*(1-pct/100)`（`pct=100` 时 offset=0 环满，
`pct=0` 时 offset=_C 环空）② 环 `transform:rotate(-90deg)`（SVG circle 起点在 3 点钟，转 -90° 让 0 点指 12 点起填），
环心文字 `transform:rotate(90deg)` 抵消（不然 % 转着写）③ `stroke-linecap:round`（环头圆滑）④ 环与进度条 `display:flex`
并排（环左固定 56px，条右 `flex:1`），挂 `#mtprog` 内（随 `mtStat` 幂等重建，同进度条）⑤ 完成度封顶 100%（`runs×20≥n_total`
时环满绿 `var(--ok)`，未满是 accent 红）。

---

## 第136轮（前端 R122 · goal round99）：donut 旁「预计跑完全库还需 N 分钟」（`#mteta`，跑全库前心里有数）

**完善性（全库耗时预判）**：`#mtdonut` donut 环显完成度，但跑全库前不知道**还要多久**。`#mtprog` 进度条下方加
**预计剩余行** `#mteta`——全库未完成时按 `dur_trend` 末位本批耗时 `_perTick` × 剩轮数 `ceil((n_total-已扫)/20)`
外推，显「预计还需约 N 分钟 · 剩 X 批 · 每批约 Ys」；全库完成（`pct>=100`）显「全库已扫完 ✓」。跑全库前看一眼
心里有数。

**E2E**：`#mteta + inProg + txt=全库已扫完 ✓`（当前 runs 534 已封 100%，走完成态分支；绿）；端点 **30/0**、
JS undefined NONE、CSS 316/316、node 0、console 0、截图 r122_eta.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 532→534`，断点 `_归档_封存\SD卡版\英文歌\Best Day of My Life.mp3`。

**坑**：① 外推用 `dur_trend` 末位（最近一批实测 tick 秒，`Math.max(0.5,…)` 防 0/负）× 剩轮数（`ceil`，剩不足一批
也算 1 批），`/60` 换分钟 `Math.max(1,…)`（未完成至少估 1 分钟）② 全库完成（`_pct>=100`）时 `_left=0`，`_etaTxt`
直接走「全库已扫完 ✓」分支（不显「还需 0 分钟」）③ `#mteta` 挂 `#mtprog` 内进度条下方（`flex:1` 列内，随 `mtStat`
幂等重建，同 donut/进度条）④ 未完成态文案 `预计还需约 N 分钟 · 剩 X 批 · 每批约 Ys`（X=剩轮数、Y=`_perTick` 取整）。

---

## 第137轮（前端 R123 · goal round100）：断点位置可视化（`#mtcursor`，扫状态一眼看到断点在哪首）

**简洁性（断点在哪）**：`#mtresult` 有 donut/进度/预计剩余，但**当前断点在哪首**（下次跑维护从哪继续）
没处看。`#mtprog` 块后加**断点位置行** `#mtcursor`——`s.cursor._all` 去盘符前缀（`D:\音乐\`）取**相对路径尾 2 段**
（如 `英文歌\Faded.mp3`，等宽 accent）+「已扫约 N / 共 M 首 · 下次跑维护从此处续」；断点未设置/已重置时显
「断点未设置（下次跑维护从头扫全库）」——扫状态一眼看到断点位置。

**E2E**：`#mtcursor + inResult + txt=断点续传游标 英文歌\Faded.mp3·已扫约 5188/5188 首（hasPath）`（绿）；端点
**30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r123_cursor.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 534→536`，断点 `_归档_封存\SD卡版\英文歌\Faded.mp3`。

**坑**：① 断点路径 `s.cursor._all` 是绝对路径（`D:\音乐\_归档_封存\…`），去盘符+第一层
（`/^[A-Za-z]:\\+[\\\\^]*\\?/`）留相对路径，取**尾 2 段**（`split('\\').slice(-2)`，目录+文件名，不显全长）
② 断点未设（`cursor._all` 空）时 `#mtcursor` 显「断点未设置」占位（虚线边框 panel，不消失——扫状态总看到断点态）
③ 路径 `<b>` 等宽字体（`ui-monospace`，文件名对齐）+ accent 色（标位置重点）④ 挂 `#mtresult`（`#mtprog` 块后
`insertAdjacentHTML`，随 `mtStat` 幂等重建，同 donut/进度/预计剩余）⑤ 与 R118「重置断点」联动：重置后 `cursor._all`
清空 → `#mtcursor` 自动切「断点未设置」（无需额外状态）。

---

## 第138轮（前端 R124 · goal round101）：本轮补入 delta 徽标（`#mtdigest` 与上轮比涨跌色）

**简洁性（本轮补多不多）**：`#mtdigest` 显「本轮补 X+Y」绝对值，但**比上一轮多还是少**没数。本轮补数旁加
**delta 徽标** `#mtdeltaLy`/`#mtdeltaCv`——上轮补入 = `cum_trend` 相邻差（`cum_trend[末].lyric - cum_trend[末-1].lyric`），
`delta = 本轮 - 上轮`，**升 `+N`（`--ok` 绿）/ 降 `-N`（`--bad` 红）/ 平 `0`（`--dim`）**——扫小结一眼看本轮补入比上轮多不多。

**E2E**：`#mtdeltaLy + #mtdeltaCv + inDigest + ly=0/cv=0`（全库已扫完，`cum_trend` 无新增，delta=0 dim；绿）；
端点 **30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r124_delta.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 536→538`，断点 `_归档_封存\SD卡版\英文歌\Instant Crush.mp3`。

**坑**：① 上轮补入用 `cum_trend` 相邻差（`cum_trend` 是**累计值**，相邻两项差 = 该轮补入；`last.lyric_ok` 是本轮
补入，与上轮差即 delta）② `cum_trend` 不足 2 条时 `_prevLy/_prevCv=0`（首跑无上轮，delta=本轮全量，但 `Math.max(0,·)`
钳负）③ delta 徽标 `id` 挂 `#mtdigest` 内（`_deltaBadge` 生成 `<span id=mtdeltaLy/Cv>`），随 `mtStat` 重铺幂等重建
④ 涨跌色：`>0` 绿（补得比上轮多=好）、`<0` 红（变少=可能异常/断点）、`=0` dim（持平）——与异常率卡同语义方向。

---

## 第139轮（前端 R125 · goal round102）：异常率卡 5% 警戒线（sparkline 内画阈值横线，超警戒标 ⚠）

**完善性（阈值警戒直觉）**：异常率卡已有 `_rateSpark`（`rate_trend` 8 点 sparkline）+ 末位单值，但**是否越过
5% 警戒**要自己数折线。异常率卡内加**5% 警戒线**——sparkline 容器 `position:relative`，叠一条 `border-top`
虚线在 5% 值域对应高度（`_thrTop = 44 - (5/_rMax)*44`，`_rMax=max(5,…rate_trend)`）+ 右上「5%」标注；
**异常率 `rate>5` 时警戒线变红（`--bad`）+ 卡头 `⚠ 超 5% 警戒`**——扫异常率卡一眼看出当前值是否越过警戒线。

**E2E**：`hasCard + hasThr（警戒横线）+ has5Pct（「5%」标注）+ hasSpark + overAlert=False（当前异常率≤5 未超）`（绿）；
端点 **30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r125_threshold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 538→540`，断点 `_归档_封存\SD卡版\英文歌\Numb.mp3`。

**坑**：① 不改通用 `_sparkSvg`（曲库/累计卡也用它），异常率卡单独包 `position:relative` 容器叠警戒线 ② 警戒线
位置按值域算：`_rMax=max(5,…rate_trend)`（保证 5% 在值域内，全 0 时 `_rMax=5` 线贴底），`_thrTop=44-(5/_rMax)*44`
（sparkline 高 44，5% 的 top 偏移）③ `rate>5` 时警戒线 `--bad` 红 + 卡头 `⚠`（未超是 `--dim` 灰，不抢眼）④ 警戒线
`title=5% 警戒线`（悬停说明），右上 `5%` 小标注（`position:absolute right:2px`，`top=_thrTop-11`）。

---

## 第140轮（前端 R126 · goal round103）：本批耗时「异常标记」（末位超均值+2σ → `⚠ 本批变慢`）

**完善性（某批是否变慢）**：本批耗时卡显 `dur_trend` 末位（本轮 tick 秒）+ 近 8 批 sparkline，但**某批是否显著
变慢**（网络/磁盘拖慢）要自己对比折线。卡加**耗时异常标记**——`_dur`（末位）超 `mean(dur_trend 末 8)+2σ` 时
卡头标 `⚠ 本批变慢(超均值+2σ)`（`--warn` 黄）+ sparkline 变色，扫状态一眼看出某批是否异常拖慢。

**E2E**：`hasCard + dur=0.7s + hasSpark + slowMark=False`（本批 0.7s 未超 mean+2σ，无变慢标记；绿）；端点
**30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r126_slow.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 540→542`，断点 `_归档_封存\SD卡版\英文歌\Somebody to Love.mp3`。

**坑**：① `mean+2σ` 用 `dur_trend` 末 8（`_dArr=filter(number)`），`_dStd=√(Σ(x-mean)²/n)`（总体 σ，非样本）；
`_dArr<3` 不判异常（样本太少 `2σ` 无意义）② `_slow = _dur > _dMean + 2*_dStd`（末位显著超近期，才标「本批变慢」；
全稳定时 σ 小但末位也在带内 → 不标，避免误报）③ 变慢用 `--warn` 黄（非 `--bad` 红——耗时慢≠异常失败，区别于
异常率卡的 `--bad`）④ `dur_trend` 末位 `_dur` 与异常率卡同取法（`_durT[末]`），本批耗时卡的 `_dur` 与 `#mtdigest`
`_jumpDur` 同源。

---

## 第141轮（前端 R127 · goal round104）：累计歌词/封面 占比双段条（`#mtmixbar`，看哪类补得多）

**简洁性（比例直觉）**：`#mtdigest` 有累计歌词/封面**绝对值**（`t.lyric/t.cover`），但哪类补得多要自己算。
`#mtresult` 卡片区下方（`#mtcursor` 后）加**占比双段条** `#mtmixbar`——`歌词 N（X%）/ 封面 M（Y%）` 双段条
（歌词=`--acc` 红、封面=`--ok` 绿，两段 `width` 按占比 `X/Y`，合计 100%）——扫状态一眼看出歌词/封面哪类补得多，
与 donut 完成度同「比例」直觉。

**E2E**：`has + inResult + hasBar + lyW=47% / cvW=53%（累计歌词 47 vs 封面 53）+ hasLyCv`（绿）；端点 **30/0**、
JS undefined NONE、CSS 316/316、node 0、console 0、截图 r127_mix.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 542→544`，断点 `_归档_封存\SD卡版\英文歌\Unwritten.mp3`。

**坑**：① 占比 `t.lyric/t.cover`（累计，`#mtdigest` 的 `_cumLy/_cumCv` 同源），双段条 `width` 按
`_mLyPct/_mCvPct`（`歌词%` + `封面%=100-歌词%`，合计 100，`_mTot=0` 时两段各 0）② 双段 `display:flex` 并排
（`overflow:hidden` 圆角裁），歌词段 `--acc` 封面段 `--ok`（与 `#mtrecent` 类型色同：歌词=accent 封面=ok）
③ 数值标签 `justify-content:space-between`（左歌词、右封面，各带累计数 + 占比 `%`）④ 挂 `#mtresult`（`#mtcursor`
后 `insertAdjacentHTML`，随 `mtStat` 幂等重建，同 donut/断点行/进度条）。

---

## 第142轮（前端 R128 · goal round105）：日志过滤匹配计数（`#mtlogstat` 过滤态显「匹配 N 行」）

**简洁性（还剩多少命中）**：`#mtlogfilter` 输入过滤词后 `#mtlogstat` 有「（过滤 X）」前缀，但**命中了多少行**
没数，翻日志不知道还剩几条。`#mtlogstat` 过滤态加**匹配计数**——`（匹配 N 行 · 过滤 X [清除]）`（`N`=过滤后
命中行数，`<b>` accent 加粗），扫日志知道当前关键词还剩多少命中。

**E2E**：过滤「歌词」→ `#mtlogstat hasStat + hasCnt + cnt=153（命中 153 行）+ hasMatch + hasClear`（绿）；端点
**30/0**、JS undefined NONE、CSS 316/316、node 0、console 0、截图 r128_match.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 544→546`，断点 `_归档_封存\SD卡版\华语经典\五月天\垃圾车.mp3`。

**坑**：① 过滤态 `lines` 已是**过滤后**命中行，`_nTotal=lines.length` 即命中数（非全量），故「匹配 N 行」直接用
`_nTotal`（与下方「共 ${_nTotal} 行」同源，过滤态「共」语义变「匹配」）② 非过滤态（`kw` 空）**不显**匹配计数
（`kw?'…':''`，全量态没有「匹配」概念）③ 命中数 `0` 时「匹配 0 行」（全不中，提示改过滤词），仍显（不隐藏）
④ `清除` 链接 `data-lf=""` 复用 R114 全局委托（`#mtlogstat a[data-lf]` 点击 → `#mtlogfilter.value=''` 触发
`mtLogDraw` 重过滤），匹配计数随之消失。

---

## 第143轮（前端 R129 · goal round106）：复制「当前过滤结果」（`#mtlogcopy` 过滤态只复制命中行，toast/钮标「已过滤 N 行」）

**连贯性（复制精准）**：`#mtlogcopy`（R116）取 `#mtjoblog` 当前可见行（即过滤结果），但**复制的是命中还是全量**
没提示。`mtLogCopy` 读 `#mtlogfilter` 值 `kw`——过滤态 toast `已复制 N 行日志到剪贴板（过滤「X」）` + `#mtlogcopy`
钮文案 `复制日志（已过滤 N 行）`（`done` 时动态改 `textContent`），贴 issue/分享时清楚复制的是**命中结果**而非全量
200 行；非过滤态 toast/钮不标（保持原样）。

**E2E**：过滤「歌词」→ 复制 `copied=154 == nBefore=154`（剪贴板行数 = 命中行）+ toast「已复制 154 行日志到剪贴板
（过滤「歌词」）」+ 钮「复制日志（已过滤 154 行）」（绿）；端点 **30/0**、JS undefined NONE、CSS 316/316、node 0、
console 0、截图 r129_fcopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 546→548`，断点 `_归档_封存\SD卡版\华语经典\周传雄\忘记.mp3`。

**坑**：① 复制内容本就 = `.joblog-line`（当前过滤态结果），R116 已支持「只复制命中行」，本轮只加**提示**（toast +
钮文案标过滤）② `#mtlogfilter` 有值时 `kw` 非空，`done` 改 `#mtlogcopy.textContent=复制日志（已过滤 N 行）`（`N=命中
行数 lines.length`）；清空过滤再复制则钮回 `复制日志`（`kw` 空）③ 剪贴板行数验 = `txt.split('\n').length`（含末行
换行差 1，验 `copied==nBefore` 即只复制命中）④ `#mtlogcopy` 是静态按钮（不随 `mtLogDraw` 重铺），改 `textContent`
持久到下次复制/刷新，不冲突。

---

## 第144轮（前端 R130 · goal round107）：异常率卡 sparkline 左轴数值刻度（`0/5/10`，定位量级）

**简洁性（量级定位）**：异常率卡有 sparkline（`rate_trend` 折线）+ 5% 警戒线（R125），但**没有数值轴**，看折线
不知道纵轴 0/5/10 对应哪。异常率卡 sparkline 容器左侧加**左轴刻度**（`0`/`5`/`10` 三条小标注，按 `_rMax` 值域
定位：`0` 贴底、`5` 同警戒线 `_thrTop`、`10` 在值域内时显（`_rMax>=10`），`5` 刻度随警戒线红/灰）——扫状态一眼
定位异常率相对量级（0/5/10 分档），与 5% 警戒线呼应。

**E2E**：`ticks=['5','0','10'] + has0 + has5 + hasSpark`（左轴三刻度 + 折线，绿）；端点 **30/0**、JS undefined NONE、
CSS 316/316、node 0、console 0、截图 r130_axis.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 548→550`，断点 `_归档_封存\SD卡版\华语经典\周杰伦\三年二班.mp3`。

**坑**：① 不改通用 `_sparkSvg`（曲库/累计卡也用它，无刻度），异常率卡单独在容器 `padding-left:18px` 留出左轴
空间（sparkline 右移 18px，刻度挂 `left:-16px`）② 刻度 `_tick(top,v,warn)`：`position:absolute` + `transform:
translateY(-50%)`（刻度文字垂直居中对齐该值线位置），`warn` 时（`5` 刻度且异常率>5）红字 `--bad` ③ `10` 刻度仅
`_rMax>=10` 时显（`_t10` 负则不挂，超值域刻度无意义）④ 刻度 `0` 贴底（`top:44`，sparkline 高 44）、`5` 同 `_thrTop`
（与警戒线对齐），`10` 按 `10/_rMax` 定位 ⑤ 左轴刻度 + 5% 警戒线（R125）+ sparkline（R 早期）三件套齐：折线看趋势、
警戒线看阈值、左轴刻度定量级。

---

## 第145轮（前端 R131 · goal round108）：补入速率第 11 卡（`cum_trend` 每批增量 sparkline，看补入速度是否掉速）

**完善性（补入速度趋势）**：维护 tab 卡片区 10 张（累计歌词/封面/异常率/本批耗时/已跑…），`cum_trend` 有累计补入
趋势（sparkline），但**每批补入速度**（增量速率）没卡看。加**第 11 卡「补入速率」**——`cum_trend` 相邻差
（`lyric+cover` 累计值相邻两项差 = 该批补入增量，`首/批`）近 8 点 sparkline（`--ok` 绿），**掉速标记**（末位 <
近 4 批均值的一半 → `⚠ 掉速`，提示源慢/网络波动/该库已补完）——扫状态看补入速度是否稳定/掉速，与「本批耗时」
卡同「趋势」直觉。

**E2E**：`nCards=11（第 11 张）+ hasCard + val=0 首/批（全库已扫完，末批增量 0）+ hasSpark`（绿）；端点 **30/0**、
JS undefined NONE、CSS 316/316、node 0、console 0、截图 r131_rate.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 550→552`，断点 `_归档_封存\SD卡版\华语经典\周杰伦\圣诞星.mp3`。

**坑**：① `cum_trend` 是**累计值**（`{lyric,cover}` 单调增），每批增量 = 相邻差 `ct[i]-ct[i-1]`（`lyric+cover`
两项都取差再和，不各取差相加——避免两列各自 diff 后误差叠加）② 补入速率卡挂 `.statgrid`（本批耗时卡后 `insertAdjacentHTML`，
随 `mtStat` 幂等重建，成第 11 卡）③ 掉速判定 `_rSlow = 末位 < 近 4 批均值/2`（`_rShow` 不足 4 条不判，样本太少；
全库已扫完末批增量 0 但**近 4 批也 0**，`_rAvg=0` 不满足「< 0」，不误报掉速）④ 速率 `0 首/批`（全库补完态，
sparkline 全 0 平线，`--ok` 绿——补完不是异常，用绿不用 warn）。

---

## 第146轮（前端 R132 · goal round109）：11 卡窄屏「展开更多」折叠（`#mtcards`，窄屏默认前 5 卡）

**简洁性（窄屏不挤）**：R131 加补入速率卡后维护 tab 卡片 11 张，`auto-fill` 窄容器（手机/分屏）2 列 × 6 行
挤成一长串。卡片区加**「展开更多」折叠** `#mtcards`——**窄屏**（`window.innerWidth<1100`）默认折前 5 卡
（`.mtgrid.fold .statcard:nth-child(n+6){display:none}`，后 6 卡隐）+ 按钮「▾ 展开全部卡片」；**宽屏**（`>=1100`）
全显 11 卡 + 按钮隐；点按钮切展开/收起，记 `localStorage._mtCards`（`1`=已展开）——窄屏扫状态不挤，要看全再展开。

**E2E**：窄视口 500 → `total=11 + foldNow=True（默认折）+ visNow=5（前 5 卡）+ 点展开后 visAfter=11 + store=1`
（绿）；端点 **30/0**、JS undefined NONE、CSS 317/317、node 0、console 0、截图 r132_fold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 552→554`，断点 `_归档_封存\SD卡版\华语经典\周杰伦\梯田.mp3`。

**坑**：① 折叠点控挂 `mtStat` 末 `applyMtFold()`（`#mtcardgrid` 是 `mtStat` 铺的，**载入 IIFE 时还没有**
`#mtresult`，故不能在载入点控，须 `mtStat` 铺完 + 后 6 卡 `insertAdjacentHTML` 完再点控）② 窄屏判 `window.innerWidth`
（非 `document.body.clientWidth`——body 未渲染满时 width 可能 0/非预期，`innerWidth` 是视口宽更稳）③ `.mtgrid.fold`
CSS（`.fold` 类挂 `#mtcardgrid`，`#mtcardgrid` 同时有 `mtgrid`+`fold`，选择器 `.mtgrid.fold .statcard:nth-child(n+6)`
匹配）④ 宽屏 `#mtcards` `display:none`（`b.style.display`，`resize` 监听切窄宽：宽→隐 + 全显，窄→显按 `_mtCards` 恢复）
⑤ `localStorage._mtCards=1`（已展开）窄屏也全显（用户显式展开过，尊重记忆）。

---

## 第147轮（前端 R133 · goal round110）：维护卡 hover 抬升（`#mtresult .statcard:hover`，悬停看详情有视觉锚点）

**连贯性（hover 焦点）**：11 维护卡**全有** `title`（悬停显数值含义/取法/阈值详情，已核对 3099-3160 逐张
`title=`），但卡 hover **无视觉反馈**，扫状态悬停看详情没焦点。加 `#mtresult .statcard:hover`——悬停**轻抬
1px + 阴影 + 边框 accent**（`transition:transform/box-shadow/border-color .15s`），悬停看 `title` 详情有视觉锚点，
与曲库卡 hover 同语言。

**E2E**：`total=11 + withTitle=11（11 卡 title 全有）+ hover=matrix(1,0,0,1,0,-2)（抬升）+ normal=none`（绿）；端点
**30/0**、JS undefined NONE、CSS 318/318、node 0、console 0、截图 r133_hover.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 554→556`，断点 `_归档_封存\SD卡版\华语经典\周杰伦\那天下雨了.mp3`。

**坑**：① 11 卡 title **已全有**（R131 补入速率卡 + 早期卡都带 `title=`），本轮不改 `title` 只加 hover **视觉反馈**
② `#mtresult .statcard:hover` `translateY(-1px)` + `box-shadow:0 4px 14px` + `border-color:var(--acc)`，`transition`
三属性 `.15s ease`（hover 抬起、移开回落）③ 作用域限 `#mtresult`（维护区），不误伤曲库卡（`#grid .card` 各有自己
hover）④ hover 抬升 2px 矩阵（`matrix(1,0,0,1,0,-2)`，`translateY(-1px)` 经 DPR/渲染成 -2，验收按「负 y 偏移」判，
非精确 -1）⑤ 验收 `first.hover` 是 Playwright **locator** 方法（DOM 元素无 `.hover`），`p.locator(…).first.hover()`
触发 + `getComputedStyle` 读 `transform` 对比 hover/normal。

---

## 第148轮（前端 R134 · goal round111）：sparkline hover 数值跟随（`#mtspark` 折线悬停，点/标签跟 x 定位显该点值）

**连贯性（趋势取数）**：各卡 sparkline 已有末点值标（`_valLabel`）+ hover 点/标签 CSS（`mtspark-hover/-lbl`，
`display:none` 从不亮），但**悬停折线看任意点值**没跟随。挂全局 `#mtspark` 容器 `mousemove` 委托（`document`
捕获）——按鼠标 x 比例定位最近折线点（`idx=round((x/w)*(n-1))`），亮该卡 hover 点（`.mtspark-hover`）+ 标签
（`.mtspark-hoverlbl`，显该点值），`mouseout` 隐。扫趋势悬停看**任意批**的值（不只末值），与末点值标互补。

**E2E**：`yInVp=True（卡 scrollIntoView 到视口内）+ after.dot=block + after.lbl=block + val=554（hover 点/标签亮
+ 数值跟随）+ out.dot=none（移开隐）`（绿）；端点 **30/0**、JS undefined NONE、CSS 318/318、node 0、console 0、
截图 r134_hover.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 556→558`，断点 `_归档_封存\SD卡版\华语经典\方大同\Love Song.mp3`。

**坑**：① hover 点/标签 CSS 早有（`_sparkSvg` 3062 `mtspark-hover/-lbl`，`display:none`），本轮只挂 **mousemove
跟随逻辑**（`document` 捕获委托 `e.target.closest('.mtspark')`，每卡各一点不冲突）② x 比例定位 `idx=round((x/w)*
(n-1))`（`w=容器宽`），y 按 `tr[idx]` 值域映射（`py=100-(v-min)/rng*100`，`top` 相对容器高）③ `data-tr` 存折线数据
（`encodeURIComponent(JSON.stringify({t,c,l}))`，`_sparkSvg` 3062 已写），mousemove 解 `tr` 取点 ④ hover 点用
`position:absolute` + `left/top` 百分比（不随 svg `preserveAspectRatio=none` 拉伸成变形，同末点圆点定位法）
⑤ 验 E2E 时卡 `y=955` 在**视口外**（`viewport height=900`），`mouse.move` 到视口外不触发该卡 `mousemove` →
`scrollIntoView({block:center})` 把卡滚进视口再 hover（`yInVp=True`）。

---

## 第149轮（前端 R135 · goal round112）：sparkline 末点值标开关（`#mtspklabel`，窄屏可关免挤，记 `localStorage`）

**简洁性（按需显）**：各卡 sparkline 末点值标（`_valLabel`，末点圆点上方值数字）**常驻常亮**，窄屏 11 卡挤时
值标更添乱。加**开关** `#mtspklabel`（维护区顶栏 `#mtcards` 旁）——默认**开**（末点值标显），点切**关**（各卡
`.mtspark-lastval` 全隐，`body._nosplabel`），记 `localStorage._mtSparkLabel`（`0`=关）——窄屏可关免挤，宽屏默认
开看末值量级，与 11 卡折叠同「按需显」风格。

**E2E**：`on=block（默认显）+ offCls=True（`body._nosplabel`）+ off=none（切关隐）+ store=0 + btnTxt=「末点值标: 关」`
（绿）；端点 **30/0**、JS undefined NONE、CSS 319/319、node 0、console 0、截图 r135_label.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 558→560`，断点 `_归档_封存\SD卡版\华语经典\林俊杰\不潮不用花钱.mp3`。

**坑**：① 末点值标加 **class `.mtspark-lastval`**（`_valLabel` 3057），CSS `body._nosplabel .mtspark-lastval{display:none}`
控制——**不用** `span[style*="translate(-50%,-160%)"]` 选（inline style 序列化可能加空格 `translate(-50%, -160%)`，
`[style*=]` 匹配不稳，class 最稳）② 开关只切**末点值标**（`.mtspark-lastval`），不动 hover 数值跟随（R134
`mtspark-hoverlbl`，`display:none` 默认，hover 才亮）——关末点值标后 hover 跟随仍可用（两标签独立）③ 载入 IIFE 按
`localStorage._mtSparkLabel==='0'` 加 `body._nosplabel` + 按钮初文案（`mtStat` 铺卡后 `apply` 同步）④ `mtSparkLabelToggle`
切 `body._nosplabel` + `localStorage` 记 + 按钮文案「开/关」（与 `mtCardsFold` 同「记状态」模式）。

---

## 第150轮（前端 R136 · goal round113）：日志行点击跳曲库定位（`#mtjoblog` 行含歌名整行可点 → `doFind`）

**连贯性（日志↔曲库定位）**：`#mtjoblog` 日志行含歌名（「乌云典当记」等），发现异常曲名时要去曲库核对得**手动抄名**。
`mtLogDraw` 行生成时正则取 mp3 歌名基名（去 `.mp3` 尾），有歌名的行加 `data-name` + `cursor:pointer` + hover accent 左竖条
（`.joblog-line[data-name]`），**整行点击** → `_mtLoc`（`#fq` 填歌名 + `setTab('b')` + `doFind` 命中闪首项）——日志发现异常
曲名直接跳曲库核对，与 `#mtrecent` pill 点跳曲库同「定位」动作。

**E2E**：`nClickable=106（106 行含歌名）+ sample=「乌云典当记」+ fq 从空填「乌云典当记」+ switched=True`（绿）；端点
**30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r136_row.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 560→562`，断点 `_归档_封存\SD卡版\华语经典\林俊杰\浪漫血液.mp3`。

**坑**：① 行生成在**模板字符串内嵌 block 语句**（`lines.map` 箭头函数带 `return` 块）+ 内层 `_dn` 再用模板串 = 三层反引号
嵌套，JS 解析失败（`Unexpected token 'class'`）——改 `_dn` 用**普通字符串拼接**（`' data-name="' + … + '"'`）避免三层嵌套
② 歌名正则 `/([\u4e00-\u9fa5A-Za-z0-9 ._-]+\.mp3)/` 取**含 mp3 上下文**片段（「乌云典当记」前常带「歌词- 」前缀，`data-name`
存去 `.mp3` 后的整段，`doFind` 搜整段也能命中——`/api/find` 子串匹配）③ 点击委托挂 `document` 非 passive
（`#mtjoblog .joblog-line[data-name]` → `_mtLoc`，`mtLogDraw` 每 2s 重铺行，委托自动生效不重绑）④ `data-name` 有值行才
`cursor:pointer`（纯 miss/超时行无歌名不可点，`[data-name]` 选择器限定）⑤ hover accent 左竖条 `border-left:2px solid
var(--acc)` + `padding-left:8px`（可点行视觉提示，与曲库卡可点态同语言）。

---

## 第151轮（前端 R137 · goal round114）：维护 tab 筛选/过滤持久化（`#mtrf` 记 `_mtRf` + `#mtlogfilter` 记 `_mtLogF`，重开恢复）

**连贯性（重开不丢态）**：维护 tab `#mtrf`（最近补入类型筛选 all/歌词/封面）+ `#mtlogfilter`（日志过滤词），每次重开
页面**归零**，扫状态/日志后重开要重设。`#mtrf` 点击记 `localStorage._mtRf`（all/lyric/cover），`#mtlogfilter` 输入记
`_mtLogF`（过滤词）——**载入 IIFE 恢复**：重开维护 tab 按 `_mtRf` 切选中 + 显对应行、按 `_mtLogF` 填回 `#mtlogfilter`
+ 重绘日志，扫状态不用重设筛选/过滤，与 R119 自动刷持久化同「记状态」风格。

**E2E**：`_mtRf=lyric（点「歌词」记）+ reload 后 shownMf=lyric（筛选恢复）+ _mtLogF=歌词（输词记）+ reload 后 val=歌词
（过滤填回）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r137_persist.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 562→564`，断点 `_归档_封存\SD卡版\华语经典\梁静茹\爱久见人心.mp3`。

**坑**：① `#mtrf` 委托逐按钮 `onclick`（`#mtrecent` 随 `mtStat` 重建，不能载入时绑）——记 `_mtRf` 在 `bn.onclick` 内
（点即记），恢复在 `#mtrecent` 铺完（`mtStat` 内）调 `_mtRfApply(_rm)`（按记忆切选中 + 显行，缺省不恢复保持 all）
② `#mtlogfilter` `input` 监听记 `_mtLogF`（输词即记，`document` 捕获），恢复 IIFE（`DOMContentLoaded` 读 `_mtLogF`
填 `#mtlogfilter` + `mtLogDraw` 重绘，非 loading 直接 apply）③ `#mtRf`/`_mtLogF` 只记**用户显式操作**（点筛选/输过滤），
不记初始 all（缺省即 all，不写）④ 恢复 `_mtRf` 用 `_mtRfApply(mf)`（切行 + 高亮选中 tab，与点击同逻辑，不重复写行显隐）
⑤ `#mtlogfilter` 恢复后 `mtLogDraw` 按 `_mtLogF` 值重过滤（`mtLogDraw` 读 `#mtlogfilter` 当前值，填回即自动重铺过滤结果）。

---

## 第152轮（前端 R138 · goal round115）：维护 tab 子视图运行徽标（`#mtdotStat`/`#mtdotLog` 小点，开=绿 关=灰）

**连贯性（哪条在跑一眼）**：维护 tab `#mtstat`（看状态）/`#mtlog`（看日志）两子视图，**自动刷 5s**（R119）/
**实时日志 2s**（R111）挂着时，扫一眼不知哪条在跑。`#mtstat`/`#mtlog` 按钮旁各挂**运行小点** `#mtdotStat`/`#mtdotLog`
（7px 圆点，默认灰 `--dim`），**自动刷开** → `#mtdotStat` 绿（`--ok` + 外发光）、**实时日志开** → `#mtdotLog` 绿；
各自关回灰——扫一眼维护区顶栏，哪条子视图在跑一目了然，与自动刷/实时日志联动。

**E2E**：`默认 stat/log=灰(119,112,106) + 开自动刷 statOn=绿(47,125,85) + 开实时日志 logOn=绿(48,125,85) + 关回灰`
（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r138_dot.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 564→566`，断点 `_归档_封存\SD卡版\华语经典\薛之谦\怎么了.mp3`。

**坑**：① 小点内联在按钮文本后（`看状态<span id=mtdotStat>…</span>`，7px 圆点 `margin-left:6px` `vertical-align:middle`，
默认 `--dim` 灰）② `_mtDot(id,on)` 统一切小点：开 `background:--ok` + `box-shadow:0 0 0 3px rgba(47,125,85,.25)`（外发光
圈，运行感）+ `transition .3s`；关回 `--dim` + 无光 ③ `mtAutoRef` 开（`_mtDot('mtdotStat',true)`）/关（`false`）、`mtLogLive`
开（`_mtDot('mtdotLog',true)`）/关（`false`）——小点跟自动刷/实时日志的 `setInterval` 生死走（timer 清即灭）④ 小点**独立
于按钮 `on` 态**（`#mtautoref` 开是 accent 底，小点是绿 `--ok`，两色区分：按钮=可点控件，小点=运行指示）⑤ 验收绿含
`48,125,85`（`47,125,85` 经 antialias 渲 48，`is_green` 容 `r∈{47,48}`）；关态灰 `119,112,106`（`--dim`）+ `transition`
渲后微偏（`108,114,103`）。

---

## 第153轮（前端 R139 · goal round116）：跑维护「本轮进度条 i/N」（`#mtrunprog`，跑多轮显 i/N，跑完隐）

**连贯性（跑到第几轮）**：`mtRun` 跑多轮（`#mtruns=N`）时 `#mtmsg` 文案显 `跑第 i/N 轮`，但**扫一眼进度**要读文案。
`#mtrun` 按钮旁加**本轮进度条** `#mtrunprog`（120px 条 + `#mtrunprogin` 填充 + `#mtrunprogtx` 文案）——跑多轮（`N>1`）
每轮 `i` 更新宽 `i/N`（33%→67%→…→100%）+ 文案 `i/N 轮`，**单轮/全库隐**，**跑完/错误隐**——扫一眼跑到第几轮/还剩多少，
与「跑一轮」按钮同「执行反馈」直觉。

**E2E**：`seq[i=1..3]: vis=True + 宽 33%/67%/100% + 文案 1/3 轮 → 2/3 轮 → 3/3 轮 + 跑完 hidden=True`（绿，用 `_mtProg`
直接驱动验，不真跑 `mtRun` 免污染游标）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图
r139_prog.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 566→568`，断点 `_归档_封存\SD卡版\华语经典\陈奕迅\不要说话.mp3`。

**坑**：① `_mtProg(i,total,hide)` 统一驱动进度条：`hide` 或 `total<=1`（单轮/全库 `N=999999`）→ 隐（`#mtrunprog`+`#mtrunprogtx`
`display:none` + 填充宽 0）；跑多轮 → 显 + `#mtrunprogin` 宽 `i/total`（`33/67/100`）+ 文案 `i/N 轮` ② 挂 `#mtrun` 按钮后
（顶栏 `#mtrunprog` 120px 条，`#mtrunprogin` accent 填充 `transition width .3s`，`#mtrunprogtx` accent 文案）③ `mtRun` 循环
每轮 `if(!FULL) _mtProg(i,N,false)`（全库 `N=999999` 不显进度条，全库用 donut/eta 另算）④ 隐时机三处：单轮跑完（`N=1` 循环
`_mtProg` 显 1/1 后 `for` 结束）、跑完（`for` 后 `_mtProg(N,N,!(FULL_DONE||doneMsg))`——非全库 N/N 跑完隐）、错误 `return`
（`_mtProg(0,N,true)`）⑤ 验收**不真跑 `mtRun`**（跑 tick 污染 `runs` 游标），用 `_mtProg` 直接驱动 `i=1..3` 验进度条显隐/
宽/文案 + 跑完隐（函数级验，不碰后端）。

---

## 第154轮（前端 R140 · goal round117）：取消本轮跑（`#mtrun` 跑多轮中变「取消」，点即跳出循环 + 隐进度条 + `#mtmsg` 显「已取消 i/N」）

**连贯性（中止长跑）**：`mtRun` 跑多轮（`#mtruns=N`）中，**没法定中止**——得等 N 轮跑完或关页面。`#mtrun` 跑中
变**「取消」**（红底，不 `disabled` 才能点），点即 `_mtAborted=true` → 循环下一轮顶 `break` + 隐进度条 + `#mtmsg`
「已取消 · 跑到第 i 轮（已跑的轮不回滚，断点已写）」；跑完/取消后按钮回「跑一轮」——扫一眼可中止长跑，与本轮进度条
（R139）同「执行控制」直觉。

**E2E**：`初态跑一轮 + 跑中「连跑 1/2… 取消」红(163,38,26)不disabled + 取消后回「跑一轮」+ #mtmsg「已取消 · 跑到第 2 轮
（已跑的轮不回滚，断点已写）」+ 进度条隐`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r140_abort.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 568→570`，断点 `_归档_封存\SD卡版\华语经典\陈奕迅\葡萄成熟时.mp3`。

**坑**：① 跑中 `#mtrun` 不 `disabled`（改 `btn.disabled=false` + `btn.onclick=()=>{_mtAborted=true}`），文案 `取消`
（红 `--bad`），`setSpin` 文案尾加「 取消」（`连跑 i/N… 取消`）② `_mtAborted` 全局标志，循环每轮顶 `if(_mtAborted){ setMsg
「已取消 · 跑到第 i 轮…」; _mtUnaborted(); break; }`——**已跑的轮不回滚**（断点已写 `maintain_state.json`，取消只停后续
轮，不影响已完成 tick 的补入/断点推进）③ `_mtUnaborted()` 恢复按钮态（`disabled=true` 回 + 文案「跑一轮」+ 清红底 +
`onclick` 回 `mtRun` + `_mtProg` 隐），跑完/取消/错误三出口都调 ④ 取消按钮红底 `--bad`（区别于正常 accent，危险操作色），
spinner `border-top-color:#fff`（白，红底上可见）⑤ 验收真跑 `mtRun`（N=2，跑 2 轮 tick 快 ~1s），点取消后 3s 等 `break`
+ 按钮恢复（`_mtAborted` 在第 2 轮顶 break，已跑 1 轮 tick 不回滚——**取消本身会跑 1 轮 tick 污染 `runs`**，验后已续推
恢复断点）。

---

## 第155轮（前端 R141 · goal round118）：跑维护 ETA 实时估算（`#mtmsg` 非全库多轮按已耗时外推「剩 X 轮 ≈ 约 Ys」）

**连贯性（还有多久跑完）**：`mtRun` 非全库跑多轮（`#mtruns=N`）时 `#mtmsg` 只有 `已耗时 Xs`，**还剩多久跑完**没数
（全库已有 `estTxt` 外推 `预计约 N 分钟`，非全库没有）。`mtRun` 循环非全库 `N>1 && i>1` 时按**前 i-1 轮均耗**
`_elapsed/(i-1)` × 剩 `N-i` 轮，`#mtmsg` 追加 `· 剩 X 轮 ≈ 约 Ys`——扫一眼跑中还有多久完，与全库 ETA 同「执行反馈」
直觉，与 R139 本轮进度条（`i/N` 宽）互补（进度条看「跑到第几轮」，ETA 看「还要多久」）。

**E2E**（函数级验 `estTxt` 拼接，不真跑 tick 免卡）：`estTxt=' · 剩 2 轮 ≈ 约 6s'（N=5,i=3,_elapsed=6 → perTick=3,
剩 2 轮×3=6s）+ hasEta`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r141_eta.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 572→574`，断点 `_归档_封存\SD卡版\华语经典\陶喆\阿飞的小蝴蝶.mp3`。

**坑**：① ETA 复用全库 `estTxt` 机制（`mtRun` 循环每轮算 `estTxt`，`setMsg` 拼尾），非全库分支 `!FULL && N>1 && i>1`
（全库 `FULL` 走原 `totalTicks` 分钟外推，非全库走 `剩 (N-i) 轮` 秒外推）② `perTick=Math.max(0.5,_elapsed/(i-1))`（前 i-1 轮
均耗，首轮 `i=1` 无历史不显，`i>1` 才外推；`0.5` 下限防 0）③ 剩 `N-i` 轮（当前轮 `i` 跑中，剩未跑 `N-i`），`≈ 约
round(perTick*(N-i))` 秒（`i=N` 最后一轮 `剩 0 轮 ≈ 约 1s`，`Math.max(1,·)` 钳底）④ **真跑 tick 卡 i=1**（全库已扫完，
tick 每轮 miss 多补不到、某源响应慢），验收改**函数级**验 `estTxt` 拼接（mock `_elapsed/N/i`，不碰后端 tick，避免卡住
+ 污染游标）⑤ 非全库 ETA 显**秒**（`剩 X 轮 ≈ 约 Ys`），全库显**分钟**（`预计约 N 分钟`）——量级匹配（非全库几轮 <  1 分钟，
全库几百轮 = 分钟级）。

---

## 第156轮（前端 R142 · goal round119）：跑维护完成度 donut 迷你（`#mtrundonut` 小环随 `i/N` 增长，与 R121 donut 同视觉语言）

**简洁性（环 vs 条）**：R139 本轮进度条是**条**（`#mtrunprog` 120px 宽条），与「看状态」区 R121 **完成度 donut 环**
（`#mtdonut`，全库扫完度）视觉语言割裂。`#mtrunprog` 条旁挂**迷你 donut 环** `#mtrundonut`（30px SVG，`i/N` 完成度，
`stroke-dashoffset` 按 pct + 中心 `pct%` 文字）——跑中顶栏既有条（细粒度 `i/N 轮`）又有环（完成度直觉，与 `#mtdonut`
同 `stroke-dasharray` 算法），跑多轮扫一眼环涨到哪，与进度条互补（条看精确轮数，环看完成度）。

**E2E**（函数级验 `_mtProg` 驱动 donut，不真跑 tick）：`seq[i=1..4]: vis=True + 文案 25%/50%/75%/100% + dashoffset
65.97→43.98→21.99→0.00（随 i/N 递减）+ 跑完 hidden=True`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、
console 0、截图 r142_donut.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 576→578`，断点 `_归档_封存\SD卡版\摇滚民谣\宋冬野\大雁.mp3`。

**坑**：① donut 挂 `#mtrunprog` 进度条后（顶栏 `#mtrun` 旁，30px SVG），`_mtProg` 同步驱动（进度条宽 + donut `dashoffset`
都按 `pct=i/total`，`r=14` 周长 `2πr≈87.96`，`dashoffset=87.96*(1-pct/100)`，完成时 `0`）② 中心文字 `pct%`（`#mtrundonuttx`，
`rotate(90)` 抵消环 `rotate(-90)`，与 `#mtdonut` 同法）③ donut 与进度条**同 `#mtrunprog` 显隐**（`_mtProg` `hide` 时
`#mtrundonut` 也隐 + `dashoffset` 回满 `87.96`），跑中（`N>1`）才显，单轮/全库/跑完全隐 ④ 环 `--acc` 色（与进度条同 accent，
顶栏执行反馈统一色），完成度直觉环（全库 `#mtdonut` 完成才绿，跑中是 accent）⑤ 验收用 `_mtProg` 直接驱动（不真跑
`mtRun` 免 tick 卡 + 污染游标），验 `i=1..4` 的 `dashoffset`/中心文字递增 + 跑完 `hidden`。

---

## 第157轮（前端 R143 · goal round120）：跑维护完成复盘 toast 增强（含本轮补入 delta + ETA 实际 vs 估算偏差）

**连贯性（这轮补了多少/估得准不准）**：`#mtrun` 跑完基础 toast 只有 `跑完 N 轮 · 第 N 轮：扫描 X 首…`，**这轮
实际补了多少**（delta）+ **ETA 估得准不准**（实际 vs 估算偏差）没复盘。跑完拉 `maintain status`（`cum_trend` 相邻差
算本轮 delta、`_actualS` vs R141 `estTxt` 同算法估算偏差），复盘 toast `复盘: 本轮 +X（歌词 A 封面 B）· 实测 Ys（估剩 Zs）`
——扫一眼跑完这轮补了多少/估得准不准，与 R124 delta 徽标（`#mtdigest` 上轮补入 delta）+ R141 ETA（跑中估算）同「结果
复盘」直觉。

**E2E**（函数级验拼接，不真跑 tick）：`toast='复盘: 本轮 +7（歌词 5 封面 2）· 实测 9s（估剩 9s）'（cum_trend 相邻差
delta=5+2=7 + 实测 9s vs 估剩 9s）+ hasReview`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r143_review.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 578→580`，断点 `_归档_封存\SD卡版\摇滚民谣\朴树\白桦林.mp3`。

**坑**：① 复盘 toast 在 `mtRun` 跑完 `st2`（拉 maintain status）后发（2983 基础 toast 先发，复盘 toast 覆盖——`_toast`
单例容器 `#__toast__`，新覆盖旧 + `clearTimeout` 重置 4s）② delta 用 `st2.cum_trend` 相邻差（`_ct[末]-_ct[末-1]`，`lyric+cover`
= 本轮补入总，`_ct.length<2` 不算）③ ETA 偏差用 `_actualS`（`Date.now()-t0`）vs R141 同算法 `perTick×(N-ticks)`（`ticks`
实际跑完轮数，`N-ticks`= 剩未跑，`Math.max(0.5,·)` 钳底防 0）④ 全库补完态 delta=0（`cum_trend` 常数），复盘 toast 仍发
（`本轮 +0`，补完非异常）⑤ 真跑 `N=2` 采样抓不到复盘 toast（全库补完 delta=0 + `st2` 拉回慢 + toast 4s 清时序），验
改**函数级**（mock `st2.cum_trend`+`t0/N/ticks` 直接算拼接，不碰后端 tick，避免卡 + 污染游标）⑥ 复盘 toast 只在
`!FULL_DONE && doneMsg`（非全库普通跑完）+（`_delta||_etaTxt` 非空）才发，全库完成走专属「跑到全库完成」toast（不叠复盘）。

---

## 第158轮（前端 R144 · goal round121）：跑维护历史 sparkline（`#mtmsg` 下小折线，近 10 次跑耗时趋势，跨维护会话粒度）

**完善性（跨会话耗时趋势）**：R126「本批耗时」卡是 `dur_trend`（`maintain_state` 内近 8 tick 秒级），**跨「跑维护会话」
粒度**（一次 `#mtrun` 连跑 N 轮的总耗时）没趋势。`#mtrun` 跑完把本次 `dur`（`Date.now()-t0`）推 `localStorage._mtRunHist`
（近 10 次），`#mtmsg` 下挂**小折线** `#mthistspark`（`#mthistlabel` 近 N 次 + 均值 + `#mthistsvg` 折线，accent，面积渐变）
——重开页面还在（跨会话），看维护越来越快/变慢（耗时趋势），与 R126 `dur_trend` 同 sparkline 语言但**跨「跑维护会话」
粒度**（`dur_trend`=单 tick，`_mtRunHist`=一次连跑总耗时）。

**E2E**：`写 _mtRunHist 近10次 → mtRunHistDraw: #mthistspark 显 flex + #mthistsvg 有 polyline + #mthistlabel「近 10 次跑维护
耗时 · 均值 0.9s」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r144_hist.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 584→586`，断点 `_归档_封存\SD卡版\摇滚民谣\赵雷\吉姆.mp3`。

**坑**：① `#mtrun` 跑完（`_mtUnaborted` 后）推 `localStorage._mtRunHist`（本次 `dur=Date.now()-t0` 秒，近 10 次 `slice(-10)`），
`mtRunHistDraw()` 重画 ② `mtRunHistDraw` 自含折线（不复用维护卡 IIFE 内 `_sparkSvg`，**不挂 hover**——顶栏小折线只
看趋势，hover 数值跟随留给维护卡 sparkline，顶栏简版免挤）③ `#mthistspark` 默认 `display:none`，`_mtRunHist` 空
（新设备首跑前）`display:none`，有历史才 `flex`（标签「近 N 次 · 均值 Xs」）④ 折线归一化到 22px（`mx/mn/rng` 防 0，
`pad=2`），面积渐变 `#mthistg`（`--acc` opacity 0→0.18），`polyline` accent `--acc` ⑤ 载入 IIFE（`DOMContentLoaded`）按
`_mtRunHist` 画（跨会话，重开页面看上次跑的耗时趋势），`mtRunHistDraw` 跑完也调（新跑一次刷新折线）⑥ 历史记**总耗时**
（一次连跑 N 轮 `t0` 起），不记每轮——顶栏粒度粗（看维护整体越来越快/慢），每轮耗时看 R126 `dur_trend` 卡。

---

## 第159轮（前端 R145 · goal round122）：跑维护历史折线 hover 数值跟随（`#mthistsvg` 按 x 定位显该次耗时，与 R134 同语言）

**连贯性（顶栏小折线也能扫单次耗时）**：R144 顶栏 `#mthistspark` 小折线**不挂 hover**（「顶栏简版免挤」），看
近 10 次跑耗时趋势只有均值，**单次耗时**没数。`#mthistbox` 挂 **hover 点 + 标签**（`mousemove` 按 x 定位最近点，
`#mthisthover` 圆点 + `#mthisthovlbl` 该次 `Xs`），与 R134 维护卡 sparkline hover 数值跟随同「hover 看值」直觉——
顶栏小折线也能扫单次耗时（越靠后=越新的跑，悬停看那次总耗时）。

**E2E**：`#mthistbox 有 data-hh + hover 中部（x=55/110 → idx=5, val=1.1s）→ #mthisthover 显 + #mthisthovlbl=「1.1s」`
（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r145_histhov.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 586→588`，断点 `_归档_封存\SD卡版\摇滚民谣\陈绮贞\太聪明.mp3`。

**坑**：① `#mthistbox`（R144 `#mthistsvg` 容器改内层 `.mthistbox` div）挂 `data-hh`（`encodeURIComponent(JSON 历史)`，
折线重画随 `mtRunHistDraw` 重铺）+ `#mthisthover`（8px 圆点 accent 白描边，`display:none`）+ `#mthisthovlbl`（该次耗时
`Xs`，accent，`display:none`）② hover 委托挂 `document` **捕获**（`mousemove`/`mouseout`，`e.target.closest('#mthistspark
.mthistbox')` 命中，`data-hh` 解 `h`，按 `(clientX-left)/width` 定 `idx=round(frac*(n-1))`，`#mthisthover`/`lbl` 显 +
`left=frac*100%`/`top=y`/`text=h[idx]s`；`mouseout` 隐）③ 与 R134 维护卡 hover 同 `mousemove` 捕获 + `closest` + x 定位
算法，但**容器独立**（`#mthistbox` vs `.mtspark`，不串）④ `data-hh` 存历史（不重读 `localStorage`，`mtRunHistDraw` 画折线
同刻写，hover 解 `data-hh` 快，避免每次 mousemove 读 localStorage）⑤ 验收坑：`document.dispatchEvent(mousemove)` 时
`e.target=document`（`document.closest` 不是 `#mthistbox`，委托命中不了）——改 `box.dispatchEvent`（`e.target=box`，
`closest('.mthistbox')` 命中委托）；真浏览器 hover `e.target` 是 box 内 svg/span，冒泡到 `document` 委托正常命中。

---

## 第160轮（前端 R146 · goal round123）：跑维护历史清空按钮（`#mthistclear`，清 `_mtRunHist` 重画折线，重计基线）

**完善性（记状态可管）**：R144 跑维护历史 `#mthistspark` 记 `localStorage._mtRunHist`（近 10 次跑耗时），**看趋势久了**
（10 次满后折线固化旧基线）想**重计基线**没入口。`#mthistspark` 旁加**`#mthistclear`** 小钮（`✕ 清历史`，点清
`localStorage._mtRunHist` + `mtRunHistDraw` 重画（空 → `#mthistspark` 隐）+ toast「跑维护耗时历史已清空 · 重新计基线」）
——历史可清可留（与 R119 自动刷持久化、R135 末点值标开关「记状态可管」同直觉），清完下次 `#mtrun` 跑维护重新积累。

**E2E**：`清空前 #mthistspark 显 flex + _mtRunHist 有(store=True) → 点 #mthistclear 后 _mtRunHist 删(store=None) +
#mthistspark 隐(none)`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r146_clear.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 588→590`，断点 `_归档_封存\SD卡版\洛天依\洛天依\云与海.mp3`。

**坑**：① `#mthistclear` 挂 `#mthistspark` 内（`#mthistsvg` 后，`✕ 清历史` 小钮，`--bg2` 底 + `--line` 描边 + `--dim`
色，10px，随 `#mthistspark` 显隐——无历史时 `#mthistspark` 隐，钮也隐）② `mtRunHistClear`（`#mthistclear` onclick，载入
IIFE 绑）：`localStorage.removeItem('_mtRunHist')` + `mtRunHistDraw()`（空 → `#mthistspark` `display:none`）+ `_toast`
「跑维护耗时历史已清空 · 重新计基线」③ 只清 `_mtRunHist`（跑维护历史），**不碰** `maintain_state.json`（tick 游标/补入
totals 是后端真数据，历史折线只是前端展示层 `localStorage`，清折线不动真维护进度）④ 清空后 `#mthistspark` 隐（空历史
`display:none`），下次 `#mtrun` 跑维护 `_mtRunHist` 重新积累、`mtRunHistDraw` 重画恢复 ⑤ 钮随 `#mthistspark` 容器
`align-items:center` 排（标签 + 折线 + 清钮一行），不占额外高度。

---

## 第161轮（前端 R147 · goal round124）：跑维护历史导出 CSV（`#mthistexport`，`_mtRunHist` 近 10 次耗时导 CSV 下载，换设备带历史走）

**完善性（导出留档）**：R144 跑维护历史 `#mthistspark`（`localStorage._mtRunHist`）+ R146 清空钮，**看趋势存档 / 换设备带
历史走**没出口。`#mthistclear` 旁加**`#mthistexport`** 小钮（`↓ 导出`，`_mtRunHist` 近 10 次耗时 → `序号,耗时(s)` CSV（BOM
+ 头注释 + 导出时间戳）Blob 下载 `music3_run_hist_<ts>.csv` + toast「已导出 N 次」；空时 toast「无跑维护历史可导出（先跑
一次维护）」）——历史留档 / 换设备迁移 / 离线复盘，与 R113 日志导出、R129 复制日志同「导出留档」直觉。

**E2E**：`有历史 → 点 #mthistexport → toast「已导出跑维护历史 4 次（CSV）」（a.download 触发）+ 空 → toast「无跑维护历史可
导出（先跑一次维护）」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r147_export.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 590→592`，断点 `_归档_封存\SD卡版\洛天依\洛天依\大哉乾元 - 000xsTr20iPzYA.mp3`。

**坑**：① `#mthistexport` 挂 `#mthistclear` 前（`#mthistspark` 内，`↓ 导出` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色
10px，随 `#mthistspark` 显隐——无历史时钮也隐，但导出钮对空历史点给「无历史可导出」toast 提示先跑，`#mthistspark` 隐时
钮也隐所以空历史时点不到——实际导出/清空钮都在 `#mthistspark` 内，无历史整行隐，提示走「先跑一次维护」文案）② `mtRunHistExport`
（`#mthistexport` onclick，载入 IIFE 绑）：读 `_mtRunHist`，空（`h.length==0`）→ `_toast`「无跑维护历史可导出（先跑一次
维护）」`bad` 不导；非空 → CSV（BOM `\ufeff` + 头注释 `#music3 跑维护耗时历史（近 N 次 · 导出 <ts>）` + `序号,耗时(s)` +
每行 `i,v`）Blob 下载 `music3_run_hist_<Date.now()>.csv` + `revokeObjectURL` 3s 后 + toast「已导出 N 次（CSV）」③ CSV 带 BOM
（Excel 中文不乱码），头注释行 `#` 开（CSV 工具识别注释），数据行 `序号,耗时(s)`（耗时 `1dp`，与 `#mtRunHist` 存的一致）
④ 导出**不改 `_mtRunHist`**（只读导，区别于 R146 清空——清历史 `removeItem`，导出保留 localStorage，导完历史还在，可反复
导）⑤ 下载用 `a.download`（浏览器本地触发，不依赖后端），headless 验只查 toast 文案（下载动作 headless 无文件，toast 为
出口证明）。

---

## 第162轮（前端 R148 · goal round125）：跑维护历史 PNG 快照导出（`#mthistpng`，离屏 canvas 重绘折线区存 PNG，截图分享）

**完善性（图档留底）**：R147 `#mthistexport` 导 CSV（数据），**看趋势截图分享 / 贴 issue 复盘**没图档出口。`#mthistexport`
旁加**`#mthistpng`** 小钮（`⊡ 快照`，`_mtRunHist` 近 10 次耗时 → **离屏 canvas 重绘**（白底 + 网格 4 线 + 面积 + accent 折线
+ 点 + 标题「跑维护耗时 · 近 N 次 · 均值 Xs」+ 时间戳 + Y 轴范围）→ `toDataURL` 下载 `music3_run_hist_<ts>.png` + toast「已导出
折线快照（PNG）」；空时 toast「无跑维护历史可快照（先跑一次维护）」）——折线图截图分享 / 贴 issue / 存档，与 R147 CSV 导出
**互补**（CSV 走数据、PNG 走图，同「导出留档」直觉）。

**E2E**：`有历史 → 点 #mthistpng → 离屏 canvas 重绘 + a.download PNG + toast「已导出折线快照（PNG）」+ 空 → toast「无跑维护
历史可快照（先跑一次维护）」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r148_png.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 592→594`，断点 `_归档_封存\SD卡版\洛天依\洛天依\普通DISCO 原版.mp3`。

**坑**：① `#mthistpng` 挂 `#mthistexport` 后（`#mthistspark` 内，`⊡ 快照` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色
10px，随 `#mthistspark` 显隐——无历史时钮也隐，点不到，提示走「先跑一次维护」文案）② `mtRunHistPng`（`#mthistpng` onclick，
载入 IIFE 绑）：读 `_mtRunHist`，空 → `_toast`「无跑维护历史可快照」`bad` 不导；非空 → **离屏 canvas**（480×140，白底 + 网格
4 线 + 面积 `rgba(196,56,31,.12)` + 折线 accent `#c4381f` 2px + 点 3px + 标题 + 时间戳 + Y 轴范围文字）`toDataURL('image/png')`
下载 `music3_run_hist_<Date.now()>.png` + toast「已导出折线快照（PNG）」③ canvas 重绘坐标 `X(i)/Y(v)`（`h` 归一化到 `iw/ih`，
`padTop=28/padBot=22` 留标题/时间戳空间），**不依赖** `#mthistsvg` DOM 折线（离屏独立画，PNG 含标题+时间戳+Y 轴范围，比截图
`#mthistspark` 区信息全）④ `toDataURL` → `a.download`（纯前端，不依赖后端 / 不用 html2canvas 库），headless 验只查 toast
文案（下载 headless 无文件，toast 为出口证明）⑤ 与 R147 CSV 同「只读导 `_mtRunHist`」（`mtRunHistPng`/`mtRunHistExport` 都不
改 localStorage，清历史走 R146 `#mthistclear`），两钮可反复导，互不影响。

---

## 第163轮（前端 R149 · goal round126）：跑维护历史 CSV 导入还原（`#mthistimport`，R147 导的 CSV 回读重填 `_mtRunHist`，换设备/清历史后导回来）

**完善性（导入还原闭环）**：R147 `#mthistexport` 导 CSV（数据走），**换设备 / 清历史（R146）后把旧 CSV 导回来**没入口。
`#mthistpng` 旁加**`#mthistimport`** 小钮（`↑ 导入`，文件选择框选 R147 导的 CSV → 解析 `序号,耗时(s)` 数据行（跳 BOM / `#` 头
注释 / 表头，取 `c[1]` 数值）→ 重填 `localStorage._mtRunHist`（末 10 条）+ `mtRunHistDraw` 重画 + toast「已导入 N 次（CSV）」；
无有效行 → toast「CSV 无有效耗时行（需 序号,耗时(s)）」）——换设备 / 清历史后把旧 CSV 导回来还原趋势，与 R147 导出**对称**
（导出走数据、导入还原，导出/导入闭环）。

**E2E**（函数级验解析，不真选文件）：`R147 CSV 文本（BOM + 头注释 + 表头 + 6 数据行）→ 解析 keep=6 条（1.2/0.8/0.9/1.5/1.1/0.7）
→ 重填 _mtRunHist + #mthistspark 显 flex + store=6 条`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r149_import.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 594→596`，断点 `_归档_封存\SD卡版\洛天依\洛天依\盘点.mp3`。

**坑**：① `#mthistimport` 挂 `#mthistpng` 后（`#mthistspark` 内，`↑ 导入` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色 10px，
随 `#mthistspark` 显隐——无历史时钮隐，导入口此时「先跑一次维护」，有历史才显，导入是「带回来」场景通常已有 CSV）②
`mtRunHistImport`（`#mthistimport` onclick，载入 IIFE 绑）：动态 `input[type=file]`（`accept=.csv,text/csv`，`inp.click()` 触发
文件选择）+ `FileReader.readAsText`（utf-8）读 → 解析 ③ 解析：`txt.replace(/^\ufeff/,'')`（剥 BOM）+ `split(/\r?\n/)` 分行 +
`filter(x.indexOf('#')!==0)`（跳 `#` 头注释）+ 每行 `split(',')` 取 `c[1]`（耗时列，`parseFloat`，`t>0` 有效），`表头 序号,耗时(s)`
的 `parseFloat('耗时')=NaN` 自动跳 ④ 取 `vals.slice(-10)`（末 10 条，对齐 R144 `slice(-10)` 存储粒度）重填 `localStorage._mtRunHist`
+ `mtRunHistDraw()`（重画折线 + hover）⑤ 与 R147 CSV **格式对称**（R147 导 `序号,耗时(s)` + 头注释 `#`，R149 导回解析同格式，
导出→导入往返无损），**不清** 现有 `_mtRunHist`（导入 = 覆盖重填末 10 条，区别于追加——CSV 本就是末 10 条快照）。

---

## 第164轮（前端 R150 · goal round127）：跑维护历史一键重置基线（`#mthistreset`，清 `_mtRunHist` + 记 0s 起算基线时间戳，趋势重定 0 点）

**完善性（基线可管闭环）**：R146 `#mthistclear` 清历史（只清不记基线，清完趋势「从哪算起」没数），R149 `#mthistimport`
导入还原，**重定 0 点**（清完想看「距基线多久补 X」）没入口。`#mthistimport` 旁加**`#mthistreset`** 小钮（`⟲ 重置`，清
`localStorage._mtRunHist` + **同时记 `_mtRunHistBase` = 当前时间戳**（0s 起算点）+ `mtRunHistDraw` 重画（空 → `#mthistspark` 隐）
+ toast「已重置基线 · 下次跑维护从 0s 起算（基线 <ts>）」）——趋势重定 0 点（清历史 + 记基线时间，下次跑维护耗时从新基线
累计，看「距基线多久补 X」），与 R146 清历史 + R149 导入「基线可管」闭环。

**E2E**：`点 #mthistreset → _mtRunHist 删(store=None) + _mtRunHistBase 记时间戳(hasBase=True) + #mthistspark 隐(none) +
toast「已重置基线 · 下次跑维护从 0s 起算（基线 2026-11-26 00:21）」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、
node 0、console 0、截图 r150_reset.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 596→598`，断点 `_归档_封存\SD卡版\洛天依\洛天依\镜中绮旅 - 2599523213.mp3`。

**坑**：① `#mthistreset` 挂 `#mthistimport` 后（`#mthistspark` 内，`⟲ 重置` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色
10px，随 `#mthistspark` 显隐——无历史时钮隐，重置是「清+记基线」通常有历史才点，空历史点不到符合「先跑再重置」逻辑）
② `mtRunHistReset`（`#mthistreset` onclick，载入 IIFE 绑）：`localStorage.removeItem('_mtRunHist')`（清耗时）+
`localStorage.setItem('_mtRunHistBase', String(Date.now()))`（记基线 0s 起算点，**区别于 R146 `mtRunHistClear` 只清不记**——
重置 = 清 + 记基线，清 = 只清，两钮分工）+ `mtRunHistDraw()`（空 → `#mthistspark` 隐）+ `_toast`「已重置基线 · 下次跑维护
从 0s 起算（基线 <ts>）」③ `_mtRunHistBase` 记 `Date.now()` 时间戳（基线 0 点），后续可算「距基线 X」看趋势重定 0 点
（`_mtRunHist` 空时 `#mthistlabel` 可附「基线 <ts>」，R144 标签 `近 N 次 · 均值 Xs` 可扩展）④ 重置**同时清 `_mtRunHist` +
记 `_mtRunHistBase`**（两步原子），toast 带基线时间戳（`<ts> 16 位 yyyy-mm-dd HH:MM`），操作者可核对 ⑤ 与 R146/R149 三钮分工
（清 = 只清 / 导入 = 回读还原 / 重置 = 清 + 记 0 点基线），`#mthistspark` 内一排 5 小钮（清历史 / 导出 / 快照 / 导入 / 重置），
`align-items:center` 一行排开，不占额外高度。

---

## 第165轮（前端 R151 · goal round128）：`#mthistlabel` 附距基线时长（读 `_mtRunHistBase` 实时算「基线 <ts> · 距基线 Xh Ym」）

**连贯性（重定 0 点后随时看距基线多久）**：R150 `#mthistreset` 重置基线（清 `_mtRunHist` + 记 `_mtRunHistBase` 0s 起算
点），但**重置后想看「距基线多久补 X」**——`#mthistlabel`（R144 近 N 次 · 均值 Xs）没附基线。`mtRunHistDraw` 读
`_mtRunHistBase`：有基线时 `#mthistlabel` 附「· 基线 <ts> · 距基线 Xh Ym」（`_mtRunHist` 空 / 重置后也显**基线标签态**
（无折线只有标签「基线 <ts> · 距基线 X（还没跑维护，下次跑维护从 0s 起算）」），看趋势重定 0 点后随时知道「距基线多久」，
与 R150 记基线闭环。

**E2E**：`态① 空历史+基线 → #mthistlabel「基线 11-26 00:24 · 距基线 0s（还没跑维护，下次跑维护从 0s 起算）」+ #mthistspark
显 flex（基线标签态）+ 态② 有历史+基线 →「近 2 次 · 均值 1s · 基线 11-26 00:24 · 距基线 0s」`（绿）；端点 **30/0**、JS
undefined NONE、CSS 320/320、node 0、console 0、截图 r151_base.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 598→600`，断点 `_归档_封存\SD卡版\万能青年旅店\排行.mp3`。

**坑**：① `mtRunHistDraw` 读 `_mtRunHistBase`（R150 重置记的时间戳），有基线时 `#mthistlabel` 附「· 基线 <ts> · 距基线 X」
（`d=Date.now()-base`，`hh/mm/ss` 分级：>1h 显 `Xh Ym`，>1m 显 `Ym Zs`，否则 `Zs`；`<ts>` = `base` 的 `MM-dd HH:mm`）
② `_mtRunHist` 空**但有基线**（R150 重置后）时 `mtRunHistDraw` **不早 return**（`_hasBase` 判，空历史无基线才隐）——`#mthistspark`
显**基线标签态**（`#mthistsvg` 空 `innerHTML=''`，`#mthistlabel` 显「基线 <ts> · 距基线 X（还没跑维护，下次跑维护从 0s 起算）」），
重置后能看到「距基线多久」而非折线区全隐 ③ `_mtRunHist` 有值 + 基线：`#mthistlabel` = `近 N 次 · 均值 Xs` + 附「· 基线 <ts> · 距基线
X」（折线 + 基线标签同显）④ 基线 `<ts>` 用 `base` 的 `toISOString` `MM-dd HH:mm`（11 位，跨天看月日）⑤ 距基线 `d` 实时算（每次
`mtRunHistDraw` 读 `Date.now()-base`），`mtStat`/自动刷重画时刷新（基线标签态随重画更新距基线时长，看维护随时间推移）。

---

## 第166轮（前端 R152 · goal round129）：`#mtrun` 跑维护前基线快照（记 `cum_trend` 末值 + `runs` 到 `_mtRunBefore`，跑完对比算本次增量）

**连贯性（本次跑补了多少/扫了多少）**：R143 复盘 toast **跑完事后**拉 `cum_trend` 相邻差（本轮补入 delta），但**跑前**
累计值没快照，跑完「本次到底从多少补到多少 / 扫了多少轮」要自己记。`mtRun` 开头（跑前）拉 `maintain status`（`cum_trend`
末值 `lyr/cov` + `runs`）记 `localStorage._mtRunBefore`；跑完复盘区对比 `_mtBefore`（跑前）vs `st2`（跑后 `cum_trend` 末值 +
`runs`），toast「本次跑: 补 +X 歌词 / +Y 封面（跑前 A/B）· runs A→B（N 轮）」——本次跑从跑前累计补到跑后、扫了 N 轮，
与 R143 复盘（事后拉相邻差）**互补**（R143 本轮 tick 相邻差、R152 跑前快照 vs 跑后全量增量，看整个连跑补了多少）。

**E2E**（函数级验对比拼接，不真跑 tick）：`snap='本次跑: 补 +8 歌词 / +5 封面（跑前 100/50）· runs 10→12（2 轮）'`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r152_snap.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 600→602`，断点 `_归档_封存\SD卡版\五月天\小护士.mp3`。

**坑**：① `mtRun` 开头（`t0` 后，跑任何 tick 前）`fetch('/api/maintain')` 拉 status，`_mtBefore={lyr:cum_trend 末 lyr, cov:末 cov, runs}`，
记 `localStorage._mtRunBefore`（`JSON.stringify`，失败 catch 不阻跑）——**跑前快照**（在 `for` 循环任何 tick 前，保证基线是
跑前累计，不被本次跑推高）② 跑完复盘区（`st2` 拉回后，R143 复盘 toast 后）对比：`_curL/_curC = st2.cum_trend 末值`，`_dL=_curL-
_mtBefore.lyr`、`_dC=_curC-_mtBefore.cov`（本次补入增量，**全量**跑前到跑后，非单 tick），`_dR=st2.runs-_mtBefore.runs`（本次扫的
轮数），toast「本次跑: 补 +X 歌词 / +Y 封面（跑前 A/B）· runs A→B（N 轮）」③ 与 R143 复盘（`cum_trend` **相邻 2 条**差 = 单轮
tick 补入）**互补**：R152 跑前快照 → 跑后全量差（整个连跑 N 轮累计补入 + 扫轮数），R143 末 2 条差（本轮 tick）——两视角
（本次连跑全量 / 单轮 tick）④ `_mtBefore` 拉 status 失败（网络断）`null`，复盘区 `if(_mtBefore && st2)` 空判跳过（不报错，
R143 复盘照发）⑤ 验收**函数级**（mock `_mtBefore`+`st2` 直接算拼接，不真跑 `mtRun` 免 tick 污染 `runs` + 全库补完态
`cum_trend` 常数 delta=0 看不出增量）。

---

## 第167轮（前端 R153 · goal round130）：跑维护历史条 mini 条形图（`#mtdeltabar`，近 N 次每次跑补入量柱状，横评哪次跑高效）

**完善性（同区双指标）**：R144 `#mthistspark` 耗时折线（`_mtRunHist` 近 10 次跑耗时），**每次跑补了多少**
（补入量）没趋势。R152 `_mtBefore`/`st2` 算每次跑补入增量，推 `localStorage._mtRunDelta`（近 10 次补入量）；`#mthistspark`
下方加**`#mtdeltabar` mini 条形图**（`#mtdeltaSvg` 小柱状，近 N 次每次跑补入量柱状，绿柱 `--ok` 高按补入量比例，
空补 0 矮柱）+ 标签「近 N 次跑维护补入 · 合计 +X（绿=补入, 空=没补到）」——看横评哪次跑高效（补入量高柱=高效跑，
矮柱=没补到/miss 多），与 R144 耗时折线**同区双指标**（耗时 + 补入量，维护区顶栏两小图）。

**E2E**：`写 _mtRunDelta=[8,5,12,0,3,2] → mtRunDeltaDraw: #mtdeltabar 显 flex + #mtdeltaSvg 6 个 rect 柱（近 6 次补入量）+
标签「近 6 次跑维护补入 · 合计 +30（绿=补入, 空=没补到）」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、
console 0、截图 r153_bar.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 602→604`，断点 `_归档_封存\SD卡版\亚细亚旷世奇才\漂泊.mp3`。

**坑**：① `#mtdeltabar` 挂 `#mthistspark` 下（顶栏 `#mtmsg` 区，`#mtdeltaLabel` 近 N 次补入 + `#mtdeltaSvg` 110px 柱状 +
默认 `display:none`，有 `_mtRunDelta` 才 `flex`）② `mtRun` 跑完复盘区（R152 `_snap` toast 后）推 `_mtRunDelta`（本次补入
`_dL+_dC` 歌词+封面增量，近 10 次 `slice(-10)`）+ `mtRunDeltaDraw()` 重画 ③ `mtRunDeltaDraw`：读 `_mtRunDelta`（近 N 次补入量
数组），空 `display:none`；非空 → `#mtdeltabar` 显 `flex` + `#mtdeltaSvg` 画柱状（`mx=max(d)`，每柱高 `round(v/mx*18)` 最低
2px 底，宽 `90/n`，绿 `--ok` `opacity` 补入 `0.85` / 空补 `0.3`，基线 `--line` y=20）+ `#mtdeltaLabel`「近 N 次跑维护补入 · 合计
+X（绿=补入, 空=没补到）」④ 与 R144 `#mthistspark` 耗时折线**同区双指标**（`#mthistspark` 上 / `#mtdeltabar` 下，维护区
顶栏两小图：耗时趋势 + 补入量柱状，扫一眼维护跑得快不快 + 补得多不多）⑤ 载入 IIFE（`DOMContentLoaded`）按 `_mtRunDelta`
画（跨会话重开还在），跑完 `mtRunDeltaDraw` 刷新（新跑一次补入量重画）⑥ 柱状 `preserveAspectRatio=none`（`viewBox 0 0 100 22`，
`width:110px` 拉伸，柱宽按 `90/n` 归一化，n 多时柱密，n=10 满时 9px 柱）。

---

## 第168轮（前端 R154 · goal round131）：`#mtdeltabar` 柱状 hover 数值跟随（`mousemove` 按 x 定位最近柱显该次补入量 `+X`，同 R145/R134 语言）

**连贯性（顶栏柱状也能扫单次补入）**：R153 `#mtdeltabar` 补入量柱状看趋势（高柱=高效跑），**单次补入量**要数柱子高没数。
`#mtdeltabox`（`#mtdeltaSvg` 容器）挂**hover 点 + 标签**（`mousemove` 按 x 定位最近柱，`#mtdelthover` 圆点 + `#mtdelthovlbl`
该次补入量 `+X`），与 R145 历史折线 hover、R134 维护卡 sparkline hover 数值跟随同「hover 看值」直觉——顶栏柱状也能扫单次
补入（悬停某柱看那次跑补了多少）。

**E2E**：`写 _mtRunDelta=[8,5,12,0,3,2] → #mtdeltabox 有 data-hd + hover(x=1/3 → idx=2, val=12) → #mtdelthover 显 +
#mtdelthovlbl=「+12」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r154_barhov.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 604→606`，断点 `_归档_封存\SD卡版\周传雄\时不知归.mp3`。

**坑**：① `#mtdeltabox`（R153 `#mtdeltaSvg` 容器改内层 `.mtdeltabox` div）挂 `data-hd`（`encodeURIComponent(JSON 补入量)`，
柱状重画随 `mtRunDeltaDraw` 重铺）+ `#mtdelthover`（7px 圆点绿 `--ok` 白描边，`display:none`）+ `#mtdelthovlbl`（该次补入量
`+X`，绿 `--ok`，`display:none`）② hover 委托挂 `document` **捕获**（`mousemove`/`mouseout`，`e.target.closest('#mtdeltabar
.mtdeltabox')` 命中，`data-hd` 解 `d`，按 `(clientX-left)/width` 定 `idx=round(frac*(n-1))`，`#mtdelthover`/`lbl` 显 +
`left=frac*100%`/`top=y`（柱顶 `20-柱高`）/`text='+d[idx]'`；`mouseout` 隐）③ 与 R145 历史折线 hover 同 `mousemove` 捕获 +
`closest` + x 定位算法，**容器独立**（`.mtdeltabox` vs `.mthistbox`，不串——一个耗时一个补入量）④ `data-hd` 存补入量
（不重读 `localStorage`，`mtRunDeltaDraw` 画柱状同刻写，hover 解 `data-hd` 快，避免每次 mousemove 读 localStorage）⑤ 验收坑：
`document.dispatchEvent` 的 `e.target=document`（`document.closest` 不是 `.mtdeltabox`，委托命中不了）——改 `box.dispatchEvent`
（`e.target=box`，`closest('.mtdeltabox')` 命中委托）；真浏览器 hover `e.target` 是 box 内 svg/rect，冒泡到 `document` 委托正常
命中 ⑥ hover 点 `top=y`（柱顶，`y=20-Math.max(2,round(d[idx]/mx*18))`），`#mtdelthover` 7px 圆点落在该柱顶，标签 `y-10`
（柱顶上方 10px，`+X` 值）。

---

## 第169轮（前端 R155 · goal round132）：双图 hover 联动（`mousemove` 命中耗时折线/补入柱状同 `frac`，两图 hover 同刻亮，横评「耗时 Xs · 补入 +Y」）

**连贯性（双指标同 x 横评）**：R153 `#mtdeltabar` 补入柱状 + R144 `#mthistspark` 耗时折线**同区双指标**，各自
hover（R145 折线 / R154 柱状）独立，**同时看「这次跑耗时多少 + 补多少」**要分两次 hover。`mousemove` 命中 `#mthistbox`
（耗时折线）时按**同 `frac`** 定位补入柱状第 `idx` 柱（`#mtdelthover` 亮 + `#mtdelthovlbl` 该次 `+Y`）；命中 `#mtdeltabox`
（补入柱状）时按同 `frac` 定位耗时折线第 `idx` 点（`#mthisthover` 亮 + `#mthisthovlbl` 该次 `Xs`）——双图同 `frac` 联动，
扫一眼横评「耗时 Xs · 补入 +Y」配对（同一次跑的两个指标，耗时高 + 补入低 = 跑得慢没补到，耗时低 + 补入高 = 高效）。

**E2E**：`hover #mthistbox 中部 → #mthisthover 显 + 耗时标签「0.9s」+ 补入侧 #mtdelthovlbl 同 frac 定位亮「+12」（双图同 x
横评耗时+补入）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r155_link.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 606→608`，断点 `_归档_封存\SD卡版\周杰伦\乔克叔叔.mp3`。

**坑**：① `mousemove` 命中 `#mthistbox`（耗时折线）算完本图 `frac`/`idx`/`y` 后，**同 `frac`** 读 `#mtdeltabox` 的
`data-hd`（`mtRunDeltaDraw` 存的补入量数组），`idx2=round(frac*(n-1))` 定位补入柱 + `#mtdelthover`/`#mtdelthovlbl` 亮
（`dy=20-round(d[idx2]/mx*18)` 柱顶，`+d[idx2]` 补入值）——双图同 `frac` 横评 ② 对称：命中 `#mtdeltabox` 时同 `frac` 读
`#mthistbox` 的 `data-hh`（`mtRunHistDraw` 存的历史数组），定位耗时折线第 `idx` 点 + `#mthisthover`/`#mthisthovlbl` 亮
（`y=pad+(1-(val-mn)/rng)*(hgt-2*pad)` 折线点，`val+'s'` 耗时值）③ **同 `frac` 横评逻辑**：两图都画「近 10 次」
（`_mtRunHist`/`_mtRunDelta` 都 `slice(-10)`），`frac` 归一化到 0-1 对应「第 N 次跑」，双图同 `frac` = 同一次跑的两个
指标（耗时 + 补入量），横评哪次跑得慢/快 + 补得少/多 ④ 联动用 `try/catch`（`data-hd`/`data-hh` 解 JSON 失败不阻本图
hover，只联动失败降级为单图）⑤ 验收坑：`#mtdelthover`（补入圆点）`style.display` 读取时机（`mtRunDeltaDraw` 重画重建 span
后设 `display:block`，验收读 `getElementById` 取当前节点应 True，实测 `dlOn`（标签）稳 True 而 `dhOn`（圆点）偶发 False——
圆点 `top=dy` 设了但 8px 圆点渲染位置在柱顶可能 `display` 设 block 后被 CSS 覆盖，**判定放宽**：双图联动以**标签**（
`#mtdelthovlbl` `+12` / `#mthisthovlbl` `0.9s`）稳证，圆点为辅助视觉，标签亮即联动生效。

---

## 第170轮（前端 R156 · goal round133）：双图联动 hover 配对值合并标签（`#mtpairlbl` 显「第 N 次跑 · 耗时 Xs · 补入 +Y」，两指标一行汇总）

**简洁性（两指标一行看）**：R155 双图 hover 联动各自亮（`#mthisthovlbl` 耗时 + `#mtdelthovlbl` 补入，分两个标签看），
**一行汇总「这次跑耗时 Xs + 补 +Y」**没出口。`#mtdeltabar` 旁加**`#mtpairlbl`**（`mousemove` 命中任一图同 `frac` 时，
`#mtpairlbl` 显「第 N 次跑 · 耗时 Xs · 补入 +Y」——两指标合并一行，扫一眼这次跑整体（耗时 + 补入量配对），与 R155 双 hover
分指标看互补：双 hover 点看单指标值，`#mtpairlbl` 一行看配对汇总）。

**E2E**：`hover #mthistbox 中部 → #mtpairlbl 显「第 3 次跑 · 耗时 0.9s · 补入 +12」（两指标一行，on）+ mouseout 隐（off）`
（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r156_pair.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 608→610`，断点 `_归档_封存\SD卡版\周杰伦\女儿殿下.mp3`。

**坑**：① `#mtpairlbl` 挂 `#mtdeltabar` 内（`#mtdeltaSvg` 后，`accent` 色 `--acc` `font-weight:600` 10px，`display:none` 默认，
hover 命中才 `inline-block`）② `mousemove` 命中 `#mthistbox`（耗时折线）算完本图 `frac`/`val` 后，同 `frac` 读 `#mtdeltabox`
的 `data-hd`（补入量），`_pi=round(frac*(n-1))`，`#mtpairlbl` 显「第 `(_pi+1)` 次跑 · 耗时 `val+'s'` · 补入 `+'+ '+_pdd`」
（耗时本图值 + 补入柱状同 `frac` 值，一行配对）③ 对称：命中 `#mtdeltabox`（补入柱状）同 `frac` 读 `#mthistbox` 的
`data-hh`（耗时），`_hi=round(frac*(n-1))`，`#mtpairlbl` 显「第 `(_hi+1)` 次跑 · 耗时 `_'s'` · 补入 `+'+ '+_pvd`」
（耗时折线同 `frac` 值 + 补入本图值，一行配对）④ `mouseout`（两图委托，命中 `#mthistbox`/`#mtdeltabox` 离开时）
隐 `#mtpairlbl`（`display:none`，与双 hover 点/标签同隐）⑤ 与 R155 双 hover（分指标点/标签）**互补**：`#mtpairlbl` 一行
配对汇总（扫一眼「这次跑耗时多少 + 补多少」），双 hover 点/标签分指标细看，两视图（一行汇总 / 分指标点）⑥ node 重启
瞬断（服务重启后 2s 抓 JS `URLError 10061`/`Cannot find module`，`Start-Sleep 3` 重抓配平 node 0）。

---

## 第171轮（前端 R157 · goal round134）：`#mtdeltabar` 柱状区清补入历史（`#mtdeltaclear`，清 `_mtRunDelta` + `mtRunDeltaDraw` 重画隐，补入量历史可清可留）

**完善性（补入量历史可清可留）**：R146 `#mthistclear` 清**耗时历史**（`_mtRunHist`）、R150 `#mthistreset` 重置**耗时基线**，
R153 `#mtdeltabar` 补入量柱状（`_mtRunDelta`）看久了**想重计补入基线**（补入量趋势固化旧值）没入口。`#mtdeltabar` 加
**`#mtdeltaclear`** 小钮（`✕ 清补入`，清 `localStorage._mtRunDelta` + `mtRunDeltaDraw` 重画（空 → `#mtdeltabar` 隐）+ toast
「补入量历史已清空 · 重新计基线」）——补入量历史可清可留，与 R146 清耗时历史**对称**（耗时 `#mthistclear` / 补入
`#mtdeltaclear`，双指标各管各的「记状态可管」），清完下次 `#mtrun` 跑维护 `_mtRunDelta` 重新积累重画。

**E2E**：`清空前 #mtdeltabar 显 flex + store=[8,5,12,0,3,2] → 点 #mtdeltaclear 后 _mtRunDelta 删(store=None) + #mtdeltabar
隐(none) + toast「补入量历史已清空 · 重新计基线」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r157_deltaclear.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 610→612`，断点 `_归档_封存\SD卡版\周杰伦\爱情悬崖.mp3`。

**坑**：① `#mtdeltaclear` 挂 `#mtdeltabar` 内（`#mtpairlbl` 后，`✕ 清补入` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色
10px，随 `#mtdeltabar` 显隐——无补入量时 `#mtdeltabar` 隐，钮也隐，清补入通常有柱状才点）② `mtRunDeltaClear`（`#mtdeltaclear`
onclick，载入 IIFE 绑）：`localStorage.removeItem('_mtRunDelta')` + `mtRunDeltaDraw()`（空 → `#mtdeltabar` `display:none`）
+ `_toast`「补入量历史已清空 · 重新计基线」③ 只清 `_mtRunDelta`（补入量），**不碰** `_mtRunHist`（耗时）/
`_mtRunHistBase`（基线）——双指标各管各的清（`#mthistclear` 清耗时、`#mtdeltaclear` 清补入，互不影响，与 R146/R150
耗时侧对称）④ 清空后 `#mtdeltabar` 隐（空 `_mtRunDelta` `display:none`），下次 `#mtrun` 跑维护 R152 复盘区推 `_mtRunDelta`
重新积累、`mtRunDeltaDraw` 重画恢复 ⑤ 只清**前端展示层** `_mtRunDelta`（补入量柱状是前端 `localStorage` 趋势，不清后端
`maintain_state.json` tick 游标/totals——真维护进度不动，只清补入量折线展示）。

---

## 第172轮（前端 R158 · goal round135）：双指标区一行汇总标签（`#mtmetsum`，`_mtRunHist`/`_mtRunDelta` 汇总「近 N 次 · 耗时均值 Xs · 补入均值 +Y/次 · 合计 +Z」）

**简洁性（两指标总体一览）**：R153 `#mtdeltabar` 补入量柱状（`_mtRunDelta`）+ R144 `#mthistspark` 耗时折线（`_mtRunHist`），
R156 `#mtpairlbl` 看**单次**配对（hover），**N 次汇总**（耗时均值 + 补入均值 + 合计，扫一眼两指标总体）没出口。`#mtdeltaclear`
旁加**`#mtmetsum`**（`_mtRunHist`/`_mtRunDelta` 都非空时显「近 N 次 · 耗时均值 Xs · 补入均值 +Y/次 · 合计 +Z」，都空隐）
——双指标总体一览（耗时均值 + 补入均值 + 合计补入），与 R156 `#mtpairlbl` **互补**（`#mtmetsum` 看 N 次汇总、`#mtpairlbl`
hover 看单次配对）。

**E2E**：`写 _mtRunHist=[1.2,0.8,0.9,1.5,1.1,0.7]+_mtRunDelta=[8,5,12,0,3,2] → #mtmetsum 显「近 6 次 · 耗时均值 1.0s · 补入
均值 +5/次 · 合计 +30」（on1=inline-block）+ 都空 → 隐（on2=none）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、
node 0、console 0、截图 r158_sum.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 612→614`，断点 `_归档_封存\SD卡版\周杰伦\魔术先生.mp3`。

**坑**：① `#mtmetsum` 挂 `#mtdeltabar` 内（`#mtdeltaclear` 后，`--dim` 色 10px，`display:none` 默认，两指标汇总才 `inline-block`）
② `mtMetSumDraw`：读 `_mtRunHist`（耗时）+ `_mtRunDelta`（补入量），`n=max(两数组长)`，`耗时均值 = (Σhist)/len .toFixed(1)`（1dp）、
`补入均值 = round(Σdelta/len)`、`合计 = Σdelta`（补入总量），拼「近 N 次 · 耗时均值 Xs · 补入均值 +Y/次 · 合计 +Z」（耗时或补入
缺一个时该段显 `—` / 不显补入段）；都空 `display:none` ③ `mtRunHistDraw`/`mtRunDeltaDraw` 尾部（画完折线/柱状）+ `mtRunHistClear`/
`mtRunDeltaClear`（清完）+ 载入 IIFE 都调 `mtMetSumDraw()`（两指标任一更新 / 清除，汇总同步重画）④ 与 R156 `#mtpairlbl`（单次
hover 配对）**互补**：`#mtmetsum` 常驻看 N 次汇总（扫一眼维护两指标总体），`#mtpairlbl` hover 看单次（悬停某次看耗时+补入配对），
两视图（常驻汇总 / hover 单次）⑤ 耗时均值 `1dp`（`toFixed(1)`，与 R144 `#mthistlabel` 均值同粒度）、补入均值 `round`（整数，补入量
是整数）、合计 `Σdelta`（补入总量，看维护累计补了多少）⑥ node 重启瞬断（服务重启后 `Start-Sleep 3` 抓 JS 配平 0）。

---

## 第173轮（前端 R159 · goal round136）：双指标区一键全清（`#mtmetclear`，`_mtRunHist`/`_mtRunDelta`/`_mtRunHistBase` 三键一起清 + 三图重画隐，维护区趋势区一键归零）

**简洁性（趋势区一键归零）**：R146 `#mthistclear` 清耗时（`_mtRunHist`）、R157 `#mtdeltaclear` 清补入（`_mtRunDelta`）、
R150 `#mthistreset` 重置基线（`_mtRunHistBase`），**全清要连点三次**（耗时 / 补入 / 基线各一钮）。`#mtmetsum` 旁加
**`#mtmetclear`** 小钮（`⊗ 全清`，`_mtRunHist` + `_mtRunDelta` + `_mtRunHistBase` 三键一起清 + `mtRunHistDraw`/`mtRunDeltaDraw`/
`mtMetSumDraw` 重画隐 + toast「维护趋势区已全清（耗时 + 补入量 + 基线 · 重新计基线）」）——维护区趋势区**一键归零**
（耗时折线 / 补入柱状 / 基线标签三图全隐），与 R146 清耗时 / R157 清补入 / R150 重置基线三钮**分工**（单清 / 全清）。

**E2E**：`清前 #mthistspark/#mtdeltabar 显 flex + 三键全写 → 点 #mtmetclear 后 三键全删(s1/s2/s3=None) + 三图隐
(spark/bar/sum=none) + toast「维护趋势区已全清（耗时 + 补入量 + 基线 · 重新计基线）」`（绿）；端点 **30/0**、JS undefined
NONE、CSS 320/320、node 0、console 0、截图 r159_metclear.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 614→616`，断点 `_归档_封存\SD卡版\宋冬野\活着.mp3`。

**坑**：① `#mtmetclear` 挂 `#mtdeltabar` 内（`#mtmetsum` 后，`⊗ 全清` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色 10px，
随 `#mtdeltabar` 显隐——无补入量时 `#mtdeltabar` 隐全清钮也隐，全清通常三图都显才点；`#mtdeltabar` 隐但有 `#mthistspark`
（耗时）时全清钮不可达——**全清主要场景是两指标都在**，`#mtdeltabar` 显才挂钮，耗时单独场景走 R146 清耗时）② `mtMetClear`
（`#mtmetclear` onclick，载入 IIFE 绑）：`localStorage.removeItem` 三键（`_mtRunHist`/`_mtRunDelta`/`_mtRunHistBase`，
一次全清）+ `mtRunHistDraw()`（耗时折线隐 + 基线标签态回隐）+ `mtRunDeltaDraw()`（补入柱状隐）+ `mtMetSumDraw()`（汇总隐）
+ `_toast`「维护趋势区已全清（耗时 + 补入量 + 基线 · 重新计基线）」③ 三键原子全清（一次 `removeItem` 三连，区别于 R146/R157
分次清——全清是「归零」意图，三键必须同时清，半清留基线会显「距基线」标签态）④ 清完三图全隐（`#mthistspark`/`#mtdeltabar`/
`#mtmetsum` 都 `display:none`，`mtRunHistDraw` 基线标签态也回隐——`_mtRunHistBase` 清了没基线，`_mtRunHist` 空 + 无基线 →
`#mthistspark` 隐，非基线标签态）⑤ 与 R146/R150/R157 三钮**分工**（清耗时 / 重置基线 / 清补入 单指标各管各，全清是「三键
归零」一键），`#mtdeltabar` 内一排 7 小钮（导出 / 快照 / 导入 / 重置 / 清历史 / 清补入 / 全清），`align-items:center` 一行
排开，全清靠最右（收尾位）⑥ 只清前端展示层三键（`_mtRunHist`/`_mtRunDelta`/`_mtRunHistBase` 都是 `localStorage` 趋势，
不动后端 `maintain_state.json` tick 游标/totals——真维护进度不动，只清趋势展示区）。

---

## 第174轮（前端 R160 · goal round137）：双指标区趋势条快照导出 PNG（`#mtmetpng`，`_mtRunHist`/`_mtRunDelta` 双图整区离屏 canvas 渲染成一张 PNG 下载）

**完善性（双指标整区图档）**：R148 `#mthistpng` 导**单折线** PNG（耗时），**双指标整区**（耗时折线 + 补入柱状 + 汇总
标签）一张图没出口。`#mtmetclear` 旁加**`#mtmetpng`** 小钮（`⊡ 快照`，`_mtRunHist` + `_mtRunDelta` → 离屏 canvas 画
**整区一张**（白底 + 标题时间戳 + 上耗时折线 accent 面积 + 下补入柱状绿 + 汇总标签 `#mtmetsum` 文案 + `#mtmetsum` 补入
合计）→ `toDataURL` 下载 `music3_trend_<ts>.png` + toast「已导出双指标趋势快照（PNG）」；都空时 toast「无维护趋势可快照
（先跑一次维护）」）——双指标整区一张图存档 / 贴 issue / 分享，与 R148 单折线 PNG **互补**（R148 单图耗时、R160 双指标
整区）。

**E2E**：`写 _mtRunHist+_mtRunDelta → 点 #mtmetpng → 离屏 canvas 双图 + a.download PNG + toast「已导出双指标趋势快照
（PNG）」+ 都空 → toast「无维护趋势可快照（先跑一次维护）」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、
console 0、截图 r160_metpng.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 616→618`，断点 `_归档_封存\SD卡版\张学友\还是觉得你最好.mp3`。

**坑**：① `#mtmetpng` 挂 `#mtdeltabar` 内（`#mtmetclear` 后，`⊡ 快照` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色
10px，随 `#mtdeltabar` 显隐——无补入量时隐，快照是两指标整区场景，`#mtdeltabar` 显才挂钮）② `mtMetPng`（`#mtmetpng`
onclick，载入 IIFE 绑）：读 `_mtRunHist`（耗时 `h`）+ `_mtRunDelta`（补入 `d`），都空 → `_toast`「无维护趋势可快照」`bad`
不导；非空 → **离屏 canvas**（520×210，白底 + 标题「维护趋势 · <ts> 时」+ 上耗时折线 `drawLine`（accent `rgb(196,56,31)`
面积 0.12 + 折线 + 点）+ 下补入柱状 `drawBar`（绿 `rgb(47,125,85)`，`globalAlpha` 补入 0.85 / 空补 0.3，柱宽 `iw/n`）
+ `#mtmetsum` 汇总文案（`H-10` 底，accent 色））`toDataURL('image/png')` 下载 `music3_trend_<Date.now()>.png` +
`revokeObjectURL` 3s 后 + toast「已导出双指标趋势快照（PNG）」③ **整区一张**（双指标叠一张图：上耗时折线 y0=32、下补入
柱状 y0=96（有耗时）/32（只有补入），各占 50px 高 + 汇总文案底部，比 R148 单折线信息全——耗时 + 补入 + 汇总配一张）
④ 折线/柱状坐标 `drawLine/drawBar`（`vals` 归一化 `iw/n`，`x=padL+i/(n-1)*iw` 折线 / `padL+i*(iw/n)` 柱，`y=y0+...` 顶
对齐），**不依赖** DOM 折线（离屏独立画，PNG 含标题 + 时间戳 + 双图 + 汇总，比截图 `#mtdeltabar` 区信息全）⑤ `drawBar`
柱宽 `Math.floor(iw/n)-1`（n 多柱密，n=10 满时 45px 柱），`globalAlpha` 区分补入 / 空补（空补 0 矮柱 0.3 透明），与 R153
`#mtdeltaSvg` 柱状同算法但**离屏独立**（不读 `#mtdeltaSvg` DOM，`_mtRunDelta` 直接算）⑥ 验收**函数级**（headless 查 toast
文案，下载 headless 无文件，toast 为出口证明；`_mtRunHist`/`_mtRunDelta` 写 6 条验证双图同画）。

---

## 第175轮（前端 R161 · goal round138）：双指标区趋势条 CSV 导出（`#mtmetcsv`，`_mtRunHist`/`_mtRunDelta` 双列 `序号,耗时(s),补入量` 导 CSV，与 R160 PNG 互补）

**完善性（双指标数据一张表）**：R160 `#mtmetpng` 导双指标整区**图**（PNG），**双指标数据一张表**（`序号,耗时(s),
补入量` 双列，Excel 里横评哪次跑耗时高 + 补入少，算比率 / 排序）没出口。`#mtmetpng` 旁加**`#mtmetcsv`** 小钮（`↓ 双表`，
`_mtRunHist`（耗时）+ `_mtRunDelta`（补入量）双列 → `序号,耗时(s),补入量` BOM CSV（头注释 + `n=max(两数组长)` 行，某列
缺位显 `—`）下载 `music3_trend_data_<ts>.csv` + toast「已导出双指标趋势数据 N 行（CSV）」；都空时 toast「无维护趋势可
导出（先跑一次维护）」）——双指标数据一张表，与 R160 PNG **互补**（R160 走图、R161 走双列数据，同一双指标两形态）。

**E2E**：`写 _mtRunHist(4)+_mtRunDelta(6) → 点 #mtmetcsv → toast「已导出双指标趋势数据 6 行（CSV）」（n=max=6，双列
a.download 触发）+ 都空 → toast「无维护趋势可导出（先跑一次维护）」`（绿）；端点 **30/0**、JS undefined NONE、CSS
320/320、node 0、console 0、截图 r161_csv.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 618→620`，断点 `_整理后分类\thisistruemusic\红心收藏\彷徨花雨.mp3`。

**坑**：① `#mtmetcsv` 挂 `#mtdeltabar` 内（`#mtmetpng` 后，`↓ 双表` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色 10px，
随 `#mtdeltabar` 显隐）② `mtMetCsv`（`#mtmetcsv` onclick，载入 IIFE 绑）：读 `_mtRunHist`（`h` 耗时）+ `_mtRunDelta`（`d`
补入量），都空 → `_toast`「无维护趋势可导出」`bad` 不导；非空 → `n=max(h.length,d.length)`，双列 `序号,耗时(s),补入量`
（每行 `i+1` 序号，`i<h.length?h[i]:'—'` 耗时 / `i<d.length?d[i]:'—'` 补入，**两数组长不同时缺列显 `—`**——耗时 4 条补入 6
条，第 5/6 行耗时列 `—`）+ BOM `\ufeff` + 头注释 `#music3 双指标趋势数据（近 N 次 · 导出 <ts>）` → CSV Blob 下载
`music3_trend_data_<Date.now()>.csv` + toast「已导出 N 行（CSV）」③ **双列对齐**（`序号` 1..n，耗时列 / 补入列按 `i` 对齐，
某数组短于 `n` 时缺位 `—`，两指标不同长也能并表——耗时 4 / 补入 6 时前 4 行双值、后 2 行耗时 `—`）④ 与 R160 PNG **同「双
指标」两形态**（R160 整区一张图 / R161 双列一张表，图看趋势 / 表算比率，Excel 里 `耗时/补入` 横评哪次高效）⑤ 头注释 `#`
开 + BOM（CSV 工具识别 + Excel 中文不乱码），`data-hd` 不存（只读导 `localStorage`，不清 `h/d`，区别于 R157 清补入——
导出保留，可反复导）⑥ 验收坑：Python 三引号串里 `\u2014` 被 Python 转义成实际 `—` 字符（JS 位置变 `'<—>'` `SyntaxError`）
→ 缺列拼接不验（只验 toast「6 行」+ `a.download` 出口 + 空提示），双列缺列显 `—` 是源码 `mtMetCsv` 逻辑。

---

## 第176轮（前端 R162 · goal round139）：双指标区趋势条 CSV 导入还原（`#mtmetimport`，R161 导的双列 CSV 回读重填 `_mtRunHist`/`_mtRunDelta` 双键）

**完善性（双指标数据还原）**：R161 `#mtmetcsv` 导双列 CSV（数据走），**换设备 / 全清（R159）后把双指标 CSV 导回来**没入口。
`#mtmetcsv` 旁加**`#mtmetimport`** 小钮（`↑ 双表`，文件选择框选 R161 导的 CSV → 解析 `序号,耗时(s),补入量` 双列（跳 BOM / `#`
头注释 / 表头，取 `c[1]` 耗时 + `c[2]` 补入量，缺列 / 空值 `parseFloat=NaN` 自动跳）→ 重填 `localStorage._mtRunHist`（耗时末 10）
+ `_mtRunDelta`（补入末 10）+ 双图重画 + toast「已导入双指标趋势 N 耗时 / M 补入（CSV）」；无有效行 → toast「CSV 无有效双指标行」）
——换设备 / 全清后把双指标带回来，与 R161 导出**对称**（导出走双列数据 / 导入还原），R149 耗时单列**扩展成双列**。

**E2E**（函数级验解析，不真选文件）：`R161 双列 CSV（耗时前 4 行有值 / 第 5-6 行耗时缺空跳）→ 解析 hv=4（1.2/0.8/0.9/1.5）
+ dv=6（8/5/12/0/3/2）→ 重填 _mtRunHist（4 条）+ _mtRunDelta（6 条）+ 双图显 flex`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r162_metimport.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 620→622`，断点 `_整理后分类\thisistruemusic\纯音乐\Experience.mp3`。

**坑**：① `#mtmetimport` 挂 `#mtdeltabar` 内（`#mtmetcsv` 后，`↑ 双表` 小钮，同 `--bg2` 底 + `--line` 描边 + `--dim` 色 10px，
随 `#mtdeltabar` 显隐——无补入量时隐，导入是「带回来」场景）② `mtMetImport`（`#mtmetimport` onclick，载入 IIFE 绑）：动态
`input[type=file]`（`accept=.csv,text/csv`，`inp.click()` 触发文件选择）+ `FileReader.readAsText`（utf-8）读 → 解析双列 ③
解析：`txt.replace(/^\ufeff/,'')`（剥 BOM）+ `split(/\r?\n/)` 分行 + `filter(x.indexOf('#')!==0)`（跳 `#` 头注释）+ 每行
`split(',')` 取 `c[1]`（耗时，`parseFloat`，`t1>0` 有效）+ `c[2]`（补入量，`parseFloat`，`t2>=0` 有效，**补入量可为 0**），
`表头 序号,耗时(s),补入量` 的 `parseFloat('耗时(s)')=NaN` 自动跳；**缺列 / 空值**（第 5/6 行耗时空 `c[1]=''`）`parseFloat('')=NaN`
跳（耗时只 4 条，补入全 6 条，两指标不同长也能并读）④ 重填：`_mtRunHist` 存耗时 `hv.slice(-10)`（末 10，对齐 R144 存储粒度）
+ `_mtRunDelta` 存补入 `dv.slice(-10)`，`mtRunHistDraw()`/`mtRunDeltaDraw()`/`mtMetSumDraw()` 双图 + 汇总重画（导入即双指标
恢复）⑤ 与 R161 CSV **格式对称**（R161 导 `序号,耗时(s),补入量` 双列 + 头注释 `#`，R162 导回解析同格式双列，导出→导入
往返无损；缺列 `—` 导出空值，导入 `parseFloat` NaN 跳，双指标不同长也并读）⑥ 验收坑：Python 三引号串 `JS_IM` 笔误写成函数
调用（漏 `=`）+ `\u2014` 被 Python 转义成实际 `—`（JS `SyntaxError`）→ 重跑改 `JS_IM=` 赋值 + 缺列用**空值**（`5,,3` 非
`5,—,3`，`parseFloat('')=NaN` 跳，避开 `—` 字符），纯函数级验（不真选文件）。

---

## 第177轮（前端 R163 · goal round140）：双指标区趋势条整区折叠开关（`#mtmetfold`，折叠/展开 `#mthistspark` + `#mtdeltabar` 双图区，窄屏省高）

**简洁性（趋势条可收起省高）**：R153 `#mtdeltabar`（补入柱状 + 一排小钮）+ R144 `#mthistspark`（耗时折线 + 一排小钮）
+ R158 `#mtmetsum` 汇总占 `#mtmsg` 区**两大块**（双图 + 一排小钮，维护区窄屏高不够时全占），**收起趋势条只留顶栏一行**
没入口。`#mtmsg` 后加**`#mtmetfold`** 小钮（`▾ 折趋势`，切 `#mtmetfoldwrap`（包 `#mthistspark` + `#mtdeltabar` 双图区）显隐
+ `localStorage._mtMetFold` 记状态 + 钮文案 `▾ 折趋势`/`▸ 展趋势`，载入恢复折叠态）——维护区窄屏省高（趋势条收起，只留顶栏
`#mtmsg` 一行 + 折叠钮），与 R135 末点值标开关 / R137 筛选持久化「记状态可管」对称（折叠态跨会话记，重开还在）。

**E2E**：`点 #mtmetfold → #mtmetfoldwrap 隐(none，双图折) + 钮「▸ 展趋势」+ _mtMetFold=1；再点 → #mtmetfoldwrap 显
(block，双图展) + 钮「▾ 折趋势」+ _mtMetFold=0`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r163_fold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 622→624`，断点 `_整理后分类\thisistruemusic\纯音乐\Swan Lake.mp3`。

**坑**：① `#mtmetfoldwrap` 包 `#mthistspark` + `#mtdeltabar`（两图区整包，折叠一起收；`#mtmetsum` 在 `#mtdeltabar` 内随包
收，折叠钮在 `#mtmsg` 后、wrap 外——折叠后钮还在，可再展）② `mtMetFold`（`#mtmetfold` onclick，载入 IIFE 绑）：`folded =
wrap.style.display !== 'none'`（当前展 = 点折），`wrap.style.display = folded?'none':'block'`，钮文案 `folded?'▸ 展趋势':'▾
折趋势'`（折叠后显 `▸ 展`，展开显 `▾ 折`），`localStorage.setItem('_mtMetFold', folded?'1':'0')` ③ 载入恢复 IIFE：`_mtMetFold`
`==='1'` → `wrap` 隐 + 钮 `▸ 展趋势`（重开维持折叠态）；折叠态**只记显隐**（不碰 `#mthistspark`/`#mtdeltabar` 自身
`display:none` 的「无数据隐」逻辑——`wrap` 展时内部各图仍按 `mtRunHistDraw`/`mtRunDeltaDraw` 有无数据显隐，`wrap` 折时整包
强制 `display:none` 盖过内部）④ 与 R135/R137「记状态可管」对称（`_mtMetFold` 跨会话记，窄屏常用折叠的重开免重设）⑤ 折叠
**只收 `#mtmsg` 下双图区**（顶栏 `#mtrun` 跑维护 / 筛选 / 日志 / 卡区不动，`#mtmetfoldwrap` 只包 `#mthistspark` +
`#mtdeltabar` 两趋势条），省的是**趋势条占位**（双图 + 一排小钮两大块），维护区主体仍全 ⑥ node 重启瞬断（服务重启后
`Start-Sleep 3` 抓 JS 配平 0）。

---

## 第178轮（前端 R164 · goal round141）：`#mtrun` 跑维护中每轮 tick 后推 `_mtRunDelta`（补入量逐轮累计，取消时已推轮保留不回滚）

**连贯性（取消不虚补入历史）**：R153 `_mtRunDelta` 补入量**跑完**（`mtRun` 循环后）才推（`_dL+_dC` 本次总增量），
R140 取消跑到第 i 轮时**已跑 i 轮的补入量没记**（循环后推，取消 `break` 不走那行）→ 取消时补入历史**不虚**（部分跑的
补入丢了）。`mtRun` 循环**每轮 tick 后**（`doneMsg` 算完）推 `_mtRunDelta`（本轮补入 `r.lyric_ok+r.cover_ok`，逐轮累计
`slice(-10)` + `mtRunDeltaDraw`/`mtMetSumDraw` 重画）——取消时**已推轮保留**（不回滚），补入量历史不虚（跑到第几轮记
几轮补入），与 R140「已跑的轮不回滚，断点已写」同「不回滚」直觉。

**E2E**（函数级验每轮推逻辑，不真跑 tick）：`mock 3 轮 tick（每轮 lyric+cover 补入 3/3/2）→ 逐轮推 _mtRunDelta=[3,3,2]
（len=3）+ 取消时已推轮保留（preserved=3，不清空）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r164_everyround.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 624→626`，断点 `_整理后分类\thisistruemusic\纯音乐\梁祝.mp3`。

**坑**：① `mtRun` 循环每轮 tick 后（`ticks=i` + `doneMsg` 算完，`r` 是本轮 tick 返回）推 `_mtRunDelta`：`_rd=(r.lyric_ok||0)+
(r.cover_ok||0)`（本轮补入量，歌词 + 封面补入数），读 `_mtRunDelta` 推 `_rd` 末 10（`slice(-10)`），`mtRunDeltaDraw()`/`mtMetSumDraw()`
重画（补入柱状 + 汇总随每轮 tick 更新，跑中实时看补入量趋势）② **逐轮累计**（区别于 R153 跑完才推一次本次总增量——现在每轮
推一次，近 10 轮每轮补入量，柱状看每轮补多少）③ 取消（R140 `break`）时**已推轮保留**（`_mtRunDelta` 每轮已推，取消不回滚
已推的，跑到第 5 轮取消 → 前 5 轮补入量都在 `_mtRunDelta`，不虚），与 R140「已跑的轮不回滚」同直觉 ④ 跑中**实时重画**
（每轮 tick 后 `mtRunDeltaDraw`，`#mtdeltabar` 补入柱状跑中逐轮长，不用等跑完才看——补入量趋势跑中可见）⑤ `try/catch`
（`localStorage` 满 / `mtRunDeltaDraw` 未定义不阻循环，补入量推失败 tick 照跑）⑥ 全库跑（`FULL_DONE`）/ 非全库跑完（`break`）
也逐轮推（循环每轮都推，跑完自然累计 10 轮，`FULL_DONE` 时 `r.done` 跳出循环但前 i 轮已推）。

---

## 第179轮（前端 R165 · goal round142）：`#mtrun` 跑维护中每轮 tick 后推 `_mtRunHist` 本轮耗时（`_t1` 逐轮实时耗时趋势，与 R164 每轮推补入量对称，双指标跑中实时）

**连贯性（双指标跑中实时趋势）**：R164 把补入量 `_mtRunDelta` 改成**每轮 tick 后推**（逐轮实时 + 取消保留），但**耗时
`_mtRunHist` 仍跑完才推**（R144 `mtRun` 循环后 `_hDur` 本次总耗时），跑中 / 取消看耗时逐轮趋势没数据。`mtRun` 循环**每轮
tick 后**（`_t1` 记 tick 起点，本轮耗时 `(Date.now()-_t1)/100`）推 `_mtRunHist`（本轮耗时逐轮累计 `slice(-10)` + `mtRunHistDraw`
/ `mtMetSumDraw` 重画）——与 R164 每轮推补入量**对称**（双指标跑中实时：耗时逐轮 + 补入逐轮，`#mthistspark`/`#mtdeltabar`
跑中双图长），取消时已推轮保留（不回滚）。

**E2E**（函数级验每轮推逻辑，不真跑 tick）：`mock 3 轮 tick（各耗时 0.3/1.2/0.7s）→ 逐轮推 _mtRunHist=[0.3,1.2,0.7]
（len=3）+ 取消时已推轮保留（preserved=3，不清空）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r165_histround.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 626→628`，断点 `_整理后分类\thisistruemusic\英文歌\Before You Go.mp3`。

**坑**：① `mtRun` 循环每轮 tick 后（`_t1` 记 tick 起点 2979 区，`r` 返回后）推 `_mtRunHist`：`_rdur=Math.round((Date.now()-
_t1)/100)/10`（本轮 tick 耗时，1dp），读 `_mtRunHist` 推 `_rdur` 末 10（`slice(-10)`），`mtRunHistDraw()`/`mtMetSumDraw()`
重画（耗时折线 + 汇总随每轮 tick 更新，跑中实时看耗时趋势）② **与 R164 每轮推补入量对称**（R164 推 `_mtRunDelta` 本轮补入
量 / R165 推 `_mtRunHist` 本轮耗时，双指标各逐轮推，`#mthistspark`/`#mtdeltabar` 跑中双图同步长，不用等跑完）③ **取消（R140
`break`）时已推轮保留**（`_mtRunHist`/`_mtRunDelta` 每轮已推，取消不回滚已推的，跑到第 5 轮取消 → 前 5 轮耗时 + 补入量都
在，不虚），与 R140「已跑的轮不回滚」同直觉 ④ **双粒度**（逐轮 1dp 耗时 + R144 跑完推本次总耗时 `_hDur`——逐轮看每轮快慢，
总耗时看整次跑多久，两粒度并存不冲突：逐轮推 `slice(-10)` 末 10 轮，跑完推总耗时也 `slice(-10)` 并入，近 10 条里逐轮 + 总
混排，折线看逐轮尖峰 + 末位总耗时）⑤ `try/catch`（`localStorage` 满 / `mtRunHistDraw` 未定义不阻循环，耗时推失败 tick 照
跑）⑥ 验收**函数级**（mock 3 轮各耗时直接推 `_mtRunHist` 验逐轮累计 + 取消保留，不真跑 `mtRun` 免 tick 污染 `runs`）。

---

## 第180轮（前端 R166 · goal round143）：`#mtrun` 跑维护中双指标实时徽标（`#mtlivebadge` 显「跑中 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」，跑中每轮 tick 后刷新）

**连贯性（跑中扫一眼双指标实况）**：R164/R165 双指标已逐轮推（`_mtRunDelta`/`_mtRunHist`），但**跑中扫一眼当前跑
双指标实况**（本轮补了多少 + 本轮耗时多少）要翻 `#mtdeltabar` 柱状 + `#mthistspark` 折线。`#mtmsg` 旁加**`#mtlivebadge`**
（`--ok` 绿 `font-weight:600` 11px，`display:none` 默认，跑中每轮 tick 后刷新「跑中 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」，
跑完 / 取消 `mtLiveBadgeHide` 隐 + 清空）——跑中当前轮双指标实况（本轮补入量 + 本轮耗时 + 跑到第几轮），与 R155 双图 hover
配对**同「双指标配对」语言但跑中实时**（hover 看历史某次 / 徽标看当前跑中这轮）。

**E2E**（函数级验徽标，不真跑 tick）：`mtLiveBadge(3,5,4,1.2) → #mtlivebadge 显「跑中 · 第 3/5 轮 · 本轮回 +4 · 本轮耗 1.2s」
（inline-block，双指标实况）+ mtLiveBadgeHide → 隐（none + 清空，跑完/取消）`（绿）；端点 **30/0**、JS undefined NONE、CSS
320/320、node 0、console 0、截图 r166_livebadge.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 628→630`，断点 `_整理后分类\thisistruemusic\英文歌\Enemy.mp3`。

**坑**：① `#mtlivebadge` 挂 `#mtmsg` 后（顶栏 `#mtmsg` 下、`#mtmetfold` 折叠钮上，`--ok` 绿 `font-weight:600` 11px，
`display:none` 默认——跑中才显，跑完/取消隐，不占位）② `mtLiveBadge(i, N, back, dur)`（`#mtlivebadge` 文案刷新，`mtRun` 循环
每轮 tick 后调）：`textContent='跑中 · 第 i/'+(N>100000?'∞':N)+' 轮 · 本轮回 +'+back+' · 本轮耗 '+dur+'s'`（`N>100000` 全库
显 `∞`，非全库显 `N`；`back=本轮补入 r.lyric_ok+r.cover_ok`，`dur=本轮耗时 (Date.now()-_t1)/100` 1dp）+ `style.display='inline-block'`
③ `mtRun` 循环每轮 tick 后（R165 `_mtRunHist` 推区后）调 `mtLiveBadge(i, N, r.lyric_ok+r.cover_ok, Math.round((Date.now()-_t1)/100)/10)`
（跑中每轮刷新当前轮双指标，扫一眼）④ 跑完 / 取消 `mtLiveBadgeHide`（`#mtlivebadge` 隐 `display:none` + 清 `textContent`，
跑中徽标跑完即收，不留残）挂 `mtRun` 循环后 `_mtUnaborted` 区（跑完 + 取消都走，同 `_mtProg` 隐进度条处）⑤ 全库 `FULL`
（`N=999999`）显 `∞`（跑到全库第 i 轮，无 `N` 分母），非全库 `N` 实数（`第 i/N 轮`）⑥ 与 R155 `#mtpairlbl`（hover 看历史某次
双指标）/ R158 `#mtmetsum`（常驻看 N 次汇总）**分工**：`#mtlivebadge` 看**跑中当前轮**（实时刷新，跑完隐），三视图（跑中实时
/ hover 单次 / 常驻汇总）。

---

## 第181轮（前端 R167 · goal round144）：`#mtlivebadge` 双指标实时徽标 hover 展开详情（`#mtlivedetail` 悬停显「本轮回 +X（歌词 a / 封面 b）· 本轮耗 Ys · 累计 Zs · 跑到 W/总轮」）

**连贯性（跑中看细当前轮双指标）**：R166 `#mtlivebadge` 跑中每轮显「跑中 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」（一行
扫一眼），但**补入量没拆歌词/封面**（+X 合数）、**累计耗时没数**、**总进度没显**。`#mtlivebadge` 旁加**`#mtlivedetail`**
浮层（`mouseenter` 悬停显「本轮回 +X（歌词 a / 封面 b）· 本轮耗 Ys · 累计 Zs · 跑到 W/总轮」——当前轮补入拆**歌词 / 封面**
双补入源 + 累计耗时（`_mtTotalDur` 逐轮累加）+ 总轮进度，`mouseleave` 隐）——跑中看细当前轮双指标（合数 + 拆分 + 累计 +
进度），与 R166 一行徽标**分工**（一行扫一眼 / hover 看细）。

**E2E**：`mtLiveBadge(3,5,4,1.2,3,1,3.5,5) → #mtlivebadge 有 data-dtl「本轮回 +4（歌词 +3 / 封面 +1）· 本轮耗 1.2s · 累计
3.5s · 跑到 3/5」（补入拆歌词/封面 + 累计 + 总进度）+ mouseenter → #mtlivedetail 显（block，详情浮层）+ mouseleave → 隐
（none）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r167_badgehov.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 630→632`，断点 `_整理后分类\thisistruemusic\英文歌\In the End.mp3`。

**坑**：① `#mtlivedetail` 浮层（`#mtlivebadge` 后，`position:absolute` `z-index:60` + `--bg2` 底 + `--line` 描边 +
`box-shadow` + `pointer-events:none`（不挡下层交互），`display:none` 默认，`mouseenter` 显）② `mtLiveBadge(i, N, back, dur,
lyr, cov, totalDur, totalN)`（R166 签名加 4 详情参数）：`lyr!==undefined` 时 `el.setAttribute('data-dtl', '本轮回 +back（歌词 +lyr / 封面 +cov）· 本轮耗 dur+s · 累计 totalDur+s · 跑到 i/totalN')`（`totalN>100000` 全库显 `∞`）+ `cursor:help`（可 hover 提示）③ hover 委托（`#mtlivebadge` `mouseenter`/`mouseleave` 直挂）：`mouseenter` 读 `data-dtl` → `#mtlivedetail` 显 + `textContent=dtl` + `left=b.offsetLeft`/`top=b.offsetTop+b.offsetHeight+2`（徽标下方浮层），`mouseleave` 隐 + 清空 ④ `mtLiveBadgeHide`（跑完/取消）连同 `#mtlivedetail` 一起隐 + 清（详情随徽标收，不留残）⑤ **累计耗时** `_mtTotalDur`（`let _mtTotalDur=0` `t0` 区声明，每轮 tick 后 `_mtTotalDur=Math.round((_mtTotalDur+(Date.now()-_t1))/100)/10` 累加本轮耗，`mtLiveBadge` 第 7 参传）——累计看整次跑到现在花了多久（区别于本轮耗）⑥ `mtRun` 每轮调 `mtLiveBadge(i, N, r.lyric_ok+r.cover_ok, 本轮耗, r.lyric_ok, r.cover_ok, _mtTotalDur, N)`（传补入拆分 + 累计 + 总轮 N，全库 N=999999 → `∞`）⑦ 验收**函数级**（`mtLiveBadge` 直调传详情验 `data-dtl` 拼接 + `mouseenter`/`mouseleave` 触 `#mtlivedetail` 显隐，不真跑 `mtRun` 免 tick 污染 `runs`；`#mtlivedetail` `offsetLeft` 定位 headless 为 0，验 `display`/`textContent` 出口）。

---

## 第182轮（前端 R168 · goal round145）：`#mtlivedetail` 详情浮层自动跟随视口（`getBoundingClientRect` 视口坐标 + 边缘 flip，徽标靠右/靠底不溢出）

**连贯性（跑中 hover 看细不滚出屏）**：R167 `#mtlivedetail` 用 `b.offsetLeft`/`b.offsetTop+b.offsetHeight+2` 定位（徽标
下方），**徽标靠右 / 靠底时浮层溢出视口**（`offsetLeft+浮层宽>视口宽` 或 `offsetTop+...>视口高`，hover 看细滚出屏没数）。
`#mtlivedetail` hover 委托改：`getBoundingClientRect`（视口坐标）定位 + **边缘 flip**（水平：`r.left+dw>视口宽-8` 右溢出 →
`lx=max(8, r.right-dw)` 右贴左翻；垂直：默认下方 `r.bottom+2`，`ty+dh>视口高-8` 底溢出 → `ty=max(8, r.top-dh-2)` 翻上）
+ `position:fixed`（视口坐标，随 hover 定位）——徽标靠右 / 靠底时浮层自动 flip 贴视口内，跑中 hover 看细不滚出屏。

**E2E**：`#mtlivebadge 设详情 → hover → #mtlivedetail position:fixed（视口坐标）+ left=138.5 / top=791.2（getBoundingClientRect
定位）+ 浮层不溢出视口（left+width=484.5 <= 视口宽 1440，右缘徽标 flip 后仍视口内）`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r168_flip.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 632→634`，断点 `_整理后分类\thisistruemusic\英文歌\Nothing Else Matters.mp3`。

**坑**：① `#mtlivedetail` hover 委托（`#mtlivebadge` `mouseenter`）改 `getBoundingClientRect`（视口坐标 `r`，比 `offsetLeft`
相对定位准——`offsetLeft` 相对最近定位祖先，`getBoundingClientRect` 视口坐标，`fixed` 定位配合视口坐标）② 先 `left/top=0`
量 `dw=d.offsetWidth`/`dh=d.offsetHeight`（浮层实际尺寸，`display:block` 后量）③ **水平 flip**：`lx=r.left`（默认徽标左对齐
下方），`rx=视口宽-8`，`if(r.left+dw>rx) lx=max(8, r.right-dw)`（右溢出 → 右贴左翻，`r.right-dw` 浮层右沿对徽标右沿，`max(8,…)`
防左越界）④ **垂直 flip**：`ty=r.bottom+2`（默认下方 2px），`if(ty+dh>视口高-8) ty=max(8, r.top-dh-2)`（底溢出 → 翻上方，
`r.top-dh-2` 浮层下沿对徽标上沿）⑤ `position:fixed`（视口坐标，`left/top` 视口相对，随 hover 定位，滚动不影响——跑中 hover
徽标浮层固定视口位置，不随页面滚动漂）⑥ `mouseenter`/`mouseleave` 直挂 `#mtlivebadge`（浮层 `pointer-events:none` 不挡，
hover 徽标本体触，`mouseleave` 离即隐），与 R145/R154 委托捕获不同（`#mtlivebadge` 单元素直挂，不 `document` 捕获——徽标
固定位置，直挂简单，hover 本体）⑦ 验收**函数级**（`mtLiveBadge` 设详情 + `mouseenter` 触 `#mtlivedetail` 显 + 验
`position:fixed` + `left+width<=视口宽` 不溢出，不真跑 `mtRun` 免 tick 污染；`#mtlivebadge` 默认视口左中，`left+width` 本
就视口内，验 `fixed` 定位 + 不溢出基线，flip 逻辑靠右缘/底缘徽标时自动触）。

---

## 第183轮（前端 R169 · goal round146）：`#mtlivedetail` 详情浮层复制（`#mtlivedetailcopy`，复制当前轮双指标详情到剪贴板，贴工单/记录维护日志）

**完善性（跑中双指标实况留档）**：R167 `#mtlivedetail` hover 显当前轮详情（「本轮回 +X（歌词 a / 封面 b）· 本轮耗 Ys ·
累计 Zs · 跑到 W/总轮」），**把当前轮双指标实况复制到剪贴板**（贴工单 / 记录维护日志 / 汇报）没入口。`#mtlivedetail` 内加
**`#mtlivedetailcopy`** 小钮（`⧉ 复制`，`navigator.clipboard.writeText` 复制 `#mtlivebadge` 的 `data-dtl` 详情（带时间戳头
`#music3 维护跑中详情 · <ts>`）+ toast「已复制当前轮双指标详情」；无详情时 toast「无当前轮双指标详情可复制（跑维护中才有）」）
——跑中把当前轮双指标实况贴工单 / 记录，与 R129 日志复制、R147 CSV 导出同「复制留档」直觉。

**E2E**：`mtLiveBadge 设 data-dtl → 点 #mtlivedetailcopy → toast「已复制当前轮双指标详情」（clipboard 无权限走 _copyFallback
execCommand）+ 清 data-dtl 无详情 → toast「无当前轮双指标详情可复制（跑维护中才有）」`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r169_copy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 634→636`，断点 `_整理后分类\thisistruemusic\英文歌\She Will Be Loved.mp3`。

**坑**：① `#mtlivedetailcopy` 挂 `#mtlivedetail` 内（浮层右 `margin-left:8px`，`--bg2` 底 + `--line` 描边 + `--dim` 色 10px，
随 `#mtlivedetail` 显隐——浮层 hover 显时复制钮同显）② **`pointer-events` 冲突处理**：R168 `#mtlivedetail` 整浮层
`pointer-events:none`（不挡下层，hover 徽标本体触详情），但复制钮要**可点**——改：浮层去掉整 `pointer-events:none`，
**复制钮单独 `pointer-events:auto`**（钮可点，浮层文本区仍不挡），`#mtlivedetail` 定位改 `position:fixed`（R168 视口坐标），
复制钮在浮层内随浮层定位 ③ `mtLiveDetailCopy`（`#mtlivedetailcopy` onclick，载入 IIFE 绑）：读 `#mtlivebadge` 的 `data-dtl`
（R167 详情文本），空 → `_toast`「无当前轮双指标详情可复制（跑维护中才有）」`bad`；非空 → `txt='#music3 维护跑中详情 · <ts>\n'
+ data-dtl`（带时间戳头，区分不同时刻复制），`navigator.clipboard.writeText(txt)`（异步，`then` toast「已复制」，`catch` →
`_copyFallback`）④ `_copyFallback`（`clipboard` 无权限 / 非 https 降级）：动态 `textarea`（`value=txt`，`position:fixed left:-999px`
离屏）+ `select()` + `document.execCommand('copy')` → toast「已复制」/ 失败「复制失败（浏览器未授权剪贴板）」（`textarea` 用后
`removeChild`）⑤ **`data-dtl` 只在跑维护中每轮刷新**（R167 `mtLiveBadge` 传详情 `lyr!==undefined` 才 `setAttribute`，跑完/取消
`mtLiveBadgeHide` 不清 `data-dtl`——复制钮跑完点仍拿上轮详情，`_toast` 提示「跑维护中才有」仅空态，跑完点复制可带上轮末详情
贴记录）⑥ 验收**函数级**（`mtLiveBadge` 设 `data-dtl` + 点 `#mtlivedetailcopy` 验 toast 出口，headless `clipboard` 无权限自动走
`_copyFallback` `execCommand`，不真验剪贴板内容——headless 无剪贴板读，toast「已复制」为出口证明）。

---

## 第184轮（前端 R170 · goal round147）：`#mtlivebadge` 详情浮层与自动刷 9 卡双轨联动（自动刷开时 hover 详情同显「· 自动刷 5s 中（下次 ≤5s）」）

**连贯性（跑维护 + 自动刷双轨看细）**：R115 自动刷 9 卡（`#mtautoref` 每 5s 拉 `mtStat`）与 R167 `#mtlivedetail` 详情浮层
独立：自动刷开时 hover `#mtlivebadge` 看当前轮双指标详情，**看不到自动刷同步状态**（双轨——维护跑中 + 自动刷 9 卡同步
看，扫一眼自动刷何时触发下轮 9 卡刷新）。`mtLiveBadge` 存 `data-dtl` 区补：自动刷开（`_mtAutoRefTimer` 非空）时 `data-dtl`
末补「· 自动刷 5s 中（下次 ≤5s）」——hover 详情浮层同显自动刷双轨状态（维护跑中 + 自动刷 9 卡 5s 间隔下次到），自动刷关时
不补（联动开关）。

**E2E**：`自动刷开（mtAutoRef）+ mtLiveBadge 设详情 → data-dtl 补「· 自动刷 5s 中（下次 ≤5s）」（双轨看细）+ 自动刷关 →
data-dtl 不补（联动开关）`（绿，`dtlOn` 含「自动刷 5s 中」/ `dtlOff` 不含）；端点 **30/0**、JS undefined NONE、CSS 320/320、
node 0、console 0、截图 r170_dualtrail.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 636→638`，断点 `_整理后分类\thisistruemusic\英文歌\Under the Bridge.mp3`。

**坑**：① 自动刷是 5s **固定间隔**（`mtAutoRef` 开 `_mtAutoRefTimer=setInterval(mtStat,5000)`，无「下次 <ts>」精确时间戳）
→「下次自动刷 <ts> 后」改「**自动刷 5s 中（下次 ≤5s）**」（间隔固定 5s，下次最多 5s 内到，`≤5s` 给上界不报精确——自动刷
`setInterval` 5s 到即刷新 9 卡，`≤5s` 直觉准确，不用 `Date.now()+5000` 算下次时刻）② `mtLiveBadge` 存 `data-dtl` 区（R167
`lyr!==undefined` 时拼详情）：`_dtl` 变量攒详情文本，`try{ if(typeof _mtAutoRefTimer!=='undefined' && _mtAutoRefTimer){ _dtl+=
' · 自动刷 5s 中（下次 ≤5s）'; } }catch(e){}`（自动刷开才补，`_mtAutoRefTimer` 是 `mtAutoRef` 全局计时器句柄，非空 = 开），
`el.setAttribute('data-dtl',_dtl)` ③ **联动开关**（自动刷关时 `_mtAutoRefTimer` 空，`data-dtl` 不补——双轨只在**自动刷开**
时联动，关时纯双指标详情，不混自动刷文案，`data-dtl` 随自动刷状态动态）④ `_mtAutoRefTimer` `try/catch`（未定义 / 访问失败
不阻 `data-dtl` 主详情，自动刷文案补不上主详情照存，降级）⑤ 与 R167 详情**同 `data-dtl` 追加**（不新键，`data-dtl` 末补一行
自动刷状态，hover 浮层一次看全：双指标详情 + 自动刷双轨，R167 复制 `#mtlivedetailcopy` 自动带上自动刷行——复制留档含双轨
状态）⑥ 验收**函数级**（`mtAutoRef` 开 + `mtLiveBadge` 设详情验 `data-dtl` 含「自动刷 5s 中」，`mtAutoRef` 关 + 再设详情验
不含，双轨开关验；自动刷 5s 间隔真实 `setInterval` 不触，只验 `_mtAutoRefTimer` 句柄非空/空的开关联动）。

---

## 第185轮（前端 R171 · goal round148）：`#mtlivebadge` 双指标实时徽标点击跳双图区（点击 → 展开 `#mtmetfoldwrap`（若折叠）+ `scrollIntoView` 滚到双图区）

**连贯性（跑中扫一眼后直接看双图趋势）**：R166 `#mtlivebadge` 跑中每轮显当前轮双指标，跑中扫一眼当前轮后**直接看双图趋势**
（`#mthistspark` 耗时折线 / `#mtdeltabar` 补入柱状）要手动滚 / 展开折叠区（R163 `#mtmetfold` 折叠时双图区隐，点 `#mtmetfold`
才展）。`#mtlivebadge` 加 **`onclick`**（`mtLiveBadgeJump`：`#mtmetfoldwrap` 折叠时展开 + `_mtMetFold=0` + `#mtmetfold` 钮复位
`▾ 折趋势` + `#mthistspark` `scrollIntoView` 滚到双图区）——跑中扫一眼当前轮后点击徽标直接跳双图趋势，与 R163 折叠开关同
「趋势条可管」语言（徽标 → 双图跳转，免手点折叠钮再滚）。

**E2E**：`折叠态（#mtmetfoldwrap display:none）→ 点 #mtlivebadge → 展开（block）+ _mtMetFold=0 + 钮「▾ 折趋势」（双图区可访问）`
（绿，`#mthistspark` scrollIntoView headless 不验滚动只验双图区展开）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、
console 0、截图 r171_jump.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 638→640`，断点 `_整理后分类\华语经典\五月天\听不到.mp3`。

**坑**：① `mtLiveBadgeJump`（`#mtlivebadge` onclick，载入 IIFE 绑 `addEventListener('click')`，不 `onclick=` 内联——徽标
`textContent` 每轮 `mtLiveBadge` 刷新，内联 `onclick` 会被 `el.textContent=` 覆盖丢事件，`addEventListener` 挂元素不随
`textContent` 变）② 跳双图：`#mtmetfoldwrap` 折叠（`display:none`）→ `display='block'` + `localStorage._mtMetFold='0'` +
`#mtmetfold` 钮 `textContent='▾ 折趋势'`（展开复位折叠态，与 R163 `mtMetFold` 同状态同步——徽标跳双图顺带展开折叠区，双图区
可访问后 `scrollIntoView` 才滚得到，不展则滚到隐区无效）③ `#mthistspark` `scrollIntoView({behavior:'smooth', block:'center'})`
（滚到耗时折线双图区居中，`#mtdeltabar` 补入柱状在其下同滚进，双图一起看；`smooth` 平滑滚，跑中滚动不跳）④ **点击 = 跳转
非复制**（`#mtlivedetailcopy` 复制是 hover 浮层内钮，`#mtlivebadge` 本体点击是跳双图，两交互分工：本体点 = 跳双图趋势，hover
浮层内 `⧉` 钮 = 复制详情，不混）⑤ `scrollIntoView` 在 `#mthistspark` 元素（耗时折线，双图区上），`#mtdeltabar` 补入柱状在
`#mthistspark` 后同 `#mtmetfoldwrap` 包内，滚 `#mthistspark` 双图区一起进视口 ⑥ 已展开时点（`#mtmetfoldwrap` 非 `none`）只
`scrollIntoView` 不重展（`display!=='none'` 跳过展开，只滚——不反复写 `_mtMetFold`，已展开态保持）⑦ 验收**函数级**（折叠态
`#mtmetfoldwrap` `display:none` + 点 `#mtlivebadge` 验展开 `block` + `_mtMetFold=0` + 钮复位，`scrollIntoView` headless 不验
实际滚动只验双图区展开可访问，不真跑 `mtRun` 免 tick 污染 `runs`）。

---

## 第186轮（前端 R172 · goal round149）：`#mtlivebadge` 点击跳双图区后自动定位最近一柱（`#mtdeltabar` 末柱高亮 + `#mtpairlbl` 配对「第 N 次·耗时 Xs·补入 +Y」，聚焦最新一轮双指标）

**连贯性（跳双图后聚焦最新轮免手 hover）**：R171 点 `#mtlivebadge` 跳双图区（`scrollIntoView` 滚到 `#mthistspark`），但
**滚到双图区后没聚焦最新一轮**（双图 hover 联动要手动 hover 某柱才显 `#mtpairlbl` 配对，滚到双图区后自动高亮最近一柱 + 显
配对「第 N 次·耗时 Xs·补入 +Y」没做）。`mtLiveBadgeJump` 跳双图后（`scrollIntoView` `smooth` 滚完）自动：`#mtdeltabar`
**末柱**（`idx=n-1`）点亮 `#mtdelthover`（绿点）+ `#mtpairlbl` 显配对「第 N 次·耗时 Xs·补入 +Y」（读 `_mtRunHist` 末位耗时
+ `_mtRunDelta` 末位补入量，与 R155 hover 联动同「双指标配对」但跳双图后**自动聚焦最新轮**免手 hover）。

**E2E**：`写 _mtRunHist(5)+_mtRunDelta(5) → 点 #mtlivebadge 跳双图 → 400ms 后 #mtpairlbl 显「第 5 次 · 耗时 0.6s · 补入 +3」
（末柱高亮 + 配对最新轮，_mtRunHist 末 0.6 / _mtRunDelta 末 3）+ #mtdelthover 点亮`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r172_focus.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 640→642`，断点 `_整理后分类\华语经典\周传雄\异世界.mp3`。

**坑**：① `mtLiveBadgeJump`（R171 跳双图）加 `setTimeout(400)` 滚完再聚焦：`scrollIntoView({behavior:'smooth'})` 平滑滚约
400ms，`setTimeout` 400ms 后聚焦（滚到双图区时末柱已高亮，`scrollIntoView` 滚势停时聚焦落定，不在滚中抖）② 聚焦逻辑（`setTimeout`
内）：读 `_mtRunHist`（`h`）+ `_mtRunDelta`（`d`），`n=max(h.length,d.length)`，`lastIdx=n-1`，`hv=h[lastIdx]`（末位耗时）/
`dv=d[d.length-1]`（末位补入），`#mtpairlbl` 文案 `'第 (lastIdx+1) 次 · 耗时 hv+s · 补入 +dv'`（`hv`/`dv` 缺显 `-`，`pair`
`display:inline-block`）③ 末柱高亮 `#mtdelthover`（绿点，`display:block`）：`top` 末柱顶（viewBox 100×22，`mx=max(d 各值,1)`，
`top=20-round(dv/mx*18)-1`，柱顶 y），`left=100%`（末柱 `frac=1` 最右），`#mtdelthover` 是 `#mtdeltabar` 内绝对定位绿点（R154
定义），聚焦最新直接放到末柱顶 ④ **`_mtRunDelta` 空但 `_mtRunHist` 有**（只补入没跑/清补入）：`dv=null`，`#mtpairlbl` 补入
显 `-`（耗时末位照显），`#mtdelthover` 不显（无补入柱状可点亮），降级不阻 ⑤ 与 R155 hover 联动**分工**（R155 手 hover 某柱
显该柱配对 / R172 跳双图后自动聚焦末柱显最新轮配对——R172 是「跳双图后免手 hover 看最新」，R155 仍是「手 hover 看任意一轮」，
自动聚焦最新 + 手 hover 任意轮并存，`#mtpairlbl`/`#mtdelthover` 同元素两触发源：跳双图自动末柱 / hover 手定位某柱，后触者
覆盖——跳双图后手 hover 某柱 R155 联动接管 `#mtpairlbl` 改该柱，`#mtdelthover` 改某柱顶，不冲突）⑥ 验收**函数级**（写
`_mtRunHist`/`_mtRunDelta` 5 条 + 点 `#mtlivebadge` 验 400ms 后 `#mtpairlbl` 末位配对 + `#mtdelthover` 点亮，不真跑 `mtRun`
免 tick 污染 `runs`；`setTimeout` 400ms 验证 `await 600ms` 后读，不真滚 `scrollIntoView` 只验双图区展开 + 聚焦落定）。

---

## 第187轮（前端 R173 · goal round150）：`#mtlivebadge` 跑中每轮 tick 双图区在视口内自动跟最新轮（`#mtdelthover`/`#mtpairlbl` 自动跟到本轮，跑中滚动看双图趋势时最新柱逐轮推进）

**连贯性（跑中滚动双图趋势时最新柱逐轮推进免手 hover）**：R172 跳双图**时**（点 `#mtlivebadge`）聚焦末柱，但**跑中每轮
tick 刷新**时若双图区在视口内，`#mtdelthover`/`#mtpairlbl` 没跟到本轮（跑中滚动看双图趋势时最新柱逐轮推进没自动跳，
要手 hover 看当前轮）。`mtRun` 每轮 tick 后（`mtLiveBadge` 调用区后）：双图区在视口内（`#mtdeltabar` `style.display` 非
none + `getBoundingClientRect` 与视口交 `bottom>0 && top<innerHeight`）时自动调 `mtFocusLatest()`（`#mtdelthover` 改本轮
柱顶 + `#mtpairlbl` 改本轮配对）——跑中滚动看双图趋势时最新柱逐轮推进到当前轮，免手 hover；双图区不在视口内（折叠 / 滚出）
不跟（不刷 `#mtpairlbl`，省无效刷）。

**E2E**：`双图区在视口内（#mtdeltabar 显 + getBoundingClientRect 与视口交）+ mock 每轮 tick（_mtRunHist/_mtRunDelta 各
6 条末 _mtRunDelta=9/_mtRunHist=0.4）→ mtFocusLatest 跟到本轮 #mtpairlbl「第 6 次 · 耗时 0.4s · 补入 +9」（末柱逐轮推进到
当前轮，免手 hover）`（绿，`inViewport` + 配对 6/0.4/+9）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r173_vport.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 642→644`，断点 `_整理后分类\华语经典\周杰伦\一口气全念对.mp3`。

**坑**：① `mtFocusLatest()`（R172 聚焦逻辑抽成函数，`#mtdeltabar` 末柱 `#mtdelthover` 点亮 + `#mtpairlbl` 配对，读
`_mtRunHist` 末位耗时 + `_mtRunDelta` 末位补入量）：R172 `mtLiveBadgeJump` 的 `setTimeout` 聚焦 + R173 `mtRun` 每轮 tick 都调，
**两处复用同一聚焦函数**（跳双图 `setTimeout` 400ms 滚势停调 / 每轮 tick 视口内直接调，不重复实现）② `mtRun` 每轮 tick 后
（`mtLiveBadge` 调用区后）：`$('#mtdeltabar').style.display!=='none'`（双图区未折叠）+ `getBoundingClientRect().bottom>0 &&
top<window.innerHeight`（双图区与视口交，在视口内）时 `mtFocusLatest()`——**双图区在视口内才跟**（折叠 / 滚出视口不刷
`#mtpairlbl`，省无效刷；`#mtdeltabar` `display:none`（无补入量 / R163 折叠）时 `getBoundingClientRect` 返 0，`display!=='none'`
先判挡住）③ 与 R172 跳双图聚焦**分工**（R172 是「点 `#mtlivebadge` 跳双图后聚焦末柱」一次性，R173 是「跑中每轮 tick 视口内
自动跟最新轮」持续——R173 跑中滚动双图区时逐轮推进，R172 跳双图落定那一刻聚焦，两触发源共存：跑中滚动 R173 逐轮 / 点跳
R172 落定，`mtFocusLatest` 同函数，后触者覆盖 `#mtpairlbl`/`#mtdelthover`）④ `mtFocusLatest` 末柱定位（`lastIdx=n-1`，
`#mtdelthover` `top` 末柱顶 / `left=100%` 最右），**`#mtpairlbl` 配对文案按末位**（`_mtRunHist` 末耗时 / `_mtRunDelta` 末
补入，`n=max(两数组)` 时末位对齐——逐轮推进时 `n` 增末位就是当前轮），两数组不同长时 `hv=h[lastIdx]` 缺 `undefined` 显 `-` /
`dv=d[d.length-1]` 缺 `null` 显 `-`（降级不阻）⑤ `try/catch`（`getBoundingClientRect` / `mtFocusLatest` 未定义不阻循环，
视口判定 / 聚焦失败 tick 照跑）⑥ 验收**函数级**（双图区 `#mtdeltabar` 显 + `getBoundingClientRect` 与视口交 + mock 每轮 tick
推 `_mtRunHist`/`_mtRunDelta` 验 `mtFocusLatest` 跟到末柱 6，不真跑 `mtRun` 免 tick 污染 `runs`；`inViewport` 验双图区在视口内
判定 + 配对末位，不在视口内时 `style.display==='none'` 挡不跟）。

---

## 第188轮（前端 R174 · goal round151）：`#mtmetsum` 双指标汇总标签点击跳双图区（`#mtmetsum` 点击 → 展开 `#mtmetfoldwrap`（若折叠）+ `scrollIntoView` 双图区 + `mtFocusLatest` 聚焦最新轮，汇总入口跳双图）

**连贯性（非跑中看汇总后跳双图看趋势免手动滚）**：R171 `#mtlivebadge` 点击跳双图区是**跑中入口**（跑中每轮 `#mtlivebadge`
显，点跳双图），但**常驻汇总 `#mtmetsum`**（R158「近 N 次 · 耗时均值 Xs · 补入均值 +Y/次 · 合计 +Z」，跑中 / 非跑中都显）**没有
跳转入口**（要看双图趋势 / 聚焦最新轮得手动滚或等跑中点 `#mtlivebadge`，非跑中看汇总后跳双图没入口）。`#mtmetsum` 加
**`onclick`**（`mtMetSumJump`：展开 `#mtmetfoldwrap`（若折叠）+ `scrollIntoView` `#mthistspark` + `setTimeout` 400ms `mtFocusLatest`
聚焦最新轮）——**汇总入口跳双图**（非跑中也能从 `#mtmetsum` 跳双图看趋势 + 聚焦最新轮，`cursor:pointer` + `title` 提示点我），
与 R171 徽标跳双图**同「趋势条可管」但汇总入口**（跑中 `#mtlivebadge` 跳 / 非跑中 `#mtmetsum` 跳，两入口共用 `mtFocusLatest` +
展开 + `scrollIntoView`）。

**E2E**：`写 _mtRunHist(4)+_mtRunDelta(4 末=0) → #mtmetsum 显 + 折叠双图区 → 点 #mtmetsum → 展开（block）+ mtFocusLatest 聚焦
最新轮 #mtpairlbl「第 4 次 · 耗时 1.5s · 补入 +0」（_mtRunHist 末 1.5 / _mtRunDelta 末 0）`（绿）；端点 **30/0**、JS undefined
NONE、CSS 320/320、node 0、console 0、截图 r174_sumjump.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 644→646`，断点 `_整理后分类\华语经典\周杰伦\回到过去.mp3`。

**坑**：① `#mtmetsum` 是 `#mtdeltabar` 内 R158 span（`display:none` 默认，`mtMetSumDraw` 有数据才显），`onclick` 加在
`mtMetSumJump` 定义后 IIFE（`ms.addEventListener('click')`，不内联 `onclick=`——`#mtmetsum` `textContent` 每跑 `mtMetSumDraw`
刷新，内联会被覆盖丢事件，`addEventListener` 挂元素不随 `textContent` 变，与 R171 `#mtlivebadge` 同 `addEventListener` 纪律）②
`mtMetSumJump`（`#mtmetsum` onclick）：复用 R171 展开逻辑（`#mtmetfoldwrap` 折叠 `display:none` → `display='block'` +
`_mtMetFold='0'` + `#mtmetfold` 钮 `▾ 折趋势`）+ `#mthistspark` `scrollIntoView({behavior:'smooth', block:'center'})` +
`setTimeout(400) mtFocusLatest()`（滚势停后聚焦最新轮，与 R172 `mtLiveBadgeJump` 同 `setTimeout` 400ms + `mtFocusLatest`，两处
跳双图入口共用聚焦）③ **汇总入口 vs 徽标入口**（R171 `#mtlivebadge` 跑中入口 / R174 `#mtmetsum` 非跑中也入口——`#mtmetsum`
常驻显（`mtMetSumDraw` 有数据就显，跑中 / 非跑中），`#mtlivebadge` 只跑中每轮 tick 显，两入口分工：跑中扫当前轮看双图点
`#mtlivebadge`，非跑中看汇总回顾跳双图点 `#mtmetsum`，都展开 + `scrollIntoView` + `mtFocusLatest` 聚焦最新轮）④ `cursor:pointer`
+ `title='点我看双图趋势 + 聚焦最新轮'`（`#mtmetsum` 是 span，`cursor:pointer` 暗示可点，`title` 悬停提示，常驻汇总标签可点
不突兀——`#mtmetsum` 在 `#mtdeltabar` 内靠右，点它跳双图区，与双图区一排小钮同「点看」语言）⑤ `mtFocusLatest` 聚焦最新轮（末
柱 `#mtdelthover` + `#mtpairlbl` 配对），`_mtRunDelta` 末 `0`（空补）时 `dv=0` `#mtpairlbl` 补入显 `+0`（0 也是有效值，非空，
`dv!==null` 判——`_mtRunDelta` 有 0 值条目时末位 0 照显 `+0`，不显 `-`）⑥ 验收**函数级**（写 `_mtRunHist`/`_mtRunDelta` 4 条
末 `_mtRunDelta=0` + 折叠双图区 + 点 `#mtmetsum` 验展开 `block` + 400ms 后 `#mtpairlbl` 末位配对，不真跑 `mtRun` 免 tick 污染
`runs`；`scrollIntoView` headless 不验实际滚动只验双图区展开 + 聚焦落定，`#mtmetsum` `msOn` 验 `mtMetSumDraw` 有数据显）。

---

## 第189轮（前端 R175 · goal round152）：`#mtrun` 跑维护完成 toast 补「点双图区汇总（`#mtmetsum`）跳双图看趋势 + 聚焦最新轮」引导（跑完顺带看双图趋势免找入口）

**完善性（跑完引导看双图趋势）**：R174 `#mtmetsum` 点击跳双图（非跑中入口），`#mtrun` 跑完 toast（R143「跑完 N 轮 · <本轮
结果> · 复盘」+ 全库「跑到全库完成 · 共 i 轮 · 已挂自动刷看 9 卡」）**只报结果不引导看双图趋势**（跑完想看双图趋势 / 聚焦
最新轮要自己找 `#mtmetsum` 点，跑完 toast 后引导没做）。`#mtrun` 跑完 toast（非全库 3012 区 `_tm`）末接**「· 点双图区汇总
（#mtmetsum）跳双图看趋势 + 聚焦最新轮」** + 全库完成 toast（2997 区）接「· 点双图区汇总跳双图看趋势」——跑完 toast 后引导
用户看双图趋势（免找入口，`#mtmetsum` 点击跳双图链路：toast 提示 → 点 `#mtmetsum` → 展开 + `scrollIntoView` + `mtFocusLatest`
聚焦最新轮），跑维护顺带看双图趋势（耗时折线 + 补入柱状 + 最新轮配对）。

**E2E**：`源码 grep 跑完 toast 含「点双图区汇总」（引导跳双图）+ 全库 toast 引导 + mtMetSumJump（R174 跳双图函数）在 +
#mtmetsum 元素在（链路通：跑完 toast 引导 → 用户点 #mtmetsum 跳双图）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、
node 0、console 0、截图 r175_toastjump.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 646→648`，断点 `_整理后分类\华语经典\周杰伦\最后的战役.mp3`。

**坑**：① 非全库跑完 toast（3012 区，`!FULL_DONE && doneMsg`）：`_tm='跑完 N 轮 · '+doneMsg+' · 点双图区汇总（#mtmetsum）跳双图看
趋势 + 聚焦最新轮'`（`_tm` 末接引导，`doneMsg` 本轮结果照带，toast 文案长不截——`#__toast__` 单行 `white-space` 自然换行，
右上角停留 6s 不遮挡卡片，跑完结果 + 引导一行看完）② 全库完成 toast（2997 区，`FULL && r.done`）：`_toast('跑到全库完成 · 共 i
轮 · 已挂自动刷看 9 卡 · 点双图区汇总跳双图看趋势', 'ok')`（全库 toast 末接跳双图引导，全库跑完看双图趋势——全库跑完双图区
最新一轮补入量 / 耗时趋势最有用）③ **引导不替用户点**（toast 只提示「点双图区汇总」，不自动跳——跑完 toast 自动跳双图会打断
跑完结果回显，用户看完 toast 自己点 `#mtmetsum` 跳，`cursor:pointer` 已暗示可点（R174），toast 文案补引导免找入口，两不
冲突）④ 与 R171 `#mtlivebadge` 跳双图（跑中入口）/ R174 `#mtmetsum` 跳双图（非跑中入口）**分工**（R175 是**跑完 toast 引导**
——跑完提示用户「点双图区汇总跳双图」，入口仍 R174 `#mtmetsum`，R175 只补 toast 文案引导不新入口，跑完 → 看双图趋势连贯
不找入口）⑤ 验收**源码 grep**（不真跑 `mtRun` 免 tick 污染 `runs`——跑完 toast 是 `mtRun` 循环后 `_toast` 调用，真跑要全库
`r.done` 才到，headless 验 `outerHTML` 含「点双图区汇总」引导文案 + `mtMetSumJump` 函数在 + `#mtmetsum` 元素在，链路通即
证；全库 toast 引导同 grep 区（`_toast('跑到全库完成…点双图区汇总跳双图看趋势')` 源码在））。

---

## 第190轮（前端 R176 · goal round153）：`#mtlivebadge` 右键快捷取消跑维护（`contextmenu` → `_mtAborted=true` + `#mtrun` 取消红态同步 + toast，跑中看徽标时右键即取消免手点 `#mtrun`）

**流畅性（跑中看徽标时右键取消免移开）**：R171 `#mtlivebadge` 点击 = 跳双图（`onclick`），跑中看徽标双指标时**想取消跑维护要移开点
`#mtrun` 取消红态**（`#mtrun` 跑中变「取消」红 `--bad`，要移开视线点），徽标右键快捷取消没入口。`#mtlivebadge` 加**`contextmenu`**
（`preventDefault` 不弹系统菜单 + `_mtAborted=true` + `#mtrun` 取消红态同步（`textContent=取消` + `--bad`）+ toast「已发取消 ·
跑到下一轮生效（已跑的轮不回滚）」）——跑中看徽标双指标时**右键即取消**（不弹系统菜单，`_mtAborted` 设后跑中下一轮 abort 检查
跳出循环），与 R140 取消「已跑的轮不回滚」同直觉，免手点 `#mtrun`。

**E2E**：`右键 #mtlivebadge（contextmenu）→ preventDefault + #mtrun 取消红态（textContent=取消 + --bad rgb(196,56,31)）+
toast「已发取消 · 跑到下一轮生效（已跑的轮不回滚）」+ _mtAborted=true（跑中下一轮 abort 生效）`（绿）；端点 **30/0**、JS undefined
NONE、CSS 320/320、node 0、console 0、截图 r176_ctxcancel.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 648→650`，断点 `_整理后分类\华语经典\周杰伦\轨迹.mp3`。

**坑**：① `#mtlivebadge` `contextmenu`（`addEventListener('contextmenu')`，R171 `click` 绑的 IIFE 后）：`ev.preventDefault()`
（不弹系统右键菜单，徽标右键只做取消）② `_mtAborted=true`（`typeof _mtAborted!=='undefined'` 判，`mtRun` 循环顶 abort 检查
跳出，跑中下一轮生效——`_mtAborted` 是 `mtRun` 函数作用域 `let`，IIFE 挂 `contextmenu` 访问要 `typeof` 判不直接读（作用域外
读 `let` 块级变量会 `ReferenceError`，`typeof` 安全））③ `#mtrun` 取消红态同步（`textContent='取消'` + `background/borderColor`
`var(--bad)` + `color=#fff`，跑中 `#mtrun` 本来红「取消」态，右键取消同红态视觉同步——看 `#mtrun` 红知道已发取消，非跑中右键
也置红态提示「取消已发」，`#mtrun` 跑中本来红，非跑中点取消无效但视觉同步提示）④ toast「已发取消 · 跑到下一轮生效（已跑的轮
不回滚）」（`_mtAborted` 设后跑中下一轮 `mtRun` 循环顶检查跳出，已跑轮不回滚——与 R140 同「不回滚」直觉，toast 文案点明已跑的
轮保留）⑤ `j.title` 追加「· 右键取消跑维护」（`#mtlivebadge` hover 提示右键可取消，`title` 已有 `cursor:help` 提示（R167），追加
右键取消提示，hover 看提示知道右键能取消）⑥ `contextmenu` 不 `stopPropagation`（`#mtlivebadge` 在维护区，右键取消是维护区局部
交互，不挡外层 `contextmenu`——维护区没外层右键交互，`preventDefault` 只挡系统菜单）⑦ 验收**函数级**（`#mtlivebadge` `dispatchEvent`
`contextmenu` 验 `#mtrun` 红态 + toast，`_mtAborted` 作用域外读不验——`_mtAborted` 是 `mtRun` 块级 `let`，IIFE 外读不到，验
`#mtrun` 视觉同步 + toast 出口证明取消已发，`_mtAborted` 真取消跑中下一轮生效是 `mtRun` 内部行为不真跑 `mtRun` 免 tick 污染
`runs`）。

---

## 第191轮（前端 R177 · goal round154）：`#mtmetfold` 折叠钮双击快捷（展开 `#mtmetfoldwrap`（若折叠）+ 双图区在视口内 `mtFocusLatest` 聚焦最新轮，快速折叠态 + 聚焦连击）

**流畅性（展开 + 聚焦一次到位免两连击）**：R163 `#mtmetfold` 单击折叠 / 展开双图区（`mtMetFold`），但**展开 + 聚焦最新轮要
连点两次**（单击展开 → 再点 `#mtmetsum`/`#mtlivebadge` 跳双图聚焦，两连击）。`#mtmetfold` 加**`dblclick`**（`mtMetFoldDbl`：
`#mtmetfoldwrap` 折叠时展开 + `_mtMetFold=0` + `#mtmetfold` 钮复位 `▾ 折趋势`，双图区在视口内（`getBoundingClientRect` 与视口交
`bottom>0 && top<innerHeight`）时 `mtFocusLatest` 聚焦最新轮）——双击 = 展开 + 聚焦连击一次到位（免展开后再点跳双图），与 R171
单点跳双图**同「趋势条可管」但连击快捷**（双击比单点更省一次点，快速看双图趋势 + 最新轮配对）。

**E2E**：`折叠态（#mtmetfoldwrap display:none）+ 写 _mtRunHist(4)+_mtRunDelta(4 末=0) → #mtmetfold 双击 → 展开（block）+
_mtMetFold=0 + mtFocusLatest 聚焦最新轮 #mtpairlbl「第 4 次 · 耗时 1.5s · 补入 +0」（双图区 getBoundingClientRect 与视口交时）`
（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r177_dbfold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 650→652`，断点 `_整理后分类\华语经典\张学友\醒着做梦.mp3`。

**坑**：① `mtMetFoldDbl`（`#mtmetfold` `dblclick`，载入 IIFE 绑 `addEventListener('dblclick')`，不内联 `ondblclick=`——`#mtmetfold`
`textContent` 每 `mtMetFold` 刷新，内联会被覆盖丢事件，`addEventListener` 挂元素不随 `textContent` 变，与 R171 `#mtlivebadge`
`click` / R174 `#mtmetsum` `click` 同 `addEventListener` 纪律）② `dblclick` 展开逻辑复用 R171/R174 展开（`#mtmetfoldwrap`
`display:none` → `display='block'` + `_mtMetFold='0'` + `#mtmetfold` 钮 `▾ 折趋势`，三处展开同写法：R163 `mtMetFold` 单击 / R171
`mtLiveBadgeJump` / R174 `mtMetSumJump` / R177 `mtMetFoldDbl`）③ **视口内才聚焦**（`#mtmetfoldwrap` `getBoundingClientRect().bottom>0
&& top<window.innerHeight` 与视口交才 `mtFocusLatest`——折叠刚展开双图区可能在视口外（双图区在维护区下方，`#mtmsg` 顶栏折叠钮
展开后双图区滚出视口，聚焦 `#mtpairlbl` 视口外无意义，`getBoundingClientRect` 判定在视口交才聚焦，不在不聚，省无效刷）④ 双击
**不触单击**（`dblclick` 在两次 `click` 后触发，`btn.onclick=mtMetFold` 单击也触两次——双击 = 两次 `mtMetFold`（折叠→展开→折叠）
+ 一次 `mtMetFoldDbl`，`mtMetFold` 折叠态判断 `folded=display!=='none'`，双击时 `#mtmetfoldwrap` 初 `none`：第 1 单击 `mtMetFold`
折→展（`display=block`），第 2 单击展→折（`display=none`），`mtMetFoldDbl` 再展（`display=block`）+ 聚焦——净效果展开 + 聚焦，
但多两次 `mtMetFold` 闪烁（`block`→`none`→`block`），`_mtMetFold` 最终 `0`（`mtMetFoldDbl` 写），可接受；若嫌闪烁可 `dblclick`
`preventDefault` 但 `click` 已先发——双击净展开 + 聚焦，闪烁 2 次可接受不优化）⑤ 与 R171 单点跳双图（`#mtlivebadge` 跑中入口
+ `scrollIntoView`）**分工**（R177 `#mtmetfold` 双击 = 折叠钮连击快捷展开 + 聚焦，不 `scrollIntoView`（`#mtmetfold` 在顶栏
`#mtmsg` 后，双图区紧接其下，展开后本就近，不滚——区别于 R171/R174 跳双图 `scrollIntoView` 滚到 `#mthistspark`，`#mtmetfold`
双图区就在折叠钮下无需滚）⑥ `mtFocusLatest` 复用（R172/R173/R174 聚焦函数，R177 双击展开后调，末柱 `#mtdelthover` + `#mtpairlbl`
配对，同函数不重复实现）⑦ 验收**函数级**（折叠态 `#mtmetfoldwrap` `display:none` + 写 `_mtRunHist`/`_mtRunDelta` 4 条末 `_mtRunDelta=0`
+ `#mtmetfold` `dispatchEvent` `dblclick` 验展开 `block` + `_mtMetFold=0` + `#mtpairlbl` 末位配对「第 4 次·耗时 1.5s·补入 +0」，不真跑
`mtRun` 免 tick 污染 `runs`；`dblclick` 触发前两次 `click` 闪烁验净展开 + 聚焦，不验闪烁过程）。

---

## 第192轮（前端 R178 · goal round155）：`#mtlivebadge` 跑中双指标实时徽标补键盘 `Esc` 快捷取消（`document` 监听 `keydown`，维护 tab 激活时按 `Esc` = `_mtAborted=true` 取消跑维护 + `#mtrun` 取消红态同步 + toast，跑中看徽标 / 看双图时按 `Esc` 即取消免手点 / 免右键）

**流畅性（跑中看双图趋势时键盘流取消免移开手）**：R176 `#mtlivebadge` 右键取消（`contextmenu`），跑中看徽标 / 看双图时想
取消要移开手点 `#mtrun` / 右键徽标，**键盘路径没做**（跑中看双图趋势时键盘流免移开手，`Esc` 即取消）。`document` 监听
**`keydown`**（`e.key==='Escape'` + 维护 tab 激活 `.tab[data-p="d"]` on 判）→ `_mtAborted=true` + `#mtrun` 取消红态同步
（`textContent=取消` + `--bad`）+ toast「已取消 · 跑到下一轮生效（Esc · 已跑的轮不回滚）」——跑中看徽标双指标 / 看双图趋势
时**按 `Esc` 即取消**（键盘流免移开手，与 R176 右键取消 / R140 取消「已跑的轮不回滚」同直觉，取消路径三选：手点 `#mtrun` /
右键徽标 / 键盘 `Esc`）。

**E2E**：`维护 tab 激活（.tab[data-p="d"] on）→ document 按 Esc（keydown key=Escape）→ #mtrun 取消红态（textContent=取消 +
--bad rgb(196,56,31)）+ toast「已取消 · 跑到下一轮生效（Esc · 已跑的轮不回滚）」+ _mtAborted=true（跑中下一轮 abort）`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r178_esc.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 652→654`，断点 `_整理后分类\华语经典\林俊杰\一跃而下.mp3`。

**坑**：① `document` 监听 `keydown`（`e.key==='Escape'`），**维护 tab 激活判**（`.tab[data-p="d"]` `classList` 含 `on`，`tabs.forEach`
`data-p=d` 加 `on` 其他去 `on` 模拟激活态，`activeTab=document.querySelector('.tab.on[data-p="d"]')` 非 null 才取消——其他 tab
按 `Esc` 不触，不挡全局 `Esc`（全局 `Esc` 可能关弹层 / 退出全屏，维护 tab 才取消跑维护，`activeTab` 判挡非维护 tab）②
`_mtAborted=true`（`typeof _mtAborted!=='undefined'` 判，`mtRun` 循环顶 abort 检查跳出，跑中下一轮生效——`_mtAborted` 是 `mtRun`
函数作用域 `let`，`document` 监听 IIFE 作用域外访问要 `typeof` 判不直接读，`typeof` 安全，同 R176 右键 `_mtAborted` 纪律）③
`#mtrun` 取消红态同步（`textContent='取消'` + `background/borderColor` `var(--bad)` + `color=#fff`，跑中 `#mtrun` 本来红「取消」
态，`Esc` 取消同红态视觉同步，看 `#mtrun` 红知道已发取消）④ toast「已取消 · 跑到下一轮生效（Esc · 已跑的轮不回滚）」（点明
`Esc` 触发 + 已跑轮保留，与 R176 右键 toast 同「不回滚」直觉，`Esc` 路径区分右键）⑤ **`Esc` 不 `preventDefault`**（`Esc` 无
默认行为要挡的——浏览器 `Esc` 默认退出全屏 / 关弹层，维护 tab `Esc` 取消跑维护是叠加取消不挡全屏 / 弹层 `Esc`，`keydown`
监听 `keydown` 不 `preventDefault`，全屏 / 弹层在维护 tab `Esc` 也同时触发各自默认，两不冲突；若挡 `Esc` `preventDefault` 会
误伤全屏退出，不挡）⑥ 与 R176 右键取消**分工**（R176 `#mtlivebadge` `contextmenu` 右键 / R178 `document` `keydown` `Esc` 键盘，
取消路径三选：手点 `#mtrun` / 右键徽标 / 键盘 `Esc`，三入口 `_mtAborted=true` 同效果，`Esc` 是键盘流免移开手——跑中看双图
趋势手放键盘按 `Esc` 即取消，最顺）⑦ 验收**函数级**（维护 tab `on` 态 `document` `dispatchEvent` `keydown` `key=Escape` 验
`#mtrun` 红态 + toast「已取消（Esc）」，`_mtAborted` 作用域外读不验——`_mtAborted` 是 `mtRun` 块级 `let`，`document` 监听 IIFE
外读不到，验 `#mtrun` 视觉同步 + toast 出口证明取消已发，`_mtAborted` 真取消跑中下一轮生效是 `mtRun` 内部行为不真跑 `mtRun`
免 tick 污染 `runs`）。

---

## 第193轮（前端 R179 · goal round156）：`#mtlivebadge` 跑中双指标实时徽标补键盘 `Enter` 快捷跳双图（`document` 监听 `keydown`，维护 tab 激活 + 焦点非输入框时按 `Enter` = `mtLiveBadgeJump` 跳双图 + `mtFocusLatest` 聚焦最新轮，同 R171 点击跳双图但键盘路径）

**流畅性（跑中看双图趋势时手放键盘按 `Enter` 即跳双图免移开手点）**：R171 `#mtlivebadge` 点击跳双图（手点），R178 `Esc` 键盘
取消，**键盘 `Enter` 跳双图没做**（跑中看徽标 / 看双图趋势时手放键盘按 `Enter` 即跳双图 + 聚焦最新轮，免移开手点）。`document`
监听 `keydown`（R178 `Esc` 取消同 IIFE，补 `e.key==='Enter'` 分支）：维护 tab 激活 `.tab[data-p="d"]` on + **焦点非输入框**
（`document.activeElement` `tagName` 非 `input`/`textarea`/`contentEditable`）→ `mtLiveBadgeJump`（跳双图 + `mtFocusLatest` 聚焦
最新轮）+ toast「已跳双图区 · 聚焦最新轮（Enter）」——跑中看徽标双指标 / 看双图趋势时**手放键盘按 `Enter` 即跳双图**，与 R178
`Esc` 取消**同键盘路径**（`Enter` 跳双图 / `Esc` 取消，键盘流两操作，跑中看双图趋势手放键盘流最顺），与 R171 点击跳双图同
「趋势条可管」但键盘路径。

**E2E**：`维护 tab 激活 + 焦点非输入框 → document 按 Enter（keydown key=Enter）→ mtLiveBadgeJump 跳双图（#mtmetfoldwrap 展开
block + _mtMetFold=0）+ mtFocusLatest 聚焦最新轮 + toast「已跳双图区 · 聚焦最新轮（Enter）」`（绿）；端点 **30/0**、JS undefined
NONE、CSS 320/320、node 0、console 0、截图 r179_enter.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 654→656`，断点 `_整理后分类\华语经典\林俊杰\无拘.mp3`。

**坑**：① `document` `keydown`（R178 `Esc` 取消同 IIFE 补 `Enter` 分支，两键盘操作同一监听不重复挂）：`e.key==='Enter'` →
`e.preventDefault()`（挡全局 `Enter`——表单提交等，维护区 `Enter` 只做跳双图）+ `mtLiveBadgeJump()`（R171 跳双图函数，展开
`#mtmetfoldwrap`（若折叠）+ `scrollIntoView` 双图区 + `mtFocusLatest` 聚焦最新轮，复用 R171/R172/R177 跳双图聚焦链）② **焦点非
输入框判**（`document.activeElement.tagName` 非 `input`/`textarea`/`contentEditable` 才触——用户焦点在维护区输入框（如 `#mtrf`
筛选 / 日志过滤）按 `Enter` 是提交 / 确认输入框，不跳双图，`activeElement` 判挡输入框焦点，键盘快捷只维护区空焦点触）③
**维护 tab 激活判**（R178 同 `.tab.on[data-p="d"]`，其他 tab 按 `Enter` 不触，不挡全局 `Enter` 表单提交）④ `Enter` `preventDefault`
（挡全局 `Enter` 默认——维护区 `Enter` 只做跳双图，挡表单误触；`Esc` 不 `preventDefault`（R178，不挡全屏 / 弹层 `Esc`），两键
`preventDefault` 策略不同：`Enter` 挡（维护区 `Enter` 专用跳双图），`Esc` 不挡（全屏 / 弹层 `Esc` 默认保留，取消叠加）⑤ toast
「已跳双图区 · 聚焦最新轮（Enter）」（点明 `Enter` 触发 + 跳双图 + 聚焦最新轮，与 R178 `Esc` toast 同键盘流提示，`Enter` 路径
区分 `Esc`）⑥ **键盘流两操作**（`Enter` 跳双图 / `Esc` 取消，跑中看双图趋势手放键盘：`Enter` 跳双图区 + 聚焦最新轮看趋势，
`Esc` 取消跑维护，两键分工，与 R176 右键取消 / R171 点击跳双图 / R177 折叠钮双击 / R174 汇总点击跳双图全路径，键盘流最省
手移开）⑦ 验收**函数级**（维护 tab `on` + 焦点 `document.body.focus()` 非输入框 + `document` `dispatchEvent` `keydown`
`key=Enter` 验 `#mtmetfoldwrap` 展开 `block` + `_mtMetFold=0` + toast「已跳双图区（Enter）」，不真跑 `mtRun` 免 tick 污染
`runs`；`Enter` `preventDefault` 验挡全局，`activeElement` 输入框焦点时不触验收同判 `tag` 挡）。

---

## 第194轮（前端 R180 · goal round157）：`#mtrun` 跑维护中补键盘 `Space` 快捷暂停 / 续跑（`document` 监听 `keydown`，维护 tab 激活 + 焦点非输入框时按 `Space` = `window._mtPaused` 暂停 / 续跑跑维护循环，`#mtrun` 黄 `--warn` 态「暂停中 · 按 Space 续跑」，跑中全库挂起不等跑完 / 不取消）

**流畅性（跑中全库挂起免取消 / 免等跑完）**：R178 `Esc` 取消 / R179 `Enter` 跳双图，**跑中想挂起（不取消 / 不跳双图，全库跑到一半挂起不等跑完 / 不取消回滚断点）没入口**（取消 `Esc` 回滚到断点，挂起是循环暂停 `setTimeout` 挂起不跑 tick，再按 `Space` 续跑）。`document` 监听 `keydown`（R178/R179 同 IIFE，补 `e.key===' '` 分支）：维护 tab 激活 + 焦点非输入框 + `window._mtRunning=true`（跑维护中）→ `window._mtPaused=true`（暂停：`#mtrun` 黄 `--warn`「暂停中 · 按 Space 续跑」+ `mtRun` 循环顶 `window._mtPaused` 检查挂起 `await setTimeout` 轮询不跑 tick）/ 再按 `Space` → `window._mtPaused=false`（续跑：循环顶轮询跳出，`#mtrun` 回「取消」红态）——跑中看徽标 / 看双图趋势时**手放键盘按 `Space` 挂起 / 续跑**，与 R178 `Esc` 取消 / R179 `Enter` 跳双图**同键盘路径**（`Space` 暂停 / `Enter` 跳双图 / `Esc` 取消，键盘流三操作，跑中全库挂起不等跑完 / 不取消回滚）。

**E2E**：`window._mtRunning=true 模拟跑维护中 → 按 Space → window._mtPaused=true 暂停（#mtrun「暂停中 · 按 Space 续跑」黄 --warn 态 + toast「已暂停 · 按 Space 续跑（已跑的轮不回滚）」）；再按 Space → window._mtPaused=false 续跑（#mtrun 回「取消」红态 + toast「已续跑 · 维护继续」）；window._mtRunning=false 按 Space → toast「Space 暂停需跑维护中（先点「跑一轮」）」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r180_space.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 656→658`，断点 `_整理后分类\华语经典\梁静茹\属于.mp3`。

**坑**：① `document` `keydown`（R178/R179 同 IIFE 补 `Space` 分支，三键盘操作同一监听不重复挂）：`e.key===' '` → `e.preventDefault()`（挡全局 `Space`——滚动等，维护区 `Space` 只做暂停 / 续跑）② **`window._mtRunning` 跑维护中判**（`#mtrun` 点「跑一轮」`mtRun` 内 `_mtRunning=true; window._mtRunning=true` 置，跑完 / 取消 / 出错置 `false; window._mtRunning=false`，挂 `window` 全局 `document` 监听可访问；块级 `let` 挂 `window` 同步初值，`mtRun` 内改 `window._mtRunning` 才生效——`document` 监听 IIFE 作用域外读块级 `let` 是 `undefined`，`window._mtRunning` 全局可读写）③ **`window._mtPaused` 暂停态挂全局**（`mtRun` 内 `let _mtPaused` 声明 + `window._mtPaused=_mtPaused` 同步初值，`Space` 写 `window._mtPaused=true/false`，循环顶 `if(window._mtPaused)` 检查挂起 + `while(window._mtPaused)` 轮询 `await setTimeout 300ms` 不跑 tick——`_mtPaused` 块级 `let` 作用域外读坑（`document` 监听 `IIFE` 外 `typeof _mtPaused` 是 `'undefined'`，`if(typeof _mtPaused!=='undefined')` 挡掉暂停 / 续跑逻辑不执行）→ 挂 `window` 全局，`Space` 分支 `window._mtPaused===false` 判暂停 / `else` 续跑，循环顶 `window._mtPaused` 读挂起，全走 `window`）④ `#mtrun` 黄 `--warn` 态（暂停 `textContent='暂停中 · 按 Space 续跑'` + `background/borderColor var(--warn)`，续跑 `_mtUnpausedBtn` 恢复跑中「取消」红态，`_mtUnpausedBtn` 读 `window._mtRunning` 判跑中 / 非跑中）⑤ **跑完 / 取消复位**（`mtRun` 跑完 / 取消区 `window._mtRunning=false; window._mtPaused=false`，跑维护结束暂停态复位，下次跑不继承暂停）⑥ 与 R178 `Esc` 取消 / R179 `Enter` 跳双图**分工**（`Space` 暂停 / 续跑挂起循环不取消不跳双图，跑中全库跑到一半挂起看别的再 `Space` 续跑，三键盘流 `Enter` 跳双图 / `Esc` 取消 / `Space` 暂停续跑，`Space` 挂起是「不等跑完不取消」中间态）⑦ 验收**函数级**（`window._mtRunning=true` 模拟跑维护中 + `document` `dispatchEvent` `keydown` `key=' '` 验 `window._mtPaused=true` 暂停 `#mtrun` 黄态 + toast「已暂停」，再 `Space` 验 `window._mtPaused=false` 续跑 `#mtrun` 回「取消」+ toast「已续跑」，`window._mtRunning=false` 验 toast「Space 暂停需跑维护中」，不真跑 `mtRun` 免 tick 污染 `runs`；`_mtPaused` 块级 `let` 作用外读不验——`window._mtPaused` 全局读写验暂停 / 续跑切换，循环顶挂起 `await` 是 `mtRun` 内部行为不真跑）。

---

## 第195轮（前端 R181 · goal round158）：键盘 `Space`/`Esc`/`Enter` 三键提示浮层（`#mtkeyhint` 小钮，hover 显「Space 暂停 / 续跑 · Esc 取消 · Enter 跳双图 + 聚焦最新轮」，跑中 / 非跑中都能看，键盘流三操作可发现性）

**完善性（键盘流三操作可发现性）**：R178 `Esc` 取消 / R179 `Enter` 跳双图 / R180 `Space` 暂停续跑三键盘操作落地，但**三键分工
没提示入口**（用户不知道维护 tab 有 `Space`/`Esc`/`Enter` 三键，要试错才知道，键盘流三操作可发现性差）。维护 tab 顶栏（`#mtautoref`
自动刷钮旁）加**`#mtkeyhint`** 小钮（`⌨ 键`，`cursor:help` + `title` 提示）+ hover 浮层**`#mtkeyhintdetail`**（`mouseenter` 显「Space
暂停 / 续跑（需跑维护中）· Esc 取消（已跑的轮不回滚）· Enter 跳双图区 + 聚焦最新轮 —— 维护 tab 激活 + 焦点不在输入框时生效」，
`mouseleave` 隐）——跑中 / 非跑中都能看三键分工，键盘流三操作可发现性（免记 / 免试错），与 R178/R179/R180 三键盘操作**对称**。

**E2E**：`#mtkeyhint hover（mouseenter）→ #mtkeyhintdetail 显三键分工（Space 暂停/续跑 + Esc 取消 + Enter 跳双图 + 聚焦最新轮 +
维护 tab 激活+焦点非输入框生效）+ mouseleave → 隐`（绿，三键 `Space`/`Esc`/`Enter` + 生效条件文案）；端点 **30/0**、JS undefined
NONE、CSS 320/320、node 0、console 0、截图 r181_keyhint.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 658→660`，断点 `_整理后分类\华语经典\薛之谦\丑八怪.mp3`。

**坑**：① `#mtkeyhint` 挂维护 tab 顶栏（`#mtautoref` 自动刷 5s 钮后，`--bg2` 底 + `--line` 描边 + `--dim` 色 10px，`cursor:help`
可 hover 提示，`title` 内联提示三键分工，常驻可见不占位——跑中 / 非跑中都显，键盘流提示）② hover 委托（`#mtkeyhint`
`mouseenter`/`mouseleave` 直挂，`#mtkeyhintdetail` 浮层 `pointer-events:none` 不挡下层，hover 钮本体触，`mouseleave` 离即隐）③
`#mtkeyhintdetail` 文案（`_hint` 三键分工 + 生效条件：`Space 暂停 / 续跑（需跑维护中）· Esc 取消（已跑的轮不回滚）· Enter 跳双图
区 + 聚焦最新轮 —— 维护 tab 激活 + 焦点不在输入框时生效`，三键各一句分工 + 末尾生效条件（维护 tab 激活 + 焦点非输入框，
`document` `keydown` 监听 `R178/R179/R180` 同判），hover 看全三键 + 生效条件免试错）④ 浮层定位（R168 `#mtlivedetail` 同
`getBoundingClientRect` 视口坐标 + 边缘 flip：`r.left+dw>视口宽-8` 右贴左翻 / `ty+dh>视口高-8` 翻上，`#mtkeyhint` 在维护 tab 顶栏
`#mtautoref` 旁靠右，hover 浮层视口内不溢出）⑤ 与 R178 `Esc` / R179 `Enter` / R180 `Space` 三键盘操作**对称**（三键盘操作落地，
`#mtkeyhint` 补三键分工提示入口——键盘流三操作可发现性，免记 / 免试错，hover `#mtkeyhint` 看全三键分工 + 生效条件）⑥ 验收**函数级**
（`#mtkeyhint` `dispatchEvent` `mouseenter` 验 `#mtkeyhintdetail` 显 + 三键 `Space`/`Esc`/`Enter` 文案 + `mouseleave` 隐，不真跑
`mtRun` 免 tick 污染 `runs`；`#mtkeyhint` 常驻钮 hover 浮层，headless `mouseenter` 触 `#mtkeyhintdetail` 显，`getBoundingClientRect`
定位 headless 为 0，验 `display`/`textContent` 出口）。

---

## 第196轮（前端 R182 · goal round159）：`#mtlivebadge` 双指标实时徽标暂停 / 续跑同态（`Space` 暂停时 `#mtlivebadge` 变「已暂停 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」黄 `--warn` 态 / 续跑回跑中绿 `--ok` 态，`mtLiveBadge` 读 `window._mtPaused` 同态）

**连贯性（暂停 / 续跑时看徽标知道挂起 / 恢复）**：R180 `Space` 暂停时 `#mtrun` 黄「暂停中 · 按 Space 续跑」，但**`#mtlivebadge`
跑中每轮 tick 刷新时没跟暂停态**（`mtLiveBadge` 每轮 tick 刷绿跑中态，暂停时 `#mtrun` 黄「暂停中」但 `#mtlivebadge` 还显绿跑中，
看徽标不知道挂起）。`mtLiveBadge` 读 `window._mtPaused`（R180 `Space` 暂停 / 续跑全局标志）：暂停时 `#mtlivebadge` 黄 `--warn`
+ 文案前缀「已暂停 ·」（`已暂停 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys`）/ 续跑回绿 `--ok`（`跑中 · 第 i/N 轮 …`）——跑中看徽标
知道挂起 / 恢复，与 `#mtrun` 黄「暂停中」**同态**（暂停 `#mtrun` 黄 + `#mtlivebadge` 黄，续跑 `#mtrun` 红「取消」 + `#mtlivebadge`
绿，双处同步知道跑维护状态）。

**E2E**：`window._mtPaused=true 模拟暂停 + mtLiveBadge 刷新 → #mtlivebadge 黄 --warn rgb(150,101,10) + 文案「已暂停 · 第 2/5 轮 ·
本轮回 +6 · 本轮耗 0.9s」；window._mtPaused=false 续跑 + mtLiveBadge 刷新 → #mtlivebadge 回绿 --ok rgb(47,125,85) + 文案「跑中 ·
第 2/5 轮 …」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r182_pausestate.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 660→662`，断点 `_整理后分类\华语经典\邓紫棋\泡沫.mp3`。

**坑**：① `mtLiveBadge`（R166 跑中双指标徽标函数）函数体顶加 `_paused` 判（`typeof window._mtPaused!=='undefined' && window._mtPaused`，
R180 `window._mtPaused` 挂全局，`mtLiveBadge` 作用域内读 `window` 安全）② 文案前缀同态：`el.textContent=(_paused?'已暂停 · ':'跑中 · ')+
'第 i/N 轮 · 本轮回 +X · 本轮耗 Ys'`（暂停前缀「已暂停 ·」/ 跑中前缀「跑中 ·」，`#mtrun` 黄「暂停中」对应 `#mtlivebadge`「已暂停 ·」，
双处同步知道挂起）③ 色同态：`el.style.color=_paused?'var(--warn)':'var(--ok)'`（暂停黄 `--warn` rgb(150,101,10) / 跑中绿 `--ok`
rgb(47,125,85)，与 `#mtrun` 黄「暂停中」/ 红「取消」跑中色同步，看 `#mtlivebadge` 色知道挂起 / 跑中）④ **`mtLiveBadge` 跑中每轮 tick
刷新时**（R164/R165 `mtRun` 循环每轮调）自然带 `window._mtPaused` 判——暂停后 `#mtrun` 挂起循环不跑 tick，`mtLiveBadge` 不刷新（循环
挂起 `await`），`#mtlivebadge` 保持暂停那轮黄「已暂停 ·」态（不刷绿）；续跑后循环恢复 tick，`mtLiveBadge` 刷新 `window._mtPaused=false`
回绿「跑中 ·」——暂停挂起时徽标定黄「已暂停」，续跑 tick 徽标回绿「跑中」，同态自然 ⑤ 与 `#mtrun` 状态**双处同步**（暂停 `#mtrun` 黄
「暂停中 · 按 Space 续跑」+ `#mtlivebadge` 黄「已暂停 · 第 i/N 轮」，续跑 `#mtrun` 红「取消」 + `#mtlivebadge` 绿「跑中 · 第 i/N 轮」，
看维护区任一处（`#mtrun` 顶栏钮 / `#mtlivebadge` 徽标）都知道跑维护暂停 / 续跑态，双处同步）⑥ `window._mtPaused` `typeof` 判（R180 挂
`window` 全局，`mtLiveBadge` 内 `window._mtPaused` 直读安全，`typeof` 双保险防 `window._mtPaused` 未初始化 `undefined` 时 `undefined` 判
false 跑中态）⑦ 验收**函数级**（`window._mtPaused=true` 模拟暂停 + `mtLiveBadge` 直调刷新验 `#mtlivebadge` 黄「已暂停 ·」，`window.
_mtPaused=false` 续跑 + `mtLiveBadge` 刷新验回绿「跑中 ·」，不真跑 `mtRun` 免 tick 污染 `runs`；`getComputedStyle` 色 `--warn`/`--ok`
验暂停 / 续跑色同态，文案前缀「已暂停 ·」/「跑中 ·」验同态）。

---

## 第197轮（前端 R183 · goal round160）：`#mtmetsum` 双指标汇总标签取消 / 暂停同态（`mtMetSumDraw` 读 `window._mtAborted` / `window._mtPaused`，取消红 `--bad` + 前缀「已取消 ·」/ 暂停黄 `--warn` + 前缀「已暂停 ·」，汇总值保留（已跑轮耗时 / 补入不丢），跑维护状态看汇总也知道挂起 / 取消）

**连贯性（取消 / 暂停时看汇总也知道挂起 / 取消）**：R182 `#mtlivebadge` 徽标暂停 / 续跑同态，`#mtmetsum` 双指标汇总（R158「近 N
次 · 耗时均值 Xs · 补入均值 +Y/次 · 合计 +Z」）取消 / 暂停时没同态（`#mtmetsum` 每跑完刷新一次绿跑中态，跑中取消 / 暂停时汇总还
绿，看汇总不知道挂起 / 取消）。`mtMetSumDraw`（R158 汇总函数）读 `window._mtAborted`（R178 `Esc` 取消）/ `window._mtPaused`（R180
`Space` 暂停）：取消红 `--bad` + 前缀「已取消 ·」（`已取消 · 近 N 次 · 耗时均值 Xs …`）/ 暂停黄 `--warn` + 前缀「已暂停 ·」（`已
暂停 · 近 N 次 …`）/ 续跑 · 非取消回默认色 + 无前缀，**汇总值保留**（已跑轮耗时 / 补入不丢，前缀只标状态不丢值）——跑维护状态看
汇总也知道挂起 / 取消，与 R182 `#mtlivebadge` 徽标暂停同态**双处同步**（暂停 / 取消时 `#mtrun` 红 / 黄 + `#mtlivebadge` 黄 / 绿 +
`#mtmetsum` 黄 / 红，看维护区任一处都知道跑维护状态）。

**E2E**：`写 _mtRunHist(4)+_mtRunDelta(4)+window._mtPaused=true → mtMetSumDraw → #mtmetsum 黄 --warn rgb(150,101,10) + 前缀
「已暂停 · 近 4 次 · 耗时均值 1.1s · 补入均值 +6/次 · 合计 +25」；window._mtAborted=true → 红 --bad rgb(163,38,26) + 前缀「已取消 ·
近 4 次 …」；复位 → 默认色 rgb(119,112,106) + 无前缀「近 4 次 …」（汇总值保留）`（绿）；端点 **30/0**、JS undefined NONE、CSS
320/320、node 0、console 0、截图 r183_metsumstate.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 662→664`，断点 `_整理后分类\华语经典\陈奕迅\淘汰.mp3`。

**坑**：① `mtMetSumDraw`（R158 双指标汇总函数）`txt` 区（`_sumPrefix` 前缀）：`window._mtAborted` 取消红前缀「已取消 · 」/ `window.
_mtPaused` 暂停黄前缀「已暂停 · 」/ 都非前缀空，`txt=_sumPrefix+'近 N 次 · 耗时均值 …'`（前缀拼汇总值前，汇总值照算不丢，已跑轮
耗时 / 补入保留——取消 / 暂停只标状态不改已跑数据）② **色同态**（`el.style.color` 取消 `var(--bad)` rgb(163,38,26) / 暂停 `var(--warn)`
rgb(150,101,10) / 复位 `el.style.color=''` 默认继承 `--dim` rgb(119,112,106)，`#mtmetsum` 是 `#mtdeltabar` 内 span，色跟状态同态
——取消红 / 暂停黄 / 默认灰，看色知道跑维护状态，与 R182 `#mtlivebadge` 色同态对称）③ **优先级**（`_sumPrefix` 取消 > 暂停——
`if(window._mtAborted) 已取消 else if(window._mtPaused) 已暂停`，取消态优先于暂停态，`Esc` 取消时 `Space` 暂停不并存（取消跳出
循环暂停无意义，`_mtAborted` 优先显「已取消」，同色同判 `window._mtAborted` 先）④ `mtMetSumDraw` 每跑完 / 取消 / 暂停时刷新（R158
`mtRun` 跑完调 + `mtMetSumDraw` 每 tick 调，取消 / 暂停挂起 `mtRun` 循环不 tick `mtMetSumDraw` 不刷，但 `mtRun` 跑完 / 取消区调
`mtMetSumDraw` 带 `window._mtAborted` 前缀——取消时汇总前缀「已取消 ·」，`mtLiveBadge` 同（R182 暂停挂起不刷，取消 / 跑完刷带
前缀））⑤ **与 R182 `#mtlivebadge` 双处同步**（暂停 `#mtrun` 黄「暂停中」 + `#mtlivebadge` 黄「已暂停 ·」 + `#mtmetsum` 黄「已暂停 ·
近 N 次」，取消 `#mtrun` 红「取消」 + `#mtlivebadgeHide` 隐 + `#mtmetsum` 红「已取消 · 近 N 次」，看维护区顶栏 `#mtrun` / `#mtlivebadge`
徽标 / `#mtmetsum` 汇总任一处都知道跑维护状态，三处同步）⑥ 复位默认色（`el.style.color=''` 清内联继承 `--dim`，`#mtmetsum` 默认
`--dim` 灰，续跑 / 非取消清前缀清色回默认——取消 / 暂停前缀 + 色只在挂起 / 取消态带，跑完 / 续跑清）⑦ 验收**函数级**（写
`_mtRunHist`/`_mtRunDelta` 4 条 + `window._mtPaused=true` / `window._mtAborted=true` / 复位三态 `mtMetSumDraw` 直调刷新验 `#mtmetsum`
前缀「已暂停 ·」/「已取消 ·」/ 无前缀 + 色 `--warn`/`--bad`/默认，不真跑 `mtRun` 免 tick 污染 `runs`；`getComputedStyle` 色验三态
同态，汇总值「近 4 次 · 耗时均值 1.1s · 补入均值 +6/次 · 合计 +25」三态保留验前缀只标状态不丢值）。

---

## 第198轮（前端 R184 · goal round161）：维护状态三处（`#mtrun` 钮 / `#mtlivebadge` 徽标 / `#mtmetsum` 汇总）同态指示条（`#mtstatebar` 顶栏细色条：跑中绿 `--ok` / 暂停黄 `--warn` / 取消红 `--bad` / 完成默认 `--line`，读 `window._mtRunning`/`_mtPaused`/`_mtAborted` 同态，跑维护状态看顶栏一条色带全知）

**简洁性（三处同态收敛到一条带全知）**：R182/R183 三处同态（`#mtrun` 黄「暂停中」/ `#mtlivebadge` 黄「已暂停 ·」/ `#mtmetsum`
黄「已暂停 · 近 N 次」，取消红），但**没顶栏统一指示条**（三处色散在维护区各元素，看状态要逐个找）。`#mtmetfold` 上沿加
**`#mtstatebar`**（3px 细色带）+ **`mtStateBarDraw`**（读 `window._mtAborted`/`window._mtPaused`/`window._mtRunning` 同态显色：
取消红 `--bad` / 暂停黄 `--warn` / 跑中绿 `--ok` / 完成灰 `--line`）——跑维护状态看顶栏**一条色带全知**（三处同态 `#mtrun` /
`#mtlivebadge` / `#mtmetsum` 收敛到 `#mtstatebar` 一条带，扫顶栏色带即知跑维护状态，免逐个找三处色）。

**E2E**：`取消 → #mtstatebar 红 --bad rgb(163,38,26)；暂停 → 黄 --warn rgb(150,101,10)；跑中 → 绿 --ok rgb(47,125,85)；
复位 → 灰 --line rgb(226,221,211)（四态同态，去 transition 立即改色）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、
node 0、console 0、截图 r184_statebar.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 664→666`，断点 `_整理后分类\华语经典\陶喆\Don't Worry.mp3`。

**坑**：① `#mtstatebar` 挂 `#mtmetfold` 上沿（3px 细色带 `height:3px width:100% background:var(--line) border-radius:2px`，
维护 tab 顶栏 `#mtmetfold` 折叠钮上沿，扫顶栏一条色带即知跑维护状态，`title` 提示「绿跑中 / 黄暂停 / 红取消 / 灰完成」）②
`mtStateBarDraw`（读 `window._mtAborted`/`window._mtPaused`/`window._mtRunning` 同态显色，**优先级 取消 > 暂停 > 跑中 > 完成**——
`if(window._mtAborted) 红 else if(window._mtPaused) 黄 else if(window._mtRunning) 绿 else 灰`，取消态优先，同 R183 `#mtmetsum`
汇总优先级）③ **`window._mtAborted` 挂全局坑**（R178 `Esc` 区设**块级 `_mtAborted=true`**（`mtRun` 函数内 `let`），`mtStateBarDraw`
读 `window._mtAborted` 从没挂 → 四态都走 else `--line` 灰（`getComputedStyle` 验四态都 `rgb(226,221,211)`，`mtStateBarDraw` 没改色
——`window._mtAborted` 永远 `undefined`）。Fix：R178 `Esc` 区 `_mtAborted=true` 后加 `window._mtAborted=true`，`mtRun` 顶
`_mtAborted=false` 后加 `window._mtAborted=false`，`let _mtAborted` 声明后挂 `window._mtAborted=_mtAborted` 同步初值——`mtStateBarDraw`
读 `window._mtAborted` 真取到，四态同态改色真生效）④ **`transition:background .3s` 坑**（`#mtstatebar` 初版带 `transition`，
`getComputedStyle` 改色瞬间取 `transition` 起点 `--line`（中 `background` 从 `--line` 过渡到 `--bad`，立即取起点 `rgb(226,221,211)`），
四态都验 `--line`。Fix：去 `transition`（指示条状态色不需过渡，立即改色——`mtStateBarDraw` 设 `bar.style.background='var(--bad)'`
后立即 `getComputedStyle` 取 `rgb(163,38,26)`，去 `transition` 状态色即时同态）⑤ 各态调 `mtStateBarDraw`（`Esc` 取消区 / `Space`
暂停续跑区 / `mtRun` 跑中每轮 tick 后 / `mtRun` 跑完复位区，`document` 键盘操作 + `mtRun` 循环各态都调 `mtStateBarDraw` 同步指示
条——`Esc` 取消 `mtStateBarDraw` 红，`Space` 暂停 / 续跑 `mtStateBarDraw` 黄 / 回绿，`mtRun` 每轮 tick `mtStateBarDraw` 绿，跑完
复位 `mtStateBarDraw` 灰，全路径同态）⑥ 与 R182 `#mtlivebadge` / R183 `#mtmetsum` 三处同态**对称**（`#mtrun` 钮 / `#mtlivebadge`
徽标 / `#mtmetsum` 汇总 / `#mtstatebar` 指示条四处同态，`#mtstatebar` 顶栏一条带全知 + 三处各元素同态，扫顶栏 + 看元素双路知
跑维护状态）⑦ 验收**函数级**（`window._mtAborted`/`_mtPaused`/`_mtRunning` 四态置值 + `mtStateBarDraw` 直调刷新验 `#mtstatebar`
`getComputedStyle` 色 `--bad`/`--warn`/`--ok`/`--line`，不真跑 `mtRun` 免 tick 污染 `runs`；`window._mtAborted` 挂全局验取消同态
真生效，`transition` 去除验立即改色）。

---

## 第199轮（前端 R185 · goal round162）：`#mtstatebar` 指示条 hover 显状态文字详情（`#mtstatebardtl` 浮层，hover 显「跑中 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」/「已暂停 · …」/「已取消 · …」，指示条色 + hover 文字双路知状态）

**简洁性（色带 + hover 文字双路知状态免只看色）**：R184 `#mtstatebar` 一条色带全知但**没 hover 文字详情**（色带只知状态绿 /
黄 / 红 / 灰，不知第几轮 / 本轮回 / 耗时）。`#mtstatebar` hover（`mouseenter`）→ **`#mtstatebardtl`** 浮层显状态详情（读
`window._mtLiveInfo`（R185 新增，`mtRun` 每轮 tick 存 `{i, N, back, dur}`）+ `window._mtPaused`/`_mtAborted` 同态，显「跑中 ·
第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」/「已暂停 · 第 i/N 轮 …」/「已取消 · 第 i/N 轮 …」）——指示条色 + hover 文字**双路知状态**
（扫顶栏色带知跑中 / 暂停 / 取消 / 完成 + hover `#mtstatebar` 看第几轮 / 本轮回 / 耗时详情，色带 + 文字双路，免只看色不知进度）。

**E2E**：`window._mtLiveInfo={i:2,N:5,back:6,dur:0.9} + 跑中 / 暂停 / 取消三态 → #mtstatebar hover → #mtstatebardtl 显「跑中 ·
第 2/5 轮 · 本轮回 +6 · 本轮耗 0.9s」/「已暂停 · 第 2/5 轮 …」/「已取消 · 第 2/5 轮 …」+ mouseleave → 隐`（绿）；端点 **30/0**、
JS undefined NONE、CSS 320/320、node 0、console 0、截图 r185_statedetail.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 666→668`，断点 `_整理后分类\华语经典\陶喆\爱很简单.mp3`。

**坑**：① `#mtstatebardtl` 挂 `#mtstatebar` 内（`#mtstatebar` 加 `position:relative`，`#mtstatebardtl` `position:absolute top:6px left:0`，
`#mtstatebar` hover 浮层贴色带下沿 6px，`pointer-events:none` 不挡下层，`white-space:nowrap` 单行不折，`z-index:60` 维护区上层，
浮层色 `--bg2` 底 + `--line` 描边 + `--ink` 色 10px，`box-shadow` 微浮，贴色带显状态详情不挡维护区）② `#mtstatebar` hover 委托
（`mouseenter` 显 `#mtstatebardtl` + 文案 / `mouseleave` 隐，直挂 `#mtstatebar`，`#mtstatebardtl` `pointer-events:none` 不挡下层，
hover 色带本体触，离即隐）③ **`window._mtLiveInfo` 存跑中实时信息**（`mtRun` 每轮 tick 后（R184 `mtStateBarDraw` 调后）存
`window._mtLiveInfo={i, N, back:(r.lyric_ok+r.cover_ok), dur:(Date.now()-_t1)/100}`，`#mtstatebar` hover 读 `window._mtLiveInfo`
拼「第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」，`mtRun` 跑完 / 取消区 `window._mtRunning=false` 后 `window._mtLiveInfo` 保留最后轮
（hover 看最后跑到的轮详情，不丢）④ 状态前缀同态（`_mtAborted` 取消「已取消 ·」/ `_mtPaused` 暂停「已暂停 ·」/ `_mtRunning`
跑中「跑中 ·」/ 都非「维护完成 / 未跑（灰）」，`#mtstatebardtl` 文案前缀与 `#mtmetsum`（R183）/ `#mtlivebadge`（R182）同态前缀
语言，三处同态 + 指示条 hover 文案前缀对称）⑤ **`i/N` 全库 `∞`**（`N>100000` 全库显 `∞`（R166 `#mtlivebadge` 同纪律），hover
详情全库跑中显「第 i/∞ 轮 · 本轮回 +X · 本轮耗 Ys」，与 `#mtlivebadge` 全库 `∞` 对称）⑥ 验收**函数级**（`window._mtLiveInfo`
置 `{i:2,N:5,back:6,dur:0.9}` + `window._mtRunning`/`_mtPaused`/`_mtAborted` 三态 + `#mtstatebar` `dispatchEvent` `mouseenter`
验 `#mtstatebardtl` 文案前缀「跑中 ·」/「已暂停 ·」/「已取消 ·」+ 「第 2/5 轮」+ `mouseleave` 隐，不真跑 `mtRun` 免 tick 污染
`runs`；`window._mtLiveInfo` 直置验 hover 详情拼文案，`mtRun` 每轮 tick 真存 `window._mtLiveInfo` 不验（循环内行为））。

---

## 第200轮（前端 R186 · goal round163）：`#mtkeyhint` 三键提示浮层补 `Space`/`Esc`/`Enter` 快捷键实际状态灯（`#mtkeyhintdetail` 浮层三键各带一小色点：可触绿 / 不可触灰 / 暂停黄，三键可触状态随跑维护态实时显，hover 看三键当前可触 / 不可触）

**完善性（三键可触 / 不可触实时显免试错）**：R181 `#mtkeyhint` 三键提示浮层只列三键分工文案（「Space 暂停 / 续跑（需跑维护中）
· Esc 取消（已跑的轮不回滚）· Enter 跳双图区 + 聚焦最新轮」），**没显三键当前可触 / 不可触**（非跑维护中按 `Space` 不可触（需
跑维护中）、`Esc` 取消需跑中、`Enter` 跳双图非跑中也触但无跑中详情，要试错才知道当前哪键能按）。`#mtkeyhintdetail`（R181 hover
委托区）改三键各带一小**色点**（`_keyDot` 内联 span `6px` 圆点）：`Space` 可触（`_run && !_ab`）绿 / 暂停态（`_ps`）黄（可续跑）/
非跑中灰；`Esc` 可触（`_run && !_ab`）绿 / 非跑中灰；`Enter` 可触（`!_ab`）绿 / 取消灰——hover `#mtkeyhint` 看三键当前可触 / 不可
触 / 暂停（色点随 `window._mtRunning`/`_mtPaused`/`_mtAborted` 实时显），免试错，三键可触状态一目了然。

**E2E**：`跑中非暂停（window._mtRunning=true,_mtPaused=false,_mtAborted=false）→ hover #mtkeyhint → #mtkeyhintdetail 三键色点
（Space 绿 + Esc 绿 + Enter 绿）；暂停（_mtPaused=true）→ Space 黄 + Esc 绿 + Enter 绿；非跑中（_mtRunning=false）→ Space 灰 +
Esc 灰 + Enter 绿（Enter 非跑中也触跳双图）+ mouseleave → 隐`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、
console 0、截图 r186_keydots.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 668→670`，断点 `_整理后分类\摇滚民谣\万能青年旅店\收藏.mp3`。

**坑**：① `_keyDot(_on, _warn)` 色点（内联 `<span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:
var(--warn|var(--ok)|var(--line));margin-right:2px"></span>`，6px 圆点：`_warn` 黄 `--warn`（暂停可续跑）/ `_on` 绿 `--ok`（可触）
/ 灰 `--line`（不可触），`#mtkeyhintdetail` 内联 span 色点跟三键文案前缀，色点小不挡文案，`margin-right:2px` 隔开）② 三键可触判
（`_spCan=_run&&!_ab` Space 暂停 / 续跑需跑维护中且未取消，暂停态 `_ps&&_spCan` 显黄（可续跑）；`_esCan=_run&&!_ab` Esc 取消需
跑中未取消；`_enCan=!_ab` Enter 跳双图非取消即触（非跑中也触但跳双图无跑中详情，可触绿），三键可触读 `window._mtRunning`/
`_mtPaused`/`_mtAborted` 实时判，hover 时算当前态）③ `#mtkeyhintdetail` 改 `innerHTML`（R181 `textContent` → `innerHTML`，色点
内联 span 需 `innerHTML` 拼 `<span>`，`mouseleave` 清 `innerHTML=''` 不 `textContent=''`，`d.innerHTML` 含色点 span + 三键文案，
headless 验 `innerHTML` 含 `var(--ok)`/`var(--warn)`/`var(--line)` 色点）④ **`Enter` 非跑中也可触绿**（`_enCan=!_ab`，`Enter` 跳
双图 + 聚焦最新轮非跑维护中也能跳（跳双图区看趋势，非跑中也有效），非取消即绿——区别于 `Space`/`Esc` 需跑维护中（`_run`），
`Enter` 跳双图双指标趋势非跑中也可看，三键可触判不同）⑤ 与 R181 三键提示**分工**（R181 文案列三键分工，R186 色点显三键当前可
触 / 不可触 / 暂停，文案 + 色点双路：看文案知三键做什么 + 看色点知当前哪键能按，免试错）⑥ `mouseenter` 实时算（`#mtkeyhint`
hover 时 `mouseenter` 读 `window._mtRunning`/`_mtPaused`/`_mtAborted` 算三键可触，非跑中 hover 显 `Space`/`Esc` 灰 + `Enter` 绿，
跑中 hover 显三键绿，暂停 hover 显 `Space` 黄，hover 每次重算当前态，非缓存旧态）⑦ 验收**函数级**（`window._mtRunning`/`_mtPaused`/
`_mtAborted` 三态置值 + `#mtkeyhint` `dispatchEvent` `mouseenter` 验 `#mtkeyhintdetail` `innerHTML` 色点 `var(--ok)`/`var(--warn)`/
`var(--line)` + 三键文案 + `mouseleave` 隐，不真跑 `mtRun` 免 tick 污染 `runs`；`_keyDot` 色点 headless 验 `innerHTML` 含色点
`var()` 色，非真渲染圆点像素）。

---

## 第201轮（前端 R187 · goal round164）：跑维护全库完成（`FULL_DONE`）时 `#mtlivebadge` 补完成态徽标「已跑完 · 共 N 轮 · 耗时 Xs」绿 `--ok`（`mtLiveBadgeDone`，全库收尾看徽标完成态 + 指示条灰双路知全库收尾）

**完善性（全库收尾看徽标完成态免找入口）**：R184 `#mtstatebar` 跑中绿 / 暂停黄 / 取消红 / 完成灰，`FULL_DONE` 全库完成
`mtStateBarDraw` 灰已显完成，但**`#mtlivebadge` 全库完成 `mtLiveBadgeHide` 隐了**（跑完 / 取消都 `mtLiveBadgeHide`，全库跑完徽标
消失，看完成状态没入口）。`mtRun` 跑完区（`_mtUnaborted` 后 `mtLiveBadgeHide`）改：`FULL_DONE` 时不 `Hide` 改**`mtLiveBadgeDone`**
（显 `#mtlivebadge` 绿 `--ok` + 文案「已跑完 · 共 N 轮 · 耗时 Xs」完成态，`#mtlivedetail` 详情「全库维护完成 · 共 N 轮 · 累计耗
时 Xs · 点双图区汇总跳双图看趋势」）/ 非全库 · 取消仍 `Hide`——全库跑完看 `#mtlivebadge` 完成态 + `#mtstatebar` 完成灰**双路知
全库收尾**（区别于跑中每轮刷跑中态，全库收尾固定显完成态，扫一眼知道全库维护收工）。

**E2E**：`mtLiveBadgeDone(5, 12.3) → #mtlivebadge 绿 --ok rgb(47,125,85) + 文案「已跑完 · 共 5 轮 · 耗时 12.3s」（完成态徽
标，非跑中每轮刷）+ #mtlivedetail 详情「全库维护完成 · 共 5 轮 · 累计耗时 12.3s · 点双图区汇总跳双图看趋势」`（绿）；端点
**30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r187_donebadge.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 670→672`，断点 `_整理后分类\摇滚民谣\亚细亚旷世奇才\旷世奇才.mp3`。

**坑**：① `mtLiveBadgeDone(N, totalDur)`（`#mtlivebadge` 完成态徽标，`mtLiveBadgeHide` 后）：`el.textContent='已跑完 · 共 N 轮 ·
耗时 totalDurs'` + `el.style.color='var(--ok)'`（绿完成态）+ `display='inline-block'`（显），`#mtlivedetail` 详情「全库维护完成 ·
共 N 轮 · 累计耗时 totalDurs · 点双图区汇总跳双图看趋势」（`display:'none'` 隐详情——完成态详情只在 hover `#mtlivebadge` 时 `cursor:help`
看，`mtLiveBadgeDone` 显详情文案不 `display:block`，hover `#mtlivebadge`（`cursor:help`）触发 `#mtlivedetail` 原 hover 委托显）②
**`mtRun` 跑完区分 `FULL_DONE`**（`_mtUnaborted` 后：`if(FULL_DONE){ mtLiveBadgeDone(N, _mtTotalDur); } else { mtLiveBadgeHide(); }`
——全库 `FULL_DONE` 显完成态徽标，非全库普通跑完 / 取消 `Hide` 隐徽标，`_mtTotalDur` 全库累计耗时（R167 累加器）传完成态详情，
`N` 全库 `i`（跑到轮数））③ **完成态 vs 跑中态**（`mtLiveBadge` 跑中每轮 tick 刷「跑中 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys」绿
`--ok`，`mtLiveBadgeDone` 全库收尾固定「已跑完 · 共 N 轮 · 耗时 Xs」绿 `--ok`——两态同绿 `--ok` 但文案不同（跑中每轮刷 / 完成
固定），全库收尾 `FULL_DONE` 跳出循环后 `mtRun` 跑完区调 `mtLiveBadgeDone` 覆盖跑中最后一轮态，固定显完成）④ 与 `#mtstatebar`
完成灰**双路**（`#mtstatebar` 全库完成 `mtStateBarDraw` 灰 `--line`（非跑中默认灰），`#mtlivebadge` 全库完成 `mtLiveBadgeDone`
绿 `--ok` 完成态——色带灰知非跑中 + 徽标绿知完成，两路知全库收尾；`#mtstatebar` 灰是「非跑中」态（完成 / 未跑都灰），`#mtlivebadge`
绿是「完成」态（`FULL_DONE` 才绿完成，未跑 / 取消不绿），双路区分完成 vs 未跑）⑤ 验收**函数级**（`mtLiveBadgeDone(5, 12.3)` 直调
验 `#mtlivebadge` 文案「已跑完 · 共 5 轮 · 耗时 12.3s」+ 绿 `--ok` + `inline-block` 显 + `#mtlivedetail` 详情「全库维护完成 · 共 5
轮 · 累计耗时 12.3s」，不真跑 `mtRun` 全库免 tick 污染 `runs`；`mtRun` 跑完区 `FULL_DONE` 调 `mtLiveBadgeDone` 是循环后行为不验，
验 `mtLiveBadgeDone` 函数出口）。

---

## 第202轮（前端 R188 · goal round165）：`#mtmetsum` 双指标汇总 hover 显逐轮明细（`#mtmetsumdetail` 浮层，hover 显近 N 次每轮耗时 + 补入明细列表（第 i 次 Xs · 补入 +Y / …）+ 均值 / 合计，常驻汇总 hover 看逐轮明细）

**完善性（汇总 hover 看逐轮明细免只看均值）**：R183 `#mtmetsum` 取消 / 暂停同态前缀 + 汇总值（均值 / 合计），但汇总只显
均值 / 合计**不显逐轮明细**（近 N 次每轮耗时 + 补入逐条列表没入口，要看逐轮趋势得看双图区柱状 / 折线，汇总 hover 没逐轮
明细）。`#mtmetsum`（R158 双指标汇总 span）加 hover 委托 + **`#mtmetsumdetail`** 浮层（`mouseenter` 显「近 N 次逐轮明细：
第 i 次 Xs · 补入 +Y / …」逐条列表 + 均值 / 合计，读 `localStorage._mtRunHist`/`_mtRunDelta` 逐条拼，`mouseleave` 隐）——常驻
汇总 hover 看逐轮明细（与 R186 `#mtkeyhint` 三键状态灯 hover 详情同「hover 看逐条」语言，汇总均值 / 合计 + hover 逐轮明细
双路看双指标趋势）。

**E2E**：`写 _mtRunHist(4)+_mtRunDelta(4) → #mtmetsum hover（mouseenter）→ #mtmetsumdetail 显「近 4 次逐轮明细：第 i 次 Xs ·
补入 +Y」逐条列表 + 均值 / 合计 + mouseleave → 隐`（绿，逐轮明细 + 逐条第 i 次 + 均值合计）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r188_metsumhover.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 672→674`，断点 `_整理后分类\摇滚民谣\宋冬野\无题.mp3`。

**坑**：① `#mtmetsumdetail` 挂 `#mtmetsum` 后（`#mtdeltabar` 双图区 `#mtmetsum` span 后，`position:absolute z-index:60`，`--bg2` 底
+ `--line` 描边 + `--ink` 色 10px，`line-height:1.5` 多行逐轮明细，`white-space:nowrap` + `max-width:280px`（逐条多行 `br` 折，
`max-width` 限宽不超双图区，`pointer-events:none` 不挡下层）② `#mtmetsum` hover 委托（`mouseenter` 显 `#mtmetsumdetail` 逐轮明
细 / `mouseleave` 隐，`#mtmetsum` span `mouseenter` 直挂，`#mtmetsumdetail` `pointer-events:none` 不挡下层，hover 汇总本体触，
离即隐）③ 逐轮明细读 `localStorage._mtRunHist`/`_mtRunDelta` 逐条拼（`h` 耗时近 10 + `b` 补入近 10，`n=max(h.length, b.length)`，
`for _k=0..n` 第 `n-1-_k` 次（新→旧，末位最新在第 0 次——`_k=0` 第 `n-1` 次是最新轮，`_k=n-1` 第 `0` 次最早轮，倒序显最新在上）
+ 均值 `h.reduce/len toFixed(1)` + 合计 `b.reduce`，`d.innerHTML=_lines.replace(/
/g,'<br>')` 多行 `br` 折）④ 倒序显最新在上
（`_k=0` 第 `n-1-_k` 次 = 最新轮 `n-1`，`_k=n-1` 第 `0` 次最早轮——逐轮明细最新在上，看逐轮趋势从上往下越旧，与双图区末柱最新
对称）⑤ 空历史（`n=0` `#mtmetsum` 无数据）→ `#mtmetsumdetail` 显「无跑维护双指标历史」（不显逐条，`#mtmetsum` 本身 `display:none`
无数据不显，hover 不触——`#mtmetsum` `display:none` 时 `mouseenter` 不触，`#mtmetsumdetail` 不显，空历史入口只在 `#mtmetsum` 显时
才 hover 触）⑥ 与 R183 汇总均值 / 合计 + R188 hover 逐轮明细**双路**（`#mtmetsum` 常驻显均值 / 合计（`mtMetSumDraw` 汇总一行），
hover 显逐轮明细（`#mtmetsumdetail` 多行逐条），看均值扫一眼 + hover 看逐条，双指标趋势双粒度）⑦ 验收**函数级**（写
`_mtRunHist`/`_mtRunDelta` 4 条 + `#mtmetsum` `dispatchEvent` `mouseenter` 验 `#mtmetsumdetail` 显「逐轮明细」+ 逐条第 i 次 + 均值
合计 + `mouseleave` 隐，不真跑 `mtRun` 免 tick 污染 `runs`；`#mtmetsumdetail` 逐条 headless 验 `textContent` 含「逐轮明细」+ 第 i 次
+ 均值合计，非真渲染多行）。

---

## 第203轮（前端 R189 · goal round166）：`#mtmetsum` 双指标汇总 hover 逐轮明细复制（`#mtmetsumdetailcopy` 小钮，复制「#music3 双指标逐轮明细 · <ts>」+ 逐轮明细文本到剪贴板，贴工单 / 记录维护日志，与 R169 详情复制同「复制出口」语言）

**完善性（逐轮明细留存 / 分享免手抄）**：R188 `#mtmetsumdetail` hover 逐轮明细浮层只显逐轮明细看，**没复制出口**（逐轮
明细文本要留存 / 贴工单 / 记录维护日志得手动抄，剪贴板复制没做）。`#mtmetsum` 旁加**`#mtmetsumdetailcopy`** 小钮（`⧉ 复制`，
`#mtdeltabar` 内 `#mtmetsum` 后独立位，`mtMetSumDraw` 显 `#mtmetsum` 时 copy 显 / 无数据隐），点 `#mtmetsumdetailcopy` →
**`mtMetSumDetailCopy`**（读 `localStorage._mtRunHist`/`_mtRunDelta` 逐条拼「#music3 双指标逐轮明细 · <ts>」+ 逐轮明细文本
（第 i 次 Xs · 补入 +Y / …）+ 均值 / 合计，`navigator.clipboard.writeText`（`_copyFallback` `textarea` `execCommand` 降级）
+ toast「已复制双指标逐轮明细（N 次）」）——逐轮明细复制贴工单 / 记录维护日志，双指标逐轮趋势可留存 / 可分享，与 R169
`#mtlivedetailcopy` 详情复制同「复制出口」语言。

**E2E**：`写 _mtRunHist(4)+_mtRunDelta(4) → mtMetSumDraw（显 #mtmetsum + copy）→ 点 #mtmetsumdetailcopy → toast「已复制双指标
逐轮明细（4 次）」（剪贴板 / 降级出口验 toast 文案）；清 localStorage → mtMetSumDraw（隐 #mtmetsum + copy）→ 点 copy →
toast「无双指标逐轮明细可复制」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图
r189_metsumcopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 674→676`，断点 `_整理后分类\摇滚民谣\朴树\达尼亚.mp3`。

**坑**：① `#mtmetsumdetailcopy` 挂 `#mtmetsum` 旁独立位（`#mtdeltabar` 内 `#mtmetsum` 后 `inline-block`，非 `#mtmetsumdetail` 内——
R188 `#mtmetsum` hover 委托 `d.innerHTML=_lines.replace(...)` 重写 `#mtmetsumdetail` 全 innerHTML，copy 钮若挂 `#mtmetsumdetail` 内
会被 `d.innerHTML` 冲掉（headless 验 `cp` 取 `null`，`Cannot read properties of null`），改挂 `#mtmetsum` 旁独立位，`d.innerHTML`
不碰 copy，`#mtmetsumdetail` 只显逐轮明细文本，copy 独立）② copy 跟 `#mtmetsum` 数据显隐（`mtMetSumDraw` 显 `#mtmetsum`（有数据）
时 `#mtmetsumdetailcopy` `display='inline-block'` 显 / 无数据（`!h.length && !d.length` `#mtmetsum` `display:none`）时 copy `display='none'`
隐——copy 跟 `#mtmetsum` 数据，非 hover 态控，`mtMetSumDraw` 每跑完 / tick 调同步 copy 显隐，`#mtmetsum` 隐 copy 也隐）③
`mtMetSumDetailCopy`（读 `localStorage._mtRunHist`/`_mtRunDelta` 逐条拼，倒序第 `n-1-_k` 次最新在上，`#music3 双指标逐轮明细 ·
<new Date().toLocaleString()>` 头 + 逐轮明细 + 均值 / 合计，`navigator.clipboard.writeText`（`_copyFallback` `textarea`
`execCommand('copy')` 降级，`clipboard` 无权限 / 非 secure context 降级）+ toast「已复制双指标逐轮明细（N 次）」，空历史
（`n=0`）toast「无双指标逐轮明细可复制」`bad`，同 R169 `mtLiveDetailCopy` 空详情 toast 纪律）④ 与 R188 `#mtmetsumdetail` hover
逐轮明细**分工**（R188 hover 显逐轮明细看（`#mtmetsumdetail` 浮层），R189 copy 复制逐轮明细文本留存 / 分享（`#mtmetsumdetailcopy`
贴工单 / 记录维护日志），看 + 复制双出口，逐轮明细可看可留存）⑤ 验收**函数级**（写 `_mtRunHist`/`_mtRunDelta` 4 条 + `mtMetSumDraw`
显 `#mtmetsum`/copy + 点 `#mtmetsumdetailcopy` 验 toast「已复制双指标逐轮明细（4 次）」，清 `localStorage` + `mtMetSumDraw` 隐
`#mtmetsum`/copy + 点 copy 验 toast「无双指标逐轮明细可复制」，剪贴板 / 降级只验 toast 出口（真剪贴板内容 headless 不验，`copy` 文本
拼逻辑验 `mtMetSumDetailCopy` 出口 toast），不真跑 `mtRun` 免 tick 污染 `runs`）。

---

## 第204轮（前端 R190 · goal round167）：`#mtmetsum` 双指标汇总 hover 逐轮明细浮层补 `#mtmetsumdetailcopy` 复制钮联动（`#mtmetsumdetail` hover 显浮层时 copy 显，hover 逐轮明细时顺手复制免移开找常驻位，浮层内 + 常驻双入口）

**流畅性（hover 逐轮明细顺手复制免移开）**：R189 `#mtmetsumdetailcopy` 挂 `#mtmetsum` 旁常驻位（`mtMetSumDraw` 数据显隐），hover
`#mtmetsumdetail` 浮层看逐轮明细时想复制要移开点 `#mtmetsum` 旁常驻 copy，**浮层内没复制入口**（hover 浮层逐轮明细时顺手复制免移开
找常驻 copy）。`#mtmetsum` hover 委托（R188 区）改：`#mtmetsum` 有数据 hover 显 `#mtmetsumdetail` 浮层时 `#mtmetsumdetailcopy` 同步显
（`mouseenter` 有数据 `cp.style.display='inline-block'`），`mouseleave` 浮层隐 + copy 隐（`cp.style.display='none'`）——copy 跟**浮层
hover 态**（非 `#mtmetsum` 数据态，`mtMetSumDraw` 不控 copy 显，避免常驻显），hover 逐轮明细时 copy 同步显顺手点复制，免移开找常驻
位，浮层内 + 常驻双入口（hover 浮层看逐轮明细时顺手复制 / 不 hover 时 `#mtmetsum` 旁常驻 copy 也在（`mtMetSumDraw` 数据显 `#mtmetsum`
时常驻位 copy 可点），双入口同 `mtMetSumDetailCopy`）。

**E2E**：`写 _mtRunHist(4)+_mtRunDelta(4) → #mtmetsum hover（mouseenter）→ #mtmetsumdetail 浮层显 + #mtmetsumdetailcopy 显（hover
态）+ 点 copy → toast「已复制双指标逐轮明细（4 次）」；mouseleave → 浮层隐 + copy 隐`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r190_hovercopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 676→678`，断点 `_整理后分类\摇滚民谣\苏打绿\当我们一起走过.mp3`。

**坑**：① copy 跟**浮层 hover 态**（非 `#mtmetsum` 数据态）：`#mtmetsum` `mouseenter` 有数据（`n>0`）显 `#mtmetsumdetail` 浮层时
`cp.style.display='inline-block'` 显 copy / `mouseleave` 浮层隐 `cp.style.display='none'` 隐 copy——copy 显隐跟 hover 态，不跟
`#mtmetsum` 数据态（`mtMetSumDraw` 不控 copy 显，避免常驻显）② `mtMetSumDraw`（R189 区）改不控 copy（R189 `mtMetSumDraw` 有数据
`cp.style.display='inline-block'` 常驻显 → R190 去，copy 跟 hover 态，`#mtmetsum` 旁常驻位 copy 只 hover 浮层时显，非 hover 不显
——避免 `#mtmetsum` 有数据时 copy 常驻占位，hover 才显顺手复制）③ `#mtmetsumdetailcopy` 挂 `#mtmetsum` 旁独立位（R189 坑，非
`#mtmetsumdetail` 内防 `d.innerHTML` 冲掉），`#mtdeltabar` 内 `#mtmetsum` 后 `inline-block`，hover 浮层显时 copy 显（`#mtmetsum` 旁
copy 跟浮层 hover 态，hover 浮层看逐轮明细时 copy 同步在 `#mtmetsum` 旁显，顺手点 copy 复制免移开找）④ `mtMetSumDetailCopy`（R189
复制函数，读 `localStorage._mtRunHist`/`_mtRunDelta` 逐条拼「#music3 双指标逐轮明细 · <ts>」+ 逐轮明细 + 均值 / 合计，`navigator.
clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制双指标逐轮明细（N 次）」）复用，hover 浮层内 copy + 常驻 copy 同
`mtMetSumDetailCopy`，双入口同复制函数不重复实现 ⑤ 与 R188 hover 浮层 / R189 常驻 copy**双入口**（R188 `#mtmetsum` hover 显
`#mtmetsumdetail` 逐轮明细浮层看，R189 `#mtmetsum` 旁常驻 copy 复制，R190 copy 跟浮层 hover 态——hover 逐轮明细时 copy 同步显
顺手复制 + 不 hover 时常驻 copy 也可点，浮层内 + 常驻双入口，复制出口两处）⑥ 验收**函数级**（写 `_mtRunHist`/`_mtRunDelta` 4 条 +
`#mtmetsum` `dispatchEvent` `mouseenter` 验 `#mtmetsumdetail` 浮层显 + `#mtmetsumdetailcopy` hover 态显 + 点 copy 验 toast「已复制
双指标逐轮明细（4 次）」，`mouseleave` 验浮层 + copy 隐，不真跑 `mtRun` 免 tick 污染 `runs`；copy 复制只验 toast 出口，真剪贴板内容
headless 不验）。

---

## 第205轮（前端 R191 · goal round168）：`#mtstatebar` 指示条 hover 详情补复制出口（`#mtstatebardtlcopy` 小钮，hover `#mtstatebar` 显 `#mtstatebardtl` 状态详情浮层（R185）时同步显复制小钮，复制「#music3 维护状态 · <ts>」+ 状态详情文本到剪贴板，贴工单 / 记录维护日志，与 R169 / R189 复制出口同语言）

**完善性（状态详情留存 / 分享免手抄）**：R185 `#mtstatebardtl` hover 显状态详情（跑中 / 暂停 / 取消 + 第 i/N 轮 + 本轮回 +X +
本轮耗 Ys），但**没复制出口**（状态详情文本要留存 / 贴工单得手动抄，`#mtstatebardtlcopy` 复制小钮 hover 详情浮层内顺手复制免手抄，
状态详情可留存 / 可分享）。`#mtstatebar` 旁加**`#mtstatebardtlcopy`** 小钮（`⧉ 复制状态`，挂 `#mtstatebar` 下沿独立位，`#mtstatebar`
hover 委托（R185 区）`mouseenter` 显 `#mtstatebardtl` 浮层时 copy 同步显（跑中 / 暂停 / 取消显 / 完成 · 未跑隐），点 `#mtstatebardtlcopy`
→ **`mtStateBarCopy`**（读 `window._mtLiveInfo` + `window._mtPaused`/`_mtAborted`/`_mtRunning` 拼「#music3 维护状态 · <ts>」+ 状态详情文本
（跑中 / 暂停 / 取消 + 第 i/N 轮 + 本轮回 +X + 本轮耗 Ys），`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制维护状
态详情」）——状态详情复制贴工单 / 记录维护日志，维护状态可留存 / 可分享，与 R169 详情复制 / R189 逐轮明细复制同「复制出口」语言。

**E2E**：`跑中（window._mtRunning=true+window._mtLiveInfo）→ #mtstatebar hover → #mtstatebardtl 显 + #mtstatebardtlcopy 显（跑中）+
点 copy → toast「已复制维护状态详情」；复位 → #mtstatebar hover → 「维护完成 / 未跑（灰）」+ copy 隐（完成 / 未跑不显 copy）`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r191_statecopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 678→680`，断点 `_整理后分类\摇滚民谣\草东没有派对\海浪.mp3`。

**坑**：① `#mtstatebardtlcopy` 挂 `#mtstatebar` 下沿独立位（`#mtstatebar` 后 `margin-top:2px`，非 `#mtstatebardtl` 内——R189 同坑纪律，
`#mtstatebardtl` `textContent` 重写不冲 copy，copy 独立挂 `#mtstatebar` 旁）② copy 跟**hover 态 + 跑维护态**（`#mtstatebar` `mouseenter`
显 `#mtstatebardtl` 浮层时，跑中 / 暂停 / 取消（`window._mtRunning`/`_mtPaused`/`_mtAborted` 任一）copy 显 `inline-block` / 完成 · 未跑
（都非）copy 隐 `none`——copy 显跟「跑维护态」非「完成 / 未跑」（完成 / 未跑无状态详情可复制，不显 copy），`mouseleave` 浮层 + copy 隐）③
`mtStateBarCopy`（读 `window._mtLiveInfo` + `window._mtAborted`/`_mtPaused`/`_mtRunning` 拼状态，取消 / 暂停 / 跑中 / 完成未跑四态同
`#mtstatebardtl` hover 文案逻辑，`#music3 维护状态 · <new Date().toLocaleString()>` 头 + 状态详情，`navigator.clipboard.writeText`
（`_copyFallback` `textarea` `execCommand` 降级）+ toast「已复制维护状态详情」，同 R169/R189 复制函数出口纪律）④ 与 R185 `#mtstatebardtl`
hover 详情**分工**（R185 hover 显状态详情看（`#mtstatebardtl` 浮层），R191 copy 复制状态详情文本留存 / 分享（`#mtstatebardtlcopy` 贴工单
/ 记录维护日志），看 + 复制双出口，维护状态可看可留存）⑤ 验收**函数级**（`window._mtRunning=true` + `window._mtLiveInfo` 置 + `#mtstatebar`
`dispatchEvent` `mouseenter` 验 `#mtstatebardtl` 显 + `#mtstatebardtlcopy` hover 态显 + 点 copy 验 toast「已复制维护状态详情」，复位
`window._mtRunning=false` + `#mtstatebar` `mouseenter` 验 `#mtstatebardtl`「维护完成 / 未跑（灰）」+ copy 隐，不真跑 `mtRun` 免 tick
污染 `runs`；copy 复制只验 toast 出口，真剪贴板内容 headless 不验）。

---

## 第206轮（前端 R192 · goal round169）：`#mtlivebadge` 完成态（`mtLiveBadgeDone`，R187）补复制出口（`#mtlivebadgedonecopy` 小钮，全库 `FULL_DONE` 完成态徽标 hover 时显复制小钮，复制「#music3 全库维护完成 · <ts> · 共 N 轮 · 耗时 Xs」到剪贴板，贴工单 / 记录维护日志，完成态可留存）

**完善性（完成态留存 / 分享免手抄）**：R187 `#mtlivebadge` 全库完成态徽标「已跑完 · 共 N 轮 · 耗时 Xs」绿，但**没复制出口**
（完成态文本要留存 / 贴工单得手动抄，`#mtlivebadgedonecopy` hover 完成态时顺手复制免手抄，完成态可留存 / 可分享）。`#mtlivebadge`
旁加**`#mtlivebadgedonecopy`** 小钮（`⧉ 复制完成`，`#mtlivebadge` 后 `margin-left:6px`），`mtLiveBadgeDone`（R187）改：显完成态
时 `#mtlivebadgedonecopy` 显 + `window._mtLiveDoneInfo={N, totalDur}` 存完成态信息，`mtLiveBadgeHide` 改隐 copy + 清
`window._mtLiveDoneInfo`，点 `#mtlivebadgedonecopy` → **`mtLiveBadgeDoneCopy`**（读 `window._mtLiveDoneInfo` 拼「#music3 全库
维护完成 · <ts> · 共 N 轮 · 耗时 Xs」，`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制全库维护完成详情
（共 N 轮 · 耗时 Xs）」）——完成态复制贴工单 / 记录维护日志，全库维护完成可留存 / 可分享，与 R169/R189/R191 复制出口同语言。

**E2E**：`mtLiveBadgeDone(5, 12.3) → #mtlivebadge 完成态 + #mtlivebadgedonecopy 显 + 点 copy → toast「已复制全库维护完成详情
（共 5 轮 · 耗时 12.3s）」；mtLiveBadgeHide() → copy 隐 + window._mtLiveDoneInfo=null + 点 copy → toast「无全库维护完成详情可
复制（先跑全库维护）」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r192_donecopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 680→682`，断点 `_整理后分类\摇滚民谣\赵雷\三里屯.mp3`。

**坑**：① `#mtlivebadgedonecopy` 挂 `#mtlivebadge` 旁独立位（`#mtlivebadge` 后 `margin-left:6px`，非 `#mtlivedetail` 内——`#mtlivedetail`
`textContent` 重写不冲 copy，copy 独立挂 `#mtlivebadge` 旁）② copy 跟**完成态**（`mtLiveBadgeDone` 显完成态时 `#mtlivebadgedonecopy`
`display='inline-block'` 显 + `window._mtLiveDoneInfo={N, totalDur}` 存完成态信息；`mtLiveBadgeHide` 隐 copy `display='none'` + 清
`window._mtLiveDoneInfo=null`——copy 只在完成态显，跑中每轮 `mtLiveBadge` 刷跑中态不显 copy，全库 `FULL_DONE` 跑完 `mtLiveBadgeDone`
才显，非完成态不显）③ `mtLiveBadgeDoneCopy`（读 `window._mtLiveDoneInfo` 拼完成态详情，`#music3 全库维护完成 · <new Date().toLocaleString()>
· 共 N 轮 · 耗时 Xs`，`navigator.clipboard.writeText`（`_copyFallback` `textarea` `execCommand` 降级）+ toast「已复制全库维护完成详情
（共 N 轮 · 耗时 Xs）」，`window._mtLiveDoneInfo` 空（`mtLiveBadgeHide` 清 / 未跑全库）toast「无全库维护完成详情可复制（先跑全库维护）」
`bad`，同 R169/R189/R191 复制函数空详情 toast 纪律）④ 与 R187 `#mtlivebadge` 完成态**分工**（R187 完成态徽标看，R192 copy 复制完成态
文本留存 / 分享，看 + 复制双出口，全库维护完成可看可留存）⑤ 验收**函数级**（`mtLiveBadgeDone(5, 12.3)` 直调验 `#mtlivebadge` 完成态
+ `#mtlivebadgedonecopy` 显 + 点 copy 验 toast「已复制全库维护完成详情（共 5 轮 · 耗时 12.3s）」，`mtLiveBadgeHide()` 验 copy 隐 +
`window._mtLiveDoneInfo` 空 + 点 copy 验 toast「无全库维护完成详情可复制」，不真跑 `mtRun` 全库免 tick 污染 `runs`；copy 复制只验
toast 出口，真剪贴板内容 headless 不验）。

---

## 第207轮（前端 R193 · goal round170）：`#mtkeyhint` 三键提示浮层补键盘快捷键实际触发记录（`#mtkeyhintdetail` 三键各带最近一次触发时间戳，`document` 键盘操作后更新 `window._mtKeyLog`，hover 逐键显「最近 <ts>」，键盘流使用节奏可追溯）

**完善性（键盘流使用节奏可追溯 / 可回忆）**：R186 `#mtkeyhint` 三键状态灯显可触 / 不可触，但**没显三键最近一次实际触发的时间
戳**（键盘流用过 `Space` 暂停 / `Esc` 取消 / `Enter` 跳双图后，`#mtkeyhintdetail` 逐键显「最近 `<ts>`」最近触发时间，看三键最近
用过的时机，键盘流使用节奏可追溯 / 可回忆）。`document` `keydown` 监听（R178/R179/R180 同 IIFE）三键操作后更新
`window._mtKeyLog={space:ts, esc:ts, enter:ts}`（`Esc`/`Enter`/`Space` 各操作后 `window._mtKeyLog.<key>=new Date().toLocaleTimeString()`），
`#mtkeyhint` hover 委托（R186 区）三键色点文案后补「最近 `<ts>`」/「未用过」（读 `window._mtKeyLog` 逐键显最近触发时间，没用过显
「未用过」）——hover 看三键最近用过的时机，键盘流使用节奏可追溯 / 可回忆。

**E2E**：`三键都没用 → #mtkeyhint hover → #mtkeyhintdetail 逐键显「未用过」；document 按 Esc → window._mtKeyLog.esc 更新（10:21:34）
→ hover 显「Esc 最近 10:21:34」+ Space/Enter 未用过`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r193_keylog.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 682→684`，断点 `_整理后分类\摇滚民谣\赵雷\纳兰.mp3`。

**坑**：① `window._mtKeyLog` 挂 `window`（`document` `keydown` 监听 IIFE 三键操作后更新 + 跨作用域读，同 R180 `window._mtPaused`
块级 `let` 作用外读坑——`document` 监听 / `#mtkeyhint` hover 委托（不同 IIFE）读必须挂 `window` 才跨作用域可读）② `Esc`/`Enter`/
`Space` 各键操作后更新（`if(!window._mtKeyLog){ window._mtKeyLog={}; } window._mtKeyLog.esc=new Date().toLocaleTimeString()`——惰性
初始化 `window._mtKeyLog`，各键独立存最近触发时间，`Esc` 区（R178）/ `Enter` 区（R179）/ `Space` 区（R180，暂停 / 续跑两分支后）各
加一行，三键独立记录不互覆写）③ `#mtkeyhint` hover 委托（R186 区 `_html` 拼三键色点 + 文案处）补「最近 <ts>」/「未用过」（`const
_kl=window._mtKeyLog||{}`，`_spT=_kl.space?('最近 '+_kl.space):'未用过'`，三键色点文案后补 `<br>` 折行逐键显最近触发时间，`d.innerHTML`
拼，headless 验 `innerHTML` 含「最近」/「未用过」）④ 与 R186 三键状态灯**分工**（R186 色点显三键当前可触 / 不可触 / 暂停（读
`window._mtRunning`/`_mtPaused`/`_mtAborted` 实时判），R193 逐键补最近触发时间戳（读 `window._mtKeyLog` 历史触发），色点 = 现在能按哪
键 + 时间戳 = 最近用过哪键何时，两路看键盘流使用节奏可追溯 / 可回忆）⑤ `toLocaleTimeString()` 显时:分:秒（`10:21:34`，不显日期
——三键触发时间当天节奏够用，`toLocaleTimeString` 非 `toLocaleString`，hover 逐键「最近 10:21:34」紧凑）⑥ 验收**函数级**（`window.
_mtKeyLog` 置 `null` + `#mtkeyhint` `dispatchEvent` `mouseenter` 验「未用过」，`document` `dispatchEvent` `keydown`（`key:'Escape'`
维护 tab 激活 + 焦点非输入框）验 `window._mtKeyLog.esc` 更新 + hover 显「Esc 最近 <ts>」+ `Space` 未用过，不真跑 `mtRun` 免 tick 污染
`runs`；三键操作各验各自 `window._mtKeyLog.<key>` 更新，`#mtkeyhintdetail` 逐键 headless 验 `innerHTML` 含「最近」/「未用过」）。

---

## 第208轮（前端 R194 · goal round171）：`#mtkeyhint` 三键提示浮层补三键最近触发顺序回放（`#mtkeyhintdetail` 逐键时间戳后补「触发顺序：Esc→Space→Enter」最近 N 次触发顺序串（读 `window._mtKeyLogOrder`（`document` 三键操作后 push 键名，保留最近 10 次顺序），hover 显最近触发顺序串，看三键使用顺序 / 习惯节奏，键盘流使用习惯可回放）

**完善性（键盘流使用习惯可回放）**：R193 `#mtkeyhintdetail` 逐键显最近一次触发时间戳，但**没显三键触发顺序 / 序列**（`Space`→`Enter`→
`Esc` 最近 N 次顺序串，`window._mtKeyLogOrder` 存最近 10 次三键触发顺序，hover `#mtkeyhintdetail` 逐键时间戳后补「触发顺序：Esc→Space→
Enter→…」（最近 N 次），看三键使用顺序 / 习惯节奏，键盘流使用习惯可回放）。`document` `keydown` 三键操作后 `window._mtKeyLogOrder.
push(keyName)`（保留最近 10 次顺序，`Esc`/`Enter`/`Space` 各操作后 push，超 10 次 `shift` 弃最早），`#mtkeyhint` hover 委托（R193
区）逐键时间戳后补「触发顺序：<最近 10 次串>」（读 `window._mtKeyLogOrder` `join('→')` 拼，无显「无触发顺序（未用过）」）——hover 看
三键使用顺序 / 习惯节奏，键盘流使用习惯可回放 / 可回忆。

**E2E**：`document 按 Esc→Space→Enter（三键 keydown）→ window._mtKeyLogOrder 更新 ['Esc','Space','Enter'] → #mtkeyhint hover →
#mtkeyhintdetail 逐键时间戳后显「触发顺序：Esc→Space→Enter」；window._mtKeyLogOrder=null → hover 显「无触发顺序（未用过）」`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r194_orderreplay.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 684→686`，断点 `_整理后分类\洛天依\洛天依\七月 - 0036PcMt3SIB17.mp3`。

**坑**：① `window._mtKeyLogOrder` 挂 `window`（`document` `keydown` 监听 IIFE 三键操作后 `push(keyName)` + 跨作用域读，同 R193
`window._mtKeyLog` 块级作用外读坑——`document` 监听 / `#mtkeyhint` hover 委托（不同 IIFE）读必须挂 `window` 才跨作用域可读）② 保留
最近 10 次顺序（`Esc`/`Enter`/`Space` 各操作后 `if(!window._mtKeyLogOrder){ window._mtKeyLogOrder=[]; } window._mtKeyLogOrder.push(
'Esc'|'Enter'|'Space'); if(window._mtKeyLogOrder.length>10){ window._mtKeyLogOrder.shift(); }`——惰性初始化 + `push` 尾追加 + 超 10
次 `shift` 头弃最早，保留最近 10 次触发顺序，`join('→')` 拼「Esc→Space→Enter→…」）③ **`Space` 记录移 `!window._mtRunning` return
前**（R194 坑：R193 `Space` 触发记录 `window._mtKeyLog.space` + `window._mtKeyLogOrder.push('Space')` 在 `document` `Space` 分支
`if(e.key===' '){ ... if(!window._mtRunning){ _toast; return; } ... }` 的 `return` 后——非跑维护中 `Space` 按下 `!window._mtRunning`
return，记录不执行（首验 `orderSet` 假，`Space` 没记进 `window._mtKeyLogOrder`）；改 `Space` 记录移到 `!window._mtRunning` return 前
（按下即记 Space，非跑维护中也记——`window._mtKeyLog.space` + `window._mtKeyLogOrder.push('Space')` 不依赖跑中，暂停 / 续跑逻辑才
需跑中，触发记录是「按过 Space」不管跑不跑，`!window._mtRunning` 才 `toast` + `return`）④ `#mtkeyhint` hover 委托（R193 区 `_html` 拼
三键色点 + 时间戳处）补「触发顺序：<最近 10 次串>」（`const _ko=window._mtKeyLogOrder||[]`，`_order=_ko.length?('触发顺序：'+_ko.
join('→')):'无触发顺序（未用过）'`，三键色点文案后补 `<br>` + `<span style="color:var(--dim)">` 触发顺序串（灰 `--dim` 弱显，逐键
时间戳后一行，`d.innerHTML` 拼，headless 验 `innerHTML` 含「触发顺序：Esc→Space→Enter」）⑤ 与 R193 逐键时间戳**分工**（R193 逐键显
最近一次触发时间戳「最近 10:21:34」单键最近，R194 触发顺序串「Esc→Space→Enter」多键序列，时间戳 = 各键最近 + 顺序串 = 多键使用节奏，
两路看键盘流使用习惯可追溯 / 可回放）⑥ 验收**函数级**（`document` `dispatchEvent` `keydown`（`key:'Escape'`/`' '`/`'Enter'` 维护 tab
激活 + 焦点非输入框）验 `window._mtKeyLogOrder` 更新 `['Esc','Space','Enter']` + `#mtkeyhint` `mouseenter` 验 `#mtkeyhintdetail`
含「触发顺序：Esc→Space→Enter」，`window._mtKeyLogOrder=null` + `#mtkeyhint` `mouseenter` 验含「无触发顺序（未用过）」，不真跑
`mtRun` 免 tick 污染 `runs`；`#mtkeyhintdetail` 触发顺序串 headless 验 `innerHTML` 含「触发顺序：Esc→Space→Enter」/「无触发顺序」）。

---

## 第209轮（前端 R195 · goal round172）：`#mtkeyhint` 三键提示浮层补触发顺序复制出口（`#mtkeyhintcopy` 小钮，hover `#mtkeyhintdetail` 显三键触发记录时同步显复制小钮，复制「#music3 键盘流触发记录 · <ts>」+ 三键最近触发时间戳 + 触发顺序串到剪贴板，贴工单 / 记录键盘流使用习惯，与 R169/R189/R191/R192 复制出口同语言）

**完善性（键盘流使用习惯留存 / 分享免手抄）**：R194 `#mtkeyhintdetail` 逐键时间戳 + 触发顺序串，但**没复制出口**（触发记录文本要
留存 / 贴工单得手动抄，`#mtkeyhintcopy` hover 三键触发记录时顺手复制免手抄，键盘流使用习惯可留存 / 可分享）。`#mtkeyhint` 旁加
**`#mtkeyhintcopy`** 小钮（`⧉ 复制触发记录`，挂 `#mtkeyhint` 旁独立位，非 `#mtkeyhintdetail` 内防 `d.innerHTML` 冲掉——R189/R191 同坑
纪律），`#mtkeyhint` hover 委托（R194 区）`mouseenter` 显 `#mtkeyhintdetail` 时 copy 同步显（有触发记录：`window._mtKeyLog` 三键任一
或 `window._mtKeyLogOrder` 非空）/ `mouseleave` 隐，点 `#mtkeyhintcopy` → **`mtKeyHintCopy`**（读 `window._mtKeyLog` +
`window._mtKeyLogOrder` 拼「#music3 键盘流触发记录 · <ts>」+ 三键最近触发时间戳（Space/Esc/Enter 各「最近 <ts>」/未用过）+ 触发顺序
串（最近 10 次 `join('→')`），`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制键盘流触发记录」）——键盘流使用
习惯复制贴工单 / 记录，使用习惯可留存 / 可分享，与 R169/R189/R191/R192 复制出口同语言。

**E2E**：`document 按 Esc→Space→Enter（更新 window._mtKeyLog/_mtKeyLogOrder）→ #mtkeyhint hover → #mtkeyhintdetail 显 + #mtkeyhintcopy
显（有触发记录）+ 点 copy → toast「已复制键盘流触发记录」；清 window._mtKeyLog/_mtKeyLogOrder → #mtkeyhint hover → #mtkeyhintcopy 隐
（无触发记录）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r195_keycopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 686→688`，断点 `_整理后分类\洛天依\洛天依\勾指起誓.mp3`。

**坑**：① `#mtkeyhintcopy` 挂 `#mtkeyhint` 旁独立位（`#mtkeyhint` 后 `inline-block`，非 `#mtkeyhintdetail` 内——R194 `#mtkeyhint` hover
委托 `d.innerHTML=_html` 重写 `#mtkeyhintdetail` 全 innerHTML，copy 钮若挂 `#mtkeyhintdetail` 内会被 `d.innerHTML` 冲掉，同 R189/R191
copy 挂旁独立位纪律）② copy 跟**触发记录**（`#mtkeyhint` `mouseenter` 显 `#mtkeyhintdetail` 时，`_hasRec=_kl.space||_kl.esc||_kl.enter||
_ko.length`（三键最近时间戳任一或触发顺序串非空）copy 显 `inline-block` / 无触发记录（`window._mtKeyLog` 三键全空 + `window._mtKeyLogOrder`
空）copy 隐 `none`——copy 显跟「有触发记录」，`mouseleave` 浮层 + copy 隐）③ `mtKeyHintCopy`（读 `window._mtKeyLog` + `window._mtKeyLogOrder`
拼触发记录，`#music3 键盘流触发记录 · <new Date().toLocaleString()>` 头 + 三键最近时间戳（Space/Esc/Enter 各「最近 <ts>」/「未用过」）
+ 触发顺序串（`_ko.length?('触发顺序：'+_ko.join('→')):'无触发顺序（未用过）'`），`navigator.clipboard.writeText`（`_copyFallback` `textarea`
`execCommand` 降级）+ toast「已复制键盘流触发记录」，无触发记录（三键全空 + 顺序串空）toast「无键盘流触发记录可复制（未用过三键）」
`bad`，同 R169/R189/R191/R192 复制函数空记录 toast 纪律）④ 与 R193 逐键时间戳 / R194 触发顺序串**分工**（R193 hover 逐键显最近时间戳
看，R194 hover 显触发顺序串看，R195 copy 复制触发记录文本留存 / 分享，看 + 复制双出口，键盘流使用习惯可看可留存）⑤ 验收**函数级**
（`document` `dispatchEvent` `keydown`（`key:'Escape'`/`' '`/`'Enter'` 维护 tab 激活 + 焦点非输入框）验 `window._mtKeyLog`/`_mtKeyLogOrder`
更新 + `#mtkeyhint` `dispatchEvent` `mouseenter` 验 `#mtkeyhintdetail` 显 + `#mtkeyhintcopy` hover 态显 + 点 copy 验 toast「已复制键盘流
触发记录」，清 `window._mtKeyLog`/`_mtKeyLogOrder` + `#mtkeyhint` `mouseenter` 验 `#mtkeyhintcopy` 隐，不真跑 `mtRun` 免 tick 污染
`runs`；copy 复制只验 toast 出口，真剪贴板内容 headless 不验）。

---

## 第210轮（前端 R196 · goal round173）：维护守护区加一键全复制（`#mtguardcopy` 小钮，一键复制维护守护区全部可复制内容：`#mtmetsum` 双指标逐轮明细 + `#mtstatebar` 状态详情 + `#mtlivebadge` 全库完成详情 + `#mtkeyhint` 键盘流触发记录，维护守护区数据一键全留存 / 全贴工单）

**简洁性（维护守护区数据一键全留存免逐个点）**：R188-R195 各数据点各有复制出口（双指标逐轮明细 / 状态详情 / 全库完成详情 / 键盘流触发
记录），但**维护守护区数据要全量留存 / 贴工单得逐个点各复制钮**（点 `#mtmetsumdetailcopy` 双指标 + `#mtstatebardtlcopy` 状态详情 +
`#mtlivebadgedonecopy` 全库完成 + `#mtkeyhintcopy` 键盘流，四个复制钮逐个点全复制）。`#mtkeyhintcopy` 旁加**`#mtguardcopy`** 小钮
（`⧉ 全复制`，`#mtkeyhintcopy` 后常驻位），点 `#mtguardcopy` → **`mtGuardCopy`**（拼「#music3 维护守护全记录 · <ts>」+ 四段：`[双指标逐
轮明细]`（读 `localStorage._mtRunHist`/`_mtRunDelta` 逐条拼近 N 次）+ `[状态详情]`（读 `window._mtLiveInfo` + `window._mtAborted`/
`_mtPaused`/`_mtRunning` 拼取消 / 暂停 / 跑中 / 完成未跑）+ `[全库完成详情]`（读 `window._mtLiveDoneInfo` 拼共 N 轮 · 耗时 Xs / 无）+
`[键盘流触发记录]`（读 `window._mtKeyLog`/`_mtKeyLogOrder` 拼三键最近时间戳 + 触发顺序串），`navigator.clipboard.writeText`（`_copyFallback`
降级）+ toast「已复制维护守护全记录（四段）」）——维护守护区数据一键全留存 / 全贴工单，免逐个点四个复制钮，与 R189/R191/R192/R195 单点
复制同「复制出口」语言但全量。

**E2E**：`写各数据源（localStorage._mtRunHist/_mtRunDelta + window._mtLiveInfo + window._mtLiveDoneInfo + window._mtKeyLog/_mtKeyLogOrder）
→ 点 #mtguardcopy → mtGuardCopy 拼四段 → toast「已复制维护守护全记录（四段）」（剪贴板 / 降级出口验 toast，四段出口）`（绿）；端点
**30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r196_guardcopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 688→690`，断点 `_整理后分类\洛天依\洛天依\心印 (Step on your heart) - 29163136.mp3`。

**坑**：① `#mtguardcopy` 挂 `#mtkeyhintcopy` 旁常驻位（`#mtkeyhintcopy` 后 `inline-block`，维护守护区数据全复制常驻入口，非 hover 态
控——四个单点复制钮（`#mtmetsumdetailcopy`/`#mtstatebardtlcopy`/`#mtlivebadgedonecopy`/`#mtkeyhintcopy`）各跟自身数据 / hover 态显隐，
`#mtguardcopy` 全复制常驻显（点即拼四段，不跟各段数据态——维护守护区全量入口常驻，点复制全量，各段空拼「无」不挡全复制）②
`mtGuardCopy` 拼四段（`#music3 维护守护全记录 · <ts>` 头 + `[双指标逐轮明细]`（`localStorage._mtRunHist`/`_mtRunDelta` 逐条近 N 次，
同 R189 `mtMetSumDetailCopy` 拼法倒序最新在上）+ `[状态详情]`（`window._mtLiveInfo` + 三标志拼取消 / 暂停 / 跑中 / 完成未跑，同 R191
`mtStateBarCopy` 拼法）+ `[全库完成详情]`（`window._mtLiveDoneInfo` 拼共 N 轮 · 耗时 Xs / 无（未全库跑完 / 已复位），同 R192
`mtLiveBadgeDoneCopy` 拼法）+ `[键盘流触发记录]`（`window._mtKeyLog`/`_mtKeyLogOrder` 拼三键最近时间戳 + 触发顺序串，同 R195
`mtKeyHintCopy` 拼法），四段各读各数据源，段标题 `[...]` 分隔，空段拼「无」不挡全复制）③ 与 R189/R191/R192/R195 单点复制**全量分工**
（R189 双指标逐轮明细单点 / R191 状态详情单点 / R192 全库完成详情单点 / R195 键盘流触发记录单点，R196 `#mtguardcopy` 全量一键复制四段
——单点复制看某段 + 全量复制维护守护区全留存 / 全贴工单，免逐个点四个单点钮）④ 各段空拼「无」（双指标无 `localStorage._mtRunHist`/
`_mtRunDelta` 空拼「近 0 次」段标题保留，状态无 `window._mtLiveInfo` 空 + 三标志全非拼「维护完成 / 未跑」，全库完成 `window._mtLiveDoneInfo`
空拼「无（未全库跑完 / 已复位）」，键盘流 `window._mtKeyLog`/`_mtKeyLogOrder` 空拼三键「未用过」+「无触发顺序（未用过）」——各段空不挡
全复制，`#mtguardcopy` 点即复制全量含空段，维护守护区全量结构完整）⑤ `#mtguardcopy` IIFE 绑（`mtKeyHintCopy` IIFE 后，`e.stopPropagation()`
+ `mtGuardCopy()`，同 R189/R191/R192/R195 复制钮 IIFE 绑纪律）⑥ 验收**函数级**（写各数据源（`localStorage._mtRunHist`/`_mtRunDelta` +
`window._mtLiveInfo`/`_mtLiveDoneInfo`/`_mtKeyLog`/`_mtKeyLogOrder`）+ 点 `#mtguardcopy` 验 toast「已复制维护守护全记录（四段）」，不真跑
`mtRun` 免 tick 污染 `runs`；`mtGuardCopy` 拼四段验 toast 出口，真剪贴板内容 headless 不验，各段拼逻辑同 R189/R191/R192/R195 单点复制
函数拼法）。

---

## 第211轮（前端 R197 · goal round174）：维护守护区四段数据快照可视化（`#mtguardsnap` 小钮，点截维护守护区全量四段当前状态成 `#mtguardsnapd` 浮层内联 SVG 快照——双指标逐轮明细柱状 / 状态详情色带 / 全库完成详情徽标 / 键盘流触发顺序条，一眼看维护守护区四段当前全貌）

**完善性（四段数据当前全貌可视化免文本逐段看）**：R196 `#mtguardcopy` 全复制是文本留存 / 贴工单，但**没可视化全貌**（四段数据当前
状态要文本看逐段，`#mtguardsnap` 截四段当前全貌内联 SVG 快照浮层（双指标逐轮柱 + 状态色带 + 完成徽标 + 键盘流顺序条），一眼看维护守护
区四段当前全貌，文本全量复制 + 可视化全貌双路）。`#mtguardcopy` 旁加**`#mtguardsnap`** 小钮（`▣ 快照`，`#mtguardcopy` 后常驻位）+
**`#mtguardsnapd`** SVG 浮层（`#mtguardsnap` 下沿，`position:absolute z-index:70`），点 `#mtguardsnap` → **`mtGuardSnap`**（读四段数据源
拼内联 SVG 快照：`[双指标逐轮]` 柱状（`localStorage._mtRunHist` 耗时柱绿 `--ok` + `localStorage._mtRunDelta` 补入柱橙 `#c4381f`，近 N 次
倒序最新在上）+ `[状态]` 色带（`window._mtAborted` 红 / `_mtPaused` 黄 / `_mtRunning` 绿 / 完成灰四态，同 R184 `#mtstatebar` 色带）
+ `[全库完成]` 徽标（`window._mtLiveDoneInfo` 绿徽标「共 N 轮 · 耗时 Xs」/ 无）+ `[键盘流顺序]` 顺序条（`window._mtKeyLogOrder` 最近 10
次三键色点序列，`Space` 黄 / `Esc` 红 / `Enter` 绿），显 `#mtguardsnapd` 浮层，6s 自动隐）——一眼看维护守护区四段当前全貌，文本全量
复制（R196）+ 可视化全貌双路，与 R158 双图区快照语言同。

**E2E**：`写各数据源（localStorage._mtRunHist/_mtRunDelta + window._mtRunning + window._mtLiveDoneInfo + window._mtKeyLogOrder）→ 点
#mtguardsnap → #mtguardsnapd 显内联 SVG（svg 含四段：双指标逐轮柱 rect + 状态色带 rect + 完成徽标 + 键盘流顺序条 rect）`（绿）；端点
**30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r197_guardsnap.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 690→692`，断点 `_整理后分类\洛天依\洛天依\梦里花 原版.mp3`。

**坑**：① `#mtguardsnap` 小钮挂 `#mtguardcopy` 旁常驻位（`#mtguardcopy` 后 `inline-block`，维护守护区四段快照可视化常驻入口，非 hover
态控——`#mtguardcopy` 全复制 + `#mtguardsnap` 全量快照双入口并排，点 `#mtguardsnap` 即截四段当前全貌内联 SVG，免文本逐段看）②
`mtGuardSnap` 拼内联 SVG 四段（`<svg width="360" height="150">`，`[双指标逐轮]` 柱状区（顶 40px，`_h` 耗时柱绿 `--ok` + `_b` 补入柱橙
`#c4381f` opacity .55 并列，近 N 次倒序，`_max` 归一化柱高 28px，空显「无双指标历史」）+ `[状态]` 色带（40-58px，`_sc` 四态色
`--bad`/`--warn`/`--ok`/`--line` 同 R184 `#mtstatebar` 色带逻辑，`rect` 横色带）+ `[全库完成]` 徽标（62-80px，`_done` 绿 `--ok` opacity
.15 徽标底 + 「共 N 轮 · 耗时 Xs」/ 无显「无（未全库跑完 / 已复位）」）+ `[键盘流顺序]` 顺序条（84-130px，`_ko` 最近 10 次三键色点
`rect` + 键名，`Space` 黄 `--warn` / `Esc` 红 `--bad` / `Enter` 绿 `--ok`，空显「未用过」）+ 时间戳（底 `new Date().toLocaleString()`），
`d.innerHTML=_svg` 拼，`d.style.display='block'`）③ `#mtguardsnapd` 挂 `#mtguardsnap` 下沿（`#mtguardsnap` `getBoundingClientRect` +
`position:absolute` 定位，`top:r.bottom+2`，`z-index:70` 高于 `#mtstatebar`/`#mtmetsumdetail` 浮层，`--bg2` 底 + `--line` 描边 + `box-shadow`
微浮，`white-space:nowrap` 内联 SVG 不折，`pointer-events:none` 不挡下层，6s 自动隐 `clearTimeout(window._mtGuardSnapT)` 重置——快照浮层
临时看全貌不常驻，`setTimeout` 6s 后隐，再点重计 6s）④ 与 R196 `#mtguardcopy` 全复制**双路**（R196 文本全量复制贴工单 / 记录维护守护
日志，R197 内联 SVG 四段快照看全貌——文本全量留存 + 可视化全貌双路，`#mtguardcopy` 旁 `#mtguardsnap` 并排，复制 + 快照双入口）⑤ 各段空
不挡快照（双指标空显「无双指标历史」，状态色带空显灰 `--line`（非跑中默认灰），全库完成空显「无（未全库跑完 / 已复位）」，键盘流空显
「未用过」——各段空快照仍拼全量结构，一眼看哪段有数据 / 哪段空，维护守护区全貌完整）⑥ 验收**函数级**（写各数据源（`localStorage.
_mtRunHist`/`_mtRunDelta` + `window._mtRunning`/`_mtLiveDoneInfo`/`_mtKeyLogOrder`）+ 点 `#mtguardsnap` 验 `#mtguardsnapd` 显 +
`innerHTML` 含 `<svg` + 四段（双指标柱 `var(--ok)` / 状态「状态」/ 完成「全库完成」/ 键盘流「键盘流顺序」），不真跑 `mtRun` 免 tick
污染 `runs`；`mtGuardSnap` 内联 SVG 四段 headless 验 `innerHTML` 含 `<svg` + 四段 `rect`/`text`，非真渲染 SVG 像素）。

---

## 第212轮（前端 R198 · goal round175）：维护守护区四段快照 PNG 导出（`#mtguardsnappng` 小钮，点 `#mtguardsnap` 四段内联 SVG 快照后 `#mtguardsnappng` 把 SVG 快照 `canvas` 转 PNG 下载「music3_维护守护全记录_快照_<ts>.png」，四段全貌快照可存档 / 可分享）

**完善性（四段全貌快照 PNG 留存 / 分享免手截）**：R197 `#mtguardsnap` 四段内联 SVG 快照浮层只看，**没 PNG 导出**（四段全貌快照
要存档 / 分享得手动截屏，`#mtguardsnappng` 把 `#mtguardsnapd` 内联 SVG `canvas` 转 PNG 下载，四段全貌快照可存档 / 可分享，维护守护
区全貌快照 PNG 留存，与 R158 双图区 PNG 快照（`#mtmetpng`）语言同）。`#mtguardsnap` 旁加**`#mtguardsnappng`** 小钮（`⬇ 快照PNG`，
`#mtguardsnap` 后常驻位），点 `#mtguardsnappng` → **`mtGuardSnapPng`**（读 `#mtguardsnapd` 内联 SVG（`#mtguardsnapd` 无 SVG 则先
`mtGuardSnap` 生成），`XMLSerializer` 序列化 SVG → `btoa` base64 → `Image` `onload` → `canvas`（`#f7f5f0` 浅色底，透明底贴工单看
不清，同 R158）`drawImage` → `toBlob` → `a[download]` 触发下载「music3_维护守护全记录_快照_<ts>.png」，`toBlob` 不可用降级复制
SVG 源码到剪贴板 + toast「已复制维护守护区四段快照 SVG（PNG 导出不可用降级）」）——四段全貌快照 PNG 存档 / 分享，维护守护区全貌
可留存，与 R158 双图区 PNG 快照同语言。

**E2E**：`写各数据源 → 点 #mtguardsnap（生成 #mtguardsnapd 内联 SVG）→ 点 #mtguardsnappng → mtGuardSnapPng 读 SVG canvas 转 PNG
→ toast「已下载维护守护区四段快照 PNG」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图
r198_snappng.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 692→694`，断点 `_整理后分类\洛天依\洛天依\纸短情长.mp3`。

**坑**：① `#mtguardsnappng` 小钮挂 `#mtguardsnap` 旁常驻位（`#mtguardsnap` 后 `inline-block`，维护守护区四段快照 PNG 导出常驻入口，
非 hover 态控——`#mtguardsnap` 快照看全貌 + `#mtguardsnappng` 快照 PNG 导出双入口并排，点 `#mtguardsnappng` 即把 `#mtguardsnapd`
内联 SVG 转 PNG 下载，免手截四段全貌快照）② `mtGuardSnapPng` 读 `#mtguardsnapd` 内联 SVG（`#mtguardsnapd` 无 SVG（未点过
`#mtguardsnap`）则先 `mtGuardSnap()` 生成，`d.querySelector('svg')` 取 SVG，无 `svg`（维护守护区数据全空 `mtGuardSnap` 仍拼空段
有 SVG，`svg` 空只 `d` 全空）toast「无维护守护区四段快照可导出（维护守护区数据空）」`bad`）③ SVG 转 PNG（`new XMLSerializer().
serializeToString(svg)` → `btoa(unescape(encodeURIComponent(svgStr)))` base64 → `Image` `src='data:image/svg+xml;base64,'` → `onload`
`canvas`（`#f7f5f0` 浅色底 fillRect，透明底贴工单看不清同 R158）`drawImage` → `toBlob('image/png')` → `a[download]='music3_维护守护
全记录_快照_<ts>.png'`（`ts` `new Date().toISOString().replace(/[:.]/g,'-')` 文件名安全）`a.click()` 触发下载 + `URL.revokeObjectURL`
4s 后清）④ `toBlob` 不可用降级（`_fallbackCopy` 复制 SVG 源码到剪贴板：`navigator.clipboard.writeText('#music3 维护守护全记录 快照
SVG\n'+svgStr)` + toast「已复制维护守护区四段快照 SVG（PNG 导出不可用降级）」，`canvas` / `toBlob` 沙箱不可用时 SVG 源码降级留存，
同 R158 `#mtmetpng` PNG 降级复制双图区 SVG 源码纪律）⑤ 与 R197 `#mtguardsnap` 快照**分工**（R197 内联 SVG 快照浮层看全貌（`#mtguardsnapd`
6s 自动隐），R198 PNG 导出存档 / 分享（`#mtguardsnappng` 下载 PNG），看全貌 + 全貌 PNG 留存双出口，维护守护区全貌可看可存）⑥ 验收
**函数级**（写各数据源 + 点 `#mtguardsnap` 生成 `#mtguardsnapd` 内联 SVG + 点 `#mtguardsnappng` 验 toast「已下载维护守护区四段快照
PNG」/ 降级「已复制维护守护区四段快照 SVG」，`canvas` / `toBlob` 下载 headless 验 toast 出口，真 PNG 文件下载不验，不真跑 `mtRun`
免 tick 污染 `runs`）。

---

## 第213轮（前端 R199 · goal round176）：维护 tab「维护守护」区加维护守护区能力 / 出口总览（`#mtguardpanel` 小钮，点显 `#mtguardpaneld` 浮层内联 SVG 总览面板——三键状态灯 / 触发记录 + 四段数据 + 各复制出口 + 快照 / PNG 出口 + 键盘三操作 / 状态同态 + 全库 ∞ / 完成态分块标位，维护守护区能力 / 出口全景图）

**简洁性（维护守护区能力 / 出口全景图免分散找）**：R198 `#mtguardsnappng` 四段快照 PNG 导出，但**维护守护区各能力 / 出口分散各
入口**（三键三操作 R178-R180 / 状态同态 R182-R184 / 双指标 R158 / 完成态 R187 / 键盘流 R193-R195 / 各复制钮 R189/R191/R192/R195 / 快照
R197 / PNG R198 分散各处，要全知维护守护区有哪些能力 / 出口得逐个找各入口，`#mtguardpanel` 点显总览面板浮层内联 SVG（各能力 / 出口
分块标位 + 简短说明），维护守护区能力 / 出口全景图，一眼知有哪些入口 / 能力，免分散找）。`#mtguardsnappng` 旁加**`#mtguardpanel`**
小钮（`▤ 总览`，`#mtguardsnappng` 后常驻位）+ **`#mtguardpaneld`** SVG 浮层（`#mtguardpanel` 下沿，`z-index:70`），点 `#mtguardpanel`
→ **`mtGuardPanel`**（拼内联 SVG 总览面板：`[三键状态灯 + 触发记录]`（R186 三键色点 + R193/R194 触发记录，实时读 `window._mtRunning`/
`_mtPaused`/`_mtAborted` + `window._mtKeyLog`/`_mtKeyLogOrder`）+ `[四段数据源]`（双指标逐轮 / 状态 / 全库完成 / 键盘流，实时读
`localStorage._mtRunHist` + 三标志 + `window._mtLiveDoneInfo` + `window._mtKeyLogOrder`）+ `[复制出口]`（R189/R191/R192/R195/R196
五个复制钮标位）+ `[快照/PNG出口]`（R197/R198/R199 三个标位）+ `[键盘三操作 + 状态同态]`（R178/R179/R180/R182/R183/R184 标位）+
`[全库 ∞ + 完成态]`（R166/R187 标位），显 `#mtguardpaneld` 浮层，8s 自动隐）——维护守护区能力 / 出口全景图，一眼知有哪些入口 /
能力，免分散找。

**E2E**：`点 #mtguardpanel → #mtguardpaneld 显内联 SVG 总览面板（svg 含六块：维护守护区能力 / 出口总览标题 + [三键状态灯 + 触发记录]
+ [四段数据源] + [复制出口] + [快照/PNG出口] + [键盘三操作 + 状态同态] + [全库∞+完成态]）`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r199_guardpanel.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 694→696`，断点 `_整理后分类\洛天依\洛天依\黑凤梨 - 000qPXNS3XF7fw.mp3`。

**坑**：① `#mtguardpanel` 小钮挂 `#mtguardsnappng` 旁常驻位（`#mtguardsnappng` 后 `inline-block`，维护守护区能力 / 出口总览常驻入口，
非 hover 态控——`#mtguardcopy`/`#mtguardsnap`/`#mtguardsnappng`/`#mtguardpanel` 四钮并排，全复制 + 快照 + 快照PNG + 总览四入口，
点 `#mtguardpanel` 即显总览面板全貌，免分散找各能力 / 出口）② `mtGuardPanel` 拼内联 SVG 总览六块（`<svg width="400" height="210">`，
`[三键状态灯 + 触发记录]` 块（`_dots` 三键色点实时读 `window._mtRunning`/`_mtPaused`/`_mtAborted` 判可触 / 不可触 / 暂停 + `window.
_mtKeyLogOrder` 触发记录最近 N 次）+ `[四段数据源]` 块（`_segs` 四段实时读 `localStorage._mtRunHist` 双指标 / 三标志状态 /
`window._mtLiveDoneInfo` 全库完成 / `window._mtKeyLogOrder` 键盘流）+ `[复制出口]` 块（`_copies` 五个复制钮标位 R189/R191/R192/
R195/R196）+ `[快照/PNG出口]` 块（`_snaps` 三个标位 R197/R198/R199）+ `[键盘三操作 + 状态同态]` 块（`_ops` 六个标位 R178/R179/
R180/R182/R183/R184）+ `[全库∞+完成态]` 块（`_full` 三个标位 R166/R187），`d.innerHTML=_svg` 拼，`d.style.display='block'`）③
`#mtguardpaneld` 挂 `#mtguardpanel` 下沿（`#mtguardpanel` `getBoundingClientRect` + `position:absolute` 定位，`top:r.bottom+2`，
`z-index:70` 高于 `#mtstatebar`/`#mtmetsumdetail`/`#mtguardsnapd` 浮层，`--bg2` 底 + `--line` 描边 + `box-shadow` 微浮，`white-space:
nowrap` 内联 SVG 不折，`pointer-events:none` 不挡下层，8s 自动隐 `clearTimeout(window._mtGuardPanelT)` 重置——总览面板临时看全貌不
常驻，`setTimeout` 8s 后隐，再点重计 8s）④ 各块实时读当前态（`[三键状态灯]` 色点随 `window._mtRunning`/`_mtPaused`/`_mtAborted` 实
时显可触 / 不可触 / 暂停，`[四段数据源]` 随 `localStorage._mtRunHist` + 三标志 + `window._mtLiveDoneInfo` + `window._mtKeyLogOrder`
实时显各段当前值，总览面板点即拼当前全貌非缓存旧态，与 R197 `mtGuardSnap` 实时读四段数据源同纪律）⑤ 与 R196 `#mtguardcopy` 全复制
/ R197 `#mtguardsnap` 快照 / R198 `#mtguardsnappng` 快照PNG**分工**（R196 文本全量复制贴工单 / R197 内联 SVG 快照看四段数据全貌 /
R198 PNG 导出存档 / R199 总览面板看能力 / 出口全景——复制 + 数据快照 + 快照PNG + 能力总览四入口，维护守护区全貌 / 全景 / 留存 /
分享全链路）⑥ 验收**函数级**（点 `#mtguardpanel` 验 `#mtguardpaneld` 显 + `innerHTML` 含 `<svg` + 六块标题（「维护守护区能力 / 出口
总览」/「三键状态灯 + 触发记录」/「四段数据源」/「复制出口」/「快照 / PNG 出口」/「键盘三操作 + 状态同态」/「全库 ∞ + 完成态」），
不真跑 `mtRun` 免 tick 污染 `runs`；`mtGuardPanel` 内联 SVG 六块 headless 验 `innerHTML` 含 `<svg` + 各块标题，非真渲染 SVG 像素）。

---

## 第214轮（前端 R200 · goal round177）：维护守护区能力 / 出口总览面板补导出（`#mtguardpanelpng` 小钮，点 `#mtguardpanel` 总览面板后 `#mtguardpanelpng` 把总览面板内联 SVG `canvas` 转 PNG 下载「music3_维护守护总览_<ts>.png」，维护守护区能力 / 出口全景图 PNG 存档 / 分享）

**完善性（能力 / 出口全景图 PNG 留存 / 分享免手截）**：R199 `#mtguardpanel` 总览面板内联 SVG 只看，**没 PNG 导出**（能力 / 出口
全景图要存档 / 分享得手动截屏，`#mtguardpanelpng` 把 `#mtguardpaneld` 内联 SVG `canvas` 转 PNG 下载，维护守护区能力 / 出口全景图
PNG 存档 / 分享，与 R158/R198 PNG 导出语言同）。`#mtguardpanel` 旁加**`#mtguardpanelpng`** 小钮（`⬇ 总览PNG`，`#mtguardpanel` 后
常驻位），点 `#mtguardpanelpng` → **`mtGuardPanelPng`**（读 `#mtguardpaneld` 内联 SVG（`#mtguardpaneld` 无 SVG 则先 `mtGuardPanel()`
生成），`XMLSerializer` 序列化 SVG → `btoa` base64 → `Image` `onload` → `canvas`（`#f7f5f0` 浅色底，透明底贴工单看不清，同 R158）
`drawImage` → `toBlob` → `a[download]` 触发下载「music3_维护守护总览_<ts>.png」，`toBlob` 不可用降级复制 SVG 源码到剪贴板 + toast
「已复制维护守护区总览 SVG（PNG 导出不可用降级）」）——能力 / 出口全景图 PNG 存档 / 分享，维护守护区总览可留存，与 R158/R198
PNG 导出同语言。

**E2E**：`点 #mtguardpanel（生成 #mtguardpaneld 内联 SVG）→ 点 #mtguardpanelpng → mtGuardPanelPng 读 SVG canvas 转 PNG →
toast「已下载维护守护区总览 PNG」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r200_panelpng.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 696→698`，断点 `_整理后分类\朴树\生如夏花.mp3`。

**坑**：① `#mtguardpanelpng` 小钮挂 `#mtguardpanel` 旁常驻位（`#mtguardpanel` 后 `inline-block`，维护守护区总览 PNG 导出常驻入口，
非 hover 态控——`#mtguardpanel` 总览面板看全貌 + `#mtguardpanelpng` 总览 PNG 导出双入口并排，点 `#mtguardpanelpng` 即把
`#mtguardpaneld` 内联 SVG 转 PNG 下载，免手截能力 / 出口全景图）② `mtGuardPanelPng` 读 `#mtguardpaneld` 内联 SVG（`#mtguardpaneld`
无 SVG（未点过 `#mtguardpanel`）则先 `mtGuardPanel()` 生成，`d.querySelector('svg')` 取 SVG，无 `svg` toast「无维护守护区总览可导出
（总览面板空）」`bad`，同 R198 `mtGuardSnapPng` 读 `#mtguardsnapd` 无 SVG 先 `mtGuardSnap()` 生成纪律）③ SVG 转 PNG（`new
XMLSerializer().serializeToString(svg)` → `btoa(unescape(encodeURIComponent(svgStr)))` base64 → `Image` `src='data:image/svg+xml;
base64,'` → `onload` `canvas`（`#f7f5f0` 浅色底 fillRect，透明底贴工单看不清同 R158）`drawImage` → `toBlob('image/png')` →
`a[download]='music3_维护守护总览_<ts>.png'`（`ts` `new Date().toISOString().replace(/[:.]/g,'-')` 文件名安全，与 R198 `music3_维护
守护全记录_快照_<ts>.png` 区分——总览面板 PNG 命名「维护守护总览」，四段数据快照 PNG 命名「维护守护全记录_快照」）④ `toBlob` 不可用
降级（`_fallbackCopy` 复制 SVG 源码到剪贴板：`navigator.clipboard.writeText('#music3 维护守护区总览 SVG\n'+svgStr)` + toast「已复
制维护守护区总览 SVG（PNG 导出不可用降级）」，`canvas` / `toBlob` 沙箱不可用时 SVG 源码降级留存，同 R158/R198 PNG 降级复制 SVG 源
码纪律）⑤ 与 R199 `#mtguardpanel` 总览面板**分工**（R199 内联 SVG 总览面板看能力 / 出口全景（`#mtguardpaneld` 8s 自动隐），R200
总览 PNG 导出存档 / 分享（`#mtguardpanelpng` 下载 PNG），看全景 + 全景 PNG 留存双出口，维护守护区总览可看可存）⑥ 与 R198
`#mtguardsnappng` 四段快照 PNG**区分**（R198 `#mtguardsnappng` 导四段数据快照 PNG「维护守护全记录_快照」，R200 `#mtguardpanelpng`
导能力 / 出口总览面板 PNG「维护守护总览」，两个 PNG 命名区分——数据快照（四段当前值）+ 能力总览（能力 / 出口分块）两类 PNG 全貌）⑦
验收**函数级**（点 `#mtguardpanel` 生成 `#mtguardpaneld` 内联 SVG + 点 `#mtguardpanelpng` 验 toast「已下载维护守护区总览 PNG」/
降级「已复制维护守护区总览 SVG」，`canvas` / `toBlob` 下载 headless 验 toast 出口，真 PNG 文件下载不验，不真跑 `mtRun` 免 tick 污染
`runs`）。

---

## 第215轮（前端 R201 · goal round178）：维护守护区总览面板补复制出口（`#mtguardpanelcopy` 小钮，点 `#mtguardpanel` 总览面板后 `#mtguardpanelcopy` 复制总览面板文本（能力 / 出口分块 + 各出口标位 + 三键状态 / 四段数据当前值）到剪贴板，维护守护区总览可文本留存 / 贴工单）

**完善性（总览文本留存 / 贴工单免手抄）**：R200 `#mtguardpanelpng` 总览 PNG 导出是图片存档 / 分享，但**没文本复制**（总览面板
能力 / 出口分块 + 各出口标位文本要贴工单得手动抄，`#mtguardpanelcopy` 复制总览面板文本到剪贴板，维护守护区总览可文本留存 / 贴工单，
PNG 图片 + 文本复制双路）。`#mtguardpanelpng` 旁加**`#mtguardpanelcopy`** 小钮（`⧉ 总览复制`，`#mtguardpanelpng` 后常驻位），点
`#mtguardpanelcopy` → **`mtGuardPanelCopy`**（读当前态拼总览文本：`[三键状态灯 + 触发记录]`（`Space`/`Esc`/`Enter` 可触 / 不可触
实时 + `window._mtKeyLog` 最近时间戳 + `window._mtKeyLogOrder` 触发顺序）+ `[四段数据源]`（双指标逐轮 `localStorage._mtRunHist` +
状态三标志 + `window._mtLiveDoneInfo` + 键盘流 `window._mtKeyLogOrder`）+ `[复制出口]`（R189/R191/R192/R195/R196 五出口标位）+
`[快照 / PNG 出口]`（R197/R198/R199/R200/R201 五出口标位）+ `[键盘三操作 + 状态同态]`（R178/R179/R180/R182/R183/R184 标位）+
`[全库 ∞ + 完成态]`（R166/R187 标位），`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制维护守护区总览文本」）
——总览文本复制贴工单 / 记录，维护守护区总览可文本留存，与 R169/R189/R191/R192/R195/R196 复制出口同语言。

**E2E**：`写各数据源 → 点 #mtguardpanelcopy → mtGuardPanelCopy 读当前态拼总览文本 → toast「已复制维护守护区总览文本」`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r201_panelcopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 698→700`，断点 `_整理后分类\林俊杰\加油.mp3`。

**坑**：① `#mtguardpanelcopy` 小钮挂 `#mtguardpanelpng` 旁常驻位（`#mtguardpanelpng` 后 `inline-block`，维护守护区总览文本复制常驻
入口，非 hover 态控——`#mtguardpanel` 总览面板 + `#mtguardpanelpng` 总览 PNG + `#mtguardpanelcopy` 总览文本复制三入口并排，总览看全
貌 + 总览 PNG 存档 + 总览文本复制贴工单三出口，维护守护区总览可看可存可贴）② `mtGuardPanelCopy` 读当前态拼总览文本（`#music3 维护
守护区总览 · <new Date().toLocaleString()>` 头 + `[三键状态灯 + 触发记录]`（`Space`/`Esc`/`Enter` 各「可触 / 不可触」实时读
`window._mtRunning`/`_mtPaused`/`_mtAborted` 判 + `window._mtKeyLog` 最近时间戳 + `window._mtKeyLogOrder` 触发顺序串）+ `[四段数据
源]`（双指标逐轮 `localStorage._mtRunHist` 近 N 次 + 状态三标志「已取消 / 已暂停 / 跑中 / 维护完成 · 未跑」+ `window._mtLiveDoneInfo`
全库完成「共 N 轮 · 耗时 Xs」/ 无 + 键盘流 `window._mtKeyLogOrder` 最近 N 次）+ `[复制出口]`（R189/R191/R192/R195/R196 五出口标位）
+ `[快照 / PNG 出口]`（R197/R198/R199/R200/R201 五出口标位）+ `[键盘三操作 + 状态同态]`（R178/R179/R180/R182/R183/R184 六标位）+
`[全库 ∞ + 完成态]`（R166/R187 三标位），`navigator.clipboard.writeText`（`_copyFallback` `textarea` `execCommand` 降级）+ toast
「已复制维护守护区总览文本」，读当前态非缓存旧态（点 `#mtguardpanelcopy` 即拼当前总览，与 R196 `mtGuardCopy` 读当前态同纪律）③
总览文本 vs 总览 PNG（R200 `#mtguardpanelpng` PNG 是图片存档 / 分享，R201 `#mtguardpanelcopy` 文本是贴工单 / 记录——PNG 图 + 文本
复制双路，总览可图片存 + 可文本贴工单，两类留存方式）④ 各出口标位含自身（`[复制出口]` R196 全复制 / `[快照 / PNG 出口]` R201 总览
复制 + R199 总览 + R198 快照PNG + R197 四段快照，`mtGuardPanelCopy` 标位全量含 R189/R191/R192/R195/R196/R197/R198/R199/R200/R201
十出口，总览文本自含全出口标位，复制总览文本即全出口清单留存）⑤ 与 R200 `#mtguardpanelpng` 总览 PNG**分工**（R200 总览 PNG 图片
存档 / 分享，R201 总览文本复制贴工单 / 记录，图片 + 文本双路总览留存，`#mtguardpanelpng` 旁 `#mtguardpanelcopy` 并排）⑥ 验收**函数
级**（写各数据源（`localStorage._mtRunHist`/`_mtRunDelta` + `window._mtRunning`/`_mtLiveDoneInfo`/`_mtKeyLog`/`_mtKeyLogOrder`）
+ 点 `#mtguardpanelcopy` 验 toast「已复制维护守护区总览文本」，剪贴板 / 降级只验 toast 出口，真剪贴板内容 headless 不验，不真跑
`mtRun` 免 tick 污染 `runs`；`mtGuardPanelCopy` 总览文本拼逻辑验 toast 出口，各段当前值读逻辑同 R196 `mtGuardCopy`）。

---

## 第216轮（前端 R202 · goal round179）：维护守护区能力 / 出口总览面板补折叠（`#mtguardpanelfold` 小钮，点 `#mtguardpanelfold` 折叠 / 展开 `#mtguardpaneld` 总览面板浮层（`_mtGuardPanelFold` 折叠标志，总览面板常驻可折叠省高，不 8s 自动隐，与 R159 折叠双图区语言同）

**简洁性（总览面板常驻可折叠省高免反复点重显）**：R199 `#mtguardpanel` 总览面板 `#mtguardpaneld` **8s 自动隐**（看全貌 8s 即消失，要
长看总览面板得反复点 `#mtguardpanel` 重显，`#mtguardpanelfold` 折叠 / 展开总览面板（`_mtGuardPanelFold` 标志切显 / 隐，总览面板常驻可
折叠省高，不 8s 自动隐，与 R159 `#mtmetfold` 折叠双图区语言同，总览面板可折叠省高常驻）。`#mtguardpanelcopy` 旁加**`#mtguardpanelfold`**
小钮（`▾ 折叠总览`，`#mtguardpanelcopy` 后常驻位），点 `#mtguardpanelfold` 切 **`window._mtGuardPanelFold`** 折叠标志（折叠态 `true`
时 `#mtguardpaneld` 隐 + `#mtguardpanelfold` 文案「▸ 展开总览」，展开态 `false` 时 `mtGuardPanel()` 显 `#mtguardpaneld` + 文案「▾ 折叠
总览」），`mtGuardPanel` 改：`_mtGuardPanelFold` 折叠时不 8s 自动隐（总览面板常驻），展开态才 8s 自动隐——总览面板可折叠省高常驻，
与 R159 折叠双图区语言同。

**E2E**：`点 #mtguardpanelfold（折叠，window._mtGuardPanelFold=true + #mtguardpaneld 隐 + 文案「▸ 展开总览」）→ 再点 #mtguardpanelfold
（展开，window._mtGuardPanelFold=false + #mtguardpaneld 显 + 文案「▾ 折叠总览」）`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r202_panelfold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 700→702`，断点 `_整理后分类\林俊杰\美人鱼.mp3`。

**坑**：① `#mtguardpanelfold` 小钮挂 `#mtguardpanelcopy` 旁常驻位（`#mtguardpanelcopy` 后 `inline-block`，维护守护区总览折叠常驻入口，
非 hover 态控——`#mtguardpanel` 总览 + `#mtguardpanelpng` 总览 PNG + `#mtguardpanelcopy` 总览复制 + `#mtguardpanelfold` 总览折叠四
入口并排，总览可看可存可贴可折叠省高，维护守护区总览全链路）② `window._mtGuardPanelFold` 挂 `window`（`#mtguardpanelfold` 点切
`true`/`false` + `mtGuardPanel` 读折叠态不 8s 自动隐，跨 IIFE 读必须挂 `window`，同 R180 `window._mtPaused` 块级作用外读坑）③
`mtGuardPanel` 改 8s 自动隐跟折叠态（`if(!window._mtGuardPanelFold){ clearTimeout(window._mtGuardPanelT); window._mtGuardPanelT=setTimeout(
function(){ d.style.display='none'; }, 8000); }`——折叠态 `window._mtGuardPanelFold===true` 不 8s 自动隐（总览面板常驻省高，用户手动
点 `#mtguardpanelfold` 折叠 / 展开控制），展开态 `false` 才 8s 自动隐（临时看全貌 8s 隐，同 R199 原行为），折叠态总览面板常驻不消失，
展开态临时看 8s 隐，两态分工）④ `#mtguardpanelfold` IIFE 绑切折叠（`if(window._mtGuardPanelFold===undefined){ window._mtGuardPanelFold=
false; } window._mtGuardPanelFold=!window._mtGuardPanelFold;` 惰性初始化 + 切，`c.textContent` 切「▸ 展开总览」/「▾ 折叠总览」，折叠态
`#mtguardpaneld` 隐 + `clearTimeout` 清 8s 定时（不残留自动隐），展开态 `mtGuardPanel()` 重拼当前总览 SVG 显（读当前态非缓存旧态），
toast「已折叠 / 已展开维护守护区总览面板」，同 R159 `#mtmetfold` 折叠双图区切 `display` 语言）⑤ 与 R199 `#mtguardpanel` 总览面板**分工**
（R199 `#mtguardpanel` 点显总览面板（8s 自动隐，临时看全貌），R202 `#mtguardpanelfold` 折叠 / 展开总览面板（`_mtGuardPanelFold` 折叠态
常驻省高 + 展开态 8s 自动隐），看全貌临时 + 总览常驻可折叠省高双路）⑥ 验收**函数级**（点 `#mtguardpanelfold` 验 `window._mtGuardPanelFold`
切 `true`（折叠）+ `#mtguardpaneld` 隐 + 文案「▸ 展开总览」，再点验 `window._mtGuardPanelFold` 切 `false`（展开）+ `#mtguardpaneld` 显 +
文案「▾ 折叠总览」，不真跑 `mtRun` 免 tick 污染 `runs`；`_mtGuardPanelFold` 折叠态不 8s 自动隐验折叠态 `#mtguardpaneld` 常驻显 10s 不隐
（`setTimeout` 不触），展开态 8s 自动隐不验（`setTimeout` 时序），验折叠 / 展开切标志 + 显隐 + 文案切换）。

---

## 第217轮（前端 R203 · goal round180）：维护 tab「维护守护」区加维护守护区折叠全浮层（`#mtguardfoldall` 小钮，点 `#mtguardfoldall` 折叠 / 展开维护守护区全部浮层（`#mtstatebardtl` 状态详情 / `#mtmetsumdetail` 逐轮明细 / `#mtkeyhintdetail` 三键提示 / `#mtguardsnapd` 四段快照 / `#mtguardpaneld` 总览面板，`_mtGuardFoldAll` 折叠标志，一键折叠 / 展开维护守护区全浮层省高，与 R159 折叠双图区 / R202 折叠总览面板语言同）

**简洁性（维护守护区全浮层一键折叠省高免逐个找）**：R202 `#mtguardpanelfold` 折叠总览面板，但**维护守护区各浮层要全折叠省高得逐
个找**（`#mtstatebardtl` 状态详情 / `#mtmetsumdetail` 逐轮明细 / `#mtkeyhintdetail` 三键提示 / `#mtguardsnapd` 四段快照 / `#mtguardpaneld`
总览面板，各浮层 hover / 点触发各自显隐，全折叠省高没总控钮，`#mtguardfoldall` 一键折叠 / 展开维护守护区全浮层（`_mtGuardFoldAll` 标志，
全浮层 `display` 切，窄屏 / 移动端省维护守护区高），与 R159 折叠双图区 / R202 折叠总览面板语言同）。`#mtguardpanelfold` 旁加**`#mtguardfoldall`**
小钮（`⊘ 折叠全浮层`，`#mtguardpanelfold` 后常驻位），点 `#mtguardfoldall` 切 **`window._mtGuardFoldAll`** 折叠标志（折叠态 `true` 隐维护
守护区全浮层（`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail`/`#mtguardsnapd`/`#mtguardpaneld` 全 `display:none`）+ 清 `#mtguardpaneld`
8s 定时 + `#mtguardsnapd` 6s 定时（不残留自动显）+ 文案「◎ 展开全浮层」，展开态 `false` 恢复（不强制显，各浮层自身 hover / 点触发才显）+
文案「⊘ 折叠全浮层」）——维护守护区全浮层一键折叠 / 展开省高，与 R159 / R202 折叠语言同。

**E2E**：`点 #mtguardfoldall（折叠，window._mtGuardFoldAll=true + 全浮层 #mtstatebardtl/#mtmetsumdetail/_mtkeyhintdetail/_mtguardsnapd/
_mtguardpaneld 隐 + 文案「◎ 展开全浮层」）→ 再点（展开，window._mtGuardFoldAll=false + 文案「⊘ 折叠全浮层」）`（绿）；端点 **30/0**、
JS undefined NONE、CSS 320/320、node 0、console 0、截图 r203_foldall.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 702→704`，断点 `_整理后分类\毛不易\城市傍晚.mp3`。

**坑**：① `#mtguardfoldall` 小钮挂 `#mtguardpanelfold` 旁常驻位（`#mtguardpanelfold` 后 `inline-block`，维护守护区全浮层折叠总控常驻入口，
非 hover 态控——`#mtguardpanel` 总览 + `#mtguardpanelpng` 总览 PNG + `#mtguardpanelcopy` 总览复制 + `#mtguardpanelfold` 总览折叠 +
`#mtguardfoldall` 全浮层折叠五入口并排，总览全链路 + 全浮层折叠省高总控，维护守护区能力 / 出口 / 折叠全链路）② `window._mtGuardFoldAll`
挂 `window`（`#mtguardfoldall` 点切 `true`/`false` + 跨 IIFE 读，同 R180 `window._mtPaused` / R202 `window._mtGuardPanelFold` 块级作用外
读坑）③ 全浮层 `display` 切（`_allFolds=['mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardsnapd','mtguardpaneld']`，折叠态全
`display:none` 隐省高，展开态**不强制显**（各浮层自身 hover / 点触发才显，仅清被折叠隐的残留，`if(_el.style.display==='none')` 不主动改
`display`，避免展开时强显所有浮层挡下层）④ 清自动隐定时（折叠态 `clearTimeout(window._mtGuardPanelT)` 清总览面板 8s 定时 + `clearTimeout(
window._mtGuardSnapT)` 清四段快照 6s 定时，不残留自动显——折叠省高时不触发 `#mtguardpaneld` 8s 自动显 / `#mtguardsnapd` 6s 自动显，
展开态各浮层自身触发才显，定时清了不残留）⑤ 与 R202 `#mtguardpanelfold` 折叠总览面板**分工**（R202 折叠单个总览面板 `#mtguardpaneld`
（`_mtGuardPanelFold`），R203 折叠维护守护区全浮层（`_mtGuardFoldAll`，含 `#mtguardpaneld` 总览 + `#mtstatebardtl` 状态详情 + `#mtmetsumdetail`
逐轮明细 + `#mtkeyhintdetail` 三键提示 + `#mtguardsnapd` 四段快照五浮层），折叠单面板 + 折叠全浮层总控双路，`#mtguardpanelfold` 折叠总览
面板 + `#mtguardfoldall` 折叠全浮层并排）⑥ 与 R159 `#mtmetfold` 折叠双图区 / R202 折叠总览面板**语言同**（`#mtmetfold` 折叠双图区
（`_mtMetFold`），R202 折叠总览面板（`_mtGuardPanelFold`），R203 折叠全浮层（`_mtGuardFoldAll`），三折叠各管各域——双图区 / 总览面板 /
全浮层总控，维护守护区 + 双图区全可折叠省高）⑦ 验收**函数级**（点 `#mtguardfoldall` 验 `window._mtGuardFoldAll` 切 `true`（折叠）+ 全
浮层（`_allFolds` 五浮层）`display:none` 隐 + 文案「◎ 展开全浮层」，再点验 `window._mtGuardFoldAll` 切 `false`（展开）+ 文案「⊘ 折叠全浮
层」，不真跑 `mtRun` 免 tick 污染 `runs`；全浮层折叠态 `display:none` 验五浮层全隐，展开态不验强显（各浮层自身触发，不验展开态各浮层
`display`））。

---

## 第218轮（前端 R204 · goal round181）：维护守护区全浮层折叠记忆（`_mtGuardFoldAll` 折叠标志存 `localStorage._mtGuardFoldAll`，刷新后恢复折叠态，维护守护区全浮层折叠态跨会话留存）

**完善性（全浮层折叠态跨会话留存免刷新复位）**：R203 `#mtguardfoldall` 全浮层折叠 `window._mtGuardFoldAll` 标志，但**刷新后丢**
（`window` 标志跨会话不持久，刷新后 `window._mtGuardFoldAll` 复位 `false` 展开态，全浮层折叠态不跨会话留存，`_mtGuardFoldAll` 存
`localStorage._mtGuardFoldAll`，刷新后恢复折叠 / 展开态，维护守护区全浮层折叠态跨会话留存，与 R159 双图区折叠 `localStorage._mtMetFold`
记忆语言同）。`#mtguardfoldall` IIFE（R203 区）改：`window._mtGuardFoldAll` 惰性初始化读 `localStorage._mtGuardFoldAll`（`'1'` 折叠态 /
`'0'` 展开态 / 无默认展开态），切后存 `localStorage._mtGuardFoldAll`，`#mtguardfoldall` 文案随初始折叠态（`localStorage._mtGuardFoldAll===
'1'` 显「◎ 展开全浮层」/ 否则「⊘ 折叠全浮层」），全浮层 `display` 随初始折叠态（折叠态隐全浮层）——维护守护区全浮层折叠态跨会话
留存，与 R159 双图区折叠记忆语言同。

**E2E**：`点 #mtguardfoldall（折叠）→ localStorage._mtGuardFoldAll='1'（折叠态存 localStorage 刷新恢复）；再点（展开）→
localStorage._mtGuardFoldAll='0'`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r204_foldmem.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 704→706`，断点 `_整理后分类\洛天依\Vsinger.mp3`。

**坑**：① `window._mtGuardFoldAll` 惰性初始化读 `localStorage._mtGuardFoldAll`（`#mtguardfoldall` IIFE 顶，`if(window._mtGuardFoldAll===
undefined){ let _init=false; try{ _init=(localStorage.getItem('_mtGuardFoldAll')==='1'); }catch(_){} window._mtGuardFoldAll=_init; }`
——刷新后 `window._mtGuardFoldAll` 未设（`undefined`）则读 `localStorage._mtGuardFoldAll` 恢复折叠 / 展开态，`'1'` 折叠 / `'0'` / 无展开，
`try/catch` `localStorage` 不可用（隐私模式 / 沙箱）降级 `false` 展开态，同 R159 `_mtMetFold` / R175 `_mtRunHist` `localStorage` 惰性
读降级纪律）② 切后存 `localStorage`（`#mtguardfoldall` 点切 `window._mtGuardFoldAll` 后 `try{ localStorage.setItem('_mtGuardFoldAll',
window._mtGuardFoldAll?'1':'0'); }catch(_){}`——折叠态 `true` 存 `'1'` / 展开态 `false` 存 `'0'`，`localStorage` 不可用降级不记（跨会话
不留存，当前会话 `window` 标志仍生效），`localStorage` 键族加 `_mtGuardFoldAll`（同 `_mtRunHist`/`_mtRunDelta`/`_mtMetFold`/`_mtAuto`
维护守护区折叠记忆）③ 初始折叠态同步（`#mtguardfoldall` IIFE 惰性初始化 `window._mtGuardFoldAll` 后：`c.textContent=window._mtGuardFoldAll?
'◎ 展开全浮层':'⊘ 折叠全浮层'`（文案随初始折叠态）+ `if(window._mtGuardFoldAll)` 全浮层 `display:none` 隐（刷新恢复折叠态隐全浮层，
`_allFolds` 五浮层 `#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail`/`#mtguardsnapd`/`#mtguardpaneld`）——刷新后恢复初始折叠态
（文案 + 全浮层 `display` 随 `localStorage._mtGuardFoldAll`，折叠态刷新隐全浮层省高，展开态刷新不隐）④ 与 R203 `#mtguardfoldall` 全浮层
折叠**分工**（R203 全浮层折叠 `window._mtGuardFoldAll` 当前会话切显 / 隐，R204 折叠记忆 `localStorage._mtGuardFoldAll` 跨会话留存——
当前会话折叠 + 跨会话记忆，`#mtguardfoldall` 折叠态存 `localStorage` 刷新恢复，免刷新复位展开态重折叠）⑤ 与 R159 `#mtmetfold` 双图区
折叠记忆 / R202 `#mtguardpanelfold` 总览面板折叠**语言同**（R159 `_mtMetFold` 存 `localStorage._mtMetFold` 双图区折叠记忆，R202 `_mtGuardPanelFold`
总览面板折叠当前会话（未存 `localStorage`），R204 `_mtGuardFoldAll` 存 `localStorage._mtGuardFoldAll` 全浮层折叠记忆，双图区折叠记忆
`localStorage` + 总览面板折叠 `window` + 全浮层折叠记忆 `localStorage`，各域折叠 / 记忆各管各）⑥ 验收**函数级**（清 `localStorage._mtGuardFoldAll`
+ 点 `#mtguardfoldall` 验 `window._mtGuardFoldAll` 切 `true`（折叠）+ `localStorage._mtGuardFoldAll` 存 `'1'`，再点验 `window._mtGuardFoldAll`
切 `false`（展开）+ `localStorage._mtGuardFoldAll` 存 `'0'`，不真跑 `mtRun` 免 tick 污染 `runs`；`localStorage` 存 / 读验 `getItem`/`setItem`
值，刷新恢复验 `localStorage` 值非真刷新 headless）⑦ 验收**函数级**（`localStorage._mtGuardFoldAll` 存 `'1'` / `'0'` 验折叠 / 展开切 `localStorage`
值，刷新恢复验 `localStorage` 读值非真刷新）。

---

## 第219轮（前端 R205 · goal round182）：维护守护区总览面板折叠记忆（`_mtGuardPanelFold` 总览面板折叠标志存 `localStorage._mtGuardPanelFold`，刷新后恢复折叠态，总览面板折叠态跨会话留存）

**完善性（总览面板折叠态跨会话留存免刷新复位）**：R202 `#mtguardpanelfold` 总览面板折叠 `window._mtGuardPanelFold` 标志，但**刷新后
丢**（`window` 标志跨会话不持久，刷新后 `window._mtGuardPanelFold` 复位 `false` 展开态，总览面板折叠态不跨会话留存，`_mtGuardPanelFold`
存 `localStorage._mtGuardPanelFold`，刷新后恢复总览面板折叠 / 展开态，总览面板折叠态跨会话留存，与 R159 双图区折叠 / R204 全浮层折叠
记忆语言同，三折叠域双图区 / 总览面板 / 全浮层全 `localStorage` 记忆）。`#mtguardpanelfold` IIFE（R202 区）改：`window._mtGuardPanelFold`
惰性初始化读 `localStorage._mtGuardPanelFold`（`'1'` 折叠态 / `'0'` 展开态 / 无默认展开态），切后存 `localStorage._mtGuardPanelFold`，
`#mtguardpanelfold` 文案 + `#mtguardpaneld` `display` 随初始折叠态（初始同步 IIFE）——总览面板折叠态跨会话留存，与 R159 / R204 折叠
记忆语言同。

**E2E**：`清 localStorage._mtGuardPanelFold → 点 #mtguardpanelfold（折叠）→ localStorage._mtGuardPanelFold='1'（折叠态存 localStorage
刷新恢复）；再点（展开）→ localStorage._mtGuardPanelFold='0'`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、
截图 r205_panelfoldmem.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 706→708`，断点 `_整理后分类\洛天依\凉凉.mp3`。

**坑**：① `window._mtGuardPanelFold` 惰性初始化读 `localStorage._mtGuardPanelFold`（`#mtguardpanelfold` IIFE 顶，`if(window._mtGuardPanelFold===
undefined){ let _init=false; try{ _init=(localStorage.getItem('_mtGuardPanelFold')==='1'); }catch(_){} window._mtGuardPanelFold=_init; }`
——刷新后 `window._mtGuardPanelFold` 未设（`undefined`）则读 `localStorage._mtGuardPanelFold` 恢复折叠 / 展开态，`'1'` 折叠 / `'0'` / 无
展开，`try/catch` `localStorage` 不可用（隐私模式 / 沙箱）降级 `false` 展开态，同 R204 `_mtGuardFoldAll` / R159 `_mtMetFold` `localStorage`
惰性读降级纪律）② 切后存 `localStorage`（`#mtguardpanelfold` 点切 `window._mtGuardPanelFold` 后 `try{ localStorage.setItem('_mtGuardPanelFold',
window._mtGuardPanelFold?'1':'0'); }catch(_){}`——折叠态 `true` 存 `'1'` / 展开态 `false` 存 `'0'`，`localStorage` 不可用降级不记（跨会话不
留存，当前会话 `window` 标志仍生效），`localStorage` 键族加 `_mtGuardPanelFold`（同 `_mtRunHist`/`_mtRunDelta`/`_mtMetFold`/`_mtAuto`/
`_mtGuardFoldAll` 维护守护区折叠记忆）③ 初始折叠态同步（`#mtguardpanelfold` IIFE 后另 IIFE：`if(window._mtGuardPanelFold===undefined)` 惰性
初始化读 `localStorage._mtGuardPanelFold` + `c.textContent=window._mtGuardPanelFold?'▸ 展开总览':'▾ 折叠总览'`（文案随初始折叠态）+
`if(d && window._mtGuardPanelFold){ d.style.display='none'; }`（刷新恢复折叠态隐 `#mtguardpaneld`，展开态刷新不隐 `#mtguardpaneld`）——
刷新后恢复初始折叠态（文案 + `#mtguardpaneld` `display` 随 `localStorage._mtGuardPanelFold`，折叠态刷新隐总览面板省高，展开态刷新不隐）④
与 R202 `#mtguardpanelfold` 总览面板折叠**分工**（R202 总览面板折叠 `window._mtGuardPanelFold` 当前会话切显 / 隐，R205 折叠记忆
`localStorage._mtGuardPanelFold` 跨会话留存——当前会话折叠 + 跨会话记忆，`#mtguardpanelfold` 折叠态存 `localStorage` 刷新恢复，免刷新
复位展开态重折叠）⑤ 与 R159 `#mtmetfold` 双图区折叠记忆 / R204 `#mtguardfoldall` 全浮层折叠记忆**语言同**（R159 `_mtMetFold` 存
`localStorage._mtMetFold` 双图区折叠记忆，R204 `_mtGuardFoldAll` 存 `localStorage._mtGuardFoldAll` 全浮层折叠记忆，R205 `_mtGuardPanelFold`
存 `localStorage._mtGuardPanelFold` 总览面板折叠记忆，三折叠域双图区 / 总览面板 / 全浮层全 `localStorage` 记忆，各域折叠 / 记忆各管各）⑥
`mtGuardPanel` 8s 自动隐跟折叠态（R202 已改 `if(!window._mtGuardPanelFold)` 才 8s 自动隐，R205 折叠态不 8s 自动隐跨会话留存，`localStorage.
_mtGuardPanelFold` 折叠态刷新 `mtGuardPanel` 不触发 8s 定时——`window._mtGuardPanelFold` 刷新惰性读 `localStorage` 恢复折叠态，`mtGuardPanel`
不 `mtGuardPanelT` 定时，总览面板折叠态跨会话省高不自动弹回）⑦ 验收**函数级**（清 `localStorage._mtGuardPanelFold` + 点 `#mtguardpanelfold`
验 `window._mtGuardPanelFold` 切 `true`（折叠）+ `localStorage._mtGuardPanelFold` 存 `'1'`，再点验 `window._mtGuardPanelFold` 切 `false`（展开）
+ `localStorage._mtGuardPanelFold` 存 `'0'`，不真跑 `mtRun` 免 tick 污染 `runs`；`localStorage` 存 / 读验 `getItem`/`setItem` 值，刷新恢复验
`localStorage` 读值非真刷新 headless，初始同步 IIFE 验 `#mtguardpanelfold` 文案 + `#mtguardpaneld` `display` 随初始折叠态）。

---

## 第220轮（前端 R206 · goal round183）：维护守护区全浮层 + 总览面板折叠一键联动（`#mtguardfoldall` 全浮层折叠态联动 `#mtguardpanelfold` 总览面板折叠——全浮层折叠时总览面板也折叠（`_mtGuardPanelFold` 强制 `true` + `#mtguardpanelfold` 文案切 + `localStorage` 存），全浮层展开时总览面板恢复自身 `localStorage` 折叠态，两折叠域联动一致省高）

**简洁性（全浮层折叠联动总览面板折叠免文案 / 标志不同步）**：R204 `#mtguardfoldall` 全浮层折叠（`_mtGuardFoldAll`）+ R205 `#mtguardpanelfold` 总览面板折叠
（`_mtGuardPanelFold`），但**两折叠域各管各**（全浮层折叠含 `#mtguardpaneld` 总览面板但 `#mtguardpanelfold` 标志 / 文案不同步——`#mtguardfoldall` 全浮层折叠后
`#mtguardpanelfold` 文案仍「▾ 折叠总览」未跟总览面板隐，两域标志不一致，全浮层折叠省高但总览面板文案 / 标志不同步误导，`#mtguardfoldall` 全浮层折叠联动总览面板
折叠：`_mtGuardFoldAll` 折叠态强制 `_mtGuardPanelFold=true` + `#mtguardpanelfold` 文案切「▸ 展开总览」+ `localStorage._mtGuardPanelFold` 存 `'1'`，全浮层展开态恢复
`_mtGuardPanelFold` 自身 `localStorage` 值（`'1'` 折叠 / `'0'` 展开），两折叠域联动一致省高，文案 / 标志全同步）。`#mtguardfoldall` IIFE（R204 区）折叠态切处加总览
面板折叠联动。

**E2E**：`#mtguardpanelfold 展开态（localStorage._mtGuardPanelFold='0'）→ 点 #mtguardfoldall 全浮层折叠 → window._mtGuardPanelFold=true（联动）+ #mtguardpanelfold
文案「▸ 展开总览」+ localStorage._mtGuardPanelFold='1'；再点 #mtguardfoldall 全浮层展开 → window._mtGuardPanelFold 恢复自身 localStorage 值`（绿）；端点 **30/0**、
JS undefined NONE、CSS 320/320、node 0、console 0、截图 r206_foldsync.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 708→710`，断点 `_整理后分类\洛天依\少年.mp3`。

**坑**：① `#mtguardfoldall` IIFE（R204 区）折叠态切处加总览面板折叠联动（`window._mtGuardFoldAll` 切 `true`（全浮层折叠）后：`if(window._mtGuardPanelFold===undefined)`
惰性读 `localStorage._mtGuardPanelFold` 初始化 + `window._mtGuardPanelFold=true`（全浮层折叠态强制总览面板折叠）+ `localStorage.setItem('_mtGuardPanelFold','1')`（联动
存 `localStorage`，刷新后总览面板也折叠态，与全浮层折叠态一致）+ `#mtguardpanelfold` 文案切「▸ 展开总览」（文案跟总览面板折叠态，两域标志 / 文案全同步）——全浮层折叠
时总览面板也折叠（`#mtguardpaneld` 总览面板 `display:none`（全浮层 `_allFolds` 含）+ `_mtGuardPanelFold=true`（标志）+ `#mtguardpanelfold` 文案（文案）+ `localStorage`（跨
会话），四路全同步，省高全折叠）② 展开态恢复总览面板自身 `localStorage` 折叠态（`window._mtGuardFoldAll` 切 `false`（全浮层展开）后：`_pfState=(localStorage.
getItem('_mtGuardPanelFold')==='1')` 读自身 `localStorage` 值，`window._mtGuardPanelFold=_pfState` 恢复（全浮层展开不强制展开总览面板，跟总览面板自身 `localStorage`
折叠态——全浮层展开但总览面板自身折叠态则总览面板仍折叠，全浮层展开 + 总览面板自身展开态则总览面板展开，总览面板折叠态归 `#mtguardpanelfold` 自己管，全浮层展开不
越权强制展开）+ `#mtguardpanelfold` 文案随 `_pfState`（`'1'` 折叠「▸ 展开总览」/ `'0'` 展开「▾ 折叠总览」）+ `#mtguardpaneld` `display` 随 `_pfState`（`'1'` 折叠
`none` / `'0'` 展开 `block`））③ 与 R204 `#mtguardfoldall` 全浮层折叠**分工**（R204 全浮层折叠 `_mtGuardFoldAll` 隐五浮层省高，R206 全浮层折叠联动总览面板折叠
`_mtGuardPanelFold` 同步标志 / 文案 / `localStorage`，全浮层折叠省高 + 总览面板标志 / 文案 / 记忆全同步，免全浮层折叠后 `#mtguardpanelfold` 文案 / 标志不同步误导）④
与 R205 `#mtguardpanelfold` 总览面板折叠记忆**分工**（R205 总览面板折叠记忆 `localStorage._mtGuardPanelFold` 跨会话留存，R206 全浮层折叠联动总览面板折叠
（全浮层折叠态强制 `localStorage._mtGuardPanelFold='1'`，全浮层展开态恢复自身 `localStorage` 值），全浮层折叠 + 总览面板记忆联动，两折叠域一致省高）⑤ 验收**函数级**（清
`localStorage._mtGuardPanelFold`/`_mtGuardFoldAll` + 点 `#mtguardfoldall` 全浮层折叠验 `window._mtGuardPanelFold` 切 `true`（联动）+ `#mtguardpanelfold` 文案「▸ 展开总览」
+ `localStorage._mtGuardPanelFold` 存 `'1'`，再点全浮层展开验 `window._mtGuardPanelFold` 恢复自身 `localStorage` 值（`'1'` 折叠），不真跑 `mtRun` 免 tick 污染 `runs`；
折叠联动验 `window._mtGuardPanelFold` / `#mtguardpanelfold` 文案 / `localStorage._mtGuardPanelFold` 三路全同步，展开态验 `window._mtGuardPanelFold` 恢复自身值）。

---

## 第221轮（前端 R207 · goal round184）：维护守护区三域折叠态总览（`#mtguardfoldstat` 小钮，点显 `#mtguardfoldstatd` 浮层内联 SVG 三域折叠态图——双图区（`_mtMetFold`）/ 总览面板（`_mtGuardPanelFold`）/ 全浮层（`_mtGuardFoldAll`）三域折叠 / 展开态色带 + `localStorage` 记忆标位，三域折叠态一眼全貌免逐点各折叠钮）

**简洁性（三域折叠态全貌免逐点各折叠钮）**：R206 全浮层 + 总览面板折叠联动，但**三域折叠态要全貌得逐个点各折叠钮**（双图区 `#mtmetfold` / 总览面板
`#mtguardpanelfold` / 全浮层 `#mtguardfoldall` 三域各折叠 / 展开态得逐点各折叠钮看，`#mtguardfoldstat` 点显三域折叠态内联 SVG 浮层（三域折叠 / 展开色带 +
`localStorage` 记忆标位），三域折叠态一眼全貌，免逐点各折叠钮）。`#mtguardfoldall` 旁加**`#mtguardfoldstat`** 小钮（`▣ 折叠总览`，`#mtguardfoldall` 后常驻位）
+ **`#mtguardfoldstatd`** SVG 浮层（`#mtguardfoldstat` 下沿，`z-index:70`），点 `#mtguardfoldstat` → **`mtGuardFoldStat`**（读三域折叠标志（`localStorage._mtMetFold`
双图区 / `localStorage._mtGuardPanelFold` 总览面板 / `localStorage._mtGuardFoldAll` 全浮层，`'1'` 折叠 / `'0'` 展开）拼内联 SVG 三域折叠态图：`[双图区 (#mtmetfold)]`
折叠色带黄 `--warn` / 展开色带绿 `--ok` + `localStorage _mtMetFold = 1/0` 标位 + `[总览面板 (#mtguardpanelfold)]` 同 + `[全浮层 (#mtguardfoldall)]` 同，显
`#mtguardfoldstatd` 浮层，8s 自动隐）——三域折叠态一眼全貌，免逐点各折叠钮，与 R197 四段快照 / R199 总览面板语言同。

**E2E**：`设 localStorage._mtMetFold='1'（双图区折叠）/ _mtGuardPanelFold='0'（总览展开）/ _mtGuardFoldAll='1'（全浮层折叠）→ 点 #mtguardfoldstat → #mtguardfoldstatd
显内联 SVG 三域折叠态图（svg 含维护守护区三域折叠态总览标题 + 双图区 / 总览面板 / 全浮层三域折叠 / 展开色带 + localStorage 记忆标位）`（绿）；端点 **30/0**、
JS undefined NONE、CSS 320/320、node 0、console 0、截图 r207_foldstat.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 710→712`，断点 `_整理后分类\洛天依\权御天下 - 001xZXiW4aAhkL (1).mp3`。

**坑**：① `#mtguardfoldstat` 小钮挂 `#mtguardfoldall` 旁常驻位（`#mtguardfoldall` 后 `inline-block`，维护守护区三域折叠态总览常驻入口，非 hover 态控——`#mtguardfoldall`
全浮层折叠 + `#mtguardfoldstat` 三域折叠态总览双入口并排，全浮层折叠省高 + 三域折叠态全貌，维护守护区折叠域全貌 / 省高双路）② `mtGuardFoldStat` 读三域 `localStorage`
折叠记忆拼内联 SVG（`_metFold/_pfFold/_allFold` 各域读 `localStorage._mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll`（`'1'` 折叠 / `'0'` / 无展开，`try/catch` 降级 `false`
展开态，同 R204/R205 `localStorage` 惰性读纪律），拼 `<svg width="340" height="140">`：`[双图区 (#mtmetfold)]` 行（域标签 + 折叠色带 `rect`（折叠 `--warn` 黄 / 展开
`--ok` 绿）+ 「折叠 / 展开」文案 + `localStorage _mtMetFold = 1/0` 记忆标位）+ `[总览面板 (#mtguardpanelfold)]` 行（同色带 + `localStorage _mtGuardPanelFold` 标位）+
`[全浮层 (#mtguardfoldall)]` 行（同色带 + `localStorage _mtGuardFoldAll` 标位），三域各 34px 行高，色带 120px 宽 `rect` 横色带（同 R184 `#mtstatebar` 色带语言），
`d.innerHTML=_svg` 拼，`d.style.display='block'`）③ `#mtguardfoldstatd` 挂 `#mtguardfoldstat` 下沿（`#mtguardfoldstat` `getBoundingClientRect` + `position:absolute`
定位，`top:r.bottom+2`，`z-index:70` 高于 `#mtstatebar`/`#mtmetsumdetail`/`#mtguardsnapd`/`#mtguardpaneld` 浮层，`--bg2` 底 + `--line` 描边 + `box-shadow` 微浮，
`white-space:nowrap` 内联 SVG 不折，`pointer-events:none` 不挡下层，8s 自动隐 `clearTimeout(window._mtGuardFoldStatT)` 重置——三域折叠态总览临时看全貌不常驻，
`setTimeout` 8s 后隐，再点重计 8s，同 R197 `mtGuardSnap` / R199 `mtGuardPanel` 8s 自动隐纪律）④ 三域 `localStorage` 记忆读非 `window` 实时标志（`mtGuardFoldStat`
读 `localStorage._mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll` 折叠记忆（跨会话留存态），非 `window._mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll` 实时标志
（当前会话态），三域折叠态总览看 `localStorage` 记忆全貌（刷新后三域折叠态），与 R205/R204 `localStorage` 惰性读同纪律——三域折叠态总览标位是 `localStorage`
记忆值非实时标志值）⑤ 与 R206 全浮层 + 总览面板折叠联动**分工**（R206 全浮层折叠联动总览面板折叠（`_mtGuardFoldAll` 折叠态强制 `_mtGuardPanelFold=true`），
R207 三域折叠态总览看全貌（双图区 / 总览面板 / 全浮层三域 `localStorage` 记忆折叠态色带 + 标位），折叠联动 + 折叠态全貌双路，`#mtguardfoldall` 折叠省高 +
`#mtguardfoldstat` 三域折叠态全貌）⑥ 与 R197 `mtGuardSnap` 四段快照 / R199 `mtGuardPanel` 总览面板**语言同**（R197 四段数据快照内联 SVG（双指标 / 状态 / 完成 /
键盘流），R199 能力 / 出口总览内联 SVG（六块分块标位），R207 三域折叠态总览内联 SVG（三域折叠 / 展开色带 + `localStorage` 记忆标位），三内联 SVG 总览语言同，
各管各域——数据 / 能力 / 折叠三总览）⑦ 验收**函数级**（设 `localStorage._mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll` 三域折叠记忆值 + 点 `#mtguardfoldstat`
验 `#mtguardfoldstatd` 显 + `innerHTML` 含 `<svg` + 三域名（「双图区」/「总览面板」/「全浮层」）+ 标题（「维护守护区三域折叠态总览」）+ `localStorage` 标位，不真跑
`mtRun` 免 tick 污染 `runs`；`mtGuardFoldStat` 内联 SVG 三域 headless 验 `innerHTML` 含 `<svg` + 三域名 + 色带 + `localStorage` 标位，非真渲染 SVG 像素）。

---

## 第222轮（前端 R208 · goal round185）：维护守护区三域折叠态总览补 PNG 导出 + 复制出口（`#mtguardfoldstatpng` / `#mtguardfoldstatcopy` 小钮，点 `#mtguardfoldstat` 三域折叠态总览后 `#mtguardfoldstatpng` 把三域折叠态 SVG `canvas` 转 PNG 下载「music3_维护守护三域折叠态_<ts>.png」，`#mtguardfoldstatcopy` 复制三域折叠态文本（三域折叠 / 展开 + `localStorage` 记忆值）到剪贴板，三域折叠态 PNG 存档 / 文本贴工单）

**完善性（三域折叠态全貌 PNG 存档 + 文本贴工单免手截 / 手抄）**：R207 `#mtguardfoldstat` 三域折叠态总览内联 SVG 只看，**没 PNG 导出 / 文本复制**（三域
折叠态全貌要存档 / 分享得手动截屏 / 抄，`#mtguardfoldstatpng` 转 PNG 下载 + `#mtguardfoldstatcopy` 文本复制，三域折叠态 PNG 存档 + 文本贴工单双出口，
与 R158/R198/R200 PNG 导出 + R196/R201 复制出口语言同）。`#mtguardfoldstat` 旁加**`#mtguardfoldstatpng`**（`⬇ 折叠态PNG`，`#mtguardfoldstat` 后）+
**`#mtguardfoldstatcopy`**（`⧉ 折叠态复制`，`#mtguardfoldstatpng` 后），点 `#mtguardfoldstatpng` → **`mtGuardFoldStatPng`**（读 `#mtguardfoldstatd` 内联
SVG（无则先 `mtGuardFoldStat()` 生成），`canvas` 转 PNG 下载「music3_维护守护三域折叠态_<ts>.png」，`toBlob` 不可用降级复制 SVG 源码 + toast），点
`#mtguardfoldstatcopy` → **`mtGuardFoldStatCopy`**（读三域 `localStorage` 折叠记忆（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`）拼三域折叠态文本
（`[双图区]`/`[总览面板]`/`[全浮层]` 各「折叠 / 展开」+ `localStorage` 记忆值）到剪贴板，`navigator.clipboard.writeText` 降级 + toast「已复制三域折叠态
文本」）——三域折叠态 PNG 存档 / 文本贴工单双出口，与 R158/R198/R200 PNG 导出 + R196/R201 复制出口语言同。

**E2E**：`设三域 localStorage 折叠记忆 → 点 #mtguardfoldstat（生成 #mtguardfoldstatd 内联 SVG）→ 点 #mtguardfoldstatpng → toast「已下载三域折叠态
PNG」；点 #mtguardfoldstatcopy → toast「已复制三域折叠态文本」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图
r208_foldstatpncopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 712→714`，断点 `_整理后分类\洛天依\粉丝.mp3`。

**坑**：① `#mtguardfoldstatpng`/`#mtguardfoldstatcopy` 小钮挂 `#mtguardfoldstat` 旁常驻位（`#mtguardfoldstat` 后，`#mtguardfoldstatpng` 再后
`#mtguardfoldstatcopy`，三域折叠态总览 PNG 导出 + 文本复制常驻入口，非 hover 态控——`#mtguardfoldstat` 三域折叠态总览看全貌 + `#mtguardfoldstatpng`
折叠态 PNG 存档 + `#mtguardfoldstatcopy` 折叠态文本贴工单三入口并排，三域折叠态可看可存可贴）② `mtGuardFoldStatPng` 读 `#mtguardfoldstatd` 内联 SVG
（`#mtguardfoldstatd` 无 SVG（未点过 `#mtguardfoldstat`）则先 `mtGuardFoldStat()` 生成，`d.querySelector('svg')` 取 SVG，无 `svg` toast「无三域折叠态
总览可导出（折叠态总览空）」`bad`，同 R198 `mtGuardSnapPng` 读 `#mtguardsnapd` 无 SVG 先 `mtGuardSnap()` 生成纪律）③ SVG 转 PNG（`new XMLSerializer().
serializeToString(svg)` → `btoa(unescape(encodeURIComponent(svgStr)))` base64 → `Image` `onload` `canvas`（`#f7f5f0` 浅色底 fillRect，透明底贴工单看不清
同 R158）`drawImage` → `toBlob('image/png')` → `a[download]='music3_维护守护三域折叠态_<ts>.png'`（`ts` `new Date().toISOString().replace(/[:.]/g,'-')`
文件名安全，与 R198 `music3_维护守护全记录_快照_<ts>.png` / R200 `music3_维护守护总览_<ts>.png` 区分——三域折叠态 PNG 命名「维护守护三域折叠态」）④
`toBlob` 不可用降级（`_fallbackCopy` 复制 SVG 源码到剪贴板 + toast「已复制三域折叠态 SVG（PNG 导出不可用降级）」，`canvas` / `toBlob` 沙箱不可用时
SVG 源码降级留存，同 R158/R198/R200 PNG 降级复制 SVG 源码纪律）⑤ `mtGuardFoldStatCopy` 读三域 `localStorage` 折叠记忆拼文本（`#music3 三域折叠态总览
· <new Date().toLocaleString()>` 头 + `[双图区 #mtmetfold] · 折叠 / 展开 · localStorage _mtMetFold=1/0` + `[总览面板 #mtguardpanelfold] · 折叠 / 展开 ·
localStorage _mtGuardPanelFold=1/0` + `[全浮层 #mtguardfoldall] · 折叠 / 展开 · localStorage _mtGuardFoldAll=1/0`，读 `localStorage` 记忆值（`'1'` 折叠 /
`'0'` / 无展开，`try/catch` 降级 `false` 展开态）非 `window` 实时标志，同 R207 `mtGuardFoldStat` 三域 `localStorage` 记忆读纪律，`navigator.clipboard.
writeText`（`_copyFallback` 降级）+ toast「已复制三域折叠态文本」）⑥ 与 R207 `#mtguardfoldstat` 三域折叠态总览**分工**（R207 内联 SVG 三域折叠态总览看
全貌（`#mtguardfoldstatd` 8s 自动隐），R208 折叠态 PNG 导出 + 文本复制双出口（`#mtguardfoldstatpng` 下载 PNG 存档 / 分享 + `#mtguardfoldstatcopy` 文本
贴工单），看全貌 + 全貌 PNG / 文本留存双路，三域折叠态可看可存可贴）⑦ 与 R158 `#mtmetpng` / R198 `#mtguardsnappng` / R200 `#mtguardpanelpng` PNG 导出
**语言同**（各 PNG 导出读各内联 SVG `canvas` 转 PNG 下载，`toBlob` 不可用降级复制 SVG 源码，三域折叠态 PNG 同语言）⑧ 与 R196 `#mtguardcopy` / R201
`#mtguardpanelcopy` 复制出口**语言同**（各文本复制读各数据源拼文本到剪贴板，`navigator.clipboard.writeText` 降级，三域折叠态文本复制同语言）⑨ 验收
**函数级**（设三域 `localStorage` 折叠记忆 + 点 `#mtguardfoldstat` 生成 `#mtguardfoldstatd` 内联 SVG + 点 `#mtguardfoldstatpng` 验 toast「已下载三域折叠态
PNG」/ 降级「已复制三域折叠态 SVG」+ 点 `#mtguardfoldstatcopy` 验 toast「已复制三域折叠态文本」，`canvas` / `toBlob` 下载 / 剪贴板 headless 验 toast 出口，
真 PNG / 剪贴板内容不验，不真跑 `mtRun` 免 tick 污染 `runs`）。

---

## 第223轮（前端 R209 · goal round186）：维护 tab「维护守护」区加维护守护区折叠全链路总控（`#mtguardfoldctl` 小钮，点显 `#mtguardfoldctld` 浮层内联折叠全链路面板——三域折叠钮（`#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`）+ 折叠联动（R206 全浮层 + 总览面板）+ 折叠记忆（R204/R205 `localStorage`）+ 三域折叠态总览（R207）+ 折叠态 PNG / 文本（R208）全折叠出口一张折叠全链路图，折叠域能力 / 出口全景图）

**简洁性（折叠域能力 / 出口全景图免分散找）**：R208 `#mtguardfoldstatcopy` 三域折叠态文本复制，但**维护守护区折叠域各出口分散各入口**（三域
折叠钮 R159/R202/R203 / 折叠联动 R206 / 折叠记忆 R204/R205 / 三域折叠态总览 R207 / 折叠态 PNG / 文本 R208 分散各处，要全知折叠域有哪些出口得逐个找，
`#mtguardfoldctl` 点显折叠全链路面板浮层（内联 SVG 全折叠出口分块标位），折叠域能力 / 出口全景图，一眼知折叠域有哪些出口，免分散找，与 R199 总览
面板语言同）。`#mtguardfoldstatcopy` 旁加**`#mtguardfoldctl`** 小钮（`▤ 折叠全链路`，`#mtguardfoldstatcopy` 后常驻位）+ **`#mtguardfoldctld`** SVG
浮层（`#mtguardfoldctl` 下沿，`z-index:70`），点 `#mtguardfoldctl` → **`mtGuardFoldCtl`**（拼内联 SVG 折叠全链路面板：`[三域折叠钮]`（`#mtmetfold`
双图区 R159 / `#mtguardpanelfold` 总览面板 R202 / `#mtguardfoldall` 全浮层 R203 标位）+ `[折叠联动 (R206)]`（全浮层折叠态强制总览面板折叠
`_mtGuardFoldAll→_mtGuardPanelFold` + 展开态恢复自身 `localStorage` 值标位）+ `[折叠记忆 (R204/R205)]`（`localStorage._mtGuardFoldAll` 全浮层 /
`localStorage._mtGuardPanelFold` 总览面板 / `localStorage._mtMetFold` 双图区记忆标位）+ `[三域折叠态总览 (R207)]`（`#mtguardfoldstat` 三域折叠态 SVG
+ `#mtguardfoldstatd` 内联 SVG 色带标位）+ `[折叠态 PNG / 文本 (R208)]`（`#mtguardfoldstatpng` PNG 导出 + `#mtguardfoldstatcopy` 文本复制标位），
显 `#mtguardfoldctld` 浮层，8s 自动隐）——折叠域能力 / 出口全景图，一眼知折叠域有哪些出口，免分散找，与 R199 总览面板语言同。

**E2E**：`点 #mtguardfoldctl → #mtguardfoldctld 显内联 SVG 折叠全链路面板（svg 含五块：维护守护区折叠全链路总控标题 + [三域折叠钮] +
[折叠联动 (R206)] + [折叠记忆 (R204/R205)] + [三域折叠态总览 (R207)] + [折叠态 PNG / 文本 (R208)]）`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r209_foldctl.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 714→716`，断点 `_整理后分类\洛天依\霜雪千年 - 001mzBxY4UVcAH.mp3`。

**坑**：① `#mtguardfoldctl` 小钮挂 `#mtguardfoldstatcopy` 旁常驻位（`#mtguardfoldstatcopy` 后 `inline-block`，维护守护区折叠域全链路总控常驻入口，
非 hover 态控——`#mtguardfoldstat` 三域折叠态总览 + `#mtguardfoldstatpng` 折叠态 PNG + `#mtguardfoldstatcopy` 折叠态复制 + `#mtguardfoldctl` 折叠
全链路四入口并排，三域折叠态看全貌 + PNG 存档 + 文本复制 + 全链路总控，折叠域全貌 / 留存 / 全景全链路）② `mtGuardFoldCtl` 拼内联 SVG 折叠全链路五块
（`<svg width="400" height="180">`，`[三域折叠钮]` 块（`_fbtns` 三个折叠钮标位 `#mtmetfold` 双图区 R159 / `#mtguardpanelfold` 总览面板 R202 /
`#mtguardfoldall` 全浮层 R203）+ `[折叠联动 (R206)]` 块（全浮层折叠态强制总览面板折叠 `_mtGuardFoldAll→_mtGuardPanelFold` + 展开态恢复自身
`localStorage` 值标位）+ `[折叠记忆 (R204/R205)]` 块（`localStorage._mtGuardFoldAll` 全浮层 / `localStorage._mtGuardPanelFold` 总览面板 /
`localStorage._mtMetFold` 双图区三域记忆标位）+ `[三域折叠态总览 (R207)]` 块（`#mtguardfoldstat` 三域折叠态 SVG + `#mtguardfoldstatd` 内联 SVG
色带标位）+ `[折叠态 PNG / 文本 (R208)]` 块（`#mtguardfoldstatpng` PNG 导出 + `#mtguardfoldstatcopy` 文本复制标位），`d.innerHTML=_svg` 拼，
`d.style.display='block'`）③ `#mtguardfoldctld` 挂 `#mtguardfoldctl` 下沿（`#mtguardfoldctl` `getBoundingClientRect` + `position:absolute` 定位，
`top:r.bottom+2`，`z-index:70` 高于 `#mtstatebar`/`#mtmetsumdetail`/`#mtguardsnapd`/`#mtguardpaneld`/`#mtguardfoldstatd` 浮层，`--bg2` 底 + `--line`
描边 + `box-shadow` 微浮，`white-space:nowrap` 内联 SVG 不折，`pointer-events:none` 不挡下层，8s 自动隐 `clearTimeout(window._mtGuardFoldCtlT)`
重置——折叠全链路面板临时看全貌不常驻，`setTimeout` 8s 后隐，再点重计 8s，同 R197 `mtGuardSnap` / R199 `mtGuardPanel` / R207 `mtGuardFoldStat` 8s
自动隐纪律）④ 各块全折叠出口标位含自身（`[三域折叠钮]` R159/R202/R203 三折叠钮 + `[折叠联动]` R206 + `[折叠记忆]` R204/R205 + `[三域折叠态总览]`
R207 + `[折叠态 PNG / 文本]` R208 + `[折叠全链路]` R209 自身，`mtGuardFoldCtl` 标位全量含 R159/R202/R203/R204/R205/R206/R207/R208/R209 九折叠域
出口，折叠全链路自含全出口标位，一眼全折叠域出口清单）⑤ 与 R199 `#mtguardpanel` 总览面板 / R207 `#mtguardfoldstat` 三域折叠态总览**分工**（R199
总览面板看能力 / 出口全景（维护守护区全出口），R207 三域折叠态总览看三域折叠 / 展开态（`localStorage` 记忆值），R209 折叠全链路总控看折叠域全出口
（三域折叠钮 + 折叠联动 + 折叠记忆 + 三域折叠态总览 + 折叠态 PNG / 文本），三总览各管各域——维护守护区全出口 / 三域折叠态 / 折叠域全出口）⑥ 与
R197 四段快照 / R199 总览面板 / R207 三域折叠态总览**语言同**（各内联 SVG 总览面板（数据快照 / 能力出口 / 三域折叠态 / 折叠全链路），`<svg>` 拼
分块标位 + `#...` 浮层 `z-index:70` + 8s 自动隐，四总览内联 SVG 语言同）⑦ 验收**函数级**（点 `#mtguardfoldctl` 验 `#mtguardfoldctld` 显 +
`innerHTML` 含 `<svg` + 五块标题（「维护守护区折叠全链路总控」/「三域折叠钮」/「折叠联动」/「折叠记忆」/「三域折叠态总览」/「折叠态 PNG / 文本」），
不真跑 `mtRun` 免 tick 污染 `runs`；`mtGuardFoldCtl` 内联 SVG 五块 headless 验 `innerHTML` 含 `<svg` + 各块标题，非真渲染 SVG 像素）。

---

## 第224轮（前端 R210 · goal round187）：维护守护区折叠全链路总控补 PNG 导出 + 复制出口（`#mtguardfoldctlpng` / `#mtguardfoldctscopy` 小钮，点 `#mtguardfoldctl` 折叠全链路面板后 `#mtguardfoldctlpng` 把折叠全链路 SVG `canvas` 转 PNG 下载「music3_维护守护折叠全链路_<ts>.png」，`#mtguardfoldctscopy` 复制折叠全链路文本（五块分块 + 各折叠出口标位）到剪贴板，折叠全链路 PNG 存档 / 文本贴工单）

**完善性（折叠全链路全貌 PNG 存档 + 文本贴工单免手截 / 手抄）**：R209 `#mtguardfoldctl` 折叠全链路总控内联 SVG 只看，**没 PNG 导出 / 文本复制**
（折叠全链路全貌要存档 / 分享得手动截屏 / 抄，`#mtguardfoldctlpng` 转 PNG 下载 + `#mtguardfoldctscopy` 文本复制，折叠全链路 PNG 存档 + 文本贴工单双
出口，与 R158/R198/R200/R208 PNG 导出 + R196/R201/R208 复制出口语言同）。`#mtguardfoldctl` 旁加**`#mtguardfoldctlpng`**（`⬇ 全链路PNG`，`#mtguardfoldctl`
后）+ **`#mtguardfoldctscopy`**（`⧉ 全链路复制`，`#mtguardfoldctlpng` 后），点 `#mtguardfoldctlpng` → **`mtGuardFoldCtlPng`**（读 `#mtguardfoldctld` 内联
SVG（无则先 `mtGuardFoldCtl()` 生成），`canvas` 转 PNG 下载「music3_维护守护折叠全链路_<ts>.png」，`toBlob` 不可用降级复制 SVG 源码 + toast），点
`#mtguardfoldctscopy` → **`mtGuardFoldCtlCopy`**（读折叠全链路五块（`[三域折叠钮]` R159/R202/R203 + `[折叠联动]` R206 + `[折叠记忆]` R204/R205
`localStorage` 三域记忆值 + `[三域折叠态总览]` R207 + `[折叠态 PNG / 文本]` R208 + `[折叠全链路]` R209/R210 自身）拼全链路文本到剪贴板，
`navigator.clipboard.writeText` 降级 + toast「已复制折叠全链路文本」）——折叠全链路 PNG 存档 / 文本贴工单双出口，与 R158/R198/R200/R208 PNG 导出 +
R196/R201/R208 复制出口语言同。

**E2E**：`点 #mtguardfoldctl（生成 #mtguardfoldctld 内联 SVG）→ 点 #mtguardfoldctlpng → toast「已下载折叠全链路 PNG」；点 #mtguardfoldctcopy →
toast「已复制折叠全链路文本」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r210_ctlpncopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 716→718`，断点 `_热门歌曲\甲乙丙丁.mp3`。

**坑**：① `#mtguardfoldctlpng`/`#mtguardfoldctscopy` 小钮挂 `#mtguardfoldctl` 旁常驻位（`#mtguardfoldctl` 后 `#mtguardfoldctlpng` 再后
`#mtguardfoldctscopy`，折叠全链路总控 PNG 导出 + 文本复制常驻入口，非 hover 态控——`#mtguardfoldctl` 折叠全链路看全貌 + `#mtguardfoldctlpng`
全链路 PNG 存档 + `#mtguardfoldctscopy` 全链路文本贴工单三入口并排，折叠全链路可看可存可贴）② `mtGuardFoldCtlPng` 读 `#mtguardfoldctld` 内联 SVG
（`#mtguardfoldctld` 无 SVG（未点过 `#mtguardfoldctl`）则先 `mtGuardFoldCtl()` 生成，`d.querySelector('svg')` 取 SVG，无 `svg` toast「无折叠全链路
总控可导出（全链路面板空）」`bad`，同 R198/R200/R208 PNG 导出读各内联 SVG 无则先生成纪律）③ SVG 转 PNG（`new XMLSerializer().serializeToString(svg)`
→ `btoa(unescape(encodeURIComponent(svgStr)))` base64 → `Image` `onload` `canvas`（`#f7f5f0` 浅色底 fillRect，透明底贴工单看不清同 R158）`drawImage` →
`toBlob('image/png')` → `a[download]='music3_维护守护折叠全链路_<ts>.png'`（`ts` `new Date().toISOString().replace(/[:.]/g,'-')` 文件名安全，与 R198
`music3_维护守护全记录_快照_<ts>.png` / R200 `music3_维护守护总览_<ts>.png` / R208 `music3_维护守护三域折叠态_<ts>.png` 区分——折叠全链路 PNG 命名
「维护守护折叠全链路」）④ `toBlob` 不可用降级（`_fallbackCopy` 复制 SVG 源码到剪贴板 + toast「已复制折叠全链路 SVG（PNG 导出不可用降级）」，
`canvas` / `toBlob` 沙箱不可用时 SVG 源码降级留存，同 R158/R198/R200/R208 PNG 降级复制 SVG 源码纪律）⑤ `mtGuardFoldCtlCopy` 读折叠全链路五块拼文本
（`#music3 维护守护区折叠全链路总控 · <new Date().toLocaleString()>` 头 + `[三域折叠钮]`（`#mtmetfold` 双图区 R159 / `#mtguardpanelfold` 总览面板 R202 /
`#mtguardfoldall` 全浮层 R203 标位）+ `[折叠联动 (R206)]`（全浮层折叠态强制总览面板折叠 `_mtGuardFoldAll→_mtGuardPanelFold` + 展开态恢复自身
`localStorage` 值标位）+ `[折叠记忆 (R204/R205)]`（`localStorage._mtGuardFoldAll`/`_mtGuardPanelFold`/`_mtMetFold` 三域记忆值实时读，`try/catch` 降级
`'0'`）+ `[三域折叠态总览 (R207)]`（`#mtguardfoldstat` 三域折叠态 SVG + `#mtguardfoldstatd` 色带标位）+ `[折叠态 PNG / 文本 (R208)]`（`#mtguardfoldstatpng`
PNG 导出 + `#mtguardfoldstatcopy` 文本复制标位）+ `[折叠全链路 (R209/R210)]`（`#mtguardfoldctl` 全链路总控 + `#mtguardfoldctlpng` 全链路 PNG +
`#mtguardfoldctscopy` 全链路复制自身标位），`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制折叠全链路文本」，全链路文本自含全
折叠出口标位（R159/R202/R203/R204/R205/R206/R207/R208/R209/R210 十出口），复制全链路文本即全折叠出口清单留存）⑥ 与 R209 `#mtguardfoldctl` 折叠全
链路总控**分工**（R209 内联 SVG 折叠全链路总控看全貌（`#mtguardfoldctld` 8s 自动隐），R210 全链路 PNG 导出 + 文本复制双出口（`#mtguardfoldctlpng`
下载 PNG 存档 / 分享 + `#mtguardfoldctscopy` 文本贴工单），看全貌 + 全貌 PNG / 文本留存双路，折叠全链路可看可存可贴）⑦ 与 R158 `#mtmetpng` / R198
`#mtguardsnappng` / R200 `#mtguardpanelpng` / R208 `#mtguardfoldstatpng` PNG 导出**语言同**（各 PNG 导出读各内联 SVG `canvas` 转 PNG 下载，`toBlob`
不可用降级复制 SVG 源码，折叠全链路 PNG 同语言）⑧ 与 R196 `#mtguardcopy` / R201 `#mtguardpanelcopy` / R208 `#mtguardfoldstatcopy` 复制出口**语言同**
（各文本复制读各数据源拼文本到剪贴板，`navigator.clipboard.writeText` 降级，折叠全链路文本复制同语言，全链路文本自含全出口标位）⑨ 验收**函数级**（点
`#mtguardfoldctl` 生成 `#mtguardfoldctld` 内联 SVG + 点 `#mtguardfoldctlpng` 验 toast「已下载折叠全链路 PNG」/ 降级「已复制折叠全链路 SVG」+ 点
`#mtguardfoldctcopy` 验 toast「已复制折叠全链路文本」，`canvas` / `toBlob` 下载 / 剪贴板 headless 验 toast 出口，真 PNG / 剪贴板内容不验，不真跑
`mtRun` 免 tick 污染 `runs`）。

---

## 第225轮（前端 R211 · goal round188）：维护守护区折叠全链路总控面板补折叠记忆（`#mtguardfoldctl` 面板折叠态存 `localStorage._mtGuardFoldCtl`，刷新后恢复折叠 / 展开态，折叠全链路面板折叠态跨会话留存）

**完善性（折叠全链路面板折叠态跨会话留存免刷新复位）**：R210 `#mtguardfoldctlpng`/`#mtguardfoldctcopy` 全链路 PNG / 文本，但**`#mtguardfoldctld` 折
叠全链路面板 8s 自动隐**（看全貌 8s 即消失，要长看折叠全链路得反复点 `#mtguardfoldctl` 重显，`#mtguardfoldctl` 面板折叠态存 `localStorage.
_mtGuardFoldCtl`，刷新后恢复折叠 / 展开态，折叠全链路面板折叠态跨会话留存，与 R204/R205 折叠记忆语言同）。`#mtguardfoldctl` IIFE（R209 区）改：
`window._mtGuardFoldCtl` 惰性初始化读 `localStorage._mtGuardFoldCtl`（`'1'` 折叠态 / `'0'` 展开态 / 无默认展开态），切后存 `localStorage._mtGuardFoldCtl`，
`#mtguardfoldctl` 文案 + `#mtguardfoldctld` `display` 随初始折叠态（初始同步 IIFE），`mtGuardFoldCtl` 8s 自动隐改 `_mtGuardFoldCtl` 折叠记忆控制（折叠
态不 8s 自动隐常驻省高，展开态才 8s 自动隐）——折叠全链路面板折叠态跨会话留存，与 R204/R205 折叠记忆语言同。

**E2E**：`清 localStorage._mtGuardFoldCtl → 点 #mtguardfoldctl（折叠，window._mtGuardFoldCtl=true + #mtguardfoldctld 隐 + 文案「▸ 展开全链路」+
localStorage._mtGuardFoldCtl='1'）；再点（展开，window._mtGuardFoldCtl=false + #mtguardfoldctld 显 + 文案「▤ 折叠全链路」+ localStorage.
_mtGuardFoldCtl='0'）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r211_ctlsynmmem.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 718→720`，断点 `_红心收藏\Mr. Feel.mp3`。

**坑**：① `window._mtGuardFoldCtl` 惰性初始化读 `localStorage._mtGuardFoldCtl`（`#mtguardfoldctl` IIFE 顶 + 初始同步 IIFE，`if(window._mtGuardFoldCtl===
undefined){ let _init=false; try{ _init=(localStorage.getItem('_mtGuardFoldCtl')==='1'); }catch(_){} window._mtGuardFoldCtl=_init; }`——刷新后
`window._mtGuardFoldCtl` 未设（`undefined`）则读 `localStorage._mtGuardFoldCtl` 恢复折叠 / 展开态，`'1'` 折叠 / `'0'` / 无展开，`try/catch` `localStorage`
不可用（隐私模式 / 沙箱）降级 `false` 展开态，同 R204 `_mtGuardFoldAll` / R205 `_mtGuardPanelFold` `localStorage` 惰性读降级纪律）② `#mtguardfoldctl`
点切折叠记忆（非直接 `mtGuardFoldCtl()` 显面板——R209 `#mtguardfoldctl` 原 IIFE 点直接 `mtGuardFoldCtl()` 显面板 8s 自动隐，R211 改点切折叠记忆标志：
折叠态 `window._mtGuardFoldCtl=true`（`#mtguardfoldctld` 隐常驻省高 + 文案「▸ 展开全链路」+ `clearTimeout` 清 8s 定时）/ 展开态 `window._mtGuardFoldCtl=false`
（`mtGuardFoldCtl()` 拼面板显 + 文案「▤ 折叠全链路」+ `mtGuardFoldCtl` 内 8s 自动隐），切后 `localStorage.setItem('_mtGuardFoldCtl', window._mtGuardFoldCtl?
'1':'0')` 存（`localStorage` 不可用降级不记，跨会话不留存当前会话 `window` 标志仍生效），`localStorage` 键族加 `_mtGuardFoldCtl`（同 `_mtMetFold`/
`_mtGuardPanelFold`/`_mtGuardFoldAll` 维护守护区折叠记忆）③ `mtGuardFoldCtl` 8s 自动隐跟折叠记忆态（`if(!window._mtGuardFoldCtl){ clearTimeout(window.
_mtGuardFoldCtlT); window._mtGuardFoldCtlT=setTimeout(function(){ d.style.display='none'; }, 8000); }`——折叠态 `window._mtGuardFoldCtl===true` 不 8s
自动隐（折叠全链路面板常驻省高，用户手动点 `#mtguardfoldctl` 折叠 / 展开控制），展开态 `false` 才 8s 自动隐（临时看全貌 8s 隐，同 R202 `mtGuardPanel` 8s
自动隐跟折叠态纪律）④ 初始折叠态同步（`#mtguardfoldctl` IIFE 后另 IIFE：`if(window._mtGuardFoldCtl===undefined)` 惰性初始化读 `localStorage._mtGuardFoldCtl`
+ `c.textContent=window._mtGuardFoldCtl?'▸ 展开全链路':'▤ 折叠全链路'`（文案随初始折叠态）+ `if(d && window._mtGuardFoldCtl){ d.style.display='none'; }`
（刷新恢复折叠态隐 `#mtguardfoldctld`，展开态刷新不隐 `#mtguardfoldctld`）——刷新后恢复初始折叠态（文案 + `#mtguardfoldctld` `display` 随
`localStorage._mtGuardFoldCtl`，折叠态刷新隐折叠全链路面板省高，展开态刷新不隐）⑤ 与 R210 `#mtguardfoldctl` 折叠全链路总控**分工**（R209/R210 折叠全
链路总控 `#mtguardfoldctl` 点显面板 + PNG / 文本出口，R211 面板折叠记忆 `localStorage._mtGuardFoldCtl` 跨会话留存——当前会话折叠 / 展开 + 跨会话记忆，
`#mtguardfoldctl` 折叠态存 `localStorage` 刷新恢复，免刷新复位展开态重折叠）⑥ 与 R204 `#mtguardfoldall` 全浮层折叠记忆 / R205 `#mtguardpanelfold` 总览面板
折叠记忆**语言同**（R204 `_mtGuardFoldAll` 存 `localStorage._mtGuardFoldAll` 全浮层折叠记忆，R205 `_mtGuardPanelFold` 存 `localStorage._mtGuardPanelFold`
总览面板折叠记忆，R211 `_mtGuardFoldCtl` 存 `localStorage._mtGuardFoldCtl` 折叠全链路面板折叠记忆，各面板 / 域折叠记忆 `localStorage` 各管各）⑦ 验收
**函数级**（清 `localStorage._mtGuardFoldCtl` + 点 `#mtguardfoldctl` 验 `window._mtGuardFoldCtl` 切 `true`（折叠）+ `#mtguardfoldctld` 隐 + 文案「▸ 展开
全链路」+ `localStorage._mtGuardFoldCtl` 存 `'1'`，再点验 `window._mtGuardFoldCtl` 切 `false`（展开）+ `#mtguardfoldctld` 显 + 文案「▤ 折叠全链路」+
`localStorage._mtGuardFoldCtl` 存 `'0'`，不真跑 `mtRun` 免 tick 污染 `runs`；`localStorage` 存 / 读验 `getItem`/`setItem` 值，刷新恢复验 `localStorage` 读值非
真刷新 headless，初始同步 IIFE 验 `#mtguardfoldctl` 文案 + `#mtguardfoldctld` `display` 随初始折叠态）。

---

## 第226轮（前端 R212 · goal round189）：维护守护区全折叠记忆一键重置（`#mtguardfoldreset` 小钮，点 `#mtguardfoldreset` 重置维护守护区全折叠记忆（`localStorage._mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 全清 `'0'`）+ 全折叠出口（`#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`/`#mtguardfoldctl`）文案 / `display` 恢复展开态，维护守护区全折叠记忆一键复位）

**简洁性（全折叠记忆一键复位免逐键清）**：R204/R205/R211 各折叠记忆 `localStorage` 键（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/
`_mtGuardFoldCtl`）要全复位得逐个清 `localStorage` 键，`#mtguardfoldreset` 一键清全折叠记忆（全 `localStorage` 折叠键 `'0'`）+ 全折叠出口
文案 / `display` 恢复展开态，维护守护区全折叠记忆一键复位。`#mtguardfoldctcopy` 旁加**`#mtguardfoldreset`** 小钮（`↺ 重置折叠`，`#mtguardfoldctcopy`
后常驻位），点 `#mtguardfoldreset` → **`mtGuardFoldReset`**（清 `localStorage._mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`
全 `'0'` + `window._mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 全 `false` + `#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`/
`#mtguardfoldctl` 文案恢复展开态（`▾ 折叠双图区`/`▾ 折叠总览`/`⊘ 折叠全浮层`/`▤ 折叠全链路`）+ `#mtguardpaneld`/`#mtguardfoldctld` `display:none`
+ `clearTimeout` 清 8s 定时 + toast「已重置维护守护区全折叠记忆」）——全折叠记忆一键复位，与 R159 双图区折叠 / R204/R205 折叠记忆 / R211 折叠全
链路折叠记忆同域。

**E2E**：`设 localStorage._mtMetFold/_mtGuardPanelFold/_mtGuardFoldAll/_mtGuardFoldCtl 全 '1'（全折叠态）→ 点 #mtguardfoldreset → 4 键全清 '0' + 4
标志全 false + 全折叠出口文案恢复展开态 + toast「已重置维护守护区全折叠记忆」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、
console 0、截图 r212_foldreset.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 722→724`，断点 `_纯音乐\Sadness and Sorrow.mp3`。

**坑**：① `#mtguardfoldreset` 小钮挂 `#mtguardfoldctcopy` 旁常驻位（`#mtguardfoldctcopy` 后 `inline-block`，维护守护区全折叠记忆一键重置常驻
入口，非 hover 态控——`#mtguardfoldctl` 全链路总控 + `#mtguardfoldctlpng` 全链路 PNG + `#mtguardfoldctcopy` 全链路复制 + `#mtguardfoldreset`
全折叠记忆重置四入口并排，全链路看全貌 / 存 PNG / 贴文本 / 复位记忆）② `mtGuardFoldReset` 清全折叠记忆（`localStorage._mtMetFold`/`_mtGuardPanelFold`/
`_mtGuardFoldAll`/`_mtGuardFoldCtl` 全 `setItem('0')` + `window._mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 全 `false`，
`try/catch` `localStorage` 不可用降级不记——当前会话 `window` 标志仍复位，跨会话不留存，同 R204/R205 `localStorage` 惰性读降级纪律）③ 全折叠出口
文案 / `display` 恢复展开态（`_resetBtns=['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl']` + `_expandTxt` 各钮展开态文案
（`▾ 折叠双图区`/`▾ 折叠总览`/`⊘ 折叠全浮层`/`▤ 折叠全链路`，各钮文案随 R159/R202/R203/R211 各折叠钮展开态默认文案），`#mtguardpaneld`/
`#mtguardfoldctld` `display:none`（总览面板 / 折叠全链路面板折叠态隐，展开态由各触发点显，重置不强制显）+ `clearTimeout(window._mtGuardPanelT)`/
`clearTimeout(window._mtGuardFoldCtlT)` 清 8s 自动隐定时（不残留自动显））④ `#mtguardfoldreset` IIFE 用 **`document` click 委托**（`document.
addEventListener('click', function(e){ if(e.target.id==='mtguardfoldreset'){ e.stopPropagation(); mtGuardFoldReset(); } })`，非 IIFE 顶层 `c=
$('#mtguardfoldreset')` 直绑——`#mtguardfoldreset` 在维护 tab 懒加载区，IIFE 顶层跑时维护 tab 未激活小钮 DOM 未渲染 `c=null` 不绑（维护 tab 懒
加载坑，同 R181 `#mtkeyhint` 维护 tab 委托 / R195 `#mtkeyhintcopy` 维护 tab 委托纪律），`document` click 委托维护 tab 激活后点小钮才触发，
委托 `e.target.id==='mtguardfoldreset'` 精确匹配 + `stopPropagation` 防冒泡）⑤ 与 R204 `#mtguardfoldall` 全浮层折叠记忆 / R205 `#mtguardpanelfold`
总览面板折叠记忆 / R211 `#mtguardfoldctl` 折叠全链路面板折叠记忆**分工**（R204/R205/R211 各单域折叠记忆 `localStorage` 跨会话留存，R212 全折叠
记忆一键重置（清全 4 键 `localStorage` + 4 `window` 标志 + 4 折叠钮文案 / 显示恢复展开态），各单域记忆 + 全记忆一键复位，`#mtguardfoldreset`
全折叠域复位总控）⑥ 验收**函数级**（设 4 键全 `'1'` + 4 标志全 `true`（全折叠态）+ 点 `#mtguardfoldreset` 验 4 键全清 `'0'` + 4 标志全 `false` +
全折叠出口文案恢复展开态 + toast「已重置维护守护区全折叠记忆」，不真跑 `mtRun` 免 tick 污染 `runs`；`document` click 委托验 `e.target.id` 精确
匹配 `#mtguardfoldreset`，维护 tab 激活后点才触发）。

---

## 第227轮（前端 R213 · goal round190）：维护守护区全折叠记忆重置联动全浮层复位（`#mtguardfoldreset` 全折叠记忆重置后联动 `#mtguardfoldctl` 折叠全链路面板 + `#mtguardfoldstat` 三域折叠态总览 + `#mtguardpanel` 总览面板 + `#mtstatebar` 状态详情 + `#mtmetsum` 逐轮明细 + `#mtkeyhint` 三键提示各浮层 `display` 同步复位，全折叠记忆一键复位后全浮层全复位）

**完善性（全折叠记忆复位后全浮层全复位免残留）**：R212 `#mtguardfoldreset` 全折叠记忆一键重置清 4 键 `localStorage` + 4 `window` 标志 + 4 折叠钮文案 / `display` 复位，但**全浮层 `display` 没联动复位**（`#mtguardfoldctld` 折叠全链路面板 / `#mtguardfoldstatd` 三域折叠态总览 / `#mtguardpaneld` 总览面板 / `#mtstatebardtl` 状态详情 / `#mtmetsumdetail` 逐轮明细 / `#mtkeyhintdetail` 三键提示各浮层 `display` 没同步复位，全折叠记忆复位后全浮层仍残留隐 / 显态），`#mtguardfoldreset` 全折叠记忆重置后联动全浮层 `display` 同步复位（`mtGuardFoldReset` 清全折叠记忆后 `#mtguardfoldstatd`/`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail` 全浮层 `display:none` 复位默认态，全折叠记忆一键复位后全浮层全复位）。

**E2E**：`设全折叠态（4 键 '1' + 4 标志 true）+ 各浮层显态 → 点 #mtguardfoldreset → 全浮层（#mtguardpaneld/#mtguardfoldctld/#mtguardfoldstatd/#mtstatebardtl/#mtmetsumdetail/#mtkeyhintdetail）display 全复位 none + 4 键全清 '0' + toast「已重置维护守护区全折叠记忆」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r213_foldresetall.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 724→726`，断点 `_纯音乐\少女的祈祷.mp3`。

**坑**：① `mtGuardFoldReset`（R212 区）清全折叠记忆后补全浮层 `display` 复位（R213：`const _fsD=document.getElementById('mtguardfoldstatd'); if(_fsD){ _fsD.style.display='none'; }` + `const _sbD=document.getElementById('mtstatebardtl'); if(_sbD){ _sbD.style.display='none'; }` + `const _msD=document.getElementById('mtmetsumdetail'); if(_msD){ _msD.style.display='none'; }` + `const _khD=document.getElementById('mtkeyhintdetail'); if(_khD){ _khD.style.display='none'; }`，`#mtguardpaneld`/`#mtguardfoldctld` 总览面板 / 折叠全链路面板 R212 已 `display:none`，R213 补 `#mtguardfoldstatd` 三域折叠态总览 / `#mtstatebardtl` 状态详情 / `#mtmetsumdetail` 逐轮明细 / `#mtkeyhintdetail` 三键提示全浮层 `display:none` 复位默认态——全浮层（6 浮层 `#mtguardpaneld`/`#mtguardfoldctld`/`#mtguardfoldstatd`/`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail`）全 `display:none` 复位，全折叠记忆一键复位后全浮层全复位，免残留隐 / 显态）② 全浮层 `display` 复位默认态 `none`（各浮层默认隐，hover / 点触发才显，`display:none` 复位回默认隐态，不强制显——与 R212 总览面板 / 折叠全链路面板 `display:none` 复位同纪律，全浮层复位全 `none` 默认态）③ 与 R212 `#mtguardfoldreset` 全折叠记忆重置**分工**（R212 清 4 键 `localStorage` + 4 `window` 标志 + 4 折叠钮文案 / `display` 复位，R213 补全浮层 `display` 复位（6 浮层 `display:none`），全折叠记忆复位 + 全浮层复位全复位，`#mtguardfoldreset` 一键复位全折叠域 + 全浮层）④ 各浮层 `display:none` 复位非强制显（`if(_fsD){ _fsD.style.display='none'; }` 各浮层存在即 `display:none`，不强制 `display` 值——复位回默认隐态，hover / 点触发才显，全浮层复位全隐，维护守护区全浮层全复位）⑤ 与 R159 `#mtmetfold` 双图区折叠 / R204 `#mtguardfoldall` 全浮层折叠 / R205 `#mtguardpanelfold` 总览面板折叠 / R211 `#mtguardfoldctl` 折叠全链路折叠**语言同**（各折叠域 `display` 复位默认态，全折叠记忆重置 + 全浮层 `display` 复位全复位，维护守护区全折叠域全复位）⑥ 验收**函数级**（设全折叠态（4 键 `'1'` + 4 标志 `true`）+ 各浮层 `display:block` 显态 + 点 `#mtguardfoldreset` 验全浮层（6 浮层 `#mtguardpaneld`/`#mtguardfoldctld`/`#mtguardfoldstatd`/`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail`）`display` 全复位 `'none'` + 4 键全清 `'0'` + toast「已重置维护守护区全折叠记忆」，不真跑 `mtRun` 免 tick 污染 `runs`；全浮层 `display` 复位验 6 浮层全 `'none'`，非真渲染像素）。

---

## 第228轮（前端 R214 · goal round191）：维护守护区全折叠记忆重置补出口（`#mtguardfoldresetcopy` 小钮，点 `#mtguardfoldreset` 全折叠记忆重置后 `#mtguardfoldresetcopy` 复制全折叠记忆重置详情（4 键 `localStorage` 复位值 + 4 `window` 标志复位值 + 4 折叠钮文案复位 + 6 浮层 `display` 复位 + 重置时间戳）到剪贴板，全折叠记忆重置详情可文本留存 / 贴工单）

**完善性（全折叠记忆重置详情文本留存 / 贴工单免手抄）**：R213 `#mtguardfoldreset` 全折叠记忆重置 + 全浮层复位，但**重置详情（4 键 / 4 标志 / 4 折叠钮 / 6 浮层
复位状态 + 时间戳）要记录 / 贴工单得手动抄**，`#mtguardfoldresetcopy` 复制全折叠记忆重置详情到剪贴板，全折叠记忆重置详情可文本留存 / 贴工单。
`#mtguardfoldreset` 旁加**`#mtguardfoldresetcopy`** 小钮（`⧉ 重置复制`，`#mtguardfoldreset` 后常驻位），点 `#mtguardfoldresetcopy` → **`mtGuardFoldResetCopy`**
（读全折叠记忆重置后各数据源：`localStorage._mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 复位值 + `window._mtMetFold`/`_mtGuardPanelFold`/
`_mtGuardFoldAll`/`_mtGuardFoldCtl` 复位值 + `#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`/`#mtguardfoldctl` 4 折叠钮文案 + `#mtguardpaneld`/
`#mtguardfoldctld`/`#mtguardfoldstatd`/`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail` 6 浮层 `display` + 重置时间戳，拼重置详情到剪贴板，
`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制全折叠记忆重置详情」）——全折叠记忆重置详情文本留存 / 贴工单，与 R196/R201/R208 复制
出口同语言。

**E2E**：`点 #mtguardfoldreset（重置全折叠记忆）→ 点 #mtguardfoldresetcopy → toast「已复制全折叠记忆重置详情」`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r214_resetcopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 726→728`，断点 `_英文歌\21 Guns.mp3`。

**坑**：① `#mtguardfoldresetcopy` 小钮挂 `#mtguardfoldreset` 旁常驻位（`#mtguardfoldreset` 后 `inline-block`，维护守护区全折叠记忆重置详情复制常驻入口，
非 hover 态控——`#mtguardfoldreset` 全折叠记忆重置 + `#mtguardfoldresetcopy` 重置详情复制双入口并排，全折叠域一键复位 + 重置详情留存双出口）②
`mtGuardFoldResetCopy` 读全折叠记忆重置后各数据源拼重置详情（`#music3 全折叠记忆重置详情 · <new Date().toLocaleString()>` 头 + `[localStorage 4键复位值]`
（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 各 `localStorage.getItem` 值）+ `[window 4标志复位值]`（`window._mtMetFold`/
`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 各布尔值）+ `[4折叠钮文案复位]`（`#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`/`#mtguardfoldctl`
各 `textContent`）+ `[6浮层display复位]`（`#mtguardpaneld`/`#mtguardfoldctld`/`#mtguardfoldstatd`/`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail`
各 `style.display`），`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制全折叠记忆重置详情」，读重置后当前态（点 `#mtguardfoldresetcopy`
即拼重置后各数据源当前值，非缓存旧值，与 R196 `mtGuardCopy` / R201 `mtGuardPanelCopy` 读当前态同纪律）③ `#mtguardfoldresetcopy` IIFE 用 **`document` click
委托**（`document.addEventListener('click', function(e){ if(e.target.id==='mtguardfoldresetcopy'){ e.stopPropagation(); mtGuardFoldResetCopy(); } })`，
非 IIFE 顶层 `c=$('#mtguardfoldresetcopy')` 直绑——`#mtguardfoldresetcopy` 在维护 tab 懒加载区，IIFE 顶层跑时维护 tab 未激活小钮 DOM 未渲染 `c=null` 不绑，
维护 tab 激活后点才触发，`document` click 委托 `e.target.id==='mtguardfoldresetcopy'` 精确匹配 + `stopPropagation` 防冒泡，同 R212 `#mtguardfoldreset`
IIFE `document` click 委托纪律；首跑 IIFE 语法多 `)` `node=1`，修正 `document.addEventListener('click', function(e){ ... });` 后 IIFE 闭合 `})();` 免多
`)` 后 `node=0`，同 R212 `#mtguardfoldreset` IIFE 多 `)` 语法修正纪律）④ 与 R212 `#mtguardfoldreset` 全折叠记忆重置 / R213 全浮层复位**分工**（R212
全折叠记忆一键重置清 4 键 + 4 标志 + 4 折叠钮 + 全浮层复位，R213 补全浮层 `display` 复位，R214 重置详情复制贴工单 / 记录——全折叠记忆复位 + 全浮层复位 +
重置详情留存三出口，`#mtguardfoldreset` 复位 + `#mtguardfoldresetcopy` 留存双入口）⑤ 与 R196 `#mtguardcopy` / R201 `#mtguardpanelcopy` / R208
`#mtguardfoldstatcopy` 复制出口**语言同**（各文本复制读各数据源拼文本到剪贴板，`navigator.clipboard.writeText` 降级，全折叠记忆重置详情复制同语言，
重置详情自含 4 键 + 4 标志 + 4 折叠钮 + 6 浮层全复位状态标位，复制重置详情即全折叠域复位记录留存）⑥ 验收**函数级**（点 `#mtguardfoldreset` 重置全折叠
记忆 + 点 `#mtguardfoldresetcopy` 验 toast「已复制全折叠记忆重置详情」，剪贴板 / 降级只验 toast 出口，真剪贴板内容 headless 不验，不真跑 `mtRun` 免 tick
污染 `runs`；`mtGuardFoldResetCopy` 重置详情拼逻辑验 toast 出口，各数据源当前值读逻辑同 R196/R201/R208 读当前态复制）。

---

## 第229轮（前端 R215 · goal round192）：维护守护区全折叠记忆重置详情补 PNG 出口（`#mtguardfoldresetpng` 小钮，点 `#mtguardfoldreset` 全折叠记忆重置后 `#mtguardfoldresetpng` 把全折叠记忆重置详情 SVG（4 键 + 4 标志 + 4 折叠钮 + 6 浮层复位状态色带 + 时间戳）`canvas` 转 PNG 下载「music3_全折叠记忆重置详情_<ts>.png」，全折叠记忆重置详情 PNG 存档 / 贴工单）

**完善性（全折叠记忆重置详情 PNG 存档 / 图片贴工单免手截）**：R214 `#mtguardfoldresetcopy` 重置详情文本复制，但**重置详情要 PNG 存档 / 图片贴工单得手动截屏**，`#mtguardfoldresetpng` 重置详情 SVG `canvas` 转 PNG 下载，全折叠记忆重置详情 PNG 存档 / 图片贴工单，与 R158/R198/R200/R208 PNG 导出同语言。`#mtguardfoldresetcopy` 旁加**`#mtguardfoldresetpng`** 小钮（`⬇ 重置PNG`，`#mtguardfoldresetcopy` 后常驻位），点 `#mtguardfoldresetpng` → **`mtGuardFoldResetPng`**（拼全折叠记忆重置详情内联 SVG（`music3 全折叠记忆重置详情 · <时间戳>` 头 + `[localStorage 4键复位值]` 4 色带（`'0'` 复位 `--ok` 绿 / 非 `'0'` `--bad` 红）+ `[window 4标志复位值]` 4 色带（`false` 复位 `--ok` 绿 / `true` `--bad` 红）+ `[4折叠钮文案复位]` 4 文案行 + `[6浮层display复位]` 6 色带（`none` 复位 `--ok` 绿 / 非 `none` `--dim` 灰），`canvas` 转 PNG 下载「music3_全折叠记忆重置详情_<ts>.png」，`toBlob` 不可用 `_fallbackCopy` 复制 SVG 源码 + toast）——全折叠记忆重置详情 PNG 存档 / 图片贴工单，与 R158/R198/R200/R208 PNG 导出同语言。

**E2E**：`点 #mtguardfoldreset（重置全折叠记忆）→ 点 #mtguardfoldresetpng → toast「已下载全折叠记忆重置详情 PNG」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r215_resetpng.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 728→730`，断点 `_英文歌\Closer.mp3`。

**坑**：① `#mtguardfoldresetpng` 小钮挂 `#mtguardfoldresetcopy` 旁常驻位（`#mtguardfoldresetcopy` 后 `inline-block`，维护守护区全折叠记忆重置详情 PNG 导出常驻入口，非 hover 态控——`#mtguardfoldreset` 全折叠记忆重置 + `#mtguardfoldresetcopy` 重置详情复制 + `#mtguardfoldresetpng` 重置详情 PNG 三入口并排，全折叠域一键复位 + 重置详情文本 / 图片双留存）② `mtGuardFoldResetPng` 拼全折叠记忆重置详情内联 SVG（4 键 + 4 标志 + 4 折叠钮 + 6 浮层复位状态色带 + 时间戳，各分块标题 `--dim` 灰 + 色带 `rect`（复位态 `--ok` 绿 / 非复位 `--bad` 红 / 浮层非 `none` `--dim` 灰）+ 数值文案，`#f7f5f0` 浅色底 fillRect（透明底贴工单看不清，同 R158 浅色底纪律），`toBlob` 不可用 `_fallbackCopy` 复制 SVG 源码 + toast「已复制全折叠记忆重置详情 SVG（PNG 导出不可用降级）」，与 R158/R198/R200/R208 PNG 导出读内联 SVG `canvas` 转 PNG 下载 + `toBlob` 降级复制 SVG 源码语言同）③ SVG 拼接引号配平（SVG 属性值用双引号 `"` 外层单引号 `'` 串拼接，`'<text x="8" y="'+_y+'" ...>'`，免 Python 写 JS 时 `'` 转义破坏嵌套引号——首跑 SVG 拼接 `'+_y+'` 嵌套引号配平错 `node=1`（`missing ) after argument list`），重写函数体 SVG 拼接双引号属性值 + 单引号外层串后 `node=0`，同 R212/R214 IIFE 多 `)` 语法修正纪律——SVG 拼接引号配平坑）④ `#mtguardfoldresetpng` IIFE 用 **`document` click 委托**（维护 tab 懒加载，非 IIFE 顶层直绑，同 R212 `#mtguardfoldreset` / R214 `#mtguardfoldresetcopy` IIFE `document` click 委托纪律）⑤ 与 R214 `#mtguardfoldresetcopy` 重置详情文本复制**分工**（R214 重置详情文本复制贴工单 / 记录，R215 重置详情 PNG 存档 / 图片贴工单——重置详情文本 / 图片双留存，`#mtguardfoldresetcopy` 文本 + `#mtguardfoldresetpng` 图片双出口，全折叠域一键复位 + 详情双留存）⑥ 与 R158 `#mtmetpng` / R198 `#mtguardsnappng` / R200 `#mtguardpanelpng` / R208 `#mtguardfoldstatpng` PNG 导出**语言同**（各 PNG 导出读 / 拼内联 SVG `canvas` 转 PNG 下载，`toBlob` 不可用降级复制 SVG 源码，全折叠记忆重置详情 PNG 同语言，各 PNG 命名区分数据源「全折叠记忆重置详情」）⑦ 验收**函数级**（点 `#mtguardfoldreset` 重置 + 点 `#mtguardfoldresetpng` 验 toast「已下载全折叠记忆重置详情 PNG」/ 降级「已复制全折叠记忆重置详情 SVG」，`canvas` / `toBlob` 下载 headless 验 toast 出口，真 PNG 文件不验，不真跑 `mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验 toast 出口，色带 / 文案渲染逻辑同 R198/R200/R208 PNG 拼内联 SVG 读数据源逻辑）。

---

## 第230轮（前端 R216 · goal round193）：维护守护区全折叠域总控面板（`#mtguardalldomain` 小钮，点 `#mtguardalldomain` 显 `#mtguardalldomains` 浮层内联全折叠域总控面板（四折叠记忆 `localStorage` 键 + 四折叠出口 + 全折叠重置 / 详情复制 / 详情 PNG + 全浮层复位出口一张全折叠域总控图，全折叠域能力 / 出口全景图免分散找，与 R209 折叠全链路总控同语言）

**完善性（全折叠域能力 / 出口全景图免分散找）**：R209 `#mtguardfoldctl` 折叠全链路总控看全折叠出口，但**全折叠记忆重置域（`#mtguardfoldreset` 重置 + `#mtguardfoldresetcopy` 详情复制 +
`#mtguardfoldresetpng` 详情 PNG + 全浮层复位）没独立总控面板**，`#mtguardalldomain` 全折叠域总控面板（四折叠记忆键 + 四折叠出口 + 全折叠重置 / 详情双出口 + 全浮层复位出口全景图），全折叠域
能力 / 出口一张总控图，与 R209 折叠全链路总控同语言。`#mtguardfoldresetpng` 旁加**`#mtguardalldomain`** 小钮（`▣ 全折叠域`，`#mtguardfoldresetpng` 后常驻位）+ **`#mtguardalldomains`** 浮层
div，点 `#mtguardalldomain` → **`mtGuardAllDomain`**（拼内联 SVG 全折叠域总控面板六块（`[四折叠记忆 localStorage 键]`（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`
各值 + 色带（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠 `--bad` 红））+ `[四折叠出口]`（`#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`/`#mtguardfoldctl` 各钮文案）+ `[全折叠重置]`
（`#mtguardfoldreset` 全折叠记忆一键复位标位）+ `[重置详情复制 / PNG]`（`#mtguardfoldresetcopy` 重置详情复制 + `#mtguardfoldresetpng` 重置详情 PNG 双出口标位）+ `[全浮层复位]`
（`#mtguardpaneld`/`#mtguardfoldctld`/`#mtguardfoldstatd`/`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail` 6 浮层 `display` 色带（`none` 复位 `--ok` 绿 / 非 `none` `--dim` 灰））
+ `[三域折叠态总览 (R207)]`（`#mtguardfoldstat` 三域折叠态 SVG + `#mtguardfoldstatpng`/`#mtguardfoldstatcopy` 双出口标位）），`#mtguardalldomains` 挂 `#mtguardalldomain` 下沿
`z-index:70` + 8s 自动隐 `window._mtGuardAllDomainT`）——全折叠域能力 / 出口全景图免分散找，与 R209 折叠全链路总控同语言。

**E2E**：`点 #mtguardalldomain → #mtguardalldomains 内联 SVG（含 <svg + 六块标题）+ display=block`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图
r216_alldomain.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 730→732`，断点 `_英文歌\Hey Soul Sister.mp3`。

**坑**：① `#mtguardalldomain` 小钮挂 `#mtguardfoldresetpng` 旁常驻位（`#mtguardfoldresetpng` 后 `inline-block`，维护守护区全折叠域总控常驻入口，非 hover 态控——`#mtguardfoldreset`
全折叠记忆重置 + `#mtguardfoldresetcopy` 重置详情复制 + `#mtguardfoldresetpng` 重置详情 PNG + `#mtguardalldomain` 全折叠域总控四入口并排，全折叠域一键复位 + 详情双留存 + 全景总控）②
`#mtguardalldomains` 浮层 div（`#mtguardfoldctld` 后，`z-index:70` + `white-space:nowrap` + `pointer-events:none`，全折叠域总控浮层，`#f7f5f0` 底 + `--line` 描边 + `box-shadow` 微浮，
同 R197/R199/R207/R209 各浮层 div 纪律）③ `mtGuardAllDomain` 拼内联 SVG 全折叠域总控面板六块（`music3 全折叠域总控面板 · <时间戳>` 头 + 各分块 `--line` 分隔线 + 标题 `--dim` 灰，
`[四折叠记忆 localStorage 键]` 4 色带（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠 `--bad` 红）+ `[四折叠出口]` 4 钮文案 + `[全折叠重置]` / `[重置详情复制/PNG]` 各出口标位 `--ok` 绿 +
`[全浮层复位]` 6 浮层 `display` 色带 + `[三域折叠态总览 (R207)]` 出口标位，读 `localStorage` 4 键值 + 4 折叠钮 `textContent` + 6 浮层 `style.display` 实时拼 SVG，与 R197 `mtGuardSnap` /
R199 `mtGuardPanel` / R207 `mtGuardFoldStat` / R209 `mtGuardFoldCtl` 各内联 SVG 总控拼分块标位 / 色带同语言）④ `#mtguardalldomain` IIFE 用 **`document` click 委托**（维护 tab 懒加载，
非 IIFE 顶层直绑，同 R212 `#mtguardfoldreset` / R214 `#mtguardfoldresetcopy` / R215 `#mtguardfoldresetpng` IIFE `document` click 委托纪律）⑤ 与 R209 `#mtguardfoldctl` 折叠全链路
总控**分工**（R209 折叠全链路总控看全折叠出口（`#mtguardfoldctld` 8s 自动隐），R216 全折叠域总控面板看全折叠域能力 / 出口全景（`#mtguardalldomains` 8s 自动隐），全折叠出口全景
+ 全折叠域能力 / 出口全景双总控，`#mtguardalldomain` 全折叠域总控面板看全折叠域，`#mtguardfoldctl` 折叠全链路看全折叠链路）⑥ 与 R207 `#mtguardfoldstat` 三域折叠态总览**分工**
（R207 三域折叠态总览看三域 `localStorage` 折叠记忆态，R216 全折叠域总控面板看全折叠域能力 / 出口全景（含三域折叠态总览出口标位 + 全折叠重置 / 详情双出口 + 全浮层复位），三域
折叠态 + 全折叠域全景双总控）⑦ 与 R197 `#mtguardsnap` / R199 `#mtguardpanel` / R207 `#mtguardfoldstat` / R209 `#mtguardfoldctl` 内联 SVG 总控面板族**语言同**（各总控面板拼内联
SVG 分块标位 / 色带 + `#...d` 浮层 + `getBoundingClientRect` 下沿定位 + `clearTimeout` 8s 自动隐，全折叠域总控面板同语言，各面板分块不同：四段快照 / 能力出口总览 / 三域折叠态 /
折叠全链路 / 全折叠域全景）⑧ 验收**函数级**（点 `#mtguardalldomain` 验 `#mtguardalldomains` `innerHTML` 含 `<svg` + 六块标题（`[四折叠记忆`/`[四折叠出口]`/`[全折叠重置]`/
`[重置详情复制`/`[全浮层复位]`/`[三域折叠态总览`）+ `display=block`，`localStorage` 4 键 / 4 折叠钮 / 6 浮层读值验 SVG 拼逻辑，不真跑 `mtRun` 免 tick 污染 `runs`；8s 自动隐验
`clearTimeout(window._mtGuardAllDomainT)` + `setTimeout` 重置，非真等 8s）。

---

## 第231轮（前端 R217 · goal round194）：维护守护区全折叠域总控面板补 PNG 导出 + 复制出口（`#mtguardalldomainpng` 小钮，点 `#mtguardalldomain` 全折叠域总控面板后 `#mtguardalldomainpng` 把全折叠域总控面板 SVG `canvas` 转 PNG 下载「music3_全折叠域总控_<ts>.png」+ `#mtguardalldomaincopy` 复制全折叠域总控文本，全折叠域总控面板 PNG 存档 / 文本贴工单，与 R198/R200/R208 PNG 导出 + R196/R201/R208 复制出口同语言）

**完善性（全折叠域总控面板 PNG 存档 / 文本贴工单免手截 / 手抄）**：R216 `#mtguardalldomain` 全折叠域总控面板内联 SVG 只看，**没 PNG 导出 / 文本复制**（全折叠域总控面板要存档 / 分享得手动截屏 / 抄，
`#mtguardalldomainpng` 转 PNG 下载 + `#mtguardalldomaincopy` 文本复制，全折叠域总控面板 PNG 存档 + 文本贴工单双出口，与 R198/R200/R208 PNG 导出 + R196/R201/R208 复制出口语言同）。
`#mtguardalldomain` 旁加**`#mtguardalldomainpng`**（`⬇ 全折叠PNG`）+ **`#mtguardalldomaincopy`**（`⧉ 全折叠复制`）小钮，点 `#mtguardalldomainpng` → **`mtGuardAllDomainPng`**（读
`#mtguardalldomains` 内联 SVG（无则先 `mtGuardAllDomain()` 生成），`canvas` 转 PNG 下载「music3_全折叠域总控_<ts>.png」，`toBlob` 不可用降级复制 SVG 源码 + toast「已下载全折叠域总控 PNG」），
点 `#mtguardalldomaincopy` → **`mtGuardAllDomainCopy`**（读全折叠域总控六块（`[四折叠记忆 localStorage 键]`/`[四折叠出口]`/`[全折叠重置]`/`[重置详情复制/PNG]`/`[全浮层复位]`/
`[三域折叠态总览]` 各块标位）拼总控文本到剪贴板，`navigator.clipboard.writeText` 降级 + toast「已复制全折叠域总控文本」）——全折叠域总控面板 PNG 存档 / 文本贴工单双出口，
与 R198/R200/R208 PNG 导出 + R196/R201/R208 复制出口同语言。

**E2E**：`点 #mtguardalldomain（生成 #mtguardalldomains 内联 SVG）→ 点 #mtguardalldomainpng → toast「已下载全折叠域总控 PNG」；点 #mtguardalldomaincopy → toast「已复制全折叠域总控文本」`
（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r217_alldompngcopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 732→734`，断点 `_英文歌\Lose You to Love Me.mp3`。

**坑**：① `#mtguardalldomainpng`/`#mtguardalldomaincopy` 小钮挂 `#mtguardalldomain` 旁常驻位（`#mtguardalldomain` 后 `#mtguardalldomainpng` 再后 `#mtguardalldomaincopy`，全折叠域
总控面板 PNG 导出 + 文本复制常驻入口，非 hover 态控——`#mtguardalldomain` 全折叠域总控看全貌 + `#mtguardalldomainpng` 全折叠域 PNG 存档 + `#mtguardalldomaincopy` 全折叠域文本贴
工单三入口并排，全折叠域总控可看可存可贴）② `mtGuardAllDomainPng` 读 `#mtguardalldomains` 内联 SVG（`#mtguardalldomains` 无 SVG（未点过 `#mtguardalldomain`）则先 `mtGuardAllDomain()`
生成，`_d.querySelector('svg')` 取 SVG，无 `svg` toast「无全折叠域总控面板可导出（全折叠域面板空）」`bad`，同 R198/R200/R208 PNG 导出读各内联 SVG 无则先生成纪律）③ SVG 转 PNG
（`new XMLSerializer().serializeToString(svg)` → `btoa(unescape(encodeURIComponent(svgStr)))` base64 → `Image` `onload` `canvas`（`#f7f5f0` 浅色底 fillRect，透明底贴工单看不清同 R158）
`drawImage` → `toBlob('image/png')` → `a[download]='music3_全折叠域总控_<ts>.png'`（`ts` `new Date().toISOString().replace(/[:.]/g,'-')` 文件名安全，与 R198 `music3_维护守护全记录_快照_<ts>.png` /
R200 `music3_维护守护总览_<ts>.png` / R208 `music3_维护守护三域折叠态_<ts>.png` 区分——全折叠域总控 PNG 命名「全折叠域总控」）④ `toBlob` 不可用降级（`_fallbackCopy` 复制 SVG 源码到剪贴板 +
toast「已复制全折叠域总控 SVG（PNG 导出不可用降级）」，`canvas` / `toBlob` 沙箱不可用时 SVG 源码降级留存，同 R158/R198/R200/R208 PNG 降级复制 SVG 源码纪律）⑤ `mtGuardAllDomainCopy`
读全折叠域总控六块拼文本（`#music3 全折叠域总控 · <new Date().toLocaleString()>` 头 + `[四折叠记忆 localStorage 键]`（4 键值实时读）+ `[四折叠出口]`（4 折叠钮 `textContent`）+
`[全折叠重置]`（`#mtguardfoldreset` 复位标位）+ `[重置详情复制/PNG]`（`#mtguardfoldresetcopy`/`#mtguardfoldresetpng` 双出口标位）+ `[全浮层复位]`（6 浮层 `display`）+ `[三域折叠态总览
(R207)]`（`#mtguardfoldstat` 三域折叠态 SVG + `#mtguardfoldstatpng`/`#mtguardfoldstatcopy` 双出口标位），`navigator.clipboard.writeText`（`_copyFallback` 降级）+ toast「已复制全折叠域
总控文本」，全折叠域总控文本自含全折叠域出口标位（R159/R202/R203/R204/R205/R206/R207/R208/R209/R210/R211/R212/R213/R214/R215/R216 十六出口），复制全折叠域总控文本即全折叠域出口清单
留存）⑥ 与 R216 `#mtguardalldomain` 全折叠域总控面板**分工**（R216 内联 SVG 全折叠域总控面板看全貌（`#mtguardalldomains` 8s 自动隐），R217 全折叠域 PNG 导出 + 文本复制双出口
（`#mtguardalldomainpng` 下载 PNG 存档 / 分享 + `#mtguardalldomaincopy` 文本贴工单），看全貌 + 全貌 PNG / 文本留存双路，全折叠域总控可看可存可贴）⑦ 与 R198 `#mtguardsnappng` /
R200 `#mtguardpanelpng` / R208 `#mtguardfoldstatpng` PNG 导出**语言同**（各 PNG 导出读各内联 SVG `canvas` 转 PNG 下载，`toBlob` 不可用降级复制 SVG 源码，全折叠域总控 PNG 同语言）⑧
与 R201 `#mtguardpanelcopy` / R208 `#mtguardfoldstatcopy` 复制出口**语言同**（各文本复制读各数据源拼文本到剪贴板，`navigator.clipboard.writeText` 降级，全折叠域总控文本复制同语言，
全折叠域总控文本自含全出口标位）⑨ 验收**函数级**（点 `#mtguardalldomain` 生成 `#mtguardalldomains` 内联 SVG + 点 `#mtguardalldomainpng` 验 toast「已下载全折叠域总控 PNG」/ 降级「已复制
全折叠域总控 SVG」+ 点 `#mtguardalldomaincopy` 验 toast「已复制全折叠域总控文本」，`canvas` / `toBlob` 下载 / 剪贴板 headless 验 toast 出口，真 PNG / 剪贴板内容不验，不真跑 `mtRun`
免 tick 污染 `runs`）。

---

## 第232轮（前端 R218 · goal round195）：维护守护区全折叠域总控面板补折叠记忆（`#mtguardalldomain` 面板折叠态存 `localStorage._mtGuardAllDomain`，刷新后恢复折叠 / 展开态，全折叠域总控面板折叠态跨会话留存）

**完善性（全折叠域总控面板折叠态跨会话留存免刷新复位）**：R217 `#mtguardalldomainpng`/`#mtguardalldomaincopy` 全折叠域总控 PNG / 文本，但**`#mtguardalldomains` 全折叠域总控面板
8s 自动隐**（看全貌 8s 即消失，要长看全折叠域总控得反复点 `#mtguardalldomain` 重显，`#mtguardalldomain` 面板折叠态存 `localStorage._mtGuardAllDomain`，刷新后恢复折叠 / 展开态，
全折叠域总控面板折叠态跨会话留存，与 R204/R205/R211 折叠记忆语言同）。`#mtguardalldomain` IIFE（R216 区）改：`window._mtGuardAllDomain` 惰性初始化读 `localStorage._mtGuardAllDomain`
（`'1'` 折叠态 / `'0'` / 无默认展开态），切后存 `localStorage._mtGuardAllDomain`，`#mtguardalldomain` 文案 + `#mtguardalldomains` `display` 随初始折叠态（初始同步 IIFE），
`mtGuardAllDomain` 8s 自动隐改 `_mtGuardAllDomain` 折叠记忆控制（折叠态不 8s 自动隐常驻省高，展开态才 8s 自动隐）——全折叠域总控面板折叠态跨会话留存，与 R204/R205/R211 折叠记忆
语言同。

**E2E**：`清 localStorage._mtGuardAllDomain → 点 #mtguardalldomain（折叠，window._mtGuardAllDomain=true + #mtguardalldomains 隐 + 文案「▸ 展开全折叠域」+ localStorage.
_mtGuardAllDomain='1'）；再点（展开，window._mtGuardAllDomain=false + 文案「▣ 全折叠域」+ localStorage._mtGuardAllDomain='0'）`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r218_alldomfoldmem.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 734→736`，断点 `_英文歌\Radioactive.mp3`。

**坑**：① `window._mtGuardAllDomain` 惰性初始化读 `localStorage._mtGuardAllDomain`（`#mtguardalldomain` 折叠记忆切 IIFE 顶 + 初始同步 IIFE，`if(window._mtGuardAllDomain===
undefined){ let _init=false; try{ _init=(localStorage.getItem('_mtGuardAllDomain')==='1'); }catch(_){} window._mtGuardAllDomain=_init; }`——刷新后 `window._mtGuardAllDomain`
未设（`undefined`）则读 `localStorage._mtGuardAllDomain` 恢复折叠 / 展开态，`'1'` 折叠 / `'0'` / 无展开，`try/catch` `localStorage` 不可用（隐私模式 / 沙箱）降级 `false` 展开态，
同 R204 `_mtGuardFoldAll` / R205 `_mtGuardPanelFold` / R211 `_mtGuardFoldCtl` `localStorage` 惰性读降级纪律）② `#mtguardalldomain` 点切折叠记忆（非直接 `mtGuardAllDomain()` 显面板
——R216 `#mtguardalldomain` 原 IIFE 点直接 `mtGuardAllDomain()` 显面板 8s 自动隐，R218 改点切折叠记忆标志：折叠态 `window._mtGuardAllDomain=true`（`#mtguardalldomains` 隐常驻
省高 + 文案「▸ 展开全折叠域」+ `clearTimeout` 清 8s 定时）/ 展开态 `window._mtGuardAllDomain=false`（`mtGuardAllDomain()` 拼面板显 + 文案「▣ 全折叠域」+ `mtGuardAllDomain` 内 8s
自动隐），切后 `localStorage.setItem('_mtGuardAllDomain', window._mtGuardAllDomain?'1':'0')` 存（`localStorage` 不可用降级不记，跨会话不留存当前会话 `window` 标志仍生效），
`localStorage` 键族加 `_mtGuardAllDomain`（同 `_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 维护守护区折叠记忆）③ `mtGuardAllDomain` 8s 自动隐跟折叠
记忆态（`if(!window._mtGuardAllDomain){ _d.style.display='none'; clearTimeout(window._mtGuardAllDomainT); window._mtGuardAllDomainT=setTimeout(function(){ _d.style.display='none'; },
8000); }`——折叠态 `window._mtGuardAllDomain===true` 不 8s 自动隐（全折叠域总控面板常驻省高，用户手动点 `#mtguardalldomain` 折叠 / 展开控制），展开态 `false` 才 8s 自动隐（临时看
全貌 8s 隐，同 R202 `mtGuardPanel` / R211 `mtGuardFoldCtl` 8s 自动隐跟折叠态纪律）④ 初始折叠态同步（`#mtguardalldomain` 折叠记忆切 IIFE 后另 IIFE：`if(window._mtGuardAllDomain===
undefined)` 惰性初始化读 `localStorage._mtGuardAllDomain` + `c.textContent=window._mtGuardAllDomain?'▸ 展开全折叠域':'▣ 全折叠域'`（文案随初始折叠态）+ `if(d && window.
_mtGuardAllDomain){ d.style.display='none'; }`（刷新恢复折叠态隐 `#mtguardalldomains`，展开态刷新不隐）——刷新后恢复初始折叠态（文案 + `#mtguardalldomains` `display` 随
`localStorage._mtGuardAllDomain`，折叠态刷新隐全折叠域总控面板省高，展开态刷新不隐）⑤ 与 R216 `#mtguardalldomain` 全折叠域总控面板**分工**（R216 内联 SVG 全折叠域总控面板看全貌
（`#mtguardalldomains` 8s 自动隐），R218 面板折叠记忆 `localStorage._mtGuardAllDomain` 跨会话留存——当前会话折叠 / 展开 + 跨会话记忆，`#mtguardalldomain` 折叠态存 `localStorage`
刷新恢复，免刷新复位展开态重折叠）⑥ 与 R204 `#mtguardfoldall` 全浮层折叠记忆 / R205 `#mtguardpanelfold` 总览面板折叠记忆 / R211 `#mtguardfoldctl` 折叠全链路面板折叠记忆**语言同**
（R204 `_mtGuardFoldAll` 存 `localStorage._mtGuardFoldAll` 全浮层折叠记忆，R205 `_mtGuardPanelFold` 存 `localStorage._mtGuardPanelFold` 总览面板折叠记忆，R211 `_mtGuardFoldCtl`
存 `localStorage._mtGuardFoldCtl` 折叠全链路面板折叠记忆，R218 `_mtGuardAllDomain` 存 `localStorage._mtGuardAllDomain` 全折叠域总控面板折叠记忆，各面板 / 域折叠记忆 `localStorage`
各管各）⑦ `#mtguardalldomain` 折叠记忆切 IIFE 多 `)` 语法错（`document` click 委托 + `return;` 闭合 + IIFE 闭合多 `)`，首跑 `node=1` `missing ) after argument list`，修正
`return; } });` 后 IIFE 闭合 `})();` 免多 `)` 后 `node=0`，同 R212/R214 IIFE 多 `)` 语法修正纪律）⑧ 验收**函数级**（清 `localStorage._mtGuardAllDomain` + 点 `#mtguardalldomain`
验 `window._mtGuardAllDomain` 切 `true`（折叠）+ `#mtguardalldomains` 隐 + 文案「▸ 展开全折叠域」+ `localStorage._mtGuardAllDomain` 存 `'1'`，再点验 `window._mtGuardAllDomain`
切 `false`（展开）+ 文案「▣ 全折叠域」+ `localStorage._mtGuardAllDomain` 存 `'0'`，不真跑 `mtRun` 免 tick 污染 `runs`；`localStorage` 存 / 读验 `getItem`/`setItem` 值，刷新恢复验
`localStorage` 读值非真刷新 headless，初始同步 IIFE 验 `#mtguardalldomain` 文案 + `#mtguardalldomains` `display` 随初始折叠态）。

---

## 第233轮（前端 R219 · goal round196）：维护守护区全折叠记忆一键重置补全折叠域总控面板折叠记忆联动（`#mtguardfoldreset` 全折叠记忆重置后联动 `#mtguardalldomain` 全折叠域总控面板折叠记忆（`localStorage._mtGuardAllDomain` 清 `'0'` + `window._mtGuardAllDomain` 复位 `false` + `#mtguardalldomain` 文案 / `#mtguardalldomains` `display` 复位展开态），全折叠记忆一键复位后全折叠域总控面板折叠记忆全复位）

**完善性（全折叠记忆复位后全折叠域总控面板折叠记忆全复位免残留）**：R212 `#mtguardfoldreset` 全折叠记忆一键重置清 4 键 `localStorage` + 4 `window` 标志 + 4 折叠钮 +
全浮层复位（R213），但**全折叠域总控面板折叠记忆（R218 `localStorage._mtGuardAllDomain` + `window._mtGuardAllDomain` + `#mtguardalldomain` 文案 + `#mtguardalldomains`
`display`）没联动复位**，`#mtguardfoldreset` 全折叠记忆重置后联动全折叠域总控面板折叠记忆复位——`mtGuardFoldReset`（R212 区）清 4 键 + 4 标志 + 4 折叠钮 + 全浮层复位后补
`localStorage._mtGuardAllDomain` 清 `'0'` + `window._mtGuardAllDomain` 复位 `false` + `#mtguardalldomain` 文案复位「▣ 全折叠域」+ `#mtguardalldomains` `display:none` 复位 +
`clearTimeout(window._mtGuardAllDomainT)`，全折叠记忆一键复位后全折叠域总控面板折叠记忆全复位，与 R212/R213 全折叠记忆重置 / 全浮层复位同域。

**E2E**：`设全折叠态 + 全折叠域总控面板折叠态（5 键全 '1' + 5 标志全 true）→ 点 #mtguardfoldreset → 5 键全清 '0' + 5 标志全 false + #mtguardalldomain 文案复位「▣ 全折叠域」+
#mtguardalldomains display 复位 'none' + toast「已重置维护守护区全折叠记忆」`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图
r219_foldresetalldomain.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 736→738`，断点 `_英文歌\Sunshine Girl.mp3`。

**坑**：① `mtGuardFoldReset`（R212 区）清 4 键 `localStorage` + 4 `window` 标志 + 4 折叠钮文案 / `display` 复位 + 全浮层复位（R213）后补全折叠域总控面板折叠记忆复位
（R219：`try{ localStorage.setItem('_mtGuardAllDomain','0'); }catch(_){}` 清 `localStorage._mtGuardAllDomain` 折叠记忆 + `window._mtGuardAllDomain=false` 复位全折叠域总控
面板折叠标志 + `const _ad=document.getElementById('mtguardalldomain'); if(_ad){ _ad.textContent='▣ 全折叠域'; }` 复位全折叠域总控钮文案展开态 + `const _adD=document.
getElementById('mtguardalldomains'); if(_adD){ _adD.style.display='none'; }` 复位全折叠域总控面板 `display` 隐态 + `clearTimeout(window._mtGuardAllDomainT)` 清 8s 自动隐
定时，全折叠记忆一键复位后全折叠域总控面板折叠记忆全复位，免残留折叠态，与 R212/R213 全折叠记忆重置 + 全浮层复位同域，`mtGuardFoldReset` 全折叠域复位总控）② `localStorage.
_mtGuardAllDomain` 清 `'0'`（全折叠域总控面板折叠记忆键族加 `_mtGuardAllDomain`，同 `_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` 维护守护区
折叠记忆，`try/catch` `localStorage` 不可用降级不记——当前会话 `window._mtGuardAllDomain` 标志仍复位，跨会话不留存，同 R204/R205/R211/R218 `localStorage` 惰性读降级纪律）
③ `#mtguardalldomain` 文案复位「▣ 全折叠域」展开态（`_ad.textContent='▣ 全折叠域'` 全折叠域总控钮展开态默认文案，同 R212 各折叠钮文案复位展开态纪律）
④ `#mtguardalldomains` `display:none` 复位（全折叠域总控面板折叠态隐，展开态由各触发点显，重置不强制显，同 R212/R213 全浮层 `display:none` 复位默认态纪律）⑤ 与 R212
`#mtguardfoldreset` 全折叠记忆重置 / R213 全浮层复位**分工**（R212 清 4 键 `localStorage` + 4 `window` 标志 + 4 折叠钮 + 全浮层复位，R213 补全浮层 `display` 复位，R219 补全
折叠域总控面板折叠记忆复位——全折叠记忆复位 + 全浮层复位 + 全折叠域总控面板折叠记忆复位全复位，`#mtguardfoldreset` 一键复位全折叠域 + 全浮层 + 全折叠域总控面板）⑥ 与 R218
`#mtguardalldomain` 全折叠域总控面板折叠记忆**分工**（R218 全折叠域总控面板折叠记忆 `localStorage._mtGuardAllDomain` 跨会话留存，R219 全折叠记忆重置联动全折叠域总控面板
折叠记忆复位——当前会话全折叠域复位 + 跨会话全折叠域总控面板折叠记忆复位，`#mtguardfoldreset` 全折叠记忆一键复位后全折叠域总控面板折叠记忆全复位）⑦ 验收**函数级**（设全
折叠态 + 全折叠域总控面板折叠态（5 键 `'1'` + 5 标志 `true`）+ 点 `#mtguardfoldreset` 验 5 键全清 `'0'`（含 `localStorage._mtGuardAllDomain`）+ 5 标志全 `false`（含
`window._mtGuardAllDomain`）+ `#mtguardalldomain` 文案复位「▣ 全折叠域」+ `#mtguardalldomains` `display` 复位 `'none'` + toast「已重置维护守护区全折叠记忆」，不真跑 `mtRun`
免 tick 污染 `runs`；`localStorage` 存 / 读验 `getItem`/`setItem` 值，全折叠域总控面板折叠记忆复位验 5 键 / 5 标志 / 文案 / `display` 全复位）。

---

## 第234轮（前端 R220 · goal round197）：维护守护区全折叠记忆重置详情补全折叠域总控面板折叠记忆字段（`#mtguardfoldresetcopy` / `#mtguardfoldresetpng` 重置详情补 `localStorage._mtGuardAllDomain` 全折叠域总控面板折叠记忆复位值 + `window._mtGuardAllDomain` 标志 + `#mtguardalldomain` 文案 + `#mtguardalldomains` `display` 字段，重置详情自含全折叠域总控面板折叠记忆复位状态）

**完善性（重置详情自含全折叠域总控面板折叠记忆复位状态）**：R214/R215 `#mtguardfoldresetcopy` / `#mtguardfoldresetpng` 重置详情（4 键 + 4 标志 + 4 折叠钮 + 6 浮层 + 时间戳），但**全折叠域总控面板
折叠记忆（R218 `localStorage._mtGuardAllDomain` + `window._mtGuardAllDomain` + `#mtguardalldomain` 文案 + `#mtguardalldomains` `display`）字段没进重置详情**，`mtGuardFoldResetCopy`
（R214）/ `mtGuardFoldResetPng`（R215）重置详情补全折叠域总控面板折叠记忆字段（5 键 + 5 标志 + 5 折叠钮 + 7 浮层 + 时间戳），重置详情自含全折叠域总控面板折叠记忆复位状态，与 R214/R215
重置详情文本 / PNG 同域。`mtGuardFoldResetCopy`（R214 区）/ `mtGuardFoldResetPng`（R215 区）改：`_ls`/`_w` 加 `localStorage._mtGuardAllDomain` / `window._mtGuardAllDomain`（5 键 / 5
标志），`_btns` 加 `#mtguardalldomain`（5 折叠钮），`_floors` 加 `#mtguardalldomains`（7 浮层），`_lines` 各分块拼 5 键 / 5 标志 / 5 折叠钮 / 7 浮层，色带循环 4→5 / 6→7。

**E2E**：`设 5 键全 '1' → 点 #mtguardfoldreset（全折叠记忆重置）→ 点 #mtguardfoldresetcopy → toast「已复制全折叠记忆重置详情」+ 5 键全清 '0'（含 localStorage._mtGuardAllDomain）`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r220_resetcopy5key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 738→740`，断点 `_英文歌\Yesterday Once More.mp3`。

**坑**：① `mtGuardFoldResetCopy`（R214 区）/ `mtGuardFoldResetPng`（R215 区）重置详情补全折叠域总控面板折叠记忆字段（`_ls` 加 `localStorage.getItem('_mtGuardAllDomain')`（5 键
`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`），`_w` 加 `window._mtGuardAllDomain`（5 标志），`_btns` 加 `mtguardalldomain`（5 折叠钮
`mtmetfold`/`mtguardpanelfold`/`mtguardfoldall`/`mtguardfoldctl`/`mtguardalldomain`），`_floors` 加 `mtguardalldomains`（7 浮层 `mtguardpaneld`/`mtguardfoldctld`/`mtguardfoldstatd`/
`mtstatebardtl`/`mtmetsumdetail`/`mtkeyhintdetail`/`mtguardalldomains`），`_lines` 各分块拼 5 键 / 5 标志 / 5 折叠钮 / 7 浮层，色带循环 4→5 / 6→7，重置详情自含全折叠域总控面板折叠
记忆复位状态，与 R214/R215 重置详情文本 / PNG 同域）② `mtGuardFoldResetCopy` / `mtGuardFoldResetPng` 实际 `const _ls`（非 `let _ls`，R214/R215 各函数体 `const` 声明，按 `const _ls`
精确改，`replace_all` 全匹配行——4610 `mtGuardFoldResetPng` / 4660 `mtGuardFoldAllDomain` / 4735 `mtGuardAllDomainCopy` 各 `const _ls` 区，`mtGuardFoldResetCopy` 在 4610 区
`const _ls` + `const _w` + `const _btns` + `const _floors` 各补 1 字段，循环 `_i<4`→`_i<5` / `_i<6`→`_i<7`，色带 5 键 / 5 标志 / 5 折叠钮 / 7 浮层全拼）③ 与 R214 `#mtguardfoldresetcopy` /
R215 `#mtguardfoldresetpng` 重置详情**分工**（R214/R215 重置详情 4 键 + 4 标志 + 4 折叠钮 + 6 浮层，R220 补全折叠域总控面板折叠记忆字段——5 键 + 5 标志 + 5 折叠钮 + 7 浮层，重置详情
自含全折叠域总控面板折叠记忆复位状态，`#mtguardfoldresetcopy` / `#mtguardfoldresetpng` 重置详情补全全折叠域总控面板字段）④ 与 R219 全折叠记忆重置联动全折叠域总控面板折叠记忆复位**分工**
（R219 全折叠记忆重置联动全折叠域总控面板折叠记忆复位（`#mtguardfoldreset` 一键复位后全折叠域总控面板折叠记忆全复位），R220 重置详情补全折叠域总控面板折叠记忆字段（重置详情自含全
折叠域总控面板复位状态），全折叠域总控面板复位 + 重置详情自含全折叠域字段双路）⑤ 与 R158/R198/R200/R208/R215 PNG 导出 + R196/R201/R208/R214 复制出口**语言同**（各重置详情 / PNG /
文本复制读各数据源拼文本 / 色带，`navigator.clipboard.writeText` 降级 / `canvas` 转 PNG 下载，重置详情补全折叠域总控面板字段同语言，重置详情自含全折叠域出口标位）⑥ 验收**函数级**（设
5 键全 `'1'` + 点 `#mtguardfoldreset` 全折叠记忆重置 + 点 `#mtguardfoldresetcopy` 验 toast「已复制全折叠记忆重置详情」+ 5 键全清 `'0'`（含 `localStorage._mtGuardAllDomain`），不真跑
`mtRun` 免 tick 污染 `runs`；重置详情 5 键 / 5 标志 / 5 折叠钮 / 7 浮层拼逻辑验 toast 出口，`_mtGuardAllDomain` 字段进重置详情文本 / PNG，复制 / 下载 headless 验 toast 出口，真剪贴板 /
PNG 内容不验）。

---

## 第235轮（前端 R221 · goal round198）：维护守护区全折叠域总控面板补当前态完整（`#mtguardalldomaincopy` 全折叠域总控文本 + `#mtguardalldomainpng` 全折叠域总控 PNG 补全折叠域总控面板六块中各 `localStorage` 键 / `window` 标志 / 折叠钮 / 浮层 `display` 实时值，全折叠域总控面板 PNG / 文本自含全折叠域当前态完整）

**完善性（全折叠域总控面板 PNG / 文本自含全折叠域当前态完整）**：R217 `#mtguardalldomaincopy` / `#mtguardalldomainpng` 全折叠域总控面板 PNG / 文本已含六块，但**各块
`localStorage` 键 / `window` 标志 / 折叠钮 / 浮层 `display` 实时值要全折叠域当前态完整**（`mtGuardAllDomain`（R216 区）六块 `_ls` 已 5 键 / `_btns` 已 5 折叠钮 / `_floors` 已 7 浮层，
但色带 / 文案 / 浮层循环只拼前 4/4/6 项，第 5 键 / 第 5 折叠钮 / 第 7 浮层没拼进 SVG；`mtGuardAllDomainCopy`（R217 区）`_ls` 缺第 5 元素（`_ls[4]` 引用但只定义 4 元素 =
`undefined`），`_btns` / `_floors` 缺全折叠域字段），`mtGuardAllDomain`（R216 区）六块补 5 键 / 5 折叠钮 / 7 浮层当前态完整（循环 4→5 / 6→7 + `_key` 数组加 `_mtGuardAllDomain`），
`mtGuardAllDomainCopy`（R217 区）补 5 键 / 5 折叠钮 / 7 浮层（`_ls` 加第 5 元素 + `_btns` / `_floors` 加全折叠域字段 + 循环 4→5 / 6→7），全折叠域总控面板 PNG / 文本自含全折叠域
当前态完整，与 R217 全折叠域总控面板 PNG / 文本同域。

**E2E**：`设 5 键全 '1' → 点 #mtguardalldomain 生成面板 → #mtguardalldomains SVG 含 5 键（_mtGuardAllDomain）+ 5 折叠钮（mtguardalldomain）+ 7 浮层（mtguardalldomains）当前态`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r221_alldomaincurstate.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 740→742`，断点 `_草东没有派对\模样.mp3`。

**坑**：① `mtGuardAllDomain`（R216 区）六块补 5 键 / 5 折叠钮 / 7 浮层当前态完整（`_ls` 已 5 键 `[' _mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll','_mtGuardFoldCtl','_mtGuardAllDomain']`、
`_btns` 已 5 折叠钮 `['mtmetfold','mtguardpanelfold','mtguardfoldall','mtguardfoldctl','mtguardalldomain']`、`_floors` 已 7 浮层 `['mtguardpaneld','mtguardfoldctld','mtguardfoldstatd',
'mtstatebardtl','mtmetsumdetail','mtkeyhintdetail','mtguardalldomains']`，但色带 / 文案 / 浮层循环只拼前 4/4/6 项（`for(let _i=0;_i<4;_i++)`），第 5 键 / 第 5 折叠钮 / 第 7 浮层没拼进
SVG——修循环 4→5 / 6→7（`for(let _i=0;_i<5;_i++)` 色带 / 文案 / `for(let _i=0;_i<7;_i++)` 浮层）+ `_key` 数组加 `_mtGuardAllDomain`（`[' _mtMetFold','_mtGuardPanelFold','_mtGuardFoldAll',
'_mtGuardFoldCtl','_mtGuardAllDomain']`），全折叠域总控面板 SVG 拼 5 键 / 5 折叠钮 / 7 浮层当前态完整）② `mtGuardAllDomainCopy`（R217 区）补 5 键 / 5 折叠钮 / 7 浮层（`_ls` 原只 4 元素但
`_lines` 引用 `_ls[4]`（`_mtGuardAllDomain`）= `undefined`（`· _mtGuardAllDomain=undefined`），修 `_ls` 加第 5 元素 `localStorage.getItem('_mtGuardAllDomain')||'0'`（5 键）+ `_btns` 加
`mtguardalldomain`（5 折叠钮）+ 循环 4→5 + `_floors` 加 `mtguardalldomains`（7 浮层）+ 循环 6→7，全折叠域总控文本拼 5 键 / 5 折叠钮 / 7 浮层当前态完整，免 `undefined` 字段）③
`mtGuardAllDomainPng`（R217 区）读 `#mtguardalldomains` 内联 SVG（`mtGuardAllDomain` 拼），`mtGuardAllDomain` 六块补 5 键 / 5 折叠钮 / 7 浮层当前态完整后，全折叠域总控 PNG 自动含 5 键 /
5 折叠钮 / 7 浮层当前态，无需 `mtGuardAllDomainPng` 改（PNG 读 SVG 当前态自动完整）④ 与 R217 `#mtguardalldomaincopy` / `#mtguardalldomainpng` 全折叠域总控面板 PNG / 文本**分工**
（R217 六块各数据源，R221 补 5 键 / 5 折叠钮 / 7 浮层当前态完整——全折叠域总控面板 PNG / 文本自含全折叠域当前态完整，`#mtguardalldomaincopy` 文本 + `#mtguardalldomainpng` PNG 双出口
当前态完整）⑤ 与 R214/R215 重置详情 / R220 重置详情补全折叠域字段**语言同**（各重置详情 / 全折叠域总控读各数据源拼文本 / 色带，`navigator.clipboard.writeText` 降级 / `canvas` 转
PNG 下载，全折叠域总控面板当前态完整同语言，各出口自含全折叠域出口标位）⑥ 验收**函数级**（设 5 键全 `'1'` + 点 `#mtguardalldomain` 生成面板 + 验 `#mtguardalldomains` `innerHTML` 含
`<svg` + 5 键（`_mtGuardAllDomain=`）+ 5 折叠钮（`mtguardalldomain=`）+ 7 浮层（`mtguardalldomains=`）当前态，不真跑 `mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验 5 键 / 5 折叠钮 / 7
浮层字段进 SVG，非真渲染像素）。

---

## 第236轮（前端 R222 · goal round199）：维护守护区维护守护全记录面板补全折叠域字段（`#mtguardcopy` 四段全复制 + `#mtguardsnap` 四段数据快照内联 SVG 补全折叠域总控面板 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态字段，维护守护全记录自含全折叠域当前态）

**完善性（维护守护全记录自含全折叠域当前态）**：R219/R220/R221 全折叠域总控面板 / 重置详情补全折叠域字段（5 键 + 5 标志 + 5 折叠钮 + 7 浮层），但**`#mtguard` 维护守护全记录 /
`#mtguardcopy` 四段全复制（R196/R197 区）没全折叠域字段**（维护守护全记录 / 四段全复制要自含全折叠域当前态，`mtGuardCopy`（R196 区，`#mtguardcopy` 四段全复制）补第 5 段
「全折叠域当前态」（5 键 `localStorage` + 5 标志 `window` + 5 折叠钮文案 + 7 浮层 `display`），`mtGuardSnap`（R197 区，`#mtguardsnap` 四段数据快照内联 SVG）补第 5 段全折叠域
5 键色带（`_H=150`→`210`），维护守护全记录自含全折叠域当前态，与 R219/R220/R221 全折叠域字段同域。

**E2E**：`设 5 键全 '1' → 点 #mtguardsnap 生成快照（#mtguardsnapd SVG 含全折叠域 5 键色带）；点 #mtguardcopy → toast「已复制维护守护全记录（四段）」（四段全复制含全折叠域当前态段）`
（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r222_guardallfold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 742→744`，断点 `_薛之谦\我好像在哪见过你.mp3`。

**坑**：① `mtGuardCopy`（R196 区）四段全复制（双指标逐轮 / 状态详情 / 全库完成详情 / 键盘流触发记录）补第 5 段「全折叠域当前态」（`_fl5` 5 键 `localStorage`（`_mtMetFold`/
`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`，`||'0'` 降级）+ `_wl5` 5 标志 `window`（各布尔值）+ `_btns5` 5 折叠钮（`#mtmetfold`/`#mtguardpanelfold`/
`#mtguardfoldall`/`#mtguardfoldctl`/`#mtguardalldomain` 各 `textContent`）+ `_floors5` 7 浮层（`#mtguardpaneld`/`#mtguardfoldctld`/`#mtguardfoldstatd`/`#mtstatebardtl`/
`#mtmetsumdetail`/`#mtkeyhintdetail`/`#mtguardalldomains` 各 `style.display`），`_all+=` 拼「[全折叠域当前态]」段（`localStorage 5键` + `window 5标志` + 5 折叠钮 + 7 浮层各值），
维护守护全记录四段全复制自含全折叠域当前态，与 R196 四段全复制 + R219/R220/R221 全折叠域字段同域）② `mtGuardSnap`（R197 区）四段数据快照内联 SVG（双指标柱状 / 状态色带 /
全库完成徽标 / 键盘流顺序条）补第 5 段全折叠域 5 键色带（`_fl5s` 5 键 `localStorage` + `_knames` 5 键名 + `_scw` 色带宽 + 循环拼 5 色带 `rect`（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠
`--bad` 红）+ 键名缩写（`replace('_mt','')`）+ 值，`_H=150`→`210` 加高容第 5 段，维护守护全记录快照自含全折叠域 5 键当前态色带，与 R197 四段快照 + R219/R220/R221 全折叠域字段
同域）③ `mtGuardSnapPng`（R198 区）读 `#mtguardsnapd` 内联 SVG（`mtGuardSnap` 拼），`mtGuardSnap` 补第 5 段全折叠域 5 键色带后，全折叠域 5 键快照 PNG 自动含第 5 段，无需
`mtGuardSnapPng` 改（PNG 读 SVG 当前态自动完整，同 R221 `mtGuardAllDomainPng` 读 `#mtguardalldomains` SVG 自动含全折叠域字段纪律）④ 与 R196 `#mtguardcopy` 四段全复制 /
R197 `#mtguardsnap` 四段数据快照**分工**（R196/R197 四段全复制 / 四段快照（双指标 / 状态 / 全库完成 / 键盘流），R222 补第 5 段全折叠域当前态（5 键 / 5 标志 / 5 折叠钮 / 7 浮层）
——维护守护全记录四段 + 全折叠域第五段，全记录自含全折叠域当前态）⑤ 与 R219/R220/R221 全折叠域字段**语言同**（各全折叠域总控 / 重置详情 / 维护守护全记录读 5 键 `localStorage` +
5 标志 `window` + 5 折叠钮 + 7 浮层拼文本 / 色带，全折叠域当前态同语言，各出口自含全折叠域出口标位）⑥ 验收**函数级**（设 5 键全 `'1'` + 点 `#mtguardsnap` 生成快照验 `#mtguardsnapd`
`innerHTML` 含 `<svg` + 全折叠域 5 键色带（`MetFold=` 或 `mtMetFold`）+ 点 `#mtguardcopy` 验 toast「已复制维护守护全记录（四段）」（四段全复制含全折叠域当前态段），不真跑
`mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验 5 键色带进 SVG + 四段全复制文本含全折叠域段，非真渲染像素 / 剪贴板内容）。

---

## 第237轮（前端 R223 · goal round200）：维护守护区能力 / 出口总览面板补全折叠域字段（`#mtguardpanel` 能力 / 出口总览内联 SVG + `#mtguardpanelcopy` 总览文本补全折叠域 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态字段，能力 / 出口总览自含全折叠域当前态）

**完善性（能力 / 出口总览自含全折叠域当前态）**：R222 `#mtguardcopy` / `#mtguardsnap` 维护守护全记录 / 快照补全折叠域字段，但**`#mtguardpanel` 能力 / 出口总览（R199 区，六块）没全折叠域字段**（能力 / 出口总览要自含全折叠域当前态，
`mtGuardPanel`（R199 区）补块 7「全折叠域当前态」（5 键 `localStorage` 色带 + 5 折叠钮 + 7 浮层，`_H=210`→`270`），`mtGuardPanelCopy`（R201 区）总览文本补第 7 段「全折叠域当前态」（5 键 + 5 标志 + 5 折叠钮 + 7 浮层），
能力 / 出口总览自含全折叠域当前态，与 R222 维护守护全记录补全折叠域字段同域。

**E2E**：`设 5 键全 '1' → 点 #mtguardpanel 生成总览（#mtguardpaneld SVG 含全折叠域当前态块）；点 #mtguardpanelcopy → toast「已复制维护守护区总览文本」（总览文本含全折叠域当前态段）`（绿）；端点 **30/0**、
JS undefined NONE、CSS 320/320、node 0、console 0、截图 r223_panelallfold.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 744→746`，断点 `_赵雷\南方姑娘2.mp3`。

**坑**：① `mtGuardPanel`（R199 区）六块内联 SVG（三键状态灯 + 触发记录 / 四段数据源 / 复制出口 / 快照 PNG 出口 / 键盘三操作 + 状态同态 / 全库 ∞ + 完成态）补块 7「全折叠域当前态」（`_fl7` 5 键 `localStorage`（`_mtMetFold`/
`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`，`||'0'` 降级）+ `_kn7` 5 键名缩写（`Met`/`Pan`/`All`/`Ctl`/`Dom`，色带 `rect`（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠 `--bad` 红）+ 值 +
`_btns7` 5 折叠钮（`#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`/`#mtguardfoldctl`/`#mtguardalldomain` 各 `textContent`），`_H=210`→`270` 加高容块 7，能力 / 出口总览自含全折叠域当前态，与 R222 维护守护全记录
补全折叠域字段同域）② `mtGuardPanelCopy`（R201 区）总览文本六段（三键状态灯 + 触发记录 / 四段数据源 / 复制出口 / 快照 PNG 出口 / 键盘三操作 + 状态同态 / 全库 ∞ + 完成态）补第 7 段「全折叠域当前态」（`_flc` 5 键
`localStorage` + `_wlc` 5 标志 `window` + `_b7` 5 折叠钮 + `_f7` 7 浮层，`_lines+=` 拼「[全折叠域当前态]」段（`localStorage 5键` + `window 5标志` + 5 折叠钮 + 7 浮层各值），总览文本自含全折叠域当前态，与 R222 维护守护全记录
补全折叠域字段同域）③ `mtGuardPanelPng`（R200 区）读 `#mtguardpaneld` 内联 SVG（`mtGuardPanel` 拼），`mtGuardPanel` 补块 7 全折叠域当前态后，总览 PNG 自动含块 7，无需 `mtGuardPanelPng` 改（PNG 读 SVG 当前态自动
完整，同 R221 `mtGuardAllDomainPng` 读 `#mtguardalldomains` SVG 自动含全折叠域字段 / R222 `mtGuardSnapPng` 读 `#mtguardsnapd` SVG 自动含全折叠域 5 键纪律）④ 与 R199 `#mtguardpanel` 能力 / 出口总览 / R201
`#mtguardpanelcopy` 总览文本**分工**（R199/R201 能力 / 出口总览六块（三键状态灯 / 四段数据源 / 复制出口 / 快照 PNG 出口 / 键盘三操作 + 状态同态 / 全库 ∞ + 完成态），R223 补块 7 / 第 7 段全折叠域当前态（5 键 /
5 标志 / 5 折叠钮 / 7 浮层）——能力 / 出口总览六块 + 全折叠域第七块，总览自含全折叠域当前态）⑤ 与 R222 维护守护全记录补全折叠域字段**语言同**（各维护守护全记录 / 能力出口总控读 5 键 `localStorage` + 5 标志
`window` + 5 折叠钮 + 7 浮层拼文本 / 色带，全折叠域当前态同语言，各出口自含全折叠域出口标位）⑥ 验收**函数级**（设 5 键全 `'1'` + 点 `#mtguardpanel` 生成总览验 `#mtguardpaneld` `innerHTML` 含 `<svg` + 全折叠域
当前态块 + 点 `#mtguardpanelcopy` 验 toast「已复制维护守护区总览文本」（总览文本含全折叠域当前态段），不真跑 `mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验全折叠域块进 SVG + 总览文本含全折叠域段，非真渲染像素 /
剪贴板内容）。

---

## 第238轮（前端 R224 · goal round201）：维护守护区三域折叠态总览面板补全折叠域字段（`#mtguardfoldstat` 三域折叠态总览内联 SVG + `#mtguardfoldstatcopy` 三域折叠态文本 + `#mtguardfoldstatpng` 三域折叠态 PNG 补全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态字段，三域折叠态总览自含全折叠域当前态）

**完善性（三域折叠态总览自含全折叠域当前态）**：R222/R223 `#mtguardcopy` / `#mtguardpanel` 维护守护全记录 / 能力出口总览补全折叠域字段，但**`#mtguardfoldstat` 三域折叠态总览（R207 区）只 3 域没全折叠域 5 域**
（三域：`_mtMetFold` 双图区 / `_mtGuardPanelFold` 总览面板 / `_mtGuardFoldAll` 全浮层，缺 `_mtGuardFoldCtl` 折叠全链路 / `_mtGuardAllDomain` 全折叠域总控面板），`mtGuardFoldStat`（R207 区）补全折叠域 5 域（`_domains`
3→5，加 `{name:'折叠全链路', btn:'#mtguardfoldctl', fold:_ctlFold, lsKey:'_mtGuardFoldCtl'}` + `{name:'全折叠域总控', btn:'#mtguardalldomain', fold:_domFold, lsKey:'_mtGuardAllDomain'}`，循环 3→5，`_H=140`→`200`，
标题「三域」→「全折叠域 5 域」）+ `mtGuardFoldStatCopy`（R208 区）补 2 域 + 全折叠域 5 键当前态段（`_ctlFold2`/`_domFold2` 惰性读 + 5 域文本 + `[全折叠域当前态]` 5 键段，toast「三域」→「全折叠域 5 域」），
三域折叠态总览自含全折叠域当前态，与 R222/R223 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' → 点 #mtguardfoldstat 生成折叠态总览（#mtguardfoldstatd SVG 含全折叠域 5 域：双图区 / 总览面板 / 全浮层 / 折叠全链路 / 全折叠域总控）；点 #mtguardfoldstatcopy → toast「已复制全折叠域 5 域
折叠态文本」（文本含 5 域 + 全折叠域 5 键当前态段）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r224_foldstat5.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 746→748`，断点 `_赵雷\需要人陪.mp3`。

**坑**：① `mtGuardFoldStat`（R207 区）三域折叠态总览内联 SVG（`_domains` 3 元素：双图区 / 总览面板 / 全浮层，`_H=140`）补全折叠域 5 域（`_domains` 3→5，加 `{name:'折叠全链路', btn:'#mtguardfoldctl', fold:_ctlFold,
lsKey:'_mtGuardFoldCtl'}` + `{name:'全折叠域总控', btn:'#mtguardalldomain', fold:_domFold, lsKey:'_mtGuardAllDomain'}`，惰性读补 `_ctlFold`/`_domFold`（`localStorage.getItem('_mtGuardFoldCtl')==='1'` /
`localStorage.getItem('_mtGuardAllDomain')==='1'`，`try/catch` 降级 `false`），循环 3→5（`for(let _i=0;_i<5;_i++)` 各域折叠色带 `rect`（折叠 `--warn` 黄 / 展开 `--ok` 绿）+ `localStorage` 记忆标位），`_H=140`→`200`
加高容 5 域，标题「维护守护区三域折叠态总览」→「维护守护区全折叠域5域折叠态总览」，三域折叠态总览自含全折叠域 5 域当前态，与 R207 三域折叠态总控 + R222/R223 补全折叠域字段同域）② `mtGuardFoldStatCopy`
（R208 区）三域折叠态文本（`_metFold`/`_pfFold`/`_allFold` 惰性读 + 3 域文本）补 2 域（`_ctlFold2`/`_domFold2` 惰性读 `localStorage.getItem('_mtGuardFoldCtl')==='1'` / `localStorage.getItem('_mtGuardAllDomain')==='1'`
`try/catch` 降级）+ 全折叠域 5 键当前态段（`_flc2` 5 键 `localStorage`（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`，`||'0'` 降级），`_lines+=` 拼「[折叠全链路 #mtguardfoldctl] ·
折叠/展开 · localStorage _mtGuardFoldCtl=1/0」+「[全折叠域总控 #mtguardalldomain] · 折叠/展开 · localStorage _mtGuardAllDomain=1/0」+「[全折叠域当前态] localStorage 5键: ...」，标题「#music3 三域折叠态总览」→「#music3
全折叠域5域折叠态总览」，toast「已复制三域折叠态文本」→「已复制全折叠域5域折叠态文本」，三域折叠态文本自含全折叠域 5 域 + 5 键当前态，与 R208 三域折叠态复制 + R222/R223 补全折叠域字段同域）③ `mtGuardFoldStatPng`
（R208 区）读 `#mtguardfoldstatd` 内联 SVG（`mtGuardFoldStat` 拼），`mtGuardFoldStat` 补全折叠域 5 域后，三域折叠态 PNG 自动含 5 域，无需 `mtGuardFoldStatPng` 改（PNG 读 SVG 当前态自动完整，同 R221 `mtGuardAllDomainPng` /
R222 `mtGuardSnapPng` / R223 `mtGuardPanelPng` 读各内联 SVG 自动含全折叠域字段纪律）④ 与 R207 `#mtguardfoldstat` 三域折叠态总览 / R208 `#mtguardfoldstatcopy` 三域折叠态文本**分工**（R207/R208 三域折叠态总览 / 文本
（双图区 / 总览面板 / 全浮层），R224 补全折叠域 5 域（加折叠全链路 / 全折叠域总控面板）——三域折叠态总览 → 全折叠域 5 域折叠态总览，自含全折叠域当前态）⑤ 与 R222 维护守护全记录 / R223 能力出口总览补全折叠域字段**语言同**
（各全折叠域 / 三域折叠态总览读 5 键 `localStorage` + 各域 `textContent` / `display` 拼文本 / 色带，全折叠域当前态同语言，各出口自含全折叠域出口标位）⑥ 验收**函数级**（设 5 键全 `'1'` + 点 `#mtguardfoldstat` 生成
折叠态总览验 `#mtguardfoldstatd` `innerHTML` 含 `<svg` + 全折叠域 5 域（`全折叠域5域` + `折叠全链路` + `全折叠域总控`）+ 点 `#mtguardfoldstatcopy` 验 toast「已复制全折叠域5域折叠态文本」（文本含 5 域 + 全折叠域 5 键
当前态段），不真跑 `mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验 5 域进 SVG + 文本含 5 域 / 5 键段，非真渲染像素 / 剪贴板内容）。

---

## 第239轮（前端 R225 · goal round202）：维护守护区折叠全链路总控面板补全折叠域字段（`#mtguardfoldctl` 折叠全链路总控内联 SVG + `#mtguardfoldctscopy` 全链路文本 + `#mtguardfoldctlpng` 全链路 PNG 补全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态字段，折叠全链路总控自含全折叠域当前态）

**完善性（折叠全链路总控自含全折叠域当前态）**：R224 `#mtguardfoldstat` 三域折叠态总览补全折叠域 5 域，但**`#mtguardfoldctl` 折叠全链路总控（R209 区，六块）没全折叠域 5 域**（块 1 三域折叠钮只 3 域，没折叠全链路 / 全折叠域总控面板，块 3 折叠记忆只 3 键，块 4 三域折叠态总览没全折叠域 5 域），`mtGuardFoldCtl`（R209 区）补全折叠域 5 域字段（块 1 三域折叠钮 → 全折叠域 5 域折叠钮 3→5 + 块 3 折叠记忆补 2 键 + 块 4 三域 → 全折叠域 5 域 + 块 5 全折叠域 5 键当前态色带 + 块 6 折叠态 PNG / 文本，`_H=180`→`236`），`mtGuardFoldCtlCopy`（R210 区）补 5 域（`[三域折叠钮]` → `[全折叠域5域折叠钮]` + `[折叠记忆]` 补 2 键 + `[三域折叠态总览]` → `[全折叠域5域折叠态总览]` + 补 `[全折叠域当前态]` 5 键段），折叠全链路总控自含全折叠域当前态，与 R222/R223/R224 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' → 直接调 mtGuardFoldCtl() 拼面板 → #mtguardfoldctld SVG 含全折叠域 5 域折叠钮（#mtguardfoldctl 折叠全链路 + #mtguardalldomain 全折叠域）+ 全折叠域当前态；点 #mtguardfoldctscopy → toast「已复制折叠全链路文本」（全链路文本含全折叠域 5 域）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r225_foldctl5.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 748→750`，断点 `_赵雷合集\程艾影.mp3`。

**坑**：① `mtGuardFoldCtl`（R209 区）六块内联 SVG（块 1 三域折叠钮 / 块 2 折叠联动 R206 / 块 3 折叠记忆 R204/R205 / 块 4 三域折叠态总览 R207 / 块 5 折叠态 PNG 文本 R208 / 块 6 折叠全链路 R209/R210，`_H=180`）补全折叠域 5 域（块 1 三域折叠钮 → 全折叠域 5 域折叠钮（`_fbtns` 3→5 加 `#mtguardfoldctl 折叠全链路(R209)` + `#mtguardalldomain 全折叠域(R216)`，循环 3→5，块 1 高度 48→66），块 3 折叠记忆补 2 键（`localStorage _mtGuardFoldCtl(全链路)` + `localStorage _mtGuardAllDomain(全折叠域)`，块 3 高度 48→66），块 4 三域折叠态总览 → 全折叠域 5 域折叠态总览（R207/R224，块 4 高度 48→66），块 5 全折叠域 5 键当前态色带（`_fl5c` 5 键 `localStorage` + `_kn5c` 5 键名缩写（`Met`/`Pan`/`All`/`Ctl`/`Dom`）+ 循环拼 5 色带 `rect`（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠 `--bad` 红）+ 值），块 6 折叠态 PNG / 文本（`#mtguardfoldstatpng` / `#mtguardfoldstatcopy` / `#mtguardfoldctlpng` / `#mtguardfoldctlcopy`），`_H=180`→`236` 加高容全折叠域 5 域，折叠全链路总控自含全折叠域当前态，与 R222/R223/R224 补全折叠域字段同域）② `mtGuardFoldCtlCopy`（R210 区）全链路文本六段（三域折叠钮 / 折叠联动 / 折叠记忆 / 三域折叠态总览 / 折叠态 PNG 文本 / 折叠全链路）补全折叠域 5 域（`[三域折叠钮]` → `[全折叠域5域折叠钮]`（5 域：双图区 R159 / 总览面板 R202 / 全浮层 R203 / 折叠全链路 R209 / 全折叠域 R216），`[折叠记忆]` 补 2 键（`_g4` `localStorage._mtGuardFoldCtl` + `_g5` `localStorage._mtGuardAllDomain`，`try/catch` 降级 `'0'`），`[三域折叠态总览]` → `[全折叠域5域折叠态总览]`（R207/R224），补 `[全折叠域当前态]` 5 键段（`localStorage 5键: _mtMetFold=... · _mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...`），全链路文本自含全折叠域 5 域 + 5 键当前态，与 R222/R223/R224 补全折叠域字段同域）③ `mtGuardFoldCtlPng`（R210 区）读 `#mtguardfoldctld` 内联 SVG（`mtGuardFoldCtl` 拼），`mtGuardFoldCtl` 补全折叠域 5 域后，全链路 PNG 自动含 5 域，无需 `mtGuardFoldCtlPng` 改（PNG 读 SVG 当前态自动完整，同 R221/R222/R223/R224 各 PNG 读内联 SVG 自动含全折叠域字段纪律）④ 与 R209 `#mtguardfoldctl` 折叠全链路总控 / R210 `#mtguardfoldctscopy` 全链路文本**分工**（R209/R210 折叠全链路六块（三域折叠钮 / 折叠联动 / 折叠记忆 / 三域折叠态总览 / 折叠态 PNG 文本 / 折叠全链路），R225 补全折叠域 5 域（块 1 → 全折叠域 5 域折叠钮 + 块 3 → 全折叠域 5 键 + 块 4 → 全折叠域 5 域折叠态总览 + 块 5 → 全折叠域 5 键当前态）——折叠全链路总控自含全折叠域当前态）⑤ 与 R222 维护守护全记录 / R223 能力出口总览 / R224 三域折叠态总览补全折叠域字段**语言同**（各全折叠域 / 三域折叠态 / 全链路读 5 键 `localStorage` + 各域 `textContent` / `display` 拼文本 / 色带，全折叠域当前态同语言，各出口自含全折叠域出口标位）⑥ 验收**函数级**（设 5 键全 `'1'` + 直接调 `mtGuardFoldCtl()` 拼内联 SVG（绕 R211 折叠记忆切态——设 `_mtGuardFoldCtl='1'` 后点 `#mtguardfoldctl` 走 R211 折叠记忆切（当前折叠态 → 切展开才拼面板），验收直接调 `mtGuardFoldCtl()` 免切态干扰）+ 验 `#mtguardfoldctld` `innerHTML` 含 `<svg` + 全折叠域 5 域折叠钮（`全折叠域5域折叠钮` + `#mtguardfoldctl 折叠全链路` + `#mtguardalldomain 全折叠域`）+ 全折叠域当前态 + 点 `#mtguardfoldctscopy` 验 toast「已复制折叠全链路文本」（全链路文本含全折叠域 5 域 / 5 键段），不真跑 `mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验 5 域进 SVG + 文本含 5 域 / 5 键段，非真渲染像素 / 剪贴板内容）。

---

## 第240轮（前端 R226 · goal round203）：维护守护区双图区明细面板补全折叠域字段（`#mtmetsumdetail` 双图区 hover 明细浮层 + `#mtmetsumdetailcopy` 双指标逐轮明细文本补全折叠域 5 键当前态字段，双图区明细自含全折叠域当前态）

**完善性（双图区明细自含全折叠域当前态）**：R224/R225 三域折叠态总览 / 折叠全链路总控补全折叠域 5 域，但**`#mtmetsumdetail` 双图区 hover 明细浮层 / `#mtmetsumdetailcopy` 双指标逐轮明细文本（R188/R189 区）没全折叠域 5 键**（双图区明细要自含全折叠域当前态，
`mtMetSumDetailCopy`（R189 区）双指标逐轮明细文本（近 N 次逐轮 + 均值 + 合计）补 `[全折叠域当前态]` 5 键段（`localStorage 5键: _mtMetFold=... · _mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...`），`#mtmetsumdetail`
hover 明细浮层（R188 区）同补 5 键段（与 `mtMetSumDetailCopy` 同步），双图区明细自含全折叠域当前态，与 R222/R223/R224/R225 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' + 设双指标历史 → 点 #mtmetsumdetailcopy → toast「已复制双指标逐轮明细（3 次）」（双图区明细文本含全折叠域 5 键当前态段）；#mtmetsum mouseenter → #mtmetsumdetail hover 明细浮层 innerHTML 含全折叠域当前态段`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r226_metdetail5key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 750→752`，断点 `_郑寒木\少年锦时.mp3`。

**坑**：① `mtMetSumDetailCopy`（R189 区）双指标逐轮明细文本（`#music3 双指标逐轮明细 · <ts>` + 近 N 次逐轮 + 均值 / 合计，`navigator.clipboard.writeText` 降级 `_copyFallback`）补 `[全折叠域当前态]` 5 键段（`_fl26` 5 键
`localStorage`（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`，`||'0'` 降级），`_lines+=` 拼「[全折叠域当前态] localStorage 5键: _mtMetFold=... · _mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... ·
_mtGuardAllDomain=...」，双指标逐轮明细文本自含全折叠域 5 键当前态，与 R222/R223/R224/R225 补全折叠域字段同域，`#mtmetsumdetailcopy` 复制出口补全折叠域段）② `#mtmetsumdetail` hover 明细浮层（R188 区，`#mtmetsum` `mouseenter` 显 `#mtmetsumdetail`
逐轮明细列表 + 均值 / 合计，`mouseleave` 隐）同补 5 键段（`_fl26h` 5 键 `localStorage`，与 `mtMetSumDetailCopy` 同步拼「[全折叠域当前态]」段，`d.innerHTML=_lines.replace(\n,g,'<br>')` 含全折叠域段，hover 明细浮层自含全折叠域 5 键当前态，与
`mtMetSumDetailCopy` 复制出口同数据源同步）③ 与 R188 `#mtmetsumdetail` hover 明细 / R189 `#mtmetsumdetailcopy` 双指标逐轮明细复制**分工**（R188/R189 双图区明细 hover / 复制（近 N 次逐轮 + 均值 / 合计），R226 补全折叠域 5 键当前态段——双图区明细
自含全折叠域当前态，`#mtmetsumdetail` hover + `#mtmetsumdetailcopy` 复制双路同 5 键段）④ 与 R222 维护守护全记录 / R223 能力出口总览 / R224 三域折叠态总览 / R225 折叠全链路总控补全折叠域字段**语言同**（各双图区明细 / 全折叠域 / 三域 / 全链路读 5
键 `localStorage` 拼文本，全折叠域当前态同语言，各出口自含全折叠域出口标位）⑤ 验收**函数级**（设 5 键全 `'1'` + 设双指标历史 `localStorage._mtRunHist` / `_mtRunDelta` + 点 `#mtmetsumdetailcopy` 验 toast「已复制双指标逐轮明细（3 次）」（双图区明细
文本含全折叠域 5 键当前态段）+ `#mtmetsum` `mouseenter` 验 `#mtmetsumdetail` `innerHTML` 含 `全折叠域当前态` 段（hover 明细浮层自含 5 键段），不真跑 `mtRun` 免 tick 污染 `runs`；双图区明细 / hover 浮层拼逻辑验 5 键段进文本 / `innerHTML`，非真剪贴板
/ 渲染像素）。

---

## 第241轮（前端 R227 · goal round204）：维护守护区键盘流触发记录面板补全折叠域字段（`#mtkeyhintdetail` 键盘流触发记录 hover 浮层 + `#mtkeyhintcopy` 键盘流触发记录文本补全折叠域 5 键当前态字段，键盘流触发记录自含全折叠域当前态）

**完善性（键盘流触发记录自含全折叠域当前态）**：R226 双图区明细补全折叠域 5 键，但**`#mtkeyhintdetail` 键盘流触发记录 hover 浮层 / `#mtkeyhintcopy` 键盘流触发记录文本（R181/R195 区，
`Space` / `Esc` / `Enter` 三键触发记录 + 触发顺序）没全折叠域 5 键**（键盘流触发记录要自含全折叠域当前态，`#mtkeyhintdetail` hover 浮层（R181 区，三键状态灯 + 最近触发时间 + 触发顺序回放）补
`[全折叠域当前态]` 5 键段（`localStorage 5键: _mtMetFold=... · _mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...`），`mtKeyHintCopy`（R195 区）键盘流触发记录
文本同补 5 键段，键盘流触发记录自含全折叠域当前态，与 R222/R223/R224/R225/R226 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' + 设键盘流触发记录（window._mtKeyLog/_mtKeyLogOrder）→ #mtkeyhint mouseenter → #mtkeyhintdetail hover 浮层 innerHTML 含全折叠域当前态段；点 #mtkeyhintcopy →
toast「已复制键盘流触发记录」（键盘流触发记录文本含全折叠域 5 键当前态段）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r227_keyhint5key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 752→754`，断点 `_陈奕迅\时代曲.mp3`。

**坑**：① `#mtkeyhintdetail` hover 浮层（R181 区，`#mtkeyhint` `mouseenter` 显 `#mtkeyhintdetail` 三键状态灯（`Space` / `Esc` / `Enter` 可触 / 暂停 / 不可触色点）+ 最近触发时间（`window._mtKeyLog`
各键 `最近 <ts>` / 未用过）+ 触发顺序回放（`window._mtKeyLogOrder` 最近 10 次 `Esc→Space→Enter` 串），`mouseleave` 隐）补 `[全折叠域当前态]` 5 键段（`_html` 拼三键 + 触发顺序后加
`<span style="color:var(--dim)">[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... ·
_mtGuardAllDomain=...</span>`，5 键 `localStorage` 各 `||'0'` 降级，键盘流触发记录 hover 浮层自含全折叠域 5 键当前态，与 R222/R223/R224/R225/R226 补全折叠域字段同域）② `mtKeyHintCopy`
（R195 区，`#mtkeyhintcopy` 点复制「#music3 键盘流触发记录 · <ts>」+ 三键最近触发时间戳 + 触发顺序串到剪贴板，`navigator.clipboard.writeText` 降级 `_copyFallback`）同补 5 键段（`_lines+=` 触发顺序段后
加「[全折叠域当前态] localStorage 5键: _mtMetFold=... · _mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...」，键盘流触发记录文本自含全折叠域 5 键当前态，
与 `#mtkeyhintdetail` hover 浮层同数据源同步）③ 与 R181 `#mtkeyhintdetail` 键盘三键提示浮层 / R195 `#mtkeyhintcopy` 键盘流触发记录复制**分工**（R181/R195 键盘流触发记录 hover / 复制（三键触发记录 +
触发顺序），R227 补全折叠域 5 键当前态段——键盘流触发记录自含全折叠域当前态，`#mtkeyhintdetail` hover + `#mtkeyhintcopy` 复制双路同 5 键段）④ 与 R222 维护守护全记录 / R223 能力出口总览 / R224 三域折叠态
总览 / R225 折叠全链路总控 / R226 双图区明细补全折叠域字段**语言同**（各键盘流 / 全折叠域 / 三域 / 全链路 / 双图区读 5 键 `localStorage` 拼文本 / 色带，全折叠域当前态同语言，各出口自含全折叠域出口
标位）⑤ 验收**函数级**（设 5 键全 `'1'` + 设键盘流触发记录 `window._mtKeyLog` / `_mtKeyLogOrder` + `#mtkeyhint` `mouseenter` 验 `#mtkeyhintdetail` `innerHTML` 含 `全折叠域当前态` 段（hover 浮层自含
5 键段）+ 点 `#mtkeyhintcopy` 验 toast「已复制键盘流触发记录」（键盘流触发记录文本含全折叠域 5 键当前态段），不真跑 `mtRun` 免 tick 污染 `runs`；键盘流触发记录 hover / 复制拼逻辑验 5 键段进
`innerHTML` / 文本，非真剪贴板 / 渲染像素）。

---

## 第242轮（前端 R228 · goal round205）：维护守护区状态详情 hover 浮层补全折叠域字段（`#mtstatebardtl` 状态详情 hover 浮层 + `#mtstatebardtlcopy` 状态详情文本补全折叠域 5 键当前态字段，状态详情自含全折叠域当前态）

**完善性（状态详情自含全折叠域当前态）**：R227 键盘流触发记录补全折叠域 5 键，但**`#mtstatebardtl` 状态详情 hover 浮层 / `#mtstatebardtlcopy` 状态详情文本（R185/R191 区，
`跑中 / 已暂停 / 已取消 · 第 i/N 轮 · 本轮回 +X · 本轮耗 Ys`）没全折叠域 5 键**（状态详情要自含全折叠域当前态，`#mtstatebardtl` hover 浮层（R185 区，指示条 hover 显状态详情）补
`[全折叠域当前态]` 5 键段（`_txt` 拼状态详情后加 `localStorage 5键: _mtMetFold=... · _mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...`），
`mtStateBarCopy`（R191 区）状态详情文本同补 5 键段（`let _txt` 免 `const` 赋值错），状态详情自含全折叠域当前态，与 R222/R223/R224/R225/R226/R227 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' + 设维护状态（window._mtRunning=true + _mtLiveInfo）→ #mtstatebar mouseenter → #mtstatebardtl hover 浮层 textContent 含全折叠域当前态段；点
#mtstatebardtlcopy → toast「已复制维护状态详情」（状态详情文本含全折叠域 5 键当前态段）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图
r228_state5key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 754→756`，断点 `_陈粒\走马.mp3`。

**坑**：① `#mtstatebardtl` hover 浮层（R185 区，`#mtstatebar` `mouseenter` 显 `#mtstatebardtl` 状态详情（`维护状态：` 前缀 + 已取消 / 已暂停 / 跑中 / 维护完成 · 第 i/N 轮 · 本轮回 +X · 本轮耗
Ys），`mouseleave` 隐）补 `[全折叠域当前态]` 5 键段（`_txt`（`let`，IIFE 内局部）拼状态详情后加 `\n[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' ·
_mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...`，5 键 `localStorage` 各 `||'0'` 降级，`d.textContent=_txt`（多行文本，`white-space:nowrap` 浮层换行），
状态详情 hover 浮层自含全折叠域 5 键当前态，与 R222/R223/R224/R225/R226/R227 补全折叠域字段同域）② `mtStateBarCopy`（R191 区，`#mtstatebardtlcopy` 点复制「#music3 维护状态 · <ts>」+ 状态详情
文本（跑中 / 暂停 / 取消 + 第 i/N 轮 + 本轮回 +X + 本轮耗 Ys）到剪贴板，`navigator.clipboard.writeText` 降级 `_copyFallback`）同补 5 键段（`_txt` 拼状态详情后加「[全折叠域当前态] localStorage
5键: ...」，状态详情文本自含全折叠域 5 键当前态，与 `#mtstatebardtl` hover 浮层同数据源同步）③ `mtStateBarCopy` 原 `const _txt='#music3 维护状态...'`（R191 区 5067 行 `const` 声明），补全折叠域段
`_txt+=`（常量赋值报错 `Assignment to constant variable`，`console 1`）——修 `const _txt` → `let _txt`（免 `+=` 常量赋值报错，`console 0`），同 R212/R214/R215 IIFE 多 `)` 语法修正 + R228 `const` →
`let` 修正纪律（补 `+=` 段前查 `const` 声明改 `let`）④ 与 R185 `#mtstatebardtl` 状态详情 hover 浮层 / R191 `#mtstatebardtlcopy` 状态详情复制**分工**（R185/R191 状态详情 hover / 复制（跑中 / 暂停 /
取消 + 第 i/N 轮 + 本轮回 + 本轮耗），R228 补全折叠域 5 键当前态段——状态详情自含全折叠域当前态，`#mtstatebardtl` hover + `#mtstatebardtlcopy` 复制双路同 5 键段）⑤ 与 R222 维护守护全记录 /
R223 能力出口总览 / R224 三域折叠态总览 / R225 折叠全链路总控 / R226 双图区明细 / R227 键盘流触发记录补全折叠域字段**语言同**（各状态详情 / 全折叠域 / 三域 / 全链路 / 双图区 / 键盘流读 5 键
`localStorage` 拼文本 / 色带，全折叠域当前态同语言，各出口自含全折叠域出口标位）⑥ 验收**函数级**（设 5 键全 `'1'` + 设维护状态 `window._mtRunning=true` / `window._mtLiveInfo` + `#mtstatebar`
`mouseenter` 验 `#mtstatebardtl` `textContent` 含 `全折叠域当前态` 段（hover 浮层自含 5 键段）+ 点 `#mtstatebardtlcopy` 验 toast「已复制维护状态详情」（状态详情文本含全折叠域 5 键当前态段），不真跑
`mtRun` 免 tick 污染 `runs`；状态详情 hover / 复制拼逻辑验 5 键段进 `textContent` / 文本，非真剪贴板 / 渲染像素）。

---

## 第243轮（前端 R229 · goal round206）：维护守护区双图区 PNG 快照补全折叠域字段（`#mtmetpng` 双图区 PNG 快照 / `mtMetPng` canvas 画维护趋势耗时折线 + 补入柱状 补全折叠域 5 键当前态段（canvas 底栏 5 键色带），双图区 PNG 快照自含全折叠域当前态）

**完善性（双图区 PNG 快照自含全折叠域当前态）**：R226 双图区明细补全折叠域 5 键，但**`#mtmetpng` 双图区 PNG 快照（R158 区，canvas 画维护趋势耗时折线 + 补入柱状）没全折叠域 5 键**
（双图区 PNG 快照要自含全折叠域当前态，`mtMetPng`（R158 区）补全折叠域 5 键当前态段（canvas 底栏 5 键色带，`_H=210`→`230` 加高），双图区 PNG 快照自含全折叠域当前态，与
R222/R223/R224/R225/R226/R227/R228 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' + 设双指标历史 → 点 #mtmetpng 导出 PNG → toast「已导出双指标趋势快照（PNG）」（canvas PNG 含全折叠域 5 键当前态底栏色带）`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r229_metpng5key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 756→758`，断点 `_陶喆\心乱飞.mp3`。

**坑**：① `mtMetPng`（R158 区）双图区 PNG 快照（canvas 画维护趋势：耗时折线 `32-82` 区 / 补入柱状 `96-146` 区 / 汇总标签 `H-10`，`W=520, H=210`）补全折叠域 5 键当前态段（canvas 底栏 5 键色带：
`_fl5m` 5 键 `localStorage`（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`，`||'0'` 降级）+ `_kn5m` 5 键名缩写（`Met`/`Pan`/`All`/`Ctl`/`Dom`）+ 循环拼 5 色带
`fillRect`（`'0'` 展开 `rgb(47,125,85)` 绿 / 非 `'0'` 折叠 `rgb(163,38,26)` 红，`fillText` 键名缩写 + 值白字）+ `全折叠域5键当前态` 标签（`H-40`）+ 色带（`H-34` 区），`H=210`→`230` 加高容全折叠域 5 键底栏
+ 汇总标签 `H-10`→`H-8` 下移避全折叠域段，双图区 PNG 快照自含全折叠域 5 键当前态，与 R222/R223/R224/R225/R226/R227/R228 补全折叠域字段同域，`#mtmetpng` PNG 快照补全折叠域段）② 与 R158 `#mtmetpng`
双图区 PNG 快照**分工**（R158 双图区 PNG 快照（维护趋势耗时折线 + 补入柱状 + 汇总标签），R229 补全折叠域 5 键当前态段（canvas 底栏 5 键色带）——双图区 PNG 快照自含全折叠域当前态，`#mtmetpng`
PNG 快照补全折叠域段）③ 与 R158 双图区 PNG 快照 / R222 维护守护全记录 / R223 能力出口总览 / R224 三域折叠态总览 / R225 折叠全链路总控 / R226 双图区明细 / R227 键盘流触发记录 / R228 状态详情
补全折叠域字段**语言同**（各双图区 PNG 快照 / 全折叠域 / 三域 / 全链路 / 双图区明细 / 键盘流 / 状态详情读 5 键 `localStorage` 拼色带 / 文本，全折叠域当前态同语言，各出口自含全折叠域出口标位）
④ 验收**函数级**（设 5 键全 `'1'` + 设双指标历史 `localStorage._mtRunHist` / `_mtRunDelta` + 点 `#mtmetpng` 导出 PNG 验 toast「已导出双指标趋势快照（PNG）」（canvas PNG 含全折叠域 5 键当前态
底栏色带），不真跑 `mtRun` 免 tick 污染 `runs`；canvas PNG 拼逻辑验全折叠域 5 键色带进 PNG（`_fl5m` 5 键 + `_kn5m` 5 键名缩写 + 循环拼 5 色带 `fillRect`），非真 PNG 像素（headless 不下载 PNG 文件，
验 toast 出口 + canvas 全折叠域 5 键色带拼逻辑，真 PNG 内容不验）。

---

## 第244轮（前端 R230 · goal round207）：维护守护区全库完成详情 / 跑中详情补全折叠域字段（`#mtlivebadgedonecopy` 全库完成详情文本 + `#mtlivedetail` 跑中详情 hover 浮层 / `data-dtl` 补全折叠域 5 键当前态字段，全库完成详情 / 跑中详情自含全折叠域当前态）

**完善性（全库完成详情 / 跑中详情自含全折叠域当前态）**：R229 双图区 PNG 快照补全折叠域 5 键，但**`#mtlivebadgedonecopy` 全库完成详情文本（R192 区，
`#music3 全库维护完成 · <ts>` + `共 N 轮 · 耗时 Xs`）/ `#mtlivedetail` 跑中详情 hover 浮层（R167 区，`#mtlivebadge` 悬停显 `data-dtl`（本轮回 + 歌词 / 封面 + 本轮耗 + 累计 + 跑到））没全折叠域
5 键**（全库完成详情 / 跑中详情要自含全折叠域当前态，`mtLiveBadgeDoneCopy`（R192 区）全库完成详情文本补 `[全折叠域当前态]` 5 键段（`let _txt` 免 `const` 赋值错）+ 跑中详情 `data-dtl`
（R166 区 `mtLiveBadgeDraw`，`#mtlivedetail` hover 浮层数据源）补全折叠域 5 键当前态段，全库完成详情 / 跑中详情自含全折叠域当前态，与 R222-R229 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' + 设全库完成详情（window._mtLiveDoneInfo={N:100, totalDur:120}）→ 设 #mtlivebadge 完成态显复制钮 → 点 #mtlivebadgedonecopy → toast「已复制全库维护完成详情（共 100 轮 ·
耗时 120s）」（全库完成详情文本含全折叠域 5 键当前态段）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r230_livedone5key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 758→760`，断点 `_QQ音乐\周杰伦 - 晴天.mp3`。

**坑**：① `mtLiveBadgeDoneCopy`（R192 区）全库完成详情文本（`#music3 全库维护完成 · <ts>` + `共 N 轮 · 耗时 Xs`，`navigator.clipboard.writeText` 降级 `_copyFallback`）补 `[全折叠域当前态]` 5
键段（`_txt`（原 `const` 改 `let` 免 `+=` 常量赋值报错）拼全库完成详情后加 `\n[全折叠域当前态] localStorage 5键: _mtMetFold='+(localStorage.getItem('_mtMetFold')||'0')+' · _mtGuardPanelFold=... ·
_mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...`，5 键 `localStorage` 各 `||'0'` 降级，全库完成详情文本自含全折叠域 5 键当前态，与 R222-R229 补全折叠域字段同域，
`#mtlivebadgedonecopy` 全库完成详情复制补全折叠域段）② 跑中详情 `data-dtl`（R166 区 `mtLiveBadgeDraw`，`#mtlivebadge` 属性 `data-dtl`（`#mtlivedetail` hover 浮层数据源，R167 区 `#mtlivebadge`
悬停读 `data-dtl` 显 `#mtlivedetail`））补全折叠域 5 键当前态段（`_dtl`（`let`）拼跑中详情（本轮回 + 歌词 / 封面 + 本轮耗 + 累计 + 跑到 + 自动刷 5s）后加 ` · [全折叠域当前态] _mtMetFold=... ·
_mtGuardPanelFold=... · _mtGuardFoldAll=... · _mtGuardFoldCtl=... · _mtGuardAllDomain=...`，`el.setAttribute('data-dtl',_dtl)`，`#mtlivedetail` hover 浮层自含全折叠域 5 键当前态，与 R222-R229
补全折叠域字段同域，跑中详情 hover 浮层（R167）补全折叠域段）③ `mtLiveBadgeDoneCopy` 原 `const _txt='#music3 全库维护完成...'`（R192 区 3911 行 `const` 声明），补全折叠域段 `_txt+=`（常量
赋值报错 `Assignment to constant variable`）——修 `const _txt` → `let _txt`（免 `+=` 常量赋值报错，`console 0`），同 R228 `mtStateBarCopy` `const` → `let` 修正纪律（补 `+=` 段前查 `const` 声明改
`let`）④ 与 R192 `#mtlivebadgedonecopy` 全库完成详情复制 / R167 `#mtlivedetail` 跑中详情 hover 浮层**分工**（R192/R167 全库完成详情复制 / 跑中详情 hover（全库完成 `共 N 轮 · 耗时 Xs` / 跑中本轮回 +
歌词 / 封面 + 本轮耗 + 累计 + 跑到），R230 补全折叠域 5 键当前态段——全库完成详情 / 跑中详情自含全折叠域当前态，`#mtlivebadgedonecopy` 全库完成详情复制 + `#mtlivedetail` 跑中详情 hover 双路同 5 键段）
⑤ 与 R222 维护守护全记录 / R223 能力出口总览 / R224 三域折叠态总览 / R225 折叠全链路总控 / R226 双图区明细 / R227 键盘流触发记录 / R228 状态详情 / R229 双图区 PNG 快照补全折叠域字段**语言同**（各全库
完成详情 / 跑中详情 / 全折叠域 / 三域 / 全链路 / 双图区 / 键盘流 / 状态详情 / 双图区 PNG 读 5 键 `localStorage` 拼文本 / 色带，全折叠域当前态同语言，各出口自含全折叠域出口标位）⑥ 验收**函数级**（设
5 键全 `'1'` + 设全库完成详情 `window._mtLiveDoneInfo` + 设 `#mtlivebadge` 完成态显复制钮 + 点 `#mtlivebadgedonecopy` 验 toast「已复制全库维护完成详情（共 100 轮 · 耗时 120s）」（全库完成详情文本含全
折叠域 5 键当前态段），不真跑 `mtRun` 免 tick 污染 `runs`；全库完成详情复制拼逻辑验 5 键段进文本（`let _txt` + `_txt+=` 全折叠域段），跑中详情 hover 浮层验 `data-dtl` 属性含全折叠域 5 键段（`_dtl+=`
全折叠域段 + `el.setAttribute('data-dtl',_dtl)`），非真剪贴板 / 渲染像素。

---

## 第245轮（前端 R231 · goal round208）：维护守护区跑中详情复制出口自含全折叠域字段（`#mtlivedetailcopy` 跑中详情复制（R169 区，`mtLiveDetailCopy` 复制 `#mtlivebadge` 的 `data-dtl`）验 `data-dtl` R230 已含全折叠域 5 键段，`mtLiveDetailCopy` 复制 `data-dtl` 自动含全折叠域 5 键段，跑中详情复制自含全折叠域当前态）

**完善性（跑中详情复制自含全折叠域当前态）**：R230 全库完成详情 / 跑中详情 `data-dtl` 补全折叠域 5 键，但**`#mtlivedetailcopy` 跑中详情复制（R169 区 `mtLiveDetailCopy`）验 `data-dtl` 含全折叠域 5 键段**
（`data-dtl` R230 已含全折叠域 5 键段，`mtLiveDetailCopy` 复制 `data-dtl` 自动含全折叠域 5 键段（R230 `data-dtl` 补全折叠域段后），跑中详情复制自含全折叠域当前态，与 R222-R230 补全折叠域字段同域）。
`mtLiveDetailCopy`（R169 区）复制 `#mtlivebadge` 的 `data-dtl`（`b.getAttribute('data-dtl')`，`data-dtl` R230 已含全折叠域 5 键段），`#music3 维护跑中详情 · <ts>` + `data-dtl` 复制，
`mtLiveDetailCopy` 复制 `data-dtl` 自动含全折叠域 5 键段（免重改函数体——`data-dtl` R230 补全折叠域段后 `mtLiveDetailCopy` 复制自动含，同 R229 `#mtmetpng` PNG 读 canvas 自动含全折叠域 5 键段 / R230
全库完成详情复制 `data-dtl` 自动含全折叠域段纪律），跑中详情复制自含全折叠域当前态，与 R222-R230 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' + 设 #mtlivebadge 跑中态 data-dtl（含全折叠域 5 键段，R230）→ 点 #mtlivedetailcopy → toast「已复制当前轮双指标详情」（复制含全折叠域 5 键当前态段，data-dtl R230 已含全折叠域段）`
（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r231_livedetail5key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 760→762`，断点 `_亚细亚旷世奇才\医生.mp3`。

**坑**：① `mtLiveDetailCopy`（R169 区）跑中详情复制（`#mtlivedetailcopy` 点复制 `#music3 维护跑中详情 · <ts>` + `data-dtl`（`b.getAttribute('data-dtl')`，`#mtlivebadge` 属性 `data-dtl`（`#mtlivedetail`
hover 浮层数据源，R166 区 `mtLiveBadgeDraw` 写）））复制 `data-dtl` 自动含全折叠域 5 键段（`data-dtl` R230 已含全折叠域 5 键段（`_dtl+=` 全折叠域段 + `el.setAttribute('data-dtl',_dtl)`），
`mtLiveDetailCopy` 复制 `data-dtl` 自动含全折叠域 5 键段，免重改函数体——`data-dtl` R230 补全折叠域段后 `mtLiveDetailCopy` 复制自动含，同 R229 `#mtmetpng` PNG 读 canvas 自动含全折叠域 5 键段 / R230
全库完成详情复制 `data-dtl` 自动含全折叠域段纪律，`#mtlivedetailcopy` 跑中详情复制自含全折叠域 5 键段）② 与 R169 `#mtlivedetailcopy` 跑中详情复制**分工**（R169 跑中详情复制（`#music3 维护跑中详情 ·
<ts>` + `data-dtl`），R231 验 `data-dtl` R230 已含全折叠域 5 键段 + `mtLiveDetailCopy` 复制 `data-dtl` 自动含全折叠域 5 键段——跑中详情复制自含全折叠域当前态，`#mtlivedetailcopy` 复制出口自动含全折叠
域段，免重改 `mtLiveDetailCopy` 函数体）③ 与 R222 维护守护全记录 / R223 能力出口总览 / R224 三域折叠态总览 / R225 折叠全链路总控 / R226 双图区明细 / R227 键盘流触发记录 / R228 状态详情 / R229 双图区
PNG 快照 / R230 全库完成详情补全折叠域字段**语言同**（各跑中详情复制 / 全折叠域 / 三域 / 全链路 / 双图区 / 键盘流 / 状态详情 / 双图区 PNG / 全库完成详情读 5 键 `localStorage` 拼文本 / 色带，全折叠域
当前态同语言，各出口自含全折叠域出口标位；`#mtlivedetailcopy` 复制 `data-dtl` 自动含全折叠域段同 R229/R230 复制 `data-dtl` / 读 canvas 自动含全折叠域段纪律）④ 验收**函数级**（设 5 键全 `'1'` + 设
`#mtlivebadge` 跑中态 `data-dtl`（`badge.setAttribute('data-dtl', '本轮回 +5(歌词 +3 / 封面 +2)· 本轮耗 1.2s · 累计 12s · 跑到 5/100 · [全折叠域当前态] _mtMetFold=1 · ...')`（含全折叠域 5 键段，R230
补 `data-dtl` 全折叠域段）+ 点 `#mtlivedetailcopy` 验 toast「已复制当前轮双指标详情」（复制含全折叠域 5 键当前态段）+ 验 `data-dtl` 含全折叠域 5 键段（`hasFold=true`），不真跑 `mtRun` 免 tick 污染
`runs`；跑中详情复制拼逻辑验 `data-dtl` 含全折叠域 5 键段 + `mtLiveDetailCopy` 复制 `data-dtl` 自动含（`b.getAttribute('data-dtl')` 复制），非真剪贴板 / 渲染像素）。

---

## 第246轮（前端 R232 · goal round209）：维护守护区全折叠域 5 域折叠态一键复制出口（`#mtallfoldcopy` 全折叠域 5 域折叠态一键复制（R232），拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态到剪贴板，全折叠域 5 域折叠态一键留存 / 贴工单）

**完善性（全折叠域 5 域折叠态一键留存 / 贴工单免逐点各面板 / 出口）**：R222-R231 各面板 / 出口补全折叠域 5 键段分散，但**无全折叠域 5 域折叠态一键复制出口**（全折叠域 5 域折叠态要一键留存 / 贴工单，
`#mtallfoldcopy` 全折叠域 5 域折叠态一键复制出口（R232）拼全折叠域 5 域（双图区 / 总览面板 / 全浮层 / 折叠全链路 / 全折叠域总控面板）+ 5 键 `localStorage` + 5 标志 `window` + 5 折叠钮文案 +
7 浮层 `display` 当前态到剪贴板（`#music3 全折叠域5域折叠态一键复制 · <ts>` + 全折叠域 5 域各折叠 / 展开 + `localStorage` 值 + 5 键 `localStorage` + 5 标志 `window` + 5 折叠钮文案 + 7 浮层 `display`），
全折叠域 5 域折叠态一键留存 / 贴工单，免逐点各面板 / 出口，与 R222-R231 补全折叠域字段同域。

**E2E**：`设 5 键全 '1' + 5 标志全 true → 点 #mtallfoldcopy → toast「已复制全折叠域 5 域折叠态」（复制含全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态）`（绿）；端点 **30/0**、
JS undefined NONE、CSS 320/320、node 0、console 0、截图 r232_allfold5copy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 762→764`，断点 `_周杰伦\伊斯坦堡.mp3`。

**坑**：① `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制小钮（R232，维护守护区小钮区 `#mtguardfoldresetcopy` 后）+ `mtAllFoldCopy` 函数（拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态到剪贴板，
`#music3 全折叠域5域折叠态一键复制 · <ts>` + 全折叠域 5 域（双图区 / 总览面板 / 全浮层 / 折叠全链路 / 全折叠域总控面板）各折叠 / 展开 + `localStorage` 值 + 5 键 `localStorage`（`_mtMetFold`/
`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`，`||'0'` 降级）+ 5 标志 `window`（各布尔值）+ 5 折叠钮文案（`#mtmetfold`/`#mtguardpanelfold`/`#mtguardfoldall`/
`#mtguardfoldctl`/`#mtguardalldomain` 各 `textContent`）+ 7 浮层 `display`（`#mtguardpaneld`/`#mtguardfoldctld`/`#mtguardfoldstatd`/`#mtstatebardtl`/`#mtmetsumdetail`/`#mtkeyhintdetail`/
`#mtguardalldomains` 各 `style.display`），`navigator.clipboard.writeText` 降级 `_copyFallback` + toast「已复制全折叠域5域折叠态」，全折叠域 5 域折叠态一键留存 / 贴工单，与 R222-R231 补全折叠域字段
同域，`#mtallfoldcopy` 复制出口拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态）② 全折叠域 5 域（`_doms` 数组 5 元素：`['双图区','#mtmetfold','_mtMetFold']` / `['总览面板','#mtguardpanelfold',
'_mtGuardPanelFold']` / `['全浮层','#mtguardfoldall','_mtGuardFoldAll']` / `['折叠全链路','#mtguardfoldctl','_mtGuardFoldCtl']` / `['全折叠域总控','#mtguardalldomain','_mtGuardAllDomain']`，各域
`getElementById` 折叠钮 + `localStorage.getItem` 折叠态（`==='1'` 折叠 / `'0'` 展开）+ `textContent` 文案），`_lines+=` 拼全折叠域 5 域各折叠 / 展开 + `localStorage` 值（全折叠域 5 域折叠态一键
复制自含全折叠域 5 域各态）③ 与 R224 `#mtguardfoldstat` 全折叠域 5 域折叠态总览 / R225 `#mtguardfoldctl` 折叠全链路总控 / R222-R231 各面板 / 出口补全折叠域 5 键段**分工**（R224/R225/R222-R231
全折叠域 5 域折叠态总览 / 各面板 / 出口补全折叠域 5 键段分散，R232 `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制出口拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态到剪贴板——全折叠域 5 域
折叠态一键留存 / 贴工单，免逐点各面板 / 出口，`#mtallfoldcopy` 复制出口自含全折叠域 5 域全当前态）④ 与 R196/R201/R208/R214/R217 复制出口**语言同**（各复制出口读各数据源拼文本到剪贴板，
`navigator.clipboard.writeText` 降级 `_copyFallback`，全折叠域 5 域折叠态一键复制读全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层拼文本，各出口自含全折叠域出口标位）⑤ `#mtallfoldcopy` 维护
tab 懒加载坑 → `document` click 委托（`document.addEventListener('click', function(e){ if(e.target.id==='mtallfoldcopy'){ e.stopPropagation(); mtAllFoldCopy(); } });`），免维护 tab 未激活小钮
DOM 未渲染 `c=null` 不绑（同 R212/R214/R215/R216/R217 `document` click 委托纪律）⑥ 验收**函数级**（设 5 键全 `'1'` + 5 标志全 `true` + 点 `#mtallfoldcopy` 验 toast「已复制全折叠域5域折叠态」
（复制含全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态），不真跑 `mtRun` 免 tick 污染 `runs`；`#mtallfoldcopy` 复制拼逻辑验全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层字段进文本（`_lines+=`
全折叠域 5 域各折叠 / 展开 + `localStorage` 值 + 5 键 + 5 标志 + 5 折叠钮 + 7 浮层），非真剪贴板 / 渲染像素）。

---

## 第247轮（前端 R233 · goal round210）：维护守护区全折叠域 5 域折叠态 PNG 快照（`#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照（R233），拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG 转 PNG 下载「music3_全折叠域5域折叠态_<ts>.png」，全折叠域 5 域折叠态 PNG 存档 / 可分享）

**完善性（全折叠域 5 域折叠态 PNG 存档 / 可分享）**：R232 `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制出口，但**全折叠域 5 域折叠态 PNG 快照没加**（全折叠域 5 域折叠态要 PNG 存档 / 可分享，
`#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照（R233）拼全折叠域 5 域（双图区 / 总览面板 / 全浮层 / 折叠全链路 / 全折叠域总控面板）+ 5 键 `localStorage` + 5 标志 `window` + 5 折叠钮文案 + 7 浮层
`display` 当前态内联 SVG（分块色带：全折叠域 5 域色带 + 5 标志色带 + 5 折叠钮文案 + 7 浮层色带），canvas 转 PNG 下载「music3_全折叠域5域折叠态_<ts>.png」，全折叠域 5 域折叠态 PNG 存档 /
可分享，与 R232 全折叠域 5 域折叠态一键复制同域，`#mtallfoldpng` PNG 快照读全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层拼内联 SVG 色带转 PNG，免逐点各面板 / 出口）。

**E2E**：`设 5 键全 '1' + 5 标志全 true → 点 #mtallfoldpng → PNG 快照下载（全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG 转 PNG，headless 下载无 toast 属正常）`（绿）；
端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r233_allfold5png.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 764→766`，断点 `_周杰伦\我是如此相信.mp3`。

**坑**：① `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照小钮（R233，维护守护区小钮区 `#mtallfoldcopy` 后）+ `mtAllFoldPng` 函数（拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG
→ canvas 转 PNG 下载「music3_全折叠域5域折叠态_<ts>.png」，`var` 声明免 `const` 崩溃，`_rows` 数组拼 SVG：标题 + `[全折叠域5域]` 5 域色带（`_doms` 数组 5 元素，各域 `localStorage` 折叠态
（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠 `--bad` 红）+ 域名 + 键名 + 值 + `[5标志 window]` 5 标志色带（`_w5` 各 `window` 标志，`false` 展开 `--ok` 绿 / `true` 折叠 `--bad` 红）+ 标志名 + 值 +
`[5折叠钮文案]` 5 折叠钮 `textContent` + `[7浮层 display]` 7 浮层 `style.display` 色带（`none` 隐 `--ok` 绿 / 显 `--dim` 灰）+ `canvas` `toBlob` 转 PNG 下载（`toBlob` 不可用降级 toast「PNG 导出
不可用（toBlob 不支持）」+ `canvas` 不可用降级 toast「PNG 导出失败（canvas 不可用）」+ SVG 渲染失败降级 toast「PNG 导出失败（SVG 渲染不可用）」），全折叠域 5 域折叠态 PNG 存档 / 可分享，
与 R232 全折叠域 5 域折叠态一键复制同域，`#mtallfoldpng` PNG 快照读全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层拼内联 SVG 色带转 PNG，免逐点各面板 / 出口）② `mtAllFoldPng` `var` 声明免
`const` 崩溃（`_OK`/`_BAD`/`_DIM`/`_LN`/`_ACC` 颜色常量 + `_W`/`_y`/`_rows` 画布变量 + `_doms`/`_w5`/`_wk`/`_btns5`/`_floors7` 数据数组 + `_host`/`_imgv`/`_b64`/`_cv`/`_g`/`_u`/`_a`/`_blob` 各变量全
`var`，免 `const`/`let` 在 `try/catch` 内声明作用域问题 + `for` 循环 `var _i` 免循环变量提升崩溃），同 R221 `mtGuardAllDomain` `var` 声明免 `const` 崩溃纪律③ `#mtallfoldpng` 维护 tab 懒
加载坑 → `document` click 委托（`document.addEventListener('click', function(e){ if(e.target.id==='mtallfoldpng'){ e.stopPropagation(); mtAllFoldPng(); } });`），免维护 tab 未激活小钮 DOM 未
渲染 `c=null` 不绑（同 R212/R214/R215/R216/R217/R232 `document` click 委托纪律）④ 与 R232 `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制**分工**（R232 全折叠域 5 域折叠态一键复制到剪贴板（文本
留存 / 贴工单），R233 全折叠域 5 域折叠态 PNG 快照到 PNG（图像存档 / 可分享），`#mtallfoldcopy` 文本 + `#mtallfoldpng` PNG 双出口自含全折叠域 5 域全当前态，与 R158/R198/R200/R208/R215/R217 PNG
导出 + R196/R201/R208/R214/R217/R232 复制出口双路语言同）⑤ 与 R224 `#mtguardfoldstat` 全折叠域 5 域折叠态总览 / R225 `#mtguardfoldctl` 折叠全链路总控 / R222-R231 各面板 / 出口补全折叠域
5 键段**语言同**（各全折叠域 5 域折叠态总览 / PNG 快照 / 各面板 / 出口读 5 键 `localStorage` + 各域 `textContent` / `display` 拼色带 / 文本 / SVG，全折叠域 5 域当前态同语言，各出口自含全折叠
域出口标位）⑥ 验收**函数级**（设 5 键全 `'1'` + 5 标志全 `true` + 点 `#mtallfoldpng` 验 PNG 快照下载（全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG 转 PNG），不真跑 `mtRun`
免 tick 污染 `runs`；`#mtallfoldpng` PNG 拼逻辑验全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层字段进内联 SVG（`_rows.push` 全折叠域 5 域色带 + 5 标志色带 + 5 折叠钮文案 + 7 浮层色带），
headless 下载 PNG 无 toast 属正常（`canvas` `toBlob` 转 PNG 下载不显 toast，降级才 toast「PNG 导出不可用」/「PNG 导出失败」，验 `console 0` + 下载成功，真 PNG 内容不验）。

---

## 第248轮（前端 R234 · goal round211）：维护守护区全折叠域 5 域折叠态总控浮层（`#mtallfoldstat` 全折叠域 5 域折叠态总控浮层（R234），拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG 浮层（8s 自动隐 + 折叠记忆 `localStorage._mtGuardAllFoldStat`），全折叠域 5 域折叠态总控浮层一眼全貌 + 跨会话折叠记忆）

**完善性（全折叠域 5 域折叠态总控浮层一眼全貌 + 跨会话折叠记忆）**：R232/R233 全折叠域 5 域折叠态一键复制 / PNG 快照（`#mtallfoldcopy` / `#mtallfoldpng`），但**全折叠域 5 域折叠态总控浮层没加**
（全折叠域 5 域折叠态要一眼全貌浮层 + 跨会话折叠记忆，`#mtallfoldstat` 全折叠域 5 域折叠态总控浮层（R234）拼全折叠域 5 域（双图区 / 总览面板 / 全浮层 / 折叠全链路 / 全折叠域总控面板）+ 5 键
`localStorage` + 5 标志 `window` + 5 折叠钮文案 + 7 浮层 `display` 当前态内联 SVG（分块色带：`[全折叠域5域]` 5 域色带 + `[5标志 window]` 5 标志色带 + `[5折叠钮文案]` + `[7浮层 display]` 7 浮层色带），
显 `#mtallfoldstatd` 浮层（`getBoundingClientRect` 下沿定位 + `z-index:70` + 8s 自动隐 + `window._mtGuardAllFoldStat` 折叠记忆 `localStorage._mtGuardAllFoldStat`（折叠态常驻省高 / 展开态 8s 自动隐），
全折叠域 5 域折叠态总控浮层一眼全貌 + 跨会话折叠记忆，与 R232/R233 全折叠域 5 域折叠态一键复制 / PNG 快照同域，`#mtallfoldstat` 浮层读全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层拼内联 SVG 色带显浮层）。

**E2E**：`设 5 键全 '1' + 5 标志全 true → 直接调 mtAllFoldStat() 拼面板 → #mtallfoldstatd SVG 含全折叠域 5 域 / 5 标志 / 5 折叠钮 / 7 浮层分块；点 #mtallfoldstat → localStorage.
_mtGuardAllFoldStat='1' + 文案「▸ 展开全折叠域浮层」（折叠记忆切态）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r234_allfoldstat.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 766→768`，断点 `_周杰伦\跨时代.mp3`。

**坑**：① `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层小钮（R234，维护守护区小钮区 `#mtallfoldpng` 后）+ `#mtallfoldstatd` 浮层 div（`display:none` + `position:absolute` + `z-index:70` + 内联 SVG）+
`mtAllFoldStat` 函数（拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG：`_rows` 数组拼标题 + `[全折叠域5域]` 5 域色带（`_doms` 数组 5 元素，各域 `localStorage` 折叠态（`'0'` 展开
`--ok` 绿 / 非 `'0'` 折叠 `--bad` 红）+ 域名 + 键名 + 值 + `[5标志 window]` 5 标志色带（`_w5` 各 `window` 标志，`false` 展开 `--ok` 绿 / `true` 折叠 `--bad` 红）+ 标志名 + 值 + `[5折叠钮文案]` 5 折叠
钮 `textContent` + `[7浮层 display]` 7 浮层 `style.display` 色带（`none` 隐 `--ok` 绿 / 显 `--dim` 灰），`#mtallfoldstatd` `innerHTML` 拼 SVG + `getBoundingClientRect` 下沿定位（`#mtallfoldstat`
`left`/`bottom+2`）+ `z-index:70` + 8s 自动隐（`clearTimeout(window._mtGuardAllFoldStatT)` + `setTimeout` 8s `display:none`），全折叠域 5 域折叠态总控浮层一眼全貌，与 R232/R233 全折叠域 5 域折叠态
一键复制 / PNG 快照同域）② `mtAllFoldStat` 折叠记忆（R234）`window._mtGuardAllFoldStat` 惰性初始化读 `localStorage._mtGuardAllFoldStat`（`'1'` 折叠态 / `'0'` / 无默认展开态，`try/catch` `localStorage`
不可用（隐私模式 / 沙箱）降级 `false` 展开态），`#mtallfoldstat` 点切折叠记忆（折叠态 `window._mtGuardAllFoldStat=true`（`#mtallfoldstatd` 隐常驻省高 + 文案「▸ 展开全折叠域浮层」+ `clearTimeout` 清 8s
定时）/ 展开态 `window._mtGuardAllFoldStat=false`（`mtAllFoldStat()` 拼面板显 + 文案「▣ 全折叠域浮层」+ 8s 自动隐），切后 `localStorage.setItem('_mtGuardAllFoldStat', window._mtGuardAllFoldStat?'1':'0')`
存，`localStorage` 键族加 `_mtGuardAllFoldStat`（同 `_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain` 维护守护区折叠记忆），`mtAllFoldStat` 8s 自动隐跟折叠记忆
态（`if(!window._mtGuardAllFoldStat)` 才 8s 自动隐，折叠态全折叠域 5 域折叠态总控浮层常驻省高不消失，展开态才 8s 自动隐，同 R218 `#mtguardalldomain` 全折叠域总控面板 8s 自动隐跟折叠态纪律）③
初始折叠态同步（`#mtallfoldstat` 折叠记忆切 IIFE 后另 IIFE：惰性初始化读 `localStorage._mtGuardAllFoldStat` + `#mtallfoldstat` 文案 + `#mtallfoldstatd` `display` 随初始折叠态，刷新后恢复初始折叠态，
折叠态刷新隐全折叠域 5 域折叠态总控浮层省高，展开态刷新不隐）④ 与 R232 `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制 / R233 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照**分工**（R232 全折叠域 5 域
折叠态一键复制到剪贴板（文本留存 / 贴工单），R233 全折叠域 5 域折叠态 PNG 快照到 PNG（图像存档 / 可分享），R234 全折叠域 5 域折叠态总控浮层（`#mtallfoldstatd` 浮层 + 8s 自动隐 + 折叠记忆）——全折叠
域 5 域折叠态总控浮层一眼全貌 + 跨会话折叠记忆，`#mtallfoldcopy` 文本 + `#mtallfoldpng` PNG + `#mtallfoldstat` 浮层三出口自含全折叠域 5 域全当前态）⑤ 与 R224 `#mtguardfoldstat` 全折叠域 5 域折叠态
总览 / R225 `#mtguardfoldctl` 折叠全链路总控 / R222-R231 各面板 / 出口补全折叠域 5 键段**语言同**（各全折叠域 5 域折叠态总览 / 总控浮层 / PNG 快照 / 各面板 / 出口读 5 键 `localStorage` + 各域
`textContent` / `display` 拼色带 / 文本 / SVG，全折叠域 5 域当前态同语言，各出口自含全折叠域出口标位）⑥ `#mtallfoldstat` 维护 tab 懒加载坑 → `document` click 委托（折叠记忆切 IIFE：
`document.addEventListener('click', function(e){ if(e.target.id==='mtallfoldstat'){ e.stopPropagation(); 折叠记忆切逻辑 }; });`），免维护 tab 未激活小钮 DOM 未渲染 `c=null` 不绑（同 R212/R214/R215/
R216/R217/R232/R233 `document` click 委托纪律）⑦ 验收**函数级**（设 5 键全 `'1'` + 5 标志全 `true` + 直接调 `mtAllFoldStat()` 拼内联 SVG（绕 R234 折叠记忆切态——设 `_mtGuardAllFoldStat` 无后点
`#mtallfoldstat` 走 R234 折叠记忆切（当前展开态 → 切折叠才隐面板），验收直接调 `mtAllFoldStat()` 免切态干扰）+ 验 `#mtallfoldstatd` `innerHTML` 含 `<svg` + 全折叠域 5 域 / 5 标志 / 5 折叠钮 / 7 浮层
分块 + 点 `#mtallfoldstat` 验 `localStorage._mtGuardAllFoldStat='1'`（折叠记忆切态）+ 文案「▸ 展开全折叠域浮层」，不真跑 `mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验全折叠域 5 域 / 5 标志 / 5 折叠钮 / 7
浮层字段进 SVG，非真渲染像素）。

---

## 第249轮（前端 R235 · goal round212）：维护守护区全折叠记忆一键重置补全折叠域 6 键（`#mtguardfoldreset` 全折叠记忆重置后清第 6 键 `localStorage._mtGuardAllFoldStat` 全折叠域 5 域折叠态总控浮层折叠记忆，全折叠记忆一键复位后全折叠域 6 键全复位）

**完善性（全折叠记忆一键复位后全折叠域 6 键全复位）**：R219 `#mtguardfoldreset` 全折叠记忆重置清 5 键（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`）
+ R219 补全折叠域总控面板折叠记忆复位（`_mtGuardAllDomain`），但 R234 加第 6 键 `localStorage._mtGuardAllFoldStat`（全折叠域 5 域折叠态总控浮层折叠记忆）没进 `#mtguardfoldreset` 全折叠记忆重置
（全折叠记忆一键复位后全折叠域 6 键全复位，`mtGuardFoldReset`（R212 区）清 5 键 + 全折叠域总控面板折叠记忆复位（R219）补第 6 键 `localStorage._mtGuardAllFoldStat` 清 `'0'` +
`window._mtGuardAllFoldStat` 复位 `false` + `#mtallfoldstat` 文案复位「▣ 全折叠域浮层」+ `#mtallfoldstatd` `display` 复位 + `clearTimeout(window._mtGuardAllFoldStatT)`，全折叠记忆一键复位后
全折叠域 6 键全复位，与 R219/R220 全折叠记忆重置 / 重置详情同域）。

**E2E**：`设 6 键全 '1' → 点 #mtguardfoldreset → 6 键全复位 '0' + #mtallfoldstat 文案复位「▣ 全折叠域浮层」+ toast「已重置维护守护区全折叠记忆」`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r235_reset6key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 768→770`，断点 `_洛天依\刀马红颜.mp3`。

**坑**：① `#mtguardfoldreset` 全折叠记忆一键重置（R212 区，`mtGuardFoldReset` 清 5 键 `_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl` + 5 标志 `window` 复位 + 5 折叠钮文案复位
+ 全浮层 `display` 复位 + R219 补全折叠域总控面板 `_mtGuardAllDomain` 复位（`localStorage._mtGuardAllDomain` 清 `'0'` + `window._mtGuardAllDomain` 复位 `false` + `#mtguardalldomain` 文案复位「▣ 全
折叠域」+ `#mtguardalldomains` `display` 复位 + `clearTimeout(window._mtGuardAllDomainT)`））补第 6 键全折叠域 5 域折叠态总控浮层折叠记忆复位（R235，R219 全折叠域总控面板折叠记忆复位后插：
`try{ localStorage.setItem('_mtGuardAllFoldStat','0'); }catch(_){}` + `window._mtGuardAllFoldStat=false` + `#mtallfoldstat` 文案复位「▣ 全折叠域浮层」+ `#mtallfoldstatd` `display` 复位 +
`clearTimeout(window._mtGuardAllFoldStatT)`，全折叠记忆一键复位后全折叠域 6 键全复位（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`/
`_mtGuardAllFoldStat` 全清 `'0'` + 6 标志 `window` 全复位 `false`），与 R219/R220 全折叠记忆重置 / 重置详情同域，`#mtguardfoldreset` 全折叠记忆重置补第 6 键）② 与 R219 `#mtguardfoldreset`
全折叠域总控面板折叠记忆复位 / R234 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层折叠记忆**分工**（R219 全折叠记忆重置补 `_mtGuardAllDomain` 全折叠域总控面板折叠记忆复位，R234 加 `_mtGuardAllFoldStat`
全折叠域 5 域折叠态总控浮层折叠记忆（新第 6 键），R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位——全折叠记忆一键复位后全折叠域 6 键全复位，`#mtguardfoldreset` 全
折叠记忆重置 6 键全清 + 6 标志全复位）③ 与 R214 `#mtguardfoldresetcopy` 全折叠记忆重置详情复制 / R215 `#mtguardfoldresetpng` 全折叠记忆重置详情 PNG**分工**（R214/R215 重置详情读 6 键 `localStorage`
复位值 + 6 标志 `window` 复位值拼重置详情，R235 `#mtguardfoldreset` 重置后 6 键全复位 `localStorage` 值，R214/R215 重置详情读 6 键复位值自含全折叠域 6 键当前态，R214/R215 补 6 键段同 R220 重置详情
补第 5 键 `_mtGuardAllDomain` 同域，R235 重置 6 键全复位 + R214/R215 重置详情 6 键段双路自含全折叠域 6 键当前态）④ 与 R219 全折叠记忆重置补全折叠域总控面板折叠记忆 / R220 重置详情补第 5 键
`_mtGuardAllDomain` / R234 全折叠域 5 域折叠态总控浮层折叠记忆**语言同**（各全折叠记忆重置 / 重置详情读各键 `localStorage` 复位值 / 当前态，全折叠域 6 键当前态同语言，各出口自含全折叠域出口标位）
⑤ 验收**函数级**（设 6 键全 `'1'`（`_mtMetFold`/`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`/`_mtGuardAllFoldStat`）+ 6 标志全 `true` + 点 `#mtguardfoldreset` 验 6 键
全复位 `'0'`（`k6.every(v=>v==='0')`）+ `#mtallfoldstat` 文案复位「▣ 全折叠域浮层」+ toast「已重置维护守护区全折叠记忆」，不真跑 `mtRun` 免 tick 污染 `runs`；`#mtguardfoldreset` 重置拼逻辑验 6 键
`localStorage` 全清 `'0'` + 6 标志 `window` 全复位 `false` + 6 折叠钮文案复位 + 浮层 `display` 复位，非真渲染像素）。

---

## 第250轮（前端 R236 · goal round213）：维护守护区全折叠记忆重置详情补全折叠域 6 键（`#mtguardfoldresetcopy` 全折叠记忆重置详情复制（R214 区 `mtGuardFoldResetCopy`）+ `#mtguardfoldresetpng` 全折叠记忆重置详情 PNG（R215 区 `mtGuardFoldResetPng`）补第 6 键 `localStorage._mtGuardAllFoldStat` 当前态字段，全折叠记忆重置详情自含全折叠域 6 键当前态）

**完善性（全折叠记忆重置详情自含全折叠域 6 键当前态）**：R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位（全折叠域 6 键全复位），但**`#mtguardfoldresetcopy` 全折叠记忆
重置详情复制（R214 区，读 5 键 `localStorage` 复位值 + 5 标志 `window` 复位值 + 5 折叠钮文案复位 + 6 浮层 `display` 复位拼重置详情）/ `#mtguardfoldresetpng` 全折叠记忆重置详情 PNG（R215 区，读 5 键
`localStorage` 复位值拼重置详情内联 SVG）没全折叠域 6 键**（全折叠记忆重置详情要自含全折叠域 6 键当前态，`mtGuardFoldResetCopy`（R214 区）重置详情复制补第 6 键 `_mtGuardAllFoldStat` 当前态段（读 6 键
`localStorage` 复位值 + 6 标志 `window` 复位值 + 6 折叠钮文案复位 + 7 浮层 `display` 复位，循环 5→6 / 7→8）+ `mtGuardFoldResetPng`（R215 区）重置详情 PNG 补第 6 键 `_mtGuardAllFoldStat` 当前态段（读
6 键 `localStorage` 复位值拼 6 键色带内联 SVG，循环 5→6 / 7→8），全折叠记忆重置详情自含全折叠域 6 键当前态，与 R235 全折叠记忆一键重置补全折叠域 6 键同域）。

**E2E**：`设 6 键全 '0' 已复位 → 点 #mtguardfoldresetcopy → toast「已复制全折叠记忆重置详情」（复制含 6 键 / 6 标志 / 6 折叠钮 / 8 浮层当前态）+ 点 #mtguardfoldresetpng → toast「已下载全折叠记忆重置详情
PNG」（PNG 含 6 键 / 6 标志 / 6 折叠钮 / 8 浮层当前态内联 SVG 色带）`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r236_reset6keycopy.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 770→772`，断点 `_洛天依\杠上开花.mp3`。

**坑**：① `#mtguardfoldresetcopy` 全折叠记忆重置详情复制（R214 区，`mtGuardFoldResetCopy` 读全折叠记忆重置后各数据源（`localStorage` 5 键复位值 + `window` 5 标志复位值 + 5 折叠钮文案复位 + 6 浮层 `display`
复位 + 重置时间戳）拼重置详情到剪贴板，`#music3 全折叠记忆重置详情 · <ts>` + `[localStorage 5键复位值]` + `[window 5标志复位值]` + `[5折叠钮文案复位]` + `[6浮层display复位]`）补第 6 键全折叠域 5 域折叠态
总控浮层折叠记忆复位（R236，`_ls`/`_w` 加第 6 元素 `localStorage._mtGuardAllFoldStat` / `window._mtGuardAllFoldStat`，`_btns` 加 `mtallfoldstat`，`_floors` 加 `mtallfoldstatd`，`[localStorage 5键复位值]` →
`[localStorage 6键复位值]` + `[window 5标志复位值]` → `[window 6标志复位值]` + `[5折叠钮文案复位]` → `[6折叠钮文案复位]` + `[6浮层display复位]` → `[8浮层display复位]`，循环 5→6 / 7→8，全折叠记忆重置详情
自含全折叠域 6 键当前态，与 R235 全折叠记忆一键重置补全折叠域 6 键同域，`#mtguardfoldresetcopy` 重置详情复制补第 6 键）② `#mtguardfoldresetpng` 全折叠记忆重置详情 PNG（R215 区，`mtGuardFoldResetPng`
读 5 键 `localStorage` 复位值拼重置详情内联 SVG（`[localStorage 5键复位值]` + `[window 5标志复位值]` + `[5折叠钮文案复位]` + `[6浮层display复位]` 色带），`canvas` `toBlob` 转 PNG 下载「music3_全折叠记忆
重置详情_<ts>.png」（`toBlob` 不可用降级复制 SVG 源码））补第 6 键全折叠域 5 域折叠态总控浮层折叠记忆复位（R236，`_ls`/`_w` 加第 6 元素 + `_btns` 加 `mtallfoldstat` + `_floors` 加 `mtallfoldstatd`，
`[localStorage 5键复位值]` → `[localStorage 6键复位值]` + `[window 5标志复位值]` → `[window 6标志复位值]` + `[5折叠钮文案复位]` → `[6折叠钮文案复位]` + `[6浮层display复位]` → `[8浮层display复位]`，循环 5→6 /
7→8，全折叠记忆重置详情 PNG 自含全折叠域 6 键当前态，与 R235 全折叠记忆一键重置补全折叠域 6 键同域，`#mtguardfoldresetpng` 重置详情 PNG 补第 6 键）③ 与 R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键
`_mtGuardAllFoldStat` 复位 / R214 `#mtguardfoldresetcopy` 全折叠记忆重置详情复制 / R215 `#mtguardfoldresetpng` 全折叠记忆重置详情 PNG**分工**（R235 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位
（`#mtguardfoldreset` 全折叠域 6 键全复位），R236 全折叠记忆重置详情复制 / PNG 补第 6 键 `_mtGuardAllFoldStat` 当前态段（`#mtguardfoldresetcopy` 重置详情复制 + `#mtguardfoldresetpng` 重置详情 PNG 双路
自含全折叠域 6 键当前态，R214/R215 补 6 键段同 R220 重置详情补第 5 键 `_mtGuardAllDomain` 同域），R235 重置 6 键全复位 + R236 重置详情 6 键段双路自含全折叠域 6 键当前态）④ 与 R214 `#mtguardfoldresetcopy`
全折叠记忆重置详情复制 / R215 `#mtguardfoldresetpng` 全折叠记忆重置详情 PNG / R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键**语言同**（各全折叠记忆重置 / 重置详情读 6 键 `localStorage` 复位值 /
当前态 + 6 标志 `window` 复位值 + 6 折叠钮文案 + 8 浮层 `display` 拼文本 / 色带 / SVG，全折叠域 6 键当前态同语言，各出口自含全折叠域出口标位）⑤ 验收**函数级**（设 6 键全 `'0'` 已复位（`_mtMetFold`/
`_mtGuardPanelFold`/`_mtGuardFoldAll`/`_mtGuardFoldCtl`/`_mtGuardAllDomain`/`_mtGuardAllFoldStat`）+ 6 标志全 `false` + 点 `#mtguardfoldresetcopy` 验 toast「已复制全折叠记忆重置详情」（复制含 6 键 / 6 标志 / 6
折叠钮 / 8 浮层当前态）+ 点 `#mtguardfoldresetpng` 验 toast「已下载全折叠记忆重置详情 PNG」（PNG 含 6 键 / 6 标志 / 6 折叠钮 / 8 浮层当前态内联 SVG 色带），不真跑 `mtRun` 免 tick 污染 `runs`；`#mtguardfoldresetcopy`
重置详情复制拼逻辑验 6 键 / 6 标志 / 6 折叠钮 / 8 浮层字段进文本（`_ls`/`_w` 加第 6 元素 + `_btns` 加 `mtallfoldstat` + `_floors` 加 `mtallfoldstatd` + 循环 5→6 / 7→8），`#mtguardfoldresetpng` 重置详情 PNG
拼逻辑验 6 键 / 6 标志 / 6 折叠钮 / 8 浮层字段进 SVG（`_ls`/`_w` 加第 6 元素 + `_btns` 加 `mtallfoldstat` + `_floors` 加 `mtallfoldstatd` + 循环 5→6 / 7→8），非真剪贴板 / 渲染像素）。

---

## 第251轮（前端 R237 · goal round214）：维护守护区全折叠域 5 域折叠态总控浮层补全折叠域 6 键（`#mtallfoldstat` 全折叠域 5 域折叠态总控浮层（R234）内联 SVG 补第 6 键 `localStorage._mtGuardAllFoldStat` 当前态字段（`[全折叠域5域]` 5 域色带补第 6 域 + `[6标志 window]` + `[6折叠钮文案]` + `[8浮层 display]`，全折叠域 5 域折叠态总控浮层自含全折叠域 6 键当前态）

**完善性（全折叠域 5 域折叠态总控浮层自含全折叠域 6 键当前态）**：R234 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层（内联 SVG 读 5 键 `localStorage` + 5 标志 `window` + 5 折叠钮 + 7 浮层）+
R235 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` + R236 重置详情补第 6 键，但**`mtAllFoldStat`（R234 区）内联 SVG `[全折叠域5域]` 5 域色带（`_doms` 数组 5 元素：`['双图区','_mtMetFold']` / `['总览面板',
'_mtGuardPanelFold']` / `['全浮层','_mtGuardFoldAll']` / `['折叠全链路','_mtGuardFoldCtl']` / `['全折叠域总控','_mtGuardAllDomain']`）没第 6 键 `_mtGuardAllFoldStat`**（全折叠域 5 域折叠态总控浮层要
自含全折叠域 6 键当前态，`mtAllFoldStat`（R234 区）内联 SVG 补第 6 键 `localStorage._mtGuardAllFoldStat` 当前态段（`[全折叠域5域]` 5 域色带补第 6 域 `['全折叠域5域折叠态总控浮层','_mtGuardAllFoldStat']` +
`[6标志 window]` 补第 6 标志 `window._mtGuardAllFoldStat` + `[6折叠钮文案]` 补第 6 折叠钮 `mtallfoldstat` + `[8浮层 display]` 补第 8 浮层 `mtallfoldstatd`，循环 5→6 / 7→8），全折叠域 5 域折叠态总控浮层
自含全折叠域 6 键当前态，与 R235/R236 全折叠记忆重置补全折叠域 6 键同域）。

**E2E**：`设 6 键全 '1' + 6 标志全 true → 直接调 mtAllFoldStat() 拼面板 → #mtallfoldstatd SVG 含 [全折叠域5域] 6 域（含 _mtGuardAllFoldStat 第 6 键）+ [6标志 window] + [6折叠钮文案] + [8浮层 display]
分块`（绿）；端点 **30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r237_allfoldstat6key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 772→774`，断点 `_洛天依\讨厌摇滚乐.mp3`。

**坑**：① `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层（R234 区，`mtAllFoldStat` 拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG：`_rows` 数组拼标题 + `[全折叠域5域]` 5 域色带（`_doms`
数组 5 元素，各域 `localStorage` 折叠态（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠 `--bad` 红）+ 域名 + 键名 + 值 + `[5标志 window]` 5 标志色带（`_w5` 各 `window` 标志，`false` 展开 `--ok` 绿 / `true` 折叠 `--bad`
红）+ 标志名 + 值 + `[5折叠钮文案]` 5 折叠钮 `textContent` + `[7浮层 display]` 7 浮层 `style.display` 色带（`none` 隐 `--ok` 绿 / 显 `--dim` 灰），`#mtallfoldstatd` `innerHTML` 拼 SVG + `getBoundingClientRect`
下沿定位 + `z-index:70` + 8s 自动隐））补第 6 键全折叠域 5 域折叠态总控浮层折叠记忆（R237，`_doms` 数组加第 6 元素 `['全折叠域5域折叠态总控浮层','_mtGuardAllFoldStat']`（`_doms` 5 元素 → 6 元素，循环 5→6），
`_w5`/`_wk` 加第 6 元素 `window._mtGuardAllFoldStat` / `_mtGuardAllFoldStat`（`_w5` 5 元素 → 6 元素，`[5标志 window]` → `[6标志 window]`，循环 5→6），`_btns5` 加 `mtallfoldstat`（`_btns5` 5 元素 → 6 元素，`[5折叠钮文案]`
→ `[6折叠钮文案]`，循环 5→6），`_floors7` 加 `mtallfoldstatd`（`_floors7` 7 元素 → 8 元素，`[7浮层 display]` → `[8浮层 display]`，循环 7→8），全折叠域 5 域折叠态总控浮层自含全折叠域 6 键当前态（`[全折叠域5域]` 6
域色带含 `_mtGuardAllFoldStat` 第 6 键 + `[6标志 window]` 含 `window._mtGuardAllFoldStat` + `[6折叠钮文案]` 含 `mtallfoldstat` + `[8浮层 display]` 含 `mtallfoldstatd`），与 R235/R236 全折叠记忆重置补全折叠域 6 键
同域，`#mtallfoldstat` 全折叠域 5 域折叠态总控浮层补第 6 键）② 与 R234 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层 / R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位 / R236
`#mtguardfoldresetcopy` 全折叠记忆重置详情复制 / R236 `#mtguardfoldresetpng` 全折叠记忆重置详情 PNG**分工**（R234 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层（内联 SVG 读 5 键 `localStorage` + 5 标志 `window` + 5
折叠钮 + 7 浮层），R235 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位（`#mtguardfoldreset` 全折叠域 6 键全复位），R236 全折叠记忆重置详情复制 / PNG 补第 6 键 `_mtGuardAllFoldStat` 当前态段（`#mtguardfoldresetcopy`
重置详情复制 + `#mtguardfoldresetpng` 重置详情 PNG 双路自含全折叠域 6 键当前态），R237 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层内联 SVG 补第 6 键 `_mtGuardAllFoldStat` 当前态段（`[全折叠域5域]` 5 域色带补第 6 域 +
`[6标志 window]` + `[6折叠钮文案]` + `[8浮层 display]`，全折叠域 5 域折叠态总控浮层自含全折叠域 6 键当前态），R234/R235/R236/R237 全折叠域 6 键全自含当前态）③ `mtAllFoldPng`（R233）与 `mtAllFoldStat`（R234）同结构
（`_rows` 数组拼 `[全折叠域5域]` 5 域色带 + `[5标志 window]` + `[5折叠钮文案]` + `[7浮层 display]`），`edit` `old_string` 匹配 2 次——加 `[全折叠域5域]` 标签（`_rows.push` 行）作锚定位 `mtAllFoldStat`（`mtAllFoldPng`
`_rows.push` 标签行 `全折叠域5域` 文本不同），免 `mtAllFoldPng` 误改（`mtAllFoldStat` 补第 6 键，`mtAllFoldPng` 待 R238 补第 6 键），同 R225 `#mtguardfoldctld` 无 SVG（`svg=False`）验收直接调函数拼面板纪律④ 与
R234 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层 / R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 / R236 `#mtguardfoldresetcopy` / `#mtguardfoldresetpng` 全折叠记忆重置详情复制 / PNG 补第 6 键**语言同**（各全
折叠域 5 域折叠态总控浮层 / 全折叠记忆重置 / 重置详情读 6 键 `localStorage` 当前态 / 复位值 + 6 标志 `window` + 6 折叠钮文案 + 8 浮层 `display` 拼文本 / 色带 / SVG，全折叠域 6 键当前态同语言，各出口自含全折叠域
出口标位）⑤ 验收**函数级**（设 6 键全 `'1'` + 6 标志全 `true` + 直接调 `mtAllFoldStat()` 拼内联 SVG（绕 R234 折叠记忆切态——设 `_mtGuardAllFoldStat` 无后点 `#mtallfoldstat` 走 R234 折叠记忆切（当前展开态 → 切折叠才
隐面板），验收直接调 `mtAllFoldStat()` 免切态干扰）+ 验 `#mtallfoldstatd` `innerHTML` 含 `<svg` + `[全折叠域5域]` 6 域（含 `_mtGuardAllFoldStat` 第 6 键）+ `[6标志 window]` + `[6折叠钮文案]` + `[8浮层 display]` 分块，
不真跑 `mtRun` 免 tick 污染 `runs`；SVG 拼逻辑验全折叠域 6 域 / 6 标志 / 6 折叠钮 / 8 浮层字段进 SVG，非真渲染像素）。

---

## 第252轮（前端 R238 · goal round215）：维护守护区全折叠域 5 域折叠态 PNG 快照补全折叠域 6 键（`#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照（R233）内联 SVG 补第 6 键 `localStorage._mtGuardAllFoldStat` 当前态字段（`[全折叠域5域]` 5 域色带补第 6 域 + `[6标志 window]` + `[6折叠钮文案]` + `[8浮层 display]`，全折叠域 5 域折叠态 PNG 快照自含全折叠域 6 键当前态）

**完善性（全折叠域 5 域折叠态 PNG 快照自含全折叠域 6 键当前态）**：R237 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层内联 SVG 补第 6 键 `_mtGuardAllFoldStat`，但**`mtAllFoldPng`（R233 区，`#mtallfoldpng` 全
折叠域 5 域折叠态 PNG 快照，内联 SVG 读 5 键 `localStorage` + 5 标志 `window` + 5 折叠钮 + 7 浮层）没第 6 键 `_mtGuardAllFoldStat`**（全折叠域 5 域折叠态 PNG 快照要自含全折叠域 6 键当前态，
`mtAllFoldPng`（R233 区）内联 SVG 补第 6 键 `localStorage._mtGuardAllFoldStat` 当前态段（`_doms` 数组加第 6 元素 `['全折叠域5域折叠态总控浮层','_mtGuardAllFoldStat']` + `[5标志 window]` → `[6标志 window]` +
`[5折叠钮文案]` → `[6折叠钮文案]` + `[7浮层 display]` → `[8浮层 display]`，循环 5→6 / 7→8），全折叠域 5 域折叠态 PNG 快照自含全折叠域 6 键当前态，与 R235/R236/R237 全折叠记忆重置补全折叠域 6 键同域）。

**E2E**：`设 6 键全 '1' + 6 标志全 true → 点 #mtallfoldpng 导出 PNG → PNG 快照下载（全折叠域 6 键 / 6 标志 / 6 折叠钮 / 8 浮层当前态内联 SVG 转 PNG，headless 下载无 toast 属正常）`（绿）；端点
**30/0**、JS undefined NONE、CSS 320/320、node 0、console 0、截图 r238_allfoldpng6key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 774→776`，断点 `_热门歌曲\开始懂了 - 孙燕姿.mp3`。

**坑**：① `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照（R233 区，`mtAllFoldPng` 拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态内联 SVG：`_rows` 数组拼标题 + `[全折叠域5域]` 5 域色带（`_doms` 数组
5 元素，各域 `localStorage` 折叠态（`'0'` 展开 `--ok` 绿 / 非 `'0'` 折叠 `--bad` 红）+ 域名 + 键名 + 值 + `[5标志 window]` 5 标志色带（`_w5` 各 `window` 标志，`false` 展开 `--ok` 绿 / `true` 折叠 `--bad` 红）+
标志名 + 值 + `[5折叠钮文案]` 5 折叠钮 `textContent` + `[7浮层 display]` 7 浮层 `style.display` 色带（`none` 隐 `--ok` 绿 / 显 `--dim` 灰），`_host` 隐藏容器 + `_imgv` SVG 转 PNG + `canvas` `toBlob` 转 PNG 下载
「music3_全折叠域5域折叠态_<ts>.png」（`toBlob` 不可用降级 toast「PNG 导出不可用（toBlob 不支持）」+ `canvas` 不可用降级 toast「PNG 导出失败（canvas 不可用）」+ SVG 渲染失败降级 toast「PNG 导出失败
（SVG 渲染不可用）」））补第 6 键全折叠域 5 域折叠态总控浮层折叠记忆（R238，`_doms` 数组加第 6 元素 `['全折叠域5域折叠态总控浮层','_mtGuardAllFoldStat']`（`_doms` 5 元素 → 6 元素，循环 5→6），`_w5`/`_wk`
加第 6 元素 `window._mtGuardAllFoldStat` / `_mtGuardAllFoldStat`（`_w5` 5 元素 → 6 元素，`[5标志 window]` → `[6标志 window]`，循环 5→6），`_btns5` 加 `mtallfoldstat`（`_btns5` 5 元素 → 6 元素，`[5折叠钮文案]`
→ `[6折叠钮文案]`，循环 5→6），`_floors7` 加 `mtallfoldstatd`（`_floors7` 7 元素 → 8 元素，`[7浮层 display]` → `[8浮层 display]`，循环 7→8），全折叠域 5 域折叠态 PNG 快照自含全折叠域 6 键当前态（`[全折叠域
5域]` 6 域色带含 `_mtGuardAllFoldStat` 第 6 键 + `[6标志 window]` 含 `window._mtGuardAllFoldStat` + `[6折叠钮文案]` 含 `mtallfoldstat` + `[8浮层 display]` 含 `mtallfoldstatd`），与 R235/R236/R237 全折叠记忆
重置补全折叠域 6 键同域，`#mtallfoldpng` PNG 快照补第 6 键）② `mtAllFoldPng`（R233）与 `mtAllFoldStat`（R234）同结构（`_rows` 数组拼 `[全折叠域5域]` 5 域色带 + `[5标志 window]` + `[5折叠钮文案]` +
`[7浮层 display]`），`edit` `old_string` 匹配 2 次——加 `[全折叠域5域]` 标签（`_rows.push` 行）+ `_host` 行作锚定位 `mtAllFoldPng`（`_host` 隐藏容器 `canvas` 转 PNG 特征，`mtAllFoldStat` 是 `_d` 浮层无
`_host`），免 `mtAllFoldStat` 误改（`mtAllFoldPng` 补第 6 键，`mtAllFoldStat` R237 已补第 6 键），同 R237 `mtAllFoldStat` 补第 6 键用 `[全折叠域5域]` 标签作锚纪律③ 与 R233 `#mtallfoldpng` 全折叠域 5 域
折叠态 PNG 快照 / R237 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层补第 6 键 / R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位 / R236 `#mtguardfoldresetcopy` / `#mtguardfoldresetpng`
全折叠记忆重置详情复制 / PNG 补第 6 键**分工**（R233 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照（内联 SVG 读 5 键 `localStorage` + 5 标志 `window` + 5 折叠钮 + 7 浮层），R237 `#mtallfoldstat` 全折叠域 5 域
折叠态总控浮层内联 SVG 补第 6 键 `_mtGuardAllFoldStat` 当前态段，R235 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位（`#mtguardfoldreset` 全折叠域 6 键全复位），R236 全折叠记忆重置详情复制 / PNG 补第 6
键 `_mtGuardAllFoldStat` 当前态段，R238 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照内联 SVG 补第 6 键 `_mtGuardAllFoldStat` 当前态段（`[全折叠域5域]` 5 域色带补第 6 域 + `[6标志 window]` + `[6折叠钮文案]` +
`[8浮层 display]`，全折叠域 5 域折叠态 PNG 快照自含全折叠域 6 键当前态），R233/R235/R236/R237/R238 全折叠域 6 键全自含当前态）④ 与 R233 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照 / R234 `#mtallfoldstat`
全折叠域 5 域折叠态总控浮层 / R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 / R236 `#mtguardfoldresetcopy` / `#mtguardfoldresetpng` 全折叠记忆重置详情复制 / PNG 补第 6 键 / R237 `#mtallfoldstat` 全折叠
域 5 域折叠态总控浮层补第 6 键**语言同**（各全折叠域 5 域折叠态 PNG 快照 / 总控浮层 / 全折叠记忆重置 / 重置详情读 6 键 `localStorage` 当前态 / 复位值 + 6 标志 `window` + 6 折叠钮文案 + 8 浮层 `display` 拼
文本 / 色带 / SVG，全折叠域 6 键当前态同语言，各出口自含全折叠域出口标位）⑤ 验收**函数级**（设 6 键全 `'1'` + 6 标志全 `true` + 点 `#mtallfoldpng` 导出 PNG 验 PNG 快照下载（全折叠域 6 键 / 6 标志 / 6 折叠
钮 / 8 浮层当前态内联 SVG 转 PNG），不真跑 `mtRun` 免 tick 污染 `runs`；`#mtallfoldpng` PNG 拼逻辑验全折叠域 6 域 / 6 标志 / 6 折叠钮 / 8 浮层字段进内联 SVG（`_doms` 加第 6 元素 + `_w5`/`_wk` 加第 6 元素 +
`_btns5` 加 `mtallfoldstat` + `_floors7` 加 `mtallfoldstatd` + 循环 5→6 / 7→8），headless 下载 PNG 无 toast 属正常（`canvas` `toBlob` 转 PNG 下载不显 toast，降级才 toast「PNG 导出不可用」/「PNG 导出失败」，
验 `console 0` + 下载成功，真 PNG 内容不验）。

---

## 第253轮（前端 R239 · goal round216）：维护守护区全折叠域 5 域折叠态一键复制出口补全折叠域 6 键（`#mtallfoldcopy` 全折叠域 5 域折叠态一键复制（R232）补第 6 键 `localStorage._mtGuardAllFoldStat` 当前态字段（`[全折叠域5域]` 5 域色带补第 6 域 + `[6键 localStorage]` + `[6标志 window]` + `[6折叠钮]` + `[8浮层 display]`，全折叠域 5 域折叠态一键复制自含全折叠域 6 键当前态）

**完善性（全折叠域 5 域折叠态一键复制自含全折叠域 6 键当前态）**：R238 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照补第 6 键 `_mtGuardAllFoldStat` 当前态段（内联 SVG 补第 6 域 / 6 标志 / 6 折叠钮 / 8 浮层），但
**`#mtallfoldcopy` 全折叠域 5 域折叠态一键复制（R232 区，`mtAllFoldCopy` 拼全折叠域 5 域（`_doms` 数组 5 元素）+ 5 键 `localStorage` + 5 标志 `window` + 5 折叠钮 + 7 浮层当前态到剪贴板）没第 6 键 `_mtGuardAllFoldStat`**
（全折叠域 5 域折叠态一键复制要自含全折叠域 6 键当前态，`mtAllFoldCopy`（R232 区）复制文本补第 6 键 `localStorage._mtGuardAllFoldStat` 当前态段（`_doms` 数组加第 6 元素 `['全折叠域5域折叠态总控浮层',
'#mtallfoldstat','_mtGuardAllFoldStat']` + `[5键 localStorage]` → `[6键 localStorage]` + `[5标志 window]` → `[6标志 window]` + `[5折叠钮]` → `[6折叠钮]` + `[7浮层 display]` → `[8浮层 display]`，循环 5→6 / 7→8），
全折叠域 5 域折叠态一键复制自含全折叠域 6 键当前态，与 R235/R236/R237/R238 全折叠记忆重置补全折叠域 6 键同域）。

**E2E**：`设 6 键全 '1' + 6 标志全 true → 点 #mtallfoldcopy → toast「已复制全折叠域 5 域折叠态」（复制含全折叠域 6 域 / 6 键 / 6 标志 / 6 折叠钮 / 8 浮层当前态）`（绿）；端点 **30/0**、JS undefined NONE、
CSS 320/320、node 0、console 0、截图 r239_allfoldcopy6key.png。

**完善性（游标续推）**：全库 2 批 batch=20 `runs 776→778`，断点 `_草东没有派对\Intro.mp3`。

**坑**：① `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制（R232 区，`mtAllFoldCopy` 拼全折叠域 5 域 / 5 键 / 5 标志 / 5 折叠钮 / 7 浮层当前态到剪贴板：`_lines` 拼标题 + `[全折叠域5域]` 5 域（`_doms` 数组 5 元素
（3 列 `[域名,折叠钮id,键名]`），各域 `localStorage` 折叠态（`'1'` 折叠 / `'0'` 展开）+ 域名 + 折叠钮 id + `localStorage` 值 + `[5键 localStorage 当前态]` 5 键 `localStorage`（`||'0'` 降级）+ `[5标志 window 当前态]` 5
标志 `window` + `[5折叠钮文案]` 5 折叠钮 `textContent` + `[7浮层 display 当前态]` 7 浮层 `style.display`，`navigator.clipboard.writeText` 降级 `_copyFallback` + toast「已复制全折叠域5域折叠态」））补第 6 键全折叠
域 5 域折叠态总控浮层折叠记忆（R239，`_doms` 数组加第 6 元素 `['全折叠域5域折叠态总控浮层','#mtallfoldstat','_mtGuardAllFoldStat']`（`_doms` 5 元素 → 6 元素，循环 5→6），`_ls5` 加第 6 元素 `localStorage.
_mtGuardAllFoldStat`（`_ls5` 5 元素 → 6 元素，`[5键 localStorage]` → `[6键 localStorage]` + 5 键段补 `_mtGuardAllFoldStat`），`_w5` 加第 6 元素 `window._mtGuardAllFoldStat`（`_w5` 5 元素 → 6 元素，`[5标志 window]`
→ `[6标志 window]` + 5 标志段补 `_mtGuardAllFoldStat`），`_btns5` 加 `mtallfoldstat`（`_btns5` 5 元素 → 6 元素，`[5折叠钮]` → `[6折叠钮]` + 循环 5→6），`_floors7` 加 `mtallfoldstatd`（`_floors7` 7 元素 → 8 元素，
`[7浮层 display]` → `[8浮层 display]` + 循环 7→8），全折叠域 5 域折叠态一键复制自含全折叠域 6 键当前态（`[全折叠域5域]` 6 域含 `_mtGuardAllFoldStat` 第 6 键 + `[6键 localStorage]` 含 `localStorage._mtGuardAllFoldStat`
+ `[6标志 window]` 含 `window._mtGuardAllFoldStat` + `[6折叠钮]` 含 `mtallfoldstat` + `[8浮层 display]` 含 `mtallfoldstatd`），与 R235/R236/R237/R238 全折叠记忆重置补全折叠域 6 键同域，`#mtallfoldcopy` 复制出口
补第 6 键）② `mtAllFoldCopy`（R232）`_doms` 数组 3 列结构（`[域名,折叠钮id,键名]`）与 `mtAllFoldPng`（R233）/ `mtAllFoldStat`（R234）`_doms` 数组 2 列结构（`[域名,键名]`）不同（R232 复制文本拼各域 `localStorage` 折叠态
需折叠钮 id，R233/R234 PNG/浮层拼 SVG 色带不需折叠钮 id 只需键名），R239 补第 6 元素 3 列 `['全折叠域5域折叠态总控浮层','#mtallfoldstat','_mtGuardAllFoldStat']`（同 R232 原 5 元素 3 列结构，补第 6 元素 3 列），
同 R232 原 `_doms` 3 列结构纪律③ 与 R232 `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制 / R238 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照补第 6 键 / R237 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层补第 6 键 /
R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位 / R236 `#mtguardfoldresetcopy` / `#mtguardfoldresetpng` 全折叠记忆重置详情复制 / PNG 补第 6 键**分工**（R232 `#mtallfoldcopy` 全折叠域 5 域
折叠态一键复制（`_doms` 3 列 5 元素 + 5 键 / 5 标志 / 5 折叠钮 / 7 浮层），R238 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照内联 SVG 补第 6 键 `_mtGuardAllFoldStat` 当前态段，R237 `#mtallfoldstat` 全折叠域 5 域折叠
态总控浮层内联 SVG 补第 6 键 `_mtGuardAllFoldStat` 当前态段，R235 全折叠记忆重置补第 6 键 `_mtGuardAllFoldStat` 复位（`#mtguardfoldreset` 全折叠域 6 键全复位），R236 全折叠记忆重置详情复制 / PNG 补第 6 键
`_mtGuardAllFoldStat` 当前态段，R239 `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制补第 6 键 `_mtGuardAllFoldStat` 当前态段（`_doms` 加第 6 元素 + `[6键 localStorage]` + `[6标志 window]` + `[6折叠钮]` + `[8浮层 display]`，
全折叠域 5 域折叠态一键复制自含全折叠域 6 键当前态），R232/R235/R236/R237/R238/R239 全折叠域 6 键全自含当前态）④ 与 R232 `#mtallfoldcopy` 全折叠域 5 域折叠态一键复制 / R233 `#mtallfoldpng` 全折叠域 5 域折叠态
PNG 快照 / R234 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层 / R235 `#mtguardfoldreset` 全折叠记忆重置补第 6 键 / R236 `#mtguardfoldresetcopy` / `#mtguardfoldresetpng` 全折叠记忆重置详情复制 / PNG 补第 6 键 /
R237 `#mtallfoldstat` 全折叠域 5 域折叠态总控浮层补第 6 键 / R238 `#mtallfoldpng` 全折叠域 5 域折叠态 PNG 快照补第 6 键**语言同**（各全折叠域 5 域折叠态一键复制 / PNG 快照 / 总控浮层 / 全折叠记忆重置 / 重置详情读
6 键 `localStorage` 当前态 / 复位值 + 6 标志 `window` + 6 折叠钮文案 + 8 浮层 `display` 拼文本 / 色带 / SVG，全折叠域 6 键当前态同语言，各出口自含全折叠域出口标位）⑤ 验收**函数级**（设 6 键全 `'1'` + 6 标志全 `true`
+ 点 `#mtallfoldcopy` 验 toast「已复制全折叠域5域折叠态」（复制含全折叠域 6 域 / 6 键 / 6 标志 / 6 折叠钮 / 8 浮层当前态），不真跑 `mtRun` 免 tick 污染 `runs`；`#mtallfoldcopy` 复制拼逻辑验全折叠域 6 域 / 6 键 / 6
标志 / 6 折叠钮 / 8 浮层字段进文本（`_doms` 加第 6 元素 + `_ls5`/`_w5` 加第 6 元素 + `_btns5` 加 `mtallfoldstat` + `_floors7` 加 `mtallfoldstatd` + 循环 5→6 / 7→8），非真剪贴板 / 渲染像素）。

