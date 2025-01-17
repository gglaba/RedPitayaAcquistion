import customtkinter as ctk
import time

class StatusLine(ctk.CTkLabel):
    def __init__(self, parent):
        super().__init__(parent, text="", anchor="center", font=("Helvetica", 16, "bold"), fg_color="#333333", text_color="#FFFFFF")
        self.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self.start_time = None
        self.update_status("Ready")

    def update_status(self, message):
        self.configure(text=message)

    def start_timer(self):
        self.start_time = time.time()
        self.update_timer()

    def update_timer(self):
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            self.update_status(f"Acquisition in progress... Elapsed time: {elapsed_time:.2f} seconds")
            self.after(1000, self.update_timer)

    def stop_timer(self):
        self.start_time = None
        self.update_status("Acquisition completed")

    def show_error(self, error_message):
        self.update_status(f"Error: {error_message}")

    def show_transfer_status(self, filename):
        self.update_status(f"Transferring file: {filename}")