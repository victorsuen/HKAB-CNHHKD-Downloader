# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['HKAB_CNHHKD.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['babel.numbers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['torch', 'torchvision', 'tensorflow', 'transformers', 'datasets', 'scipy', 'matplotlib', 'sympy', 'botocore', 'boto3', 'pydantic', 'pyarrow', 'IPython', 'sklearn', 'numba', 'PIL', 'jinja2', 'sqlalchemy', 'dask', 'tables', 'notebook', 'Crypto', 'cv2'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HKAB_CNHHKD',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['..\\icon.ico'],
)
