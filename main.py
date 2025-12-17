import sys
from tkinter import *
import tkinter
import customtkinter as ctk
import os
import threading
import subprocess
from pathlib import Path
import queue
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import ConnectionManager
from ProgressWindow import ProgressWindow
from CheckBoxes import CheckBoxes
from InputBoxes import InputBoxes
from StatusLine import StatusLine
from PresetManager import PresetManager
from merge_files import merge_bin_files
import json
import re
import threading
import time
import datetime
from GUI_helper import ToolTip, attach_tooltips
from verify import parse_footer
import json

ctk.set_appearance_mode("dark")
load_dotenv()

ENV_MASTERRP = os.getenv("MASTER_RP")
ENV_SLAVE1 = os.getenv("SLAVE1")
ENV_SLAVE2 = os.getenv("SLAVE2")
ENV_PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
ENV_USERNAME = os.getenv("USERNAME")
ENV_PASSWORD = os.getenv("PASSWORD")
ENV_LOCALPATH = os.getenv("LOCALPATH")
ENV_REMOTEPATH = os.getenv("REMOTEPATH")
ENV_LOCAL_DIR = os.getenv("LOCAL_DIR")
ENV_ARCHIVE_DIR = os.getenv("ARCHIVEPATH") 

pitaya_dict = {
    ENV_MASTERRP: 'Z:/',
    ENV_SLAVE1: 'Y:/',
    ENV_SLAVE2: 'X:/'
}


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.command = "cd /root/RedPitaya/G && ./test2" #command used to launch acquisition software on pitaya
        self.connections = [] #list of connected pitayas
        self.error_queue = queue.Queue() #queue for error messages
        self.selected_ips = [] #currently selected pitayas from checkboxes
        self.pipeline_lock = threading.Lock()
        self.pipeline_running = False
        self.pipeline_active_count = 0
        if not os.path.exists("Data"): #making sure Data folder exists on host
            os.makedirs("Data")
        
        self.status_line = StatusLine(self)
        self.presets = PresetManager()
        
        self.title("RedPitaya Signal Acquisition")
        self.geometry("700x720")
        self.resizable(True,True) #disabling resizing of the window
        self.minsize(700, 700)
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self.grid_rowconfigure(5, weight=1)
        self.grid_rowconfigure(6, weight=1)
        self.grid_rowconfigure(7, weight=1)

        self.status_line.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.checkboxes_frame = CheckBoxes(self, "Devices", ips=[ENV_MASTERRP, ENV_SLAVE1, ENV_SLAVE2]) #creating checkbox for each device (using checkboxes class)
        self.checkboxes_frame.grid(row=0, column=0,rowspan = 3, padx=10, pady=(10, 0), sticky="nsew")

        self.connect_button = ctk.CTkButton(self, text="Connect to Pitayas", command=self.start_connect_to_devices_thread) #creating connect button
        self.connect_button.grid(row=3, column=0,columnspan=2, padx=10, pady=10)

        self.preset_controls_frame = ctk.CTkFrame(self)
        self.preset_controls_frame.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="new")
        self.preset_controls_frame.grid_columnconfigure(0, weight=1)
        self.preset_controls_frame.grid_columnconfigure(1, weight=0)
        self.preset_controls_frame.grid_columnconfigure(2, weight=1)
        self.preset_controls_frame.grid_columnconfigure(3, weight=0)
        self.preset_controls_frame.grid_columnconfigure(4, weight=1)

        self._bottom_right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._bottom_right_frame.grid(row=7, column=1, sticky="se", padx=10, pady=10)

        self.xyplot_button = ctk.CTkButton(
            master=self._bottom_right_frame,
            text="xy - plot",
            width=80,
            height=28,
            command=self.run_xyplot
        )
        self.fft_button = ctk.CTkButton(
            master=self._bottom_right_frame,
            text="FFT",
            width=60,
            height=28,
            command=self.run_fft
        )

        self.xyplot_button.grid(row=0, column=0, padx=(10, 6))
        self.fft_button.grid(row=0, column=1, padx=(6, 0))


        preset_names = self.presets.names()
        preset_names.append("Create New Preset...")
        self.presets_box = ctk.CTkComboBox(
            master=self.preset_controls_frame,
            width=160,
            state="readonly",
            values=preset_names,
            command=lambda _: self._load_selected_preset()
        )
        self.presets_box.set("Select Preset")
        self.presets_box.grid(row=0, column=0, padx=(0, 5), pady=0, sticky="ew")

        self.save_preset_btn = ctk.CTkButton(
            master=self.preset_controls_frame,
            text="Save Preset",
            width=60,
            command=self.__save_current_preset
        )
        self.save_preset_btn.grid(row=0, column=2, padx=(0, 5), pady=0, sticky="ew")

        self.delete_preset_btn = ctk.CTkButton(
            master=self.preset_controls_frame,
            text="Delete Preset",
            width=60,
            command=self.__delete_current_preset
        )
        self.delete_preset_btn.grid(row=0, column=4, padx=10, pady=0, sticky="ew")

        # --- PARAMETERS (InputBoxes) ---
        self.inputboxes_frame = InputBoxes(self, "Parameters", labels=['Decimation', 'Buffer size', 'Delay', 'Loops','Time','Trigger Source'], status_line=self.status_line)
        self.inputboxes_frame.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="nsew")

        self.acquire_button = ctk.CTkButton(self, text="Acquire Signals", command=self.initiate_acquisition) #creating acquire button
        self.acquire_button.grid(row=4, column=0, columnspan=2, padx=20, pady=10)
        self.acquire_button.configure(state="disabled")

        self.transfer_button = ctk.CTkButton(self, text="Transfer Data", command=self.transfer_files) #creating transfer button
        self.transfer_button.grid(row=5, column=0, padx=10,columnspan=2, pady=0)
        self.transfer_button.configure(state="disabled")

        self.merge_files_button = ctk.CTkButton(self,text = "Manually Merge Files", command=self.on_merge_button_click)
        self.merge_files_button.grid(row=6, column=0, padx=20, pady=20,columnspan=2)
        #self.merge_files_button.configure(state="disabled")

        # Option: open merged file in Explorer after merge (moved into switches area below)

        self.stop_button = ctk.CTkButton(self, text="STOP", command=self.stop_acquisition,fg_color = '#cc7000',hover_color='#cc8900') #creating stop button
        self.stop_button.grid(row=2, column=1,columnspan=2, padx=10, pady=10,sticky="nsew")
        self.stop_button.grid_remove()

        self.abort_button = ctk.CTkButton(self, text="ABORT", command=self.abort_acquisition,fg_color = '#cc0000',hover_color='#cc1111') #creating abort button
        self.abort_button.grid(row=3, column=1,columnspan=2, padx=10, pady=10,sticky="nsew")
        self.abort_button.grid_remove()

        self.isLocal = ctk.StringVar(value=0)
        self.switch_local_frame = ctk.CTkFrame(self)
        self.switch_local_frame.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.switch_local = ctk.CTkSwitch(self.switch_local_frame, text="Local Acquisition",command= lambda:self.get_Switch_bool(self.isLocal), variable=self.isLocal, onvalue=1, offvalue=0)
        self.switch_local.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.isMerge = ctk.StringVar(value=0)
        self.switch_merge = ctk.CTkSwitch(self.switch_local_frame, text="Automatically merge BIN Files",command = lambda:self.get_Switch_bool(self.isMerge), variable=self.isMerge, onvalue=1, offvalue=0)
        self.switch_merge.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        #self.switch_merge.grid_remove()

        self.isLoops = ctk.StringVar(value=0)
        self.switch_loops = ctk.CTkSwitch(self.switch_local_frame, text="Loops parameter",command = lambda:self.loops_switch_toggled(), variable=self.isLoops, onvalue=1, offvalue=0)
        self.switch_loops.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.switch_loops.grid_remove()

        self.isStreaming = ctk.StringVar(value=0)
        self.switch_streaming = ctk.CTkSwitch(self.switch_local_frame, text="Streaming mode",command = lambda:self.get_Switch_bool(self.isStreaming), variable=self.isStreaming, onvalue=1, offvalue=0)
        self.switch_streaming.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        #self.switch_streaming.grid_remove()

        self.send_config_button = ctk.CTkButton(self, text="Send config",command=lambda: self.save_streaming_config())
        self.send_config_button.grid(row=4,rowspan=1, column=0,columnspan=2, padx=10, pady=10)
        self.send_config_button.grid_remove()

        self.start_server_button = ctk.CTkButton(self, text="Start Streaming Server",command=lambda: self.start_streaming_mode())
        self.start_server_button.grid(row=3,rowspan=1, column=0,columnspan=2, padx=10, pady=10)
        self.start_server_button.grid_remove()

        # Open merged file switch (placed with other switches)
        self.open_merged = ctk.StringVar(value=0)
        self.switch_open_merged = ctk.CTkSwitch(self.switch_local_frame, text="Open acquisition folder after merge", command=lambda: self.get_Switch_bool(self.open_merged, "Open merged file"), variable=self.open_merged, onvalue=1, offvalue=0)
        self.switch_open_merged.grid(row=4, column=0, padx=10, pady=2, sticky="w")

        self.check_errors() #constantly checking for errors in queue
        self.check_new_checked_boxes() #constantly checking for new checked boxes
        self.check_transfer_button() #if remote has BIN/CSV files then enable transfer button
        self.check_files_to_merge()
        self.bind("<Return>", lambda event:self.initiate_acquisition())
        #self.acquire_button.configure(state="normal")
        tooltips = {
            self.checkboxes_frame: "Device list. Select devices to connect to and run acquisition on.",
            self.connect_button: "Establish SSH connections with the selected devices.",
            self.presets_box: "Select a preset. Use 'Create New Preset...' to make a new one.",
            self.save_preset_btn: "Save current acquisition settings as a preset (may overwrite).",
            self.delete_preset_btn: "Delete the currently selected preset.",
            self.inputboxes_frame: "Acquisition parameters: Decimation, Buffer size, Delay, Loops, Time.",
            self.acquire_button: "Start acquisition on all connected devices.",
            self.transfer_button: "Download BIN files from devices to Data folder",
            self.merge_files_button: "Groupes and merges all available .bin files in Data folder.",
            self.stop_button: "STOPS acquisition and saves current data",
            self.abort_button: "ABORTS acquisition and deletes data",
            self.switch_local: "If enabled, acquisition files automatically saved in Data folder",
            self.switch_merge: "If enabled, automatically merge BIN files after acquisition.",
            self.switch_open_merged: "If enabled, open the merged file folder after merging.",
            self.xyplot_button: "Open `xyplot.py` with the latest merged file.",
            self.fft_button: "Open `fft.py` with the latest merged file.",
        }
        param_short = {
            "Decimation": "Decimation: choose sampling rate",
            "Buffer size": "Buffer size: number of samples captured per loop.",
            "Delay": "Delay: pause before acquisition",
            "Loops": "Loops: how many buffers to acquire",
            "Time": "Time: target acquisition time (s).",
            "Trigger Source": "Trigger Source: source of trigger for acquisition"
        }

        param_long = {
            "Decimation": "Decimation: in RedPitaya, decimation is the division factor of the max sampling rate ",
            "Buffer size": "Buffer size: number of samples in RedPitaya buffer. Max is 16384.",
            "Delay": "Delay: delay before starting acquisition",
            "Loops": "Loops: Number of buffers to be acquired, total samples = Buffer size * Loops",
            "Time": "Time: Target acquisition time, total time of the process might be different",
            "Trigger Source": "Now (immediate - no sync), CHA - CH1, CHB - CH2, PE - positive edge, NE - negative edge"
        }
        attach_tooltips(tooltips)
        try:
            widgets = self.inputboxes_frame.inputs
            param_tooltips = {}
            for key, text in param_short.items():
                w = widgets.get(key)
                if w:
                    param_tooltips[w] = text
            attach_tooltips(param_tooltips)

            # dodatkowo: pokaż dłuższy opis w StatusLine przy najechaniu
            for key, long_text in param_long.items():
                w = widgets.get(key)
                if w:
                    # używaj domyślnych argumentów w lambda, żeby nie złapać zmiennej pętli
                    w.bind("<Enter>", lambda e, t=long_text: self.status_line.update_status(t))
                    w.bind("<Leave>", lambda e: self.status_line.update_status(""))
        except Exception:
        # bezpieczne pominięcie, jeśli struktura InputBoxes się zmieni
            pass


    def on_preset_selected(self, _value: str):
        name = self.presets_box.get()
        presets = presets.load_all()
        if name in presets:
            self.inputboxes_frame.set(presets[name])

    def save_preset(self):
        name = ctk.CTkInputDialog(text="Nazwa presetu").get_input()
        if not name: return
        self.presets.save_preset(name, self.inputboxes_frame.get())
        self.presets_box.configure(values=list(self.presets.load_all().keys()))
        self.status_line.update_status(f"Preset '{name}' zapisany")

    def delete_preset(self):
        name = self.presets_box.get()
        self.presets.delete_preset(name)
        self.presets_box.configure(values=list(self.presets.load_all().keys()))
        self.presets_box.set("")

    def save_streaming_config(self):
        config_path = Path("streaming_mode/config.json")
        # Load existing config or create new structure
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception as e:
                self.status_line.update_status(f"Failed to load config.json: {e}")
                config = {}
        else:
            config = {}

        # Get current streaming parameters from InputBoxes
        params = self.inputboxes_frame.get_streaming_params()

        # Convert numeric fields if needed (adc_decimation should be int)
        if "adc_decimation" in params:
            try:
                params["adc_decimation"] = int(params["adc_decimation"])
            except Exception:
                pass

        # Update or create 'adc_streaming' section
        config["adc_streaming"] = config.get("adc_streaming", {})
        config["adc_streaming"].update(params)

        # Save back to config.json
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
                self.status_line.update_status("Streaming config saved.")
        except Exception as e:
            self.status_line.update_status(f"Failed to save config.json: {e}")



    def get_Switch_bool(self, switch_var, name: str = None):
        bool_value = bool(int(switch_var.get()))
        
        if name is None:
            if switch_var is self.isLocal:
                name = "Local Acquisition"
                if bool_value:
                    self.transfer_button.grid_remove()
                    self.transfer_button.configure(state="disabled")
                else:
                    self.transfer_button.grid()
                    self.transfer_button.configure(state="normal")
            elif switch_var is self.isMerge:
                name = "Merge BIN Files"
                if bool_value:
                    pass
                    #self.merge_files_button.grid_remove()
                    #self.merge_files_button.configure(state="disabled")
                else:
                    self.merge_files_button.grid()
                    self.merge_files_button.configure(state="normal")
            elif switch_var is self.isLoops:
                name = "Loops"
            elif switch_var is self.isStreaming:
                name = "Streaming mode"
                if bool_value:
                    # entering streaming view
                    self.clear_grid_for_streaming()
                    self.start_server_button.grid()
                else:
                    # leaving streaming view -> hard restart app
                    self.after(0, self.restart_app)
            else:
                name = "Switch"
        print(f"{name}: {bool_value}")

        if switch_var is self.isLoops:
            if bool_value:
                self.inputboxes_frame.hide_input("Loops")
            else:
                self.inputboxes_frame.show_input("Loops")
        return bool_value

    
    def loops_switch_toggled(self):
        bool_value = self.isLoops.get()
        bool_value = bool(int(bool_value))
        print(f"Loops switch toggled: {bool_value}")
        # Check if the switch_loops is toggled
        if bool_value:
            self.inputboxes_frame.hide_input("Loops")
        else:
            self.inputboxes_frame.show_input("Loops")

    def start_streaming_mode(self):
        for connection in self.connections:
            threading.Thread(target=self.streaming_worker, args=(connection,), daemon=True).start()
            
            
    def streaming_worker(self,connection):
        try:
                    # Step 1: overlay.sh stream_app
            self.status_line.update_status(f"{connection.ip}: Running overlay.sh stream_app...")
            stdout, stderr = connection.execute_command("echo TEST && /opt/redpitaya/sbin/overlay.sh stream_app")
            connection.start_listener()
                    # Wait for overlay to finish (optional: check output or just sleep briefly)
            time.sleep(1)
                    # Step 2: streaming-server
            self.status_line.update_status(f"{connection.ip}: Starting streaming-server...")
            stdout, stderr = connection.execute_command("/opt/redpitaya/bin/streaming-server")
            connection.start_listener()
            self.status_line.update_status(f"{connection.ip}: Streaming server started.")
            self.start_server_button.grid_remove()
        except Exception as e:
            err = f"Streaming mode failed for {connection.ip}: {e}"
            print(err)
            self.error_queue.put(err)


        

    def show_acquisition_view(self): #showing acquisition view
        self.connect_button.grid_remove()
        self.acquire_button.grid_remove()
        self.transfer_button.grid_remove()
        self.switch_local_frame.grid_remove()
        self.switch_merge.grid_remove()
        self.merge_files_button.grid_remove()
        self.stop_button.grid()
        self.abort_button.grid()
    
    def reset_view(self):
        # legacy: keep for compatibility; delegate to restart
        self.restart_app()

    def restart_app(self):
        """Spawn a fresh instance of this script and close the current window."""
        try:
            # Launch new process
            script_path = Path(__file__).resolve()
            python_exe = sys.executable
            subprocess.Popen([python_exe, str(script_path)])
        except Exception as e:
            # If spawning fails, just log and try to restore main view
            try:
                self.status_line.update_status(f"Restart failed: {e}")
            except Exception:
                pass
            try:
                self.show_main_view()
            except Exception:
                pass
            return
        # Close current app
        try:
            self.destroy()
        except Exception:
            os._exit(0)

    def show_main_view(self): #showing main view
        self.stop_button.grid_remove()
        self.abort_button.grid_remove()
        self.connect_button.grid()
        self.acquire_button.grid()
        self.transfer_button.grid()
        self.switch_local_frame.grid()
        self.switch_merge.grid()
        self.merge_files_button.grid()

    def clear_grid_for_streaming(self):
        self.connect_button.grid_remove()
        self.acquire_button.grid_remove()
        self.transfer_button.grid_remove()
        self.switch_local.grid_remove()
        self.switch_open_merged.grid_remove()
        self.switch_merge.grid_remove()
        self.merge_files_button.grid_remove()
        self.stop_button.grid_remove()
        self.abort_button.grid_remove()
        self.checkboxes_frame.grid(row=0, column=0, rowspan=1, padx=10, pady=(10, 10), sticky="nsew")
        self.xyplot_button.grid_remove()
        self.fft_button.grid_remove()
        self.preset_controls_frame.grid_remove()
        self.inputboxes_frame.grid(row=0, column=1, padx=10, pady=(10, 10), sticky="nsew")
        self.inputboxes_frame.create_streaming_view()
        self.send_config_button.grid()
    
    def check_new_checked_boxes(self): #checking if new checkboxes are checked, if so and not connected already enable connect button
        selected_ips = self.checkboxes_frame.get()
        if selected_ips != self.selected_ips:
            self.selected_ips = selected_ips
            self.connect_button.configure(state="normal")
            #add functionality that checks for suddenly disconnected devices
        elif len(self.selected_ips) == len(self.connections):
            self.connect_button.configure(state="disabled")

        self.after(100, self.check_new_checked_boxes)

    def check_transfer_button(self):
        for connection in self.connections:
            remote_files = connection.list_files(ENV_REMOTEPATH)
            csv_files = [file for file in remote_files if file.endswith('.csv') or file.endswith('.bin')]
            if len(csv_files) != 0:
                self.transfer_button.configure(state="normal")
            else:
                self.transfer_button.configure(state="disabled")

    def check_files_to_merge(self):
        data_files = [file for file in os.listdir(ENV_LOCALPATH) if file.endswith('.csv') or file.endswith('.bin')]
        if len(data_files) != 0:
            self.merge_files_button.configure(state="normal")
        else:
            self.merge_files_button.configure(state="disabled")
        self.after(1000, self.check_files_to_merge)
    

    def check_errors(self):
        try:
            error_message = self.error_queue.get_nowait() #checking if there is any error in queue
        except queue.Empty:
            pass
        else:
            self.show_error(error_message) #if there is show error message using tkinter messagebox
        self.after(100, self.check_errors)
    
    # def get_Switch_bool(self,switch_var):
    #     bool_value = switch_var.get()
    #     bool_value = bool(int(bool_value))
    #     print(f"{switch_var}:{bool_value}")
    #     return bool_value


    def show_error(self,error_text): #simple method to pop up tkinter messagebox with error message
        tkinter.messagebox.showerror("Error",error_text)

    def initiate_acquisition(self): #method to open progress window and start acquisition on pitaya
        # Debounce: if external guard PY_VAR6 is set and a pipeline is already running, skip
        if self.pipeline_running:
           self.status_line.update_status("Pipeline already running")
           return

        self.show_acquisition_view()
        self.progress_window = ProgressWindow(self)
        self.progress_window.focus_set()
        self.progress_window.attributes('-topmost', True) #forcing window to stay on top
        self.acquire_button.configure(state="disabled")
        self.start_acquisition_thread() #starting acquisition in separate thread

    def start_connect_to_devices_thread(self): #starting connection to pitayas in separate thread to stop gui from freezing
        self.connect_button.configure(state="disabled")
        threading.Thread(target=self.connect_to_devices).start()
        
    def connect_to_devices(self): #connecting to pitayas checked in checkboxes
        self.selected_ips = self.checkboxes_frame.get()
        with ThreadPoolExecutor(max_workers=len(self.selected_ips)) as executor: #limiting number of threads to number of selected pitayas
            for ip in self.selected_ips: #if ip already in connections list then skip
                if ip not in [connection.ip for connection in self.connections]:
                    executor.submit(self.connect_to_device, ip)
        self.check_transfer_button()#checking for data files upon connecting

    def connect_to_device(self, ip): #connecting to pitaya
        try:
            rp = ConnectionManager.ConnectionManager(self, ip, 'root', 'root')
            if rp.connect() and rp.client is not None:
                self.connections.append(rp)
                output = rp.execute_command(f"echo 'Connected to {ip}'")
                self.checkboxes_frame.update_label(ip, "Connected")
                self.checkboxes_frame.show_disconnect_button(ip)
                self.acquire_button.configure(state="normal")
                self.switch_streaming.grid()
            else:
                raise Exception(f"Failed to connect to {ip}")
        except Exception as e:
            self.error_queue.put(str(e) + f" {ip}")
            self.checkboxes_frame.update_label(ip, "Failed to connect")
            self.connect_button.configure(state="normal")

    def start_acquisition_thread(self):
        threading.Thread(target=self.start_acquisition, args=(self.command,), daemon=True).start() #starting acquisition in separate thread

    def start_acquisition(self, command):
        # Mark pipeline as running and set active count
        with self.pipeline_lock:
            self.pipeline_running = True
            self.pipeline_active_count = len(self.connections) if self.connections else 0

                        # sync device clock to host time with second precision
        # Set every device clock to current host epoch seconds (date -s '@<sec>') at acquisition start
        try:
            ts = int(time.time())
            for conn in self.connections:
                try:
                    conn.execute_command(f"date -s '@{ts}'")
                except Exception as e:
                    # non-fatal; report to error queue for visibility
                    self.error_queue.put(f"Time sync failed for {conn.ip}: {e}")
        except Exception as e:
            self.error_queue.put(f"Time sync scheduling failed: {e}")
        # Clear contents of files in local logs folder at acquisition start
        try:
            logs_dir = Path("logs")
            import shutil
            if not logs_dir.exists():
                logs_dir.mkdir(parents=True, exist_ok=True)

            if logs_dir.exists() and logs_dir.is_dir():
                for p in logs_dir.iterdir():
                    try:
                        if p.is_file() or p.is_symlink():
                            # truncate file contents but keep the file entry
                            try:
                                with open(p, 'w'):
                                    pass
                            except Exception as e:
                                self.error_queue.put(f"Failed to truncate log file {p}: {e}")
                        elif p.is_dir():
                            # clear directory contents but keep the directory itself
                            for sub in p.iterdir():
                                try:
                                    if sub.is_file() or sub.is_symlink():
                                        sub.unlink()
                                    elif sub.is_dir():
                                        shutil.rmtree(sub)
                                except Exception as e:
                                    self.error_queue.put(f"Failed to remove log entry {sub}: {e}")
                    except Exception as e:
                        # non-fatal; report and continue
                        self.error_queue.put(f"Failed while processing log entry {p}: {e}")
        except Exception as e:
            self.error_queue.put(f"Failed to clear logs folder: {e}")

        self.status_line.start_timer()
        for connection in self.connections:
            threading.Thread(target=self.run_acquisition, args=(connection, command), daemon=True).start()


    def run_acquisition(self, connection, command): #running acquisition on pitaya
        self.acquire_button.configure(state="normal")
        # Execute acquisition command (select binary based on Decimation)
        try:
            params = self.inputboxes_frame.get()
            print(f"Parameters received: {params}")
            required_params = ["Decimation", "Buffer size", "Delay", "Loops","Trigger Source"]
            for param in required_params:
                if param not in params:
                    raise KeyError(f"Missing parameter: {param}")
            param_str = ' '.join([str(params[param]) for param in required_params])
            isLocal_str = str(self.get_Switch_bool(self.isLocal))

            # choose binary: use high_dec2 if Decimation < 64
            binary = "./test2"
            try:
                dec = params.get("Decimation")
                if dec is not None:
                    dec_val = int(float(dec))
                    if dec_val <= 256:
                        binary = "./test3_trig"
            except Exception:
                # if parsing fails, stick to default binary
               pass

            # build and execute remote command
            # if 'command' already contains cd && binary, override binary part to be safe
            # prefer explicit cd and chosen binary
            full_command = f"cd /root/RedPitaya/G && {binary} {param_str} {isLocal_str}"
            print(f"Executing command on {connection.ip}: {full_command}")
            stdout, stderr = connection.execute_command(full_command)
            connection.start_listener()
        except Exception as e:
            e_msg = f"{connection}: {str(e)}"
            print(e_msg)
            self.error_queue.put(e_msg)

        # Post-acquisition work (transfer/merge) — run best-effort and log errors to queue
        try:
            self.check_transfer_button()
            connection.merge_csv_files(False,
                                       self.get_Switch_bool(self.isLocal),
                                       ENV_LOCALPATH, ENV_ARCHIVE_DIR,
                                       [pitaya_dict.get(connection.ip)])
        except Exception as e:
            err = f"Post-acquisition error for {connection.ip}: {e}"
            print(err)
            self.error_queue.put(err)

        # Decrement active counter and only perform UI cleanup when last thread finishes
        last = False
        with self.pipeline_lock:
            self.pipeline_active_count = max(0, (self.pipeline_active_count or 0) - 1)
            if self.pipeline_active_count <= 0:
                self.pipeline_running = False
                last = True

        if last:
            # schedule UI updates on the main thread
            def finish_ui():
                try:
                    if getattr(self, "progress_window", None):
                        try:
                            self.progress_window.close()
                        except Exception:
                            pass
                    try:
                        self.status_line.stop_timer()
                    except Exception:
                        pass
                    self.after(1000, lambda: self.status_line.update_status("Merging completed"))
                    self.show_main_view()
                except Exception as e:
                    print("Error finishing UI:", e)

            if self.get_Switch_bool(self.isMerge):
                # if merging is enabled, do it before finishing UI
                try:
                    self.on_merge_button_click()
                except Exception as e:
                    self.error_queue.put(f"Error during merging: {e}")
                    self.after(0, finish_ui)

            self.after(0, finish_ui)


    def stop_acquisition(self): #stopping acquisition on pitaya
        for connection in self.connections:
            connection.execute_command("echo 'STOP' > /tmp/acq_control.txt") #sending stop command to pitaya
        self.show_main_view()

    def abort_acquisition(self): #aborting acquisition on pitaya
        for connection in self.connections:
            connection.execute_command("echo 'ABORT' > /tmp/acq_control.txt")
        self.show_main_view()

    def transfer_files(self):
        for connection in self.connections:
            files_to_transfer = connection.transfer_all_csv_files(ENV_REMOTEPATH, ENV_LOCALPATH,self.get_Switch_bool(self.isMerge)) # transferring files from pitaya to local machine
            if files_to_transfer is None:
                self.status_line.update_status("No files to transfer")
                continue
            for file in files_to_transfer:
                self.status_line.show_transfer_status(file)  # Show transfer status
                connection.transfer_file(file, ENV_LOCALPATH) #merging csv files after acquisition
        self.status_line.update_status("File transfer completed")

    def disconnect_from_device(self, ip): #disconnecting from pitaya with disconnect button
        for connection in self.connections:
            if connection.ip == ip:
                connection.disconnect() 
                self.connections.remove(connection)#removing connection from connections list
                self.checkboxes_frame.update_label(ip, "Disconnected")#updating label in checkboxes
                self.checkboxes_frame.hide_disconnect_button(ip)#hiding disconnect button
                self.connect_button.configure(state="normal")#enabling connect button
                break

    def destroy(self): #disconnect from all pitayas before closing the app
        for connection in self.connections:
            connection.disconnect()
        super().destroy()

    def _load_selected_preset(self):
        name = self.presets_box.get()
        if name == "Create New Preset...":
            from tkinter.simpledialog import askstring
            new_name = askstring("Create Preset", "Enter new preset name:")
            if new_name:
                self.presets.save(new_name, self.inputboxes_frame.get())
                preset_names = self.presets.names()
                preset_names.append("Create New Preset...")
                self.presets_box.configure(values=preset_names)
                self.presets_box.set(new_name)
                self.status_line.update_status(f"Preset '{new_name}' created")
        elif name and name != "Select Preset":
            params = self.presets.load(name)
            if params:
                self.inputboxes_frame.set(params)
                self.status_line.update_status(f"Preset '{name}' loaded")
            else:
                self.status_line.update_status(f"Preset '{name}' not found")

    def __save_current_preset(self):
        name = self.presets_box.get()
        if not name or name in ["Select Preset", "Create New Preset..."]:
            self.status_line.update_status("Select a preset to overwrite or use 'Create New Preset...'")
            return
        self.presets.save(name, self.inputboxes_frame.get())
        self.status_line.update_status(f"Preset '{name}' updated")

    def __delete_current_preset(self):
        name = self.presets_box.get()
        if not name or name == "Select Preset":
            self.status_line.update_status("No preset selected to delete")
            return
        if name in self.presets.names():
            del self.presets.data[name]
            self.presets.path.write_text(json.dumps(self.presets.data, indent=2))
            preset_names = self.presets.names()
            preset_names.append("Create New Preset...")
            self.presets_box.configure(values=preset_names)
            self.presets_box.set("Select Preset")
            self.status_line.update_status(f"Preset '{name}' deleted")
        else:
            self.status_line.update_status(f"Preset '{name}' not found")

    def on_merge_button_click(self):
        try:
            for file in os.listdir(ENV_LOCALPATH):
                if file.endswith('.bin'):
                    try:
                        with open(os.path.join(ENV_LOCALPATH, file), 'rb') as f:
                            pass
                    except PermissionError:
                        self.status_line.update_status(f"Cannot access {file} - file is in use")
                        return
            
            merge_bin_files()
            self.status_line.update_status("Files merged successfully")

            # # Verify merged file against logs' footers
            # try:
            #     verify_result = self.verify_merged_against_logs()
            #     if verify_result is not None:
            #         ok, details = verify_result
            #         if ok:
            #             self.status_line.update_status("Verification OK: merged file matches logs")
            #         else:
            #             self.status_line.update_status(f"Verification FAILED: {details}")
            # except Exception as e:
            #     self.error_queue.put(f"Verification failed: {e}")

            # Optionally open the most recently created merged BIN in file explorer
            try:
                if self.get_Switch_bool(self.open_merged, "Open merged file"):
                    merged_dir = Path("Merged")
                    if merged_dir.exists():
                        bin_files = [p for p in merged_dir.glob("*.bin") if p.is_file()]
                        if bin_files:
                            latest = max(bin_files, key=lambda p: p.stat().st_mtime)
                            # Use explorer to select the file on Windows
                            try:
                                subprocess.run(["explorer", "/select,", str(latest)])
                            except Exception:
                                # Fallback: open the folder
                                subprocess.run(["explorer", str(merged_dir)])
                        else:
                            self.status_line.update_status("No merged BIN files found to open")
                    else:
                        self.status_line.update_status("Merged directory not found")
            except Exception as e:
                print(f"Failed to open merged file: {e}")

            self.merge_files_button.configure(state="disabled")
            
        except PermissionError as pe:
            self.status_line.update_status("Error accessing files")
        except Exception as e:
            self.status_line.update_status(f"Error merging files: {str(e)}")
            print(f"Error: {e}")  # For debugging
    
    def _spawn_script(self, script_path: Path, args: list):
            python_exe = sys.executable
            cmd = [python_exe, str(script_path)] + args
            try:
                subprocess.Popen(cmd)
                return True
            except Exception as e:
                self.status_line.update_status(f"Failed to launch: {e}")
                return False

    def run_xyplot(self):
        latest = self._find_latest_merged_file(extensions=(".bin", ".BIN"))
        if not latest:
            self.status_line.update_status("No merged .bin files found in 'Merged' directory")
            return
        script = Path(__file__).parent / "xyplot.py"
        if not script.exists():
            self.status_line.update_status("xyplot.py not found")
            return
        args = [str(latest)]
        launched = self._spawn_script(script, args)
        if launched:
            self.status_line.update_status(f"Opened xy-plot for {latest.name}")

    def run_fft(self):
        latest = self._find_latest_merged_file(extensions=(".bin", ".BIN"))
        if not latest:
            self.status_line.update_status("No merged .bin files found in 'Merged' directory")
            return
        script = Path(__file__).parent / "fft.py"
        if not script.exists():
            self.status_line.update_status("fft.py not found")
            return
        args = ["--binfile", str(latest), "--channel", "CH1"]

        # Auto-add --channels if filename contains "<N>ch" (e.g. "_6ch" or "6ch_...").
        m = re.search(r'_(\d+)ch(?=[._-]|$)|(\d+)ch', latest.name, re.IGNORECASE)
        if m:
            ch = m.group(1) or m.group(2)
            if ch:
                try:
                    args += ["--channels", str(int(ch))]
                except Exception:
                    pass
        launched = self._spawn_script(script, args)
        if launched:
            self.status_line.update_status(f"Opened FFT for {latest.name}")

    def _find_latest_merged_file(self, extensions=(".bin", ".BIN", ".csv", ".CSV")):
            merged_dir = Path("Merged")
            if not merged_dir.exists() or not merged_dir.is_dir():
                return None
            files = [f for f in merged_dir.iterdir() if f.suffix in extensions and f.is_file()]
            if not files:
                return None
            latest = max(files, key=lambda p: p.stat().st_mtime)
            return latest

    def verify_merged_against_logs(self, merged_path: Path = None):
        """Sum FOOTER expected sizes from files in `logs/` and compare with merged file size.

        Returns (True, details) if OK, (False, details) if mismatch, or None if no merged file.
        """
        try:
            if merged_path is None:
                merged_path = self._find_latest_merged_file(extensions=(".bin", ".BIN"))
            if merged_path is None:
                return None

            logs_dir = Path("logs")
            if not logs_dir.exists() or not logs_dir.is_dir():
                return (False, "logs/ directory missing")

            total_expected = 0
            files_parsed = 0
            channels_set = set()
            samples_set = []

            for p in sorted(logs_dir.iterdir()):
                if p.is_file():
                    try:
                        samples, channels, bps, expected = parse_footer(str(p))
                        total_expected += expected
                        files_parsed += 1
                        channels_set.add(channels)
                        samples_set.append(samples)
                    except Exception:
                        # skip files without FOOTER
                        continue

            if files_parsed == 0:
                return (False, "no FOOTER entries found in logs/")

            actual_size = merged_path.stat().st_size
            if actual_size == total_expected:
                details = f"files={files_parsed}, expected={total_expected}, actual={actual_size}"
                return (True, details)
            else:
                details = f"files={files_parsed}, sum_expected={total_expected}, merged_actual={actual_size}"
                return (False, details)
        except Exception as e:
            return (False, f"exception: {e}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
