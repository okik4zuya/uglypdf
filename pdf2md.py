import os
import sys

from pdfminer.high_level import extract_text
from pdf2image import convert_from_path
import pytesseract


def get_base_dir():
    """Return base directory (handles PyInstaller _MEIPASS)."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()

POPPLER_PATH = os.path.join(BASE_DIR, "poppler", "Library", "bin")
TESSERACT_PATH = os.path.join(BASE_DIR, "tesseract", "tesseract.exe")

if os.path.exists(TESSERACT_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def extract_text_to_markdown(pdf_path):
    """Convert one PDF file to Markdown."""
    try:

        output_md = os.path.splitext(pdf_path)[0] + ".md"

        print(f"\nProcessing: {os.path.basename(pdf_path)}")

        # Step 1: Try normal extraction
        text = extract_text(pdf_path)

        if not text.strip():
            print("  No text detected → running OCR...")

            pages = convert_from_path(
                pdf_path,
                dpi=300,
                poppler_path=POPPLER_PATH
            )

            text_list = []

            for i, page in enumerate(pages, start=1):
                print(f"  OCR page {i}/{len(pages)}...")
                ocr_text = pytesseract.image_to_string(page)
                text_list.append(ocr_text)

            text = "\n".join(text_list)

        else:
            print("  Text layer detected.")

        md_content = "# Extracted PDF Content\n\n" + text

        with open(output_md, "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"  ✔ Saved: {output_md}")

    except Exception as e:
        print(f"  ❌ Error processing {pdf_path}")
        print(f"     {e}")


def main():

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python pdf_to_md.py file1.pdf file2.pdf ...")
        sys.exit(1)

    pdf_files = sys.argv[1:]

    total = len(pdf_files)

    print("\nPDF → Markdown Conversion")
    print("-------------------------")

    for i, pdf in enumerate(pdf_files, start=1):

        if not os.path.exists(pdf):
            print(f"\n[{i}/{total}] ❌ File not found: {pdf}")
            continue

        print(f"\n[{i}/{total}] Starting...")
        extract_text_to_markdown(pdf)

    print("\nDone.")


if __name__ == "__main__":
    main()