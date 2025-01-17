from tkinter import *
import customtkinter as ctk

class InputBoxes(ctk.CTkFrame):
    def __init__(self, master, title, labels,status_line):
        super().__init__(master)
        self.labels = labels
        self.inputs = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.status_line = status_line
        self.label = ctk.CTkLabel(self, text=title, fg_color="gray30", corner_radius=5)
        self.label.grid(row=0, column=0, padx=10, pady=(10,0),sticky = 'ew')
        
        # Default values dictionary
        default_values = {
            "Decimation": 1,
            "Buffer size": 16384,
            "Delay": 0,
            "Loops": 64
        }

        descriptions = {
            "Decimation": "Decimation factor for signal processing",
            "Buffer size": "Size of the buffer for data acquisition",
            "Delay": "Delay before starting the acquisition",
            "Loops": "Number of loops for the acquisition process"
        }
        
        # Validation function to ensure only numbers are entered
        def validate_input(value_if_allowed):
            if value_if_allowed.isdigit() or value_if_allowed == "":
                return True
            else:
                return False
        
        vcmd = (self.register(validate_input), '%P')
        
        for i, ip in enumerate(self.labels):
            label = ctk.CTkLabel(self, text=ip)
            label.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")
            
            # Use default value if available, otherwise use 0
            default_value = default_values.get(ip, 0)
            input_var = IntVar(value=default_value)
            input_entry = ctk.CTkEntry(self, textvariable=input_var, validate="key", validatecommand=vcmd)
            input_entry.grid(row=i+1, column=1, padx=10, pady=5, sticky="e")
            self.bind_input_click(input_entry, descriptions.get(ip, "No description available"))
            self.inputs[ip] = input_var
    
    def bind_input_click(self, widget, info):
        widget.bind("<Button-1>", lambda event: self.on_input_click(event, info))

    def on_input_click(self, event,info):
        # Update the status line when an input box is clicked
        self.status_line.update_status(f'{info}')


    def get(self):
        return {ip: var.get() for ip, var in self.inputs.items()}