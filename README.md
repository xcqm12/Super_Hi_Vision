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
  - **音频降噪强度滑杆 0-100%**（highpass + afftdn 参数随滑杆变化，保存时处理）+ 响度归一化（loudnorm）

- **后台运行（托盘保活）**
  - 关闭窗口最小化到系统托盘，程序继续在后台运行，录制不中断
  - 再次点击桌面图标/EXE 会唤出已有窗口（单实例，不会开出第二份）
  - 保存过程静默进行，只在窗口内显示进度，不弹对话框

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

## 🩹 最新更新（v1.5.22）

**音频降噪强度改成可调滑杆（0-100%）**：

- **🎚️ 降噪强度滑杆**：音频设置页原来的「降噪开关」换成滑杆。最左 0 = 关闭降噪；往右按 `轻度(≤33%) / 中度(≤66%) / 强力(>66%)` 显示，默认 **40%**（手感等价于 v1.5.21 的固定参数）
- **滑杆值实时生效并持久化**：写入 `~/.super_hi_vision_settings.json` 的 `denoise_strength`，保存视频时直接反映到 FFmpeg 降噪链：`highpass=f=80` → `afftdn=nr=6~24:nf=-40~-20` → `loudnorm=I=-16:TP=-1.5:LRA=11` → `apad`
- **参数含义**：`nr` = 降噪量（6 → 24），`nf` = 噪声底（-40 → -20 dB，越接近 -20 压得越狠）。实测粉噪声样本，强度 20/40/60/80/100 的输出底噪为 **-43.1 / -46.2 / -51.0 / -57.4 / -62.3 dB**（原始 -36.2 dB），单调递增地压得更干净
- **兼容旧设置**：老版本写的 `{"denoise": true/false}` 读入后自动折算为 40% / 关闭，不会因为升级丢配置

<details><summary>v1.5.21 版新增</summary>

**新增音频降噪 + 后台保活（关闭窗口进托盘）+ 再次点击图标能唤出窗口 + 保存静默不弹窗**：

- **🎙️ 音频降噪**：音频设置页新增降噪（默认开启）。降噪在保存阶段由 FFmpeg 统一处理，**不增加录制时的 CPU 负担**：`highpass=f=80`（滤低频轰隆/电流声）→ `afftdn=nr=12:nf=-30`（FFT 自适应降噪）→ `loudnorm`（响度归一化）→ `apad`。合并命令带三级降级（降噪+归一化 → 仅归一化 → 不处理），某个滤波器不可用也不会变成「有画面没声音」
- **🖥️ 后台保活**：新增系统托盘。关闭窗口默认**最小化到托盘、程序继续在后台跑**——录制不中断、F9/F10/F11/F12 全局热键照常可用；托盘菜单有「显示主窗口 / 开始·暂停 / 停止录制 / 退出」。想恢复旧行为可在高级设置里关掉该开关
- **👆 再次点击图标能唤出窗口**：新增单实例机制（本机命名管道）。程序已在运行（哪怕藏在托盘里）时，再点桌面图标/EXE 会让**已有实例把窗口弹回前台**，第二个进程立即退出——不再出现「明明后台在跑，点图标却打不开」
- **🔇 静默合成视频，不弹窗**：保存不再弹模态进度框，改为窗口内进度条 + 状态栏文字；保存成功也不再弹「Recording Complete」，只在状态栏显示 `✅ 已保存 <文件名>`（窗口在托盘时仅更新托盘提示）。**只有失败才弹窗**，避免静默丢文件
- **🧯 修复「保存完成后应用崩溃/打不开」**：根因是 `cv2.VideoWriter` 跨线程使用触发 OpenCV 内置 FFmpeg 封装 `abort()`（事件日志异常代码 `0x40000015`，故障模块 `opencv_videoio_ffmpeg*.dll`）。写入器改为录制线程全权持有；新增全局异常兜底（未捕获异常写 `SuperHiVision_error.log` + 弹窗，程序继续存活）
- **🧹 安装/卸载更干净**：异常日志「按需创建」（探测不留空文件），装到 `Program Files` 时退回 `%LOCALAPPDATA%\SuperHiVision\`；卸载补删日志、`resources\`/`ffmpeg\` 用 `RMDir /r` 删净、主程序 `Delete /REBOOTOK`

</details>

<details><summary>v1.5.20 及更早</summary>

修复「视频保存完成之后应用崩溃 / 打不开」：

- **根因**：`cv2.VideoWriter` 此前是「GUI 线程创建 → 录制线程写帧 → GUI 线程释放」，跨线程使用。OpenCV 自带的 FFmpeg 封装不是线程安全的，跨线程 `release()` 时会让进程直接 `abort()`（Windows 事件日志：异常代码 `0x40000015`，故障模块 `opencv_videoio_ffmpeg*.dll`），表现就是**保存完成的那一刻程序自己消失、再点图标打不开**
- **修复**：写入器改为由录制线程全权持有（创建 / 写帧 / 释放同线程）；创建失败经新增信号回主线程弹窗；录制循环改用启动时的参数快照，不再从工作线程读取控件
- **新增全局异常兜底**：未捕获异常不再触发 `qFatal()` → `abort()`，改为写 `SuperHiVision_error.log` 并弹窗提示，程序继续可用
- **保存过程不再「无响应」**：帧率校正 / 音视频合并改到后台线程，主线程用进度对话框驱动事件循环；保存期间禁用录制按钮，防止重复触发
- **安装/卸载更干净**：异常日志改为「按需创建」（可写性探测不留空文件），卸载脚本补删 `SuperHiVision_error.log`、`resources\` 目录用 `RMDir /r` 删净、主程序 `Delete /REBOOTOK`（正在运行时卸载不再留残骸）

<details><summary>v1.5.19 及更早</summary>

补齐安装版依赖并修复「打包版启动即崩溃」问题：

- **打包版双击闪退 / 从控制台启动即退出**：启动阶段的日志打印遇到无控制台 EXE（`sys.stdout` 为 `None`）或中文 Windows 的 GBK 控制台时会抛 `UnicodeEncodeError` / `AttributeError`，直接把程序崩在初始化。现启动最早阶段统一把 stdout/stderr 改为 UTF-8 + `errors="replace"`（缺失时指向 `os.devnull`），`print` 不再可能抛异常
- **依赖探测误判**：`_probe_ffmpeg` 原先只认 `ffmpeg -version` 的横幅，导致 `ffprobe` / `ffplay` 即使就在 `ffmpeg\` 目录里也被判为不可用，现已按三种版本横幅分别判定
- **安装包补全所有依赖文件**：加入源码回退文件（`Super_Hi_Vision_PyQt.py`、`Super_Hi_Vision.py`、`run.bat`、`requirements.txt`）与 FFmpeg 许可文本（`ffmpeg\FFMPEG_NOTICE.txt`、`ffmpeg\LICENSE_GPLv3.txt`）；内置 FFmpeg 是 `--enable-gpl --enable-version3` 静态构建，分发需附 GPLv3 全文
- **卸载残留修复**：卸载脚本补删 `icon.ico`，卸载后安装目录不再残留；`EstimatedSize` 由 120MB 修正为 540MB
- （1.5.18 的「视频合成失败 / 合成后无法播放」修复说明见 `CHANGELOG.md`）

</details>

</details>

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
SuperHiVision_v1.5.22.exe
```

#### 方式二：双击 VBS 启动器（自动选择 EXE / Python 源码）

```bash
# 直接双击运行（无控制台窗口）
SuperHiVision_Launcher.vbs
```

启动器自动按以下优先级选择运行方式：

1. 若同目录存在已打包的 `SuperHiVision_v1.5.22.exe` → 直接启动 EXE
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
└── SuperHiVision_v1.5.22.exe      # 打包后的可执行文件
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
**版本**: 1.5.22