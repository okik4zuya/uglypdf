# PDF → Markdown Converter (CLI Tool)

A simple command-line tool to convert **PDF files into Markdown (.md)**.
It supports both:

* **Text-based PDFs** (fast extraction using `pdfminer`)
* **Scanned PDFs** (OCR using `Tesseract`)

The tool integrates with **Windows Explorer context menu**, allowing you to:

> Right-click any folder → select PDFs → convert them to Markdown.

---

# Features

* Convert **multiple PDFs at once**
* Detect **text layer automatically**
* **OCR fallback** for scanned documents
* Interactive **CLI selection**
* Works via **Windows right-click context menu**
* Uses **Python virtual environment (venv)** for isolation
* Supports **Poppler + Tesseract bundled locally**

---

# Example Workflow

Right-click a folder:

```
Convert PDF → Markdown
```

CLI opens:

```
Scanning folder:
D:\Research\Papers

1. paper1.pdf
2. thesis.pdf
3. report.pdf
4. notes.pdf

Select files (example: 1 3 4):
> 1 3

Starting conversion...

[1/2] paper1.pdf
  Text layer detected
  ✔ Saved: paper1.md

[2/2] thesis.pdf
  No text detected → OCR running
  ✔ Saved: thesis.md

Done.
```

Markdown files will be created in the **same directory as the PDFs**.

---

# Project Structure

```
pdf-md-tool/
│
├─ run.bat                # CLI launcher
├─ register.bat           # install context menu
├─ unregister.bat         # remove context menu
│
├─ pdf_to_md.py           # main conversion script
├─ requirements.txt
│
├─ venv/                  # Python virtual environment
│
├─ poppler/               # Poppler binaries
│   └─ Library/bin/
│
└─ tesseract/             # Tesseract OCR
    └─ tesseract.exe
```

---

# Installation

## 1 Create Virtual Environment

```
python -m venv venv
```

Activate it:

```
venv\Scripts\activate
```

---

## 2 Install Python Dependencies

```
pip install -r requirements.txt
```

Dependencies:

* `pdfminer.six`
* `pdf2image`
* `Pillow`
* `pytesseract`

---

## 3 Install Poppler

Download Poppler for Windows and place it inside:

```
poppler/Library/bin/
```

Used by:

```
pdf2image
```

---

## 4 Install Tesseract OCR

Download **Tesseract for Windows** and place:

```
tesseract.exe
```

inside:

```
tesseract/
```

Your structure should look like:

```
tesseract/tesseract.exe
```

---

# Enable Right-Click Menu

Run:

```
register.bat
```

This adds a Windows Explorer option:

```
Convert PDF → Markdown
```

---

# Remove Right-Click Menu

Run:

```
unregister.bat
```

---

# Manual Usage

You can also run the script directly:

```
venv\Scripts\python pdf_to_md.py file1.pdf file2.pdf
```

Example:

```
venv\Scripts\python pdf_to_md.py thesis.pdf report.pdf
```

---

# Output

For every PDF:

```
paper.pdf
```

A Markdown file will be created:

```
paper.md
```

Structure:

```
# Extracted PDF Content

(text content here)
```

---

# How It Works

1. Try extracting text using:

```
pdfminer
```

2. If the PDF has **no text layer**:

* convert pages to images (`pdf2image`)
* run OCR (`pytesseract`)

3. Combine the result and write:

```
Markdown (.md)
```

---

# Known Limitations

* Layout is **linearized** (not perfect for complex multi-column PDFs)
* Tables may not convert cleanly
* OCR quality depends on scan quality

---

# Possible Improvements

Future upgrades may include:

* Markdown **heading detection**
* Table reconstruction
* **Parallel PDF processing**
* Range selection (`1-5`)
* Skip already converted files
* Build **single EXE distribution**

---

# License

Free for personal and research use.

---

# Author

Created as a lightweight utility for **PDF text extraction and OCR to Markdown conversion**.
