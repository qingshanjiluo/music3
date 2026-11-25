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

