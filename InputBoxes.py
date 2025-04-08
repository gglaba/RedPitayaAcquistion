# # # from tkinter import *
# # # import customtkinter as ctk

# # # class InputBoxes(ctk.CTkFrame):
# # #     def __init__(self, master, title, labels,status_line):
# # #         super().__init__(master)
# # #         self.labels = labels
# # #         self.inputs = {}
# # #         self.grid_columnconfigure(0, weight=1)
# # #         self.grid_columnconfigure(1, weight=1)
# # #         self.status_line = status_line
# # #         self.label = ctk.CTkLabel(self, text=title, fg_color="gray30", corner_radius=5)
# # #         self.label.grid(row=0, column=0, padx=10, pady=(10,0),sticky = 'ew')
        
# # #         # Default values dictionary
# # #         default_values = {
# # #             "Decimation": 1,
# # #             "Buffer size": 16384,
# # #             "Delay": 0,
# # #             "Loops": 64
# # #         }

# # #         descriptions = {
# # #             "Decimation": "Decimation factor for signal processing",
# # #             "Buffer size": "Size of the buffer for data acquisition",
# # #             "Delay": "Delay before starting the acquisition",
# # #             "Loops": "Number of loops for the acquisition process"
# # #         }

# # #         decimation_options = {
# # #             "125 MSPS" : "RP_DEC_1",
# # #             "62.5 MSPS" : "RP_DEC_2",
# # #             "41.67 MSPS" : "RP_DEC_4",
# # #             "31.25 MSPS" : "RP_DEC_8",
# # #             "25 MSPS" : "RP_DEC_16",
# # #             "20.83 MSPS" : "RP_DEC_32",
# # #             "17.86 MSPS" : "RP_DEC_64",
# # #             "13.88 MSPS" : "RP_DEC_256",
# # #             "12.5 MSPS" : "RP_DEC_512",
# # #             "10.42 MSPS" : "RP_DEC_2048",
# # #             "7.35 MSPS" : "RP_DEC_65536"
# # #         }
        
# # #         # Validation function to ensure only numbers are entered
# # #         def validate_input(value_if_allowed):
# # #             if value_if_allowed.isdigit() or value_if_allowed == "":
# # #                 return True
# # #             else:
# # #                 return False
        
# # #         vcmd = (self.register(validate_input), '%P')

# # #         for i, ip in enumerate(self.labels):
# # #             label = ctk.CTkLabel(self, text=ip)
# # #             label.grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")

# # #             if ip == "Decimation":
# # #                 input_var = StringVar(value="125 MSPS")
# # #                 input_entry = ctk.CTkComboBox(self, values=list(decimation_options.keys()), textvariable=input_var)
# # #             else:
# # #                 input_var = IntVar(value=0)
# # #                 input_entry = ctk.CTkEntry(self, textvariable=input_var)

# # #             input_entry.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")
# # #             self.bind_input_click(input_entry, descriptions.get(ip, "No description available"))
# # #             self.inputs[ip] = input_var
        
# # #         self.decimation_options = decimation_options
    
# # #     def bind_input_click(self, widget, info):
# # #         widget.bind("<Button-1>", lambda event: self.on_input_click(event, info))

# # #     def on_input_click(self, event,info):
# # #         # Update the status line when an input box is clicked
# # #         self.status_line.update_status(f'{info}')


# # #     def get(self):
# # #         result = {}
# # #         for ip, var in self.inputs.items():
# # #             if ip == "Decimation":
# # #                 result[ip] = self.decimation_options[var.get()]
# # #             else:
# # #                 result[ip] = var.get()
# # #         return result

# # from tkinter import *
# # import customtkinter as ctk

# # class InputBoxes(ctk.CTkFrame):
# #     def __init__(self, master, title, labels, status_line):
# #         super().__init__(master)
# #         self.labels = labels
# #         self.inputs = {}
# #         self.grid_columnconfigure(0, weight=1)
# #         self.grid_columnconfigure(1, weight=1)
# #         self.status_line = status_line
# #         self.label = ctk.CTkLabel(self, text=title, fg_color="gray30", corner_radius=5)
# #         self.label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky='ew')

# #         descriptions = {
# #             "Decimation": "Decimation factor for signal processing",
# #             "Buffer size": "Size of the buffer for data acquisition",
# #             "Delay": "Delay before starting the acquisition",
# #             "Loops": "Number of loops for the acquisition process",
# #             "Time" : "Time for the acquisition process"
# #         }

# #         default_values = {
# #             "Buffer size": 16384,
# #             "Delay": 0,
# #             "Loops": 64
# #         }

# #         decimation_options = {
# #             "125 MSa/s": "1",
# #             "62.5 MSa/s": "2",
# #             "31.25 MSa/s": "4",
# #             "15.6 MSa/s": "8",
# #             "7.8 MSa/s": "16",
# #             "3.9 MSa/s": "32",
# #             "1.95 MSa/s": "64",
# #             "122.07 kSa/s": "1024",
# #             "15.258 kSa/s": "8192",
# #             "1.907 kSa/s": "65536"
# #         }

# #         self.decimation_options = decimation_options


# #         for i, ip in enumerate(self.labels):
# #             label = ctk.CTkLabel(self, text=ip)
# #             label.grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")

# #             if ip == "Decimation":
# #                 input_entry = ctk.CTkComboBox(self, values=list(decimation_options.keys()))
# #                 input_entry.set("125 MSa/s")
# #             else:
# #                 input_var = IntVar(value=default_values.get(ip, 0))
# #                 input_entry = ctk.CTkEntry(self, textvariable=input_var)

# #             input_entry.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")
# #             self.bind_input_click(input_entry, descriptions.get(ip, "No description available"))
# #             self.inputs[ip] = input_entry

# #         self.decimation_options = decimation_options

# #     def bind_input_click(self, widget, info):
# #         widget.bind("<Button-1>", lambda event: self.on_input_click(event, info))

# #     def on_input_click(self, event, info):
# #         # Update the status line when an input box is clicked
# #         self.status_line.update_status(f'{info}')

# #     def get(self):
# #         result = {}
# #         for ip, widget in self.inputs.items():
# #             if ip == "Decimation":
# #                 result[ip] = self.decimation_options[widget.get()]
# #             else:
# #                 result[ip] = widget.get()
# #         return result


# from tkinter import *
# import customtkinter as ctk
# import math

# class InputBoxes(ctk.CTkFrame):
#     def __init__(self, master, title, labels, status_line):
#         super().__init__(master)
#         self.labels = labels
#         self.inputs = {}
#         self.grid_columnconfigure(0, weight=1)
#         self.grid_columnconfigure(1, weight=1)
#         self.status_line = status_line
#         self.label = ctk.CTkLabel(self, text=title, fg_color="gray30", corner_radius=5)
#         self.label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky='ew')

#         descriptions = {
#             "Decimation": "Decimation factor for signal processing",
#             "Buffer size": "Size of the buffer for data acquisition",
#             "Delay": "Delay before starting the acquisition",
#             "Loops": "Number of loops for the acquisition process",
#             "Time": "Time for the acquisition process"
#         }

#         default_values = {
#             "Buffer size": 16384,
#             "Delay": 0,
#             "Loops": 64,
#             "Time": 0.008 # Default time in seconds
#         }

#         decimation_options = {
#             "125 MSa/s": "1",
#             "62.5 MSa/s": "2",
#             "31.25 MSa/s": "4",
#             "15.6 MSa/s": "8",
#             "7.8 MSa/s": "16",
#             "3.9 MSa/s": "32",
#             "1.95 MSa/s": "64",
#             "122.07 kSa/s": "1024",
#             "15.258 kSa/s": "8192",
#             "1.907 kSa/s": "65536"
#         }

#         self.decimation_options = decimation_options

#         def getSampling(sampling_rate):
#             factor = int(self.decimation_options[sampling_rate])
#             return 125e6 / factor

#         def getLoopsCount():
#             try:
#                 time = float(self.inputs["Time"].get())
#                 buffer = float(self.inputs["Buffer size"].get())
#                 sampling_input = self.inputs["Decimation"].get()
#                 sampling_rate = getSampling(sampling_input)
#                 if buffer > 0:
#                     loops = time * sampling_rate / buffer
#                     loops = max(0, loops)
#                 else:
#                     loops = 0
#                 self.inputs["Loops"].delete(0, "end")
#                 self.inputs["Loops"].insert(0, str(int(loops)))
#             except:
#                 pass

#         def getTime():
#             try:
#                 loops = float(self.inputs["Loops"].get())
#                 buffer = float(self.inputs["Buffer size"].get())
#                 sampling_input = self.inputs["Decimation"].get()
#                 sampling_rate = getSampling(sampling_input)
#                 if sampling_rate > 0:
#                     total_time = (buffer * loops) / sampling_rate
#                     total_time = max(0, total_time)
#                 else:
#                     total_time = 0
#                 self.inputs["Time"].delete(0, "end")
#                 self.inputs["Time"].insert(0, f"{total_time:.3f}")
#             except:
#                 pass

#         for i, ip in enumerate(self.labels):
#             label = ctk.CTkLabel(self, text=ip)
#             label.grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")

#             if ip == "Decimation":
#                 combo = ctk.CTkComboBox(self, values=list(decimation_options.keys()), command=lambda val: getTime())
#                 combo.set("125 MSa/s")
#                 combo.bind("<<ComboboxSelected>>", lambda e: getTime())
#                 self.inputs[ip] = combo
#                 combo.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")

#             elif ip == "Time":
#                 # Entry for time; changing time recalculates loops
#                 entry_time = ctk.CTkEntry(self)
#                 entry_time.insert(0, str(default_values.get(ip, 0)))
#                 entry_time.bind("<KeyRelease>", lambda e: getLoopsCount())
#                 self.inputs[ip] = entry_time
#                 entry_time.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")

#             else:
#                 # Entry for buffer size, loops, delay
#                 var = IntVar(value=default_values.get(ip, 0))
#                 entry = ctk.CTkEntry(self, textvariable=var)
#                 if ip in ["Buffer size", "Loops"]:
#                     # On key release, recalc time
#                     entry.bind("<KeyRelease>", lambda e: getTime())
#                 self.inputs[ip] = entry
#                 entry.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")

#             self.bind_input_click(self.inputs[ip], descriptions.get(ip, "No description available"))

#     def bind_input_click(self, widget, info):
#         widget.bind("<Button-1>", lambda event: self.on_input_click(event, info))

#     def on_input_click(self, event, info):
#         self.status_line.update_status(f'{info}')

#     def get(self):
#         result = {}
#         for ip, widget in self.inputs.items():
#             if ip == "Decimation":
#                 key = widget.get()
#                 result[ip] = self.decimation_options[key]
#             else:
#                 result[ip] = widget.get()
#         return result
from tkinter import *
import customtkinter as ctk

class InputBoxes(ctk.CTkFrame):
    def __init__(self, master, title, labels, status_line):
        super().__init__(master)
        self.labels = labels
        self.inputs = {}
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.status_line = status_line
        self.label = ctk.CTkLabel(self, text=title, fg_color="gray30", corner_radius=5)
        self.label.grid(row=0, column=0, padx=10, pady=(10, 0), sticky='ew')

        descriptions = {
            "Decimation": "Decimation factor for signal processing",
            "Buffer size": "Size of the buffer for data acquisition",
            "Delay": "Delay before starting the acquisition",
            "Loops": "Number of loops for the acquisition process",
            "Time": "Time for the acquisition process"
        }

        default_values = {
            "Buffer size": "16384",
            "Delay": "0",
            "Loops": "64",
            "Time": "0.008"
        }

        decimation_options = {
            "125 MSa/s": "1",
            "62.5 MSa/s": "2",
            "31.25 MSa/s": "4",
            "15.6 MSa/s": "8",
            "7.8 MSa/s": "16",
            "3.9 MSa/s": "32",
            "1.95 MSa/s": "64",
            "122.07 kSa/s": "1024",
            "15.258 kSa/s": "8192",
            "1.907 kSa/s": "65536"
        }

        self.decimation_options = decimation_options

        def getSampling(sampling_rate):
            factor = int(self.decimation_options[sampling_rate])
            return 125e6 / factor

        def getLoopsCount():
            try:
                time = float(self.inputs["Time"].get())
                buffer = float(self.inputs["Buffer size"].get())
                sampling_input = self.inputs["Decimation"].get()
                sampling_rate = getSampling(sampling_input)
                loops = max(0, time * sampling_rate / buffer) if buffer > 0 else 0
                self.inputs["Loops"].delete(0, "end")
                self.inputs["Loops"].insert(0, str(int(loops)))
            except:
                pass

        def getTime():
            try:
                loops = float(self.inputs["Loops"].get())
                buffer = float(self.inputs["Buffer size"].get())
                sampling_input = self.inputs["Decimation"].get()
                sampling_rate = getSampling(sampling_input)
                total_time = max(0, (buffer * loops) / sampling_rate) if sampling_rate > 0 else 0
                self.inputs["Time"].delete(0, "end")
                self.inputs["Time"].insert(0, f"{total_time:.3f}")
            except:
                pass

        for i, ip in enumerate(self.labels):
            label = ctk.CTkLabel(self, text=ip)
            label.grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")

            if ip == "Decimation":
                combo = ctk.CTkComboBox(self, values=list(decimation_options.keys()), command=lambda val: getTime())
                combo.set("125 MSa/s")
                combo.bind("<<ComboboxSelected>>", lambda e: getTime())
                self.inputs[ip] = combo
                combo.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")

            elif ip == "Time":
                var = StringVar(value=default_values.get(ip, "0"))
                var.trace_add("write", lambda *args: getLoopsCount())
                entry_time = ctk.CTkEntry(self, textvariable=var)
                self.inputs[ip] = entry_time
                entry_time.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")

            else:
                var = StringVar(value=default_values.get(ip, "0"))
                entry = ctk.CTkEntry(self, textvariable=var)
                if ip in ["Buffer size", "Loops"]:
                    entry.bind("<KeyRelease>", lambda e: getTime())
                self.inputs[ip] = entry
                entry.grid(row=i + 1, column=1, padx=10, pady=5, sticky="e")

            self.bind_input_click(self.inputs[ip], descriptions.get(ip, "No description available"))

    def bind_input_click(self, widget, info):
        widget.bind("<Button-1>", lambda event: self.on_input_click(event, info))

    def on_input_click(self, event, info):
        self.status_line.update_status(f'{info}')

    def get(self):
        result = {}
        for ip, widget in self.inputs.items():
            if ip == "Decimation":
                key = widget.get()
                result[ip] = self.decimation_options.get(key, "1")
            else:
                raw = widget.get()
                try:
                    result[ip] = float(raw) if ip == "Time" else int(raw)
                except ValueError:
                    result[ip] = 0
        return result
