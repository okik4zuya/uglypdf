# Changelog

## 1.0.3

### Added
- New **MD → PDF** tab: converts Markdown (typed or from files) into styled PDFs (A4, 3cm margins), with emoji support via rasterized image fallback.
- Page Editor: **"Save Selected…"** button to export only the currently selected pages to a new PDF (in canvas order), alongside the existing "Save PDF…" (all pages).
- Clickable "reveal in Explorer" links for saved-file paths in the log panel (`LogPanel.write_link`), rolled out to Convert, Compress, Merge, and Split tabs.
- Windows NSIS installer (`installer.nsi`, `build_installer.bat`) and macOS build groundwork in CI.

### Changed
- `build.bat` now builds from `UglyPDF.spec` instead of raw PyInstaller CLI flags, so hand-tuned settings (e.g. `hiddenimports` for `xhtml2pdf`/`reportlab`) persist across builds.
- Compress tab's success log lines now show a clickable output-file link instead of plain text.

### Removed
- Top toolbar's "+ Open PDF" button — it silently failed to route files on tabs without an `_add_files` method (e.g. Page Editor); use each tab's own "Add"/"Drop" controls instead.

## 1.0.2

- Baseline prior to this changelog.
