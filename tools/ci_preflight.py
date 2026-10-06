# -*- coding: utf-8 -*-
"""CI 预检：确认打包依赖都能导入。

PyInstaller 在 CI 里若因环境问题秒退且无 traceback，日志里几乎什么都看不到。
这个探针把每个依赖单独导入，失败时用 GitHub 的 ::error 工作流命令输出到 check-run 注解，
这样即使拿不到 job 日志（无 token），也能通过 annotations API 读到原因。
"""
import importlib
import importlib.metadata as md
import sys

MODS = ["PyInstaller", "PyQt5", "cv2", "numpy", "PIL", "pyaudio", "pynput"]
PKG = {"cv2": "opencv-python", "PIL": "pillow"}

failed = []
for name in MODS:
    try:
        importlib.import_module(name)
    except BaseException as e:  # noqa: BLE001 - 连 SystemExit/崩溃都要抓住
        failed.append(name)
        print(f"::error title=预检失败::{name} -> {type(e).__name__}: {e}")
        continue
    try:
        ver = md.version(PKG.get(name, name))
    except Exception:
        ver = "?"
    print(f"OK   {name:<14} {ver}")

print(f"python {sys.version.split()[0]} / {sys.executable}")
sys.exit(1 if failed else 0)
