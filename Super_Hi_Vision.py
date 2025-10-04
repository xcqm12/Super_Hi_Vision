import os
import sys
import time
import threading
import subprocess
import tempfile
import platform
import shutil
import json
from datetime import datetime
import math
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import cv2
import numpy as np
import wave
import pyaudio

# 版权信息
__author__ = "七零喵网络互娱科技有限公司"
__copyright__ = "Copyright 2019-2025, 七零喵网络互娱科技有限公司"
__version__ = "1.5.0"  # 优化性能，降低CPU功耗
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
        
        # 创建画图工具窗口
        self.create_drawing_window()
    
    def create_drawing_window(self):
        """创建画图工具窗口"""
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
        
        # 如果是矩形或圆形，保存最终图形
        if self.temp_shape:
            self.shapes.append(self.temp_shape)
            self.temp_shape = None
    
    def clear_all(self):
        """清除所有绘制内容"""
        self.shapes = []
        self.temp_shape = None
    
    def apply_drawings(self, frame):
        """将绘制的图形应用到帧上"""
        # 创建一个可绘制的副本
        frame_copy = frame.copy()
        
        # 绘制所有保存的图形
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
                                      (shape["y2"] - shape["y1"])** 2))
                cv2.circle(frame_copy, center, radius, shape["color"], shape["thickness"])
            elif shape["type"] == "text":
                font = cv2.FONT_HERSHEY_SIMPLEX
                cv2.putText(frame_copy, shape["text"], 
                           (shape["x"], shape["y"]), 
                           font, shape["size"] / 10,  # 调整字体大小
                           shape["color"], shape["thickness"], cv2.LINE_AA)
        
        # 绘制临时图形（如果有）
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
                                      (self.temp_shape["y2"] - self.temp_shape["y1"])** 2))
                cv2.circle(frame_copy, center, radius, self.temp_shape["color"], self.temp_shape["thickness"])
        
        return frame_copy

class MouseTracker:
    """鼠标跟踪器类"""
    def __init__(self):
        self.current_x = 0
        self.current_y = 0
        self.last_click_x = 0
        self.last_click_y = 0
        self.click_detected = False
        self.tracking_area = None  # (x, y, width, height)
        self.mouse_listener = None
        self.is_tracking = False
    
    def start_tracking(self):
        """开始跟踪鼠标"""
        if self.is_tracking:
            return
        
        def on_move(x, y):
            self.current_x = x
            self.current_y = y
        
        def on_click(x, y, button, pressed):
            if pressed:
                self.last_click_x = x
                self.last_click_y = y
                self.click_detected = True
                print(f"鼠标点击位置: ({x}, {y})")
        
        self.mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click)
        self.mouse_listener.start()
        self.is_tracking = True
    
    def stop_tracking(self):
        """停止跟踪鼠标"""
        if self.mouse_listener:
            self.mouse_listener.stop()
        self.is_tracking = False
    
    def get_tracking_area_around_click(self, width=800, height=600):
        """根据最后点击位置获取跟踪区域"""
        if not self.click_detected:
            return None
        
        # 计算区域，确保在屏幕范围内
        screen_width, screen_height = pyautogui.size()
        
        x1 = max(0, self.last_click_x - width // 2)
        y1 = max(0, self.last_click_y - height // 2)
        
        # 调整区域确保不超出屏幕
        if x1 + width > screen_width:
            x1 = screen_width - width
        if y1 + height > screen_height:
            y1 = screen_height - height
        
        x1 = max(0, x1)
        y1 = max(0, y1)
        
        self.tracking_area = (x1, y1, width, height)
        return self.tracking_area
    
    def get_tracking_area_around_cursor(self, width=800, height=600):
        """根据当前光标位置获取跟踪区域"""
        screen_width, screen_height = pyautogui.size()
        
        x1 = max(0, self.current_x - width // 2)
        y1 = max(0, self.current_y - height // 2)
        
        # 调整区域确保不超出屏幕
        if x1 + width > screen_width:
            x1 = screen_width - width
        if y1 + height > screen_height:
            y1 = screen_height - height
        
        x1 = max(0, x1)
        y1 = max(0, y1)
        
        self.tracking_area = (x1, y1, width, height)
        return self.tracking_area

class ScreenRecorder:
    """屏幕录制器类 - 优化版"""
    def __init__(self, root):
        self.root = root
        self.recording = False
        self.paused = False
        self.video_writer = None
        self.audio_writer = None
        self.audio_frames = []
        self.mouse_tracker = MouseTracker()
        
        # 音频相关变量 - 默认开启录制声音
        self.record_audio = True  # 默认开启音频录制
        self.audio_enabled = False
        self.audio_thread = None
        self.audio_stop_event = threading.Event()
        self.audio_device_index = None  # 音频设备索引
        self.audio_devices = []  # 初始化音频设备列表
        
        # 录制参数 - 新增蓝光、格式、编码器和FPS选项
        self.quality = "high"  # 包括新增的bluray选项
        self.format = "MP4"  # 默认格式
        self.codec = "libx264"  # 默认编码器
        self.fps = 30  # 默认FPS
        self.output_dir = os.path.expanduser("~/Videos")
        self.output_file = None
        self.temp_audio_file = None
        
        # 性能优化变量
        self.frame_count = 0
        self.last_frame_time = 0
        self.target_frame_time = 1.0 / self.fps
        self.performance_mode = "medium"  # 性能模式
        self.frame_skip_counter = 0
        
        # 新增：临时截图文件管理
        self.temp_screenshots = []
        self.temp_dir = tempfile.mkdtemp(prefix="screen_recorder_")
        
        # 初始化音频设备
        self.init_audio_devices()
        
        # 创建画图工具
        self.drawing_tool = DrawingTool(self)
        
        # 创建界面
        self.create_gui()
        
        # 启动鼠标跟踪
        self.mouse_tracker.start_tracking()
        
        # 设置热键监听
        self.setup_hotkeys()
        
        print("✅ 屏幕录制器初始化完成 - 优化版")
        print(f"📁 临时目录: {self.temp_dir}")
    
    def init_audio_devices(self):
        """初始化音频设备列表"""
        try:
            p = pyaudio.PyAudio()
            self.audio_devices = []
            
            for i in range(p.get_device_count()):
                dev_info = p.get_device_info_by_index(i)
                if dev_info.get('maxInputChannels', 0) > 0:
                    self.audio_devices.append({
                        'index': i,
                        'name': dev_info.get('name', f'设备 {i}')
                    })
            
            p.terminate()
            
            if self.audio_devices:
                self.audio_device_index = self.audio_devices[0]['index']
                print(f"✅ 找到 {len(self.audio_devices)} 个音频输入设备")
            else:
                print("❌ 未找到可用的音频输入设备")
                self.record_audio = False
                
        except Exception as e:
            print(f"❌ 初始化音频设备失败: {e}")
            self.record_audio = False
    
    def create_gui(self):
        """创建图形用户界面"""
        self.root.title(f"🎬 高级超高清屏幕录制工具 - 优化版 v{__version__}")
        self.root.geometry("800x700")
        self.root.configure(bg="#2c3e50")
        
        # 设置窗口图标
        try:
            self.root.iconbitmap(default=self.get_icon_path())
        except:
            pass
        
        # 主框架
        main_frame = tk.Frame(self.root, bg="#2c3e50")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 标题
        title_frame = tk.Frame(main_frame, bg="#2c3e50")
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(title_frame, text="🎬 高级超高清屏幕录制工具", 
                font=("Arial", 20, "bold"), fg="white", bg="#2c3e50").pack()
        
        tk.Label(title_frame, text=f"版本 {__version__} | 优化性能，降低CPU功耗", 
                font=("Arial", 10), fg="#bdc3c7", bg="#2c3e50").pack()
        
        # 创建标签页
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 基本设置标签页
        basic_frame = tk.Frame(notebook, bg="#34495e")
        notebook.add(basic_frame, text="🎯 基本设置")
        
        # 录制设置标签页
        advanced_frame = tk.Frame(notebook, bg="#34495e")
        notebook.add(advanced_frame, text="⚙️ 高级设置")
        
        # 音频设置标签页
        audio_frame = tk.Frame(notebook, bg="#34495e")
        notebook.add(audio_frame, text="🎵 音频设置")
        
        # 热键设置标签页
        hotkey_frame = tk.Frame(notebook, bg="#34495e")
        notebook.add(hotkey_frame, text="⌨️ 热键设置")
        
        # 填充基本设置标签页
        self.create_basic_tab(basic_frame)
        
        # 填充高级设置标签页
        self.create_advanced_tab(advanced_frame)
        
        # 填充音频设置标签页
        self.create_audio_tab(audio_frame)
        
        # 填充热键设置标签页
        self.create_hotkey_tab(hotkey_frame)
        
        # 状态栏
        self.create_status_bar(main_frame)
        
        # 控制按钮
        self.create_control_buttons(main_frame)
    
    def create_basic_tab(self, parent):
        """创建基本设置标签页"""
        # 录制区域设置
        area_frame = tk.LabelFrame(parent, text="📐 录制区域设置", 
                                 font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        area_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 录制模式选择
        mode_frame = tk.Frame(area_frame, bg="#34495e")
        mode_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.area_mode = tk.StringVar(value="fullscreen")
        
        tk.Radiobutton(mode_frame, text="全屏录制", variable=self.area_mode,
                      value="fullscreen", bg="#34495e", fg="white", 
                      selectcolor="#2c3e50", command=self.update_area_mode).pack(side=tk.LEFT)
        
        tk.Radiobutton(mode_frame, text="自定义区域", variable=self.area_mode,
                      value="custom", bg="#34495e", fg="white",
                      selectcolor="#2c3e50", command=self.update_area_mode).pack(side=tk.LEFT, padx=(20,0))
        
        tk.Radiobutton(mode_frame, text="跟随鼠标", variable=self.area_mode,
                      value="follow_mouse", bg="#34495e", fg="white",
                      selectcolor="#2c3e50", command=self.update_area_mode).pack(side=tk.LEFT, padx=(20,0))
        
        # 自定义区域设置
        self.custom_frame = tk.Frame(area_frame, bg="#34495e")
        self.custom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.custom_frame, text="宽度:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="1920")
        tk.Entry(self.custom_frame, textvariable=self.width_var, width=8).pack(side=tk.LEFT, padx=(5,15))
        
        tk.Label(self.custom_frame, text="高度:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="1080")
        tk.Entry(self.custom_frame, textvariable=self.height_var, width=8).pack(side=tk.LEFT, padx=(5,15))
        
        tk.Button(self.custom_frame, text="选择区域", bg="#3498db", fg="white",
                 command=self.select_area).pack(side=tk.LEFT)
        
        # 跟随鼠标设置
        self.follow_frame = tk.Frame(area_frame, bg="#34495e")
        self.follow_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(self.follow_frame, text="区域大小:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.follow_width_var = tk.StringVar(value="800")
        tk.Entry(self.follow_frame, textvariable=self.follow_width_var, width=6).pack(side=tk.LEFT, padx=(5,5))
        
        tk.Label(self.follow_frame, text="x", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.follow_height_var = tk.StringVar(value="600")
        tk.Entry(self.follow_frame, textvariable=self.follow_height_var, width=6).pack(side=tk.LEFT, padx=(5,15))
        
        tk.Button(self.follow_frame, text="测试跟随", bg="#9b59b6", fg="white",
                 command=self.test_follow).pack(side=tk.LEFT)
        
        # 更新区域模式显示
        self.update_area_mode()
        
        # 输出设置
        output_frame = tk.LabelFrame(parent, text="💾 输出设置", 
                                   font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        output_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 文件名设置
        name_frame = tk.Frame(output_frame, bg="#34495e")
        name_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(name_frame, text="文件名:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.filename_var = tk.StringVar(value=f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        tk.Entry(name_frame, textvariable=self.filename_var, width=30).pack(side=tk.LEFT, padx=(10,10))
        
        tk.Button(name_frame, text="浏览", bg="#3498db", fg="white",
                 command=self.browse_output_dir).pack(side=tk.LEFT)
        
        # 输出目录显示
        dir_frame = tk.Frame(output_frame, bg="#34495e")
        dir_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(dir_frame, text="输出目录:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.output_dir_var = tk.StringVar(value=self.output_dir)
        dir_label = tk.Label(dir_frame, textvariable=self.output_dir_var, 
                           bg="#34495e", fg="#bdc3c7", anchor=tk.W)
        dir_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10,0))
        
        # 新增：自定义输出路径设置
        custom_path_frame = tk.Frame(output_frame, bg="#34495e")
        custom_path_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(custom_path_frame, text="自定义输出路径:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        
        self.custom_output_path_var = tk.StringVar(value="")
        custom_path_entry = tk.Entry(custom_path_frame, textvariable=self.custom_output_path_var, width=40)
        custom_path_entry.pack(side=tk.LEFT, padx=(10,5), fill=tk.X, expand=True)
        
        tk.Button(custom_path_frame, text="选择文件", bg="#9b59b6", fg="white",
                 command=self.browse_custom_output_file).pack(side=tk.LEFT, padx=(0,5))
        
        tk.Button(custom_path_frame, text="使用默认", bg="#95a5a6", fg="white",
                 command=self.use_default_output).pack(side=tk.LEFT)
    
    def create_advanced_tab(self, parent):
        """创建高级设置标签页"""
        # 视频格式设置
        format_frame = tk.LabelFrame(parent, text="🎥 视频格式设置", 
                                   font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        format_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 格式选择
        format_row1 = tk.Frame(format_frame, bg="#34495e")
        format_row1.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(format_row1, text="输出格式:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.format_var = tk.StringVar(value="MP4")
        format_combo = ttk.Combobox(format_row1, textvariable=self.format_var, 
                                   values=list(SUPPORTED_FORMATS.keys()), state="readonly", width=15)
        format_combo.pack(side=tk.LEFT, padx=(10,20))
        format_combo.bind('<<ComboboxSelected>>', self.on_format_change)
        
        tk.Label(format_row1, text="编码器:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.codec_var = tk.StringVar(value="H.264 (libx264)")
        codec_combo = ttk.Combobox(format_row1, textvariable=self.codec_var, 
                                  values=list(SUPPORTED_CODECS.keys()), state="readonly", width=20)
        codec_combo.pack(side=tk.LEFT, padx=(10,0))
        
        # FPS设置
        format_row2 = tk.Frame(format_frame, bg="#34495e")
        format_row2.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(format_row2, text="帧率(FPS):", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.fps_var = tk.StringVar(value="30 FPS (标准)")
        fps_combo = ttk.Combobox(format_row2, textvariable=self.fps_var, 
                                values=list(FPS_OPTIONS.keys()), state="readonly", width=20)
        fps_combo.pack(side=tk.LEFT, padx=(10,20))
        fps_combo.bind('<<ComboboxSelected>>', self.on_fps_change)
        
        # 质量设置
        quality_frame = tk.LabelFrame(parent, text="📊 录制质量", 
                                    font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        quality_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 质量预设
        preset_frame = tk.Frame(quality_frame, bg="#34495e")
        preset_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.quality_var = tk.StringVar(value="high")
        
        qualities = [
            ("低功耗 (15fps, 500kbps)", "low"),
            ("标准 (30fps, 2Mbps)", "medium"),
            ("高清 (30fps, 5Mbps)", "high"),
            ("超清 (60fps, 10Mbps)", "ultra"),
            ("蓝光 (60fps, 25Mbps)", "bluray")
        ]
        
        for text, value in qualities:
            tk.Radiobutton(preset_frame, text=text, variable=self.quality_var,
                          value=value, bg="#34495e", fg="white", 
                          selectcolor="#2c3e50", command=self.update_quality).pack(anchor=tk.W)
        
        # 性能优化设置
        perf_frame = tk.LabelFrame(parent, text="⚡ 性能优化", 
                                 font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        perf_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.performance_var = tk.StringVar(value="medium")
        
        perf_options = [
            ("低功耗模式 (CPU占用低)", "low"),
            ("平衡模式 (推荐)", "medium"),
            ("高性能模式 (质量优先)", "high"),
            ("极致模式 (最佳质量)", "ultra")
        ]
        
        for text, value in perf_options:
            tk.Radiobutton(perf_frame, text=text, variable=self.performance_var,
                          value=value, bg="#34495e", fg="white", 
                          selectcolor="#2c3e50", command=self.update_performance).pack(anchor=tk.W)
        
        # 画图工具按钮
        drawing_frame = tk.Frame(parent, bg="#34495e")
        drawing_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(drawing_frame, text="🎨 打开画图工具", bg="#e67e22", fg="white",
                 font=("Arial", 10, "bold"), command=self.open_drawing_tool).pack(pady=5)
    
    def create_audio_tab(self, parent):
        """创建音频设置标签页"""
        # 音频录制开关
        audio_switch_frame = tk.LabelFrame(parent, text="🔊 音频录制", 
                                         font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        audio_switch_frame.pack(fill=tk.X, padx=10, pady=10)
        
        switch_frame = tk.Frame(audio_switch_frame, bg="#34495e")
        switch_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.audio_enabled_var = tk.BooleanVar(value=self.record_audio)
        audio_switch = tk.Checkbutton(switch_frame, text="启用音频录制", 
                                    variable=self.audio_enabled_var,
                                    bg="#34495e", fg="white", selectcolor="#2c3e50",
                                    command=self.toggle_audio_recording)
        audio_switch.pack(anchor=tk.W)
        
        # 音频设备选择
        device_frame = tk.LabelFrame(parent, text="🎤 音频设备", 
                                   font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        device_frame.pack(fill=tk.X, padx=10, pady=10)
        
        if self.audio_devices:
            tk.Label(device_frame, text="选择输入设备:", bg="#34495e", fg="white").pack(anchor=tk.W, padx=10, pady=5)
            
            self.audio_device_var = tk.StringVar()
            device_names = [f"{dev['index']}: {dev['name']}" for dev in self.audio_devices]
            
            device_combo = ttk.Combobox(device_frame, textvariable=self.audio_device_var, 
                                      values=device_names, state="readonly", width=50)
            device_combo.pack(fill=tk.X, padx=10, pady=5)
            device_combo.set(device_names[0])
            device_combo.bind('<<ComboboxSelected>>', self.on_audio_device_change)
        else:
            tk.Label(device_frame, text="❌ 未找到可用的音频输入设备", 
                    bg="#34495e", fg="#e74c3c").pack(padx=10, pady=10)
        
        # 音频测试
        test_frame = tk.LabelFrame(parent, text="🎧 音频测试", 
                                 font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        test_frame.pack(fill=tk.X, padx=10, pady=10)
        
        test_buttons_frame = tk.Frame(test_frame, bg="#34495e")
        test_buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(test_buttons_frame, text="🔊 测试音频输入", bg="#3498db", fg="white",
                 command=self.test_audio_input).pack(side=tk.LEFT, padx=5)
        
        tk.Button(test_buttons_frame, text="🔄 刷新设备列表", bg="#9b59b6", fg="white",
                 command=self.refresh_audio_devices).pack(side=tk.LEFT, padx=5)
        
        # 音频状态显示
        self.audio_status_var = tk.StringVar()
        if AUDIO_SUPPORT:
            self.audio_status_var.set("✅ 音频支持已启用")
        else:
            self.audio_status_var.set("❌ 音频支持不可用")
        
        status_label = tk.Label(test_frame, textvariable=self.audio_status_var, 
                              bg="#34495e", fg="#bdc3c7")
        status_label.pack(pady=5)
    
    def create_hotkey_tab(self, parent):
        """创建热键设置标签页"""
        # 热键说明
        desc_frame = tk.LabelFrame(parent, text="⌨️ 热键说明", 
                                 font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        desc_frame.pack(fill=tk.X, padx=10, pady=10)
        
        hotkey_text = """
全局热键（录制过程中可用）：
• F9  - 开始/暂停录制
• F10 - 停止录制
• F11 - 截图（录制中也可用）
• F12 - 显示/隐藏画图工具

画图工具热键：
• 鼠标左键 - 开始绘制
• 鼠标移动 - 持续绘制
• 鼠标释放 - 停止绘制
• C键     - 清除所有绘制
• ESC键   - 退出画图模式

注意：热键在应用程序窗口激活时生效
        """
        
        hotkey_label = tk.Label(desc_frame, text=hotkey_text, justify=tk.LEFT,
                              bg="#34495e", fg="#bdc3c7", font=("Consolas", 10))
        hotkey_label.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # 自定义热键设置
        custom_frame = tk.LabelFrame(parent, text="🔧 自定义热键", 
                                   font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        custom_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # 开始/暂停热键
        start_frame = tk.Frame(custom_frame, bg="#34495e")
        start_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(start_frame, text="开始/暂停:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.start_hotkey_var = tk.StringVar(value="F9")
        tk.Entry(start_frame, textvariable=self.start_hotkey_var, width=10).pack(side=tk.LEFT, padx=(10,20))
        
        # 停止热键
        stop_frame = tk.Frame(custom_frame, bg="#34495e")
        stop_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(stop_frame, text="停止录制:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.stop_hotkey_var = tk.StringVar(value="F10")
        tk.Entry(stop_frame, textvariable=self.stop_hotkey_var, width=10).pack(side=tk.LEFT, padx=(10,20))
        
        # 截图热键
        screenshot_frame = tk.Frame(custom_frame, bg="#34495e")
        screenshot_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(screenshot_frame, text="截图:", bg="#34495e", fg="white").pack(side=tk.LEFT)
        self.screenshot_hotkey_var = tk.StringVar(value="F11")
        tk.Entry(screenshot_frame, textvariable=self.screenshot_hotkey_var, width=10).pack(side=tk.LEFT, padx=(10,20))
        
        # 应用热键按钮
        apply_frame = tk.Frame(custom_frame, bg="#34495e")
        apply_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(apply_frame, text="💾 应用热键设置", bg="#27ae60", fg="white",
                 command=self.apply_hotkeys).pack()
    
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = tk.Frame(parent, bg="#34495e")
        status_frame.pack(fill=tk.X, pady=(20, 10))
        
        # 录制状态
        self.recording_status_var = tk.StringVar(value="🔴 未开始录制")
        status_label = tk.Label(status_frame, textvariable=self.recording_status_var,
                              font=("Arial", 12, "bold"), bg="#34495e", fg="white")
        status_label.pack(side=tk.LEFT)
        
        # 录制时间
        self.recording_time_var = tk.StringVar(value="00:00:00")
        time_label = tk.Label(status_frame, textvariable=self.recording_time_var,
                            font=("Arial", 12), bg="#34495e", fg="#bdc3c7")
        time_label.pack(side=tk.RIGHT)
        
        # 帧率显示
        self.fps_status_var = tk.StringVar(value="FPS: --")
        fps_label = tk.Label(status_frame, textvariable=self.fps_status_var,
                           font=("Arial", 10), bg="#34495e", fg="#bdc3c7")
        fps_label.pack(side=tk.RIGHT, padx=(0, 20))
        
        # 文件大小显示
        self.file_size_var = tk.StringVar(value="大小: --")
        size_label = tk.Label(status_frame, textvariable=self.file_size_var,
                            font=("Arial", 10), bg="#34495e", fg="#bdc3c7")
        size_label.pack(side=tk.RIGHT, padx=(0, 20))
    
    def create_control_buttons(self, parent):
        """创建控制按钮"""
        button_frame = tk.Frame(parent, bg="#2c3e50")
        button_frame.pack(fill=tk.X, pady=10)
        
        # 开始录制按钮
        self.start_button = tk.Button(button_frame, text="🎬 开始录制 (F9)", 
                                    font=("Arial", 14, "bold"), bg="#27ae60", fg="white",
                                    width=15, height=2, command=self.start_recording)
        self.start_button.pack(side=tk.LEFT, padx=10)
        
        # 暂停录制按钮
        self.pause_button = tk.Button(button_frame, text="⏸️ 暂停录制 (F9)", 
                                    font=("Arial", 14, "bold"), bg="#f39c12", fg="white",
                                    width=15, height=2, command=self.pause_recording,
                                    state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=10)
        
        # 停止录制按钮
        self.stop_button = tk.Button(button_frame, text="⏹️ 停止录制 (F10)", 
                                   font=("Arial", 14, "bold"), bg="#e74c3c", fg="white",
                                   width=15, height=2, command=self.stop_recording,
                                   state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=10)
        
        # 截图按钮
        self.screenshot_button = tk.Button(button_frame, text="📸 截图 (F11)", 
                                         font=("Arial", 12, "bold"), bg="#3498db", fg="white",
                                         width=12, height=2, command=self.take_screenshot)
        self.screenshot_button.pack(side=tk.LEFT, padx=10)
    
    def update_area_mode(self):
        """更新区域模式显示"""
        mode = self.area_mode.get()
        
        # 隐藏所有区域设置框架
        self.custom_frame.pack_forget()
        self.follow_frame.pack_forget()
        
        # 显示对应的设置框架
        if mode == "custom":
            self.custom_frame.pack(fill=tk.X, padx=10, pady=5)
        elif mode == "follow_mouse":
            self.follow_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def update_quality(self):
        """更新质量设置"""
        quality = self.quality_var.get()
        preset = QUALITY_PRESETS[quality]
        self.fps = preset["fps"]
        self.target_frame_time = 1.0 / self.fps
        
        # 更新FPS显示
        for name, fps_value in FPS_OPTIONS.items():
            if fps_value == self.fps:
                self.fps_var.set(name)
                break
        
        print(f"✅ 质量设置更新: {quality}, FPS: {self.fps}")
    
    def update_performance(self):
        """更新性能模式"""
        self.performance_mode = self.performance_var.get()
        print(f"✅ 性能模式更新: {self.performance_mode}")
    
    def on_format_change(self, event=None):
        """格式改变事件"""
        self.format = self.format_var.get()
        print(f"✅ 输出格式更新: {self.format}")
    
    def on_fps_change(self, event=None):
        """FPS改变事件"""
        fps_name = self.fps_var.get()
        self.fps = FPS_OPTIONS.get(fps_name, 30)
        self.target_frame_time = 1.0 / self.fps
        print(f"✅ FPS更新: {self.fps}")
    
    def on_audio_device_change(self, event=None):
        """音频设备改变事件"""
        if hasattr(self, 'audio_device_var') and self.audio_device_var.get():
            device_str = self.audio_device_var.get()
            try:
                self.audio_device_index = int(device_str.split(':')[0])
                print(f"✅ 音频设备更新: {device_str}")
            except:
                print("❌ 音频设备选择错误")
    
    def toggle_audio_recording(self):
        """切换音频录制状态"""
        self.record_audio = self.audio_enabled_var.get()
        if self.record_audio and not AUDIO_SUPPORT:
            messagebox.showwarning("音频不可用", "音频录制功能当前不可用，请检查音频设备或安装必要的依赖。")
            self.record_audio = False
            self.audio_enabled_var.set(False)
        print(f"✅ 音频录制: {'启用' if self.record_audio else '禁用'}")
    
    def select_area(self):
        """选择录制区域"""
        messagebox.showinfo("选择区域", "请拖动鼠标选择录制区域\n\n完成后按ESC键确认")
        
        # 创建全屏透明窗口用于区域选择
        self.area_selector = AreaSelector(self.root, self)
        self.area_selector.start_selection()
    
    def test_follow(self):
        """测试跟随鼠标模式"""
        if self.area_mode.get() == "follow_mouse":
            try:
                width = int(self.follow_width_var.get())
                height = int(self.follow_height_var.get())
                messagebox.showinfo("测试跟随", f"将测试 {width}x{height} 的跟随区域\n移动鼠标查看效果")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的宽度和高度数值")
        else:
            messagebox.showinfo("提示", "请先选择'跟随鼠标'模式")
    
    def browse_output_dir(self):
        """浏览输出目录"""
        directory = filedialog.askdirectory(initialdir=self.output_dir)
        if directory:
            self.output_dir = directory
            self.output_dir_var.set(directory)
            print(f"✅ 输出目录更新: {directory}")
    
    def browse_custom_output_file(self):
        """浏览自定义输出文件"""
        # 获取当前选择的格式
        format_info = SUPPORTED_FORMATS.get(self.format, SUPPORTED_FORMATS["MP4"])
        file_ext = format_info["ext"]
        
        # 设置默认文件名
        default_filename = f"screen_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
        
        # 打开文件选择对话框
        file_path = filedialog.asksaveasfilename(
            title="选择输出文件",
            initialdir=self.output_dir,
            initialfile=default_filename,
            defaultextension=f".{file_ext}",
            filetypes=[
                (f"{self.format} 文件", f"*.{file_ext}"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.custom_output_path_var.set(file_path)
            print(f"✅ 自定义输出路径: {file_path}")
    
    def use_default_output(self):
        """使用默认输出路径"""
        self.custom_output_path_var.set("")
        print("✅ 使用默认输出路径")
    
    def open_drawing_tool(self):
        """打开画图工具"""
        try:
            if hasattr(self, 'drawing_tool') and hasattr(self.drawing_tool, 'drawing_window'):
                self.drawing_tool.drawing_window.deiconify()
                self.drawing_tool.drawing_window.lift()
            else:
                self.drawing_tool = DrawingTool(self)
        except Exception as e:
            print(f"❌ 打开画图工具失败: {e}")
            self.drawing_tool = DrawingTool(self)
    
    def test_audio_input(self):
        """测试音频输入"""
        if not AUDIO_SUPPORT:
            messagebox.showerror("音频不可用", "音频录制功能当前不可用")
            return
        
        try:
            import pyaudio
            import wave
            
            # 音频参数
            FORMAT = pyaudio.paInt16
            CHANNELS = 1
            RATE = 44100
            CHUNK = 1024
            RECORD_SECONDS = 3
            WAVE_OUTPUT_FILENAME = os.path.join(self.temp_dir, "audio_test.wav")
            
            audio = pyaudio.PyAudio()
            
            # 获取选定的音频设备
            device_index = self.audio_device_index if hasattr(self, 'audio_device_index') else None
            
            # 开始录制
            stream = audio.open(format=FORMAT, channels=CHANNELS,
                              rate=RATE, input=True,
                              input_device_index=device_index,
                              frames_per_buffer=CHUNK)
            
            messagebox.showinfo("音频测试", "正在录制3秒音频...")
            
            frames = []
            for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                data = stream.read(CHUNK)
                frames.append(data)
            
            # 停止录制
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # 保存文件
            wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(audio.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            messagebox.showinfo("测试成功", f"音频测试完成！\n文件保存至: {WAVE_OUTPUT_FILENAME}")
            
        except Exception as e:
            messagebox.showerror("测试失败", f"音频测试失败: {str(e)}")
    
    def refresh_audio_devices(self):
        """刷新音频设备列表"""
        self.init_audio_devices()
        messagebox.showinfo("刷新完成", f"找到 {len(self.audio_devices)} 个音频设备")
    
    def apply_hotkeys(self):
        """应用热键设置"""
        messagebox.showinfo("热键设置", "热键设置已应用！\n\n注意：部分热键可能需要重启程序才能生效")
    
    def setup_hotkeys(self):
        """设置热键监听"""
        try:
            # 创建键盘监听器
            def on_press(key):
                try:
                    if hasattr(key, 'char') and key.char:
                        key_char = key.char.lower()
                        # 画图工具热键
                        if hasattr(self, 'drawing_tool') and self.drawing_tool.drawing_window.winfo_viewable():
                            if key_char == 'c':  # 清除绘制
                                self.drawing_tool.clear_all()
                            elif key == keyboard.Key.esc:  # 退出画图
                                self.drawing_tool.drawing_window.withdraw()
                    
                    # 功能热键
                    if key == keyboard.Key.f9:
                        if self.recording:
                            self.pause_recording()
                        else:
                            self.start_recording()
                    elif key == keyboard.Key.f10 and self.recording:
                        self.stop_recording()
                    elif key == keyboard.Key.f11:
                        self.take_screenshot()
                    elif key == keyboard.Key.f12:
                        self.open_drawing_tool()
                        
                except Exception as e:
                    print(f"热键处理错误: {e}")
            
            # 启动监听器
            self.keyboard_listener = keyboard.Listener(on_press=on_press)
            self.keyboard_listener.start()
            print("✅ 热键监听器已启动")
            
        except Exception as e:
            print(f"❌ 热键设置失败: {e}")
    
    def get_icon_path(self):
        """获取图标路径"""
        try:
            # 尝试创建临时图标文件
            icon_path = os.path.join(self.temp_dir, "icon.ico")
            
            # 这里可以添加创建图标的代码
            # 暂时返回空字符串，使用系统默认图标
            return ""
        except:
            return ""
    
    def start_recording(self):
        """开始录制"""
        try:
            if self.recording:
                return
            
            # 获取录制参数
            self.get_recording_params()
            
            # 创建输出文件
            self.create_output_file()
            
            # 初始化视频写入器
            if not self.init_video_writer():
                return
            
            # 启动音频录制（如果启用）
            if self.record_audio and AUDIO_SUPPORT:
                self.start_audio_recording()
            
            # 更新状态
            self.recording = True
            self.paused = False
            self.recording_start_time = time.time()
            self.last_frame_time = time.time()
            self.frame_count = 0
            
            # 更新UI
            self.update_ui_for_recording()
            
            # 启动录制线程
            self.recording_thread = threading.Thread(target=self.record_screen, daemon=True)
            self.recording_thread.start()
            
            # 启动计时器
            self.start_timer()
            
            print("🎬 开始屏幕录制...")
            
        except Exception as e:
            messagebox.showerror("录制错误", f"开始录制失败: {str(e)}")
            self.cleanup_recording()
    
    def pause_recording(self):
        """暂停/恢复录制"""
        if not self.recording:
            return
        
        self.paused = not self.paused
        
        if self.paused:
            # 暂停音频录制
            if self.audio_enabled:
                self.audio_stop_event.set()
            
            self.pause_button.config(text="▶️ 恢复录制 (F9)", bg="#27ae60")
            self.recording_status_var.set("⏸️ 录制已暂停")
            print("⏸️ 录制暂停")
        else:
            # 恢复音频录制
            if self.record_audio and AUDIO_SUPPORT and not self.audio_enabled:
                self.start_audio_recording()
            
            self.pause_button.config(text="⏸️ 暂停录制 (F9)", bg="#f39c12")
            self.recording_status_var.set("🔴 录制中...")
            print("▶️ 录制恢复")
    
    def stop_recording(self):
        """停止录制"""
        if not self.recording:
            return
        
        print("⏹️ 停止录制...")
        
        # 停止计时器
        self.stop_timer()
        
        # 更新状态
        self.recording = False
        self.paused = False
        
        # 停止音频录制
        self.stop_audio_recording()
        
        # 等待录制线程结束
        if hasattr(self, 'recording_thread') and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)
        
        # 清理资源
        self.cleanup_recording()
        
        # 合并音视频（如果录制了音频）
        if self.record_audio and AUDIO_SUPPORT and self.audio_frames:
            self.merge_audio_video()
        
        # 更新UI
        self.update_ui_for_stopped()
        
        # 显示完成消息
        if self.output_file and os.path.exists(self.output_file):
            file_size = os.path.getsize(self.output_file) / (1024 * 1024)  # MB
            messagebox.showinfo("录制完成", 
                              f"录制已完成！\n"
                              f"文件: {self.output_file}\n"
                              f"大小: {file_size:.2f} MB\n"
                              f"时长: {self.recording_time_var.get()}")
        else:
            messagebox.showinfo("录制完成", "录制已停止")
    
    def get_recording_params(self):
        """获取录制参数"""
        # 获取录制区域
        mode = self.area_mode.get()
        if mode == "fullscreen":
            self.recording_area = None  # 全屏
            self.area_size = pyautogui.size()
        elif mode == "custom":
            try:
                width = int(self.width_var.get())
                height = int(self.height_var.get())
                self.recording_area = (0, 0, width, height)  # 从左上角开始
                self.area_size = (width, height)
            except ValueError:
                messagebox.showerror("错误", "请输入有效的宽度和高度数值")
                raise
        elif mode == "follow_mouse":
            try:
                width = int(self.follow_width_var.get())
                height = int(self.follow_height_var.get())
                self.recording_area = "follow"  # 特殊标记
                self.area_size = (width, height)
            except ValueError:
                messagebox.showerror("错误", "请输入有效的宽度和高度数值")
                raise
        
        # 获取其他参数
        self.quality = self.quality_var.get()
        self.format = self.format_var.get()
        self.fps = FPS_OPTIONS.get(self.fps_var.get(), 30)
        self.codec = SUPPORTED_CODECS.get(self.codec_var.get(), "libx264")
        self.performance_mode = self.performance_var.get()
        
        print(f"📊 录制参数: {self.area_size}, FPS: {self.fps}, 质量: {self.quality}")
    
    def create_output_file(self):
        """创建输出文件"""
        # 检查是否使用自定义输出路径
        custom_path = self.custom_output_path_var.get().strip()
        if custom_path:
            # 使用自定义路径
            self.output_file = custom_path
            
            # 确保目录存在
            output_dir = os.path.dirname(self.output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"✅ 创建输出目录: {output_dir}")
        else:
            # 使用默认路径生成
            # 确保输出目录存在
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
            
            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = self.filename_var.get() or f"screen_recording_{timestamp}"
            
            # 添加格式扩展名
            format_info = SUPPORTED_FORMATS.get(self.format, SUPPORTED_FORMATS["MP4"])
            file_ext = format_info["ext"]
            
            self.output_file = os.path.join(self.output_dir, f"{base_name}.{file_ext}")
            
            # 如果文件已存在，添加数字后缀
            counter = 1
            original_file = self.output_file
            while os.path.exists(self.output_file):
                self.output_file = original_file.replace(f".{file_ext}", f"_{counter}.{file_ext}")
                counter += 1
        
        print(f"💾 输出文件: {self.output_file}")
    
    def init_video_writer(self):
        """初始化视频写入器"""
        try:
            # 获取FourCC编码
            format_info = SUPPORTED_FORMATS.get(self.format, SUPPORTED_FORMATS["MP4"])
            fourcc = cv2.VideoWriter_fourcc(*format_info["fourcc"])
            
            # 创建视频写入器
            self.video_writer = cv2.VideoWriter(
                self.output_file,
                fourcc,
                self.fps,
                self.area_size
            )
            
            if not self.video_writer.isOpened():
                messagebox.showerror("错误", "无法创建视频文件，请检查编码器和格式设置")
                return False
            
            return True
            
        except Exception as e:
            messagebox.showerror("错误", f"初始化视频写入器失败: {str(e)}")
            return False
    
    def start_audio_recording(self):
        """开始音频录制"""
        if not self.record_audio or not AUDIO_SUPPORT:
            return
        
        try:
            import pyaudio
            
            # 音频参数
            self.audio_format = pyaudio.paInt16
            self.audio_channels = 1
            self.audio_rate = 44100
            self.audio_chunk = 1024
            self.audio_frames = []
            
            # 创建PyAudio实例
            self.audio = pyaudio.PyAudio()
            
            # 打开音频流
            self.audio_stream = self.audio.open(
                format=self.audio_format,
                channels=self.audio_channels,
                rate=self.audio_rate,
                input=True,
                input_device_index=self.audio_device_index,
                frames_per_buffer=self.audio_chunk
            )
            
            self.audio_enabled = True
            self.audio_stop_event.clear()
            
            # 启动音频录制线程
            self.audio_thread = threading.Thread(target=self.record_audio_thread, daemon=True)
            self.audio_thread.start()
            
            print("🎵 音频录制已启动")
            
        except Exception as e:
            print(f"❌ 启动音频录制失败: {e}")
            self.audio_enabled = False
    
    def record_audio_thread(self):
        """音频录制线程"""
        try:
            while not self.audio_stop_event.is_set() and self.audio_enabled:
                data = self.audio_stream.read(self.audio_chunk, exception_on_overflow=False)
                self.audio_frames.append(data)
        except Exception as e:
            print(f"❌ 音频录制错误: {e}")
    
    def stop_audio_recording(self):
        """停止音频录制"""
        if self.audio_enabled:
            self.audio_stop_event.set()
            self.audio_enabled = False
            
            if hasattr(self, 'audio_stream'):
                self.audio_stream.stop_stream()
                self.audio_stream.close()
            
            if hasattr(self, 'audio'):
                self.audio.terminate()
            
            print("🔇 音频录制已停止")
    
    def merge_audio_video(self):
        """合并音视频"""
        if not self.audio_frames or not self.output_file:
            return
        
        try:
            # 创建临时音频文件
            import wave
            
            self.temp_audio_file = os.path.join(self.temp_dir, "temp_audio.wav")
            
            # 保存音频到WAV文件
            wf = wave.open(self.temp_audio_file, 'wb')
            wf.setnchannels(self.audio_channels)
            wf.setsampwidth(self.audio.get_sample_size(self.audio_format))
            wf.setframerate(self.audio_rate)
            wf.writeframes(b''.join(self.audio_frames))
            wf.close()
            
            # 使用FFmpeg合并音视频
            temp_output = self.output_file.replace('.mp4', '_with_audio.mp4')
            
            ffmpeg_cmd = [
                'ffmpeg', '-y',  # -y 覆盖输出文件
                '-i', self.output_file,  # 输入视频文件
                '-i', self.temp_audio_file,  # 输入音频文件
                '-c:v', 'copy',  # 视频流直接复制
                '-c:a', 'aac',  # 音频编码为AAC
                '-strict', 'experimental',
                temp_output
            ]
            
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(temp_output):
                # 删除原始文件，重命名新文件
                os.remove(self.output_file)
                os.rename(temp_output, self.output_file)
                print("✅ 音视频合并完成")
            else:
                print(f"❌ 音视频合并失败: {result.stderr}")
            
            # 清理临时音频文件
            if os.path.exists(self.temp_audio_file):
                os.remove(self.temp_audio_file)
                
        except Exception as e:
            print(f"❌ 音视频合并错误: {e}")
    
    def record_screen(self):
        """录制屏幕主循环"""
        performance_config = PERFORMANCE_OPTIONS.get(self.performance_mode, PERFORMANCE_OPTIONS["medium"])
        frame_skip = performance_config["frame_skip"]
        sleep_factor = performance_config["sleep_factor"]
        
        while self.recording:
            if self.paused:
                time.sleep(0.1)
                continue
            
            try:
                current_time = time.time()
                elapsed = current_time - self.last_frame_time
                
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
                
                # 性能优化：控制帧率
                processing_time = time.time() - current_time
                sleep_time = max(0, self.target_frame_time - processing_time) * sleep_factor
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
        if hasattr(self, 'drawing_tool') and hasattr(self.drawing_tool, 'drawing_window'):
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

if __name__ == "__main__":
    main()