# Super Hi Vision

高级超高清屏幕录制工具 - 基于 PyQt5 构建的现代化界面屏幕录制软件

## 📋 功能特点

- **多种录制模式**
  - 全屏录制：录制整个屏幕
  - 自定义区域：指定录制区域大小
  - 跟随鼠标：录制鼠标周围区域

- **视频格式支持**
  - MP4、AVI、MKV 等多种格式
  - 多种编码器选择（H.264、VP9、MPEG-4 等）
  - 可调节帧率（15-120 FPS）

- **音频录制**
  - 支持麦克风音频录制
  - 自动检测音频设备
  - 音频状态实时显示

- **质量设置**
  - 5档质量预设（低功耗/标准/高清/超清/蓝光）
  - 4档性能模式（低功耗/平衡/高性能/极致）

- **热键支持**
  - F9：开始/暂停录制
  - F10：停止录制
  - F11：截图
  - F12：显示/隐藏画图工具

- **多语言支持**
  - 中文 / English 语言切换

- **多主题支持**
  - 6种精美主题（深色/浅色/海洋/日落/森林/紫色）

## 🩹 最新更新（v1.5.18）

修复打包版 EXE「视频合成失败 / 合成后的视频无法播放」问题：

- **打包后找不到 FFmpeg**：单文件 EXE 运行时 `__file__` 指向临时解包目录，程序现在按「EXE 所在目录 → 解包目录 → 源码目录 → 常见安装路径 → 系统 PATH」逐级查找并校验 ffmpeg，不再静默跳过音视频合并（此前表现为"录出来没声音 / 合成失败"）
- **MKV 录出 0 字节文件**：`X264` 编码器在当前 OpenCV 中缺失时会静默失败，现按容器逐个候选编码校验（MKV 回退 `mp4v`），全部失败则明确弹窗报错，不再谎报"录制完成"
- **音频比画面短会把视频截短**：合成命令增加 `apad` 补静音，整段画面都有声音，且画面不再被截断
- 其余加固：停止录制先等录制线程退出再释放写入器（避免文件损坏无法播放）、音视频合并多策略重试（流复制 → 重编码 / 响度归一化回退）、MP4/MOV 加 `-movflags +faststart`、录制结束后校验输出文件（0 字节即报失败）

> ⚠️ 直接运行的 EXE 需与 `ffmpeg\` 文件夹**放在同一目录**（安装包会自动布置到 `安装目录\ffmpeg\`）。安装版另含源码回退文件（`Super_Hi_Vision_PyQt.py`、`run.bat`、`requirements.txt`）与 FFmpeg 许可文本（`ffmpeg\FFMPEG_NOTICE.txt`、`ffmpeg\LICENSE_GPLv3.txt`），无需另行下载依赖。

---

## 🚀 快速开始

### 系统要求

- Windows 10/11 (64位)
- Python 3.8+（源码运行）

### 运行方式（应用模式，无需 cmd / PowerShell）

本项目已改造为 **应用模式** 运行：双击图标即启动 GUI 应用，**不显示任何控制台窗口**，无需通过 cmd 或 PowerShell 手动执行命令。

#### 方式一：双击 EXE（推荐，已打包全部依赖）

```bash
# 直接双击运行（无控制台窗口）
SuperHiVision_v1.5.18.exe
```

#### 方式二：双击 VBS 启动器（自动选择 EXE / Python 源码）

```bash
# 直接双击运行（无控制台窗口）
SuperHiVision_Launcher.vbs
```

启动器自动按以下优先级选择运行方式：

1. 若同目录存在已打包的 `SuperHiVision_v1.5.18.exe` → 直接启动 EXE
2. 否则使用 `pythonw.exe`（无控制台）运行 `Super_Hi_Vision_PyQt.py` 源码
3. 否则运行 `Super_Hi_Vision_App.pyw`（pythonw 启动器）
4. 最后回退到 `python.exe` 运行源码

#### 方式三：双击 .pyw 启动器（不依赖 VBS）

若系统禁用了 Windows 脚本宿主（VBS），可改用此文件，双击自动以 `pythonw.exe` 无控制台运行：

```bash
# 直接双击运行（无控制台窗口）
Super_Hi_Vision_App.pyw
```

#### 方式四：创建桌面快捷方式（双击图标启动）

```bash
# 双击运行，在桌面创建 "Super Hi Vision" 快捷方式
Create_Desktop_Shortcut.vbs
```

#### 方式五：运行批处理（兼容旧入口，控制台自动关闭）

```bash
# 双击运行，控制台窗口一闪即关，不驻留
run.bat
```

### 使用 Python 运行源码（开发模式）

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
pythonw Super_Hi_Vision_PyQt.py
```

> 使用 `pythonw`（而非 `python`）运行不会弹出控制台窗口，依赖错误会以 GUI 消息框提示。

## 📖 使用说明

### 1. 选择录制区域

在「基本设置」标签页中选择录制模式：

- **全屏录制**：录制整个显示器屏幕
- **自定义区域**：输入宽度和高度，或点击「选择」按钮手动选择区域
- **跟随鼠标**：录制鼠标周围的指定区域

### 2. 设置输出路径

在「基本设置」标签页中：

- 输入文件名（支持自动时间戳）
- 点击「浏览」选择输出目录
- 使用快捷按钮快速选择常用目录（桌面/文档/视频/图片）

### 3. 配置高级选项

在「高级设置」标签页中：

- **视频格式**：选择输出格式（MP4/AVI/MKV）
- **编码器**：选择视频编码器
- **帧率**：设置录制帧率
- **质量**：选择录制质量级别
- **性能**：选择性能模式

### 4. 音频设置

在「音频设置」标签页中：

- 勾选「启用音频录制」
- 选择音频输入设备
- 点击「测试」测试音频输入

### 5. 开始录制

点击底部「开始」按钮或按 F9 键开始录制：

- 录制过程中可以按 F9 暂停/继续
- 按 F10 停止录制
- 按 F11 截取当前画面
- 按 F12 打开画图工具

## ⌨️ 快捷键列表

| 快捷键 | 功能 |
|--------|------|
| F9 | 开始/暂停录制 |
| F10 | 停止录制 |
| F11 | 截图 |
| F12 | 显示/隐藏画图工具 |

### 画图工具快捷键

| 操作 | 功能 |
|------|------|
| 鼠标左键 | 开始绘制 |
| 鼠标移动 | 继续绘制 |
| 鼠标释放 | 停止绘制 |
| C | 清除所有绘制 |
| ESC | 退出画图模式 |

## 📁 项目结构

```
Super_Hi_Vision/
├── Super_Hi_Vision_PyQt.py        # 主程序文件（PyQt5）
├── Super_Hi_Vision_App.pyw        # 应用模式启动器（pythonw，无控制台）
├── SuperHiVision_Launcher.vbs     # 应用模式启动器（VBS，无控制台）
├── Create_Desktop_Shortcut.vbs    # 创建桌面快捷方式脚本
├── check_environment.py           # 环境检测脚本（应用模式）
├── run.bat                        # 兼容入口（调用启动器，控制台自动关闭）
├── requirements.txt               # 依赖列表
├── CHANGELOG.md                   # 更新日志
├── LICENSE.txt                    # 许可证
├── README.md                      # 使用说明（本文件）
├── installer.nsi                  # NSIS 安装脚本（已合成全部依赖）
├── SuperHiVision.spec             # PyInstaller 配置
├── ffmpeg/                        # 自带 FFmpeg 依赖
│   ├── ffmpeg.exe
│   ├── ffplay.exe
│   └── ffprobe.exe
└── SuperHiVision_v1.5.18.exe      # 打包后的可执行文件
```

## 🛠️ 技术栈

- **框架**: PyQt5
- **视频处理**: OpenCV
- **音频处理**: PyAudio
- **截图**: PyAutoGUI
- **打包**: PyInstaller

## 📝 更新日志

查看 [CHANGELOG.md](CHANGELOG.md) 获取详细更新记录。

## 📄 许可证

MIT License - 详见 [LICENSE.txt](LICENSE.txt)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**版权**: QLM Network Entertainment Technology Co., Ltd.
**网站**: https://team.qlm.org.cn
**版本**: 1.5.18