#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Super Hi Vision - Application Mode Launcher (.pyw)
双击运行，使用 pythonw.exe 无控制台启动。
优先级：
  1. 同目录已打包的 SuperHiVision_v1.5.14.exe -> 直接启动
  2. 否则以无控制台方式运行 Super_Hi_Vision_PyQt.py 源码
"""

import os
import sys
import subprocess

APP_DIR = os.path.dirname(os.path.abspath(__file__))
EXE_NAME = "SuperHiVision_v1.5.14.exe"
MAIN_SCRIPT = "Super_Hi_Vision_PyQt.py"


def hide_console():
    """隐藏当前进程的控制台窗口（若由 python.exe 启动）"""
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass


def main():
    hide_console()

    exe_path = os.path.join(APP_DIR, EXE_NAME)
    if os.path.exists(exe_path):
        # 优先启动已打包的 EXE（应用模式，无控制台）
        try:
            subprocess.Popen([exe_path], cwd=APP_DIR)
            return
        except Exception:
            pass

    script_path = os.path.join(APP_DIR, MAIN_SCRIPT)
    if os.path.exists(script_path):
        # 源码方式：直接用当前解释器（.pyw 双击即 pythonw，无控制台）
        subprocess.Popen([sys.executable, script_path], cwd=APP_DIR)
        return

    # 找不到任何入口，弹出 GUI 提示
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(
            0,
            "未找到 Super Hi Vision 主程序文件：\n\n"
            f"  {exe_path}\n"
            f"  {script_path}\n\n"
            "程序无法启动。",
            "Super Hi Vision",
            0x10,
        )
    except Exception:
        pass


if __name__ == "__main__":
    main()
