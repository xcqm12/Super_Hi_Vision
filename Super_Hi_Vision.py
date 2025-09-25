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
from tkinter import ttk, messagebox, filedialog

# 版权信息
__author__ = "七零喵网络互娱科技有限公司"
__copyright__ = "Copyright 2019-2025, 七零喵网络互娱科技有限公司"
__version__ = "1.0.6"
__license__ = "MIT"
__email__ = "team@qlm.org.cn"
__website__ = "https://team.qlm.org.cn"
__team__ = "SevenZeroMeowTeam"

print("=" * 60)
print("🎬 高级超高清屏幕录制工具")
print(f"📝 版本: {__version__}")
print(f"👥 开发团队: {__team__}")
print(f"🏢 版权所有: {__copyright__}")
print(f"🌐 官方网站: {__website__}")
print("=" * 60)

# 自动安装依赖
def install_packages():
    required_packages = {
        'Pillow': 'PIL',
        'pynput': 'pynput',
        'psutil': 'psutil',
        'numpy': 'numpy'
    }
    
    for package, import_name in required_packages.items():
        try:
            if import_name == 'PIL':
                from PIL import ImageGrab, Image, ImageDraw, ImageFont, ImageTk
            else:
                __import__(import_name)
            print(f"✓ {package} 已安装")
        except ImportError:
            print(f"正在安装 {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✓ {package} 安装成功")
            except Exception as e:
                print(f"✗ {package} 安装失败: {e}")

# 安装必要包
install_packages()

# 现在导入所有需要的模块
try:
    from PIL import ImageGrab, Image, ImageDraw, ImageFont, ImageTk
    import psutil
    from pynput import keyboard
    from pynput.keyboard import Key, KeyCode
    import numpy as np
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请手动安装依赖: pip install Pillow pynput psutil numpy")
    sys.exit(1)

class DrawingTool:
    """画图工具类"""
    def __init__(self, master=None):
        self.master = master
        self.drawing = False
        self.last_x = 0
        self.last_y = 0
        self.pen_color = "red"
        self.pen_size = 3
        self.drawing_mode = "pen"  # pen, line, rectangle, ellipse, text, arrow
        self.text_to_draw = ""
        self.start_x = 0
        self.start_y = 0
        self.drawn_shapes = []  # 存储绘制的形状用于撤销
        self.canvas_image = None
        self.original_image = None
        self.current_shape = None
        
        # 创建画图窗口
        if master:
            self.create_drawing_window()
    
    def create_drawing_window(self):
        """创建画图窗口"""
        self.draw_window = tk.Toplevel(self.master)
        self.draw_window.title("🎨 画图工具 - 屏幕标注")
        self.draw_window.geometry("900x700")
        self.draw_window.configure(bg="#f0f0f0")
        self.draw_window.protocol("WM_DELETE_WINDOW", self.on_drawing_window_close)
        
        # 主框架
        main_frame = tk.Frame(self.draw_window, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 工具栏
        tool_frame = tk.Frame(main_frame, bg="#2c3e50", height=100)
        tool_frame.pack(fill=tk.X, pady=(0, 10))
        tool_frame.pack_propagate(False)
        
        # 工具按钮框架
        tool_buttons_frame = tk.Frame(tool_frame, bg="#2c3e50")
        tool_buttons_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)
        
        # 第一行工具按钮
        tools_row1 = [
            ("✏️ 画笔", "pen"),
            ("📏 直线", "line"),
            ("⬜ 矩形", "rectangle"),
            ("⭕ 椭圆", "ellipse"),
            ("🔺 三角形", "triangle")
        ]
        
        row1_frame = tk.Frame(tool_buttons_frame, bg="#2c3e50")
        row1_frame.pack(fill=tk.X, pady=2)
        
        for text, mode in tools_row1:
            btn = tk.Button(row1_frame, text=text, font=("Arial", 10),
                           command=lambda m=mode: self.set_drawing_mode(m),
                           bg="#3498db", fg="white", width=10, height=1,
                           relief="raised", bd=2)
            btn.pack(side=tk.LEFT, padx=3, pady=2)
        
        # 第二行工具按钮
        tools_row2 = [
            ("🔷 菱形", "diamond"),
            ("🔴 圆形", "circle"),
            ("➡️ 箭头", "arrow"),
            ("📝 文字", "text"),
            ("🧽 橡皮", "eraser")
        ]
        
        row2_frame = tk.Frame(tool_buttons_frame, bg="#2c3e50")
        row2_frame.pack(fill=tk.X, pady=2)
        
        for text, mode in tools_row2:
            btn = tk.Button(row2_frame, text=text, font=("Arial", 10),
                           command=lambda m=mode: self.set_drawing_mode(m),
                           bg="#3498db", fg="white", width=10, height=1,
                           relief="raised", bd=2)
            btn.pack(side=tk.LEFT, padx=3, pady=2)
        
        # 颜色选择框架
        color_frame = tk.Frame(tool_frame, bg="#2c3e50")
        color_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(color_frame, text="颜色:", font=("Arial", 10, "bold"), 
                bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        
        colors = [
            ("红色", "red"), ("蓝色", "blue"), ("绿色", "green"), 
            ("黄色", "yellow"), ("橙色", "orange"), ("紫色", "purple"), 
            ("黑色", "black"), ("白色", "white"), ("粉色", "pink"),
            ("青色", "cyan")
        ]
        
        for color_name, color_code in colors:
            color_btn = tk.Button(color_frame, text=color_name, font=("Arial", 8),
                                 command=lambda c=color_code: self.set_pen_color(c),
                                 bg=color_code, fg="black" if color_code in ["yellow", "white"] else "white",
                                 width=6, height=1, relief="solid", bd=1)
            color_btn.pack(side=tk.LEFT, padx=2)
        
        # 大小选择和功能按钮框架
        control_frame = tk.Frame(tool_frame, bg="#2c3e50")
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 大小选择
        size_label_frame = tk.Frame(control_frame, bg="#2c3e50")
        size_label_frame.pack(side=tk.LEFT)
        
        tk.Label(size_label_frame, text="大小:", font=("Arial", 10, "bold"), 
                bg="#2c3e50", fg="white").pack(side=tk.LEFT)
        
        sizes = [1, 2, 3, 5, 8, 12]
        for size in sizes:
            size_btn = tk.Button(size_label_frame, text=str(size), font=("Arial", 9),
                                command=lambda s=size: self.set_pen_size(s),
                                bg="#2980b9", fg="white", width=3, height=1,
                                relief="raised", bd=1)
            size_btn.pack(side=tk.LEFT, padx=1)
        
        # 功能按钮
        function_frame = tk.Frame(control_frame, bg="#2c3e50")
        function_frame.pack(side=tk.RIGHT)
        
        tk.Button(function_frame, text="↶ 撤销", font=("Arial", 10),
                 command=self.undo_last, bg="#e67e22", fg="white",
                 width=8, height=1).pack(side=tk.LEFT, padx=2)
        
        tk.Button(function_frame, text="🗑️ 清空", font=("Arial", 10),
                 command=self.clear_canvas, bg="#e74c3c", fg="white",
                 width=8, height=1).pack(side=tk.LEFT, padx=2)
        
        tk.Button(function_frame, text="💾 保存", font=("Arial", 10),
                 command=self.save_drawing, bg="#27ae60", fg="white",
                 width=8, height=1).pack(side=tk.LEFT, padx=2)
        
        tk.Button(function_frame, text="📷 截图", font=("Arial", 10),
                 command=self.take_screenshot, bg="#9b59b6", fg="white",
                 width=8, height=1).pack(side=tk.LEFT, padx=2)
        
        # 画布区域
        canvas_frame = tk.Frame(main_frame, bg="#ecf0f1")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建滚动条
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)
        
        # 创建画布
        self.canvas = tk.Canvas(canvas_frame, bg="white", cursor="crosshair",
                               yscrollcommand=v_scrollbar.set,
                               xscrollcommand=h_scrollbar.set,
                               scrollregion=(0, 0, 2000, 2000))
        
        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)
        
        # 布局
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # 绑定事件
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_draw)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)  # Windows
        self.canvas.bind("<Button-4>", self.on_mousewheel)    # Linux
        self.canvas.bind("<Button-5>", self.on_mousewheel)    # Linux
        
        # 状态栏
        status_frame = tk.Frame(main_frame, bg="#34495e", height=30)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        status_frame.pack_propagate(False)
        
        self.status_var = tk.StringVar(value="就绪 - 选择工具开始绘制")
        status_label = tk.Label(status_frame, textvariable=self.status_var,
                               font=("Arial", 10), bg="#34495e", fg="white")
        status_label.pack(expand=True)
        
        # 坐标显示
        self.coord_var = tk.StringVar(value="坐标: (0, 0)")
        coord_label = tk.Label(status_frame, textvariable=self.coord_var,
                              font=("Arial", 10), bg="#34495e", fg="white")
        coord_label.pack(side=tk.RIGHT, padx=10)
        
        # 绑定鼠标移动事件
        self.canvas.bind("<Motion>", self.show_coordinates)
        
        # 文字输入对话框
        self.text_window = None
        
        # 设置初始模式
        self.set_drawing_mode("pen")
        
        # 初始截图
        self.take_screenshot()
    
    def on_mousewheel(self, event):
        """鼠标滚轮缩放"""
        if event.delta > 0 or event.num == 4:
            self.canvas.scale("all", event.x, event.y, 1.1, 1.1)
        elif event.delta < 0 or event.num == 5:
            self.canvas.scale("all", event.x, event.y, 0.9, 0.9)
        
        # 更新滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def show_coordinates(self, event):
        """显示鼠标坐标"""
        x, y = event.x, event.y
        self.coord_var.set(f"坐标: ({x}, {y})")
    
    def set_drawing_mode(self, mode):
        """设置绘图模式"""
        self.drawing_mode = mode
        mode_names = {
            "pen": "画笔",
            "line": "直线",
            "rectangle": "矩形",
            "ellipse": "椭圆",
            "triangle": "三角形",
            "diamond": "菱形",
            "circle": "圆形",
            "arrow": "箭头",
            "text": "文字",
            "eraser": "橡皮"
        }
        self.status_var.set(f"模式: {mode_names.get(mode, mode)} - 在画布上拖动鼠标进行绘制")
    
    def set_pen_color(self, color):
        """设置画笔颜色"""
        self.pen_color = color
        self.status_var.set(f"颜色已设置为: {color}")
    
    def set_pen_size(self, size):
        """设置画笔大小"""
        self.pen_size = size
        self.status_var.set(f"画笔大小已设置为: {size}")
    
    def start_draw(self, event):
        """开始绘制"""
        self.drawing = True
        self.last_x = self.canvas.canvasx(event.x)
        self.last_y = self.canvas.canvasy(event.y)
        self.start_x = self.last_x
        self.start_y = self.last_y
        
        if self.drawing_mode == "text":
            self.open_text_input()
        elif self.drawing_mode in ["line", "rectangle", "ellipse", "circle", "triangle", "diamond", "arrow"]:
            # 对于这些模式，我们将在拖动时实时预览
            pass
    
    def draw(self, event):
        """绘制过程"""
        if not self.drawing:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # 删除之前的预览形状
        if self.current_shape:
            self.canvas.delete(self.current_shape)
        
        if self.drawing_mode == "pen":
            self.current_shape = self.canvas.create_line(self.last_x, self.last_y, x, y,
                                   fill=self.pen_color, width=self.pen_size,
                                   capstyle=tk.ROUND, smooth=True)
            self.last_x, self.last_y = x, y
            
        elif self.drawing_mode == "eraser":
            self.current_shape = self.canvas.create_line(self.last_x, self.last_y, x, y,
                                   fill="white", width=self.pen_size * 2,
                                   capstyle=tk.ROUND, smooth=True)
            self.last_x, self.last_y = x, y
            
        elif self.drawing_mode == "line":
            self.current_shape = self.canvas.create_line(self.start_x, self.start_y, x, y,
                                                  fill=self.pen_color, width=self.pen_size)
        
        elif self.drawing_mode == "rectangle":
            self.current_shape = self.canvas.create_rectangle(self.start_x, self.start_y, x, y,
                                                       outline=self.pen_color, width=self.pen_size)
        
        elif self.drawing_mode == "ellipse":
            self.current_shape = self.canvas.create_oval(self.start_x, self.start_y, x, y,
                                                  outline=self.pen_color, width=self.pen_size)
        
        elif self.drawing_mode == "circle":
            radius = ((x - self.start_x)**2 + (y - self.start_y)**2)**0.5
            self.current_shape = self.canvas.create_oval(self.start_x - radius, self.start_y - radius,
                                                  self.start_x + radius, self.start_y + radius,
                                                  outline=self.pen_color, width=self.pen_size)
        
        elif self.drawing_mode == "triangle":
            self.current_shape = self.canvas.create_polygon(
                self.start_x, self.start_y,
                x, y,
                self.start_x - (x - self.start_x), y,
                outline=self.pen_color, fill="", width=self.pen_size
            )
        
        elif self.drawing_mode == "diamond":
            center_x = (self.start_x + x) / 2
            center_y = (self.start_y + y) / 2
            width = abs(x - self.start_x)
            height = abs(y - self.start_y)
            
            points = [
                center_x, self.start_y,
                x, center_y,
                center_x, y,
                self.start_x, center_y
            ]
            self.current_shape = self.canvas.create_polygon(points, outline=self.pen_color, fill="", width=self.pen_size)
        
        elif self.drawing_mode == "arrow":
            # 绘制箭头
            self.current_shape = self.draw_arrow(self.start_x, self.start_y, x, y)
    
    def draw_arrow(self, x1, y1, x2, y2):
        """绘制箭头"""
        # 绘制主线
        line = self.canvas.create_line(x1, y1, x2, y2, fill=self.pen_color, width=self.pen_size)
        
        # 计算箭头角度
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_length = 20  # 箭头长度
        
        # 计算箭头点
        x3 = x2 - arrow_length * math.cos(angle - math.pi/6)
        y3 = y2 - arrow_length * math.sin(angle - math.pi/6)
        x4 = x2 - arrow_length * math.cos(angle + math.pi/6)
        y4 = y2 - arrow_length * math.sin(angle + math.pi/6)
        
        # 绘制箭头
        arrow_head = self.canvas.create_polygon(x2, y2, x3, y3, x4, y4, 
                                               fill=self.pen_color, outline=self.pen_color)
        
        return (line, arrow_head)
    
    def stop_draw(self, event):
        """结束绘制"""
        if not self.drawing:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # 保存当前形状用于撤销
        if self.current_shape and self.drawing_mode not in ["pen", "eraser"]:
            if self.drawing_mode == "arrow":
                # 箭头由多个部分组成
                for shape in self.current_shape:
                    self.drawn_shapes.append(shape)
            else:
                self.drawn_shapes.append(self.current_shape)
        
        self.drawing = False
        self.current_shape = None
    
    def open_text_input(self):
        """打开文字输入对话框"""
        if self.text_window and self.text_window.winfo_exists():
            self.text_window.lift()
            return
            
        self.text_window = tk.Toplevel(self.draw_window)
        self.text_window.title("输入文字")
        self.text_window.geometry("300x150")
        self.text_window.resizable(False, False)
        self.text_window.transient(self.draw_window)
        self.text_window.grab_set()
        
        tk.Label(self.text_window, text="请输入要绘制的文字:", 
                font=("Arial", 11)).pack(pady=10)
        
        text_entry = tk.Entry(self.text_window, font=("Arial", 12), width=30)
        text_entry.pack(pady=5, padx=20, fill=tk.X)
        text_entry.focus()
        
        def confirm_text():
            self.text_to_draw = text_entry.get()
            if self.text_to_draw:
                # 在画布中央添加文字
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                text_id = self.canvas.create_text(canvas_width//2, canvas_height//2,
                                                text=self.text_to_draw, fill=self.pen_color,
                                                font=("Arial", 16, "bold"))
                self.drawn_shapes.append(text_id)
                
            self.text_window.destroy()
            self.text_window = None
        
        btn_frame = tk.Frame(self.text_window)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="确定", command=confirm_text,
                 bg="#27ae60", fg="white", width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="取消", command=lambda: self.text_window.destroy(),
                 bg="#e74c3c", fg="white", width=10).pack(side=tk.LEFT, padx=10)
    
    def take_screenshot(self):
        """截取当前屏幕"""
        try:
            # 截取屏幕
            screenshot = ImageGrab.grab()
            
            # 调整大小以适应画布
            canvas_width = 1800
            canvas_height = 1000
            screenshot.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            
            # 清空画布
            self.canvas.delete("all")
            self.drawn_shapes.clear()
            
            # 显示截图
            self.original_image = screenshot
            self.canvas_image = ImageTk.PhotoImage(screenshot)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.canvas_image)
            
            # 设置滚动区域
            self.canvas.configure(scrollregion=(0, 0, screenshot.width, screenshot.height))
            
            self.status_var.set("截图已加载到画布")
            
        except Exception as e:
            messagebox.showerror("错误", f"截图失败: {e}")
    
    def undo_last(self):
        """撤销上一步操作"""
        if self.drawn_shapes:
            last_shape = self.drawn_shapes.pop()
            if isinstance(last_shape, tuple):  # 处理由多个部分组成的形状（如箭头）
                for shape in last_shape:
                    self.canvas.delete(shape)
            else:
                self.canvas.delete(last_shape)
            self.status_var.set("已撤销上一步操作")
        else:
            self.status_var.set("没有可撤销的操作")
    
    def clear_canvas(self):
        """清空画布"""
        if messagebox.askyesno("确认", "确定要清空画布吗？"):
            self.canvas.delete("all")
            self.drawn_shapes.clear()
            # 重新加载截图
            if self.original_image:
                self.canvas_image = ImageTk.PhotoImage(self.original_image)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.canvas_image)
            self.status_var.set("画布已清空")
    
    def save_drawing(self):
        """保存绘图"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG图片", "*.png"), ("JPEG图片", "*.jpg"), ("所有文件", "*.*")],
            title="保存绘图"
        )
        
        if file_path:
            try:
                # 获取画布内容
                self.canvas.postscript(file=file_path + ".eps", colormode='color')
                
                # 使用PIL转换EPS到PNG
                img = Image.open(file_path + ".eps")
                img.save(file_path, quality=95)
                
                # 删除临时EPS文件
                os.remove(file_path + ".eps")
                
                self.status_var.set(f"绘图已保存: {file_path}")
                messagebox.showinfo("成功", f"绘图已保存到:\n{file_path}")
                
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {e}")
    
    def on_drawing_window_close(self):
        """画图窗口关闭事件"""
        if messagebox.askokcancel("退出", "确定要关闭画图工具吗？"):
            self.draw_window.destroy()

class AdvancedScreenRecorderGUI:
    """GUI界面类"""
    def __init__(self, recorder):
        self.recorder = recorder
        self.root = tk.Tk()
        self.root.title(f"高级屏幕录制工具 v{__version__} - {__team__}")
        self.root.geometry("800x700")  # 增加高度以容纳画图工具按钮
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(True, True)
        
        # 设置图标
        try:
            self.root.iconbitmap(default="icon.ico")
        except:
            pass
        
        # 画图工具实例
        self.drawing_tool = None
        
        self.setup_gui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_gui(self):
        """设置GUI界面"""
        # 标题栏
        title_frame = tk.Frame(self.root, bg="#2c3e50", height=100)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="🎬 高级屏幕录制工具", 
                              font=("Arial", 24, "bold"), fg="white", bg="#2c3e50")
        title_label.pack(expand=True, pady=5)
        
        version_label = tk.Label(title_frame, text=f"版本 {__version__} • {__team__}", 
                                font=("Arial", 12), fg="#ecf0f1", bg="#2c3e50")
        version_label.pack()
        
        # 主内容区域
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧设置区域
        left_frame = tk.Frame(main_frame, bg="#f0f0f0")
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        
        # 右侧状态区域
        right_frame = tk.Frame(main_frame, bg="#f0f0f0")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 录制设置区域
        settings_frame = tk.LabelFrame(left_frame, text="📁 录制设置", font=("Arial", 12, "bold"),
                                      bg="#f0f0f0", padx=15, pady=15, width=300)
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 质量选择
        quality_label = tk.Label(settings_frame, text="视频质量:", font=("Arial", 10, "bold"), 
                                bg="#f0f0f0", anchor="w")
        quality_label.pack(fill=tk.X, pady=2)
        
        self.quality_var = tk.StringVar(value="hd")
        quality_options = [
            ("蓝光 (Ultra HD) 4K", "uhd"),
            ("全高清 (FHD) 1080P", "fhd"),
            ("高清 (HD) 720P", "hd"),
            ("流畅 (Smooth) 480P", "smooth"),
            ("标清 (SD) 480P", "sd")
        ]
        
        for text, mode in quality_options:
            tk.Radiobutton(settings_frame, text=text, variable=self.quality_var, 
                          value=mode, bg="#f0f0f0", font=("Arial", 9),
                          command=self.on_quality_change).pack(anchor="w", pady=1)
        
        # 录制选项
        options_frame = tk.Frame(settings_frame, bg="#f0f0f0")
        options_frame.pack(fill=tk.X, pady=10)
        
        self.audio_var = tk.BooleanVar(value=True)
        audio_cb = tk.Checkbutton(options_frame, text="录制系统音频", variable=self.audio_var,
                                 font=("Arial", 10), bg="#f0f0f0", 
                                 command=self.on_audio_change)
        audio_cb.pack(anchor="w", pady=2)
        
        self.timestamp_var = tk.BooleanVar(value=True)
        timestamp_cb = tk.Checkbutton(options_frame, text="显示录制时间戳", variable=self.timestamp_var,
                                     font=("Arial", 10), bg="#f0f0f0",
                                     command=self.on_timestamp_change)
        timestamp_cb.pack(anchor="w", pady=2)
        
        # 输出路径设置
        path_frame = tk.Frame(settings_frame, bg="#f0f0f0")
        path_frame.pack(fill=tk.X, pady=10)
        
        path_label = tk.Label(path_frame, text="保存路径:", font=("Arial", 10, "bold"), 
                             bg="#f0f0f0", anchor="w")
        path_label.pack(fill=tk.X)
        
        path_btn_frame = tk.Frame(path_frame, bg="#f0f0f0")
        path_btn_frame.pack(fill=tk.X, pady=5)
        
        self.path_var = tk.StringVar(value=os.path.expanduser("~/Videos"))
        path_entry = tk.Entry(path_btn_frame, textvariable=self.path_var, font=("Arial", 9))
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        browse_btn = tk.Button(path_btn_frame, text="浏览", font=("Arial", 8),
                              command=self.browse_path, bg="#3498db", fg="white")
        browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # 画图工具区域
        drawing_frame = tk.LabelFrame(left_frame, text="🎨 画图工具", font=("Arial", 12, "bold"),
                                     bg="#f0f0f0", padx=15, pady=15, width=300)
        drawing_frame.pack(fill=tk.X, pady=5)
        
        drawing_btn = tk.Button(drawing_frame, text="打开画图工具", font=("Arial", 12, "bold"),
                               command=self.open_drawing_tool, bg="#9b59b6", fg="white",
                               width=20, height=2)
        drawing_btn.pack(pady=10)
        
        drawing_desc = tk.Label(drawing_frame, text="用于屏幕标注、教学演示等场景\n支持多种绘图工具和实时截图", 
                               font=("Arial", 9), bg="#f0f0f0", fg="#7f8c8d", justify=tk.LEFT)
        drawing_desc.pack()
        
        # 状态显示区域
        status_frame = tk.LabelFrame(right_frame, text="📊 录制状态", font=("Arial", 12, "bold"),
                                    bg="#f0f0f0", padx=15, pady=15)
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 状态指示器
        self.status_var = tk.StringVar(value="等待开始录制")
        status_indicator = tk.Label(status_frame, textvariable=self.status_var,
                                   font=("Arial", 16, "bold"), fg="#2c3e50", bg="#f0f0f0")
        status_indicator.pack(pady=10)
        
        # 统计信息
        stats_frame = tk.Frame(status_frame, bg="#f0f0f0")
        stats_frame.pack(fill=tk.X, pady=10)
        
        self.duration_var = tk.StringVar(value="时长: 00:00:00")
        self.frames_var = tk.StringVar(value="帧数: 0")
        self.fps_var = tk.StringVar(value="实时帧率: 0.0 FPS")
        self.file_size_var = tk.StringVar(value="文件大小: 0 MB")
        
        info_labels = [
            self.duration_var,
            self.frames_var,
            self.fps_var,
            self.file_size_var
        ]
        
        for label_var in info_labels:
            label = tk.Label(stats_frame, textvariable=label_var, font=("Arial", 11),
                            bg="#f0f0f0", anchor="w")
            label.pack(fill=tk.X, pady=3)
        
        # 预览区域
        preview_frame = tk.LabelFrame(status_frame, text="🎬 实时预览", font=("Arial", 12, "bold"),
                                     bg="#f0f0f0", padx=15, pady=15)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.preview_text = tk.Text(preview_frame, height=8, font=("Arial", 9),
                                   bg="#2c3e50", fg="#ecf0f1", wrap=tk.WORD)
        self.preview_text.pack(fill=tk.BOTH, expand=True)
        
        # 控制按钮区域
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        btn_frame = tk.Frame(control_frame, bg="#f0f0f0")
        btn_frame.pack(expand=True)
        
        self.start_btn = tk.Button(btn_frame, text="🎬 开始录制", 
                                  font=("Arial", 14, "bold"), bg="#27ae60", fg="white",
                                  width=12, height=2, command=self.start_recording)
        self.start_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="⏹️ 停止录制", 
                                 font=("Arial", 14, "bold"), bg="#e74c3c", fg="white",
                                 width=12, height=2, command=self.stop_recording,
                                 state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        self.pause_btn = tk.Button(btn_frame, text="⏸️ 暂停", 
                                  font=("Arial", 14), bg="#f39c12", fg="white",
                                  width=10, height=2, command=self.toggle_pause,
                                  state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=10)
        
        # 画图工具按钮
        self.drawing_btn = tk.Button(btn_frame, text="🎨 画图工具", 
                                    font=("Arial", 14), bg="#9b59b6", fg="white",
                                    width=12, height=2, command=self.open_drawing_tool)
        self.drawing_btn.pack(side=tk.LEFT, padx=10)
        
        # 进度条
        self.progress = ttk.Progressbar(control_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=10)
        
        # 版权信息
        copyright_frame = tk.Frame(self.root, bg="#f0f0f0")
        copyright_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        copyright_text = f"© 2019-2025 {__author__} | {__website__}"
        copyright_label = tk.Label(copyright_frame, text=copyright_text, 
                                  font=("Arial", 9), fg="#7f8c8d", bg="#f0f0f0")
        copyright_label.pack()
        
        # 初始化预览文本
        self.update_preview("程序已就绪，等待开始录制...\n")
        self.update_preview(f"当前质量: {self.get_quality_display_name()}\n")
        self.update_preview("快捷键: Ctrl+Alt+S(开始) Ctrl+Alt+E(停止) Ctrl+Alt+Q(切换质量)\n")
        self.update_preview("画图工具: 可用于屏幕标注、教学演示等场景\n")
    
    def open_drawing_tool(self):
        """打开画图工具"""
        if self.drawing_tool is None or not self.drawing_tool.draw_window.winfo_exists():
            self.drawing_tool = DrawingTool(self.root)
            self.update_preview("画图工具已打开\n")
        else:
            self.drawing_tool.draw_window.lift()
            self.drawing_tool.draw_window.focus_force()
    
    def get_quality_display_name(self):
        """获取质量模式的显示名称"""
        quality_names = {
            'uhd': '蓝光 (Ultra HD 4K)',
            'fhd': '全高清 (FHD 1080P)',
            'hd': '高清 (HD 720P)',
            'smooth': '流畅 (Smooth) 480P',
            'sd': '标清 (SD) 480P'
        }
        return quality_names.get(self.quality_var.get(), '高清')
    
    def update_preview(self, text):
        """更新预览文本"""
        self.preview_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {text}")
        self.preview_text.see(tk.END)
        self.root.update_idletasks()
    
    def on_quality_change(self):
        """质量设置改变"""
        quality = self.quality_var.get()
        self.recorder.current_quality = quality
        self.update_preview(f"质量模式已切换: {self.get_quality_display_name()}\n")
    
    def on_audio_change(self):
        """音频设置改变"""
        self.recorder.record_audio = self.audio_var.get()
        status = "启用" if self.recorder.record_audio else "禁用"
        self.update_preview(f"音频录制: {status}\n")
    
    def on_timestamp_change(self):
        """时间戳设置改变"""
        self.recorder.show_time_during_recording = self.timestamp_var.get()
        status = "显示" if self.recorder.show_time_during_recording else "隐藏"
        self.update_preview(f"时间戳: {status}\n")
    
    def browse_path(self):
        """浏览保存路径"""
        path = filedialog.askdirectory(initialdir=self.path_var.get())
        if path:
            self.path_var.set(path)
            self.recorder.output_directory = path
            self.update_preview(f"保存路径已更新: {path}\n")
    
    def gui_callback(self, event_type, data):
        """GUI回调函数"""
        if not self.root:
            return
            
        def update_gui():
            try:
                if event_type == 'recording_started':
                    self.status_var.set("录制中...")
                    self.start_btn.config(state=tk.DISABLED)
                    self.stop_btn.config(state=tk.NORMAL)
                    self.pause_btn.config(state=tk.NORMAL)
                    self.progress.start()
                    self.update_preview("录制已开始...\n")
                    
                elif event_type == 'recording_stopped':
                    self.status_var.set("录制已停止")
                    self.start_btn.config(state=tk.NORMAL)
                    self.stop_btn.config(state=tk.DISABLED)
                    self.pause_btn.config(state=tk.DISABLED)
                    self.progress.stop()
                    
                    if data:
                        duration = data.get('duration', 0)
                        frame_count = data.get('frame_count', 0)
                        avg_fps = data.get('avg_fps', 0)
                        file_path = data.get('file_path', '')
                        
                        self.duration_var.set(f"时长: {self.format_duration(duration)}")
                        self.frames_var.set(f"帧数: {frame_count}")
                        self.fps_var.set(f"平均帧率: {avg_fps:.1f} FPS")
                        
                        if file_path and os.path.exists(file_path):
                            file_size = os.path.getsize(file_path) / (1024 * 1024)
                            self.file_size_var.set(f"文件大小: {file_size:.1f} MB")
                            self.update_preview(f"视频已保存: {file_path}\n")
                            self.update_preview(f"文件大小: {file_size:.1f} MB\n")
                    
                elif event_type == 'recording_progress':
                    duration = data.get('duration', 0)
                    frame_count = data.get('frame_count', 0)
                    actual_fps = data.get('actual_fps', 0)
                    
                    self.duration_var.set(f"时长: {self.format_duration(duration)}")
                    self.frames_var.set(f"帧数: {frame_count}")
                    self.fps_var.set(f"实时帧率: {actual_fps:.1f} FPS")
                    
                elif event_type == 'recording_paused':
                    is_paused = data.get('paused', False)
                    if is_paused:
                        self.status_var.set("已暂停")
                        self.pause_btn.config(text="▶️ 继续")
                        self.update_preview("录制已暂停\n")
                    else:
                        self.status_var.set("录制中...")
                        self.pause_btn.config(text="⏸️ 暂停")
                        self.update_preview("录制已继续\n")
                        
                elif event_type == 'error':
                    error_msg = data.get('message', '未知错误')
                    self.update_preview(f"错误: {error_msg}\n")
                    messagebox.showerror("错误", error_msg)
                    
            except Exception as e:
                print(f"GUI更新错误: {e}")
        
        self.root.after(0, update_gui)
    
    def format_duration(self, seconds):
        """格式化时长显示"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def start_recording(self):
        """开始录制"""
        self.recorder.output_directory = self.path_var.get()
        threading.Thread(target=self.recorder.start_recording, daemon=True).start()
    
    def stop_recording(self):
        """停止录制"""
        threading.Thread(target=self.recorder.stop_recording, daemon=True).start()
    
    def toggle_pause(self):
        """暂停/继续录制"""
        self.recorder.toggle_pause()
    
    def on_closing(self):
        """关闭窗口事件"""
        if messagebox.askokcancel("退出", "确定要退出程序吗？"):
            # 关闭画图工具窗口
            if self.drawing_tool and self.drawing_tool.draw_window.winfo_exists():
                self.drawing_tool.draw_window.destroy()
            
            if self.recorder.recording:
                self.recorder.stop_recording()
                time.sleep(1)
            self.root.destroy()
            sys.exit(0)
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

# AdvancedScreenRecorder 类保持不变（与原始代码相同）
class AdvancedScreenRecorder:
    def __init__(self, gui_callback=None):
        print(f"🎯 初始化高级屏幕录制器 - {__team__}")
        
        self.recording = False
        self.paused = False
        self.frame_count = 0
        self.temp_dir = None
        self.start_time = None
        self.screen_size = self.get_screen_size()
        self.recording_thread = None
        self.ffmpeg_path = self.install_or_find_ffmpeg()
        self.listener = None
        self.gui_callback = gui_callback
        self.output_directory = os.path.expanduser("~/Videos")
        
        # 录制质量配置
        self.quality_modes = {
            'uhd': {'scale': 1.0, 'fps': 60, 'crf': 18, 'preset': 'medium', 'bitrate': '256k'},
            'fhd': {'scale': 1.0, 'fps': 30, 'crf': 25, 'preset': 'fast', 'bitrate': '128k'},
            'hd': {'scale': 0.75, 'fps': 25, 'crf': 27, 'preset': 'fast', 'bitrate': '96k'},
            'smooth': {'scale': 0.5, 'fps': 15, 'crf': 30, 'preset': 'ultrafast', 'bitrate': '64k'},
            'sd': {'scale': 0.5, 'fps': 15, 'crf': 32, 'preset': 'veryfast', 'bitrate': '32k'}
        }
        
        self.current_quality = 'hd'
        self.record_audio = True
        self.show_time_during_recording = True
        
        # 性能监控
        self.last_capture_time = 0
        self.actual_fps = 0
        self.target_fps = 0
        self.frame_time_accumulator = 0
        self.frame_count_accumulator = 0
        
        # 键盘监听
        self.pressed_keys = set()
        self.setup_hotkeys()
        
        print(f"📺 屏幕尺寸: {self.screen_size[0]}x{self.screen_size[1]}")
        print(f"🎚️ 质量模式: {self.current_quality.upper()}")
        print("✅ 初始化完成")
    
    def get_screen_size(self):
        """获取屏幕尺寸"""
        try:
            screen = ImageGrab.grab()
            return screen.size
        except:
            return (1920, 1080)
    
    def setup_hotkeys(self):
        """设置快捷键"""
        self.hotkeys = {
            'start_recording': {'ctrl', 'alt', 's'},
            'stop_recording': {'ctrl', 'alt', 'e'},
            'toggle_quality': {'ctrl', 'alt', 'q'}
        }
    
    def install_or_find_ffmpeg(self):
        """安装或查找FFmpeg"""
        # 检查系统PATH
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            print(f"✅ 找到FFmpeg: {ffmpeg_path}")
            return ffmpeg_path
        
        # 尝试自动安装FFmpeg
        if platform.system() == "Windows":
            url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"
            zip_path = os.path.join(tempfile.gettempdir(), "ffmpeg-master-latest-win64-gpl-shared.zip")
            extract_dir = os.path.join(tempfile.gettempdir(), "ffmpeg")
            
            try:
                import requests
                print("🔍 下载FFmpeg...")
                response = requests.get(url)
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                print("📦 解压FFmpeg...")
                import zipfile
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                ffmpeg_path = os.path.join(extract_dir, "bin", "ffmpeg.exe")
                print(f"✅ FFmpeg已安装: {ffmpeg_path}")
                return ffmpeg_path
            except Exception as e:
                print(f"❌ FFmpeg安装失败: {e}")
        
        print("❌ 未找到FFmpeg，请手动安装FFmpeg并添加到PATH")
        return "ffmpeg"
    
    def toggle_quality_mode(self):
        """切换质量模式"""
        modes = list(self.quality_modes.keys())
        current_index = modes.index(self.current_quality)
        next_index = (current_index + 1) % len(modes)
        self.current_quality = modes[next_index]
        
        mode = self.quality_modes[self.current_quality]
        print(f"🔄 切换到 {self.current_quality.upper()} 模式")
        print(f"  分辨率: {int(self.screen_size[0] * mode['scale'])}x{int(self.screen_size[1] * mode['scale'])}")
        print(f"  帧率: {mode['fps']} FPS")
        
        return self.current_quality
    
    def toggle_pause(self):
        """暂停/继续录制"""
        self.paused = not self.paused
        if self.gui_callback:
            self.gui_callback('recording_paused', {'paused': self.paused})
    
    def on_press(self, key):
        """按键按下事件"""
        try:
            key_str = str(key).replace('Key.', '').replace('\'', '')
            self.pressed_keys.add(key_str.lower())
            
            # 检查快捷键
            if self.hotkeys['start_recording'].issubset(self.pressed_keys):
                if not self.recording:
                    print("🎬 开始录制快捷键触发")
                    threading.Thread(target=self.start_recording, daemon=True).start()
            
            elif self.hotkeys['stop_recording'].issubset(self.pressed_keys):
                if self.recording:
                    print("⏹️ 停止录制快捷键触发")
                    threading.Thread(target=self.stop_recording, daemon=True).start()
            
            elif self.hotkeys['toggle_quality'].issubset(self.pressed_keys):
                print("🔄 切换质量快捷键触发")
                self.toggle_quality_mode()
                
        except Exception as e:
            print(f"快捷键错误: {e}")
        
        return True
    
    def on_release(self, key):
        """按键释放事件"""
        try:
            key_str = str(key).replace('Key.', '').replace('\'', '')
            if key_str.lower() in self.pressed_keys:
                self.pressed_keys.remove(key_str.lower())
        except:
            pass
        return True
    
    def start_recording(self):
        """开始录制"""
        if self.recording:
            return
        
        print("🎬 开始录制...")
        self.recording = True
        self.paused = False
        self.frame_count = 0
        self.start_time = time.time()
        
        # 创建临时目录
        self.temp_dir = tempfile.mkdtemp(prefix="screen_rec_")
        print(f"📁 临时目录: {self.temp_dir}")
        
        # 设置目标帧率
        mode = self.quality_modes[self.current_quality]
        self.target_fps = mode['fps']
        
        # 启动录制线程
        self.recording_thread = threading.Thread(target=self._recording_loop, daemon=True)
        self.recording_thread.start()
        
        # 通知GUI
        if self.gui_callback:
            self.gui_callback('recording_started', None)
        
        print("✅ 录制已开始")
    
    def _recording_loop(self):
        """录制循环"""
        last_fps_update = time.time()
        fps_update_interval = 1.0
        
        while self.recording:
            try:
                if self.paused:
                    time.sleep(0.1)
                    continue
                
                current_time = time.time()
                elapsed_time = current_time - self.start_time
                
                # 捕获屏幕
                frame = self._capture_frame(elapsed_time)
                if frame:
                    # 保存帧
                    frame_filename = os.path.join(self.temp_dir, f"frame_{self.frame_count:08d}.png")
                    frame.save(frame_filename, 'PNG', optimize=True)
                    self.frame_count += 1
                
                # 更新帧率统计
                frame_time = time.time() - current_time
                self.frame_time_accumulator += frame_time
                self.frame_count_accumulator += 1
                
                # 定期更新GUI
                if current_time - last_fps_update >= fps_update_interval:
                    if self.frame_count_accumulator > 0:
                        self.actual_fps = self.frame_count_accumulator / self.frame_time_accumulator
                        
                        if self.gui_callback:
                            progress_data = {
                                'duration': elapsed_time,
                                'frame_count': self.frame_count,
                                'actual_fps': self.actual_fps
                            }
                            self.gui_callback('recording_progress', progress_data)
                        
                        self.frame_time_accumulator = 0
                        self.frame_count_accumulator = 0
                        last_fps_update = current_time
                
                # 控制帧率
                time.sleep(1.0 / self.target_fps)
                
            except Exception as e:
                print(f"录制错误: {e}")
                time.sleep(0.1)
    
    def _capture_frame(self, elapsed_time):
        """捕获一帧屏幕"""
        try:
            screenshot = ImageGrab.grab()
            
            # 调整尺寸
            mode = self.quality_modes[self.current_quality]
            if mode['scale'] != 1.0:
                new_size = (
                    int(screenshot.width * mode['scale']),
                    int(screenshot.height * mode['scale'])
                )
                screenshot = screenshot.resize(new_size, Image.Resampling.LANCZOS)
            
            # 添加时间戳
            if self.show_time_during_recording:
                screenshot = self._add_timestamp_to_image(screenshot, elapsed_time)
            
            return screenshot
            
        except Exception as e:
            print(f"捕获帧失败: {e}")
            return None
    
    def _add_timestamp_to_image(self, image, elapsed_time):
        """添加时间戳"""
        try:
            draw = ImageDraw.Draw(image)
            
            # 字体设置
            try:
                font_size = max(20, int(image.height * 0.02))
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            # 时间文本
            hours = int(elapsed_time // 3600)
            minutes = int((elapsed_time % 3600) // 60)
            seconds = int(elapsed_time % 60)
            time_text = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # 绘制背景
            padding = 10
            text_bbox = draw.textbbox((0, 0), time_text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            draw.rectangle([
                10 - padding, 10 - padding,
                10 + text_width + padding, 10 + text_height + padding
            ], fill=(0, 0, 0, 180))
            
            # 绘制文本
            draw.text((10, 10), time_text, fill=(255, 255, 255), font=font)
            
            return image
        except Exception as e:
            print(f"添加时间戳错误: {e}")
            return image
    
    def stop_recording(self):
        """停止录制"""
        if not self.recording:
            return
        
        print("⏹️ 停止录制...")
        self.recording = False
        self.paused = False
        
        # 等待录制线程结束
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=5.0)
        
        # 计算录制时长
        end_time = time.time()
        duration = end_time - self.start_time
        
        print(f"📊 录制统计:")
        print(f"  时长: {duration:.2f}秒")
        print(f"  帧数: {self.frame_count}")
        print(f"  帧率: {self.frame_count / duration:.2f} FPS")
        
        # 编码视频
        if self.frame_count > 0:
            print("🎞️ 编码视频...")
            try:
                video_file = self._encode_video(duration)
                
                if self.gui_callback:
                    result_data = {
                        'duration': duration,
                        'frame_count': self.frame_count,
                        'avg_fps': self.frame_count / duration,
                        'file_path': video_file
                    }
                    self.gui_callback('recording_stopped', result_data)
                
            except Exception as e:
                print(f"❌ 视频编码失败: {e}")
                if self.gui_callback:
                    self.gui_callback('error', {'message': f'视频编码失败: {e}'})
        else:
            print("❌ 没有可用的帧数据")
            if self.gui_callback:
                self.gui_callback('recording_stopped', None)
        
        # 清理临时文件
        self._cleanup_temp_files()
        
        print("✅ 录制完成")
    
    def _encode_video(self, duration):
        """编码视频"""
        try:
            # 生成输出文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(
                self.output_directory,
                f"screen_record_{self.current_quality}_{timestamp}.mp4"
            )
            
            mode = self.quality_modes[self.current_quality]
            target_width = int(self.screen_size[0] * mode['scale'])
            target_height = int(self.screen_size[1] * mode['scale'])
            
            # FFmpeg命令
            ffmpeg_cmd = [
                self.ffmpeg_path,
                '-y',
                '-f', 'image2',
                '-r', str(mode['fps']),
                '-i', os.path.join(self.temp_dir, 'frame_%08d.png'),
                '-c:v', 'libx264',
                '-crf', str(mode['crf']),
                '-preset', mode['preset'],
                '-pix_fmt', 'yuv420p',
                '-r', str(mode['fps']),
                output_file
            ]
            
            print(f"🔧 运行FFmpeg...")
            result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                file_size = os.path.getsize(output_file) / (1024 * 1024)
                print(f"✅ 视频编码完成: {output_file} ({file_size:.1f} MB)")
                return output_file
            else:
                raise Exception(f"FFmpeg错误: {result.stderr}")
                
        except Exception as e:
            print(f"❌ 编码错误: {e}")
            raise
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                print("🗑️ 临时文件已清理")
        except Exception as e:
            print(f"清理临时文件失败: {e}")
    
    def start_keyboard_listener(self):
        """启动键盘监听"""
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
        self.listener.daemon = True
        self.listener.start()
    
    def run(self):
        """运行录制器"""
        self.start_keyboard_listener()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            if self.recording:
                self.stop_recording()
            if self.listener:
                self.listener.stop()

def main():
    """主函数"""
    try:
        print("🖥️ 启动GUI模式...")
        recorder = AdvancedScreenRecorder()
        gui = AdvancedScreenRecorderGUI(recorder)
        recorder.gui_callback = gui.gui_callback
        recorder.start_keyboard_listener()
        gui.run()
        
    except Exception as e:
        print(f"❌ 程序错误: {e}")
        import traceback
        traceback.print_exc()
        input("按Enter键退出...")

if __name__ == "__main__":
    main()