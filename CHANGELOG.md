# Super Hi Vision Changelog

## Version 1.5.25 (2026-10-09)

**正式发行包**：把 1.5.24 的修复与代码签名一起打包发布（1.5.24 未单独发版，其内容并入本版）。

### 本次新增
- **CI 去掉版本号硬编码**：workflow 里 11 处 `SuperHiVision_v<版本>.exe` 改为通配符查找 / `${{ github.ref_name }}`，以后再升版不必逐个修改（漏改会让 CI 在「检查产物」那步直接失败）
- **重新打包并正式签名**：exe / 安装包的属性与 UAC 提示里，发行者显示为 `SevenZeroMeowTeam`

### 包含 1.5.24 的内容（详见下一节）
- FFmpeg 定位路径的**大小写归一化**（磁盘上是 `ffmpeg.EXE` 也统一显示/调用为小写 `ffmpeg.exe`）
- 代码签名流程（`tools/create_signing_cert.ps1` + `tools/sign_binaries.ps1`）、发行者版本资源（spec + installer.nsi）、说明文档 `docs/CODE_SIGNING.md`

## Version 1.5.24 (2026-10-08)

### 修复：定位到的 FFmpeg 路径显示成大写后缀（`ffmpeg.EXE`）
- **现象**：高级设置页的 FFmpeg 状态常驻显示 `FFmpeg 已就绪：C:\...\ffmpeg\ffmpeg.EXE`，后缀是大写
- **根因**：程序构造的候选路径写的是小写 `<目录>\ffmpeg\ffmpeg.exe`。Windows 文件名不区分大小写，`os.path.isfile()` 照样命中磁盘上的 `ffmpeg.EXE`，但**返回给界面的字符串保留了磁盘上的原始拼写**，于是状态栏回显成 `.EXE`，下发给子进程的命令行也带着这串大写拼写。磁盘上文件名恰好是小写时看不出问题，所以只在「下载/解压工具把文件名写成大写」的机器上暴露
- **修法**：新增三个助手把「路径拼写」统一收敛——`_match_exe_in_dir()` 只把目录项当作「存在性证据」，命中后一律用规范拼写 `ffmpeg.exe` 回填路径；`_canonical_exe()` / `_resolve_exe()` 统一处理所有来源（候选目录、`sys._MEIPASS`、`%LOCALAPPDATA%`、注册表、系统 `PATH`），显示与调用都稳定成小写
- **顺手兼容**：① `FFMPEG.EXE` / `Ffmpeg.Exe` 等各种大小写写法；② 用户解压后自行改名成 `ffmpeg-n7.1-essentials.exe` 这类变体（同目录内按「小写 `ffmpeg` 开头 + `.exe` 结尾」宽容匹配）；③ 不再把同目录的 `ffplay.exe` 误当成 `ffmpeg`
- **回归测试**：新增 `tools/verify_ffmpeg_case.py` —— 用 AST 从 `Super_Hi_Vision_PyQt.py` 里取出真实方法本体执行（不是副本，避免假绿灯），覆盖 8 个用例（大写/全大写/混合/正常小写/改名变体/缺失/无关 exe/0 字节坏文件）：8/8 通过

### 新增：代码签名与「发行者」信息（SevenZeroMeowTeam）
- **exe / 安装包的发行者固定为 `SevenZeroMeowTeam`**：`SuperHiVision.spec` 动态生成版本资源（版本号从 `__version__` 读取，不再两处维护），`installer.nsi` 补上 `VIProductVersion` + `VIAddVersionKey`。这部分**不需要证书**，重新打包即生效
- **自签名代码签名流程**：新增 `tools/create_signing_cert.ps1`（生成 `CN=SevenZeroMeowTeam` 代码签名证书并登记为本机受信任发行者）与 `tools/sign_binaries.ps1`（签名工具，签名前自动留 `.unsigned` 备份、带 RFC3161 时间戳、失败可不带时间戳重试）
- **CI 可选自动签名**：仓库配置 `SIGNING_PFX_BASE64` / `SIGNING_PFX_PASSWORD` 两个 secrets 后，推 tag 时自动签名绿色版与安装包；**未配置则自动跳过，不影响出包**
- **关键限制已写进文档** `docs/CODE_SIGNING.md`：自签名证书只让**装了这张证书的机器**不再提示「未知发布者」；要让所有下载者都不看到警告，必须使用商业 CA 证书（届时只需换证书，代码无需改动）
- **构建期校验**：新增 `tools/check_version_resource.py`，按 PyInstaller 的加载方式校验版本资源；spec 内部也加了自校验，资源异常时降级为「不带版本资源构建」，而不是让 CI 整体失败

## Version 1.5.23 (2026-10-06)

### 修复：保存后「有画面无声音」
- **根因**：绿色版 exe 本身不带 FFmpeg，一旦被单独拷到别处（如 `F:\videos`），保存阶段的音视频合成直接失败 —— 视频写出来了却没声音，而且旧提示只让用户「确认 ffmpeg 文件夹存在」，既没说清去哪找、也没保住录到的音频
- **FFmpeg 现在内置进单文件 exe**：`ffmpeg.exe` + `ffprobe.exe` 随包解到 `_MEIPASS\ffmpeg\`，绿色版拷到任意目录都能合成音频；不再分发无用的 `ffplay.exe`（省约 150MB）
- **查找范围大幅加宽**（按优先级）：`<exe目录>\ffmpeg`（外置优先，可自行替换版本）→ `_MEIPASS\ffmpeg`（内置）→ `<exe目录>\bin` → 上一级目录 → `%LOCALAPPDATA%` → `C:\ffmpeg\bin` / Program Files / scoop / chocolatey → 注册表 `HKLM|HKCU\SOFTWARE\ffmpeg` → 系统 PATH；候选结果缓存，一次录制只探测一次
- **合并失败绝不丢音频**：改为把 WAV 另存为与视频同名的 `xxx.audio.wav`，提示里给出完整路径，装上 FFmpeg 后可再合成
- **失败原因不再含糊**：对话框区分「未找到 FFmpeg」（明确给出该放的确切路径）与「FFmpeg 跑了但报错」（附 FFmpeg 错误尾部），并把完整现场写进错误日志
- **新增「检查 FFmpeg」自检**：高级设置页常驻显示 FFmpeg 状态（✅ 路径 / ❌ 缺失），一键重新探测并弹出结论
- **帧率校正同样受益**：以前找不到 FFmpeg 时帧率校正会静默跳过（导致快放/慢放），现在同样能找到内置副本

## Version 1.5.22 (2026-10-05)

### 新增：降噪强度可调滑杆（0-100%）
- 音频设置页的「降噪开关」改为**滑杆**：最左 0 = 关闭降噪，往右依次显示 `轻度(1-33%) / 中度(34-66%) / 强力(67-100%)`，默认 **40%**（等价于 1.5.21 的固定参数）
- 滑杆值实时写入 `~/.super_hi_vision_settings.json` 的 `denoise_strength`，并在保存视频时反映到 FFmpeg 链：
  `highpass=f=80` → `afftdn=nr=6~24:nf=-40~-20` → `loudnorm=I=-16:TP=-1.5:LRA=11` → `apad`（三级降级逻辑保持不变）
- 参数映射：`nr`（降噪量）6 → 24，`nf`（噪声底）‑40 → ‑20 dB；强度 40 ≈ `nr=13.1:nf=-32`
- **实测标定**（6 秒粉噪声样本，原始底噪 ≈‑36 dB，每轮随机样本浮动 ±0.5 dB）：强度 20 / 40 / 60 / 80 / 100 的输出底噪依次为 **≈‑43.1 / ‑46.2 / ‑51.0 / ‑57.4 / ‑62.3 dB**，单调下降（强度 100 比 20 多压约 19 dB）
- **兼容旧设置**：读到 1.5.21 及更早的 `{"denoise": true/false}` 自动折算为 40% / 关闭；越界值夹到 0-100

### 界面
- 音频页滑杆右侧实时显示当前档位与百分比；提示文案说明「降噪在保存时处理，不占录制 CPU」

## Version 1.5.21 (2026-10-05)

### 新增：音频降噪
- 音频设置页新增「音频降噪（去除背景底噪 / 电流声）」开关（默认开启，随 `~/.super_hi_vision_settings.json` 持久化）
- 降噪放在保存阶段由 FFmpeg 统一处理，**不占用录制时的 CPU**：`highpass=f=80`（滤掉低频轰隆/电流声）→ `afftdn=nr=12:nf=-30`（FFT 自适应降噪）→ `loudnorm` 响度归一化 → `apad`
- 合并命令带**三级降级**：`降噪+响度归一化` → `无降噪+响度归一化` → `不做音频处理`，某个滤波器不可用时不会整段失败（避免「有画面没声音」）

### 修复：应用后台不保活 / 再次点击应用打不开
- 新增系统托盘（`QSystemTrayIcon`）：关闭窗口默认**最小化到托盘、程序继续在后台运行**——录制不中断、全局热键（F9/F10/F11/F12）照常可用；托盘菜单提供「显示主窗口 / 开始·暂停 / 停止录制 / 退出」
- `app.setQuitOnLastWindowClosed(False)`：窗口隐藏期间不会被 Qt 当成「最后一个窗口已关闭」而退出
- 新增**单实例机制**（`QLocalServer`/`QLocalSocket` 本机命名管道）：程序已在运行（可能在托盘里）时，再次点击桌面图标/EXE 会通知已有实例**把窗口唤回前台**，第二个进程随即退出——不再出现「明明在后台跑，点了图标却打不开、也看不到窗口」
- 唤起窗口时在 Windows 上借用 `WindowStaysOnTopHint` 强制前台（仅 `activateWindow()` 常常抢不到焦点）
- 高级设置页新增「关闭窗口时最小化到托盘（后台继续运行）」开关，可关掉该行为（关掉后关闭窗口=退出，行为和旧版一致）

### 变更：静默合成视频，不弹窗
- 保存（帧率校正 / 音视频合并）不再弹出模态进度对话框，改为**窗口内**进度提示：状态栏文字 + 底部不确定进度条，主线程持续 `processEvents()`，窗口既不「无响应」也不打断用户
- 保存成功不再弹「Recording Complete」对话框，改为状态栏提示 `✅ 已保存 <文件名>` + 托盘提示（窗口在托盘时只更新托盘 tooltip，全程静默）
- 仅在**失败**时保留对话框（0 字节/合并失败等），避免静默丢文件

### 修复：视频保存完成后应用崩溃 / 打不开（1.5.20 引入的根因修复，本节为当版延续）
- 根因：`cv2.VideoWriter` 的「创建（GUI 线程）→ 写帧（录制线程）→ 释放（GUI 线程）」跨线程使用。OpenCV 自带的 FFmpeg 封装（`opencv_videoio_ffmpeg*.dll`）不是线程安全的，跨线程 `release()` 时直接 `abort()`——Windows 事件日志：异常代码 `0x40000015`（`STATUS_FATAL_APP_EXIT`），故障模块正是该 dll
- 写入器由录制线程全权持有（创建 / 写帧 / 释放同线程）；创建失败经 `recording_error` 信号回主线程弹窗
- 全局异常兜底 `_install_exception_guard()`：槽函数里的未捕获异常改为「写 `SuperHiVision_error.log` + 弹窗」并让程序继续存活（此前 PyQt5 → `qFatal()` → `abort()`）
- 安装目录不可写时（`Program Files`）日志回退到 `%LOCALAPPDATA%\SuperHiVision\`；卸载脚本补删日志、`resources\`/`ffmpeg\` 用 `RMDir /r` 删净、主程序 `Delete /REBOOTOK`

## Version 1.5.20 (2026-10-05)

### 修复：视频保存完成后应用崩溃 / 打不开

- 根因：`cv2.VideoWriter` 的「创建（GUI 线程）→ 写帧（录制线程）→ 释放（GUI 线程）」跨线程使用。OpenCV 自带的 FFmpeg 封装（`opencv_videoio_ffmpeg*.dll`）不是线程安全的，跨线程 `release()` 时直接 `abort()`——Windows 事件日志：异常代码 `0x40000015`（`STATUS_FATAL_APP_EXIT`），故障模块正是该 dll；表现就是「视频保存完成之后程序自己没了 / 再打开打不开」
- 现改为写入器由录制线程全权持有（创建 / 写帧 / 释放全部同线程），创建失败经新增 `recording_error` 信号回主线程弹窗（不再从工作线程碰 `QMessageBox`）
- 录制循环不再读取 `width_spin` / `follow_*_spin` 等 QWidget，改用启动录制时快照的普通属性（`_cap_mode` / `_cap_width` / `_cap_height`），消除工作线程访问控件的隐患
- 新增全局异常兜底 `_install_exception_guard()`：接管 `sys.excepthook`，槽函数里的未捕获异常改为「写 `SuperHiVision_error.log` + 弹窗」并让程序继续存活。此前 PyQt5 把未捕获异常交给 `qFatal()` → `abort()`，同样表现为进程瞬间消失。日志先探测可写性（探测文件用完即删，不留残留），程序目录不可写时退回 `%LOCALAPPDATA%\SuperHiVision\`
- 保存阶段（帧率校正 / 音视频合并）改在后台线程执行、主线程以模态进度对话框驱动事件循环：FFmpeg 收尾期间窗口不再「无响应」，也避免被用户当成卡死；保存异常就地捕获并提示
- 保存期间禁用录制按钮并阻止重入（`_saving` 标志）

## Version 1.5.19 (2026-10-05)

安装版补全全部依赖文件，并修复打包版「启动即崩溃」与依赖探测误判：

### 安装包（`installer.nsi`）
- 补入源码回退所需文件：`Super_Hi_Vision_PyQt.py`、`Super_Hi_Vision.py`、`run.bat`、`requirements.txt`（此前只有启动器脚本，源码模式必然失败）
- 随包附带 `ffmpeg\FFMPEG_NOTICE.txt` 与 `ffmpeg\LICENSE_GPLv3.txt`：内置 FFmpeg 为 `--enable-gpl --enable-version3` 静态构建，分发需附许可全文
- 卸载补删 `icon.ico`（此前卸载后安装目录残留），`EstimatedSize` 由 120MB 修正为 540MB

### 修复：打包版「双击闪退 / 从控制台启动即退出」
- 根因：启动阶段打印 `✅ 全局热键注册成功: ...` / `❌ 全局热键注册失败: ...` 时，无控制台 EXE 的 `sys.stdout` 为 `None`（`AttributeError`），中文 Windows 下从控制台/管道启动则是 GBK(cp936)（`UnicodeEncodeError`），二者都会把程序崩在初始化阶段
- 新增 `_ensure_safe_stdout()`：启动最早阶段把 stdout/stderr 就地改为 UTF-8 + `errors="replace"`，缺失时指向 `os.devnull`，保证任何 `print` 都不再抛异常
- `check_environment.py` 加入同样的兜底（否则「环境检测」在 GBK 控制台下同样会崩）

### 修复：依赖探测误判（`_probe_ffmpeg`）
- 原先只认 `ffmpeg -version` 横幅里的 `"ffmpeg version"`，导致 `ffprobe`/`ffplay` 即使文件就在 `ffmpeg\` 目录内也被判为「不可用」（`_find_ffmpeg('ffprobe')` 返回 `None`）
- 现按 `ffmpeg` / `ffprobe` / `ffplay` 三种版本横幅 + 文件名前缀分别判定

## Version 1.5.18 (2026-10-05)

### Bug Fixes

- **修复打包版 EXE「视频合成失败 / 输出视频无法播放」问题**（`Super_Hi_Vision_PyQt.py`）
  - 根因1：单文件 EXE 下 `__file__` 指向 PyInstaller 临时解包目录，原 `_find_ffmpeg()` 只在该目录同级找 ffmpeg，随程序分发的 `ffmpeg\ffmpeg.exe` 永远找不到，音视频合并被直接跳过（录出来没声音、看起来像"合成失败"）
    - 现按优先级枚举解包目录、可执行文件所在目录（安装目录，含 `_internal`）、源码目录、当前工作目录、常见安装路径与系统 PATH，并对每个候选做一次 `-version` 可执行性校验
  - 根因2：MKV 使用 `X264` fourcc，当前 OpenCV 没有对应编码器时**静默失败**——不报错也不写数据，最终留下 0 字节、无法播放的文件
    - 改为按容器逐个候选编码尝试并校验 `isOpened()`（MKV 回退 `mp4v`），全部失败则明确弹窗报错，不再谎报"录制完成"
  - 根因3：合成命令使用 `-shortest` 且未补静音，音频比画面短时会把视频截短
    - 增加 `apad` 补静音：整段画面都有声音，同时不会截断画面
- 其他加固
  - 录制前自动创建输出目录；宽高取偶数（yuv420 系列编码器要求）
  - 停止录制时先等待录制线程退出再 `release()`，避免写坏 MP4 的 moov 索引导致文件无法播放
  - 音视频合并改为多策略重试：视频流复制失败回退 `libx264` 重编码；`loudnorm` 失败回退无滤镜合并
  - MP4/MOV 输出统一加 `-movflags +faststart`（索引前置），播放器/网页不再打开即报错
  - 时间戳缩放系数限幅 0.05~20，避免帧率统计异常时视频时长失控
  - 录制结束后校验输出文件（不存在或 0 字节 → 明确提示失败，不再提示成功）
- `check_environment.py` 同步修复 ffmpeg 查找逻辑（同样枚举可执行文件目录与解包目录）
- **修复打包版「双击闪退 / 从控制台启动即退出」问题**（`Super_Hi_Vision_PyQt.py`）
  - 根因：启动阶段打印 `✅ 全局热键注册成功: ...` / `❌ 全局热键注册失败: ...` 时，打包版 `sys.stdout` 要么是 `None`（无控制台 EXE），要么是中文 Windows 的 GBK(cp936) 编码，emoji 字符直接抛 `UnicodeEncodeError` / `AttributeError`，把整个程序崩在初始化阶段
  - 新增 `_ensure_safe_stdout()`：启动最早阶段把 stdout/stderr 就地改为 UTF-8 + `errors="replace"`，缺失时指向 `os.devnull`，保证任何 `print` 不再抛异常
  - `check_environment.py` 加入同样的兜底（否则「环境检测」在 GBK 控制台下同样会崩）
- **修复依赖探测误判**（`Super_Hi_Vision_PyQt.py` 的 `_probe_ffmpeg`）：原先只认 `ffmpeg -version` 横幅里的 `"ffmpeg version"`，导致 `ffprobe`/`ffplay` 即使文件就在 `ffmpeg\` 目录里也被判为「不可用」（`_find_ffmpeg('ffprobe')` 返回 `None`）。现按 `ffmpeg/ffprobe/ffplay` 三种横幅 + 文件名前缀分别判定
- **安装包补全依赖文件**（`installer.nsi`）
  - 补入源码模式所需的 `Super_Hi_Vision_PyQt.py`、`Super_Hi_Vision.py`、`run.bat`、`requirements.txt`（此前启动器脚本 `.pyw` / `check_environment.py` 已随包但源码缺失，回退源码运行必失败）
  - 随包附上 FFmpeg 版本说明与 GPLv3 许可全文（`FFMPEG_NOTICE.txt`、`LICENSE_GPLv3.txt`）：内置 FFmpeg 为 `--enable-gpl --enable-version3` 静态构建，分发需附许可
  - `EstimatedSize` 由 120MB 修正为 540MB（实际安装体积）

---

## Version 1.5.17 (2026-08-26)

### Bug Fixes

- **修复录音音量过低、合成视频听不见声音问题**（`Super_Hi_Vision_PyQt.py` 与 `Super_Hi_Vision.py`）
  - 根因：录制的 PCM 音频未做任何音量处理，麦克风输入电平较低时，测试播放音量低、合成进视频后接近静音（实测 -44dB 几乎听不见）
  - 新增 `_boost_audio_gain()` 自动增益：根据整段音频峰值计算统一增益（默认目标峰值 0.5、最大 8 倍），带削波保护，静音/正常音量不处理
  - 「测试」按钮录音保存前应用自动增益，测试播放音量恢复正常
  - 音视频合成前对全部音频帧应用自动增益，并用 FFmpeg `loudnorm` 响度归一化（目标 -16 LUFS，符合主流视频平台标准），将过低音量拉回标准响度
  - 移除过时的 FFmpeg `-async` 选项（新版已弃用）
  - 实测效果：低音量输入（max -44dB）合成后达到 max -11.7dB / mean -15.3dB，恢复正常可听音量

---

## Version 1.5.16 (2026-08-26)

### New Features

- **新增自定义应用图标**（AI 辅助设计，`icon.ico`）
  - 新增 `icon.ico`：蓝紫渐变圆角方块 + 白色摄像机 + 红色录制点，代表「高清录屏」
  - 打包后的 EXE 不再使用 PyInstaller 默认的「保存/软盘」图标，改用自定义图标
  - 主程序窗口标题栏 / 任务栏也显示新图标（打包版从 `_MEIPASS` 加载，源码版从脚本目录加载）
  - NSIS 安装包与卸载程序同样使用新图标
  - 新增 `generate_icon.py` 图标生成脚本，可随时重新生成/调整图标

---

## Version 1.5.15 (2026-08-26)

### New Features

- **新增「二次元」主题**（`Super_Hi_Vision_PyQt.py`）
  - 主题下拉框新增 `Anime` 选项，切换后自动从 [dmoe.cc](https://www.dmoe.cc/random.php) 随机获取二次元图片作为窗口背景
  - 后台线程异步下载（不阻塞界面），带本地缓存（`%TEMP%/super_hi_vision_anime_bg.jpg`），切换主题立即显示上次缓存、后台刷新新图
  - 半透明深色面板（rgba）+ 背景遮罩，保证控件可读性；无网络时自动回退为纯色深色主题
  - 背景图居中裁剪缩放填充窗口，适配不同分辨率

---

## Version 1.5.14 (2026-08-26)

### Bug Fixes

- **修复热键无法正常使用问题**（`Super_Hi_Vision_PyQt.py` 为主，`Super_Hi_Vision.py` 同步修复）
  - 根因：`Super_Hi_Vision_PyQt.py`（打包入口版本）的 `update_global_hotkeys()` 是空函数，全局热键监听从未启动 → 打包版 F9/F10/F11/F12 全部无效
  - PyQt 版本：实现完整全局热键监听（pynput 后台线程 + `pyqtSignal` 跨线程回到主线程，线程安全）
    - 支持自定义热键及修饰键组合（`F9`、`Ctrl+F9`、`Ctrl+Shift+F9` 等），修改/重置热键后立即生效
    - 增加防抖，避免按住热键重复触发；程序退出时自动停止监听器
  - Tkinter 版本：`setup_hotkeys()` 支持读取 UI 中自定义热键（开始/暂停、停止、截图），不再写死 F9/F10/F11
    - 修复 Esc 退出画图失效的 bug（原先被 `hasattr(key,'char')` 分支吞掉，永不执行）
    - 「应用热键设置」立即重启监听器生效，不再需要重启程序
    - 热键回调统一通过 `root.after` 调度到主线程，避免跨线程操作 Tk 控件
  - F12 画图热键：PyQt 版本新增画图工具面板（工具/颜色/粗细/清除叠加绘制），与 Tkinter 版本功能对齐
  - PyInstaller spec 增加 `pynput` 到 hiddenimports，确保打包后热键依赖可用

---

## Version 1.5.13 (2026-08-25)

### Bug Fixes

- **修复录屏与合成视频没有声音问题**（`Super_Hi_Vision_PyQt.py` 为主，`Super_Hi_Vision.py` 同步修复）
  - 根因 1：`Super_Hi_Vision_PyQt.py` 的 `merge_audio_video()` 是空函数，音频帧虽被录制但从不合成进视频 → 最终视频永远无声；已实现完整音视频合并（FFmpeg `-c:v copy` 不重编码视频，音频转 AAC，保证音视频同步）
  - 根因 2：`AudioRecorderThread` 默认以双声道打开音频流，单声道麦克风会打开失败 → 录屏时无声；已改为自动适配设备声道数与采样率（`min(maxInputChannels, 2)` + 设备默认采样率）
  - 根因 3：音频设备默认选中第一个枚举设备（常为虚拟/静音设备），现改为默认选中系统默认输入设备（麦克风）
  - 停止录制时先等待音频线程结束再合并，避免丢失尾部音频帧
  - 「测试」按钮实现真实录音 3 秒并自动播放，便于验证麦克风

---

## Version 1.5.12 (2026-08-24)

### Bug Fixes

- **修复合成视频快速播放（快放）问题**（`Super_Hi_Vision.py` 与 `Super_Hi_Vision_PyQt.py`）
  - 根因：`VideoWriter` 以目标 FPS（如 30）初始化，但实际捕获帧率往往低于目标值（屏幕抓取耗时、低性能模式跳帧等），导致视频帧数不足、播放时长被压缩（快放），且与实时音频不同步
  - 新增 `fix_video_playback_speed()`：根据「实际帧数 / 有效录制时长」计算真实帧率，用 FFmpeg 调整视频时间戳使播放时长与真实录制时长一致
    - 优先 `-itsscale` 时间戳缩放 + 流复制（无损、不重新编码）
    - 失败自动回退为输入端 `-r` 重新编码校正
  - 录制循环累计有效录制时长（暂停期间不计入），并优化帧率控制休眠（完整补偿），使捕获节奏更贴近目标帧率
  - 帧率校正先于音视频合并执行，保证合并后音视频同步

---

## Version 1.5.11 (2026-08-23)

### 应用模式改造（无需 cmd / PowerShell）

- **新增 `SuperHiVision_Launcher.vbs`**：无控制台启动器，双击即启动应用
  - 自动优先选择已打包的 `SuperHiVision_v1.5.10.exe`
  - 其次使用 `pythonw.exe` 无控制台运行 PyQt 源码
  - 最后回退到 `Super_Hi_Vision_App.pyw` 或 `python.exe`
- **新增 `Super_Hi_Vision_App.pyw`**：pythonw 应用模式启动器（不依赖 VBS）
- **新增 `Create_Desktop_Shortcut.vbs`**：一键创建桌面快捷方式（双击图标启动）
- **改造 `run.bat`**：不再驻留控制台，改为调用 VBS 启动器后自动退出
- **主程序 GUI 化错误处理**：依赖缺失时以 Windows 消息框提示，不再依赖控制台 `input()`
- **`check_environment.py` 应用模式化**：
  - 优先检测并启动已打包的 EXE
  - 优先使用 `pythonw.exe` 无控制台运行源码
  - 自动识别程序自带 `ffmpeg/` 目录（安装包已合成依赖，无需配置 PATH）
- **更新 `installer.nsi`**：安装包合成全部依赖
  - 主程序 EXE（已含全部 Python 依赖）
  - FFmpeg（ffmpeg/ffplay/ffprobe）
  - 全部启动器脚本（VBS / pyw）
  - 桌面及开始菜单快捷方式均指向无控制台启动器

---

## Version 1.5.10 (2026-05-28)

### New Features
- **Multi-theme System**: Added 6 beautiful themes with free switching
  - Dark Theme
  - Light Theme
  - Ocean Theme
  - Sunset Theme
  - Forest Theme
  - Purple Theme
- **Theme Switch Control**: Added theme dropdown in title bar for one-click theme switching
- **Dynamic Style Update**: Interface colors automatically update when switching themes

### Improvements
- Modern UI design with theme support
- Optimized interface layout and visual effects
- All recording logic remains intact

### Preserved
- All recording logic remains intact
- Video recording, audio recording, screenshot and other functions work normally
- Hotkey settings, output directory settings and other features unchanged

---

## Version 1.5.9 (2026-05-28)

### New Features
- **Language Selection**: Added Chinese/English language switching support
- Language dropdown in title bar for one-click language switching
- All UI elements support dynamic language switching

### Bug Fixes
- Fixed advanced settings page text display issues
- Fixed button px value causing display abnormalities
- Fixed audio support not available warning message
- Improved QGroupBox styling for better text visibility
- Replaced emojis with text to avoid display issues

### UI Improvements
- Changed all Chinese text to English for better compatibility
- Updated all tab group titles to English
- Fixed spinbox suffix "px" display issues
- Improved button styling consistency
- Reduced button sizes for better layout fitting

### Audio Support
- Added clearer warning message when PyAudio is not installed
- Audio status now shows helpful message about installation

### Version Update
- Updated version number from 1.5.8 to 1.5.9
- Updated changelog and version information

---

## Version 1.5.8 (2025-01-XX)

### New Features
- **Multi-theme System**: Added 6 beautiful themes with free switching
  - Dark Theme
  - Light Theme
  - Ocean Theme
  - Sunset Theme
  - Forest Theme
  - Purple Theme
- **Theme Switch Control**: Added theme dropdown in title bar for one-click theme switching
- **Dynamic Style Update**: Interface colors automatically update when switching themes

### Improvements
- Modern UI design
- Optimized interface layout and visual effects
- Fixed some known issues

### Preserved
- All recording logic remains intact
- Video recording, audio recording, screenshot and other functions work normally
- Hotkey settings, output directory settings and other features unchanged

---

## Version 1.5.7
- Fixed version number display issue
- Output directory can be customized

## Version 1.5.6
- Initial PyQt5 modern version released

---

## About Super Hi Vision

Super Hi Vision is a professional HD screen recording tool featuring:
- Multiple recording modes (fullscreen, custom area, follow mouse)
- Multiple video formats and encoders
- Synchronized audio recording
- Flexible quality settings
- Modern interface design
- Multi-language support (Chinese/English)

**Copyright**: Copyright 2019-2025 QLM Network Entertainment Technology Co., Ltd.
**Website**: https://team.qlm.org.cn
**Version**: 1.5.25
