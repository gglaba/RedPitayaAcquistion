# ui_setup.py
import customtkinter as ctk
from CheckBoxes import CheckBoxes
from InputBoxes import InputBoxes
from StatusLine import StatusLine

def setup_ui(app,env_master_rp, env_slave1, env_slave2):
    app.status_line = StatusLine(app)
        
    app.title("RedPitaya Signal Acquisition")
    app.geometry("600x420")
    app.grid_columnconfigure(0, weight=1)
    app.resizable(False, False) #disabling resizing of the window

    app.grid_columnconfigure(0, weight=1)
    app.grid_columnconfigure(1, weight=1)
    app.grid_rowconfigure(0, weight=1)
    app.grid_rowconfigure(1, weight=1)
    app.grid_rowconfigure(2, weight=1)
    app.grid_rowconfigure(3, weight=0)
    app.grid_rowconfigure(4, weight=0)
    app.grid_rowconfigure(5, weight=0)
    app.grid_rowconfigure(6, weight=0)

    app.status_line.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

    app.checkboxes_frame = CheckBoxes(app, "Devices", ips=[env_master_rp, env_slave1, env_slave2]) #creating checkbox for each device (using checkboxes class)
    app.checkboxes_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

    app.connect_button = ctk.CTkButton(app, text="Connect to Pitayas", command=app.start_connect_to_devices_thread) #creating connect button
    app.connect_button.grid(row=3, column=0,columnspan=2, padx=10, pady=10)

    app.inputboxes_frame = InputBoxes(app, "Parameters", labels=['Decimation', 'Buffer size', 'Delay', 'Loops'], status_line=app.status_line)
    app.inputboxes_frame.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nsew")

    app.acquire_button = ctk.CTkButton(app, text="Acquire Signals", command=app.initiate_acquisition) #creating acquire button
    app.acquire_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
    app.acquire_button.configure(state="disabled")

    app.transfer_button = ctk.CTkButton(app, text="Transfer Data", command=app.transfer_files) #creating transfer button
    app.transfer_button.grid(row=5, column=0, padx=10,columnspan=2, pady=10)
    app.transfer_button.configure(state="disabled")

    app.isLocal = ctk.StringVar(value=1)
    app.switch_local_frame = ctk.CTkFrame(app)
    app.switch_local_frame.grid(row=4, column=0, padx=10, pady=10, sticky="w")
    app.switch_local = ctk.CTkSwitch(app.switch_local_frame, text="Local Acquisition",command=app.get_IsLocal, variable=app.isLocal, onvalue=1, offvalue=0)
    app.switch_local.grid(row=0, column=0, padx=10, pady=10, sticky="w")