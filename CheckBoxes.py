import time
from tkinter import *
import customtkinter as ctk

# checkboxes class handling labels and disconnect buttons

class CheckBoxes(ctk.CTkFrame):
    def __init__(self, master, title, ips):
        super().__init__(master)
        self.ips = ips
        self.title = title
        self.checkboxes = []
        self.labels = []
        self.vars = []
        self.disconnect_buttons = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        for i, ip in enumerate(self.ips):  # creating checkboxes for each ip
            var = IntVar()
            checkbox = ctk.CTkCheckBox(self, text=ip, variable=var)
            checkbox.grid(row=i + 1, column=0, padx=10, pady=(15, 15), sticky="w")
            self.checkboxes.append(checkbox)
            self.vars.append(var)

            disconnect_button = ctk.CTkButton(
                self,
                text="Disconnect",
                command=lambda ip=ip: self.master.disconnect_from_device(ip)
            )
            disconnect_button.grid(row=i + 1, column=0, padx=10, pady=10, sticky="w")
            disconnect_button.grid_remove()  # hiding disconnect buttons
            self.disconnect_buttons[ip] = disconnect_button

            label = ctk.CTkLabel(self, text="Disconnected", fg_color="red")
            label.grid(row=i + 1, column=1, padx=10, pady=(10, 0), sticky="ew")
            self.labels.append(label)

        self.title_label = ctk.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=5)
        self.title_label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

        # Add "Connect to All" button
        self.connect_all_btn = ctk.CTkButton(
            self,
            text="Connect to All",
            command=self.select_all_and_connect
        )
        self.connect_all_btn.grid(row=len(self.ips) + 2, column=0, padx=10, pady=5, sticky="ew")

    def show_disconnect_button(self, ip):
        self.disconnect_buttons[ip].grid()

    def hide_disconnect_button(self, ip):
        self.disconnect_buttons[ip].grid_remove()
        
    def hide_connect_all_button(self): 
        self.connect_all_btn.grid_remove()
        
    def show_connect_all_button(self): 
        self.connect_all_btn.grid()

    def get(self):
        selected_ips = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                selected_ips.append(checkbox.cget("text"))
        return selected_ips

    def update_label(self, ip, status):
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.cget("text") == ip:
                self.labels[i].configure(text=status)
                if status == "Connected":
                    self.labels[i].configure(fg_color="green")
                else:
                    self.labels[i].configure(fg_color="red")
                break

    def select_all(self):
        for var in self.vars:
            var.set(1)

    def select_all_and_connect(self):
        self.select_all()
        self.connect_all_btn.configure(state="disabled")
        try:
            self.connect_all_btn.configure(state="disabled")
            if hasattr(self.master, "start_connect_to_devices_thread"):
                self.master.start_connect_to_devices_thread()
        finally:
            if hasattr(self.master, "connections"):
                    if len(self.master.connections) != 2:
                        self.connect_all_btn.configure(state="normal")
            
