import tkinter as tk


class Toolbar(tk.Frame):
    """Thin top bar showing the app name."""

    def __init__(self, parent, notebook, tabs: dict, **kw):
        super().__init__(parent, bg="#1a1a1a", height=38, **kw)
        self.pack_propagate(False)
        self._nb   = notebook
        self._tabs = tabs   # { tab_index: tab_frame }
        self._build()

    def _build(self):
        # App name — left
        tk.Label(self, text="Ugly PDF", bg="#1a1a1a", fg="#ffffff",
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=14)
