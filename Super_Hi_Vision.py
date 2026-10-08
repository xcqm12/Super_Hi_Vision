import os
import sys
import time
import threading
import subprocess
import tempfile
import platform
import shutil
import json
import re
from datetime import datetime
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import cv2
import numpy as np
import wave
import pyaudio

# MIT License
# Copyright (c) 2019-2025 七零喵网络互娱科技有限公司
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# 版权信息
__author__ = "七零喵网络互娱科技有限公司"
__copyright__ = "Copyright 2019-2025, 七零喵网络互娱科技有限公司"
__version__ = "1.5.24"  # 应用图标
__license__ = "MIT"
__email__ = "qlm@qlm.org.cn"
__website__ = "https://team.qlm.org.cn"
__team__ = "SevenZeroMeowTeam"

print("=" * 60)
print("🎬 高级超高清屏幕录制工具 - 优化版")
print(f"📝 版本: {__version__}")
print(f"👥 开发团队: {__team__}")
print(f"🏢 版权所有: {__copyright__}")
print(f"🌐 官方网站: {__website__}")
print("=" * 60)

# 音频支持状态
AUDIO_SUPPORT = False
PYAUDIO_AVAILABLE = False
FFMPEG_AVAILABLE = False


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

# 国内镜像源列表
MIRROR_SOURCES = [
    {
        "name": "清华源",
        "url": "https://pypi.tuna.tsinghua.edu.cn/simple/",
        "trusted_host": "pypi.tuna.tsinghua.edu.cn"
    },
    {
        "name": "阿里源",
        "url": "https://mirrors.aliyun.com/pypi/simple/",
        "trusted_host": "mirrors.aliyun.com"
    },
    {
        "name": "华为源",
        "url": "https://repo.huaweicloud.com/repository/pypi/simple/",
        "trusted_host": "repo.huaweicloud.com"
    },
    {
        "name": "腾讯源",
        "url": "https://mirrors.cloud.tencent.com/pypi/simple/",
        "trusted_host": "mirrors.cloud.tencent.com"
    },
    {
        "name": "豆瓣源",
        "url": "https://pypi.douban.com/simple/",
        "trusted_host": "pypi.douban.com"
    },
    {
        "name": "中科大源",
        "url": "https://pypi.mirrors.ustc.edu.cn/simple/",
        "trusted_host": "pypi.mirrors.ustc.edu.cn"
    }
]

# 新增：支持的视频格式和对应的扩展名与MIME类型
SUPPORTED_FORMATS = {
    "MP4": {"ext": "mp4", "mime": "video/mp4", "fourcc": "mp4v"},
    "AVI": {"ext": "avi", "mime": "video/x-msvideo", "fourcc": "XVID"},
    "MKV": {"ext": "mkv", "mime": "video/x-matroska", "fourcc": "X264"},
    "FLV": {"ext": "flv", "mime": "video/x-flv", "fourcc": "FLV1"},
    "MOV": {"ext": "mov", "mime": "video/quicktime", "fourcc": "avc1"}
}

# 新增：支持的视频编码器
SUPPORTED_CODECS = {
    "H.264 (libx264)": "libx264",
    "H.265/HEVC (libx265)": "libx265",
    "MPEG-4 (mpeg4)": "mpeg4",
    "VP8 (libvpx)": "libvpx",
    "VP9 (libvpx-vp9)": "libvpx-vp9",
    "AV1 (libaom-av1)": "libaom-av1"
}

# 新增：FPS选项
FPS_OPTIONS = {
    "10 FPS (低功耗)": 10,
    "15 FPS (流畅)": 15,
    "24 FPS (电影)": 24,
    "30 FPS (标准)": 30,
    "45 FPS (流畅)": 45,
    "60 FPS (高清)": 60,
    "90 FPS (超流畅)": 90,
    "120 FPS (电竞)": 120
}

# 新增：录制质量配置，包括蓝光选项
QUALITY_PRESETS = {
    "low": {"fps": 15, "bitrate": "500k", "crf": 30},
    "medium": {"fps": 30, "bitrate": "2000k", "crf": 25},
    "high": {"fps": 30, "bitrate": "5000k", "crf": 20},
    "ultra": {"fps": 60, "bitrate": "10000k", "crf": 18},
    "bluray": {"fps": 60, "bitrate": "25000k", "crf": 15}  # 蓝光配置
}

# 新增：性能优化配置
PERFORMANCE_OPTIONS = {
    "low": {"compression": 0.7, "sleep_factor": 0.8, "frame_skip": 1},
    "medium": {"compression": 0.8, "sleep_factor": 0.6, "frame_skip": 0},
    "high": {"compression": 0.9, "sleep_factor": 0.4, "frame_skip": 0},
    "ultra": {"compression": 1.0, "sleep_factor": 0.2, "frame_skip": 0}
}

def check_audio_environment():
    """检查音频环境并自动修复"""
    global AUDIO_SUPPORT, PYAUDIO_AVAILABLE, FFMPEG_AVAILABLE
    
    print("🔊 检查音频环境...")
    
    # 检查PyAudio
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        device_count = p.get_device_count()
        print(f"✅ PyAudio 可用 - 找到 {device_count} 个音频设备")
        PYAUDIO_AVAILABLE = True
        
        # 检查是否有可用的输入设备
        input_devices = []
        for i in range(device_count):
            dev_info = p.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels', 0) > 0:
                input_devices.append(dev_info)
        
        if not input_devices:
            print("❌ 未找到可用的音频输入设备")
            PYAUDIO_AVAILABLE = False
        else:
            print(f"✅ 找到 {len(input_devices)} 个可用的音频输入设备")
            
        p.terminate()
    except ImportError:
        print("❌ PyAudio 未安装，尝试自动安装...")
        if install_pyaudio():
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                device_count = p.get_device_count()
                print(f"✅ PyAudio 安装成功 - 找到 {device_count} 个音频设备")
                PYAUDIO_AVAILABLE = True
                p.terminate()
            except Exception as e:
                print(f"❌ PyAudio 安装后仍然不可用: {e}")
        else:
            print("❌ PyAudio 自动安装失败，音频录制功能不可用")
    except Exception as e:
        print(f"❌ PyAudio 检测失败: {e}")
    
    # 检查FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ FFmpeg 可用")
            FFMPEG_AVAILABLE = True
        else:
            print("❌ FFmpeg 未正确安装")
    except:
        print("❌ FFmpeg 未安装，尝试自动安装...")
        if install_ffmpeg():
            FFMPEG_AVAILABLE = True
            print("✅ FFmpeg 安装成功")
        else:
            print("❌ FFmpeg 自动安装失败")
    
    AUDIO_SUPPORT = PYAUDIO_AVAILABLE and FFMPEG_AVAILABLE
    
    if AUDIO_SUPPORT:
        print("🎵 音频环境完整支持!")
    else:
        print("🔇 音频环境不完整，部分功能受限")
    
    return AUDIO_SUPPORT

def install_pyaudio():
    """自动安装PyAudio"""
    print("正在安装PyAudio...")
    
    # 尝试使用多个镜像源安装
    for mirror in MIRROR_SOURCES:
        try:
            print(f"尝试使用{mirror['name']}安装PyAudio...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "PyAudio", "-i", mirror['url'],
                "--trusted-host", mirror['trusted_host'],
                "--timeout", "60"
            ])
            print(f"✅ 使用{mirror['name']}安装PyAudio成功")
            return True
        except Exception as e:
            print(f"❌ 使用{mirror['name']}安装PyAudio失败: {e}")
            continue
    
    # 如果所有镜像源都失败，尝试直接安装
    try:
        print("尝试直接安装PyAudio...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyAudio"])
        print("✅ PyAudio 安装成功")
        return True
    except subprocess.CalledProcessError:
        print("❌ PyAudio 安装失败")
        return False

def install_ffmpeg():
    """自动安装FFmpeg"""
    print("正在安装FFmpeg...")
    
    try:
        if platform.system() == "Windows":
            return install_ffmpeg_windows()
        elif platform.system() == "Darwin":
            return install_ffmpeg_macos()
        else:
            return install_ffmpeg_linux()
    except Exception as e:
        print(f"FFmpeg安装失败: {e}")
        return False

def install_ffmpeg_windows():
    """在Windows上安装FFmpeg"""
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        ffmpeg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
        
        if not os.path.exists(ffmpeg_dir):
            os.makedirs(ffmpeg_dir)
        
        # 下载FFmpeg
        ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        zip_path = os.path.join(temp_dir, "ffmpeg.zip")
        
        print("下载FFmpeg...")
        if download_file(ffmpeg_url, zip_path):
            # 解压
            print("解压FFmpeg...")
            import zipfile
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # 查找ffmpeg可执行文件
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file in ["ffmpeg.exe", "ffplay.exe", "ffprobe.exe"]:
                        ffmpeg_src = os.path.join(root, file)
                        ffmpeg_dst = os.path.join(ffmpeg_dir, file)
                        shutil.copy2(ffmpeg_src, ffmpeg_dst)
                        print(f"✅ 复制 {file} 到: {ffmpeg_dst}")
            
            # 添加到当前环境PATH
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ["PATH"]
            
            # 验证安装
            try:
                result = subprocess.run([os.path.join(ffmpeg_dir, "ffmpeg.exe"), '-version'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    print("✅ FFmpeg 安装验证成功")
                    return True
            except:
                print("❌ FFmpeg 安装验证失败")
                return False
        else:
            print("❌ FFmpeg 下载失败")
            return False
            
    except Exception as e:
        print(f"FFmpeg安装错误: {e}")
        return False
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def download_file(url, destination):
    """下载文件"""
    try:
        import urllib.request
        urllib.request.urlretrieve(url, destination)
        return True
    except:
        try:
            import requests
            response = requests.get(url, stream=True)
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except:
            return False

def install_ffmpeg_macos():
    """在macOS上安装FFmpeg"""
    try:
        subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
        print("✅ FFmpeg 安装完成")
        return True
    except Exception as e:
        print(f"❌ FFmpeg 安装失败: {e}")
        print("请先安装Homebrew，然后运行: brew install ffmpeg")
        return False

def install_ffmpeg_linux():
    """在Linux上安装FFmpeg"""
    try:
        # 尝试使用包管理器安装
        if shutil.which('apt-get'):
            subprocess.run(['sudo', 'apt-get', 'update'], check=True)
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], check=True)
        elif shutil.which('yum'):
            subprocess.run(['sudo', 'yum', 'install', '-y', 'ffmpeg'], check=True)
        elif shutil.which('dnf'):
            subprocess.run(['sudo', 'dnf', 'install', '-y', 'ffmpeg'], check=True)
        else:
            print("❌ 不支持的Linux发行版，请手动安装FFmpeg")
            return False
        
        print("✅ FFmpeg 安装完成")
        return True
    except Exception as e:
        print(f"❌ FFmpeg 安装失败: {e}")
        return False

def install_package_with_deps(package, deps=None):
    """安装包及其依赖"""
    if deps:
        print(f"先安装 {package} 的依赖项...")
        for dep in deps:
            if not install_single_package(dep):
                print(f"依赖项 {dep} 安装失败，无法继续安装 {package}")
                return False
    
    return install_single_package(package)

def install_single_package(package):
    """安装单个包，尝试多个源"""
    # 尝试使用多个镜像源安装
    for mirror in MIRROR_SOURCES:
        try:
            print(f"  尝试使用{mirror['name']}安装 {package}...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "--upgrade", package, "-i", mirror['url'],
                "--trusted-host", mirror['trusted_host'],
                "--timeout", "60",  # 增加超时时间
                "--retries", "3"    # 增加重试次数
            ])
            print(f"✓ {package} 使用{mirror['name']}安装成功")
            return True
        except Exception as e:
            print(f"  {mirror['name']}安装{package}失败: {e}")
            continue
    
    # 如果所有镜像源都失败，尝试使用默认源
    try:
        print(f"尝试使用默认源安装 {package}...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "--upgrade", package, "--timeout", "120", "--retries", "5"
        ])
        print(f"✓ {package} 使用默认源安装成功")
        return True
    except Exception as e2:
        print(f"✗ {package} 最终安装失败: {e2}")
        return False

# 自动安装依赖 - 使用多个国内源
def install_packages():
    """安装所有必要的包"""
    required_packages = {
        'Pillow': 'PIL',
        'pynput': 'pynput',
        'psutil': 'psutil',
        'numpy': 'numpy',
        'opencv-python': 'cv2',
        'pygame': 'pygame',
        'pyautogui': 'pyautogui',
        'pyaudio': 'pyaudio'
    }
    
    print("正在检查并安装必要的依赖包...")
    print("使用多个国内镜像源进行安装...")
    
    # 安装其他包
    missing_packages = []
    for package, import_name in required_packages.items():
        try:
            if import_name == 'PIL':
                from PIL import ImageGrab, Image, ImageDraw, ImageFont, ImageTk
            else:
                __import__(import_name)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"正在安装 {package}...")
            if install_single_package(package):
                print(f"✓ {package} 安装成功")
            else:
                missing_packages.append(package)
    
    # 检查音频环境
    audio_ready = check_audio_environment()
    
    if not audio_ready:
        print("⚠️ 音频支持不完整，将使用无音频模式")
    
    return len(missing_packages) == 0

# 检查并安装必要包
print("检查FFmpeg依赖...")
import shutil

def check_ffmpeg():
    """检查系统是否安装了 FFmpeg"""
    return shutil.which("ffmpeg") is not None

# 检查并安装必要包
if not install_packages():
    print("⚠️ 部分依赖安装失败，某些功能可能无法使用")
else:
    print("✅ 所有依赖包安装完成！")

# 现在导入所有需要的模块
try:
    from PIL import ImageGrab, Image, ImageDraw, ImageFont, ImageTk
    import psutil
    from pynput import keyboard, mouse
    from pynput.keyboard import Key, KeyCode
    import numpy as np
    import cv2
    import pyaudio
    import pygame
    import pyautogui
    print("✅ 所有模块导入成功！")
    
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("正在尝试修复安装...")
    
    # 尝试修复安装 - 使用多个镜像源
    installed = False
    for mirror in MIRROR_SOURCES:
        try:
            print(f"使用{mirror['name']}进行修复安装...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "Pillow", "pynput", "psutil", "numpy", "opencv-python", 
                "pygame", "pyautogui", "pyaudio",
                "-i", mirror['url'],
                "--trusted-host", mirror['trusted_host'],
                "--timeout", "120"
            ])
            print(f"✅ 使用{mirror['name']}修复安装成功")
            installed = True
            break
        except Exception as install_error:
            print(f"❌ {mirror['name']}修复安装失败: {install_error}")
    
    if not installed:
        # 尝试使用默认源
        try:
            print("尝试使用默认源进行修复安装...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "Pillow", "pynput", "psutil", "numpy", "opencv-python", 
                "pygame", "pyautogui", "pyaudio"
            ])
            print("✅ 使用默认源修复安装成功")
        except Exception as final_error:
            print(f"❌ 最终修复安装失败: {final_error}")
            print("请手动安装依赖: pip install Pillow pynput psutil numpy opencv-python pygame pyautogui pyaudio")
    
    # 重新尝试导入
    try:
        from PIL import ImageGrab, Image, ImageDraw, ImageFont, ImageTk
        import psutil
        from pynput import keyboard, mouse
        import numpy as np
        import cv2
        import pyaudio
        import pygame
        import pyautogui
        print("✅ 修复后所有模块导入成功！")
    except ImportError as final_import_error:
        print(f"❌ 最终导入失败: {final_import_error}")
        sys.exit(1)

class DrawingTool:
    """画图工具类"""
    def __init__(self, recorder):
        self.recorder = recorder
        self.drawing = False
        self.last_x = None
        self.last_y = None
        self.shapes = []  # 存储绘制的图形
        self.current_color = (255, 0, 0)  # 默认红色
        self.current_thickness = 3
        self.current_tool = "pen"  # pen, rectangle, circle, text
        self.temp_shape = None  # 临时图形，用于拖拽绘制
        self.drawing_window = None  # 延迟创建窗口
    
    def create_drawing_window(self):
        """创建画图工具窗口"""
        if self.drawing_window is not None:
            return
        
        self.drawing_window = tk.Toplevel(self.recorder.root)
        self.drawing_window.title("🎨 画图工具")
        self.drawing_window.geometry("300x500")
        self.drawing_window.configure(bg="#f0f0f0")
        self.drawing_window.attributes("-topmost", True)  # 窗口置顶
        
        # 工具选择
        tool_frame = tk.LabelFrame(self.drawing_window, text="工具", bg="#f0f0f0")
        tool_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.tool_var = tk.StringVar(value="pen")
        
        tools = [
            ("画笔", "pen"),
            ("矩形", "rectangle"),
            ("圆形", "circle"),
            ("文字", "text")
        ]
        
        for text, value in tools:
            btn = tk.Radiobutton(tool_frame, text=text, variable=self.tool_var,
                                value=value, bg="#f0f0f0", command=self.set_tool)
            btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 颜色选择
        color_frame = tk.LabelFrame(self.drawing_window, text="颜色", bg="#f0f0f0")
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.color_preview = tk.Canvas(color_frame, width=30, height=30, bg="#ff0000")
        self.color_preview.pack(side=tk.LEFT, padx=5, pady=5)
        
        tk.Button(color_frame, text="选择颜色", bg="#f0f0f0",
                 command=self.choose_color).pack(side=tk.LEFT, padx=5)
        
        # 线条粗细
        thickness_frame = tk.LabelFrame(self.drawing_window, text="线条粗细", bg="#f0f0f0")
        thickness_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.thickness_var = tk.IntVar(value=3)
        thickness_scale = tk.Scale(thickness_frame, from_=1, to=20, 
                                  variable=self.thickness_var, orient=tk.HORIZONTAL,
                                  bg="#f0f0f0", command=self.set_thickness)
        thickness_scale.pack(fill=tk.X, padx=5, pady=5)
        
        # 文字设置
        text_frame = tk.LabelFrame(self.drawing_window, text="文字设置", bg="#f0f0f0")
        text_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(text_frame, text="文字内容:", bg="#f0f0f0").pack(anchor=tk.W, padx=5)
        self.text_var = tk.StringVar(value="标注文字")
        tk.Entry(text_frame, textvariable=self.text_var).pack(fill=tk.X, padx=5, pady=5)
        
        # 控制按钮
        control_frame = tk.LabelFrame(self.drawing_window, text="控制", bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(control_frame, text="清除所有", bg="#e74c3c", fg="white",
                 command=self.clear_all).pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(control_frame, text="最小化", bg="#3498db", fg="white",
                 command=self.drawing_window.iconify).pack(fill=tk.X, padx=5, pady=5)
    
    def set_tool(self):
        """设置当前工具"""
        self.current_tool = self.tool_var.get()
    
    def choose_color(self):
        """选择颜色"""
        color = colorchooser.askcolor(title="选择颜色")[0]
        if color:
            self.current_color = (int(color[2]), int(color[1]), int(color[0]))  # BGR转RGB
            hex_color = f"#{int(color[0]):02x}{int(color[1]):02x}{int(color[2]):02x}"
            self.color_preview.config(bg=hex_color)
    
    def set_thickness(self, value):
        """设置线条粗细"""
        self.current_thickness = int(value)
    
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
        elif self.current_tool == "text":
            # 添加文字
            self.shapes.append({
                "type": "text",
                "x": x,
                "y": y,
                "text": self.text_var.get(),
                "color": self.current_color,
                "size": self.current_thickness * 5  # 文字大小基于线条粗细
            })
    
    def draw(self, x, y):
        """绘制中"""
        if not self.drawing:
            return
            
        if self.current_tool == "pen":
            # 添加线条段
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
            # 更新临时图形
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
            elif shape["type"] == "text":
                cv2.putText(frame_copy,
                           shape["text"],
                           (shape["x"], shape["y"]),
                           cv2.FONT_HERSHEY_SIMPLEX,
                           shape["size"] / 30,
                           shape["color"],
                           2)
        
        # 绘制临时图形（拖拽中）
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

class MouseTracker:
    """鼠标跟踪器类"""
    def __init__(self):
        self.mouse_listener = None
        self.current_x = 0
        self.current_y = 0
        self.last_click_x = 0
        self.last_click_y = 0
        self.click_detected = False
        self.tracking_area = None  # (x, y, width, height)
        self.is_tracking = False
    
    def start_tracking(self):
        """开始跟踪鼠标"""
        def on_move(x, y):
            self.current_x = x
            self.current_y = y
        
        def on_click(x, y, button, pressed):
            if pressed:
                self.last_click_x = x
                self.last_click_y = y
                self.click_detected = True
        
        self.mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
        self.mouse_listener.start()
        self.is_tracking = True
    
    def stop_tracking(self):
        """停止跟踪鼠标"""
        if self.mouse_listener:
            self.mouse_listener.stop()
            self.is_tracking = False
    
    def get_tracking_area_around_cursor(self, width, height):
        """获取鼠标周围的区域"""
        # 计算区域（居中于鼠标位置）
        x = max(0, self.current_x - width // 2)
        y = max(0, self.current_y - height // 2)
        
        # 确保不超出屏幕边界
        screen_width, screen_height = pyautogui.size()
        x = min(x, screen_width - width)
        y = min(y, screen_height - height)
        
        # 确保坐标有效
        x = max(0, x)
        y = max(0, y)
        
        self.tracking_area = (x, y, width, height)
        return self.tracking_area
    
    def get_click_centered_area(self, width, height, offset_x=0, offset_y=0):
        """获取以点击位置为中心的区域"""
        if not self.click_detected:
            return self.get_tracking_area_around_cursor(width, height)
        
        # 使用最后点击位置
        x = max(0, self.last_click_x - width // 2 + offset_x)
        y = max(0, self.last_click_y - height // 2 + offset_y)
        
        # 确保不超出屏幕边界
        screen_width, screen_height = pyautogui.size()
        x = min(x, screen_width - width)
        y = min(y, screen_height - height)
        
        # 确保坐标有效
        x = max(0, x)
        y = max(0, y)
        
        self.tracking_area = (x, y, width, height)
        return self.tracking_area

class ScreenRecorder:
    """屏幕录制器主类"""
    def __init__(self, root):
        self.root = root
        self.root.title(f"Super Hi Vision - 高级超高清屏幕录制工具 v{__version__}")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设置图标（如果有）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        # 初始化变量
        self.recording = False
        self.paused = False
        self.video_writer = None
        self.output_file = None
        self.frame_count = 0
        self.start_time = None
        self.audio_recording = False
        self.audio_frames = []
        self.audio_stream = None
        self.audio = None
        
        # 实际录制时长统计（用于校正视频帧率，防止快放/慢放）
        self.recording_active_seconds = 0.0
        self.last_active_tick = 0
        
        # 录制区域
        self.recording_area = None  # None表示全屏，"follow"表示跟随鼠标
        self.area_size = (800, 600)  # 跟随鼠标时的固定区域大小
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="screen_recorder_")
        self.temp_audio_file = os.path.join(self.temp_dir, "temp_audio.wav")
        self.temp_screenshots = []
        
        # 初始化鼠标跟踪器
        self.mouse_tracker = MouseTracker()
        
        # 画图工具
        self.drawing_tool = None
        
        # 创建UI
        self.create_widgets()
        
        # 初始化音频设备
        self.audio_devices = []
        self.init_audio_devices()
        
        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 热键监听
        self.keyboard_listener = None
        self.setup_hotkeys()
        
        # 录制计时器
        self.recording_start_time = None
        self.last_frame_time = time.time()
        self.target_frame_time = 1.0 / 30  # 默认30fps
        
        # 帧率控制
        self.frame_skip_counter = 0
        
        # 版本更新提示
        self.check_version_update()
        
        # 设置UI样式
        self.setup_styles()
        
        print("✅ 屏幕录制器初始化完成")
    
    def check_version_update(self):
        """检查版本更新"""
        try:
            config_file = os.path.join(os.path.expanduser("~"), ".super_hi_vision_config")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    config = f.read()
                    if f"version_{__version__}_notified" in config:
                        return  # 已经提示过此版本
        except:
            pass
        
        # 显示更新提示
        dialog = tk.Toplevel(self.root)
        dialog.title(f"📢 更新公告 - 版本 {__version__}")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 500) // 2
        y = (dialog.winfo_screenheight() - 400) // 2
        dialog.geometry(f"500x400+{x}+{y}")
        
        # 公告内容
        announcement_text = f"""📋 版本更新内容 v{__version__}

🎬 高级超高清屏幕录制工具

1. 🎨 新增二次元主题，界面更美观
2. 🔊 音频降噪强度可调滑杆（0-100%）
3. 🖥️ 后台保活：关闭窗口最小化到托盘
4. 🎯 优化录制性能，减少卡顿
5. 🐛 修复已知问题

感谢您的使用！
"""
        
        tk.Label(dialog, text=announcement_text, justify=tk.LEFT, font=("Arial", 11)).pack(pady=20, padx=20)
        
        # 确定按钮
        tk.Button(dialog, text="知道了", bg="#4CAF50", fg="white", 
                 font=("Arial", 12), padx=20, pady=10,
                 command=dialog.destroy).pack(pady=20)
        
        # 记录已提示
        try:
            config_file = os.path.join(os.path.expanduser("~"), ".super_hi_vision_config")
            with open(config_file, 'a') as f:
                f.write(f"\nversion_{__version__}_notified\n")
        except:
            pass
    
    def setup_styles(self):
        """设置UI样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 设置字体
        default_font = ('Microsoft YaHei UI', 10)
        self.root.option_add('*Font', default_font)
        
        # 设置颜色主题
        bg_color = '#f0f0f0'
        self.root.configure(bg=bg_color)
    
    def create_widgets(self):
        """创建UI组件"""
        # 主框架
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题栏
        title_frame = tk.Frame(main_frame, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        title_frame.pack_propagate(False)
        
        tk.Label(title_frame, text="🎬 Super Hi Vision", 
                font=('Arial', 20, 'bold'), bg='#2c3e50', fg='white').pack(side=tk.LEFT, padx=10)
        tk.Label(title_frame, text=f"版本 {__version__} | 现代化设计，提升用户体验", 
                font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1').pack(side=tk.LEFT, padx=10)
        
        # 使用Notebook（标签页）
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建各个标签页
        self.create_basic_tab()
        self.create_advanced_tab()
        self.create_audio_tab()
        self.create_hotkey_tab()
        
        # 控制按钮区域
        control_frame = tk.Frame(main_frame, bg='#f0f0f0')
        control_frame.pack(fill=tk.X, pady=10)
        
        # 开始/暂停按钮
        self.start_button = tk.Button(control_frame, text="▶ 开始录制", 
                                      font=('Arial', 12, 'bold'),
                                      bg='#27ae60', fg='white',
                                      padx=20, pady=10,
                                      command=self.toggle_recording,
                                      cursor='hand2')
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # 停止按钮
        self.stop_button = tk.Button(control_frame, text="⏹ 停止录制", 
                                     font=('Arial', 12, 'bold'),
                                     bg='#7f8c8d', fg='white',
                                     padx=20, pady=10,
                                     command=self.stop_recording,
                                     state=tk.DISABLED,
                                     cursor='hand2')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # 暂停按钮
        self.pause_button = tk.Button(control_frame, text="⏸ 暂停", 
                                      font=('Arial', 12, 'bold'),
                                      bg='#7f8c8d', fg='white',
                                      padx=20, pady=10,
                                      command=self.pause_recording,
                                      state=tk.DISABLED,
                                      cursor='hand2')
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        # 截图按钮
        self.screenshot_button = tk.Button(control_frame, text="📸 截图", 
                                           font=('Arial', 12, 'bold'),
                                           bg='#3498db', fg='white',
                                           padx=20, pady=10,
                                           command=self.take_screenshot,
                                           cursor='hand2')
        self.screenshot_button.pack(side=tk.LEFT, padx=5)
        
        # 状态栏
        status_frame = tk.Frame(main_frame, bg='#2c3e50', height=40)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        # 录制状态
        self.recording_status_var = tk.StringVar(value="🔴 未开始录制")
        tk.Label(status_frame, textvariable=self.recording_status_var,
                font=('Arial', 10, 'bold'), bg='#2c3e50', fg='white').pack(side=tk.LEFT, padx=10)
        
        # 录制时间
        self.recording_time_var = tk.StringVar(value="00:00:00")
        tk.Label(status_frame, textvariable=self.recording_time_var,
                font=('Arial', 10, 'bold'), bg='#2c3e50', fg='#ecf0f1').pack(side=tk.LEFT, padx=10)
        
        # 文件大小
        self.file_size_var = tk.StringVar(value="大小: --")
        tk.Label(status_frame, textvariable=self.file_size_var,
                font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1').pack(side=tk.LEFT, padx=10)
        
        # FPS显示
        self.fps_status_var = tk.StringVar(value="FPS: --")
        tk.Label(status_frame, textvariable=self.fps_status_var,
                font=('Arial', 10), bg='#2c3e50', fg='#ecf0f1').pack(side=tk.RIGHT, padx=10)
    
    def create_basic_tab(self):
        """创建基本设置标签页"""
        basic_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(basic_frame, text='📋 基本设置')
        
        # 录制区域设置
        area_group = tk.LabelFrame(basic_frame, text="录制区域", bg='#f0f0f0', 
                                   font=('Arial', 11, 'bold'))
        area_group.pack(fill=tk.X, padx=10, pady=10)
        
        # 区域模式
        area_mode_frame = tk.Frame(area_group, bg='#f0f0f0')
        area_mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.area_mode = tk.StringVar(value="fullscreen")
        
        tk.Radiobutton(area_mode_frame, text="全屏录制", variable=self.area_mode,
                      value="fullscreen", bg='#f0f0f0', font=('Arial', 10),
                      command=self.update_area_mode).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(area_mode_frame, text="自定义区域", variable=self.area_mode,
                      value="custom", bg='#f0f0f0', font=('Arial', 10),
                      command=self.update_area_mode).pack(side=tk.LEFT, padx=5)
        
        tk.Radiobutton(area_mode_frame, text="跟随鼠标", variable=self.area_mode,
                      value="follow", bg='#f0f0f0', font=('Arial', 10),
                      command=self.update_area_mode).pack(side=tk.LEFT, padx=5)
        
        # 自定义区域设置
        custom_area_frame = tk.Frame(area_group, bg='#f0f0f0')
        custom_area_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(custom_area_frame, text="宽度:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.width_var = tk.StringVar(value="1920")
        tk.Entry(custom_area_frame, textvariable=self.width_var, width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Label(custom_area_frame, text="高度:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.height_var = tk.StringVar(value="1080")
        tk.Entry(custom_area_frame, textvariable=self.height_var, width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(custom_area_frame, text="选择区域", bg='#3498db', fg='white',
                 command=self.select_area, cursor='hand2').pack(side=tk.LEFT, padx=10)
        
        # 跟随鼠标区域设置
        follow_area_frame = tk.Frame(area_group, bg='#f0f0f0')
        follow_area_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(follow_area_frame, text="跟随区域宽度:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.follow_width_var = tk.StringVar(value="800")
        tk.Entry(follow_area_frame, textvariable=self.follow_width_var, width=10).pack(side=tk.LEFT, padx=5)
        
        tk.Label(follow_area_frame, text="高度:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.follow_height_var = tk.StringVar(value="600")
        tk.Entry(follow_area_frame, textvariable=self.follow_height_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 输出设置
        output_group = tk.LabelFrame(basic_frame, text="输出设置", bg='#f0f0f0',
                                     font=('Arial', 11, 'bold'))
        output_group.pack(fill=tk.X, padx=10, pady=10)
        
        # 输出目录
        output_dir_frame = tk.Frame(output_group, bg='#f0f0f0')
        output_dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(output_dir_frame, text="输出目录:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.output_dir = os.path.join(os.path.expanduser("~"), "Videos")
        self.output_dir_var = tk.StringVar(value=self.output_dir)
        tk.Entry(output_dir_frame, textvariable=self.output_dir_var, width=40).pack(side=tk.LEFT, padx=5)
        
        tk.Button(output_dir_frame, text="浏览", bg='#3498db', fg='white',
                 command=self.browse_output_dir, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # 文件名
        filename_frame = tk.Frame(output_group, bg='#f0f0f0')
        filename_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(filename_frame, text="文件名:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.filename_var = tk.StringVar(value=f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        tk.Entry(filename_frame, textvariable=self.filename_var, width=40).pack(side=tk.LEFT, padx=5)
        
        tk.Button(filename_frame, text="浏览", bg='#3498db', fg='white',
                 command=self.browse_output_file, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def create_advanced_tab(self):
        """创建高级设置标签页"""
        advanced_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(advanced_frame, text='⚙️ 高级设置')
        
        # 视频格式设置
        format_group = tk.LabelFrame(advanced_frame, text="视频格式", bg='#f0f0f0',
                                     font=('Arial', 11, 'bold'))
        format_group.pack(fill=tk.X, padx=10, pady=10)
        
        # 格式选择
        format_frame = tk.Frame(format_group, bg='#f0f0f0')
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(format_frame, text="格式:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.format_var = tk.StringVar(value="MP4")
        format_menu = ttk.Combobox(format_frame, textvariable=self.format_var,
                                   values=list(SUPPORTED_FORMATS.keys()),
                                   state='readonly', width=10)
        format_menu.pack(side=tk.LEFT, padx=5)
        
        # 编码器选择
        tk.Label(format_frame, text="编码器:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.codec_var = tk.StringVar(value="H.264 (libx264)")
        codec_menu = ttk.Combobox(format_frame, textvariable=self.codec_var,
                                  values=list(SUPPORTED_CODECS.keys()),
                                  state='readonly', width=20)
        codec_menu.pack(side=tk.LEFT, padx=5)
        
        # 帧率设置
        fps_frame = tk.Frame(format_group, bg='#f0f0f0')
        fps_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(fps_frame, text="帧率:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.fps_var = tk.StringVar(value="30 FPS (标准)")
        fps_menu = ttk.Combobox(fps_frame, textvariable=self.fps_var,
                                values=list(FPS_OPTIONS.keys()),
                                state='readonly', width=15)
        fps_menu.pack(side=tk.LEFT, padx=5)
        
        # 质量设置
        quality_frame = tk.Frame(format_group, bg='#f0f0f0')
        quality_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(quality_frame, text="质量:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.quality_var = tk.StringVar(value="high")
        for quality in ["low", "medium", "high", "ultra", "bluray"]:
            tk.Radiobutton(quality_frame, text=quality.capitalize(), variable=self.quality_var,
                          value=quality, bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        # 性能设置
        performance_group = tk.LabelFrame(advanced_frame, text="性能模式", bg='#f0f0f0',
                                          font=('Arial', 11, 'bold'))
        performance_group.pack(fill=tk.X, padx=10, pady=10)
        
        performance_frame = tk.Frame(performance_group, bg='#f0f0f0')
        performance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.performance_mode = "medium"
        for mode in ["low", "medium", "high", "ultra"]:
            tk.Radiobutton(performance_frame, text=mode.capitalize(), variable=tk.StringVar(value="medium"),
                          value=mode, bg='#f0f0f0', font=('Arial', 10),
                          command=lambda m=mode: setattr(self, 'performance_mode', m)).pack(side=tk.LEFT, padx=5)
    
    def create_audio_tab(self):
        """创建音频设置标签页"""
        audio_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(audio_frame, text='🔊 音频设置')
        
        # 音频录制设置
        audio_group = tk.LabelFrame(audio_frame, text="音频录制", bg='#f0f0f0',
                                    font=('Arial', 11, 'bold'))
        audio_group.pack(fill=tk.X, padx=10, pady=10)
        
        # 启用音频
        self.enable_audio_var = tk.BooleanVar(value=AUDIO_SUPPORT)
        tk.Checkbutton(audio_group, text="启用音频录制", variable=self.enable_audio_var,
                      bg='#f0f0f0', font=('Arial', 10)).pack(anchor=tk.W, padx=10, pady=5)
        
        # 音频设备选择
        device_frame = tk.Frame(audio_group, bg='#f0f0f0')
        device_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(device_frame, text="音频设备:", bg='#f0f0f0', font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        self.audio_device_var = tk.StringVar()
        self.audio_device_menu = ttk.Combobox(device_frame, textvariable=self.audio_device_var,
                                              state='readonly', width=30)
        self.audio_device_menu.pack(side=tk.LEFT, padx=5)
        
        tk.Button(device_frame, text="测试", bg='#3498db', fg='white',
                 command=self.test_audio, cursor='hand2').pack(side=tk.LEFT, padx=10)
        
        # 音频信息
        info_group = tk.LabelFrame(audio_frame, text="音频信息", bg='#f0f0f0',
                                   font=('Arial', 11, 'bold'))
        info_group.pack(fill=tk.X, padx=10, pady=10)
        
        self.audio_info_var = tk.StringVar(value="等待检测...")
        tk.Label(info_group, textvariable=self.audio_info_var, bg='#f0f0f0',
                font=('Arial', 10), justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=5)
        
        # 降噪设置
        denoise_group = tk.LabelFrame(audio_frame, text="音频降噪", bg='#f0f0f0',
                                      font=('Arial', 11, 'bold'))
        denoise_group.pack(fill=tk.X, padx=10, pady=10)
        
        self.denoise_var = tk.BooleanVar(value=True)
        tk.Checkbutton(denoise_group, text="启用音频降噪（去除背景噪音）", variable=self.denoise_var,
                      bg='#f0f0f0', font=('Arial', 10)).pack(anchor=tk.W, padx=10, pady=5)
    
    def create_hotkey_tab(self):
        """创建热键设置标签页"""
        hotkey_frame = tk.Frame(self.notebook, bg='#f0f0f0')
        self.notebook.add(hotkey_frame, text='⌨️ 热键设置')
        
        hotkey_group = tk.LabelFrame(hotkey_frame, text="热键设置", bg='#f0f0f0',
                                     font=('Arial', 11, 'bold'))
        hotkey_group.pack(fill=tk.X, padx=10, pady=10)
        
        # 当前热键显示
        self.hotkey_info_var = tk.StringVar(value="当前热键：\nF9 - 开始/暂停录制\nF10 - 停止录制\nF11 - 截图\nF12 - 显示/隐藏画图工具")
        tk.Label(hotkey_group, textvariable=self.hotkey_info_var, bg='#f0f0f0',
                font=('Arial', 10), justify=tk.LEFT).pack(anchor=tk.W, padx=10, pady=10)
        
        # 说明
        tk.Label(hotkey_group, text="提示：热键在程序运行期间全局有效", bg='#f0f0f0',
                font=('Arial', 9, 'italic'), fg='#7f8c8d').pack(anchor=tk.W, padx=10, pady=5)
    
    def update_area_mode(self):
        """更新区域模式"""
        mode = self.area_mode.get()
        if mode == "custom":
            self.recording_area = None  # 稍后从输入框读取
        elif mode == "follow":
            self.recording_area = "follow"
        else:
            self.recording_area = None
    
    def init_audio_devices(self):
        """初始化音频设备"""
        try:
            p = pyaudio.PyAudio()
            self.audio_devices = []
            
            # 获取设备列表
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # 只显示输入设备
                    name = device_info['name']
                    self.audio_devices.append((i, name))
            
            p.terminate()
            
            # 更新下拉菜单
            if self.audio_devices:
                device_names = [f"{name}" for _, name in self.audio_devices]
                self.audio_device_menu['values'] = device_names
                if device_names:
                    self.audio_device_menu.current(0)
                    self.audio_device_var.set(device_names[0])
                
                self.audio_info_var.set(f"✅ 找到 {len(self.audio_devices)} 个音频输入设备")
            else:
                self.audio_info_var.set("❌ 未找到音频输入设备")
                
        except Exception as e:
            print(f"❌ 音频设备初始化失败: {e}")
            self.audio_info_var.set(f"❌ 音频设备初始化失败: {e}")
    
    def test_audio(self):
        """测试音频录制"""
        try:
            # 获取选中的设备索引
            selected_name = self.audio_device_var.get()
            device_index = None
            for idx, name in self.audio_devices:
                if name == selected_name:
                    device_index = idx
                    break
            
            if device_index is None:
                messagebox.showwarning("警告", "请先选择音频设备")
                return
            
            # 录制3秒测试音频
            messagebox.showinfo("测试", "将录制3秒测试音频，请对着麦克风说话...")
            
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16,
                          channels=1,
                          rate=44100,
                          input=True,
                          input_device_index=device_index,
                          frames_per_buffer=1024)
            
            frames = []
            for _ in range(0, int(44100 / 1024 * 3)):
                data = stream.read(1024)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            # 测试音频数据非空
            test_file = os.path.join(self.temp_dir, "audio_test.wav")
            # 自动增益放大，解决麦克风录音音量过低、测试播放听不清的问题
            audio_data = _boost_audio_gain(b''.join(frames))
            with wave.open(test_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(audio_data)
            
            file_size = os.path.getsize(test_file)
            messagebox.showinfo("测试成功", f"音频已录制到: {test_file}\n文件大小: {file_size} bytes\n\n请检查文件是否有声音")
            
        except Exception as e:
            messagebox.showerror("测试失败", f"音频测试失败: {str(e)}")
    
    def setup_hotkeys(self):
        """设置全局热键"""
        def on_press(key):
            try:
                if key == Key.f9:
                    self.root.after(0, self.toggle_recording)
                elif key == Key.f10:
                    self.root.after(0, self.stop_recording)
                elif key == Key.f11:
                    self.root.after(0, self.take_screenshot)
                elif key == Key.f12:
                    self.root.after(0, self.toggle_drawing_tool)
            except:
                pass
        
        self.keyboard_listener = keyboard.Listener(on_press=on_press)
        self.keyboard_listener.start()
        print("✅ 全局热键已设置")
    
    def toggle_drawing_tool(self):
        """切换画图工具"""
        if self.drawing_tool is None:
            self.drawing_tool = DrawingTool(self)
            self.drawing_tool.create_drawing_window()
        else:
            if self.drawing_tool.drawing_window and self.drawing_tool.drawing_window.winfo_exists():
                self.drawing_tool.drawing_window.destroy()
            self.drawing_tool = None
    
    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if dir_path:
            self.output_dir_var.set(dir_path)
            self.output_dir = dir_path
    
    def browse_output_file(self):
        """浏览输出文件"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{SUPPORTED_FORMATS[self.format_var.get()]['ext']}",
            filetypes=[("视频文件", f"*.{SUPPORTED_FORMATS[self.format_var.get()]['ext']}")],
            initialdir=self.output_dir_var.get(),
            initialfile=self.filename_var.get()
        )
        if file_path:
            self.filename_var.set(os.path.splitext(os.path.basename(file_path))[0])
    
    def select_area(self):
        """选择录制区域"""
        selector = AreaSelector(self.root, self)
        selector.start_selection()
    
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
        try:
            # 检查输出目录
            output_dir = self.output_dir_var.get()
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # 生成输出文件名
            filename = self.filename_var.get()
            if not filename:
                filename = f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            fmt = self.format_var.get()
            ext = SUPPORTED_FORMATS[fmt]['ext']
            self.output_file = os.path.join(output_dir, f"{filename}.{ext}")
            
            # 获取录制区域
            mode = self.area_mode.get()
            if mode == "custom":
                try:
                    width = int(self.width_var.get())
                    height = int(self.height_var.get())
                    # 确保宽高为偶数（yuv420 系列编码器要求）
                    width -= width % 2
                    height -= height % 2
                    self.recording_area = (0, 0, width, height)
                except:
                    messagebox.showerror("错误", "宽度和高度必须是数字")
                    return
            elif mode == "follow":
                width = int(self.follow_width_var.get())
                height = int(self.follow_height_var.get())
                width -= width % 2
                height -= height % 2
                self.area_size = (width, height)
                self.recording_area = "follow"
                self.mouse_tracker.start_tracking()
            else:
                self.recording_area = None
            
            # 获取录制参数
            fps = FPS_OPTIONS[self.fps_var.get()]
            self.fps = fps
            self.target_frame_time = 1.0 / fps
            
            # 获取视频写入器
            self.video_writer = self.create_video_writer(self.output_file, fmt)
            if self.video_writer is None:
                messagebox.showerror("错误", "无法创建视频文件，请检查输出路径和编码器")
                return
            
            # 开始录制
            self.recording = True
            self.paused = False
            self.frame_count = 0
            self.start_time = time.time()
            self.recording_start_time = time.time()
            self.last_frame_time = time.time()
            self.recording_active_seconds = 0.0
            self.last_active_tick = time.time()
            self.frame_skip_counter = 0
            
            # 启动音频录制
            if self.enable_audio_var.get() and AUDIO_SUPPORT:
                self.start_audio_recording()
            
            # 启动录制线程
            self.recording_thread = threading.Thread(target=self.record_screen)
            self.recording_thread.daemon = True
            self.recording_thread.start()
            
            # 启动计时器
            self.start_timer()
            
            # 更新UI
            self.update_ui_for_recording()
            
            print(f"🔴 开始录制: {self.output_file}")
            
        except Exception as e:
            print(f"❌ 开始录制失败: {e}")
            messagebox.showerror("错误", f"开始录制失败: {str(e)}")
            self.recording = False
    
    def create_video_writer(self, output_file, fmt):
        """创建视频写入器
        
        某些 fourcc（例如 MKV 常用的 X264）在当前 OpenCV 里没有对应编码器时
        会静默失败——不抛异常、不写任何数据，最后留下 0 字节文件。
        这里按容器优先的候选顺序逐个验证 isOpened()。
        """
        candidates = {
            "MP4": ["mp4v", "avc1"],
            "AVI": ["XVID", "MJPG"],
            "MKV": ["mp4v", "XVID", "MJPG"],
            "FLV": ["FLV1", "mp4v"],
            "MOV": ["avc1", "mp4v"],
        }.get(fmt, ["mp4v", "MJPG"])
        
        # 获取分辨率
        if self.recording_area == "follow":
            width, height = self.area_size
        elif self.recording_area:
            width, height = self.recording_area[2], self.recording_area[3]
        else:
            screen_width, screen_height = pyautogui.size()
            width, height = screen_width, screen_height
        
        width -= width % 2
        height -= height % 2
        
        for fourcc_str in candidates:
            try:
                fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
                writer = cv2.VideoWriter(output_file, fourcc, self.fps, (width, height))
                if writer.isOpened():
                    print(f"🎬 视频编码: {fourcc_str} -> {output_file} ({width}x{height})")
                    return writer
                writer.release()
            except Exception as e:
                print(f"⚠️ 编码 {fourcc_str} 失败: {e}")
                continue
        
        print("❌ 所有编码候选均不可用")
        return None
    
    def start_audio_recording(self):
        """开始音频录制"""
        try:
            selected_name = self.audio_device_var.get()
            device_index = None
            for idx, name in self.audio_devices:
                if name == selected_name:
                    device_index = idx
                    break
            
            if device_index is None:
                print("⚠️ 未选择音频设备")
                return
            
            p = pyaudio.PyAudio()
            dev_info = p.get_device_info_by_index(device_index)
            max_channels = int(dev_info.get('maxInputChannels', 1) or 1)
            channels = min(max_channels, 2)
            rate = int(dev_info.get('defaultSampleRate', 44100) or 44100)
            
            self.audio = p
            self.audio_stream = p.open(format=pyaudio.paInt16,
                                       channels=channels,
                                       rate=rate,
                                       input=True,
                                       input_device_index=device_index,
                                       frames_per_buffer=1024)
            self.audio_channels = channels
            self.audio_rate = rate
            self.audio_recording = True
            self.audio_frames = []
            
            def record_audio():
                while self.audio_recording:
                    try:
                        data = self.audio_stream.read(1024, exception_on_overflow=False)
                        self.audio_frames.append(data)
                    except Exception as e:
                        print(f"❌ 音频录制错误: {e}")
                        break
            
            self.audio_thread = threading.Thread(target=record_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            
            print(f"🔊 音频录制已启动: {channels}ch @ {rate}Hz")
            
        except Exception as e:
            print(f"❌ 启动音频录制失败: {e}")
            self.audio_recording = False
    
    def stop_audio_recording(self):
        """停止音频录制"""
        self.audio_recording = False
        try:
            if getattr(self, 'audio_thread', None):
                self.audio_thread.join(timeout=2)
        except:
            pass
        try:
            if self.audio_stream:
                self.audio_stream.stop_stream()
                self.audio_stream.close()
                self.audio_stream = None
        except:
            pass
        try:
            if self.audio:
                self.audio.terminate()
                self.audio = None
        except:
            pass
    
    def pause_recording(self):
        """暂停录制"""
        if self.recording and not self.paused:
            self.paused = True
            self.pause_button.config(text="▶ 继续", bg='#27ae60')
            self.recording_status_var.set("⏸ 已暂停")
            print("⏸ 录制已暂停")
    
    def resume_recording(self):
        """恢复录制"""
        if self.recording and self.paused:
            self.paused = False
            self.last_active_tick = time.time()
            self.pause_button.config(text="⏸ 暂停", bg='#f39c12')
            self.recording_status_var.set("🔴 录制中...")
            print("▶ 录制已恢复")
    
    def stop_recording(self):
        """停止录制"""
        if not self.recording:
            return
        
        print("⏹ 正在停止录制...")
        
        # 停止录制线程
        self.recording = False
        if hasattr(self, 'recording_thread') and self.recording_thread:
            self.recording_thread.join(timeout=5)
        
        # 释放视频写入器
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        # 停止音频录制
        self.stop_audio_recording()
        
        # 停止鼠标跟踪
        if self.mouse_tracker.is_tracking:
            self.mouse_tracker.stop_tracking()
        
        # 停止计时器
        self.stop_timer()
        
        # 确保录制时长和帧数有效
        if self.frame_count > 0 and self.recording_active_seconds > 0:
            try:
                # 校正视频播放速度
                self.fix_video_playback_speed()
                
                # 合成音频和视频
                if self.audio_frames and self.output_file:
                    self.merge_audio_video()
                
                # 视频压缩（如果需要）
                if self.quality_var.get() != "high":
                    self.compress_video()
                    
            except Exception as e:
                print(f"❌ 视频处理错误: {e}")
                messagebox.showerror("错误", f"视频处理失败: {str(e)}")
        
        # 更新UI
        self.update_ui_for_stopped()
        
        # 显示完成消息
        if self.output_file and os.path.exists(self.output_file):
            file_size = os.path.getsize(self.output_file) / (1024 * 1024)  # MB
            messagebox.showinfo("录制完成", 
                              f"视频已保存！\n"
                              f"文件: {self.output_file}\n"
                              f"大小: {file_size:.1f} MB\n"
                              f"时长: {self.recording_time_var.get()}")
            print(f"✅ 录制完成: {self.output_file}")
        else:
            messagebox.showerror("错误", "视频文件未能正常生成")
            print("❌ 视频文件未能正常生成")
    
    def merge_audio_video(self):
        """合并音频和视频：将录制到的麦克风音频合成进视频文件
        
        返回 True 表示最终视频里确实带上了音频，False 表示合并失败或被跳过。
        """
        if not self.audio_frames or not self.output_file:
            return False
        
        try:
            print(f"🔊 音频帧数: {len(self.audio_frames)}")
            
            # 写入音频文件（自动增益放大，解决音量过低）
            with wave.open(self.temp_audio_file, 'wb') as wf:
                wf.setnchannels(getattr(self, 'audio_channels', 1))
                wf.setsampwidth(2)
                wf.setframerate(getattr(self, 'audio_rate', 44100))
                wf.writeframes(_boost_audio_gain(b''.join(self.audio_frames)))
            
            # 合成命令：视频流复制，音频转 AAC + 响度归一化 + apad 补静音
            if not FFMPEG_AVAILABLE:
                print("⚠️ FFmpeg 不可用，跳过音视频合并（音频已保存至临时目录）")
                return False
            
            temp_output = os.path.splitext(self.output_file)[0] + "_with_audio" + os.path.splitext(self.output_file)[1]
            faststart = ['-movflags', '+faststart'] if self.output_file.lower().endswith(('.mp4', '.mov', '.m4v')) else []
            
            filter_variants = [
                ('降噪+响度归一化', 'highpass=f=80,afftdn=nr=12:nf=-30,loudnorm=I=-16:TP=-1.5:LRA=11,apad'),
                ('仅响度归一化', 'loudnorm=I=-16:TP=-1.5:LRA=11,apad'),
                ('不做音频处理', None),
            ]
            video_attempts = [
                ('流复制', ['-c:v', 'copy']),
                ('重新编码', ['-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-pix_fmt', 'yuv420p']),
            ]
            
            merged = False
            last_err = ''
            for label, video_opts in video_attempts:
                for filter_label, audio_filter in filter_variants:
                    if os.path.exists(temp_output):
                        try:
                            os.remove(temp_output)
                        except:
                            pass
                    cmd = ['ffmpeg', '-y', '-i', self.output_file, '-i', self.temp_audio_file]
                    cmd += video_opts
                    cmd += ['-c:a', 'aac', '-b:a', '128k']
                    if audio_filter:
                        cmd += ['-af', audio_filter]
                    cmd += ['-shortest'] + faststart + [temp_output]
                    
                    print(f"🔄 正在合并音视频（{label} / {filter_label}）...")
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0 and os.path.exists(temp_output) and os.path.getsize(temp_output) > 0:
                        merged = True
                        print(f"✅ 音视频合并成功（{label} / {filter_label}）")
                        break
                    last_err = (result.stderr or '')[-500:]
                if merged:
                    break
            
            if merged:
                os.remove(self.output_file)
                os.rename(temp_output, self.output_file)
                print(f"✅ 音视频合并完成: {self.output_file}")
                return True
            else:
                print(f"❌ 音视频合并失败: {last_err}")
                if os.path.exists(temp_output):
                    try:
                        os.remove(temp_output)
                    except:
                        pass
                return False
            
        except Exception as e:
            print(f"❌ 音视频合并错误: {e}")
            return False
    
    def compress_video(self):
        """压缩视频"""
        try:
            if not self.output_file or not os.path.exists(self.output_file):
                return
            
            quality = self.quality_var.get()
            quality_config = QUALITY_PRESETS.get(quality, QUALITY_PRESETS["medium"])
            crf = quality_config["crf"]
            
            original_size = os.path.getsize(self.output_file)
            temp_compressed = os.path.splitext(self.output_file)[0] + "_compressed" + os.path.splitext(self.output_file)[1]
            
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-i', self.output_file,
                '-c:v', 'libx264',
                '-crf', str(crf),
                '-preset', 'medium',
                '-c:a', 'copy',
                '-progress', 'pipe:1',
                temp_compressed
            ]
            
            self.root.after(0, lambda: self.recording_status_var.set("🔄 视频压缩中... 0%"))
            
            process = subprocess.Popen(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            total_duration = None
            for line in process.stdout:
                line = line.strip()
                if line.startswith('duration='):
                    duration_str = line.split('=')[1]
                    try:
                        h, m, s = duration_str.split(':')
                        total_duration = int(h) * 3600 + int(m) * 60 + float(s)
                    except:
                        pass
                elif line.startswith('out_time_ms='):
                    if total_duration:
                        time_ms = int(line.split('=')[1]) / 1000000
                        progress = min(int((time_ms / total_duration) * 100), 99)
                        self.root.after(0, lambda p=progress: self.recording_status_var.set(f"🔄 视频压缩中... {p}%"))
            
            process.wait()
            
            if process.returncode == 0 and os.path.exists(temp_compressed):
                compressed_size = os.path.getsize(temp_compressed)
                
                if compressed_size < original_size:
                    os.remove(self.output_file)
                    os.rename(temp_compressed, self.output_file)
                    
                    compression_ratio = (1 - compressed_size / original_size) * 100
                    self.root.after(0, lambda: self.recording_status_var.set(f"✅ 压缩完成! 节省{compression_ratio:.1f}%"))
                    print(f"✅ 视频压缩完成 - 压缩率: {compression_ratio:.1f}%")
                    print(f"   原大小: {original_size / (1024 * 1024):.2f} MB")
                    print(f"   压缩后: {compressed_size / (1024 * 1024):.2f} MB")
                else:
                    os.remove(temp_compressed)
                    self.root.after(0, lambda: self.recording_status_var.set("⚠️ 压缩后文件未变小，保留原文件"))
                    print("⚠️ 压缩后文件未变小，保留原文件")
            else:
                stderr = process.stderr.read() if process.stderr else ""
                print(f"❌ 视频压缩失败: {stderr}")
                self.root.after(0, lambda: self.recording_status_var.set("❌ 视频压缩失败"))
                if os.path.exists(temp_compressed):
                    os.remove(temp_compressed)
                    
        except Exception as e:
            print(f"❌ 视频压缩错误: {e}")
            self.root.after(0, lambda: self.recording_status_var.set(f"❌ 压缩错误: {str(e)[:20]}"))
    
    def record_screen(self):
        """录制屏幕主循环"""
        performance_config = PERFORMANCE_OPTIONS.get(self.performance_mode, PERFORMANCE_OPTIONS["medium"])
        frame_skip = performance_config["frame_skip"]
        sleep_factor = performance_config["sleep_factor"]
        
        while self.recording:
            if self.paused:
                # 暂停期间刷新计时点，保证暂停时长不计入有效录制时长
                self.last_active_tick = time.time()
                time.sleep(0.1)
                continue
            
            try:
                current_time = time.time()
                elapsed = current_time - self.last_frame_time
                
                # 累加有效录制时长（不含暂停），用于录制结束后校正视频帧率
                if self.last_active_tick > 0:
                    self.recording_active_seconds += current_time - self.last_active_tick
                self.last_active_tick = current_time
                
                # 帧跳过逻辑
                self.frame_skip_counter += 1
                if frame_skip > 0 and self.frame_skip_counter % (frame_skip + 1) != 0:
                    time.sleep(self.target_frame_time * sleep_factor)
                    continue
                
                # 获取屏幕帧
                frame = self.capture_screen_frame()
                if frame is None:
                    continue
                
                # 应用画图（如果有）
                if hasattr(self, 'drawing_tool') and self.drawing_tool.shapes:
                    frame = self.drawing_tool.apply_drawings(frame)
                
                # 写入帧
                self.video_writer.write(frame)
                
                # 更新统计信息
                self.frame_count += 1
                self.last_frame_time = current_time
                
                # 计算实际FPS
                if self.frame_count % 30 == 0:  # 每30帧更新一次显示
                    actual_fps = 30 / (time.time() - (current_time - elapsed * 30))
                    self.root.after(0, lambda: self.fps_status_var.set(f"FPS: {actual_fps:.1f}"))
                
                # 性能优化：控制帧率（完整补偿休眠，尽量贴近目标帧率，避免帧数偏差导致快放/慢放）
                processing_time = time.time() - current_time
                sleep_time = max(0, self.target_frame_time - processing_time)
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    
            except Exception as e:
                print(f"❌ 录制错误: {e}")
                if self.recording:  # 如果还在录制，继续尝试
                    time.sleep(0.1)
                else:
                    break
    
    def capture_screen_frame(self):
        """捕获屏幕帧"""
        try:
            # 获取录制区域
            if self.recording_area == "follow":
                # 跟随鼠标模式
                area = self.mouse_tracker.get_tracking_area_around_cursor(
                    self.area_size[0], self.area_size[1]
                )
            elif self.recording_area:
                # 固定区域模式
                area = self.recording_area
            else:
                # 全屏模式
                area = None
            
            # 捕获屏幕
            if area:
                screenshot = ImageGrab.grab(bbox=area)
            else:
                screenshot = ImageGrab.grab()
            
            # 转换为OpenCV格式
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            return frame
            
        except Exception as e:
            print(f"❌ 捕获屏幕帧错误: {e}")
            return None
    
    def take_screenshot(self):
        """截图功能"""
        try:
            # 获取截图区域（与录制区域一致）
            if self.recording_area == "follow":
                area = self.mouse_tracker.get_tracking_area_around_cursor(
                    int(self.follow_width_var.get()), 
                    int(self.follow_height_var.get())
                )
            elif self.recording_area:
                area = self.recording_area
            else:
                area = None
            
            # 截图
            if area:
                screenshot = ImageGrab.grab(bbox=area)
            else:
                screenshot = ImageGrab.grab()
            
            # 保存截图
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_dir = os.path.join(self.output_dir, "Screenshots")
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            
            screenshot_file = os.path.join(screenshot_dir, f"screenshot_{timestamp}.png")
            screenshot.save(screenshot_file)
            
            # 应用画图（如果有）
            if hasattr(self, 'drawing_tool') and self.drawing_tool.shapes:
                # 将PIL图像转换为OpenCV格式进行绘制
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                frame_with_drawings = self.drawing_tool.apply_drawings(frame)
                # 转换回PIL格式保存
                screenshot_with_drawings = Image.fromarray(cv2.cvtColor(frame_with_drawings, cv2.COLOR_BGR2RGB))
                screenshot_with_drawings.save(screenshot_file)
            
            # 添加到临时文件列表（用于清理）
            self.temp_screenshots.append(screenshot_file)
            
            # 显示成功消息
            file_size = os.path.getsize(screenshot_file) / 1024  # KB
            messagebox.showinfo("截图成功", 
                              f"截图已保存！\n"
                              f"文件: {screenshot_file}\n"
                              f"大小: {file_size:.1f} KB")
            
            print(f"📸 截图已保存: {screenshot_file}")
            
        except Exception as e:
            messagebox.showerror("截图错误", f"截图失败: {str(e)}")
    
    def start_timer(self):
        """启动计时器"""
        self.recording_start_time = time.time()
        self.update_timer()
    
    def update_timer(self):
        """更新计时器"""
        if self.recording and not self.paused:
            elapsed = time.time() - self.recording_start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            self.recording_time_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # 更新文件大小显示（如果文件存在）
            if self.output_file and os.path.exists(self.output_file):
                file_size = os.path.getsize(self.output_file) / (1024 * 1024)  # MB
                self.file_size_var.set(f"大小: {file_size:.1f}MB")
        
        if self.recording:
            self.root.after(1000, self.update_timer)
    
    def stop_timer(self):
        """停止计时器"""
        # 计时器通过递归调用自动停止
        pass
    
    def update_ui_for_recording(self):
        """更新UI为录制状态"""
        self.start_button.config(state=tk.DISABLED, bg="#7f8c8d")
        self.pause_button.config(state=tk.NORMAL, bg="#f39c12")
        self.stop_button.config(state=tk.NORMAL, bg="#e74c3c")
        self.screenshot_button.config(state=tk.NORMAL)
        
        self.recording_status_var.set("🔴 录制中...")
        self.recording_time_var.set("00:00:00")
    
    def update_ui_for_stopped(self):
        """更新UI为停止状态"""
        self.start_button.config(state=tk.NORMAL, bg="#27ae60")
        self.pause_button.config(state=tk.DISABLED, bg="#7f8c8d")
        self.stop_button.config(state=tk.DISABLED, bg="#7f8c8d")
        
        self.recording_status_var.set("🔴 未开始录制")
        self.fps_status_var.set("FPS: --")
        self.file_size_var.set("大小: --")
    
    def cleanup_recording(self):
        """清理录制资源"""
        # 关闭视频写入器
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        
        # 停止音频录制
        self.stop_audio_recording()
        
        # 清理临时文件
        self.cleanup_temp_files()
        
        print("🧹 录制资源已清理")
    
    def fix_video_playback_speed(self):
        """校正视频播放速度：按实际捕获帧率重设视频帧率
        
        问题根源：视频写入器以目标FPS（如30）初始化，但实际捕获帧率往往低于
        目标值（屏幕抓取耗时、低性能模式跳帧等），导致视频文件帧数少于按目标
        FPS应有时长，播放时速度加快（快放），且与实时音频不同步。
        
        本方法根据 实际帧数/有效录制时长 计算真实帧率，用FFmpeg调整视频时间戳
        使播放时长与真实录制时长一致：
        - 方式一：-itsscale 时间戳缩放 + 流复制（无损、不重新编码）
        - 方式二：输入端 -r 重新编码（精确，作为回退）
        """
        if not self.output_file or not os.path.exists(self.output_file):
            return
        if not FFMPEG_AVAILABLE:
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
            actual_fps_str = f"{actual_fps:.3f}"
            
            # 方式一：-itsscale 时间戳缩放 + 流复制（无损、快速）
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-itsscale', f"{scale_factor:.6f}",
                '-i', self.output_file,
                '-c:v', 'copy',
                '-an',
                temp_corrected
            ]
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(temp_corrected) and os.path.getsize(temp_corrected) > 0:
                os.remove(self.output_file)
                os.rename(temp_corrected, self.output_file)
                print(f"✅ 视频帧率校正完成(无损): {actual_fps:.2f} FPS")
                return
            
            # 方式二：重封装失败则重新编码校正（输入端 -r 重新生成时间戳）
            if os.path.exists(temp_corrected):
                os.remove(temp_corrected)
            print("⚠️ 时间戳缩放失败，尝试重新编码...")
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-r', actual_fps_str,
                '-i', self.output_file,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '18',
                '-an',
                temp_corrected
            ]
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
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
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        try:
            # 清理临时音频文件
            if hasattr(self, 'temp_audio_file') and self.temp_audio_file and os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
            
            # 清理临时目录（保留截图）
            for file in os.listdir(self.temp_dir):
                if file.endswith('.wav') or file.endswith('.tmp'):
                    os.remove(os.path.join(self.temp_dir, file))
                    
        except Exception as e:
            print(f"❌ 清理临时文件错误: {e}")
    
    def on_closing(self):
        """程序关闭事件"""
        print("👋 正在关闭应用程序...")
        
        # 停止录制
        if self.recording:
            self.stop_recording()
        
        # 停止鼠标跟踪
        if hasattr(self, 'mouse_tracker'):
            self.mouse_tracker.stop_tracking()
        
        # 停止热键监听
        if hasattr(self, 'keyboard_listener'):
            self.keyboard_listener.stop()
        
        # 关闭画图工具窗口
        if hasattr(self, 'drawing_tool') and self.drawing_tool.drawing_window is not None:
            self.drawing_tool.drawing_window.destroy()
        
        # 清理临时目录
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
        
        print("✅ 应用程序已安全关闭")
        self.root.destroy()

class AreaSelector:
    """区域选择器类"""
    def __init__(self, root, recorder):
        self.root = root
        self.recorder = recorder
        self.selector_window = None
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.rect = None
    
    def start_selection(self):
        """开始区域选择"""
        # 创建全屏透明窗口
        self.selector_window = tk.Toplevel(self.root)
        self.selector_window.attributes('-fullscreen', True)
        self.selector_window.attributes('-alpha', 0.3)
        self.selector_window.configure(bg='black')
        self.selector_window.attributes('-topmost', True)
        
        # 创建画布用于绘制选择矩形
        self.canvas = tk.Canvas(self.selector_window, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定事件
        self.canvas.bind('<Button-1>', self.on_button_press)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_button_release)
        self.selector_window.bind('<Escape>', self.cancel_selection)
        
        # 显示说明文字
        self.canvas.create_text(
            self.selector_window.winfo_screenwidth() // 2,
            50,
            text="拖动鼠标选择录制区域，按ESC取消",
            fill="white",
            font=("Arial", 16, "bold")
        )
    
    def on_button_press(self, event):
        """鼠标按下事件"""
        self.start_x = event.x
        self.start_y = event.y
        
        # 创建选择矩形
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y,
            outline='red', width=2, fill='blue', stipple='gray50'
        )
    
    def on_mouse_drag(self, event):
        """鼠标拖动事件"""
        self.current_x = event.x
        self.current_y = event.y
        
        # 更新矩形
        self.canvas.coords(
            self.rect, self.start_x, self.start_y, self.current_x, self.current_y
        )
    
    def on_button_release(self, event):
        """鼠标释放事件"""
        self.current_x = event.x
        self.current_y = event.y
        
        # 确保坐标有效
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        width = x2 - x1
        height = y2 - y1
        
        # 设置最小尺寸
        if width < 100 or height < 100:
            messagebox.showwarning("区域太小", "请选择更大的区域（最小100x100像素）")
            self.cancel_selection()
            return
        
        # 更新录制器的区域设置
        self.recorder.width_var.set(str(width))
        self.recorder.height_var.set(str(height))
        self.recorder.area_mode.set("custom")
        self.recorder.update_area_mode()
        
        # 关闭选择窗口
        self.selector_window.destroy()
        
        messagebox.showinfo("区域选择", f"已选择区域: {width}x{height} 像素")
    
    def cancel_selection(self, event=None):
        """取消选择"""
        if self.selector_window:
            self.selector_window.destroy()
        messagebox.showinfo("取消", "区域选择已取消")

def main():
    """主函数"""
    try:
        # 显示MIT许可证协议
        if not show_license_agreement():
            print("❌ 用户不同意许可证协议，应用程序已退出")
            sys.exit(0)
        
        # 创建主窗口
        root = tk.Tk()
        
        # 创建录制器实例
        recorder = ScreenRecorder(root)
        
        # 设置关闭事件
        root.protocol("WM_DELETE_WINDOW", recorder.on_closing)
        
        # 启动主循环
        print("🚀 应用程序启动完成")
        print("=" * 60)
        root.mainloop()
        
    except Exception as e:
        print(f"❌ 应用程序错误: {e}")
        messagebox.showerror("错误", f"应用程序启动失败: {str(e)}")

def show_license_agreement():
    """显示MIT许可证协议对话框"""
    import urllib.request
    import ssl
    
    license_text = """
MIT License

Copyright (c) 2019-2025 七零喵网络互娱科技有限公司

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
    
    # 创建许可证对话框（作为独立窗口）
    license_root = tk.Tk()
    license_root.title("📜 MIT 许可证协议 - 必须同意才能继续")
    
    # 获取屏幕尺寸并设置合适的大小
    screen_width = license_root.winfo_screenwidth()
    screen_height = license_root.winfo_screenheight()
    
    # 设置窗口大小为屏幕的80%
    window_width = min(int(screen_width * 0.8), 900)
    window_height = min(int(screen_height * 0.85), 700)
    
    # 窗口居中
    x = (screen_width - window_width) // 2
    y = (screen_height - window_height) // 2
    license_root.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    # 允许调整大小
    license_root.resizable(True, True)
    
    # 设置窗口最小尺寸确保按钮可见
    license_root.minsize(600, 500)
    
    # 标题
    title_label = tk.Label(license_root, text="📜 MIT 许可证协议", font=("Arial", 16, "bold"))
    title_label.pack(pady=15)
    
    # 说明
    info_label = tk.Label(license_root, text="请仔细阅读以下许可证协议条款：", font=("Arial", 10))
    info_label.pack(pady=5)
    
    # 许可证文本框（带滚动条）
    text_frame = tk.Frame(license_root)
    text_frame.pack(pady=10, padx=20, fill="both", expand=True)
    
    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")
    
    license_textbox = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Arial", 10))
    license_textbox.insert("1.0", license_text)
    license_textbox.config(state="disabled")
    license_textbox.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=license_textbox.yview)
    
    # 尝试在线验证许可证
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        license_root.update()
    except:
        pass
    
    # 变量存储用户选择
    user_agreed = [False]
    
    def on_agree():
        user_agreed[0] = True
        license_root.destroy()
    
    def on_disagree():
        license_root.destroy()
        cleanup_and_exit()
    
    # 按钮框架 - 使用固定底部布局确保按钮始终可见
    button_frame = tk.Frame(license_root, bg="#f0f0f0", relief="raised", bd=2)
    button_frame.pack(side="bottom", fill="x", pady=15, padx=20)
    
    # 按钮容器 - 让按钮居中
    button_container = tk.Frame(button_frame)
    button_container.pack(anchor="center", pady=5)
    
    # 同意按钮（绿色）
    agree_button = tk.Button(button_container, text="✅ 同意并继续", font=("Arial", 14, "bold"),
                            bg="#4CAF50", fg="white", padx=30, pady=15,
                            command=on_agree, cursor="hand2")
    agree_button.pack(side="left", padx=30)
    
    # 不同意按钮（红色）
    disagree_button = tk.Button(button_container, text="❌ 不同意并退出", font=("Arial", 14, "bold"),
                               bg="#f44336", fg="white", padx=30, pady=15,
                               command=on_disagree, cursor="hand2")
    disagree_button.pack(side="left", padx=30)
    
    # 设置窗口模态
    license_root.transient()
    license_root.grab_set()
    
    # 等待窗口关闭
    license_root.wait_window()
    
    return user_agreed[0]

def cleanup_and_exit():
    """清理数据并退出应用"""
    try:
        # 清理临时目录
        temp_dir = tempfile.mkdtemp(prefix="screen_recorder_")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        # 清理FFmpeg目录（如果存在）
        ffmpeg_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ffmpeg")
        if os.path.exists(ffmpeg_dir):
            shutil.rmtree(ffmpeg_dir, ignore_errors=True)
        
        print("🧹 数据清理完成")
    except:
        pass
    
    messagebox.showinfo("退出", "您已不同意许可证协议，应用程序将退出。")
    sys.exit(0)

if __name__ == "__main__":
    main()
