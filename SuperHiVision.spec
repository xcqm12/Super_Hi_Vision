# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# FFmpeg 随包分发：单文件 exe 解包到 _MEIPASS\ffmpeg\，程序启动时按
# <exe目录>\ffmpeg → _MEIPASS\ffmpeg 的顺序查找。
# 这样「绿色版」exe 单独拷到任何地方都能合成音频，不再出现「有画面无声音」。
# 只带 ffmpeg.exe + ffprobe.exe（合成/探测用得上），不带 ffplay（无人调用，省 ~150MB）。
# 注意：这里的输出一律用 ASCII。GitHub Windows runner 的控制台代码页是 cp1252，
# 打印中文会抛 UnicodeEncodeError 让 PyInstaller 直接秒退（日志里只有 banner，没有 traceback）。
_datas = [('icon.ico', '.')]
_missing = []
for _f in ('ffmpeg.exe', 'ffprobe.exe'):
    _p = os.path.join('ffmpeg', _f)
    if os.path.exists(_p):
        _datas.append((_p, 'ffmpeg'))
        print(f'[spec] bundle FFmpeg: {_p}')
    else:
        _missing.append(_p)
        print(f'[spec] WARNING: not found {_p} - built without bundled FFmpeg')
if _missing and os.environ.get('SHV_REQUIRE_FFMPEG') == '1':
    raise SystemExit('[spec] ERROR: bundled FFmpeg missing: %s' % _missing)

a = Analysis(
    ['Super_Hi_Vision_PyQt.py'],
    pathex=[],
    binaries=[],
    datas=_datas,
    hiddenimports=[
        'cv2', 'PIL', 'numpy', 'pyaudio', 'wave', 'struct', 'math',
        'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets',
        'pynput', 'pynput.keyboard', 'pynput.mouse',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# onefile 模式：全部依赖（Python 运行时 + 第三方库）打进单个 EXE，
# 不再生成 _internal 目录。分发/安装只需这一个文件，避免丢失运行时。
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SuperHiVision_v1.5.24',
    icon='icon.ico',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)