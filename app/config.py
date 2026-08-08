import os
import shutil
import sys


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    # app/ is one level inside the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


IS_MAC = sys.platform == "darwin"

BASE_DIR = get_base_dir()

if IS_MAC:
    # Packaged builds bundle these under *-mac/ (see .github/workflows/release.yml).
    # Running from source on a real Mac, fall back to Homebrew-installed
    # binaries on PATH instead.
    _poppler_mac = os.path.join(BASE_DIR, "poppler-mac")
    POPPLER_PATH = _poppler_mac if os.path.isdir(_poppler_mac) else None

    _tesseract_mac = os.path.join(BASE_DIR, "tesseract-mac", "tesseract")
    TESSERACT_PATH = _tesseract_mac if os.path.isfile(_tesseract_mac) else (shutil.which("tesseract") or _tesseract_mac)

    _gs_mac = os.path.join(BASE_DIR, "ghostscript-mac", "gs")
    GHOSTSCRIPT_PATH = _gs_mac if os.path.isfile(_gs_mac) else (shutil.which("gs") or _gs_mac)
else:
    POPPLER_PATH     = os.path.join(BASE_DIR, "poppler", "Library", "bin")
    TESSERACT_PATH   = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")
    GHOSTSCRIPT_PATH = os.path.join(BASE_DIR, "ghostscript", "bin", "gswin64c.exe")
