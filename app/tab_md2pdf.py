import base64
import io
import os
import re
import threading
import tkinter as tk
from tkinter import filedialog

import markdown
from PIL import Image, ImageDraw
from xhtml2pdf import pisa

from .widgets import DropZone, LogPanel

# xhtml2pdf/reportlab draws text using the base14 PDF fonts (Helvetica etc.),
# which have no glyphs for status emoji — they render as blank boxes, and
# getting xhtml2pdf to honor a custom @font-face for just these characters
# proved unreliable. Render the icons as tiny raster images instead (drawn at
# 4x and downscaled for smooth edges) and swap them in as inline <img> tags,
# which xhtml2pdf always supports regardless of font/glyph coverage.
_VARIATION_SELECTORS = re.compile(f"[{chr(0xFE0E)}{chr(0xFE0F)}]")


def _icon_data_uri(draw_fn, size=32, supersample=4):
    hi = size * supersample
    img = Image.new("RGBA", (hi, hi), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(img), hi)
    img = img.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _draw_check(d, s):
    d.ellipse((s * 0.03, s * 0.03, s * 0.97, s * 0.97), fill=(56, 142, 60, 255))
    w = max(2, round(s * 0.09))
    d.line([(s * 0.27, s * 0.53), (s * 0.44, s * 0.70), (s * 0.75, s * 0.32)],
           fill="white", width=w, joint="curve")


def _draw_cross(d, s):
    d.ellipse((s * 0.03, s * 0.03, s * 0.97, s * 0.97), fill=(211, 47, 47, 255))
    m, w = s * 0.28, max(2, round(s * 0.09))
    d.line([(m, m), (s - m, s - m)], fill="white", width=w)
    d.line([(s - m, m), (m, s - m)], fill="white", width=w)


def _draw_warning(d, s):
    d.polygon([(s * 0.5, s * 0.06), (s * 0.97, s * 0.92), (s * 0.03, s * 0.92)],
              fill=(255, 179, 0, 255))
    w = max(2, round(s * 0.08))
    d.line([(s * 0.5, s * 0.40), (s * 0.5, s * 0.68)], fill="white", width=w)
    r = s * 0.035
    d.ellipse((s * 0.5 - r, s * 0.76 - r, s * 0.5 + r, s * 0.76 + r), fill="white")


def _draw_circle(color):
    def f(d, s):
        d.ellipse((s * 0.15, s * 0.15, s * 0.85, s * 0.85), fill=color)
    return f


_ICON_URIS = {
    "✅": _icon_data_uri(_draw_check),
    "⚠": _icon_data_uri(_draw_warning),
    "❌": _icon_data_uri(_draw_cross),
    "🔴": _icon_data_uri(_draw_circle((229, 57, 53, 255))),
    "🟡": _icon_data_uri(_draw_circle((249, 168, 37, 255))),
}


def _fix_unsupported_glyphs(html: str) -> str:
    html = _VARIATION_SELECTORS.sub("", html)
    for ch, uri in _ICON_URIS.items():
        html = html.replace(
            ch, f'<img src="{uri}" width="11" height="11" style="vertical-align:middle;">')
    return html


_PDF_CSS = """
<style>
@page { size: A4; margin: 2cm; }
body { font-family: Helvetica, sans-serif; font-size: 11pt; }
h1, h2, h3, h4 { color: #1a1a1a; }
code, pre { font-family: Consolas, monospace; background: #f0f0f0; }
pre { padding: 6px; border: 1px solid #ddd; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #ccc; padding: 4px 8px; }
blockquote { color: #555; border-left: 3px solid #ccc; margin: 0; padding-left: 10px; }
</style>
"""


def _md_to_pdf(md_text: str, out_path: str):
    html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
    html = _fix_unsupported_glyphs(html)
    html = f"<html><head>{_PDF_CSS}</head><body>{html}</body></html>"
    with open(out_path, "wb") as f:
        result = pisa.CreatePDF(html, dest=f)
    if result.err:
        raise RuntimeError("PDF generation failed")


class MdToPdfTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self.files: list[str] = []
        self.mode = tk.StringVar(value="files")
        self._build()

    def _build(self):
        mode_row = tk.Frame(self, bg="#f5f5f5")
        mode_row.pack(fill="x", padx=12, pady=(12, 4))
        tk.Label(mode_row, text="Input:", bg="#f5f5f5",
                 font=("Segoe UI", 9), fg="#333").pack(side="left")
        tk.Radiobutton(mode_row, text="Paste text", variable=self.mode,
                       value="paste", bg="#f5f5f5", font=("Segoe UI", 9),
                       command=self._switch_mode).pack(side="left", padx=6)
        tk.Radiobutton(mode_row, text="Select files", variable=self.mode,
                       value="files", bg="#f5f5f5", font=("Segoe UI", 9),
                       command=self._switch_mode).pack(side="left")

        # ── paste mode ─────────────────────────────────────────────
        self.paste_frame = tk.Frame(self, bg="#f5f5f5")
        text_wrap = tk.Frame(self.paste_frame, bg="#f5f5f5")
        text_wrap.pack(fill="both", expand=True)
        sb = tk.Scrollbar(text_wrap, orient="vertical")
        sb.pack(side="right", fill="y")
        self.text = tk.Text(text_wrap, font=("Consolas", 9), height=12,
                             wrap="word", yscrollcommand=sb.set,
                             relief="solid", bd=1)
        self.text.pack(fill="both", expand=True)
        sb.config(command=self.text.yview)

        paste_btn_row = tk.Frame(self.paste_frame, bg="#f5f5f5")
        paste_btn_row.pack(fill="x", pady=4)
        self.btn_paste = tk.Button(paste_btn_row, text="Convert to PDF", command=self._start,
                                    relief="flat", bg="#388e3c", fg="white",
                                    font=("Segoe UI", 9, "bold"), padx=14, pady=3,
                                    cursor="hand2")
        self.btn_paste.pack(side="right")

        # ── files mode ─────────────────────────────────────────────
        self.files_frame = tk.Frame(self, bg="#f5f5f5")
        DropZone(self.files_frame, label="Drop .md files here",
                 on_drop=self._add_files,
                 on_browse=self._browse).pack(fill="x", pady=(0, 4))

        list_frame = tk.Frame(self.files_frame, bg="#f5f5f5")
        list_frame.pack(fill="x", pady=4)
        tk.Label(list_frame, text="Files queued:", bg="#f5f5f5",
                 font=("Segoe UI", 9), fg="#333").pack(anchor="w")

        inner = tk.Frame(list_frame, bg="#f5f5f5")
        inner.pack(fill="x")
        lb_sb = tk.Scrollbar(inner, orient="vertical")
        lb_sb.pack(side="right", fill="y")
        self.listbox = tk.Listbox(inner, font=("Segoe UI", 9), height=4,
                                   yscrollcommand=lb_sb.set,
                                   bg="white", selectbackground="#bbdefb",
                                   relief="solid", bd=1)
        self.listbox.pack(fill="x", expand=True)
        lb_sb.config(command=self.listbox.yview)

        files_btn_row = tk.Frame(self.files_frame, bg="#f5f5f5")
        files_btn_row.pack(fill="x", pady=4)
        tk.Button(files_btn_row, text="Remove Selected", command=self._remove,
                  relief="flat", bg="#e0e0e0", padx=8, pady=3).pack(side="left")
        tk.Button(files_btn_row, text="Clear All", command=self._clear,
                  relief="flat", bg="#e0e0e0", padx=8, pady=3).pack(side="left", padx=6)
        self.btn_files = tk.Button(files_btn_row, text="Convert to PDF", command=self._start,
                                    relief="flat", bg="#388e3c", fg="white",
                                    font=("Segoe UI", 9, "bold"), padx=14, pady=3,
                                    cursor="hand2")
        self.btn_files.pack(side="right")

        self.files_frame.pack(fill="both", expand=True, padx=12, pady=4)
        self.btn = self.btn_files

        # ── log ─────────────────────────────────────────────────────
        self.log = LogPanel(self, height=7, bg="#f5f5f5")
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    # ── mode switching ───────────────────────────────────────────────

    def _switch_mode(self):
        if self.mode.get() == "paste":
            self.files_frame.pack_forget()
            self.paste_frame.pack(fill="both", expand=True, padx=12, pady=4,
                                   before=self.log)
            self.btn = self.btn_paste
        else:
            self.paste_frame.pack_forget()
            self.files_frame.pack(fill="both", expand=True, padx=12, pady=4,
                                   before=self.log)
            self.btn = self.btn_files

    # ── file management ─────────────────────────────────────────────

    def _browse(self):
        paths = filedialog.askopenfilenames(
            filetypes=[("Markdown files", "*.md;*.markdown")])
        self._add_files(list(paths))

    def _add_files(self, paths: list[str]):
        added = 0
        for p in paths:
            if p.lower().endswith((".md", ".markdown")) and p not in self.files:
                self.files.append(p)
                self.listbox.insert("end", os.path.basename(p))
                added += 1
        if added:
            self.log.write(f"Added {added} file(s).", "info")

    def _remove(self):
        sel = self.listbox.curselection()
        if sel:
            self.listbox.delete(sel[0])
            self.files.pop(sel[0])

    def _clear(self):
        self.listbox.delete(0, "end")
        self.files.clear()

    # ── conversion ──────────────────────────────────────────────────

    def _start(self):
        if self.mode.get() == "paste":
            text = self.text.get("1.0", "end").strip()
            if not text:
                self.log.write("No Markdown text to convert.", "err")
                return
            out_path = filedialog.asksaveasfilename(
                defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
            if not out_path:
                return
            self.btn.configure(state="disabled", text="Converting…")
            threading.Thread(target=self._run_paste, args=(text, out_path),
                              daemon=True).start()
        else:
            if not self.files:
                self.log.write("No files queued.", "err")
                return
            self.btn.configure(state="disabled", text="Converting…")
            threading.Thread(target=self._run_files, args=(list(self.files),),
                              daemon=True).start()

    def _run_paste(self, text: str, out_path: str):
        try:
            _md_to_pdf(text, out_path)
            self.after(0, lambda: self.log.write_link("✔ Saved: ", out_path, "ok"))
        except Exception as e:
            self.after(0, lambda e=e: self.log.write(f"✘ Error: {e}", "err"))
        finally:
            self.after(0, lambda: self.btn.configure(state="normal", text="Convert to PDF"))

    def _run_files(self, files: list[str]):
        for i, path in enumerate(files, 1):
            self.after(0, lambda p=path, n=i, t=len(files):
                       self.log.write(f"\n[{n}/{t}] {os.path.basename(p)}", "info"))
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
                out_path = os.path.splitext(path)[0] + ".pdf"
                _md_to_pdf(text, out_path)
                self.after(0, lambda p=out_path: self.log.write_link("  ✔ Saved: ", p, "ok"))
            except Exception as e:
                self.after(0, lambda e=e: self.log.write(f"  ✘ Error: {e}", "err"))
        self.after(0, lambda: self.log.write("\nAll done.", "ok"))
        self.after(0, lambda: self.btn.configure(state="normal", text="Convert to PDF"))
