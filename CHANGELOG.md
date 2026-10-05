# Super Hi Vision Changelog

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
**Version**: 1.5.18