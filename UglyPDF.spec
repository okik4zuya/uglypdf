# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules

# reportlab.graphics.barcode and xhtml2pdf both import submodules dynamically
# (via __import__ / plugin-style lookup), so PyInstaller's static analysis
# misses them unless listed explicitly here.
hidden = (
    collect_submodules('reportlab.graphics.barcode')
    + collect_submodules('xhtml2pdf')
)

a = Analysis(
    ['pdf2md_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('poppler', 'poppler'), ('tesseract', 'tesseract'), ('app', 'app'), ('icon.ico', '.')],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='UglyPDF',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='UglyPDF',
)
