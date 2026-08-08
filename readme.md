# Ugly PDF

A free, offline PDF toolkit for Windows. No upload. No account. Just PDF tools.

---

## Download

**[Download UglyPDF v1.0.2](https://github.com/okik4zuya/uglypdf/releases/download/v1.0.2/UglyPDF1.0.2.zip)**

- Windows 10 / 11 — `UglyPDFSetup-<version>.exe` installer (Start Menu shortcut, uninstaller) or the portable zip
- macOS — `UglyPDF.dmg` (drag to Applications). Unsigned build — see [Known Limitations](#known-limitations).

---

## Features

| Tool | Description |
| --- | --- |
| **PDF → Markdown** | Extract text from PDFs. Auto OCR fallback for scanned files. |
| **Compress** | Reduce file size by stripping metadata and re-compressing streams. |
| **Merge** | Combine multiple PDFs into one. Reorder before merging. |
| **Split** | Split by every page or by custom ranges (e.g. `1-3, 5, 7-9`). |
| **Page Editor** | Drag pages to reorder, rotate, delete. Mix pages from multiple PDFs. |

---

## Usage (pre-built)

**Windows (installer)**

1. Download and run `UglyPDFSetup-<version>.exe`
2. Launch UglyPDF from the Start Menu (or Desktop, if selected during install)

**Windows (portable zip)**

1. Download and unzip `UglyPDF.zip`
2. Open the `UglyPDF/` folder
3. Double-click `UglyPDF.exe`

**macOS**

1. Download and open `UglyPDF.dmg`
2. Drag `UglyPDF.app` to `Applications`
3. First launch: right-click the app → **Open** (or run `xattr -cr /Applications/UglyPDF.app`) to bypass the Gatekeeper "unidentified developer" warning — see [Known Limitations](#known-limitations)

Drag and drop PDF files onto the app. Output files are always saved next to the source PDF.

---

## Project Structure

```text
pdf2md-cli/
│
├── app/
│   ├── config.py          # paths for poppler / tesseract
│   ├── main.py            # app window + tab container
│   ├── toolbar.py         # top toolbar
│   ├── widgets.py         # shared: DropZone, LogPanel
│   ├── tab_convert.py     # PDF → Markdown
│   ├── tab_compress.py    # Compress
│   ├── tab_merge.py       # Merge
│   ├── tab_split.py       # Split
│   ├── tab_editor.py      # Page Editor
│   └── tab_about.py       # About
│
├── poppler/               # Poppler binaries, Windows (bundled)
├── tesseract/             # Tesseract OCR, Windows (bundled)
├── ghostscript/           # Ghostscript, Windows (bundled)
├── poppler-mac/           # Poppler binaries, macOS (bundled, not yet in repo)
├── tesseract-mac/         # Tesseract OCR, macOS (bundled, not yet in repo)
├── ghostscript-mac/       # Ghostscript, macOS (bundled, not yet in repo)
├── assets/
│   └── mascot.svg         # landing page mascot
│
├── .github/workflows/
│   └── release.yml        # CI: builds Windows installer + macOS dmg on version tags
│
├── pdf2md_gui.py          # entry point
├── pdf2md.py              # CLI version (legacy)
├── icon.ico               # app icon (Windows)
├── icon.icns              # app icon (macOS, not yet in repo)
├── index.html             # landing page
│
├── build.bat              # build standalone exe
├── build_installer.bat    # build exe + Windows NSIS installer
├── installer.nsi           # NSIS installer script
├── setup.bat              # set up venv on a new machine
├── run.bat                # run from source (CLI mode)
├── register.bat           # add Windows context menu
├── unregister.bat         # remove Windows context menu
└── requirements.txt
```

---

## Development Setup

### 1. Clone the repo

```bat
git clone https://github.com/okik4zuya/uglypdf
cd uglypdf
```

### 2. Create virtual environment

```bat
python -m venv venv
```

Or use the provided script:

```bat
setup.bat
```

### 3. Install dependencies

```bat
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Add bundled binaries

Place the following in the project root:

**Poppler** — download from [oschwartz10612/poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases)

```text
poppler/Library/bin/   ← extract here
```

**Tesseract** — download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)

```text
tesseract/tesseract.exe
tesseract/tessdata/eng.traineddata
```

**Ghostscript** — download from [ghostscript.com](https://www.ghostscript.com/releases/gsdnld.html)

```text
ghostscript/bin/gswin64c.exe
```

#### macOS binaries (for building/running on macOS)

These aren't produced on Windows and must be sourced separately (e.g. via `brew install` + copying the resulting binaries/dylibs out of the Homebrew cellar, or downloading prebuilt bottles):

```text
poppler-mac/            ← pdftoppm, pdftocairo + dylibs (from a poppler Homebrew bottle)
tesseract-mac/tesseract
tesseract-mac/tessdata/eng.traineddata
ghostscript-mac/gs
```

Also add `icon.icns` (converted from `icon.ico`) at the repo root for the macOS `.app` bundle icon.

### 5. Run from source

```bat
venv\Scripts\python pdf2md_gui.py
```

---

## Build Standalone Exe

Requires UPX for smaller output (optional):

1. Download [upx.exe](https://github.com/upx/upx/releases) and place it in `upx/`
2. Run:

```bat
build.bat
```

Output: `dist/UglyPDF/` — copy this folder to any Windows machine.

## Build Windows Installer

Requires [NSIS](https://nsis.sourceforge.io/Download) (`makensis.exe` on `PATH`):

```bat
build_installer.bat
```

Runs `build.bat` first, then compiles `installer.nsi` into `dist/UglyPDFSetup-<version>.exe`. Bump `APP_VERSION` in `installer.nsi` alongside `app/tab_about.py::VERSION` before building.

## macOS Build

No PyInstaller cross-compilation — macOS builds run on the `macos-latest` GitHub Actions runner defined in `.github/workflows/release.yml`, triggered by pushing a `v*` tag. It produces both the Windows installer and the macOS `.dmg` and attaches them to a GitHub Release. Requires the macOS binaries and `icon.icns` described above to be committed first.

---

## Dependencies

| Package | Purpose |
| --- | --- |
| `pdfminer.six` | Text extraction from PDFs |
| `pdf2image` | Render PDF pages to images (for OCR) |
| `Pillow` | Image processing |
| `pytesseract` | OCR via Tesseract |
| `pypdf` | Merge, split, compress, page editing |
| `tkinterdnd2` | Drag-and-drop support in the GUI |
| `pyinstaller` | Build standalone exe |

---

## Known Limitations

- Table structure is not preserved in Markdown output
- OCR quality depends on the scan resolution (300 DPI recommended)
- Compression results vary — some PDFs may not shrink significantly
- The Windows installer and macOS `.dmg` are unsigned. Windows may show a SmartScreen warning; macOS will refuse to open the app until you right-click → **Open** or run `xattr -cr` on it. Code signing/notarization is not yet set up.
- Windows context-menu integration (`register.bat`) is not wired into the installer — it must still be run manually. There is no macOS Finder equivalent.

---

## License

Free for personal use.
