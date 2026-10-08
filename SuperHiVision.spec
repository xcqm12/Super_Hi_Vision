# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# ---- Version resource: what Windows shows in the exe Properties -------------
# Without this the "Company" field is empty and the UAC prompt shows no
# publisher name at all. The version is read from the main script, so it never
# has to be maintained in two places. ASCII only: the CI console is cp1252 and
# printing non-ASCII from a spec makes PyInstaller abort (see the note below).
# Self-contained imports on purpose (the spec imports os/sys above as well).
import os as _os
import re as _re
import tempfile as _tempfile


def _read_app_version():
    try:
        with open('Super_Hi_Vision_PyQt.py', encoding='utf-8') as _f:
            _m = _re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', _f.read(), _re.M)
            if _m:
                return _m.group(1)
    except Exception:
        pass
    return '0.0.0'


APP_NAME = 'Super Hi Vision'
APP_PUBLISHER = 'SevenZeroMeowTeam'      # publisher name shown by Windows
APP_VERSION = _read_app_version()
_vnum = [int(x) for x in (_re.findall(r'\d+', APP_VERSION) + ['0', '0', '0', '0'])[:4]]

VERSION_FILE = None
try:
    _vi = (
        'VSVersionInfo(\n'
        '  ffi=FixedFileInfo(\n'
        '    filevers=(%d, %d, %d, %d),\n'
        '    prodvers=(%d, %d, %d, %d),\n'
        '    mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)\n'
        '  ),\n'
        '  kids=[\n'
        '    StringFileInfo([\n'
        "      StringTable(u'080404B0', [\n"
        "        StringStruct(u'CompanyName', u'%s'),\n"
        "        StringStruct(u'FileDescription', u'%s - Advanced HD Screen Recorder'),\n"
        "        StringStruct(u'FileVersion', u'%s'),\n"
        "        StringStruct(u'InternalName', u'SuperHiVision'),\n"
        "        StringStruct(u'LegalCopyright', u'Copyright (C) 2019-2025 QLM Network Entertainment Technology Co., Ltd.'),\n"
        "        StringStruct(u'OriginalFilename', u'SuperHiVision_v%s.exe'),\n"
        "        StringStruct(u'ProductName', u'%s'),\n"
        "        StringStruct(u'ProductVersion', u'%s')\n"
        '      ])\n'
        '    ]),\n'
        "    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])\n"
        '  ]\n'
        ')\n'
    ) % (_vnum[0], _vnum[1], _vnum[2], _vnum[3],
         _vnum[0], _vnum[1], _vnum[2], _vnum[3],
         APP_PUBLISHER, APP_NAME, APP_VERSION, APP_VERSION, APP_NAME, APP_VERSION)
    VERSION_FILE = _os.path.join(_tempfile.gettempdir(), 'shv_version_info.txt')
    with open(VERSION_FILE, 'w', encoding='utf-8') as _f:
        _f.write(_vi)

    # Self-check before handing it to PyInstaller: exec it with stub classes so
    # a malformed structure is caught HERE (and we just build without a version
    # resource) instead of aborting the whole PyInstaller run. PyInstaller
    # injects VSVersionInfo/StringStruct/... into the namespace when it loads
    # the file, so stubs are enough to prove the structure parses.
    _Stub = type('_Stub', (object,), {'__init__': lambda self, *a, **k: None})
    _probe = dict((_n, _Stub) for _n in (
        'VSVersionInfo', 'FixedFileInfo', 'StringFileInfo', 'StringTable',
        'StringStruct', 'VarFileInfo', 'VarStruct'))
    exec(compile(_vi, 'shv_version_probe', 'exec'), _probe)

    print('[spec] version resource: publisher=%s version=%s (self-check ok)'
          % (APP_PUBLISHER, APP_VERSION))
except Exception as _e:
    VERSION_FILE = None
    print('[spec] WARNING: version resource skipped (%s)' % _e)

EXE_NAME = 'SuperHiVision_v%s' % APP_VERSION

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
    name=EXE_NAME,
    version=VERSION_FILE,
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
