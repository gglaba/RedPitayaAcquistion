from logging import config
import sys
from tkinter import *
import tkinter
from tkinter import dialog
import customtkinter as ctk
import os
import threading
import subprocess
from pathlib import Path
import queue
import psutil
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import ConnectionManager
from CheckBoxes import CheckBoxes
from InputBoxes import InputBoxes
from StatusLine import StatusLine
import json
import re
import threading
import time
from GUI_helper import ToolTip, attach_tooltips
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
STREAMINGKEY = os.getenv("STREAMINGKEY")
STOPKEY = os.getenv("STOPKEY")

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
        self.selected_ips = [] #currently selected pitayas from checkboxes
        self.error_queue = queue.Queue() #queue for error messages'
        self.selected_ips = [] #currently selected pitayas from checkboxes
        self.streaming_ips = [] #list of pitayas in streaming mode
        self.streaming_time = 1.0
        self._streaming_key_last_time = 0  # For debounce
        self._streaming_key_debounce_ms = 500 
        self.start_streaming_key = STREAMINGKEY
        self.stop_streaming_key = STOPKEY
        self.pipeline_lock = threading.Lock()
        self.streaming_process = None
        self.pipeline_running = False
        self.pipeline_active_count = 0
        if not os.path.exists("Data"): #making sure Data folder exists on host
            os.makedirs("Data")
        
        self.status_line = StatusLine(self)
        self.title("RedPitaya Signal Acquisition")
        self.geometry("750x850")
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
        self.switch_local_frame = ctk.CTkFrame(self)
        self.switch_local_frame.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.isStatic = ctk.IntVar(value=0)
        self.isStaticIP_switch = ctk.CTkSwitch(self.switch_local_frame, text="Static IPs mode", command=self.isStaticIP_switch_toggled, variable=self.isStatic, onvalue=1, offvalue=0)
        self.isStaticIP_switch.grid(row=7, column=0, padx=10, pady=10, sticky="w")
        self.checkboxes_frame = CheckBoxes(self, "Devices", ips=[ENV_MASTERRP, ENV_SLAVE1, ENV_SLAVE2]) #creating checkbox for each device (using checkboxes class)
        self.checkboxes_frame.grid(row=0, column=0,rowspan = 3, padx=10, pady=(10, 0), sticky="nsew")
        self.checkboxes_frame.master.on_connect_all = self.connect_all_devices
        self.connect_button = ctk.CTkButton(self.checkboxes_frame, text="Connect to Pitayas", command=self.start_connect_to_devices_thread) #creating connect button
        self.connect_button.grid(row=6, column=0,columnspan=1, padx=10, pady=5,sticky="ew")

        self.assing_ips_button = ctk.CTkButton(self.switch_local_frame, text="Assign Static IPs", command=self.assign_static_ips)
        self.assing_ips_button.grid(row = 8,column=0,columnspan=1, padx=20, pady=10,sticky="ew")
        self.assing_ips_button.grid_remove()

        self.preset_controls_frame = ctk.CTkFrame(self)
        self.preset_controls_frame.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="new")
        self.preset_controls_frame.grid_columnconfigure(0, weight=1)
        self.preset_controls_frame.grid_columnconfigure(1, weight=0)
        self.preset_controls_frame.grid_columnconfigure(2, weight=1)
        self.preset_controls_frame.grid_columnconfigure(3, weight=0)
        self.preset_controls_frame.grid_columnconfigure(4, weight=1)

        self._bottom_right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._bottom_right_frame.grid(row=7, column=1, sticky="se", padx=10, pady=10)

        # Live Preview button for streaming mode
        self.live_preview_button = ctk.CTkButton(
            master=self._bottom_right_frame,
            text="Live Preview",
            width=100,
            height=28,
            command=self.run_live_preview
        )

        # Live Preview button is hidden by default
        self.live_preview_button.grid_remove()

        self.stop_streaming_button = ctk.CTkButton(self, text="STOP Streaming", command=self.stop_streaming,fg_color = '#cc7000',hover_color='#cc8900') #creating stop button
        self.stop_streaming_button.grid(row=5,rowspan=1, column=0,columnspan=2, padx=10, pady=10)
        self.stop_streaming_button.grid_remove()

        self.inputboxes_frame = InputBoxes(self, status_line=self.status_line)
        self.inputboxes_frame.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="nsew")

        self.send_config_button = ctk.CTkButton(self, text="Send config",command=lambda: self.save_streaming_config())
        self.send_config_button.grid(row=6,rowspan=1, column=0,columnspan=2, padx=10, pady=5)
        self.send_config_button.grid_remove()

        self.start_server_button = ctk.CTkButton(self, text="Start Streaming Server",command=lambda: self.start_streaming_mode())
        self.start_server_button.grid(row=3,rowspan=1, column=0,columnspan=2, padx=10, pady=5)
        self.start_server_button.configure(state="normal")

        self.start_streaming_button = ctk.CTkButton(self, text="Start Streaming Data",command=lambda: self.send_streaming_command())
        self.start_streaming_button.grid(row=4,rowspan=1, column=0,columnspan=2, padx=10, pady=10)
        self.start_streaming_button.grid_remove()

        self.fft_streaming_button = ctk.CTkButton(self, text="FFT Streaming Data",command=lambda: self.run_fft_streaming())
        self.fft_streaming_button.grid(row=1, column=1, padx=10, pady=10,sticky="e")
        self.fft_streaming_button.configure(state="normal")
        self.fft_streaming_button.grid_remove()


        self.edit_live_preview_btn = ctk.CTkButton(self.switch_local_frame, text="Edit Live Preview Config", command=self.open_live_preview_config_dialog, width=180)
        self.edit_live_preview_btn.grid(row=6, column=0, padx=20, pady=10, sticky="ew")

        self.help_button = ctk.CTkButton(
            master=self,
            text="?",
            width=32,
            height=32,
            fg_color="#444444",
            hover_color="#666666",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=self.show_streaming_help
        )
        self.check_errors() #constantly checking for errors in queue
        self.check_new_checked_boxes() #constantly checking for new checked boxes
        self.clear_grid_for_streaming()

        tooltips = {
        }
        param_short = {
            "data_type_sd": "Data type: choose between voltage or raw ADC values.",
            "format_sd": "File format: select BIN, WAV, or TDMS.",
            "resolution": "Resolution: 8 or 16 bit data.",
            "channel_state_1": "Channel 1: enable or disable.",
            "channel_state_2": "Channel 2: enable or disable.",
            "channel_attenuator_1": "Channel 1 attenuator: 1x or 20x.",
            "channel_attenuator_2": "Channel 2 attenuator: 1x or 20x.",
            "adc_decimation": "ADC decimation: sampling rate divider."
        }

        param_long = {
            "data_type_sd": "Data type: VOLT gives calibrated voltage values, RAW gives raw ADC counts.",
            "format_sd": "File format: BIN is binary, WAV is audio, TDMS is LabVIEW format.",
            "resolution": "Resolution: choose 8 or 16 bits per sample.",
            "channel_state_1": "Channel 1 state: ON enables acquisition, OFF disables.",
            "channel_state_2": "Channel 2 state: ON enables acquisition, OFF disables.",
            "channel_attenuator_1": "Channel 1 attenuator: A_1_1 is 1x, A_1_20 is 20x attenuation.",
            "channel_attenuator_2": "Channel 2 attenuator: A_1_1 is 1x, A_1_20 is 20x attenuation.",
            "adc_decimation": "ADC decimation: divides max sample rate (1=125MSa/s, 2=62.5MSa/s, etc).",
            "streaming_time" : "Duration of data streaming in seconds. If set to 0, streaming continues until manually stopped."
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
            for key, long_text in param_long.items():
                w = widgets.get(key)
                if w:
                    w.bind("<Enter>", lambda e, t=long_text: self.status_line.update_status(t))
                    w.bind("<Leave>", lambda e: self.status_line.update_status(""))
        except Exception:
            pass

    def open_live_preview_config_dialog(self):
        import json
        config_path = Path("live_preview_config.json")
        if not config_path.exists():
            tkinter.messagebox.showerror("Error", "live_preview_config.json not found.")
            return
        try:
            with config_path.open("r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            tkinter.messagebox.showerror("Error", f"Failed to load config: {e}")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title("Edit Live Preview Config")
        dialog.geometry("420x420")
        dialog.attributes('-topmost', True)

        entries = {}
        row = 0
        for key, value in config.items():
            if key == "CHANNELS":  # Skip displaying CHANNELS to the user
                continue
            ctk.CTkLabel(dialog, text=key + ":").grid(row=row, column=0, padx=10, pady=6, sticky="w")
            entry = ctk.CTkEntry(dialog, width=220)
            entry.insert(0, str(value))
            entry.grid(row=row, column=1, padx=10, pady=6, sticky="ew")
            entries[key] = entry
            row += 1

        def save_config():
            new_config = {}
            for k, e in entries.items():
                v = e.get()
                # Try to convert to int/float if original was numeric
                orig = config[k]
                if isinstance(orig, int):
                    try:
                        v = int(v)
                    except Exception:
                        pass
                elif isinstance(orig, float):
                    try:
                        v = float(v)
                    except Exception:
                        pass
                new_config[k] = v

            # Preserve the CHANNELS attribute in the saved config
            if "CHANNELS" in config:
                new_config["CHANNELS"] = config["CHANNELS"]

            try:
                with config_path.open("w", encoding="utf-8") as f:
                    json.dump(new_config, f, indent=4)
                tkinter.messagebox.showinfo("Success", "Config updated. Changes will take effect on next Live Preview launch.")
                dialog.destroy()
            except Exception as e:
                tkinter.messagebox.showerror("Error", f"Failed to save config: {e}")

        save_btn = ctk.CTkButton(dialog, text="Save", command=save_config, width=80)
        save_btn.grid(row=row, column=0, columnspan=2, pady=16)

    def bind_streaming_keys(self):
            try:
                self.unbind(f"<{self.start_streaming_key}>")
            except Exception:
                pass
            try:
                self.unbind(f"<{self.stop_streaming_key}>")
            except Exception:
                pass
            # Bind new keys with debounce wrappers
            if self.start_streaming_key:
                self.bind(f"<{self.start_streaming_key}>", self._debounced_start_streaming)
            if self.stop_streaming_key:
                self.bind(f"<{self.stop_streaming_key}>", self._debounced_stop_streaming)


    def _debounced_start_streaming(self, event=None):
        now = time.time()
        if now - getattr(self, "_streaming_key_last_time", 0) < self._streaming_key_debounce_ms / 1000.0:
            return  # Debounced
        self._streaming_key_last_time = now
        # Prevent running if already running
        if getattr(self, "streaming_process", None) is not None and self.streaming_process.poll() is None:
            self.status_line.update_status("Streaming is already running.")
            return
        self.send_streaming_command()

    def _debounced_stop_streaming(self, event=None):
        now = time.time()
        if now - getattr(self, "_streaming_key_last_time", 0) < self._streaming_key_debounce_ms / 1000.0:
            return  # Debounced
        self._streaming_key_last_time = now
        self.stop_streaming()

    def update_env_file(self, key, value):
        env_path = Path(__file__).parent / ".env"
        if not env_path.exists():
            return
        lines = env_path.read_text(encoding="utf-8").splitlines()
        pattern = re.compile(rf"^{re.escape(key)}\s*=\s*.*$", re.IGNORECASE)
        found = False
        for i, line in enumerate(lines):
            if pattern.match(line.strip()):
                lines[i] = f"{key} = '{value}'"
                found = True
                break
        if not found:
            lines.append(f"{key} = '{value}'")
        env_path.write_text("\n".join(lines), encoding="utf-8")


    def connect_all_devices(self):
        self.selected_ips = self.checkboxes_frame.get()
        self.start_connect_to_devices_thread()

    def save_streaming_config(self):
        self.streaming_time = int(self.inputboxes_frame.get_streaming_time())
        print(f"Streaming time set to: {self.streaming_time*1000} seconds")

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
                self.run_client_detect(True)
                print(self.streaming_ips)

        except Exception as e:
            self.status_line.update_status(f"Failed to save config.json: {e}")
        self.send_config_command(config_path)


    def send_streaming_command(self):
        if getattr(self, "streaming_process", None) is not None and self.streaming_process.poll() is None:
            self.status_line.update_status("Streaming is already running.")
            return
        #self.stop_streaming_button.configure(state="normal")
        self.streaming_time = self.inputboxes_frame.get_streaming_time()
        exe_path = "streaming_mode/rpsa_client.exe"
        params = self.inputboxes_frame.get_streaming_params()
        file_format = params["format_sd"]
        command = [
            exe_path,
            "-s",
            "-h", ",".join(self.streaming_ips),
            "-d", "./Data",
            "-f", file_format.lower(),
            "-v"
        ]
        if self.streaming_time and str(self.streaming_time).strip() not in ("", "0", "0.0"):
            command += ["-t", str(int(float(self.streaming_time) * 1000))]

        print(f"Running streaming command: {command} (cwd=streaming_mode)")

        def run():
            try:
                self.send_config_button.configure(state="disabled")
                self.start_streaming_button.configure(state="disabled")
                self.stop_streaming_button.grid()
                self.status_line.start_timer()  # Start timer using StatusLine
                self.streaming_timer_active = True
                self.streaming_process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                self.after(0, lambda: self.status_line.update_status("Data streaming started."))
                stdout, stderr = self.streaming_process.communicate()
                self.streaming_process = None
                self.status_line.stop_timer()  # Stop timer using StatusLine
                self.streaming_timer_active = False
                if self.streaming_process is None or self.streaming_process.returncode == 0:
                    self.after(0, lambda: self.status_line.update_status("Data streaming completed successfully."))
                    self.start_streaming_button.configure(state="normal")
                    self.send_config_button.configure(state="normal")
                else:
                    self.after(0, lambda: self.status_line.update_status(f"Data streaming error: {stderr or stdout}"))
                    self.start_streaming_button.configure(state="normal")
            except Exception as e:
                print(f"Exception in streaming thread: {e}")
                self.status_line.stop_timer()
                self.streaming_timer_active = False
                self.after(0, lambda e=e: self.status_line.update_status(f"Failed to run rpsa_client.exe: {e}"))

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

    def stop_streaming(self):
        self._streaming_key_last_time = 0
        killed = False
        try:
            for p in psutil.process_iter(['name']):
                if p.info['name'] and p.info['name'].lower() == 'rpsa_client.exe':
                    p.kill()
                    killed = True
            if killed:
                self.status_line.update_status("All rpsa_client.exe processes killed.")
            else:
                self.status_line.update_status("No rpsa_client.exe process running.")
        except Exception as e:
            self.status_line.update_status(f"Failed to kill rpsa_client.exe: {e}")
        self.status_line.stop_timer()  # Stop timer here
        self.streaming_timer_active = False
        self.stop_streaming_button.grid_remove()


    def send_config_command(self, config_path):
        exe_path = str(Path("streaming_mode") / "rpsa_client.exe")
        command = [
            exe_path,
            "-c",
            "-h", ",".join(self.streaming_ips),
            "-s", "F",
            "-f", str(config_path),
            "-v"
        ]

        def run_and_capture():
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                print(f"Running command: {command} (cwd=streaming_mode)")
                stdout, stderr = process.communicate(timeout=15)
                if process.returncode == 0:
                    self.status_line.update_status("Config sent successfully.")
                else:
                    self.status_line.update_status(f"Error sending config: {stderr or stdout}")
                return stdout
            except Exception as e:
                self.status_line.update_status(f"Failed to run rpsa_client.exe: {e}")
                return str(e)

        # Run in a background thread to avoid blocking the GUI
        thread = threading.Thread(target=run_and_capture, daemon=True)
        thread.start()

    def run_client_detect(self,detect=True):
        # Launch rpsa_client.exe with -d and capture output
        bool_value = self.isStatic.get()
        bool_value = bool(int(bool_value))
        print(f"Static IP switch toggled: {bool_value}")
        if detect:
            if(bool_value):
                return
            command = ["streaming_mode/rpsa_client.exe", "-d"]
        else:
            command = ["streaming_mode/rpsa_client.exe -c -h", ",".join(self.streaming_ips), "-s", "F", "-f", "/streaming_mode/config.json", "-v"]
            print(command)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
        except subprocess.CalledProcessError as e:
            output = e.stdout or e.stderr or str(e)
            return "", []

        if detect:
            # Find the last occurrence of "Found boards:" and extract everything after
            found_idx = output.rfind("Found boards:")
            if found_idx == -1:
                return "", []

            summary = output[found_idx:].strip()

            # Extract IPs using regex (matches IPv4 addresses)
            ips = re.findall(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", summary)
            self.streaming_ips = ips

            return summary, ips

    def run_terminal_command(self,command):
        os.system(f'{command}')
        return sys
    
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
        self.start_server_button.configure(state="disabled")
        bool_value = self.isStatic.get()
        bool_value = bool(int(bool_value))
        print(f"Static IP switch toggled: {bool_value}")
        if(bool_value):
            self.start_server_button.grid_remove()
            self.bind_streaming_keys()
            self.set_keys_btn.configure(state="normal")
            self.start_streaming_button.grid()
            self.send_config_button.grid()
        else:
            self.run_client_detect(True)
            if( len(self.streaming_ips) == 0):
                self.status_line.update_status("No streaming devices detected.")
                self.start_server_button.configure(state="normal")
                return
            else:
                self.start_server_button.grid_remove()
                self.bind_streaming_keys()
                self.set_keys_btn.configure(state="normal")
                self.start_streaming_button.grid()
                self.send_config_button.grid()
            
            
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
            connection.execute_command("echo TEST && /opt/redpitaya/bin/streaming-server -b -v")
            connection.start_listener()
            self.status_line.update_status(f"{connection.ip}: Streaming server started.")

        except Exception as e:
            err = f"Streaming mode failed for {connection.ip}: {e}"
            print(err)
            self.error_queue.put(err)


    def reset_view(self):
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
            for connection in self.connections:
                connection.execute_command("reboot")
            self.destroy()
        except Exception:
            os._exit(0)


    def clear_grid_for_streaming(self):
        self.checkboxes_frame.grid(row=0, column=0, rowspan=1, padx=10, pady=(10, 10), sticky="nsew")
        self.preset_controls_frame.grid_remove()
        self.inputboxes_frame.grid(row=0, column=1, padx=10, pady=(10, 10), sticky="nsew")
        self.live_preview_button.grid(row=0, column=0, padx=(10, 6))
        #self.fft_streaming_button.grid()
        self.help_button.grid(row=0, column=0, padx=10, pady=10, sticky="sw")
        self.set_keys_btn = ctk.CTkButton(self.switch_local_frame, text="Set Streaming Keys", command=self.open_streaming_keys_dialog, width=120)
        self.set_keys_btn.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        self.set_keys_btn.configure(state="normal")

    def open_streaming_keys_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Set Streaming Keys")
        dialog.geometry("350x200")
        dialog.attributes('-topmost', True)

        ctk.CTkLabel(dialog, text="Start streaming key:").grid(row=0, column=0, padx=10, pady=10)
        start_key_label = ctk.CTkLabel(dialog, text=self.start_streaming_key or "Not set", width=80)
        start_key_label.grid(row=0, column=1, padx=10, pady=10)
        set_start_btn = ctk.CTkButton(dialog, text="Set Start Key", width=100)
        set_start_btn.grid(row=0, column=2, padx=10, pady=10)

        ctk.CTkLabel(dialog, text="Stop streaming key:").grid(row=1, column=0, padx=10, pady=10)
        stop_key_label = ctk.CTkLabel(dialog, text=self.stop_streaming_key or "Not set", width=80)
        stop_key_label.grid(row=1, column=1, padx=10, pady=10)
        set_stop_btn = ctk.CTkButton(dialog, text="Set Stop Key", width=100)
        set_stop_btn.grid(row=1, column=2, padx=10, pady=10)

        info_label = ctk.CTkLabel(dialog, text="Click a button, then press any key to set.", text_color="#888888")
        info_label.grid(row=2, column=0, columnspan=3, pady=(0, 10))

        def capture_key(which):
            info_label.configure(text=f"Press any key for {'Start' if which == 'start' else 'Stop'}...")
            def on_key(event):
                key = event.keysym
                if which == "start":
                    start_key_label.configure(text=key)
                    dialog.unbind("<Key>")
                    dialog.focus_set()
                else:
                    stop_key_label.configure(text=key)
                    dialog.unbind("<Key>")
                    dialog.focus_set()
                info_label.configure(text="Click a button, then press any key to set.")
            dialog.bind("<Key>", on_key)
            dialog.focus_set()

        set_start_btn.configure(command=lambda: capture_key("start"))
        set_stop_btn.configure(command=lambda: capture_key("stop"))

        def save_keys():
            new_start = start_key_label.cget("text")
            new_stop = stop_key_label.cget("text")
            # Unbind old keys
            try: self.unbind(f"<{self.start_streaming_key}>")
            except Exception: pass
            try: self.unbind(f"<{self.stop_streaming_key}>")
            except Exception: pass
            # Set and bind new keys
            self.start_streaming_key = new_start
            self.stop_streaming_key = new_stop
            self.bind_streaming_keys()
            self.update_env_file("STREAMINGKEY", new_start)
            self.update_env_file("STOPKEY", new_stop)
            self.status_line.update_status(f"Streaming keys set: Start={new_start}, Stop={new_stop}")
            dialog.destroy()

        save_btn = ctk.CTkButton(dialog, text="Save", command=save_keys, width=80)
        save_btn.grid(row=3, column=0, columnspan=3, pady=10)

    def show_streaming_help(self):
        # Simple popup with streaming instructions
        help_win = ctk.CTkToplevel(self)
        help_win.title("Streaming Mode Instructions")
        help_win.geometry("620x440")
        help_win.attributes('-topmost', True)
        help_text = (
            "Streaming Mode Instructions:\n\n"
            "1. Click 'Start Streaming Server' to launch the server on all connected devices.\n\n"
            "2. Set your streaming parameters, you can also view all possible options in /streaming_mode/config.json file\n\n"
            "3. Click 'Send config' to send the configuration to all devices and get RedPitaya IP addresses.\n\n"
            "4. Click 'Start Streaming Data' to begin streaming to the Data folder.\n\n"
            "   - !IMPORTANT! If you set time parameter to 0, streaming will run continuously.\n\n"
            "   - Use the 'STOP Streaming' button to end streaming at any time. Stop Streaming button appears after streaming is launched.\n\n"
            "5. Use 'Live Preview' to view real-time signal for each channel of each device(optional).\n\n"
            "6. Streamed data files are saved in the Data folder.\n\n" \
            "7. You can also change the parameters of live preview to adjust it to your signal, by editing live_preview_config.json \n\n"
            "\n"
        )
        label = ctk.CTkLabel(help_win, text=help_text, justify="left", wraplength=500)
        label.pack(padx=20, pady=20)
        close_btn = ctk.CTkButton(help_win, text="Close", command=help_win.destroy)
        close_btn.pack(pady=(0, 20))

    def run_live_preview(self):
        params = self.inputboxes_frame.get_streaming_params() or {}
        file_format = params.get("format_sd", "tdms").lower()  # Default to "tdms" if not specified
        # Ensure there are streaming IPs
        if not self.streaming_ips:
            self.status_line.update_status("No streaming devices detected for Live Preview.")
            return

        exe_name = "live_preview.exe"
        script = Path(sys._MEIPASS) / exe_name if getattr(sys, "frozen", False) else Path(__file__).parent / exe_name

        if not script.exists():
            self.status_line.update_status(f"{exe_name} not found")
            return

        try:
            # Construct the command with file_format and individual IPs as separate arguments
            cmd = [str(script), file_format] + self.streaming_ips
            print(f"Launching {exe_name} with command: {cmd}")
            subprocess.Popen(cmd)
            self.status_line.update_status("Live Preview launched")
        except Exception as e:
            self.status_line.update_status(f"Failed to launch Live Preview: {e}")
            print(f"Failed to launch {exe_name}: {e}")
    
    def check_new_checked_boxes(self): #checking if new checkboxes are checked, if so and not connected already enable connect button
        selected_ips = self.checkboxes_frame.get()
        if selected_ips != self.selected_ips:
            self.selected_ips = selected_ips
            self.connect_button.configure(state="normal")
            #add functionality that checks for suddenly disconnected devices
        elif len(self.selected_ips) == len(self.connections):
            self.connect_button.configure(state="disabled")
        self.after(100, self.check_new_checked_boxes)

    def check_errors(self):
        try:
            error_message = self.error_queue.get_nowait() #checking if there is any error in queue
        except queue.Empty:
            pass
        else:
            self.show_error(error_message) #if there is show error message using tkinter messagebox
        if(len(self.connections)>=2):
            self.connect_button.grid_remove()
            self.checkboxes_frame.hide_connect_all_button()
        self.after(100, self.check_errors)

    def show_error(self,error_text): #simple method to pop up tkinter messagebox with error message
        tkinter.messagebox.showerror("Error",error_text)

    def start_connect_to_devices_thread(self): #starting connection to pitayas in separate thread to stop gui from freezing
        self.connect_button.configure(state="disabled")
        threading.Thread(target=self.connect_to_devices).start()
        
    def connect_to_devices(self): #connecting to pitayas checked in checkboxes
        self.selected_ips = self.checkboxes_frame.get()
        with ThreadPoolExecutor(max_workers=len(self.selected_ips)) as executor: #limiting number of threads to number of selected pitayas
            for ip in self.selected_ips: #if ip already in connections list then skip
                if ip not in [connection.ip for connection in self.connections]:
                    executor.submit(self.connect_to_device, ip)


    def connect_to_device(self, ip): #connecting to pitaya
        try:
            rp = ConnectionManager.ConnectionManager(self, ip, 'root', 'root')
            if rp.connect() and rp.client is not None:
                self.connections.append(rp)
                output = rp.execute_command(f"echo 'Connected to {ip}'")
                self.checkboxes_frame.update_label(ip, "Connected")
                self.checkboxes_frame.show_disconnect_button(ip)
                self.start_server_button.grid()
                self.start_server_button.configure(state="normal")
                # Run start_streaming_mode after successful connection
            else:
                raise Exception(f"Failed to connect to {ip}")
        except Exception as e:
            self.error_queue.put(str(e) + f" {ip}")
            self.checkboxes_frame.update_label(ip, "Failed to connect")
            self.connect_button.configure(state="normal")


    def disconnect_from_device(self, ip): #disconnecting from pitaya with disconnect button
        for connection in self.connections:
            if connection.ip == ip:
                connection.disconnect() 
                self.connections.remove(connection)#removing connection from connections list
                self.checkboxes_frame.update_label(ip, "Disconnected")#updating label in checkboxes
                self.checkboxes_frame.hide_disconnect_button(ip)#hiding disconnect button
                self.connect_button.grid()
                self.connect_button.configure(state="normal")#enabling connect button
                self.checkboxes_frame.show_connect_all_button()
                break

    def destroy(self): #disconnect from all pitayas before closing the app
        for connection in self.connections:
            connection.disconnect()
        super().destroy()

    
    def _spawn_script(self, script_path: Path, args: list):
            python_exe = sys.executable
            cmd = [python_exe, str(script_path)] + args
            try:
                subprocess.Popen(cmd)
                return True
            except Exception as e:
                self.status_line.update_status(f"Failed to launch: {e}")
                return False

    def isStaticIP_switch_toggled(self, isStatic=None):
        bool_value = self.isStatic.get()
        bool_value = bool(int(bool_value))
        print(f"Static IP switch toggled: {bool_value}")

        static_ips_path = Path("static_ips.json")

        if bool_value:  # Static IP mode enabled
            self.assing_ips_button.grid()
            print("Static IP mode enabled. Loading static IPs...")
            if static_ips_path.exists():
                try:
                    with static_ips_path.open("r", encoding="utf-8") as f:
                        static_ips = json.load(f)
                    # Set streaming_ips to the static IPs
                    self.streaming_ips = [
                        static_ips.get("master_rp", ""),
                        static_ips.get("slave1_rp", ""),
                        static_ips.get("slave2_rp", "")
                    ]
                    # Filter out empty IPs
                    self.streaming_ips = [ip for ip in self.streaming_ips if ip]
                    print(f"Streaming IPs set to: {self.streaming_ips}")
                    self.status_line.update_status("Static IPs loaded and set for streaming.")
                except Exception as e:
                    print(f"Failed to load static IPs: {e}")
                    self.status_line.update_status(f"Failed to load static IPs: {e}")
            else:
                print("static_ips.json not found.")
                self.status_line.update_status("static_ips.json not found.")
        else:  # Static IP mode disabled
            print("Static IP mode disabled.")
            self.assing_ips_button.grid_remove()
            self.streaming_ips = []  # Clear streaming IPs
            self.status_line.update_status("Static IP mode disabled. Streaming IPs cleared.")

    def assign_static_ips(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Set Static IPs")
        dialog.geometry("400x250")
        dialog.attributes('-topmost', True)

        # Load existing IPs from static_ips.json
        static_ips_path = Path("static_ips.json")
        if static_ips_path.exists():
            with static_ips_path.open("r", encoding="utf-8") as f:
                static_ips = json.load(f)
        else:
            static_ips = {"master_rp": "", "slave1_rp": "", "slave2_rp": ""}

        # Create input fields for each IP
        ctk.CTkLabel(dialog, text="Master Red Pitaya IP").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        master_ip_entry = ctk.CTkEntry(dialog, width=200)
        master_ip_entry.insert(0, static_ips.get("master_rp", ""))
        master_ip_entry.grid(row=0, column=1, padx=10, pady=10)

        ctk.CTkLabel(dialog, text="Slave 1 Red Pitaya IP").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        slave1_ip_entry = ctk.CTkEntry(dialog, width=200)
        slave1_ip_entry.insert(0, static_ips.get("slave1_rp", ""))
        slave1_ip_entry.grid(row=1, column=1, padx=10, pady=10)

        ctk.CTkLabel(dialog, text="Slave 2 Red Pitaya IP").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        slave2_ip_entry = ctk.CTkEntry(dialog, width=200)
        slave2_ip_entry.insert(0, static_ips.get("slave2_rp", ""))
        slave2_ip_entry.grid(row=2, column=1, padx=10, pady=10)

        # Save button to write the IPs to static_ips.json
        def save_static_ips():
            new_static_ips = {
                "master_rp": master_ip_entry.get().strip(),
                "slave1_rp": slave1_ip_entry.get().strip(),
                "slave2_rp": slave2_ip_entry.get().strip()
            }
            try:
                # Save the new IPs to static_ips.json
                with static_ips_path.open("w", encoding="utf-8") as f:
                    json.dump(new_static_ips, f, indent=4)

                # Update streaming_ips with the new values
                self.streaming_ips = [
                    new_static_ips.get("master_rp", ""),
                    new_static_ips.get("slave1_rp", ""),
                    new_static_ips.get("slave2_rp", "")
                ]
                # Filter out empty IPs
                self.streaming_ips = [ip for ip in self.streaming_ips if ip]

                print(f"Streaming IPs updated to: {self.streaming_ips}")
                self.status_line.update_status("Static IPs saved and updated for streaming.")
                dialog.destroy()
            except Exception as e:
                self.status_line.update_status(f"Failed to save static IPs: {e}")

        save_button = ctk.CTkButton(dialog, text="Save", command=save_static_ips, width=100)
        save_button.grid(row=3, column=0, columnspan=2, pady=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()
