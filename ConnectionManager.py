import paramiko
import os
from paramiko import SSHClient, AutoAddPolicy
import threading
from scp import SCPClient
import select
import pandas as pd
import shutil
import re
import numpy as np
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import uuid
import json
#class for managing connection - basically trying to keep backend separate

class ConnectionManager:
    def __init__(self,app, ip, username, password): #initializing with ip, username, password and private key path (not sure if the key is necessary but keeping it for making sure there are no password tempts)
        self.ip = ip
        self.username = username
        self.password = password
        #self.private_key_path = private_key_path
        self.client = None
        self.error_event = threading.Event() #event for error handling
        self.app = app #passing app instance so error msgbox can be shown properly

        # Per-host debug log to reduce cross-host noise
        logs_dir = Path("logs")
        try:
            logs_dir.mkdir(exist_ok=True)
        except Exception:
            pass
        sanitized = str(self.ip).replace(':', '_').replace('.', '_')
        log_path = logs_dir / f"debug_{sanitized}.log"
        self.debug_log_file = open(log_path, "a", encoding="utf-8") #append-mode per-host debug log

    def log(self, message): #helper method for logging 
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self.debug_log_file.write(f"[{ts}] {message}\n")
        self.debug_log_file.flush()

    def connect(self, use_key=False): #method for connecting to pitaya
        self.client = SSHClient()
        self.client.set_missing_host_key_policy(AutoAddPolicy()) #auto add policy for adding host key
        if use_key:
            private_key = paramiko.RSAKey.from_private_key_file(self.private_key_path) #loading private key
            self.client.connect(self.ip, username=self.username, pkey=private_key)
        else:
            self.client.connect(self.ip, username=self.username, password=self.password)
        return self.client

    def disconnect(self): #simple method for disconnecting from pitaya
        if self.client:
            self.client.close()
            print(f"Disconnected from {self.ip}")
            self.log(f"Disconnected")

    def execute_command(self, command): #method for executing command on pitaya, basically used only to run send_acquire on remote
        self.stdin, self.stdout, self.stderr = self.client.exec_command(command)
        self.start_listener() #starting listener thread for stdout and stderr
        self.stdout.channel.recv_exit_status() #waiting for command to finish
        return self.stdout, self.stderr

    def start_listener(self): #method for starting stdout and stderr listener thread
        self.stdout_content = ""
        self.stderr_content = ""
        self.listener_thread = threading.Thread(target=self.listener) #thread so it doesn't block the main thread/gui
        self.listener_thread.start()

    def join_listener(self): #joining listeners, used for waiting for command to finish
        if self.listener_thread.is_alive(): 
            self.listener_thread.join()

    def listener(self): #listener method for stdout and stderr
        while True:
            read_ready, _, _ = select.select([self.stdout.channel, self.stderr.channel], [], [], 0.1) #selecting ready streams
            if not read_ready:
                continue
            for stream in read_ready: 
                if stream == self.stdout.channel and stream.recv_ready(): #if stdout is ready
                    stdout_content = stream.recv(1024).decode('utf-8') #printing stdout as well as logging it
                    print("STDOUT_LISTENER:", stdout_content, end='', flush=True)
                    self.log(stdout_content)
                elif stream == self.stderr.channel and stream.recv_stderr_ready(): #same for stderr
                    stderr_content = stream.recv_stderr(1024).decode('utf-8')
                    print("STDERR_LISTENER:", stderr_content, end='', flush=True)
                    self.log(stderr_content)
                    self.app.error_queue.put(f"{self.ip}: {stderr_content}") #adding stderr to main app error_que so messagebox can be shown
            if self.stdout.channel.exit_status_ready():
                break

    def list_files(self, directory): #listing files in directory
        sftp = self.client.open_sftp()
        try:
            if sftp.stat(directory): # Check if directory exists
                files = sftp.listdir(directory)
                return files
        except IOError as e:
            print(f"Directory {directory} does not exist.")
            return []
        finally:
            sftp.close()

    def transfer_all_csv_files(self, remote_directory, local_directory, isMerge, progress_callback=None): #transfering data files from pitaya to local machine

        if not os.path.exists(local_directory): #making sure local directory exists, not doing it atm for remote directory might add in future
            print(f"Local directory {local_directory} does not exist.")
            self.app.error_queue.put(f"{self.ip}: Local directory {local_directory} does not exist.")
            return

        with SCPClient(self.client.get_transport()) as scp: #using scp for transfering files, mostly because its faster than sftp
            try:
                remote_files = self.list_files(remote_directory) #listing files in remote directory
            except Exception as e:
                print(f"Failed to list remote directory {remote_directory}. Error: {str(e)}")
                self.app.error_queue.put(f"{self.ip}: Failed to list remote directory {remote_directory}. Error: {str(e)}") #if error is raised messagebox appears
                return

            print(f"Remote files: {remote_files}")

            data_files = [file for file in remote_files if file.endswith('.csv') or file.endswith('.bin')] #tmp location in pitaya has other files so filtering only BIN/CSV files

            # Transfer each BIN/CSV file
            for file in data_files:
                remote_path = os.path.join(remote_directory, file).replace("\\", "/")#replacing backslashes with forward slashes
                local_path = os.path.join(local_directory, file)
                try:
                    scp.get(remote_path, local_path) #transfering file
                    print(f"Successfully transferred {file}.")
                    self.client.exec_command(f"rm {remote_path}")
                except Exception as e:
                    print(f"Failed to transfer {file}. Error: {str(e)}")
                    self.app.error_queue.put(f"{self.ip}: Failed to transfer {file}. Error: {str(e)}") #for any other error - messagebox


    def merge_csv_files(self, merge_enabled, local_mode, target_dir, archive_dir, drive_list=None):
        # BIN files merging logic
        BIN_SUFFIX = ".bin"
        TIMESTAMP_PATTERN = re.compile(r"\d{4}_\d{2}_\d{2}_\d{2}_\d{2}_\d{2}")
        CHANNEL_PATTERN = re.compile(r"CH(\d+)", re.IGNORECASE)
        THREADS = 8

        if local_mode and drive_list:
            target_path = Path(target_dir)
            target_path.mkdir(parents=True, exist_ok=True)

            normalized_drives = [d if len(d) > 2 else d + "\\" for d in drive_list]
            bin_files: list[Path] = []

            for drive in normalized_drives:
                drive_root = Path(drive)
                if not drive_root.exists():
                    error_msg = f"Drive path {drive_root} does not exist."
                    print("ERR:", error_msg)
                    self.app.error_queue.put(error_msg)
                    continue
                found_bins = [f for f in drive_root.rglob("*")
                              if f.suffix.lower() == BIN_SUFFIX and f.is_file()]
                bin_files.extend(found_bins)

            if bin_files:
                def move_file(src: Path):
                    dest = target_path / src.name
                    if dest.exists():
                        base, ext = dest.stem, dest.suffix
                        idx = 1
                        while (candidate := dest.parent / f"{base}_{idx}{ext}").exists():
                            idx += 1
                        dest = candidate
                    try:
                        shutil.move(src, dest)
                    except Exception as exc:
                        move_err = f"Move failed {src} -> {dest}: {exc}"
                        print("ERR:", move_err)
                        self.app.error_queue.put(move_err)

                with ThreadPoolExecutor(THREADS) as executor:
                    executor.map(move_file, bin_files)
            else:
                print("No BIN files to move.")

        if not merge_enabled:
            return None

        print("Merging BIN files")
        target_path = Path(target_dir)
        bin_candidates = [p for p in target_path.iterdir() if p.suffix.lower() == BIN_SUFFIX]
        if not bin_candidates:
            print("No BIN files found in working directory.")
            return None

        # Group by timestamp
        grouped_bins: dict[str, list[Path]] = defaultdict(list)
        for bin_file in bin_candidates:
            ts_match = TIMESTAMP_PATTERN.search(bin_file.name)
            if ts_match:
                grouped_bins[ts_match.group(0)].append(bin_file)
            else:
                no_ts_msg = f"BIN without timestamp: {bin_file.name}"
                print("ERR:", no_ts_msg)
                self.app.error_queue.put(no_ts_msg)

        merged_outputs: list[Path] = []

        for timestamp, files in grouped_bins.items():
            try:
                # Ensure all files contain all the info
                missing_chan = [f for f in files if CHANNEL_PATTERN.search(f.name) is None]
                if missing_chan:
                    missing_names = [m.name for m in missing_chan]
                    merge_err = f"[{timestamp}] skipping merge - missing channel info in: {missing_names}"
                    print("ERR:", merge_err)
                    self.app.error_queue.put(merge_err)
                    continue

                files.sort(key=lambda f: int(CHANNEL_PATTERN.search(f.name).group(1)))

                memmaps = [np.memmap(f, dtype=np.float32, mode="r") for f in files]
                sizes = [m.size for m in memmaps]
                min_size = min(sizes)
                truncated = [m[:min_size] for m in memmaps]
                samples_per_channel = min_size // 2
                device_count = len(truncated)
                total_channels = device_count * 2

                merged_data = np.empty(samples_per_channel * total_channels, dtype=np.float32)
                for dev_idx, mm in enumerate(truncated):
                    merged_data[dev_idx*2   :: total_channels] = mm[0::2]
                    merged_data[dev_idx*2+1 :: total_channels] = mm[1::2]

                # Create unique merged filename to avoid overwrites
                # Use a short UUID (4 hex chars) to keep filenames concise but check for collisions.
                # Retry up to 10 times; if still colliding, fall back to full UUID to guarantee uniqueness.
                merged_filepath = None
                for attempt in range(10):
                    short = uuid.uuid4().hex[:4]
                    merged_filename = f"{timestamp}_{total_channels}ch_{short}.bin"
                    candidate = target_path / merged_filename
                    if not candidate.exists():
                        merged_filepath = candidate
                        break
                if merged_filepath is None:
                    # fallback to full uuid if unlucky
                    merged_filename = f"{timestamp}_{total_channels}ch_{uuid.uuid4().hex}.bin"
                    merged_filepath = target_path / merged_filename

                merged_data.tofile(merged_filepath)
                merged_outputs.append(merged_filepath)
                try:
                    status = {"timestamp": timestamp, "merged": str(merged_filepath)}
                    status_file = target_path / f"{timestamp}_merged_status.json"
                    status_file.write_text(json.dumps(status))
                    os.environ['PY_VAR7'] = 'True'
                    self.log(f"Merged output created: {merged_filepath}")
                except Exception as e:
                    self.log(f"Failed to write merged status: {e}")

                archive_path = Path(archive_dir)
                archive_path.mkdir(parents=True, exist_ok=True)
                with ThreadPoolExecutor(THREADS) as executor:
                    executor.map(lambda f: shutil.move(f, archive_path / f.name), files)

            except Exception as exc:
                merge_err = f"[{timestamp}] merge failed: {exc}"
                print("ERR:", merge_err)
                self.app.error_queue.put(merge_err)
        return