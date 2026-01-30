# PyInstaller spec for TfeaterMathLab Windows .exe
# Build from project root: pyinstaller deploy/windows/TfeaterMathLab.spec

import os

block_cipher = None
spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
project_root = os.path.abspath(os.path.join(spec_dir, '..', '..'))

# Bundle project files so the frozen app can run Django from _MEIPASS
datas = [
    (os.path.join(project_root, 'manage.py'), '.'),
    (os.path.join(project_root, 'mathsolver'), 'mathsolver'),
    (os.path.join(project_root, 'solver'), 'solver'),
]

# Django and app hidden imports (add more if runtime reports ModuleNotFoundError)
hiddenimports = [
    'django',
    'django.conf',
    'django.core',
    'django.core.management',
    'django.core.management.commands',
    'django.core.management.commands.migrate',
    'django.core.management.commands.runserver',
    'django.db',
    'django.utils',
    'django.apps',
    'mathsolver',
    'mathsolver.settings',
    'solver',
    'sympy',
    'matplotlib',
    'PIL',
    'reportlab',
    'requests',
]

a = Analysis(
    [os.path.join(spec_dir, 'launcher.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TfeaterMathLab',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='TfeaterMathLab',
)
