# -*- coding: utf-8 -*-
"""Verify the generated VSVersionInfo file is loadable the way PyInstaller loads it.

PyInstaller reads the file passed to EXE(..., version=...) through
PyInstaller.utils.win32.versioninfo.load_version_info_from_text_file(), which
executes it as Python and then walks the resulting VersionInfo object.
This reproduces that loading path so a malformed resource is caught before CI.

Run from the repository root:  python tools/check_version_resource.py
"""
import os
import sys

SPEC = 'SuperHiVision.spec'
if not os.path.exists(SPEC):
    sys.exit('run me from the repository root (SuperHiVision.spec not found)')

# --- 1. produce the resource exactly like the spec does -------------------
spec = open(SPEC, encoding='utf-8').read()
code = spec[spec.index('block_cipher = None'):spec.index('EXE_NAME = ')] \
    + "EXE_NAME = 'SuperHiVision_v%s' % APP_VERSION\n"
ns = {'__name__': 'spec_probe', 'os': os, 'sys': sys}
exec(compile(code, 'spec_probe', 'exec'), ns)
vfile = ns['VERSION_FILE']
if not vfile:
    sys.exit('FAILED: the spec produced no version resource')
print('resource file:', vfile)

# --- 2. prefer PyInstaller's own loader ----------------------------------
try:
    from PyInstaller.utils.win32 import versioninfo

    vi = versioninfo.load_version_info_from_text_file(vfile)
    print('PyInstaller loader: OK')
    for kid in getattr(vi, 'kids', []):
        if type(kid).__name__ == 'StringFileInfo':
            for table in getattr(kid, 'kids', []):
                for st in getattr(table, 'kids', []):
                    print(f'  {st.name} = {st.val}')
    print('RESULT: OK (validated with PyInstaller)')
    sys.exit(0)
except ImportError:
    print('PyInstaller not installed - falling back to a plain exec check')
except Exception as e:
    print(f'FAILED: PyInstaller rejected the resource file: {type(e).__name__}: {e}')
    sys.exit(1)

# --- 3. fallback: the same stub-based structural check the spec performs ----
# VSVersionInfo / StringStruct / ... are injected by PyInstaller at load time,
# so define stubs; if the structure parses with stubs, PyInstaller can load it.
try:
    source = open(vfile, encoding='utf-8').read()
    _Stub = type('_Stub', (object,), {'__init__': lambda self, *a, **k: None})
    probe = dict((n, _Stub) for n in (
        'VSVersionInfo', 'FixedFileInfo', 'StringFileInfo', 'StringTable',
        'StringStruct', 'VarFileInfo', 'VarStruct'))
    exec(compile(source, vfile, 'exec'), probe)
    assert 'SevenZeroMeowTeam' in source, 'publisher name missing'
    assert ns['APP_VERSION'] in source, 'version string missing'
    print('structural check: OK (stub classes)')
    print('RESULT: OK (fallback check - install PyInstaller to use the real loader)')
    sys.exit(0)
except Exception as e:
    print(f'FAILED: {type(e).__name__}: {e}')
    sys.exit(1)
