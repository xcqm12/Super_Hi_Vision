# Super Hi Vision Changelog

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
**Version**: 1.5.10