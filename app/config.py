import os
import sys


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    # app/ is one level inside the project root
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


IS_MAC = sys.platform == "darwin"

BASE_DIR = get_base_dir()

if IS_MAC:
    POPPLER_PATH     = os.path.join(BASE_DIR, "poppler-mac")
    TESSERACT_PATH   = os.path.join(BASE_DIR, "tesseract-mac", "tesseract")
    GHOSTSCRIPT_PATH = os.path.join(BASE_DIR, "ghostscript-mac", "gs")
else:
    POPPLER_PATH     = os.path.join(BASE_DIR, "poppler", "Library", "bin")
    TESSERACT_PATH   = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")
    GHOSTSCRIPT_PATH = os.path.join(BASE_DIR, "ghostscript", "bin", "gswin64c.exe")
