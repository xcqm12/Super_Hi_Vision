#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Hi Vision - 高级超高清屏幕录制工具 (PyQt5现代化版本)
版本: 1.5.10
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
    print("\n[ERROR] 程序无法启动，PyQt5 依赖不可用！")
    print("请确保已安装 Python 和 pip，然后运行:")
    print("  pip install PyQt5")
    input("\n按回车键退出...")
    sys.exit(1)

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit, QGroupBox, QRadioButton, QCheckBox, QTabWidget,
    QFileDialog, QMessageBox, QProgressBar, QFrame, QScrollArea,
    QSplitter, QStatusBar, QSizePolicy, QSlider, QDialog,
    QDialogButtonBox, QTextEdit, QGridLayout, QStyleFactory,
    QSystemTrayIcon, QMenu, QAction, QToolButton
)
from PyQt5.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPoint, QRect,
    QObject, QEvent, QCoreApplication, QTranslator, QLibraryInfo
)
from PyQt5.QtGui import (
    QFont, QColor, QPalette, QBrush, QLinearGradient, QPainter,
    QIcon, QPixmap, QCursor, QFontDatabase, QKeySequence
)

import subprocess
import platform
import cv2
import numpy as np
import pyaudio
import wave
import shutil

# ==================== 版本和版权信息 ====================
__author__ = "QLM Network Entertainment Technology Co., Ltd."
__copyright__ = "Copyright 2019-2025, QLM Network Entertainment Technology Co., Ltd."
__version__ = "1.5.10"
__license__ = "MIT"
__email__ = "qlm@qlm.org.cn"
__website__ = "https://team.qlm.org.cn"
__team__ = "SevenZeroMeowTeam"

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

# ==================== 音频录制线程 ====================
class AudioRecorderThread(QThread):
    """音频录制线程"""
    audio_data_signal = pyqtSignal(bytes)
    error_signal = pyqtSignal(str)

    def __init__(self, device_index, sample_rate=44100, channels=2, chunk_size=1024):
        super().__init__()
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.running = False
        self.audio = None

    def run(self):
        """开始录制"""
        self.running = True
        try:
            self.audio = pyaudio.PyAudio()
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk_size
            )

            while self.running:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_data_signal.emit(data)
                except Exception as e:
                    if self.running:
                        self.error_signal.emit(str(e))
                    break

            stream.stop_stream()
            stream.close()
            self.audio.terminate()
        except Exception as e:
            self.error_signal.emit(str(e))

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

    def __init__(self):
        super().__init__()
        self.recording = False
        self.paused = False
        self.video_writer = None
        self.mouse_tracker = MouseTracker()
        self.drawing_tool = DrawingTool()
        self.audio_recorder = None
        self.audio_frames = []
        self.audio_enabled = False
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

        self.theme_manager = ThemeManager()
        self.language_manager = LanguageManager()

        self.audio_devices = []
        self.audio_device_index = None
        self.record_audio = True

        # 热键配置
        self.hotkeys = {
            'start_pause': 'F9',
            'stop': 'F10',
            'screenshot': 'F11',
            'drawing': 'F12'
        }
        self.load_hotkeys()

        self.init_audio_devices()
        self.init_ui()
        self.apply_theme()

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

    def init_audio_devices(self):
        """初始化音频设备"""
        try:
            p = pyaudio.PyAudio()
            self.audio_devices = []

            for i in range(p.get_device_count()):
                dev_info = p.get_device_info_by_index(i)
                if dev_info.get('maxInputChannels', 0) > 0:
                    self.audio_devices.append({
                        'index': i,
                        'name': dev_info.get('name', f'Device {i}')
                    })

            p.terminate()

            if self.audio_devices:
                self.audio_device_index = self.audio_devices[0]['index']
        except Exception as e:
            print(f"Audio device init error: {e}")

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
        self.create_status_bar(main_layout)

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
        self.theme_combo.addItems(['Dark', 'Light', 'Ocean', 'Sunset', 'Forest', 'Purple'])
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
        else:
            self.audio_device_combo.addItem("No audio device available", -1)
        device_layout.addWidget(self.audio_device_combo)

        self.test_audio_btn = QPushButton(self.language_manager.get_text('test_audio'))
        self.test_audio_btn.clicked.connect(self.test_audio)
        device_layout.addWidget(self.test_audio_btn)

        audio_layout.addLayout(device_layout)
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

    def test_audio(self):
        """测试音频"""
        QMessageBox.information(self, "Test Audio", "Audio test functionality")

    def change_theme(self, theme_name):
        """改变主题"""
        theme_map = {
            'Dark': 'dark',
            'Light': 'light',
            'Ocean': 'ocean',
            'Sunset': 'sunset',
            'Forest': 'forest',
            'Purple': 'purple'
        }
        theme_key = theme_map.get(theme_name, 'dark')
        self.theme_manager.set_theme(theme_key)
        self.apply_theme()

    def apply_theme(self):
        """应用主题"""
        theme = self.theme_manager.get_theme()
        style_sheet = self.theme_manager.generate_style_sheet()
        self.setStyleSheet(style_sheet)

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

    def start_recording(self):
        """开始录制"""
        if self.recording:
            return

        self.recording = True
        self.paused = False
        self.frame_count = 0
        self.audio_frames = []
        self.recording_start_time = time.time()

        output_filename = self.filename_edit.text()
        if not output_filename:
            output_filename = f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.output_file = os.path.join(self.output_dir, f"{output_filename}.{self.format.lower()}")

        fourcc_map = {
            'MP4': cv2.VideoWriter_fourcc(*'mp4v'),
            'AVI': cv2.VideoWriter_fourcc(*'XVID'),
            'MKV': cv2.VideoWriter_fourcc(*'X264'),
            'FLV': cv2.VideoWriter_fourcc(*'FLV1'),
            'MOV': cv2.VideoWriter_fourcc(*'avc1')
        }
        fourcc = fourcc_map.get(self.format, cv2.VideoWriter_fourcc(*'mp4v'))

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

        self.video_writer = cv2.VideoWriter(self.output_file, fourcc, self.fps, (width, height))

        if self.record_audio and self.enable_audio_check.isChecked():
            device_index = self.audio_device_combo.currentData()
            if device_index >= 0:
                self.audio_recorder = AudioRecorderThread(device_index)
                self.audio_recorder.audio_data_signal.connect(self.on_audio_data)
                self.audio_recorder.start()

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
        """录制循环"""
        while self.recording:
            if not self.paused:
                try:
                    if self.area_mode == 'fullscreen':
                        from PIL import ImageGrab
                        img = ImageGrab.grab()
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    elif self.area_mode == 'custom':
                        from PIL import ImageGrab
                        x, y = 0, 0
                        w = self.width_spin.value()
                        h = self.height_spin.value()
                        img = ImageGrab.grab(bbox=(x, y, w, h))
                        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                    elif self.area_mode == 'follow_mouse':
                        from PIL import ImageGrab
                        area = self.mouse_tracker.get_tracking_area_around_cursor(
                            self.follow_width_spin.value(),
                            self.follow_height_spin.value()
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
                        self.video_writer.write(frame)
                        self.frame_count += 1

                except Exception as e:
                    print(f"Recording error: {e}")
                    continue

            QThread.msleep(int(1000 / self.fps))

    def pause_recording(self):
        """暂停录制"""
        self.paused = True
        if self.audio_recorder:
            self.audio_recorder.stop()

        self.start_btn.setText(self.language_manager.get_text('resume_recording'))
        self.status_label.setText(self.language_manager.get_text('paused'))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['warning']};")
        self.recording_paused.emit()

    def resume_recording(self):
        """恢复录制"""
        self.paused = False

        if self.record_audio and self.enable_audio_check.isChecked():
            device_index = self.audio_device_combo.currentData()
            if device_index >= 0:
                self.audio_recorder = AudioRecorderThread(device_index)
                self.audio_recorder.audio_data_signal.connect(self.on_audio_data)
                self.audio_recorder.start()

        self.start_btn.setText(self.language_manager.get_text('pause_recording'))
        self.status_label.setText(self.language_manager.get_text('recording'))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['danger']};")
        self.recording_resumed.emit()

    def stop_recording(self):
        """停止录制"""
        if not self.recording:
            return

        self.recording = False
        self.paused = False

        if self.timer:
            self.timer.stop()

        if self.audio_recorder:
            self.audio_recorder.stop()

        if self.video_writer:
            self.video_writer.release()

        if self.audio_frames and self.output_file:
            self.merge_audio_video()

        self.start_btn.setText(self.language_manager.get_text('start_recording'))
        self.stop_btn.setEnabled(False)
        self.status_label.setText(self.language_manager.get_text('ready'))
        self.status_label.setStyleSheet(f"color: {self.theme_manager.get_theme()['success']};")

        self.recording_stopped.emit()

        QMessageBox.information(self, "Recording Complete", f"Video saved to:\n{self.output_file}")

    def on_audio_data(self, data):
        """处理音频数据"""
        if self.recording and not self.paused:
            self.audio_frames.append(data)

    def merge_audio_video(self):
        """合并音频和视频"""
        pass

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
        """关闭事件"""
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
        """更新全局热键监听"""
        pass

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

    translator = QTranslator(app)
    locale = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    app.installTranslator(translator)

    window = ScreenRecorderApp()
    window.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()