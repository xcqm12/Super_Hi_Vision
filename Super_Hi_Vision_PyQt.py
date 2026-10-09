#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Hi Vision - 高级超高清屏幕录制工具 (PyQt5现代化版本)
版本: 1.5.27
使用PyQt5构建现代化界面，保持原有录制逻辑不变
支持中英文语言切换
支持多主题切换
自动检测和安装 PyQt5 依赖
"""

import sys
import os
import tempfile
import threading
import time
import datetime
import shutil
import json
import ssl
import wave
import struct
import math
from datetime import datetime
from pathlib import Path

# ==================== 控制台编码兜底（打包版 / 中文 Windows 必装） ====================
def _ensure_safe_stdout():
    """让 print 在任何环境下都不会把程序打崩。

    打包出的无控制台 EXE 里 sys.stdout 可能是 None；从控制台/管道启动时它又常是
    GBK(cp936) 编码，打印 ✅❌⚠️ 这类字符会抛 UnicodeEncodeError。两种情况都发生在
    启动阶段（例如全局热键注册成功/失败时的那一句 print），会直接把整个程序崩掉，
    表现为"双击闪退 / 刚打开就没了"。这里统一改成 UTF-8 + errors=replace，
    stdout 缺失时换成黑洞对象，保证 print 永不抛异常。
    """
    import io

    sink = None
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            if sink is None:
                sink = open(os.devnull, "w", encoding="utf-8", errors="replace")
            setattr(sys, name, sink)
            continue
        try:  # 首选：就地改编码（Python 3.7+）
            stream.reconfigure(encoding="utf-8", errors="replace")
            continue
        except Exception:
            pass
        try:  # 退路：用同一底层缓冲重新包一层 UTF-8
            buffer = getattr(stream, "buffer", None)
            if buffer is not None:
                setattr(sys, name, io.TextIOWrapper(buffer, encoding="utf-8",
                                                    errors="replace", line_buffering=True))
        except Exception:
            pass


try:
    _ensure_safe_stdout()
except Exception:
    pass


def _app_dir():
    """程序所在目录（打包版取 EXE 所在目录：_MEIPASS 是临时解包目录，不能用来写日志）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _dir_writable(d):
    """探测目录可写性且不留残留（不能靠建一个空日志文件来试——那样每次启动都会留下空文件）"""
    probe = os.path.join(d, f".shv_write_test_{os.getpid()}")
    try:
        with open(probe, "w", encoding="utf-8"):
            pass
        try:
            os.remove(probe)
        except Exception:
            pass
        return True
    except Exception:
        return False


ERROR_LOG_PATH = None


def _resolve_error_log_path():
    """定位可写的错误日志路径（程序目录不可写时退回 %LOCALAPPDATA%\\SuperHiVision）"""
    log_path = os.path.join(_app_dir(), "SuperHiVision_error.log")
    if not _dir_writable(_app_dir()):
        candidates = []
        try:
            base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
            candidates.append(os.path.join(base, "SuperHiVision"))
            candidates.append(os.path.expanduser("~"))
        except Exception:
            pass
        for d in candidates:
            try:
                os.makedirs(d, exist_ok=True)
                if _dir_writable(d):
                    log_path = os.path.join(d, "SuperHiVision_error.log")
                    break
            except Exception:
                continue
    return log_path


def _log_path():
    global ERROR_LOG_PATH
    if ERROR_LOG_PATH is None:
        ERROR_LOG_PATH = _resolve_error_log_path()
    return ERROR_LOG_PATH


def log_diagnostic(text):
    """把诊断信息（如音视频合并失败的真实原因）追加进错误日志，便于用户回传现场"""
    try:
        with open(_log_path(), "a", encoding="utf-8", errors="replace") as f:
            f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} {text}\n")
    except Exception:
        pass


def _install_exception_guard():
    """把未捕获异常变成「写日志 + 弹窗」，而不是让 PyQt5 直接 abort() 掉整个进程

    PyQt5(>=5.5) 借 sys.excepthook 把槽函数里未捕获的异常交给 qFatal() → abort()，
    进程当场消失，用户看到的就是「应用自己没了 / 保存完视频之后打不开」。
    这里接管 sys.excepthook：异常写进程序目录下的 SuperHiVision_error.log 并弹窗，
    程序继续存活可用（也留下可诊断的现场）。
    """
    log_path = _log_path()

    def _hook(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            sys.stderr.write(text)
        except Exception:
            pass
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as f:
                f.write(f"\n===== {datetime.now():%Y-%m-%d %H:%M:%S} 未捕获异常 =====\n{text}")
        except Exception:
            pass
        try:
            show_error_dialog(
                "程序异常",
                f"{exc_type.__name__}: {exc_value}\n\n详细堆栈已写入：\n{log_path}"
            )
        except Exception:
            pass

    sys.excepthook = _hook
    return log_path


# ==================== GUI 消息框（应用模式，无控制台） ====================
def show_error_dialog(title, message):
    """使用 Windows 原生消息框显示错误（不依赖 PyQt5/tkinter）"""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)  # MB_ICONERROR
    except Exception:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(title, message)
            root.destroy()
        except Exception:
            pass

def show_info_dialog(title, message):
    """使用 Windows 原生消息框显示提示（不依赖 PyQt5/tkinter）"""
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x40)  # MB_ICONINFORMATION
    except Exception:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo(title, message)
            root.destroy()
        except Exception:
            pass

# ==================== 自动检测和安装 PyQt5 ====================
def check_and_install_pyqt5():
    """自动检测并安装 PyQt5"""
    try:
        import PyQt5
        from PyQt5.QtWidgets import QApplication
        print("[OK] PyQt5 已安装")
        return True
    except ImportError:
        print("[WARN] PyQt5 未安装，正在自动安装...")
        try:
            import subprocess
            import sysconfig
            
            pip_exe = sys.executable.replace("python.exe", "Scripts\\pip.exe")
            if not os.path.exists(pip_exe):
                pip_exe = "pip"
            
            result = subprocess.run(
                [pip_exe, "install", "PyQt5"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("[OK] PyQt5 安装成功！")
                return True
            else:
                print(f"[ERROR] PyQt5 安装失败: {result.stderr}")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "PyQt5"],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print("[OK] PyQt5 安装成功！")
                    return True
                else:
                    print(f"[ERROR] 自动安装失败，请手动运行: pip install PyQt5")
                    return False
        except Exception as e:
            print(f"[ERROR] 安装过程出错: {str(e)}")
            print("请手动运行: pip install PyQt5")
            return False

if not check_and_install_pyqt5():
    show_error_dialog(
        "Super Hi Vision - 无法启动",
        "程序无法启动，PyQt5 依赖不可用！\n\n"
        "请确保已安装 Python 和 pip，然后运行：\n"
        "    pip install PyQt5\n\n"
        "或直接使用已打包的 EXE 版本（SuperHiVision_v1.5.27.exe）。"
    )
    sys.exit(1)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QGroupBox, QRadioButton, QCheckBox, QTabWidget,
    QFileDialog, QMessageBox, QProgressBar, QProgressDialog, QFrame, QScrollArea,
    QSplitter, QStatusBar, QSizePolicy, QSlider, QDialog,
    QDialogButtonBox, QTextEdit, QGridLayout, QStyleFactory,
    QSystemTrayIcon, QMenu, QAction, QToolButton
)
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPoint, QRect,
    QObject, QEvent, QCoreApplication, QTranslator, QLibraryInfo
)
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QBrush, QLinearGradient, QPainter,
    QIcon, QPixmap, QCursor, QFontDatabase, QKeySequence
)

import subprocess
import platform
import traceback
import cv2
import numpy as np
import pyaudio
import wave
import shutil
import urllib.request

# ==================== 全局热键（pynput，可选依赖） ====================
# 热键监听在后台线程运行，通过 pyqtSignal 回到主线程，保证线程安全
try:
    from pynput import keyboard as _pynput_keyboard
    PYNPUT_AVAILABLE = True
except Exception:
    _pynput_keyboard = None
    PYNPUT_AVAILABLE = False

# ==================== 版本和版权信息 ====================
__author__ = "QLM Network Entertainment Technology Co., Ltd."
__copyright__ = "Copyright 2019-2025, QLM Network Entertainment Technology Co., Ltd."
__version__ = "1.5.27"
__license__ = "MIT"
__email__ = "qlm@qlm.org.cn"
__website__ = "https://team.qlm.org.cn"
__team__ = "SevenZeroMeowTeam"

# ==================== 应用图标 ====================
def _app_icon_path():
    """定位应用图标：打包版从 _MEIPASS 提取，源码版从脚本目录"""
    if getattr(sys, 'frozen', False):
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'icon.ico')


def _load_app_icon():
    """加载应用图标（文件缺失时返回空图标，不报错）"""
    path = _app_icon_path()
    if os.path.exists(path):
        return QIcon(path)
    return QIcon()

# 全局异常兜底：槽函数里的未捕获异常不再 abort 掉进程，改为写日志 + 弹窗
try:
    _install_exception_guard()
except Exception:
    pass


# ==================== 主题管理器 ====================
class ThemeManager:
    """主题管理器类"""
    def __init__(self):
        self.themes = {
            'dark': {
                'name': 'Dark',
                'primary': '#1a1a2e',
                'secondary': '#16213e',
                'accent': '#e94560',
                'text': '#ffffff',
                'text_light': '#a2a2a2',
                'border': '#3a3a5a',
                'success': '#4ecca3',
                'info': '#3498db',
                'warning': '#f39c12',
                'danger': '#e74c3c',
                'button_hover': '#ff6b6b',
                'button_pressed': '#7fdbda',
                'input_bg': '#0f3460',
                'group_bg': '#16213e'
            },
            'light': {
                'name': 'Light',
                'primary': '#f5f5f5',
                'secondary': '#ffffff',
                'accent': '#3498db',
                'text': '#333333',
                'text_light': '#666666',
                'border': '#dddddd',
                'success': '#27ae60',
                'info': '#3498db',
                'warning': '#f39c12',
                'danger': '#e74c3c',
                'button_hover': '#5dade2',
                'button_pressed': '#85c1e9',
                'input_bg': '#ffffff',
                'group_bg': '#ffffff'
            },
            'ocean': {
                'name': 'Ocean',
                'primary': '#0a1929',
                'secondary': '#132f4c',
                'accent': '#0077b6',
                'text': '#ffffff',
                'text_light': '#90caf9',
                'border': '#1e4976',
                'success': '#00bfa5',
                'info': '#0288d1',
                'warning': '#ffb300',
                'danger': '#f44336',
                'button_hover': '#2196f3',
                'button_pressed': '#64b5f6',
                'input_bg': '#0d2137',
                'group_bg': '#132f4c'
            },
            'sunset': {
                'name': 'Sunset',
                'primary': '#1a1a1a',
                'secondary': '#2d2d2d',
                'accent': '#ff6b35',
                'text': '#ffffff',
                'text_light': '#b0b0b0',
                'border': '#404040',
                'success': '#4caf50',
                'info': '#2196f3',
                'warning': '#ff9800',
                'danger': '#f44336',
                'button_hover': '#ff8a50',
                'button_pressed': '#ffab70',
                'input_bg': '#252525',
                'group_bg': '#2d2d2d'
            },
            'forest': {
                'name': 'Forest',
                'primary': '#1b2d1b',
                'secondary': '#2d4a2d',
                'accent': '#4caf50',
                'text': '#ffffff',
                'text_light': '#a5d6a7',
                'border': '#3d5a3d',
                'success': '#81c784',
                'info': '#66bb6a',
                'warning': '#ffca28',
                'danger': '#ef5350',
                'button_hover': '#66bb6a',
                'button_pressed': '#81c784',
                'input_bg': '#243524',
                'group_bg': '#2d4a2d'
            },
            'purple': {
                'name': 'Purple',
                'primary': '#1a1a2e',
                'secondary': '#2d2d44',
                'accent': '#9c27b0',
                'text': '#ffffff',
                'text_light': '#ce93d8',
                'border': '#4a4a6a',
                'success': '#4caf50',
                'info': '#2196f3',
                'warning': '#ff9800',
                'danger': '#f44336',
                'button_hover': '#ab47bc',
                'button_pressed': '#ba68c8',
                'input_bg': '#252540',
                'group_bg': '#2d2d44'
            },
            'anime': {
                'name': 'Anime',
                # 二次元主题：半透明深色面板 + 随机二次元背景图（https://www.dmoe.cc/random.php）
                # 背景图由主窗口 paintEvent 绘制，面板使用 rgba 半透明让背景透出
                'primary': 'rgba(22, 26, 46, 165)',
                'secondary': 'rgba(30, 34, 60, 140)',
                'accent': '#ff6ec7',
                'text': '#ffffff',
                'text_light': '#d0d0e0',
                'border': 'rgba(255, 110, 199, 130)',
                'success': '#4ecca3',
                'info': '#64b5f6',
                'warning': '#ffb74d',
                'danger': '#ff5252',
                'button_hover': '#ff8ad4',
                'button_pressed': '#ffb0e3',
                'input_bg': 'rgba(40, 44, 75, 190)',
                'group_bg': 'rgba(44, 48, 82, 130)'
            }
        }
        self.current_theme = 'dark'
        self.theme_changed_callback = None

    def get_theme(self, theme_name=None):
        """获取主题配置"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.themes.get(theme_name, self.themes['dark'])

    def set_theme(self, theme_name):
        """设置当前主题"""
        if theme_name in self.themes:
            self.current_theme = theme_name
            if self.theme_changed_callback:
                self.theme_changed_callback(theme_name)
            return True
        return False

    def generate_style_sheet(self, theme_name=None):
        """生成QSS样式表"""
        theme = self.get_theme(theme_name)
        return f"""
            QMainWindow {{ background-color: {theme['primary']}; }}
            QWidget {{ background-color: {theme['primary']}; color: {theme['text']}; }}
            QGroupBox {{ background-color: {theme['group_bg']}; color: {theme['text']}; border: 2px solid {theme['border']}; border-radius: 8px; margin-top: 10px; padding-top: 10px; font-weight: bold; }}
            QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; color: {theme['accent']}; }}
            QPushButton {{ background-color: {theme['accent']}; color: {theme['text']}; border: none; border-radius: 5px; padding: 8px 16px; font-weight: bold; min-width: 80px; }}
            QPushButton:hover {{ background-color: {theme['button_hover']}; }}
            QPushButton:pressed {{ background-color: {theme['button_pressed']}; }}
            QPushButton:disabled {{ background-color: {theme['border']}; color: {theme['text_light']}; }}
            QComboBox {{ background-color: {theme['input_bg']}; color: {theme['text']}; border: 2px solid {theme['border']}; border-radius: 5px; padding: 5px 10px; min-width: 100px; }}
            QComboBox:hover {{ border-color: {theme['accent']}; }}
            QComboBox::drop-down {{ border: none; }}
            QComboBox::down-arrow {{ image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 5px solid {theme['text_light']}; margin-right: 10px; }}
            QComboBox QAbstractItemView {{ background-color: {theme['secondary']}; color: {theme['text']}; selection-background-color: {theme['accent']}; border: 1px solid {theme['border']}; }}
            QLineEdit {{ background-color: {theme['input_bg']}; color: {theme['text']}; border: 2px solid {theme['border']}; border-radius: 5px; padding: 5px 10px; }}
            QLineEdit:hover {{ border-color: {theme['accent']}; }}
            QLineEdit:focus {{ border-color: {theme['accent']}; }}
            QSpinBox {{ background-color: {theme['input_bg']}; color: {theme['text']}; border: 2px solid {theme['border']}; border-radius: 5px; padding: 5px 10px; }}
            QSpinBox:hover {{ border-color: {theme['accent']}; }}
            QSpinBox::up-button, QSpinBox::down-button {{ background-color: {theme['secondary']}; border: none; }}
            QSpinBox::up-arrow, QSpinBox::down-arrow {{ border-left: 5px solid transparent; border-right: 5px solid transparent; }}
            QSpinBox::up-arrow {{ border-bottom: 5px solid {theme['text']}; }}
            QSpinBox::down-arrow {{ border-top: 5px solid {theme['text']}; }}
            QTabWidget::pane {{ border: 2px solid {theme['border']}; border-radius: 5px; background-color: {theme['secondary']}; }}
            QTabBar::tab {{ background-color: {theme['primary']}; color: {theme['text_light']}; padding: 8px 20px; margin-right: 2px; border-top-left-radius: 5px; border-top-right-radius: 5px; }}
            QTabBar::tab:selected {{ background-color: {theme['accent']}; color: {theme['text']}; }}
            QTabBar::tab:hover {{ background-color: {theme['secondary']}; }}
            QCheckBox {{ color: {theme['text']}; spacing: 8px; }}
            QCheckBox::indicator {{ width: 18px; height: 18px; border: 2px solid {theme['border']}; border-radius: 4px; background-color: {theme['input_bg']}; }}
            QCheckBox::indicator:checked {{ background-color: {theme['accent']}; border-color: {theme['accent']}; }}
            QRadioButton {{ color: {theme['text']}; spacing: 8px; }}
            QRadioButton::indicator {{ width: 18px; height: 18px; border: 2px solid {theme['border']}; border-radius: 9px; background-color: {theme['input_bg']}; }}
            QRadioButton::indicator:checked {{ background-color: {theme['accent']}; border-color: {theme['accent']}; }}
            QProgressBar {{ background-color: {theme['input_bg']}; color: {theme['text']}; border: none; border-radius: 5px; text-align: center; }}
            QProgressBar::chunk {{ background-color: {theme['accent']}; border-radius: 5px; }}
            QStatusBar {{ background-color: {theme['secondary']}; color: {theme['text_light']}; border-top: 1px solid {theme['border']}; }}
            QLabel {{ color: {theme['text']}; background-color: transparent; }}
            QScrollBar:vertical {{ background-color: {theme['primary']}; width: 12px; border: none; }}
            QScrollBar::handle:vertical {{ background-color: {theme['border']}; border-radius: 6px; min-height: 20px; }}
            QScrollBar::handle:vertical:hover {{ background-color: {theme['accent']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ border: none; background: none; }}
            QScrollBar:horizontal {{ background-color: {theme['primary']}; height: 12px; border: none; }}
            QScrollBar::handle:horizontal {{ background-color: {theme['border']}; border-radius: 6px; min-width: 20px; }}
            QScrollBar::handle:horizontal:hover {{ background-color: {theme['accent']}; }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ border: none; background: none; }}
            QSlider::groove:horizontal {{ background-color: {theme['border']}; height: 6px; border-radius: 3px; }}
            QSlider::handle:horizontal {{ background-color: {theme['accent']}; width: 16px; margin: -5px 0; border-radius: 8px; }}
            QSlider::handle:horizontal:hover {{ background-color: {theme['button_hover']}; }}
            QTextEdit {{ background-color: {theme['input_bg']}; color: {theme['text']}; border: 2px solid {theme['border']}; border-radius: 5px; }}
            QMenu {{ background-color: {theme['secondary']}; color: {theme['text']}; border: 1px solid {theme['border']}; }}
            QMenu::item:selected {{ background-color: {theme['accent']}; }}
            QMenuBar {{ background-color: {theme['secondary']}; color: {theme['text']}; }}
            QMenuBar::item:selected {{ background-color: {theme['accent']}; }}
            QToolButton {{ background-color: {theme['accent']}; color: {theme['text']}; border: none; border-radius: 5px; padding: 8px; }}
            QToolButton:hover {{ background-color: {theme['button_hover']}; }}
        """

# ==================== 语言管理器 ====================
class LanguageManager:
    """语言管理器类"""
    def __init__(self):
        self.current_language = 'zh'
        self.translations = {
            'zh': {
                'app_title': 'Super Hi Vision - 高级超高清屏幕录制工具',
                'basic_settings': '基本设置',
                'advanced_settings': '高级设置',
                'audio_settings': '音频设置',
                'hotkey_settings': '热键设置',
                'recording_area': '录制区域设置',
                'fullscreen': '全屏录制',
                'custom_area': '自定义区域',
                'follow_mouse': '跟随鼠标',
                'width': '宽度',
                'height': '高度',
                'select_area': '选择区域',
                'output_settings': '输出设置',
                'filename': '文件名',
                'browse': '浏览',
                'output_dir': '输出目录',
                'video_format': '视频格式',
                'encoder': '编码器',
                'fps': '帧率',
                'quality': '质量',
                'performance': '性能模式',
                'audio_recording': '音频录制',
                'enable_audio': '启用音频录制',
                'audio_device': '音频设备',
                'test_audio': '测试',
                'enable_denoise': '音频降噪（去除背景底噪 / 电流声）',
                'check_ffmpeg': '检查 FFmpeg',
                'denoise_strength': '降噪强度：',
                'denoise_off': '关闭（不做降噪）',
                'denoise_light': '轻度',
                'denoise_medium': '中度',
                'denoise_strong': '强力',
                'denoise_hint': '降噪在保存时统一处理（highpass + afftdn），不增加录制时的 CPU 负担；左端关闭，越往右压得越狠（环境噪声大可拉到 70% 以上）',
                'minimize_to_tray': '关闭窗口时最小化到托盘（后台继续运行）',
                'show_window': '显示主窗口',
                'quit_app': '退出',
                'tray_running': 'Super Hi Vision 正在后台运行',
                'tray_tip': 'Super Hi Vision — 后台运行中（双击显示窗口）',
                'saving_video': '正在保存视频…',
                'hotkeys': '热键设置',
                'start_pause': '开始/暂停',
                'stop': '停止',
                'screenshot': '截图',
                'drawing_tool': '画图工具',
                'start_recording': '开始录制',
                'stop_recording': '停止录制',
                'pause_recording': '暂停录制',
                'resume_recording': '恢复录制',
                'ready': '就绪',
                'recording': '录制中',
                'paused': '已暂停',
                'theme': '主题',
                'language': '语言',
                'status': '状态',
                'duration': '时长',
                'file_size': '文件大小',
                'about': '关于',
                'version': '版本',
                'copyright': '版权所有',
                'website': '网站',
            },
            'en': {
                'app_title': 'Super Hi Vision - Advanced HD Screen Recording Tool',
                'basic_settings': 'Basic Settings',
                'advanced_settings': 'Advanced Settings',
                'audio_settings': 'Audio Settings',
                'hotkey_settings': 'Hotkey Settings',
                'recording_area': 'Recording Area',
                'fullscreen': 'Fullscreen',
                'custom_area': 'Custom Area',
                'follow_mouse': 'Follow Mouse',
                'width': 'Width',
                'height': 'Height',
                'select_area': 'Select Area',
                'output_settings': 'Output Settings',
                'filename': 'Filename',
                'browse': 'Browse',
                'output_dir': 'Output Directory',
                'video_format': 'Video Format',
                'encoder': 'Encoder',
                'fps': 'FPS',
                'quality': 'Quality',
                'performance': 'Performance Mode',
                'audio_recording': 'Audio Recording',
                'enable_audio': 'Enable Audio Recording',
                'audio_device': 'Audio Device',
                'test_audio': 'Test',
                'enable_denoise': 'Audio Denoise (remove background hiss / hum)',
                'check_ffmpeg': 'Check FFmpeg',
                'denoise_strength': 'Denoise strength:',
                'denoise_off': 'Off (no denoise)',
                'denoise_light': 'Light',
                'denoise_medium': 'Medium',
                'denoise_strong': 'Strong',
                'denoise_hint': 'Denoise is applied while saving (highpass + afftdn), no extra CPU load while recording; leftmost = off, further right removes more (use 70%+ in noisy rooms)',
                'minimize_to_tray': 'Minimize to tray on close (keep running in background)',
                'show_window': 'Show Window',
                'quit_app': 'Quit',
                'tray_running': 'Super Hi Vision is running in the background',
                'tray_tip': 'Super Hi Vision — running in background (double-click to show)',
                'saving_video': 'Saving video…',
                'hotkeys': 'Hotkey Settings',
                'start_pause': 'Start/Pause',
                'stop': 'Stop',
                'screenshot': 'Screenshot',
                'drawing_tool': 'Drawing Tool',
                'start_recording': 'Start Recording',
                'stop_recording': 'Stop Recording',
                'pause_recording': 'Pause Recording',
                'resume_recording': 'Resume Recording',
                'ready': 'Ready',
                'recording': 'Recording',
                'paused': 'Paused',
                'theme': 'Theme',
                'language': 'Language',
                'status': 'Status',
                'duration': 'Duration',
                'file_size': 'File Size',
                'about': 'About',
                'version': 'Version',
                'copyright': 'Copyright',
                'website': 'Website',
            }
        }

    def set_language(self, lang):
        """设置语言"""
        if lang in self.translations:
            self.current_language = lang
            return True
        return False

    def get_text(self, key):
        """获取翻译文本"""
        return self.translations.get(self.current_language, {}).get(key, key)

# ==================== 音频增益处理 ====================
def _boost_audio_gain(frame_data, target_peak=0.5, max_gain=8.0):
    """对 16-bit PCM 音频数据做自动增益放大，解决麦克风录音音量过低的问题。

    根据整段数据的峰值计算统一增益（避免逐帧增益导致的音量波动），
    并做削波保护（clip）。输入为静音时不做任何处理。

    参数:
        frame_data: bytes，int16 小端 PCM 原始数据
        target_peak: 目标峰值（0~1），默认 0.5
        max_gain: 最大增益倍数，防止将底噪放大得过响

    返回:
        放大后的原始字节数据（int16 小端）
    """
    try:
        samples = np.frombuffer(frame_data, dtype=np.int16).astype(np.float32)
        if samples.size == 0:
            return frame_data
        peak = float(np.max(np.abs(samples))) / 32768.0
        if peak <= 0.0001:
            return frame_data  # 静音或接近静音，不放大
        gain = min(target_peak / peak, max_gain)
        if gain <= 1.0:
            return frame_data  # 音量已足够，无需放大
        samples *= gain
        np.clip(samples, -32768, 32767, out=samples)
        return samples.astype(np.int16).tobytes()
    except Exception:
        return frame_data

# ==================== 音频录制线程 ====================
class AudioRecorderThread(QThread):
    """音频录制线程"""
    audio_data_signal = pyqtSignal(bytes)
    error_signal = pyqtSignal(str)

    def __init__(self, device_index, sample_rate=None, channels=None, chunk_size=1024):
        super().__init__()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.running = False
        self.audio = None
        self.stream = None
        # 实际使用的参数（打开音频流后确定，供 WAV 写入使用）
        self.actual_sample_rate = 44100
        self.actual_channels = 1

    def run(self):
        """开始录制"""
        self.running = True
        try:
            self.audio = pyaudio.PyAudio()

            # 查询设备信息，自动适配采样率与声道数（单声道麦克风也能正常录制）
            try:
                dev_info = self.audio.get_device_info_by_index(self.device_index)
            except Exception:
                dev_info = {}
            max_channels = int(dev_info.get('maxInputChannels', 1) or 1)
            default_rate = int(dev_info.get('defaultSampleRate', 44100) or 44100)

            # 声道数：不超过设备支持的最大声道数（上限 2），保证单声道设备可用
            channels = self.channels or min(max_channels, 2)
            if channels < 1:
                channels = 1
            # 采样率：未指定时使用设备默认采样率
            sample_rate = self.sample_rate or default_rate
            self.actual_channels = channels
            self.actual_sample_rate = sample_rate

            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )

            while self.running:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_data_signal.emit(data)
                except Exception as e:
                    if self.running:
                        self.error_signal.emit(str(e))
                    break
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            # 确保资源被释放
            try:
                if self.stream:
                    self.stream.stop_stream()
                    self.stream.close()
            except Exception:
                pass
            try:
                if self.audio:
                    self.audio.terminate()
            except Exception:
                pass

    def stop(self):
        """停止录制"""
        self.running = False

# ==================== 鼠标跟踪器 ====================
class MouseTracker:
    """鼠标跟踪器类"""
    def __init__(self):
        self.current_x = 0
        self.current_y = 0
        self.last_click_x = 0
        self.last_click_y = 0
        self.click_detected = False
        self.tracking_area = None
        self.is_tracking = False

    def update_position(self, x, y):
        """更新鼠标位置"""
        self.current_x = x
        self.current_y = y

    def update_click(self, x, y):
        """更新点击位置"""
        self.last_click_x = x
        self.last_click_y = y
        self.click_detected = True

    def get_tracking_area_around_cursor(self, width=800, height=600):
        """根据当前光标位置获取跟踪区域"""
        try:
            from PIL import ImageGrab
            screen_width, screen_height = ImageGrab.grab().size
        except:
            screen_width, screen_height = 1920, 1080

        x1 = max(0, self.current_x - width // 2)
        y1 = max(0, self.current_y - height // 2)

        if x1 + width > screen_width:
            x1 = screen_width - width
        if y1 + height > screen_height:
            y1 = screen_height - height

        x1 = max(0, x1)
        y1 = max(0, y1)

        self.tracking_area = (x1, y1, width, height)
        return self.tracking_area

# ==================== 画图工具 ====================
class DrawingTool:
    """画图工具类"""
    def __init__(self):
        self.drawing = False
        self.last_x = None
        self.last_y = None
        self.shapes = []
        self.current_color = (255, 0, 0)
        self.current_thickness = 3
        self.current_tool = "pen"
        self.temp_shape = None

    def set_tool(self, tool):
        """设置工具"""
        self.current_tool = tool

    def set_color(self, color):
        """设置颜色"""
        self.current_color = color

    def set_thickness(self, thickness):
        """设置线条粗细"""
        self.current_thickness = thickness

    def start_drawing(self, x, y):
        """开始绘制"""
        self.drawing = True
        self.last_x = x
        self.last_y = y

        if self.current_tool in ["rectangle", "circle"]:
            self.temp_shape = {
                "type": self.current_tool,
                "x1": x,
                "y1": y,
                "x2": x,
                "y2": y,
                "color": self.current_color,
                "thickness": self.current_thickness
            }

    def draw(self, x, y):
        """绘制中"""
        if not self.drawing:
            return

        if self.current_tool == "pen":
            self.shapes.append({
                "type": "line",
                "x1": self.last_x,
                "y1": self.last_y,
                "x2": x,
                "y2": y,
                "color": self.current_color,
                "thickness": self.current_thickness
            })
            self.last_x = x
            self.last_y = y
        elif self.current_tool in ["rectangle", "circle"] and self.temp_shape:
            self.temp_shape["x2"] = x
            self.temp_shape["y2"] = y

    def stop_drawing(self):
        """停止绘制"""
        self.drawing = False
        if self.temp_shape:
            self.shapes.append(self.temp_shape)
            self.temp_shape = None

    def clear_all(self):
        """清除所有绘制"""
        self.shapes = []
        self.temp_shape = None

    def apply_drawings(self, frame):
        """将绘制应用到帧上"""
        frame_copy = frame.copy()

        for shape in self.shapes:
            if shape["type"] == "line":
                cv2.line(frame_copy,
                        (shape["x1"], shape["y1"]),
                        (shape["x2"], shape["y2"]),
                        shape["color"],
                        shape["thickness"])
            elif shape["type"] == "rectangle":
                cv2.rectangle(frame_copy,
                             (shape["x1"], shape["y1"]),
                             (shape["x2"], shape["y2"]),
                             shape["color"],
                             shape["thickness"])
            elif shape["type"] == "circle":
                center = (shape["x1"], shape["y1"])
                radius = int(math.sqrt((shape["x2"] - shape["x1"])**2 +
                                      (shape["y2"] - shape["y1"])**2))
                cv2.circle(frame_copy, center, radius, shape["color"], shape["thickness"])

        if self.temp_shape:
            if self.temp_shape["type"] == "rectangle":
                cv2.rectangle(frame_copy,
                             (self.temp_shape["x1"], self.temp_shape["y1"]),
                             (self.temp_shape["x2"], self.temp_shape["y2"]),
                             self.temp_shape["color"],
                             self.temp_shape["thickness"])
            elif self.temp_shape["type"] == "circle":
                center = (self.temp_shape["x1"], self.temp_shape["y1"])
                radius = int(math.sqrt((self.temp_shape["x2"] - self.temp_shape["x1"])**2 +
                                      (self.temp_shape["y2"] - self.temp_shape["y1"])**2))
                cv2.circle(frame_copy, center, radius, self.temp_shape["color"], self.temp_shape["thickness"])

        return frame_copy

# ==================== 主应用类 ====================
class ScreenRecorderApp(QMainWindow):
    """屏幕录制器主应用类"""
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    recording_paused = pyqtSignal()
    recording_resumed = pyqtSignal()
    # 全局热键触发信号（pynput 后台线程 -> 主线程）
    hotkey_triggered = pyqtSignal(str)
    # 二次元主题背景图就绪信号（下载线程 -> 主线程）
    anime_bg_ready = pyqtSignal(str)
    # 录制线程报告「无法创建视频文件」（录制线程 -> 主线程弹窗）
    recording_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowIcon(_load_app_icon())
        self.recording = False
        self.paused = False
        self.video_writer = None
        # 采集参数快照（录制线程只读这些普通属性，不碰 QWidget）
        self._cap_mode = None
        self._cap_width = 0
        self._cap_height = 0
        # 是否正在保存（FFmpeg 收尾）：禁用录制按钮 / 防重入
        self._saving = False
        self.mouse_tracker = MouseTracker()
        self.drawing_tool = DrawingTool()
        self.audio_recorder = None
        self.audio_frames = []
        self.audio_enabled = False
        # 音视频合并失败时的现场：真实原因 + 音频另存路径（不丢音频）
        self._audio_merge_error = None
        self._audio_sidecar = None
        self._ffmpeg_cache = {}
        self.recording_thread = None
        self.temp_dir = tempfile.mkdtemp(prefix="screen_recorder_")

        self.quality = "high"
        self.format = "MP4"
        self.codec = "libx264"
        self.fps = 30
        self.output_dir = os.path.expanduser("~/Videos")
        self.output_file = None
        self.temp_audio_file = None

        self.frame_count = 0
        self.recording_start_time = None
        self.elapsed_time = 0

        # 实际录制时长统计（用于校正视频帧率，防止快放/慢放）
        self.recording_active_seconds = 0.0
        self.last_active_tick = 0

        self.theme_manager = ThemeManager()
        self.language_manager = LanguageManager()

        self.audio_devices = []
        self.audio_device_index = None
        self.record_audio = True
        # 音频降噪：保存时由 FFmpeg 统一处理（不拖累录制时的 CPU）
        # 强度 0-100（0 = 关闭降噪）；默认 40 约等于 1.5.21 的固定参数（nr≈13 / nf≈-32）
        self.denoise_strength = 40
        # 关闭窗口时最小化到托盘（后台保活）
        self.minimize_to_tray = True
        self._force_quit = False
        self._tray = None
        self._tray_notified = False
        # 单实例通讯服务（由 main() 注入；收到 SHOW 时把窗口唤到前台）
        self._instance_server = None
        self.load_settings()

        # 热键配置
        self.hotkeys = {
            'start_pause': 'F9',
            'stop': 'F10',
            'screenshot': 'F11',
            'drawing': 'F12'
        }
        self.load_hotkeys()

        self.hotkey_triggered.connect(self._on_hotkey_triggered)
        self.recording_error.connect(self._on_recording_error)
        self._hotkey_listener = None
        self._drawing_window = None

        # 二次元主题背景
        self.anime_bg_pixmap = None
        self.anime_bg_loading = False
        self.anime_bg_ready.connect(self._on_anime_bg_ready)

        self.init_audio_devices()
        self.init_ui()
        self.apply_theme()

        # 启动全局热键监听
        self.update_global_hotkeys()

    def load_hotkeys(self):
        """加载热键配置"""
        hotkey_file = os.path.join(os.path.expanduser("~"), ".super_hi_vision_hotkeys.json")
        if os.path.exists(hotkey_file):
            try:
                with open(hotkey_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.hotkeys.update(saved)
            except:
                pass

    def save_hotkeys(self):
        """保存热键配置"""
        hotkey_file = os.path.join(os.path.expanduser("~"), ".super_hi_vision_hotkeys.json")
        try:
            with open(hotkey_file, 'w', encoding='utf-8') as f:
                json.dump(self.hotkeys, f, indent=2)
        except:
            pass

    def _settings_file(self):
        return os.path.join(os.path.expanduser("~"), ".super_hi_vision_settings.json")

    def load_settings(self):
        """加载界面偏好（降噪强度 / 托盘保活），失败一律回退默认值"""
        try:
            with open(self._settings_file(), 'r', encoding='utf-8') as f:
                saved = json.load(f) or {}
            if isinstance(saved, dict):
                if 'denoise_strength' in saved:
                    try:
                        self.denoise_strength = max(0, min(100, int(saved['denoise_strength'])))
                    except (TypeError, ValueError):
                        pass
                elif 'denoise' in saved:
                    # 兼容 1.5.21 及更早的布尔开关：开 = 中度（40），关 = 关闭（0）
                    self.denoise_strength = 40 if bool(saved['denoise']) else 0
                if 'minimize_to_tray' in saved:
                    self.minimize_to_tray = bool(saved['minimize_to_tray'])
        except Exception:
            pass

    def save_settings(self):
        """保存界面偏好"""
        try:
            with open(self._settings_file(), 'w', encoding='utf-8') as f:
                json.dump({
                    'denoise_strength': int(self.denoise_strength),
                    'denoise': bool(int(self.denoise_strength) > 0),   # 兼容旧版本读取
                    'minimize_to_tray': bool(self.minimize_to_tray),
                }, f, indent=2)
        except Exception:
            pass

    def _denoise_filter_chain(self):
        """按降噪强度(0-100)生成 FFmpeg 滤波链；0 = 关闭降噪返回空列表。

        映射（ffmpeg 实测：nf 越接近 -20、nr 越大，压掉的底噪越多）：
          nr = 6 ~ 24，nf = -40 ~ -20 dB；强度 40 ≈ nr 13 / nf -32（≈1.5.21 的固定值）
        """
        try:
            s = max(0, min(100, int(self.denoise_strength)))
        except (TypeError, ValueError):
            s = 0
        if s <= 0:
            return []
        nr = round(6 + (s - 1) * 18.0 / 99.0, 1)
        nf = int(round(-40 + (s - 1) * 20.0 / 99.0))
        return ['highpass=f=80', f'afftdn=nr={nr}:nf={nf}']

    def init_audio_devices(self):
        """初始化音频设备（优先选择系统默认输入设备）"""
        try:
            p = pyaudio.PyAudio()
            self.audio_devices = []

            # 获取系统默认输入设备（Windows 默认麦克风）
            default_input_index = None
            try:
                default_input_index = p.get_default_input_device_info().get('index')
            except Exception:
                pass

            for i in range(p.get_device_count()):
                dev_info = p.get_device_info_by_index(i)
                if dev_info.get('maxInputChannels', 0) > 0:
                    self.audio_devices.append({
                        'index': i,
                        'name': dev_info.get('name', f'Device {i}'),
                        'is_default': (i == default_input_index)
                    })

            p.terminate()

            if self.audio_devices:
                # 默认选中系统默认输入设备，避免选中静音/错误的设备导致录不到声音
                default_device = next(
                    (d for d in self.audio_devices if d.get('is_default')),
                    self.audio_devices[0]
                )
                self.audio_device_index = default_device['index']
            else:
                self.audio_device_index = None
        except Exception as e:
            print(f"Audio device init error: {e}")
            self.audio_device_index = None

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle(f"Super Hi Vision - {self.language_manager.get_text('app_title')} v{__version__}")
        self.setGeometry(100, 100, 900, 750)
        self.setMinimumSize(800, 650)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.create_header(main_layout)

        self.tab_widget = QTabWidget()
        self.create_basic_tab()
        self.create_advanced_tab()
        self.create_audio_tab()
        self.create_hotkey_tab()
        main_layout.addWidget(self.tab_widget)

        self.create_control_buttons(main_layout)

        # 保存进度条：合成音视频 / 校正帧率时在窗口内实时显示，不弹任何对话框
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        self.create_status_bar(main_layout)

        # 系统托盘（后台保活 / 关闭窗口后继续可用）
        self.init_tray()

    def create_header(self, parent_layout):
        """创建标题栏"""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)

        left_layout = QVBoxLayout()
        title_label = QLabel("Super Hi Vision")
        title_label.setFont(QFont("Segoe UI", 20, QFont.Bold))
        title_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['accent']};")

        version_label = QLabel(f"{self.language_manager.get_text('version')} {__version__}")
        version_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['text_light']};")

        left_layout.addWidget(title_label)
        left_layout.addWidget(version_label)

        right_layout = QHBoxLayout()

        theme_label = QLabel(self.language_manager.get_text('theme') + ":")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(['Dark', 'Light', 'Ocean', 'Sunset', 'Forest', 'Purple', 'Anime'])
        self.theme_combo.currentTextChanged.connect(self.change_theme)

        lang_label = QLabel(self.language_manager.get_text('language') + ":")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(['中文', 'English'])
        self.lang_combo.currentTextChanged.connect(self.change_language)

        right_layout.addWidget(theme_label)
        right_layout.addWidget(self.theme_combo)
        right_layout.addSpacing(20)
        right_layout.addWidget(lang_label)
        right_layout.addWidget(self.lang_combo)

        header_layout.addLayout(left_layout, 1)
        header_layout.addLayout(right_layout, 0)

        parent_layout.addWidget(header_frame)

        self.status_label = QLabel(self.language_manager.get_text('ready'))
        self.status_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['success']};")

    def create_basic_tab(self):
        """创建基本设置标签页"""
        basic_widget = QWidget()
        layout = QVBoxLayout(basic_widget)

        area_group = QGroupBox(self.language_manager.get_text('recording_area'))
        area_layout = QVBoxLayout()

        mode_layout = QHBoxLayout()
        self.area_mode = 'fullscreen'
        self.fullscreen_radio = QRadioButton(self.language_manager.get_text('fullscreen'))
        self.fullscreen_radio.setChecked(True)
        self.fullscreen_radio.clicked.connect(lambda: self.set_area_mode('fullscreen'))

        self.custom_radio = QRadioButton(self.language_manager.get_text('custom_area'))
        self.custom_radio.clicked.connect(lambda: self.set_area_mode('custom'))

        self.follow_radio = QRadioButton(self.language_manager.get_text('follow_mouse'))
        self.follow_radio.clicked.connect(lambda: self.set_area_mode('follow_mouse'))

        mode_layout.addWidget(self.fullscreen_radio)
        mode_layout.addWidget(self.custom_radio)
        mode_layout.addWidget(self.follow_radio)
        mode_layout.addStretch()
        area_layout.addLayout(mode_layout)

        self.custom_frame = QFrame()
        custom_layout = QHBoxLayout(self.custom_frame)
        custom_layout.addWidget(QLabel(self.language_manager.get_text('width') + ":"))

        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 9999)
        self.width_spin.setValue(1920)
        custom_layout.addWidget(self.width_spin)

        custom_layout.addWidget(QLabel(self.language_manager.get_text('height') + ":"))

        self.height_spin = QSpinBox()
        self.height_spin.setRange(100, 9999)
        self.height_spin.setValue(1080)
        custom_layout.addWidget(self.height_spin)

        self.select_area_btn = QPushButton(self.language_manager.get_text('select_area'))
        self.select_area_btn.clicked.connect(self.select_area)
        custom_layout.addWidget(self.select_area_btn)
        custom_layout.addStretch()

        area_layout.addWidget(self.custom_frame)
        self.custom_frame.hide()

        self.follow_frame = QFrame()
        follow_layout = QHBoxLayout(self.follow_frame)
        follow_layout.addWidget(QLabel(self.language_manager.get_text('width') + ":"))

        self.follow_width_spin = QSpinBox()
        self.follow_width_spin.setRange(100, 9999)
        self.follow_width_spin.setValue(800)
        follow_layout.addWidget(self.follow_width_spin)

        follow_layout.addWidget(QLabel("x"))

        self.follow_height_spin = QSpinBox()
        self.follow_height_spin.setRange(100, 9999)
        self.follow_height_spin.setValue(600)
        follow_layout.addWidget(self.follow_height_spin)

        follow_layout.addWidget(QLabel(self.language_manager.get_text('height') + ":"))
        follow_layout.addStretch()

        area_layout.addWidget(self.follow_frame)
        self.follow_frame.hide()

        area_group.setLayout(area_layout)
        layout.addWidget(area_group)

        output_group = QGroupBox(self.language_manager.get_text('output_settings'))
        output_layout = QVBoxLayout()

        filename_layout = QHBoxLayout()
        filename_layout.addWidget(QLabel(self.language_manager.get_text('filename') + ":"))

        self.filename_edit = QLineEdit()
        self.filename_edit.setText(f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        filename_layout.addWidget(self.filename_edit)

        self.browse_btn = QPushButton(self.language_manager.get_text('browse'))
        self.browse_btn.clicked.connect(self.browse_output)
        filename_layout.addWidget(self.browse_btn)

        output_layout.addLayout(filename_layout)

        dir_layout = QHBoxLayout()
        dir_layout.addWidget(QLabel(self.language_manager.get_text('output_dir') + ":"))

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setText(self.output_dir)
        dir_layout.addWidget(self.output_dir_edit)

        self.output_dir_btn = QPushButton("...")
        self.output_dir_btn.clicked.connect(self.browse_output_dir)
        dir_layout.addWidget(self.output_dir_btn)

        output_layout.addLayout(dir_layout)
        output_group.setLayout(output_layout)
        layout.addWidget(output_group)

        layout.addStretch()
        self.tab_widget.addTab(basic_widget, self.language_manager.get_text('basic_settings'))

    def create_advanced_tab(self):
        """创建高级设置标签页"""
        advanced_widget = QWidget()
        layout = QVBoxLayout(advanced_widget)

        video_group = QGroupBox("Video Settings")
        video_layout = QGridLayout()

        video_layout.addWidget(QLabel(self.language_manager.get_text('video_format') + ":"), 0, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "AVI", "MKV", "FLV", "MOV"])
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        video_layout.addWidget(self.format_combo, 0, 1)

        video_layout.addWidget(QLabel(self.language_manager.get_text('encoder') + ":"), 1, 0)
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(["H.264 (libx264)", "H.265/HEVC (libx265)", "MPEG-4 (mpeg4)", "VP8 (libvpx)", "VP9 (libvpx-vp9)"])
        video_layout.addWidget(self.codec_combo, 1, 1)

        video_layout.addWidget(QLabel(self.language_manager.get_text('fps') + ":"), 2, 0)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["10 FPS", "15 FPS", "24 FPS", "30 FPS", "45 FPS", "60 FPS", "90 FPS", "120 FPS"])
        self.fps_combo.setCurrentText("30 FPS")
        video_layout.addWidget(self.fps_combo, 2, 1)

        video_layout.addWidget(QLabel(self.language_manager.get_text('quality') + ":"), 3, 0)
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Low", "Medium", "High", "Ultra", "Bluray"])
        self.quality_combo.setCurrentText("High")
        video_layout.addWidget(self.quality_combo, 3, 1)

        video_group.setLayout(video_layout)
        layout.addWidget(video_group)

        # 后台保活（关闭窗口不退出，驻留系统托盘）
        behavior_group = QGroupBox(self.language_manager.get_text('basic_settings'))
        behavior_layout = QVBoxLayout()
        self.tray_check = QCheckBox(self.language_manager.get_text('minimize_to_tray'))
        self.tray_check.setChecked(bool(self.minimize_to_tray))
        self.tray_check.stateChanged.connect(self.on_minimize_to_tray_changed)
        behavior_layout.addWidget(self.tray_check)
        behavior_group.setLayout(behavior_layout)
        layout.addWidget(behavior_group)

        # FFmpeg 自检：把「有画面无声音」的排查从盲猜变成一条可执行结论
        ff_group = QGroupBox("FFmpeg（音视频合成 / 帧率校正）")
        ff_layout = QVBoxLayout()
        self.ffmpeg_status_label = QLabel(self.ffmpeg_status_short())
        self.ffmpeg_status_label.setWordWrap(True)
        ff_layout.addWidget(self.ffmpeg_status_label)
        ff_row = QHBoxLayout()
        self.ffmpeg_check_btn = QPushButton(self.language_manager.get_text('check_ffmpeg'))
        self.ffmpeg_check_btn.clicked.connect(self.on_check_ffmpeg)
        ff_row.addWidget(self.ffmpeg_check_btn)
        ff_row.addStretch()
        ff_layout.addLayout(ff_row)
        ff_group.setLayout(ff_layout)
        layout.addWidget(ff_group)

        layout.addStretch()
        self.tab_widget.addTab(advanced_widget, self.language_manager.get_text('advanced_settings'))

    def create_audio_tab(self):
        """创建音频设置标签页"""
        audio_widget = QWidget()
        layout = QVBoxLayout(audio_widget)

        audio_group = QGroupBox(self.language_manager.get_text('audio_recording'))
        audio_layout = QVBoxLayout()

        self.enable_audio_check = QCheckBox(self.language_manager.get_text('enable_audio'))
        self.enable_audio_check.setChecked(True)
        self.enable_audio_check.stateChanged.connect(self.on_audio_enabled_changed)
        audio_layout.addWidget(self.enable_audio_check)

        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel(self.language_manager.get_text('audio_device') + ":"))

        self.audio_device_combo = QComboBox()
        if self.audio_devices:
            for device in self.audio_devices:
                self.audio_device_combo.addItem(device['name'], device['index'])
            # 默认选中系统默认输入设备
            default_index = getattr(self, 'audio_device_index', None)
            idx = self.audio_device_combo.findData(default_index)
            if idx >= 0:
                self.audio_device_combo.setCurrentIndex(idx)
        else:
            self.audio_device_combo.addItem("No audio device available", -1)
        device_layout.addWidget(self.audio_device_combo)

        self.test_audio_btn = QPushButton(self.language_manager.get_text('test_audio'))
        self.test_audio_btn.clicked.connect(self.test_audio)
        device_layout.addWidget(self.test_audio_btn)

        audio_layout.addLayout(device_layout)

        # 音频降噪强度（保存阶段由 FFmpeg 统一处理）
        denoise_row = QHBoxLayout()
        denoise_row.addWidget(QLabel(self.language_manager.get_text('denoise_strength')))
        self.denoise_slider = QSlider(Qt.Horizontal)
        self.denoise_slider.setRange(0, 100)
        self.denoise_slider.setSingleStep(5)
        self.denoise_slider.setPageStep(10)
        self.denoise_slider.setTickInterval(25)
        self.denoise_slider.setTickPosition(QSlider.TicksBelow)
        self.denoise_slider.setValue(int(self.denoise_strength))
        self.denoise_slider.setToolTip(self.language_manager.get_text('denoise_hint'))
        self.denoise_slider.valueChanged.connect(self.on_denoise_strength_changed)
        denoise_row.addWidget(self.denoise_slider, 1)
        self.denoise_value_label = QLabel('')
        self.denoise_value_label.setMinimumWidth(96)
        denoise_row.addWidget(self.denoise_value_label)
        audio_layout.addLayout(denoise_row)
        self._refresh_denoise_label()

        denoise_hint = QLabel(self.language_manager.get_text('denoise_hint'))
        denoise_hint.setWordWrap(True)
        denoise_hint.setStyleSheet(f"color: {self.theme_manager.get_theme()['text_light']}; font-size: 11px;")
        audio_layout.addWidget(denoise_hint)

        audio_group.setLayout(audio_layout)
        layout.addWidget(audio_group)

        layout.addStretch()
        self.tab_widget.addTab(audio_widget, self.language_manager.get_text('audio_settings'))

    def create_hotkey_tab(self):
        """创建热键设置标签页"""
        hotkey_widget = QWidget()
        layout = QVBoxLayout(hotkey_widget)

        hotkey_group = QGroupBox(self.language_manager.get_text('hotkeys'))
        hotkey_layout = QGridLayout()

        self.hotkey_buttons = {}

        hotkey_items = [
            ('start_pause', self.language_manager.get_text('start_pause')),
            ('stop', self.language_manager.get_text('stop')),
            ('screenshot', self.language_manager.get_text('screenshot')),
            ('drawing', self.language_manager.get_text('drawing_tool'))
        ]

        for i, (key, label) in enumerate(hotkey_items):
            hotkey_layout.addWidget(QLabel(label), i, 0)
            
            btn = QPushButton(self.hotkeys[key])
            btn.setStyleSheet("padding: 5px 15px; min-width: 80px;")
            btn.clicked.connect(lambda checked, k=key: self.change_hotkey(k))
            self.hotkey_buttons[key] = btn
            hotkey_layout.addWidget(btn, i, 1)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self.reset_hotkeys)
        hotkey_layout.addWidget(reset_btn, 4, 0, 1, 2)

        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)

        layout.addStretch()
        self.tab_widget.addTab(hotkey_widget, self.language_manager.get_text('hotkey_settings'))

    def create_control_buttons(self, parent_layout):
        """创建控制按钮"""
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)

        self.start_btn = QPushButton(self.language_manager.get_text('start_recording'))
        self.start_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.start_btn.clicked.connect(self.toggle_recording)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton(self.language_manager.get_text('stop_recording'))
        self.stop_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_recording)
        control_layout.addWidget(self.stop_btn)

        self.screenshot_btn = QPushButton(self.language_manager.get_text('screenshot'))
        self.screenshot_btn.clicked.connect(self.take_screenshot)
        control_layout.addWidget(self.screenshot_btn)

        parent_layout.addWidget(control_frame)

    def create_status_bar(self, parent_layout):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet(f"QStatusBar {{ background-color: {self.theme_manager.get_theme()['secondary']}; color: {self.theme_manager.get_theme()['text_light']}; }}")

        self.duration_label = QLabel(f"{self.language_manager.get_text('duration')}: 00:00:00")
        self.file_size_label = QLabel(f"{self.language_manager.get_text('file_size')}: 0 MB")

        self.status_bar.addPermanentWidget(self.duration_label)
        self.status_bar.addPermanentWidget(self.file_size_label)
        self.status_bar.addWidget(self.status_label)

        parent_layout.addWidget(self.status_bar)

    def set_area_mode(self, mode):
        """设置录制区域模式"""
        self.area_mode = mode
        if mode == 'fullscreen':
            self.custom_frame.hide()
            self.follow_frame.hide()
        elif mode == 'custom':
            self.custom_frame.show()
            self.follow_frame.hide()
        elif mode == 'follow_mouse':
            self.custom_frame.hide()
            self.follow_frame.show()

    def select_area(self):
        """选择录制区域"""
        QMessageBox.information(self, "Select Area", "Click and drag to select recording area")

    def browse_output(self):
        """浏览输出文件"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Recording",
            self.output_dir,
            f"Video Files (*.{self.format.lower()})"
        )
        if filename:
            self.filename_edit.setText(os.path.splitext(os.path.basename(filename))[0])

    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.output_dir)
        if dir_path:
            self.output_dir = dir_path
            self.output_dir_edit.setText(dir_path)

    def on_format_changed(self, format_name):
        """格式改变事件"""
        self.format = format_name

    def on_audio_enabled_changed(self, state):
        """音频启用状态改变"""
        self.record_audio = (state == Qt.Checked)

    def on_denoise_strength_changed(self, value):
        """降噪强度滑杆变化"""
        self.denoise_strength = int(value)
        self._refresh_denoise_label()
        self.save_settings()

    def _refresh_denoise_label(self):
        """刷新降噪强度文字（关闭 / 轻度 / 中度 / 强力 + 百分比）"""
        try:
            s = max(0, min(100, int(self.denoise_strength)))
        except (TypeError, ValueError):
            s = 0
        if s <= 0:
            text = self.language_manager.get_text('denoise_off')
        elif s <= 33:
            text = f"{self.language_manager.get_text('denoise_light')} {s}%"
        elif s <= 66:
            text = f"{self.language_manager.get_text('denoise_medium')} {s}%"
        else:
            text = f"{self.language_manager.get_text('denoise_strong')} {s}%"
        if getattr(self, 'denoise_value_label', None) is not None:
            self.denoise_value_label.setText(text)

    def on_denoise_changed(self, state):
        """兼容旧签名：布尔开关 → 强度 40/0"""
        self.denoise_strength = 40 if state == Qt.Checked else 0
        self.save_settings()

    def on_minimize_to_tray_changed(self, state):
        """关闭窗口时是否最小化到托盘（后台保活）"""
        self.minimize_to_tray = (state == Qt.Checked)
        self.save_settings()

    # ==================== 系统托盘 / 后台保活 ====================
    def init_tray(self):
        """创建系统托盘图标：关闭窗口后程序继续在后台运行（录制与全局热键不受影响）"""
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                print("⚠️ 系统托盘不可用，关闭窗口将直接退出")
                self._tray = None
                return
            tray = QSystemTrayIcon(_load_app_icon(), self)
            tray.setToolTip(self.language_manager.get_text('tray_tip'))

            menu = QMenu()
            act_show = menu.addAction(self.language_manager.get_text('show_window'))
            act_show.triggered.connect(self.restore_window)

            act_rec = menu.addAction(self.language_manager.get_text('start_pause'))
            act_rec.triggered.connect(lambda: self._on_hotkey_triggered('start_pause'))

            act_stop = menu.addAction(self.language_manager.get_text('stop_recording'))
            act_stop.triggered.connect(lambda: self._on_hotkey_triggered('stop'))

            menu.addSeparator()
            act_quit = menu.addAction(self.language_manager.get_text('quit_app'))
            act_quit.triggered.connect(self.quit_app)

            tray.setContextMenu(menu)
            tray.activated.connect(self._on_tray_activated)
            tray.show()
            self._tray = tray
        except Exception as e:
            print(f"⚠️ 系统托盘初始化失败: {e}")
            self._tray = None

    def _on_tray_activated(self, reason):
        """双击/单击托盘图标 → 把窗口唤回前台"""
        try:
            if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
                self.restore_window()
        except Exception:
            pass

    def _update_tray_tooltip(self, text=None):
        if self._tray is None:
            return
        try:
            self._tray.setToolTip(text or self.language_manager.get_text('tray_tip'))
        except Exception:
            pass

    def _notify_tray_once(self):
        """首次隐藏到托盘时提示一次（之后保持静默）"""
        if self._tray is None or self._tray_notified:
            return
        self._tray_notified = True
        try:
            self._tray.showMessage(
                "Super Hi Vision",
                self.language_manager.get_text('tray_running'),
                QSystemTrayIcon.Information, 3000
            )
        except Exception:
            pass

    def restore_window(self):
        """把窗口从托盘/最小化状态唤回前台（再次点击程序时也走这里）"""
        try:
            self.show()
            if self.isMinimized():
                self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
            self.raise_()
            self.activateWindow()
            # Windows 下仅靠 activateWindow 常常拿不到焦点，借用置顶窗口属性强制前台
            if os.name == 'nt':
                try:
                    self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
                    self.show()
                    self.setWindowFlag(Qt.WindowStaysOnTopHint, False)
                    self.show()
                except Exception:
                    pass
        except Exception as e:
            print(f"⚠️ 唤起窗口失败: {e}")

    def handle_instance_message(self, message):
        """收到第二个实例的唤醒请求 → 显示窗口（解决「再次点击应用打不开」）"""
        try:
            if message.strip().upper() == 'SHOW':
                self.restore_window()
        except Exception:
            pass

    def quit_app(self):
        """真正退出（托盘菜单 / 关闭窗口时禁用托盘保活的分支都会走到这里）"""
        self._force_quit = True
        try:
            if self.recording:
                self.stop_recording()
        except Exception:
            pass
        try:
            self._stop_global_hotkeys()
        except Exception:
            pass
        if getattr(self, '_instance_server', None) is not None:
            try:
                self._instance_server.close()
            except Exception:
                pass
        if self._tray is not None:
            try:
                self._tray.hide()
            except Exception:
                pass
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        QApplication.quit()

    def test_audio(self):
        """测试音频：从所选设备录制约 3 秒并播放，验证音频设备是否可用"""
        device_index = self.audio_device_combo.currentData()
        if device_index is None or device_index < 0:
            QMessageBox.warning(self, "测试失败", "没有可用的音频输入设备，请检查麦克风设置。")
            return

        try:
            p = pyaudio.PyAudio()
            try:
                dev_info = p.get_device_info_by_index(device_index)
            except Exception:
                dev_info = {}

            max_channels = int(dev_info.get('maxInputChannels', 1) or 1)
            channels = min(max_channels, 2)
            rate = int(dev_info.get('defaultSampleRate', 44100) or 44100)

            stream = p.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=1024
            )

            frames = []
            for _ in range(int(rate / 1024 * 3)):  # 录制约 3 秒
                frames.append(stream.read(1024, exception_on_overflow=False))

            stream.stop_stream()
            stream.close()
            p.terminate()

            test_path = os.path.join(self.temp_dir, "audio_test.wav")
            # 自动增益放大，解决麦克风录音音量过低、测试播放听不清的问题
            audio_data = _boost_audio_gain(b''.join(frames))
            with wave.open(test_path, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)
                wf.setframerate(rate)
                wf.writeframes(audio_data)

            # 播放测试音频
            try:
                import winsound
                winsound.PlaySound(test_path, winsound.SND_FILENAME)
            except Exception:
                os.startfile(test_path)

            device_name = dev_info.get('name', '未知设备')
            QMessageBox.information(
                self, "测试成功",
                f"音频录制测试成功！\n"
                f"设备: {device_name}\n"
                f"声道: {channels}  采样率: {rate}\n\n"
                f"已录制约 3 秒并自动播放，请确认能否听到声音。"
            )
        except Exception as e:
            QMessageBox.critical(self, "测试失败", f"音频测试失败: {str(e)}")

    def change_theme(self, theme_name):
        """改变主题"""
        theme_map = {
            'Dark': 'dark',
            'Light': 'light',
            'Ocean': 'ocean',
            'Sunset': 'sunset',
            'Forest': 'forest',
            'Purple': 'purple',
            'Anime': 'anime'
        }
        theme_key = theme_map.get(theme_name, 'dark')
        self.theme_manager.set_theme(theme_key)
        self.apply_theme()

    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_theme()
        style_sheet = self.theme_manager.generate_style_sheet()
        self.setStyleSheet(style_sheet)
        # 二次元主题：异步加载随机背景图
        self.load_anime_background()

    def load_anime_background(self):
        """加载二次元主题背景（异步从 dmoe.cc 获取随机图片）"""
        if self.theme_manager.current_theme != 'anime':
            self.anime_bg_pixmap = None
            self.update()
            return

        # 优先显示本地缓存，避免每次切换都等待网络
        cache = os.path.join(tempfile.gettempdir(), "super_hi_vision_anime_bg.jpg")
        if os.path.exists(cache):
            pm = QPixmap(cache)
            if not pm.isNull():
                self.anime_bg_pixmap = pm
                self.update()

        if self.anime_bg_loading:
            return
        self.anime_bg_loading = True
        threading.Thread(target=self._download_anime_bg, args=(cache,), daemon=True).start()

    def _download_anime_bg(self, cache_path):
        """后台线程下载随机二次元背景图（dmoe.cc 国内 API，禁用系统代理直连）"""
        try:
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
            req = urllib.request.Request(
                "https://www.dmoe.cc/random.php",
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with opener.open(req, timeout=15) as resp:
                data = resp.read()
            if data and len(data) > 1000:
                with open(cache_path, 'wb') as f:
                    f.write(data)
                self.anime_bg_ready.emit(cache_path)
                print("✅ 二次元背景图已更新")
            else:
                print("❌ 二次元背景下载内容无效")
        except Exception as e:
            print(f"❌ 二次元背景下载失败: {e}")
        finally:
            self.anime_bg_loading = False

    def _on_anime_bg_ready(self, path):
        """主线程：加载下载完成的二次元背景图"""
        pm = QPixmap(path)
        if not pm.isNull():
            self.anime_bg_pixmap = pm
            self.update()

    def paintEvent(self, event):
        """绘制窗口背景（二次元主题绘制随机图片背景 + 遮罩）"""
        if (self.theme_manager.current_theme == 'anime'
                and self.anime_bg_pixmap is not None
                and not self.anime_bg_pixmap.isNull()):
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(22, 26, 46))
            pm = self.anime_bg_pixmap
            scaled = pm.scaled(self.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            painter.drawPixmap(0, 0, scaled, x, y, self.width(), self.height())
            # 半透明深色遮罩，保证控件可读性
            painter.fillRect(self.rect(), QColor(10, 10, 30, 100))
            painter.end()
        else:
            super().paintEvent(event)

    def change_language(self, lang_text):
        """改变语言"""
        lang = 'zh' if lang_text == '中文' else 'en'
        self.language_manager.set_language(lang)
        self.refresh_ui_texts()

    def refresh_ui_texts(self):
        """刷新界面文本"""
        self.setWindowTitle(f"Super Hi Vision - {self.language_manager.get_text('app_title')} v{__version__}")
        self.status_label.setText(self.language_manager.get_text('ready'))

    def toggle_recording(self):
        """切换录制状态"""
        if not self.recording:
            self.start_recording()
        else:
            if not self.paused:
                self.pause_recording()
            else:
                self.resume_recording()

    # 各容器可用的编码 fourcc 候选（按优先级尝试，避免个别编码器缺失时录出空文件）
    _FOURCC_CANDIDATES = {
        'MP4': ['mp4v', 'avc1'],
        'AVI': ['XVID', 'MJPG'],
        'MKV': ['mp4v', 'XVID', 'MJPG'],
        'FLV': ['FLV1', 'mp4v'],
        'MOV': ['avc1', 'mp4v'],
    }
    _FOURCC_DEFAULT = ['mp4v', 'MJPG']

    def _create_video_writer(self, output_file, width, height):
        """创建视频写入器：按容器依次尝试可用编码，并校验是否真正打开

        某些 fourcc（例如 MKV 常用的 X264）在当前 OpenCV 里没有对应编码器时会
        静默失败——不抛异常、不写任何数据，最后留下一个 0 字节、无法播放的文件。
        这里逐个候选验证 isOpened()，全部失败则返回 None，由调用方提示用户。
        """
        candidates = self._FOURCC_CANDIDATES.get(self.format, self._FOURCC_DEFAULT)
        last_error = "无可用编码器"

        for tag in candidates:
            try:
                writer = cv2.VideoWriter(
                    output_file, cv2.VideoWriter_fourcc(*tag), self.fps, (width, height)
                )
            except Exception as e:
                last_error = str(e)
                continue

            if writer.isOpened():
                if tag != candidates[0]:
                    print(f"⚠️ 编码 {candidates[0]} 不可用，已回退到 {tag}")
                print(f"🎬 视频编码: {tag} -> {output_file}")
                return writer

            try:
                writer.release()
            except Exception:
                pass
            last_error = f"编码 {tag} 无法打开"

        print(f"❌ 无法创建视频写入器: {last_error}")
        return None

    def start_recording(self):
        """开始录制"""
        if self.recording:
            return
        if getattr(self, '_saving', False):
            # 正在保存上一段视频（FFmpeg 收尾），此时不接受新的录制请求
            print("⚠️ 正在保存上一段视频，请稍候再开始录制")
            return

        self.recording = True
        self.paused = False
        self.frame_count = 0
        self.audio_frames = []
        self._audio_merge_error = None
        self._audio_sidecar = None
        self.recording_start_time = time.time()
        self.recording_active_seconds = 0.0
        self.last_active_tick = time.time()

        output_filename = self.filename_edit.text()
        if not output_filename:
            output_filename = f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.output_file = os.path.join(self.output_dir, f"{output_filename}.{self.format.lower()}")

        # 编码器候选由 _create_video_writer 按容器逐个尝试（见下方创建写入器处）

        fps_map = {
            '10 FPS': 10, '15 FPS': 15, '24 FPS': 24, '30 FPS': 30,
            '45 FPS': 45, '60 FPS': 60, '90 FPS': 90, '120 FPS': 120
        }
        self.fps = fps_map.get(self.fps_combo.currentText(), 30)

        if self.area_mode == 'fullscreen':
            try:
                from PIL import ImageGrab
                screen = ImageGrab.grab()
                width, height = screen.size
            except:
                width, height = 1920, 1080
        elif self.area_mode == 'custom':
            width = self.width_spin.value()
            height = self.height_spin.value()
        else:
            width = self.follow_width_spin.value()
            height = self.follow_height_spin.value()

        # 确保输出目录存在（首次运行 / 用户手改了路径时，缺目录会让录制静默失败）
        try:
            os.makedirs(self.output_dir, exist_ok=True)
        except Exception as e:
            print(f"⚠️ 无法创建输出目录 {self.output_dir}: {e}")

        # yuv420 系列编码器要求宽高为偶数，否则部分编码器会拒绝打开
        width -= width % 2
        height -= height % 2

        # 采集参数快照到普通属性：录制循环跑在工作线程里，QWidget 非线程安全，
        # 不能在循环里读 width_spin / follow_*_spin 等控件。
        self._cap_mode = self.area_mode
        self._cap_width = width
        self._cap_height = height

        # 关键：cv2.VideoWriter 必须在同一个线程里「创建 / 写帧 / 释放」。
        # 此前是「GUI 线程创建 → 录制线程 write → GUI 线程 release」，跨线程使用
        # OpenCV 自带的 FFmpeg 封装（opencv_videoio_ffmpeg4110_64.dll）会在释放时
        # 直接 abort()——Windows 事件日志：异常代码 0x40000015（STATUS_FATAL_APP_EXIT），
        # 故障模块正是该 dll。表现为「视频保存完成之后应用崩溃 / 打不开」。
        # 现在写入器由录制线程全权持有，创建失败时经 recording_error 信号回主线程弹窗。
        self.video_writer = None

        if self.record_audio and self.enable_audio_check.isChecked():
            device_index = self.audio_device_combo.currentData()
            if device_index is not None and device_index >= 0:
                self.audio_recorder = AudioRecorderThread(device_index)
                self.audio_recorder.audio_data_signal.connect(self.on_audio_data)
                self.audio_recorder.error_signal.connect(self.on_audio_error)
                self.audio_recorder.start()
            else:
                print("❌ 未选择有效的音频输入设备，本次录制不包含声音")

        self.recording_thread = QThread()
        self.recording_thread.run = self.recording_loop
        self.recording_thread.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_recording_status)
        self.timer.start(1000)

        self.start_btn.setText(self.language_manager.get_text('pause_recording'))
        self.stop_btn.setEnabled(True)
        self.status_label.setText(self.language_manager.get_text('recording'))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['danger']};")

        self.recording_started.emit()

    def recording_loop(self):
        """录制循环（运行在工作线程里）

        cv2.VideoWriter 的创建、写帧、释放全部在本线程内完成：OpenCV 自带的
        FFmpeg 封装不是线程安全的，跨线程 release 会让进程直接 abort()
        （Windows 事件日志异常代码 0x40000015，故障模块 opencv_videoio_ffmpeg*.dll）。
        """
        writer = None
        try:
            writer = self._create_video_writer(self.output_file, self._cap_width, self._cap_height)
        except Exception as e:
            print(f"❌ 创建视频写入器异常: {e}")

        if writer is None:
            self.recording = False
            self.recording_error.emit(
                f"无法创建视频文件：\n{self.output_file}\n\n"
                f"请确认输出目录可写，或更换视频格式（当前：{self.format}）。"
            )
            return

        self.video_writer = writer
        try:
            while self.recording:
                # 累加有效录制时长（不含暂停），用于录制结束后校正视频帧率
                if self.last_active_tick > 0 and not self.paused:
                    self.recording_active_seconds += time.time() - self.last_active_tick
                self.last_active_tick = time.time()

                if not self.paused:
                    try:
                        if self._cap_mode == 'fullscreen':
                            from PIL import ImageGrab
                            img = ImageGrab.grab()
                            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        elif self._cap_mode == 'custom':
                            from PIL import ImageGrab
                            img = ImageGrab.grab(bbox=(0, 0, self._cap_width, self._cap_height))
                            frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                        elif self._cap_mode == 'follow_mouse':
                            from PIL import ImageGrab
                            area = self.mouse_tracker.get_tracking_area_around_cursor(
                                self._cap_width,
                                self._cap_height
                            )
                            if area:
                                x, y, w, h = area
                                img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                            else:
                                continue
                        else:
                            continue

                        if frame is not None and frame.size > 0:
                            frame = self.drawing_tool.apply_drawings(frame)
                            writer.write(frame)
                            self.frame_count += 1

                    except Exception as e:
                        print(f"Recording error: {e}")
                        continue

                QThread.msleep(int(1000 / self.fps))
        finally:
            # 释放必须与创建/写帧同线程（见方法开头说明），否则会 abort
            try:
                writer.release()
            except Exception as e:
                print(f"⚠️ 释放视频写入器失败: {e}")
            self.video_writer = None

    def pause_recording(self):
        """暂停录制"""
        self.paused = True
        if self.audio_recorder:
            self.audio_recorder.stop()
            self.audio_recorder.wait(3000)

        self.start_btn.setText(self.language_manager.get_text('resume_recording'))
        self.status_label.setText(self.language_manager.get_text('paused'))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['warning']};")
        self.recording_paused.emit()

    def resume_recording(self):
        """恢复录制"""
        self.paused = False

        if self.record_audio and self.enable_audio_check.isChecked():
            device_index = self.audio_device_combo.currentData()
            if device_index is not None and device_index >= 0:
                self.audio_recorder = AudioRecorderThread(device_index)
                self.audio_recorder.audio_data_signal.connect(self.on_audio_data)
                self.audio_recorder.error_signal.connect(self.on_audio_error)
                self.audio_recorder.start()
            else:
                print("❌ 未选择有效的音频输入设备，本次录制不包含声音")

        self.start_btn.setText(self.language_manager.get_text('pause_recording'))
        self.status_label.setText(self.language_manager.get_text('recording'))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['danger']};")
        self.recording_resumed.emit()

    def _on_recording_error(self, message):
        """录制线程无法创建视频文件时回到主线程：复位界面 + 弹窗"""
        self.recording = False
        self.video_writer = None
        try:
            self.start_btn.setText(self.language_manager.get_text('start_recording'))
            self.stop_btn.setEnabled(False)
            self.status_label.setText(self.language_manager.get_text('ready'))
        except Exception:
            pass
        QMessageBox.critical(self, "无法开始录制", message)

    def _set_saving_state(self, saving):
        """保存（FFmpeg 收尾）期间禁用录制按钮并更新状态文字，避免重复触发"""
        self._saving = bool(saving)
        try:
            if saving:
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(False)
                self.status_label.setText("正在保存视频…")
            else:
                self.start_btn.setEnabled(True)
        except Exception:
            pass

    def _run_with_busy_progress(self, message, task):
        """在保持界面响应的前提下执行耗时的 FFmpeg 收尾任务，返回 task() 的返回值

        静默原则：全程不弹任何对话框。进度直接显示在窗口内（状态栏文字 + 进度条），
        窗口已隐藏到托盘时则只更新托盘提示——用户在录屏/干别的事时不会被打断。
        主线程持续 processEvents()，所以窗口照常重绘、不会「无响应」被当成卡死。
        """
        try:
            self.status_label.setText(message)
            self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['accent']};")
            if hasattr(self, 'progress_bar'):
                self.progress_bar.setVisible(True)
        except Exception:
            pass
        self._update_tray_tooltip(f"Super Hi Vision — {message}")
        QApplication.processEvents()

        result: dict = {'value': None, 'error': None}

        def _worker():
            try:
                result['value'] = task()
            except Exception as e:  # 后台线程的异常带回主线程抛，避免静默失败
                result['error'] = e

        worker = threading.Thread(target=_worker, daemon=True)
        worker.start()
        try:
            while worker.is_alive():
                QApplication.processEvents()
                worker.join(0.05)
        finally:
            try:
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.setVisible(False)
            except Exception:
                pass
            QApplication.processEvents()

        if result['error'] is not None:
            raise result['error']
        return result['value']

    def stop_recording(self):
        """停止录制"""
        if not self.recording:
            return

        self.recording = False
        self.paused = False

        if self.timer:
            self.timer.stop()

        # 等录制线程退出：写入器的 release 由录制线程在退出前完成（同线程创建/写帧/释放，
        # 见 recording_loop 的说明），这里必须等它真正结束——既保证最后一帧写完，
        # 也保证文件已关闭后再交给 FFmpeg 处理。
        if self.recording_thread is not None:
            try:
                if self.recording_thread.isRunning():
                    self.recording_thread.wait(20000)
            except Exception:
                pass
        self.video_writer = None

        if self.audio_recorder:
            self.audio_recorder.stop()
            # 等待音频线程结束，确保所有音频帧已被收集
            self.audio_recorder.wait(3000)

        # 校正帧率 + 合并音视频都要跑 FFmpeg（可能数十秒）：放后台线程执行，
        # 主线程用进度对话框驱动事件循环，避免窗口「无响应」被当成卡死/打不开。
        # 保存阶段的任何异常都必须在这里就地消化——stop_recording 是按钮/热键的槽函数，
        # 让异常逃出槽函数会被 PyQt5 当成致命错误直接 abort()（进程当场消失）。
        self._set_saving_state(True)
        audio_merged = False
        save_error = None
        try:
            def _finalize():
                self.fix_video_playback_speed()
                if self.audio_frames and self.output_file:
                    return bool(self.merge_audio_video())
                return False

            audio_merged = bool(
                self._run_with_busy_progress("正在保存视频（校正帧率 / 合成音频），请稍候…", _finalize)
            )
        except Exception as e:
            save_error = e
            print(f"❌ 保存视频时出错: {e}")
        finally:
            self._set_saving_state(False)

        self.start_btn.setText(self.language_manager.get_text('start_recording'))
        self.stop_btn.setEnabled(False)
        self.status_label.setText(self.language_manager.get_text('ready'))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['success']};")

        self.recording_stopped.emit()

        # 结果校验：避免"录制完成"的提示掩盖 0 字节 / 损坏文件
        saved = bool(self.output_file) and os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0
        if not saved:
            QMessageBox.warning(
                self, "录制失败",
                "视频文件未能正常生成（文件不存在或为空）。\n"
                f"输出路径：{self.output_file}\n格式：{self.format}\n\n"
                "请更换视频格式（推荐 MP4）或确认输出目录可写后重试。"
            )
        elif save_error is not None:
            QMessageBox.warning(
                self, "保存过程出错",
                f"视频已保存：\n{self.output_file}\n\n"
                f"但保存流程（帧率校正 / 音频合成）出错：\n{save_error}\n\n"
                "若视频无声音或时长不对，请重试或改用 MP4 格式。"
            )
        elif self.record_audio and self.audio_frames and not audio_merged:
            # 区分「根本没找到 FFmpeg」和「FFmpeg 跑了但合并失败」，并给出可执行的下一步
            reason = (self._audio_merge_error or "").strip()
            if len(reason) > 400:
                reason = reason[-400:]
            sidecar = self._audio_sidecar
            lines = [f"视频已保存：{self.output_file}", ""]
            lines.append("但音频合成失败，这段视频暂时没有声音。")
            if sidecar:
                lines.append(f"✓ 音频已单独保存（不会丢）：\n{sidecar}")
            lines.append("")
            if self._find_ffmpeg():
                lines.append("原因（FFmpeg 报错）：")
                lines.append(reason if reason else "未知")
            else:
                expected = os.path.join(_app_dir(), "ffmpeg", "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
                lines.append("原因：未找到可用的 FFmpeg。")
                lines.append(f"请把 ffmpeg 文件夹（含 ffmpeg.exe）放到：\n{expected}")
                lines.append("或安装官方完整安装包（自带 FFmpeg）。")
            lines.append("")
            lines.append(f"详细日志：{_log_path()}")
            QMessageBox.warning(self, "有画面无声音", "\n".join(lines))
        else:
            # 静默完成：不弹窗，只在窗口内状态栏 + 托盘提示（「合成视频不弹窗」）
            file_name = os.path.basename(self.output_file) if self.output_file else ""
            self.status_label.setText(f"✅ 已保存 {file_name}")
            self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['success']};")
            self._update_tray_tooltip(f"Super Hi Vision — 已保存 {file_name}")
            print(f"✅ 视频已保存: {self.output_file}")

    def on_audio_data(self, data):
        """处理音频数据"""
        if self.recording and not self.paused:
            self.audio_frames.append(data)

    def on_audio_error(self, message):
        """音频录制错误处理"""
        print(f"❌ 音频录制错误: {message}")

    @staticmethod
    def _match_exe_in_dir(directory, exe_name):
        """在一个目录里判断 exe_name（忽略大小写）是否存在，存在则返回规范化路径。

        Windows 上文件名不区分大小写，用户（或某些下载/解压工具）磁盘上的文件可能叫
        ffmpeg.EXE、FFMPEG.EXE、Ffmpeg.Exe，而这里构造的候选路径固定写小写 ffmpeg.exe。
        `os.path.isfile()` 照样为真，但 `os.scandir` 拿到的 `entry.name` 保留磁盘上的
        原始拼写 —— 直接用它，界面就会显示 `...\\ffmpeg\\ffmpeg.EXE`，子进程命令行里
        也是这串大写拼写，换台机器显示还不一样。

        因此这里只把目录项当作「存在性证据」，返回的路径一律用 `exe_name` 的规范拼写
        拼出来，让显示与调用都稳定成小写。只在同一目录内比较，不递归。
        """
        want = exe_name.lower()
        try:
            entries = list(os.scandir(directory))
        except OSError:
            return None
        for entry in entries:
            try:
                if entry.is_file() and entry.name.lower() == want:
                    return os.path.join(directory, exe_name)
            except OSError:
                continue
        return None

    @classmethod
    def _canonical_exe(cls, path, exe_name):
        """把候选路径换成磁盘上的真实文件名。

        精确同名（仅大小写不同）优先；同目录下查无此名时，再宽容匹配
        「小写 exe_name 前缀 + .exe 后缀」的变体（用户解压后自行改名的情形），
        变体按文件名排序取第一个。找不到返回 None。
        """
        if not path:
            return None
        directory = os.path.dirname(path)
        real = cls._match_exe_in_dir(directory, exe_name)
        if real:
            return real
        if os.name != "nt":
            return None
        stem = os.path.splitext(exe_name)[0].lower()
        if not stem:
            return None
        try:
            entries = sorted(os.scandir(directory), key=lambda e: e.name)
        except OSError:
            return None
        for entry in entries:
            try:
                if entry.is_file():
                    low = entry.name.lower()
                    if low.startswith(stem) and low.endswith(".exe"):
                        return entry.path
            except OSError:
                continue
        return None

    @classmethod
    def _resolve_exe(cls, path, exe_name):
        """把「候选路径 / 裸命令名」解析成可交给子进程的规范路径。

        先按同名文件归一化（磁盘上是大写拼写也统一成规范小写），再退回 shutil.which；
        一路都拿不到时返回 None，因此可以用 `if not real` 判断「这个名字确实不存在」。
        """
        if not path:
            return None
        real = cls._canonical_exe(path, exe_name)
        if real:
            return real
        found = shutil.which(path)
        if not found:
            return None
        return cls._canonical_exe(found, exe_name) or found

    def _find_ffmpeg(self, name='ffmpeg'):
        """查找FFmpeg可执行文件

        注意：打包成单文件 exe 后 __file__ 指向 PyInstaller 的临时解包目录
        (_MEIPASS)，而不是程序所在目录，只按 __file__ 查找会漏掉随程序分发的
        <安装目录>\\ffmpeg\\ffmpeg.exe，导致音视频合并直接失败。这里按优先级
        枚举所有可能的落地点，并对候选做一次可执行性验证（避免命中损坏文件）。

        找到的结果会缓存（一次录制只探测一次），候选清单同时记进
        self.ffmpeg_candidates_tried，失败时用来说明「到底找过哪些地方」。
        """
        cache = self.__dict__.setdefault("_ffmpeg_cache", {})
        if name in cache:
            return cache[name] or None

        exe_name = name + ".exe" if os.name == "nt" else name
        candidates = []

        env_ffmpeg = os.environ.get("FFMPEG_BINARY")
        if env_ffmpeg:
            candidates.append(env_ffmpeg)

        # 1. 可执行文件所在目录（安装目录）、源码目录、当前工作目录
        search_dirs = []
        for probe in (getattr(sys, "executable", None), sys.argv[0] if sys.argv else None):
            if probe:
                try:
                    search_dirs.append(os.path.dirname(os.path.abspath(probe)))
                except Exception:
                    pass
        try:
            search_dirs.append(os.path.dirname(os.path.abspath(__file__)))
        except Exception:
            pass
        try:
            search_dirs.append(os.getcwd())
        except Exception:
            pass

        # 「安装包把 ffmpeg 放在安装目录」的各种可能布局都要覆盖：
        # <base>\ffmpeg\ffmpeg.exe、<base>\ffmpeg\bin\ffmpeg.exe、<base>\ffmpeg.exe、
        # <base>\bin\ffmpeg.exe、<base>\_internal\...
        subdirs = ["ffmpeg", os.path.join("ffmpeg", "bin"), "", "bin",
                   os.path.join("_internal", "ffmpeg"),
                   os.path.join("_internal", "ffmpeg", "bin"),
                   os.path.join("_internal", "bin"), "_internal"]
        for base in search_dirs:
            if not base:
                continue
            for sub in subdirs:
                candidates.append(os.path.join(base, sub, exe_name) if sub
                                  else os.path.join(base, exe_name))

        # 2b. 程序目录的「上一级」也看一眼（用户常把 exe 放在 ffmpeg 的子文件夹里）
        for base in list(search_dirs):
            if not base:
                continue
            parent = os.path.dirname(os.path.abspath(base))
            if parent and parent != base:
                candidates.append(os.path.join(parent, "ffmpeg", exe_name))
                candidates.append(os.path.join(parent, exe_name))

        # 1b. 单文件 exe 的内置副本（PyInstaller 解包到 _MEIPASS）：
        # 放在外置目录之后 —— 用户想在 exe 旁边放一个自备的 ffmpeg 覆盖内置版本时，
        # 外置的那个要优先被选中
        mei = getattr(sys, "_MEIPASS", None)
        if mei:
            candidates += [os.path.join(mei, "ffmpeg", exe_name),
                           os.path.join(mei, exe_name),
                           os.path.join(mei, "bin", exe_name)]

        # 3. 应用数据目录（用户手动丢进来的 ffmpeg）
        try:
            la = os.environ.get("LOCALAPPDATA")
            if la:
                for sub in ("SuperHiVision", "_MEI", ""):
                    candidates.append(os.path.join(la, sub, "ffmpeg", exe_name) if sub
                                      else os.path.join(la, exe_name))
                candidates.append(os.path.join(la, "SuperHiVision", "ffmpeg", exe_name))
        except Exception:
            pass

        # 4. 常见安装位置（含 winget / choco / scoop 默认落点）
        candidates += [
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\ffmpeg\ffmpeg.exe",
            r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
            os.path.expanduser(r"~\ffmpeg\bin\ffmpeg.exe"),
            os.path.expanduser(r"~\scoop\apps\ffmpeg\current\bin\ffmpeg.exe"),
            r"C:\ProgramData\chocolatey\bin\ffmpeg.exe",
            "/usr/bin/ffmpeg",
            "/usr/local/bin/ffmpeg",
        ]

        # 5. 注册表里 ffmpeg 自己登记的安装位置
        if os.name == "nt":
            try:
                import winreg
                for root, key in ((winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ffmpeg"),
                                  (winreg.HKEY_CURRENT_USER, r"SOFTWARE\ffmpeg")):
                    try:
                        with winreg.OpenKey(root, key) as k:
                            path, _ = winreg.QueryValueEx(k, "Path")
                            for leaf in (os.path.join(path, "bin", exe_name),
                                         os.path.join(path, exe_name)):
                                candidates.append(leaf)
                    except Exception:
                        continue
            except Exception:
                pass

        def use(path, via_path=False):
            """记下探测成功的位置并缓存，返回给调用方"""
            self.ffmpeg_candidates_tried = tried
            self._ffmpeg_cache[name] = path
            print(f"✅ FFmpeg 已定位{'（PATH）' if via_path else ''}: {path}")
            return path

        seen = set()
        tried = []
        for path in candidates:
            if not path or path in seen:
                continue
            seen.add(path)

            # 按磁盘上的真实拼写取出文件名（ffmpeg.EXE → ffmpeg.exe），
            # 顺带容忍同目录下用户改过名的变体；两者都没有才算未命中
            real = self._canonical_exe(path, exe_name)
            if not real:
                tried.append(path)
                continue
            if real not in seen:
                seen.add(real)
            tried.append(real)
            if not os.path.isfile(real):
                # 磁盘上确实没有这个名字（_canonical_exe 也可能返回目录内的
                # 改名变体，那种情况 isfile 为真，不走这里）
                continue
            if self._probe_ffmpeg(real):
                return use(real)

        # 6. 系统 PATH（最后兜底）
        for extra in (shutil.which(name), name):
            if not extra:
                continue
            # PATH 命中的可能是裸命令名，也可能已经在当前目录里解析成大写拼写，
            # 统一过一遍「真实文件名」再交给子进程，保证界面与命令行都稳定
            real = self._resolve_exe(extra, exe_name)
            if not real or real in seen:
                continue
            seen.add(real)
            tried.append(real)
            if os.path.isfile(real) and self._probe_ffmpeg(real):
                return use(real, via_path=True)

        self.ffmpeg_candidates_tried = tried
        self._ffmpeg_cache[name] = ""
        print(f"⚠️ 未找到可用的 FFmpeg（已尝试 {len(tried)} 个位置）")
        log_diagnostic("未找到可用的 FFmpeg，已尝试以下位置：" + chr(10) + chr(10).join("  " + t for t in tried))
        return None

    def ffmpeg_status_text(self):
        """给用户看的 FFmpeg 定位结果说明（失败时告诉他到底该把文件放哪）"""
        path = self._find_ffmpeg()
        if path:
            return f"FFmpeg 已就绪：{path}"
        expected = os.path.join(_app_dir(), "ffmpeg", "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        return ("未找到可用的 FFmpeg。\n"
                f"请把 ffmpeg 文件夹（含 ffmpeg.exe）放到：\n{expected}\n"
                f"或安装完整安装包（自带 FFmpeg）。\n详细日志：{_log_path()}")

    def ffmpeg_status_short(self):
        """一行式状态，用于设置在页面上常驻显示"""
        path = self._find_ffmpeg()
        if path:
            return f"✅ {path}"
        return ("❌ 未找到 FFmpeg —— 保存的视频会没有声音。\n"
                f"请把 ffmpeg 文件夹放到程序目录：{os.path.join(_app_dir(), 'ffmpeg')}")

    def on_check_ffmpeg(self):
        """「检查 FFmpeg」按钮：重新探测（清缓存）并给出结论"""
        self._ffmpeg_cache = {}
        text = self.ffmpeg_status_text()
        try:
            self.ffmpeg_status_label.setText(text.splitlines()[0])
        except Exception:
            pass
        print(f"🔎 FFmpeg 自检:\n{text}")
        QMessageBox.information(self, self.language_manager.get_text('check_ffmpeg'), text)

    def _write_temp_audio_wav(self):
        """把录制到的 PCM 帧写成一个 WAV。返回 (路径, 采样率, 声道数)，失败返回 None。

        单独抽出来是为了「FFmpeg 缺失 / 合并失败」时也能立刻把音频落地，
        不让用户录了半天的声音凭空消失。
        """
        try:
            if not self.audio_frames:
                return None
            temp_audio_file = os.path.join(self.temp_dir, "temp_audio.wav")
            if self.audio_recorder is not None:
                channels = getattr(self.audio_recorder, 'actual_channels', 1) or 1
                sample_rate = getattr(self.audio_recorder, 'actual_sample_rate', 44100) or 44100
            else:
                channels = 1
                sample_rate = 44100

            # 自动增益放大（解决音量过低），再交由 FFmpeg loudnorm 归一化到标准响度
            audio_data = _boost_audio_gain(b''.join(self.audio_frames))
            with wave.open(temp_audio_file, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(2)  # 16 位 PCM
                wf.setframerate(sample_rate)
                wf.writeframes(audio_data)

            if not os.path.exists(temp_audio_file) or os.path.getsize(temp_audio_file) == 0:
                return None
            return temp_audio_file, sample_rate, channels
        except Exception as e:
            print(f"❌ 写音频文件失败: {e}")
            log_diagnostic(f"写音频文件失败: {type(e).__name__}: {e}")
            return None

    def _salvage_audio(self, temp_audio_file):
        """合并失败时把音频另存为 <视频名>.audio.wav，尽量放在视频旁边。

        临时目录一般在 C:，而用户输出目录可能在 F:/D: —— 跨盘 os.replace 会抛
        WinError 17，所以用 shutil.move（自动退化成复制+删除）。输出目录不可写时
        退回用户主目录，总之不删源文件。
        """
        sidecar = os.path.splitext(self.output_file)[0] + ".audio.wav"
        saved = None
        for target in (sidecar, os.path.join(os.path.expanduser("~"), os.path.basename(sidecar))):
            try:
                if os.path.exists(target):
                    os.remove(target)
                shutil.move(temp_audio_file, target)
                saved = target
                break
            except Exception as e:
                print(f"⚠️ 音频另存到 {target} 失败: {e}")
        if saved:
            self._audio_sidecar = saved
            print(f"🔊 合并失败，音频已单独保存: {saved}")
            log_diagnostic("音频已单独保存到: " + saved)
            return saved
        print(f"⚠️ 音频未能另存，保留在临时目录: {temp_audio_file}")
        log_diagnostic("音频未能另存，保留在临时目录: " + temp_audio_file)
        return None

    @staticmethod
    def _probe_ffmpeg(cmd):
        """验证候选 ffmpeg 是否真的可执行"""
        try:
            result = subprocess.run(
                [cmd, "-version"], capture_output=True, text=True, timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            out = ((result.stdout or "") + (result.stderr or "")).lower()
            if result.returncode != 0 or "version" not in out:
                return False
            # ffmpeg -version / ffprobe -version / ffplay -version 的横幅文本各不相同
            # （分别是 "ffmpeg version" / "ffprobe version" / "ffplay version"），
            # 早期只认 "ffmpeg version" 会让 ffprobe/ffplay 的候选全部被判为不可用。
            base = os.path.basename(cmd).lower()
            return any(t in out for t in ("ffmpeg version", "ffprobe version", "ffplay version")) \
                or base.startswith(("ffmpeg", "ffprobe", "ffplay"))
        except Exception:
            return False

    def fix_video_playback_speed(self):
        """校正视频播放速度：按实际捕获帧率重设视频帧率（防止快放/慢放）

        视频写入器以目标FPS初始化，但实际捕获帧率往往低于目标值（屏幕抓取耗时等），
        导致视频文件帧数不足、播放时速度加快。此处根据 实际帧数/有效录制时长 计算
        真实帧率并用FFmpeg调整视频时间戳，使播放时长与真实录制时长一致：
        - 方式一：-itsscale 时间戳缩放 + 流复制（无损、不重新编码）
        - 方式二：输入端 -r 重新编码（精确，作为回退）
        """
        if not self.output_file or not os.path.exists(self.output_file):
            return

        ffmpeg_cmd_exe = self._find_ffmpeg()
        if not ffmpeg_cmd_exe:
            print("⚠️ FFmpeg不可用，无法校正视频帧率")
            return

        active_seconds = getattr(self, 'recording_active_seconds', 0.0)
        frame_count = getattr(self, 'frame_count', 0)
        if active_seconds <= 0 or frame_count <= 0:
            return

        actual_fps = frame_count / active_seconds
        target_fps = getattr(self, 'fps', 30)

        # 帧率差异小于阈值时无需校正
        if abs(actual_fps - target_fps) < 0.5:
            return

        print(f"🎞️ 校正视频帧率: 声明 {target_fps} FPS, 实际捕获 {actual_fps:.2f} FPS")

        try:
            base_name = os.path.splitext(self.output_file)[0]
            ext = os.path.splitext(self.output_file)[1]
            temp_corrected = base_name + "_fps_corrected" + ext

            # 时间戳缩放系数：目标播放时长 / 文件当前时长 = target_fps / actual_fps
            scale_factor = target_fps / actual_fps
            # 限幅：帧率统计异常（暂停/设备卡顿）时避免时间戳缩放失控
            scale_factor = max(0.05, min(scale_factor, 20.0))
            actual_fps_str = f"{actual_fps:.3f}"

            # MP4/MOV 加 faststart：把索引放到文件头，避免播放器打开即报错/卡住
            faststart = ['-movflags', '+faststart'] if ext.lower() in ('.mp4', '.mov', '.m4v') else []

            # 方式一：-itsscale 时间戳缩放 + 流复制（无损、快速）
            result = subprocess.run(
                [ffmpeg_cmd_exe, '-y', '-itsscale', f"{scale_factor:.6f}",
                 '-i', self.output_file, '-c:v', 'copy', '-an'] + faststart + [temp_corrected],
                capture_output=True, text=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )

            if result.returncode == 0 and os.path.exists(temp_corrected) and os.path.getsize(temp_corrected) > 0:
                os.remove(self.output_file)
                os.rename(temp_corrected, self.output_file)
                print(f"✅ 视频帧率校正完成(无损): {actual_fps:.2f} FPS")
                return

            # 方式二：缩放失败则重新编码校正（输入端 -r 重新生成时间戳）
            if os.path.exists(temp_corrected):
                os.remove(temp_corrected)
            print("⚠️ 时间戳缩放失败，尝试重新编码...")
            result = subprocess.run(
                [ffmpeg_cmd_exe, '-y', '-r', actual_fps_str,
                 '-i', self.output_file, '-c:v', 'libx264',
                 '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p', '-an'] + faststart + [temp_corrected],
                capture_output=True, text=True,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
            )

            if result.returncode == 0 and os.path.exists(temp_corrected) and os.path.getsize(temp_corrected) > 0:
                os.remove(self.output_file)
                os.rename(temp_corrected, self.output_file)
                print(f"✅ 视频帧率校正完成(重新编码): {actual_fps:.2f} FPS")
            else:
                if os.path.exists(temp_corrected):
                    os.remove(temp_corrected)
                print(f"❌ 视频帧率校正失败: {result.stderr[-300:]}")
        except Exception as e:
            print(f"❌ 视频帧率校正错误: {e}")

    def merge_audio_video(self):
        """合并音频和视频：将录制到的麦克风音频合成进视频文件

        返回 True 表示最终视频里确实带上了音频，False 表示合并失败或被跳过。
        """
        if not self.audio_frames or not self.output_file:
            print("⚠️ 音频帧为空或输出文件不存在，跳过音视频合并")
            return False

        # 先把 PCM 帧落成 WAV：即使 FFmpeg 缺失或合并失败，录到的音频也绝不丢
        prepared = self._write_temp_audio_wav()
        if not prepared:
            print("❌ 音频文件创建失败或为空，跳过音视频合并")
            return False
        temp_audio_file, sample_rate, channels = prepared

        ffmpeg_cmd_exe = self._find_ffmpeg()
        if not ffmpeg_cmd_exe:
            print("⚠️ FFmpeg不可用，跳过音视频合并（音频会单独保存）")
            self._audio_merge_error = "未找到可用的 FFmpeg"
            log_diagnostic("未找到 FFmpeg，无法合成音视频；音频将另存")
            self._salvage_audio(temp_audio_file)
            return False

        try:
            print(f"🔊 音频文件已创建: {os.path.getsize(temp_audio_file)} bytes")

            base_name = os.path.splitext(self.output_file)[0]
            ext = os.path.splitext(self.output_file)[1] or ".mp4"

            # 输出候选：优先视频所在目录；若 FFmpeg 在那里就是写不进去（目录权限、
            # 文件被占用、杀软/「受控文件夹访问」拦写等），就退到系统临时目录 ——
            # 那里程序刚刚成功写过 WAV，可用性是已知的。合成完再用 Python 搬过去
            # （Python 写目标目录这一步是验证过可行的，能绕开只拦子进程的限制）。
            primary_output = base_name + "_with_audio" + ext
            fallback_output = os.path.join(
                tempfile.gettempdir(),
                os.path.basename(base_name) + "_with_audio" + ext)
            output_candidates = [primary_output]
            if os.path.abspath(fallback_output) != os.path.abspath(primary_output):
                output_candidates.append(fallback_output)

            # MP4/MOV 加 faststart：把索引放到文件头，避免播放器打开即报错/卡顿
            faststart = ['-movflags', '+faststart'] if ext.lower() in ('.mp4', '.mov', '.m4v') else []

            # 音频处理链：降噪（可选）→ 响度归一化（解决声音太小/听不见）→ apad 补静音。
            # 逐级降级尝试（见下方 filter_variants），避免某个滤波器不可用就整段失败。
            denoise_chain = self._denoise_filter_chain()
            loudnorm_chain = ['loudnorm=I=-16:TP=-1.5:LRA=11', 'apad']
            filter_variants = [('降噪+响度归一化', ','.join(denoise_chain + loudnorm_chain))]
            if denoise_chain:
                filter_variants.append(('无降噪+响度归一化', ','.join(loudnorm_chain)))
            filter_variants.append(('不做音频处理', None))

            # 视频优先流复制（无损、快速）；容器不支持该编码时回退重新编码
            video_attempts = [
                ('流复制', ['-c:v', 'copy']),
                ('重新编码', ['-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p']),
            ]

            def build_cmd(video_opts, audio_filter=None, output_path=None):
                cmd = [ffmpeg_cmd_exe, '-y', '-i', self.output_file, '-i', temp_audio_file]
                cmd += video_opts
                cmd += ['-c:a', 'aac', '-b:a', '128k',
                        '-ar', str(sample_rate), '-ac', str(min(channels, 2))]
                if audio_filter:
                    cmd += ['-af', audio_filter]
                cmd += ['-shortest'] + faststart + [output_path or primary_output]
                return cmd

            merged = False
            last_err = ''
            used_output = None
            for temp_output in output_candidates:
                for label, video_opts in video_attempts:
                    for filter_label, audio_filter in filter_variants:
                        if os.path.exists(temp_output):
                            try:
                                os.remove(temp_output)
                            except Exception:
                                pass
                        print(f"🔄 正在合并音视频（{label} / {filter_label} → {temp_output}）...")
                        result = subprocess.run(
                            build_cmd(video_opts, audio_filter, temp_output),
                            capture_output=True, text=True,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                        )
                        if (result.returncode == 0 and os.path.exists(temp_output)
                                and os.path.getsize(temp_output) > 0):
                            merged = True
                            used_output = temp_output
                            print(f"✅ 音视频合并成功（{label} / {filter_label}）")
                            break
                        last_err = (result.stderr or '')[-500:]
                    if merged:
                        break
                if merged:
                    break

            if merged:
                try:
                    if os.path.exists(self.output_file):
                        os.remove(self.output_file)
                except Exception as e:
                    log_diagnostic(f"合并后删除原视频失败: {type(e).__name__}: {e}")
                try:
                    shutil.move(used_output, self.output_file)
                except Exception as e:
                    # 跨盘或目标被占用：退化为复制，绝不因此丢掉合成结果
                    log_diagnostic(f"移动合成结果失败({type(e).__name__}: {e})，改用复制")
                    shutil.copy2(used_output, self.output_file)
                    try:
                        os.remove(used_output)
                    except Exception:
                        pass
                self._audio_merge_error = None
                print(f"✅ 音视频合并完成: {self.output_file}")
            else:
                print(f"❌ 音视频合并失败: {last_err}")
                for leftover in output_candidates:
                    if os.path.exists(leftover):
                        try:
                            os.remove(leftover)
                        except Exception:
                            pass
                # 合并失败也绝不丢音频：把 WAV 落到视频旁边，用户装上 FFmpeg 后可再合成
                self._audio_merge_error = (last_err or "").strip() or "FFmpeg 返回错误"
                # 把可诊断的现场一并写进日志：试过哪些输出路径、目标目录当前是否可写。
                # 这样下次再出现「Permission denied」能一眼看出是目录侧还是 FFmpeg 侧。
                try:
                    probe = os.path.join(os.path.dirname(self.output_file), ".shv_write_probe")
                    with open(probe, "wb") as f:
                        f.write(b"x")
                    os.remove(probe)
                    dir_probe = "目标目录用 Python 可写（说明是被拦在子进程侧）"
                except Exception as e:
                    dir_probe = f"目标目录用 Python 也不可写: {type(e).__name__}: {e}"
                log_diagnostic(
                    "音视频合并失败，FFmpeg=" + str(ffmpeg_cmd_exe) +
                    chr(10) + "输出: " + str(self.output_file) +
                    chr(10) + "尝试过的输出路径: " + " | ".join(output_candidates) +
                    chr(10) + "目录探测: " + dir_probe +
                    chr(10) + "FFmpeg 错误尾部:" + chr(10) + self._audio_merge_error
                )
                saved = self._salvage_audio(temp_audio_file)
                temp_audio_kept = bool(saved)

            # 清理临时音频文件：仅在「合并成功」或「已另存成功」后删，
            # 否则保留现场（宁可留下临时 WAV，也不能丢用户的录音）
            if merged or locals().get('temp_audio_kept', False):
                try:
                    if os.path.exists(temp_audio_file):
                        os.remove(temp_audio_file)
                except Exception:
                    pass
            else:
                print(f"⚠️ 音频保留在临时目录: {temp_audio_file}")

            return merged

        except Exception as e:
            print(f"❌ 音视频合并错误: {e}")
            self._audio_merge_error = str(e)
            log_diagnostic(f"音视频合并异常: {type(e).__name__}: {e}")
            return False

    def take_screenshot(self):
        """截图"""
        try:
            from PIL import ImageGrab
            screenshot = ImageGrab.grab()
            filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.output_dir, filename)
            screenshot.save(filepath)
            QMessageBox.information(self, "Screenshot", f"Screenshot saved to:\n{filepath}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to take screenshot:\n{str(e)}")

    def update_recording_status(self):
        """更新录制状态"""
        if self.recording and self.recording_start_time:
            self.elapsed_time = int(time.time() - self.recording_start_time)
            hours = self.elapsed_time // 3600
            minutes = (self.elapsed_time % 3600) // 60
            seconds = self.elapsed_time % 60
            self.duration_label.setText(f"Duration: {hours:02d}:{minutes:02d}:{seconds:02d}")

            if os.path.exists(self.output_file):
                size_mb = os.path.getsize(self.output_file) / (1024 * 1024)
                self.file_size_label.setText(f"File Size: {size_mb:.1f} MB")

    def closeEvent(self, event):
        """关闭事件

        默认行为是「最小化到托盘、程序继续在后台运行」——关掉窗口不会中断录制，
        全局热键（F9/F10/F11/F12）依然有效；要真正退出请用托盘菜单的「退出」，
        或在高级设置里关掉托盘保活。
        """
        if (not self._force_quit) and self.minimize_to_tray and self._tray is not None:
            event.ignore()
            self.hide()
            self._notify_tray_once()
            self._update_tray_tooltip()
            return

        if self.recording:
            reply = QMessageBox.question(
                self, 'Confirm Exit',
                'Recording in progress. Are you sure you want to exit?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

            self.stop_recording()

        # 停止全局热键监听
        self._stop_global_hotkeys()

        # 关闭画图窗口
        if getattr(self, '_drawing_window', None) is not None:
            try:
                self._drawing_window.close()
            except Exception:
                pass

        if self._tray is not None:
            try:
                self._tray.hide()
            except Exception:
                pass

        shutil.rmtree(self.temp_dir, ignore_errors=True)
        event.accept()

    def change_hotkey(self, action):
        """修改热键"""
        dialog = HotkeyDialog(self, action, self.hotkeys[action])
        if dialog.exec_() == QDialog.Accepted:
            new_hotkey = dialog.get_hotkey()
            if new_hotkey:
                # 检查热键冲突
                if new_hotkey in self.hotkeys.values():
                    QMessageBox.warning(self, "Hotkey Conflict", "This hotkey is already in use!")
                    return
                
                self.hotkeys[action] = new_hotkey
                self.hotkey_buttons[action].setText(new_hotkey)
                self.save_hotkeys()
                self.update_global_hotkeys()

    def reset_hotkeys(self):
        """重置热键为默认值"""
        self.hotkeys = {
            'start_pause': 'F9',
            'stop': 'F10',
            'screenshot': 'F11',
            'drawing': 'F12'
        }
        for key, btn in self.hotkey_buttons.items():
            btn.setText(self.hotkeys[key])
        self.save_hotkeys()
        self.update_global_hotkeys()
        QMessageBox.information(self, "Reset", "Hotkeys have been reset to defaults")

    def update_global_hotkeys(self):
        """更新全局热键监听（pynput 后台线程 + 信号回到主线程）"""
        self._stop_global_hotkeys()

        if not PYNPUT_AVAILABLE:
            print("⚠️ pynput 不可用，全局热键已禁用（请 pip install pynput）")
            return

        try:
            kb = _pynput_keyboard

            def _norm_mod(key):
                """将左右修饰键归一化为 ctrl/alt/shift/win"""
                if key in (kb.Key.ctrl, kb.Key.ctrl_l, kb.Key.ctrl_r):
                    return 'ctrl'
                if key in (kb.Key.alt, kb.Key.alt_l, kb.Key.alt_r):
                    return 'alt'
                if key in (kb.Key.shift, kb.Key.shift_l, kb.Key.shift_r):
                    return 'shift'
                if key in (kb.Key.cmd, kb.Key.cmd_l, kb.Key.cmd_r):
                    return 'win'
                return None

            # 预解析热键配置 -> {action: (mods_set, key)}
            parsed = {}
            for action, hotkey_str in self.hotkeys.items():
                target = self._parse_hotkey_key(hotkey_str)
                if target is not None:
                    mods, key = target
                    parsed[action] = (set(mods), key)
                else:
                    print(f"⚠️ 热键格式无法解析，已跳过: {action} = {hotkey_str}")

            state = {'mods': set(), 'last_fire': 0.0}

            def on_press(key):
                try:
                    norm = _norm_mod(key)
                    if norm is not None:
                        state['mods'].add(norm)
                        return
                    now = time.time()
                    for action, (mods, target_key) in parsed.items():
                        if state['mods'] != mods:
                            continue
                        if self._hotkey_key_matches(key, target_key):
                            # 防抖：避免按住键重复触发
                            if now - state['last_fire'] > 0.35:
                                state['last_fire'] = now
                                self.hotkey_triggered.emit(action)
                            break
                except Exception as e:
                    print(f"热键处理错误: {e}")

            def on_release(key):
                norm = _norm_mod(key)
                if norm is not None:
                    state['mods'].discard(norm)

            self._hotkey_listener = kb.Listener(on_press=on_press, on_release=on_release)
            self._hotkey_listener.daemon = True
            self._hotkey_listener.start()
            print(f"✅ 全局热键监听已启动: {parsed}")
        except Exception as e:
            print(f"❌ 全局热键启动失败: {e}")

    def _parse_hotkey_key(self, hotkey_str):
        """解析 'Ctrl+Shift+F9' 之类的热键字符串 -> (mods, key) 或 None"""
        if not hotkey_str or not PYNPUT_AVAILABLE:
            return None
        kb = _pynput_keyboard
        parts = [p.strip() for p in hotkey_str.split('+')]
        mods = []
        for m in parts[:-1]:
            ml = m.lower()
            if ml == 'ctrl':
                mods.append('ctrl')
            elif ml == 'alt':
                mods.append('alt')
            elif ml == 'shift':
                mods.append('shift')
            elif ml == 'win':
                mods.append('win')
            else:
                return None
        key_part = parts[-1].strip()
        upper = key_part.upper()
        if len(upper) > 1 and upper[0] == 'F' and upper[1:].isdigit():
            n = int(upper[1:])
            if 1 <= n <= 24:
                return mods, getattr(kb.Key, f'f{n}')
        name_map = {
            'ESC': kb.Key.esc, 'TAB': kb.Key.tab, 'SPACE': kb.Key.space,
            'ENTER': kb.Key.enter, 'BACKSPACE': kb.Key.backspace,
            'DEL': kb.Key.delete, 'DELETE': kb.Key.delete, 'INSERT': kb.Key.insert,
            'HOME': kb.Key.home, 'END': kb.Key.end, 'PAGEUP': kb.Key.page_up,
            'PAGEDOWN': kb.Key.page_down, 'LEFT': kb.Key.left, 'RIGHT': kb.Key.right,
            'UP': kb.Key.up, 'DOWN': kb.Key.down,
        }
        if upper in name_map:
            return mods, name_map[upper]
        if len(key_part) == 1 and key_part.isalnum():
            return mods, kb.KeyCode.from_char(key_part.lower())
        return None

    def _hotkey_key_matches(self, event_key, target_key):
        """比较按键是否匹配（兼容大小写/左右修饰键）"""
        if not PYNPUT_AVAILABLE:
            return False
        kb = _pynput_keyboard
        if isinstance(target_key, kb.Key):
            return event_key == target_key
        try:
            if hasattr(event_key, 'char') and event_key.char and hasattr(target_key, 'char'):
                return event_key.char.lower() == target_key.char.lower()
        except Exception:
            pass
        return False

    def _stop_global_hotkeys(self):
        """停止全局热键监听器"""
        listener = getattr(self, '_hotkey_listener', None)
        if listener is not None:
            try:
                listener.stop()
            except Exception:
                pass
            self._hotkey_listener = None

    def _on_hotkey_triggered(self, action):
        """主线程处理热键动作"""
        try:
            if action == 'start_pause':
                self.toggle_recording()
            elif action == 'stop':
                self.stop_recording()
            elif action == 'screenshot':
                self.take_screenshot()
            elif action == 'drawing':
                self.open_drawing_tool()
        except Exception as e:
            print(f"❌ 热键动作执行失败 [{action}]: {e}")

    def open_drawing_tool(self):
        """打开/切换画图工具窗口"""
        try:
            if self._drawing_window is None:
                self._drawing_window = DrawingWindow(self.drawing_tool)
                self._drawing_window.setAttribute(Qt.WA_DeleteOnClose, False)
            if self._drawing_window.isVisible():
                self._drawing_window.hide()
            else:
                self._drawing_window.show()
                self._drawing_window.raise_()
                self._drawing_window.activateWindow()
        except Exception as e:
            print(f"❌ 打开画图工具失败: {e}")

# ==================== 画图工具窗口（PyQt） ====================
class DrawingWindow(QWidget):
    """画图工具控制面板：配置画笔/矩形/圆形、颜色、粗细，清除叠加绘制"""
    def __init__(self, drawing_tool, parent=None):
        super().__init__(parent)
        self.drawing_tool = drawing_tool
        self.setWindowTitle("🎨 画图工具")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.resize(320, 360)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # 工具选择
        tool_group = QGroupBox("工具")
        tool_layout = QHBoxLayout()
        self.tool_btns = {}
        for text, value in [("画笔", "pen"), ("矩形", "rectangle"), ("圆形", "circle")]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(value == self.drawing_tool.current_tool)
            btn.clicked.connect(lambda checked, v=value: self._set_tool(v))
            self.tool_btns[value] = btn
            tool_layout.addWidget(btn)
        tool_group.setLayout(tool_layout)
        layout.addWidget(tool_group)

        # 颜色选择
        color_group = QGroupBox("颜色")
        color_layout = QHBoxLayout()
        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self._update_color_preview()
        color_layout.addWidget(self.color_preview)
        color_btn = QPushButton("选择颜色")
        color_btn.clicked.connect(self._choose_color)
        color_layout.addWidget(color_btn)
        color_layout.addStretch()
        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # 线条粗细
        thickness_group = QGroupBox("线条粗细")
        thick_layout = QVBoxLayout()
        self.thickness_label = QLabel(f"粗细: {self.drawing_tool.current_thickness}")
        self.thickness_slider = QSlider(Qt.Horizontal)
        self.thickness_slider.setRange(1, 20)
        self.thickness_slider.setValue(self.drawing_tool.current_thickness)
        self.thickness_slider.valueChanged.connect(self._set_thickness)
        self.thickness_slider.valueChanged.connect(
            lambda v: self.thickness_label.setText(f"粗细: {v}"))
        thick_layout.addWidget(self.thickness_label)
        thick_layout.addWidget(self.thickness_slider)
        thickness_group.setLayout(thick_layout)
        layout.addWidget(thickness_group)

        # 控制按钮
        control_group = QGroupBox("控制")
        control_layout = QVBoxLayout()
        clear_btn = QPushButton("清除所有")
        clear_btn.setStyleSheet("background-color: #e74c3c; color: white; font-weight: bold;")
        clear_btn.clicked.connect(self.drawing_tool.clear_all)
        control_layout.addWidget(clear_btn)
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)

        layout.addStretch()

    def _set_tool(self, tool):
        self.drawing_tool.set_tool(tool)
        for value, btn in self.tool_btns.items():
            btn.setChecked(value == tool)

    def _choose_color(self):
        from PyQt5.QtWidgets import QColorDialog
        r, g, b = self.drawing_tool.current_color
        color = QColorDialog.getColor(QColor(r, g, b), self, "选择颜色")
        if color.isValid():
            self.drawing_tool.set_color((color.red(), color.green(), color.blue()))
            self._update_color_preview()

    def _update_color_preview(self):
        r, g, b = self.drawing_tool.current_color
        self.color_preview.setStyleSheet(
            f"background-color: rgb({r},{g},{b}); border: 1px solid #888888;")

    def _set_thickness(self, value):
        self.drawing_tool.set_thickness(value)

# ==================== 热键设置对话框 ====================
class HotkeyDialog(QDialog):
    """热键设置对话框"""
    def __init__(self, parent, action, current_hotkey):
        super().__init__(parent)
        self.setWindowTitle("Set Hotkey")
        self.resize(300, 150)
        
        self.new_hotkey = None
        self.action = action
        
        layout = QVBoxLayout()
        
        self.label = QLabel(f"Press a key combination for:\n{action}")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        self.current_label = QLabel(f"Current: {current_hotkey}")
        self.current_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.current_label)
        
        self.press_label = QLabel("Press any key...")
        self.press_label.setAlignment(Qt.AlignCenter)
        self.press_label.setStyleSheet("color: #e94560; font-weight: bold;")
        layout.addWidget(self.press_label)
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        self.grabKeyboard()

    def keyPressEvent(self, event):
        """键盘事件处理"""
        key = event.key()
        modifiers = event.modifiers()
        
        key_text = ""
        
        if modifiers & Qt.ControlModifier:
            key_text += "Ctrl+"
        if modifiers & Qt.AltModifier:
            key_text += "Alt+"
        if modifiers & Qt.ShiftModifier:
            key_text += "Shift+"
        if modifiers & Qt.MetaModifier:
            key_text += "Win+"
        
        key_names = {
            Qt.Key_F1: 'F1', Qt.Key_F2: 'F2', Qt.Key_F3: 'F3', Qt.Key_F4: 'F4',
            Qt.Key_F5: 'F5', Qt.Key_F6: 'F6', Qt.Key_F7: 'F7', Qt.Key_F8: 'F8',
            Qt.Key_F9: 'F9', Qt.Key_F10: 'F10', Qt.Key_F11: 'F11', Qt.Key_F12: 'F12',
            Qt.Key_Escape: 'Esc', Qt.Key_Tab: 'Tab', Qt.Key_Backspace: 'Backspace',
            Qt.Key_Return: 'Enter', Qt.Key_Space: 'Space', Qt.Key_Delete: 'Del',
            Qt.Key_Insert: 'Insert', Qt.Key_Home: 'Home', Qt.Key_End: 'End',
            Qt.Key_PageUp: 'PageUp', Qt.Key_PageDown: 'PageDown',
            Qt.Key_Left: 'Left', Qt.Key_Right: 'Right', Qt.Key_Up: 'Up', Qt.Key_Down: 'Down'
        }
        
        if key in key_names:
            key_text += key_names[key]
        elif key >= Qt.Key_0 and key <= Qt.Key_9:
            key_text += str(key - Qt.Key_0)
        elif key >= Qt.Key_A and key <= Qt.Key_Z:
            key_text += chr(key).upper()
        else:
            return
        
        self.new_hotkey = key_text
        self.press_label.setText(f"Selected: {key_text}")

    def get_hotkey(self):
        """获取新热键"""
        return self.new_hotkey

# ==================== 主程序入口 ====================
# 单实例通讯名：第二个实例启动时通过本机命名管道通知已有实例「把窗口唤到前台」，
# 解决「程序还在后台跑，再点桌面图标却打不开（看不到窗口）」的问题。
INSTANCE_SERVER_NAME = "SuperHiVision_SingleInstance_v1"


def _notify_running_instance():
    """若已有实例在运行，通知它显示窗口并返回 True"""
    try:
        sock = QLocalSocket()
        sock.connectToServer(INSTANCE_SERVER_NAME)
        if sock.waitForConnected(500):
            sock.write(b"SHOW")
            sock.flush()
            sock.waitForBytesWritten(500)
            # 等一小会儿再断开：立刻 disconnect 时，对端可能先看到「断开」而
            # 来不及读到管道里剩下的消息，导致窗口唤不起来。
            try:
                sock.waitForReadyRead(300)
            except Exception:
                pass
            try:
                sock.disconnectFromServer()
            except Exception:
                pass
            return True
    except Exception:
        pass
    return False


def _create_instance_server(window):
    """注册单实例服务；收到第二个实例的消息时唤起窗口"""
    try:
        # 上次异常退出（崩溃 / 强杀）可能残留服务名，先清掉
        try:
            QLocalServer.removeServer(INSTANCE_SERVER_NAME)
        except Exception:
            pass
        server = QLocalServer()
        if not server.listen(INSTANCE_SERVER_NAME):
            print(f"⚠️ 单实例服务注册失败（{server.errorString()}），程序仍可正常使用")
            return None

        def _on_new_connection():
            try:
                conn = server.nextPendingConnection()
                if conn is None:
                    return
                state = {'handled': False, 'text': ''}

                def _try_read(*_args):
                    """多次机会读取消息：readyRead / 定时重试 / 断开前最后一次"""
                    if state['handled']:
                        return
                    try:
                        chunk = bytes(conn.readAll()).decode('utf-8', 'replace')
                    except Exception:
                        chunk = ''
                    if chunk.strip():
                        state['text'] += chunk
                        state['handled'] = True
                        window.handle_instance_message(state['text'])
                        print("ℹ️ 收到第二个实例的唤醒请求，已显示窗口")

                def _on_disconnected():
                    _try_read()  # 断开前把管道里剩下的数据读干净
                    try:
                        conn.deleteLater()
                    except Exception:
                        pass

                conn.readyRead.connect(_try_read)
                conn.disconnected.connect(_on_disconnected)
                for delay in (0, 150, 400, 900):
                    QTimer.singleShot(delay, _try_read)
            except Exception as e:
                print(f"⚠️ 处理单实例消息失败: {e}")

        server.newConnection.connect(_on_new_connection)
        window._instance_server = server
        return server
    except Exception as e:
        print(f"⚠️ 单实例服务初始化失败: {e}")
        return None


def main():
    print("=" * 60)
    print("Super Hi Vision - Advanced HD Screen Recording Tool")
    print(f"Version: {__version__}")
    print(f"Team: {__team__}")
    print(f"Copyright: {__copyright__}")
    print(f"Website: {__website__}")
    print("=" * 60)

    app = QApplication(sys.argv)
    app.setApplicationName("Super Hi Vision")
    app.setApplicationVersion(__version__)
    app.setWindowIcon(_load_app_icon())

    # 已经有实例在跑（可能在托盘里）→ 唤醒它，然后本进程直接退出，
    # 而不是再开一个「看不见的窗口」或静默失败。
    if _notify_running_instance():
        print("ℹ️ 程序已在运行，已请求显示窗口（本进程退出）")
        return 0

    # 托盘保活期间窗口被隐藏，不能因为「没有可见窗口」就自己退出
    if QSystemTrayIcon.isSystemTrayAvailable():
        app.setQuitOnLastWindowClosed(False)

    translator = QTranslator(app)
    locale = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    app.installTranslator(translator)

    window = ScreenRecorderApp()
    _create_instance_server(window)
    window.show()

    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())