# Prosta klasa tooltip, działa dla tkinter / customtkinter widgets
import tkinter as tk

class ToolTip:
    def __init__(self, widget, text, delay=1000):
        self.widget = widget
        self.text = text
        self.delay = delay
        self._id = None
        self._tipwindow = None
        widget.bind("<Enter>", self._schedule)
        widget.bind("<Leave>", self._hide)
        widget.bind("<ButtonPress>", self._hide)
        widget.bind("<Motion>", self._motion)

    def _schedule(self, event=None):
        self._unschedule()
        self._id = self.widget.after(self.delay, self._show)

    def _unschedule(self):
        if self._id:
            try:
                self.widget.after_cancel(self._id)
            except Exception:
                pass
            self._id = None

    def _show(self):
        if self._tipwindow or not self.text:
            return
        x = y = 0
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("Segoe UI", 9))
        label.pack(ipadx=6, ipady=3)

    def _hide(self, event=None):
        self._unschedule()
        tw = self._tipwindow
        self._tipwindow = None
        if tw:
            try:
                tw.destroy()
            except Exception:
                pass

    def _motion(self, event=None):
        # opcjonalnie możemy przesuwać tooltip za kursorem; prosty wariant nic nie robi
        pass

# Funkcja pomocnicza do przypięcia wielu tooltipów
def attach_tooltips(mapping):
    for widget, text in mapping.items():
        try:
            ToolTip(widget, text)
        except Exception:
            pass
        