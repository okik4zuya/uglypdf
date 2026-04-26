import io
import os
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog

import PIL.Image
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject, NumberObject

from .config import GHOSTSCRIPT_PATH
from .widgets import DropZone, LogPanel


def _find_ghostscript() -> str | None:
    """Return path to gswin64c.exe — bundled first, then system PATH."""
    if os.path.isfile(GHOSTSCRIPT_PATH):
        return GHOSTSCRIPT_PATH
    for exe in ("gswin64c", "gswin32c", "gs"):
        path = shutil.which(exe)
        if path:
            return path
    return None


_GS_SETTINGS = {
    "low":    "/screen",
    "medium": "/ebook",
    "high":   "/printer",
    "custom": "/ebook",
}


_PRESETS = {
    "low":    dict(quality=40,  dpi=96,  meta=True,  streams=True, thumbs=False),
    "medium": dict(quality=65,  dpi=150, meta=True,  streams=True, thumbs=False),
    "high":   dict(quality=85,  dpi=300, meta=False, streams=True, thumbs=False),
}


def _human_size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} GB"


def _compress_xobject_dict(xobjects, quality: int, max_px: float | None) -> int:
    """Re-compress raster images in an XObject dict. Returns count replaced."""
    count = 0
    for key in list(xobjects.keys()):
        try:
            xobj = xobjects[key].get_object()
            subtype = xobj.get("/Subtype")

            # Recurse into Form XObjects — they carry their own Resources/XObject tree
            if subtype == "/Form":
                form_res = xobj.get("/Resources")
                if form_res:
                    form_res = form_res.get_object()
                    form_xobjs = form_res.get("/XObject")
                    if form_xobjs:
                        count += _compress_xobject_dict(
                            form_xobjs.get_object(), quality, max_px
                        )
                continue

            if subtype != "/Image":
                continue

            # Skip colour-key / stencil hard masks (rare, complex)
            if "/Mask" in xobj and "/SMask" not in xobj:
                continue

            width  = int(xobj["/Width"])
            height = int(xobj["/Height"])
            bits   = int(xobj.get("/BitsPerComponent", 8))
            if bits != 8:
                continue

            cs_obj = xobj.get("/ColorSpace")
            if cs_obj is None:
                continue
            cs_res  = cs_obj.get_object() if hasattr(cs_obj, "get_object") else cs_obj
            cs_name = str(cs_res[0] if isinstance(cs_res, ArrayObject) else cs_res)

            if   "Gray" in cs_name: mode, ch = "L",    1
            elif "CMYK" in cs_name: mode, ch = "CMYK", 4
            elif "RGB"  in cs_name: mode, ch = "RGB",  3
            else:                   continue

            filt_obj = xobj.get("/Filter")
            is_jpeg  = filt_obj is not None and "DCTDecode" in str(filt_obj)
            raw      = xobj.get_data()

            if is_jpeg:
                img = PIL.Image.open(io.BytesIO(raw))
                img.load()
            else:
                if len(raw) != width * height * ch:
                    continue
                img = PIL.Image.frombytes(mode, (width, height), raw)

            # Composite SMask (soft alpha) onto white so the output is opaque JPEG
            smask_handled = False
            smask_ref = xobj.get("/SMask")
            if smask_ref is not None:
                try:
                    smask_obj = smask_ref.get_object()
                    sw = int(smask_obj["/Width"])
                    sh = int(smask_obj["/Height"])
                    mask_raw = smask_obj.get_data()
                    if len(mask_raw) == sw * sh:
                        alpha = PIL.Image.frombytes("L", (sw, sh), mask_raw)
                        rgba  = img.convert("RGBA")
                        rgba.putalpha(
                            alpha.resize((img.width, img.height), PIL.Image.LANCZOS)
                        )
                        background = PIL.Image.new("RGB", rgba.size, (255, 255, 255))
                        background.paste(rgba, mask=rgba.split()[3])
                        img = background
                        smask_handled = True
                except Exception:
                    pass

            # Downsample if longest axis exceeds the DPI target for this page
            if max_px and max(img.width, img.height) > max_px:
                ratio = max_px / max(img.width, img.height)
                img   = img.resize(
                    (max(1, int(img.width * ratio)), max(1, int(img.height * ratio))),
                    PIL.Image.LANCZOS,
                )

            out_img = img.convert("RGB") if mode == "CMYK" else img
            buf = io.BytesIO()
            out_img.save(buf, "JPEG", quality=quality, optimize=True)
            compressed = buf.getvalue()

            if len(compressed) >= len(raw):
                continue

            for k in ("/Filter", "/DecodeParms"):
                if k in xobj:
                    del xobj[k]
            xobj.set_data(compressed)
            xobj[NameObject("/Filter")]           = NameObject("/DCTDecode")
            xobj[NameObject("/Width")]            = NumberObject(out_img.width)
            xobj[NameObject("/Height")]           = NumberObject(out_img.height)
            xobj[NameObject("/BitsPerComponent")] = NumberObject(8)
            if mode == "CMYK":
                xobj[NameObject("/ColorSpace")] = NameObject("/DeviceRGB")
            if smask_handled and "/SMask" in xobj:
                del xobj["/SMask"]
            count += 1

        except Exception:
            continue

    return count


def _compress_images_on_page(page, quality: int, max_dpi: int | None) -> int:
    """Re-compress raster images on a page using Pillow. Returns count replaced."""
    resources = page.get("/Resources")
    if not resources:
        return 0
    resources = resources.get_object()
    xobjects = resources.get("/XObject")
    if not xobjects:
        return 0

    if max_dpi:
        try:
            mb = page.mediabox
            max_px = max(float(mb.width), float(mb.height)) / 72.0 * max_dpi
        except Exception:
            max_px = float(max_dpi * 11)
    else:
        max_px = None

    return _compress_xobject_dict(xobjects.get_object(), quality, max_px)


class CompressTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg="#f5f5f5")
        self.files: list[str] = []
        self._build()

    def _build(self):
        BG = "#f5f5f5"

        DropZone(self, label="Drop PDF files here",
                 on_drop=self._add_files,
                 on_browse=self._browse).pack(fill="x", padx=12, pady=(12, 4))

        # File list — fixed height, no expand
        list_frame = tk.Frame(self, bg=BG)
        list_frame.pack(fill="x", padx=12, pady=(0, 4))
        tk.Label(list_frame, text="Files queued:", bg=BG,
                 font=("Segoe UI", 9), fg="#333").pack(anchor="w")
        inner = tk.Frame(list_frame, bg=BG)
        inner.pack(fill="x")
        sb = tk.Scrollbar(inner, orient="vertical")
        sb.pack(side="right", fill="y")
        self.listbox = tk.Listbox(inner, font=("Segoe UI", 9), height=4,
                                   yscrollcommand=sb.set, bg="white",
                                   selectbackground="#bbdefb", relief="solid", bd=1)
        self.listbox.pack(fill="x", expand=True)
        sb.config(command=self.listbox.yview)

        file_btns = tk.Frame(list_frame, bg=BG)
        file_btns.pack(anchor="w", pady=(2, 0))
        tk.Button(file_btns, text="Remove Selected", command=self._remove,
                  relief="flat", bg="#e0e0e0", padx=8, pady=3).pack(side="left")
        tk.Button(file_btns, text="Clear All", command=self._clear,
                  relief="flat", bg="#e0e0e0", padx=8, pady=3).pack(side="left", padx=6)

        # Preset
        self.pre_lf = tk.LabelFrame(self, text=" Preset ", bg=BG,
                                     font=("Segoe UI", 9), fg="#555")
        self.pre_lf.pack(fill="x", padx=12, pady=(4, 2))
        self.preset = tk.StringVar(value="medium")
        pre_row = tk.Frame(self.pre_lf, bg=BG)
        pre_row.pack(anchor="w", padx=8, pady=4)
        for label, val in [("Low", "low"), ("Medium", "medium"),
                            ("High", "high"), ("Custom", "custom")]:
            tk.Radiobutton(pre_row, text=label, variable=self.preset, value=val,
                           bg=BG, font=("Segoe UI", 9),
                           command=lambda v=val: self._apply_preset(v)
                           ).pack(side="left", padx=(0, 14))

        # Image + PDF options side by side — only shown when Custom is selected
        self.options_frame = tk.Frame(self, bg=BG)

        img_lf = tk.LabelFrame(self.options_frame, text=" Image ", bg=BG,
                                font=("Segoe UI", 9), fg="#555")
        img_lf.pack(side="left", fill="both", expand=True, padx=(0, 4))

        q_row = tk.Frame(img_lf, bg=BG)
        q_row.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(q_row, text="JPEG quality:", bg=BG, font=("Segoe UI", 9)).pack(side="left")
        self.img_quality = tk.IntVar(value=65)
        self.quality_lbl = tk.Label(q_row, text="65", width=3, bg=BG, font=("Segoe UI", 9))
        self.quality_lbl.pack(side="right")
        tk.Scale(q_row, from_=10, to=95, orient="horizontal", variable=self.img_quality,
                 bg=BG, highlightthickness=0, showvalue=False,
                 command=self._on_quality_change
                 ).pack(side="left", fill="x", expand=True, padx=6)

        dpi_row = tk.Frame(img_lf, bg=BG)
        dpi_row.pack(fill="x", padx=8, pady=(0, 6))
        self.limit_dpi_var = tk.BooleanVar(value=True)
        tk.Checkbutton(dpi_row, text="Limit resolution:", bg=BG, font=("Segoe UI", 9),
                       variable=self.limit_dpi_var,
                       command=self._on_custom_change).pack(side="left")
        self.max_dpi_var = tk.IntVar(value=150)
        tk.Spinbox(dpi_row, from_=72, to=600, increment=50, textvariable=self.max_dpi_var,
                   font=("Segoe UI", 9), width=5,
                   command=self._on_custom_change).pack(side="left", padx=4)
        tk.Label(dpi_row, text="DPI", bg=BG, font=("Segoe UI", 9)).pack(side="left")

        pdf_lf = tk.LabelFrame(self.options_frame, text=" PDF ", bg=BG,
                                font=("Segoe UI", 9), fg="#555")
        pdf_lf.pack(side="left", fill="both", expand=True)
        pdf_row = tk.Frame(pdf_lf, bg=BG)
        pdf_row.pack(anchor="w", padx=8, pady=(4, 6))
        self.remove_meta      = tk.BooleanVar(value=True)
        self.compress_streams = tk.BooleanVar(value=True)
        self.remove_images    = tk.BooleanVar(value=False)
        for text, var in [("Remove metadata",     self.remove_meta),
                           ("Re-compress streams", self.compress_streams),
                           ("Remove thumbnails",   self.remove_images)]:
            tk.Checkbutton(pdf_row, text=text, variable=var, bg=BG, font=("Segoe UI", 9),
                           command=self._on_custom_change).pack(anchor="w", pady=1)

        # Output
        out_lf = tk.LabelFrame(self, text=" Output ", bg=BG,
                                font=("Segoe UI", 9), fg="#555")
        out_lf.pack(fill="x", padx=12, pady=(2, 4))
        out_row = tk.Frame(out_lf, bg=BG)
        out_row.pack(fill="x", padx=8, pady=(6, 6))
        tk.Label(out_row, text="Save to:", bg=BG, font=("Segoe UI", 9)).pack(side="left")
        self.save_mode = tk.StringVar(value="same")
        tk.Radiobutton(out_row, text="Same folder  (_compressed suffix)",
                       variable=self.save_mode, value="same",
                       bg=BG, font=("Segoe UI", 9)).pack(side="left", padx=6)
        tk.Radiobutton(out_row, text="Choose folder…",
                       variable=self.save_mode, value="choose",
                       bg=BG, font=("Segoe UI", 9)).pack(side="left")

        # Compress button
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(fill="x", padx=12, pady=(0, 4))
        self.btn = tk.Button(btn_row, text="Compress", command=self._start,
                              relief="flat", bg="#e65100", fg="white",
                              font=("Segoe UI", 9, "bold"), padx=14, pady=3, cursor="hand2")
        self.btn.pack(side="right")

        self.log = LogPanel(self, height=5, bg=BG)
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    # ── preset ───────────────────────────────────────────────────────

    def _apply_preset(self, name: str):
        if name == "custom":
            self.options_frame.pack(fill="x", padx=12, pady=2, after=self.pre_lf)
            return
        self.options_frame.pack_forget()
        p = _PRESETS[name]
        self.img_quality.set(p["quality"])
        self.quality_lbl.configure(text=str(p["quality"]))
        self.limit_dpi_var.set(True)
        self.max_dpi_var.set(p["dpi"])
        self.remove_meta.set(p["meta"])
        self.compress_streams.set(p["streams"])
        self.remove_images.set(p["thumbs"])

    def _on_quality_change(self, val: str):
        self.quality_lbl.configure(text=str(int(float(val))))
        self._on_custom_change()

    def _on_custom_change(self, *_):
        self.preset.set("custom")
        self.options_frame.pack(fill="x", padx=12, pady=2, after=self.pre_lf)

    # ── file management ──────────────────────────────────────────────

    def _browse(self):
        paths = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        self._add_files(list(paths))

    def _add_files(self, paths: list[str]):
        added = 0
        for p in paths:
            if p.lower().endswith(".pdf") and p not in self.files:
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

    # ── compression ──────────────────────────────────────────────────

    def _start(self):
        if not self.files:
            self.log.write("No files queued.", "err")
            return
        if self.save_mode.get() == "choose":
            output_dir = filedialog.askdirectory(title="Select output folder")
            if not output_dir:
                return
        else:
            output_dir = None
        self.btn.configure(state="disabled", text="Compressing…")
        max_dpi = self.max_dpi_var.get() if self.limit_dpi_var.get() else None
        opts = {
            "preset":           self.preset.get(),
            "img_quality":      self.img_quality.get(),
            "max_dpi":          max_dpi,
            "remove_meta":      self.remove_meta.get(),
            "compress_streams": self.compress_streams.get(),
            "remove_images":    self.remove_images.get(),
        }
        threading.Thread(
            target=self._run, args=(list(self.files), output_dir, opts), daemon=True
        ).start()

    def _run(self, files: list[str], output_dir: str | None, opts: dict):
        for i, path in enumerate(files, 1):
            self.after(0, lambda p=path, n=i, t=len(files):
                       self.log.write(f"\n[{n}/{t}] {os.path.basename(p)}", "info"))
            self._compress_one(path, output_dir, opts)
        self.after(0, lambda: self.log.write("\nDone.", "ok"))
        self.after(0, lambda: self.btn.configure(state="normal", text="Compress"))

    def _compress_one(self, path: str, output_dir: str | None, opts: dict):
        try:
            before   = os.path.getsize(path)
            stem     = os.path.splitext(os.path.basename(path))[0]
            out_dir  = output_dir or os.path.dirname(path)
            out_path = os.path.join(out_dir, f"{stem}_compressed.pdf")

            gs = _find_ghostscript()
            if gs:
                self.after(0, lambda: self.log.write("  Using GhostScript…", "info"))
                gs_setting = _GS_SETTINGS.get(opts.get("preset", "medium"), "/ebook")
                subprocess.run(
                    [
                        gs,
                        "-dNOPAUSE", "-dBATCH", "-dQUIET",
                        "-sDEVICE=pdfwrite",
                        "-dCompatibilityLevel=1.4",
                        f"-dPDFSETTINGS={gs_setting}",
                        f"-sOutputFile={out_path}",
                        path,
                    ],
                    check=True,
                    creationflags=0x08000000,  # CREATE_NO_WINDOW on Windows
                )
            else:
                self.after(0, lambda: self.log.write(
                    "  GhostScript not found — using pypdf fallback.", "info"))
                reader  = PdfReader(path)
                writer  = PdfWriter()
                quality = opts["img_quality"]
                max_dpi = opts["max_dpi"]

                for page in reader.pages:
                    new_page = writer.add_page(page)
                    if opts["compress_streams"]:
                        new_page.compress_content_streams()
                    if quality < 95 or max_dpi:
                        _compress_images_on_page(new_page, quality, max_dpi)

                if not opts["remove_meta"] and reader.metadata:
                    writer.add_metadata(reader.metadata)

                writer.compress_identical_objects()

                if opts["remove_images"]:
                    for page in writer.pages:
                        if "/Resources" in page and "/XObject" in page["/Resources"]:
                            del page["/Resources"]["/XObject"]

                with open(out_path, "wb") as f:
                    writer.write(f)

            after = os.path.getsize(out_path)
            saved = before - after
            pct   = (saved / before * 100) if before else 0

            if saved > 0:
                self.after(0, lambda a=after, b=before, p=pct, o=out_path:
                           self.log.write(
                               f"  ✔ {_human_size(b)} → {_human_size(a)}"
                               f"  (−{p:.1f}%)  →  {os.path.basename(o)}", "ok"))
            else:
                self.after(0, lambda o=out_path:
                           self.log.write(
                               f"  ✔ Saved (no size reduction)  →  {os.path.basename(o)}",
                               "ok"))

        except Exception as e:
            self.after(0, lambda e=e: self.log.write(f"  ✘ Error: {e}", "err"))
