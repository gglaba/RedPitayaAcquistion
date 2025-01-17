from tkinter import *
import customtkinter as ctk

class ProgressWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Acquisition Progress")
        self.resizable(False, False)
        self.progressbar = ctk.CTkProgressBar(self)
        self.progressbar.configure(width=500, mode='indeterminate', progress_color="green", height=10)
        self.progressbar.pack(padx=10, pady=10)
        self.progressbar.start()

        self.status_label = ctk.CTkLabel(self, text="Acquiring signals...")
        self.status_label.pack(padx=10, pady=10)
        self.animate_status_label()


    def animate_status_label(self):
        text = self.status_label.cget("text")
        if text.count('.') < 3:
            text += '.'
        else:
            text = "Acquiring signals"
        self.status_label.configure(text=text)
        self.after(500, self.animate_status_label)
    
    def close(self):
        self.progressbar.stop()
        self.destroy()

