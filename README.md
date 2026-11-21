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

