from tkinter import *
import tkinter
import customtkinter as ctk
import os
import threading
import queue
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import ConnectionManager
from ProgressWindow import ProgressWindow
from CheckBoxes import CheckBoxes
from InputBoxes import InputBoxes
from StatusLine import StatusLine

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
        if not os.path.exists("Data"): #making sure Data folder exists on host
            os.makedirs("Data")
        
        self.status_line = StatusLine(self)
        
        self.title("RedPitaya Signal Acquisition")
        self.geometry("600x500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.resizable(False, False) #disabling resizing of the window

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self.grid_rowconfigure(3, weight=0)
        self.grid_rowconfigure(4, weight=0)
        self.grid_rowconfigure(5, weight=0)
        self.grid_rowconfigure(6, weight=0)
        self.grid_rowconfigure(7, weight=0)

        self.status_line.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.checkboxes_frame = CheckBoxes(self, "Devices", ips=[ENV_MASTERRP, ENV_SLAVE1, ENV_SLAVE2]) #creating checkbox for each device (using checkboxes class)
        self.checkboxes_frame.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="nsew")

        self.connect_button = ctk.CTkButton(self, text="Connect to Pitayas", command=self.start_connect_to_devices_thread) #creating connect button
        self.connect_button.grid(row=3, column=0,columnspan=2, padx=10, pady=10)

        self.inputboxes_frame = InputBoxes(self, "Parameters", labels=['Decimation', 'Buffer size', 'Delay', 'Loops','Time'], status_line=self.status_line)
        self.inputboxes_frame.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="nsew")

        self.acquire_button = ctk.CTkButton(self, text="Acquire Signals", command=self.initiate_acquisition) #creating acquire button
        self.acquire_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)
        self.acquire_button.configure(state="disabled")

        self.transfer_button = ctk.CTkButton(self, text="Transfer Data", command=self.transfer_files) #creating transfer button
        self.transfer_button.grid(row=5, column=0, padx=10,columnspan=2, pady=10)
        self.transfer_button.configure(state="disabled")

        self.stop_button = ctk.CTkButton(self, text="STOP", command=self.stop_acquisition) #creating stop button
        self.stop_button.grid(row=2, column=0,columnspan=2, padx=10, pady=10,sticky="new")
        self.stop_button.grid_remove()

        self.abort_button = ctk.CTkButton(self, text="ABORT", command=self.abort_acquisition) #creating abort button
        self.abort_button.grid(row=3, column=0,columnspan=2, padx=10, pady=10,sticky="nsew")
        self.abort_button.grid_remove()

        self.isLocal = ctk.StringVar(value=0)
        self.switch_local_frame = ctk.CTkFrame(self)
        self.switch_local_frame.grid(row=4, column=0, padx=10, pady=10, sticky="w")
        self.switch_local = ctk.CTkSwitch(self.switch_local_frame, text="Local Acquisition",command= lambda:self.get_Switch_bool(self.isLocal), variable=self.isLocal, onvalue=1, offvalue=0)
        self.switch_local.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.isMerge = ctk.StringVar(value=0)
        #self.switch_merge_frame = ctk.CTkFrame(self)
        #self.switch_merge_frame.grid(row=5, column=0, padx=10, pady=10, sticky="w")
        self.switch_merge = ctk.CTkSwitch(self.switch_local_frame, text="Merge CSV Files",command = lambda:self.get_Switch_bool(self.isMerge), variable=self.isMerge, onvalue=1, offvalue=0)
        self.switch_merge.grid(row=1, column=0, padx=10, pady=10, sticky="w")

        self.check_errors() #constantly checking for errors in queue
        self.check_new_checked_boxes() #constantly checking for new checked boxes
        self.check_transfer_button() #if remote has csv files then enable transfer button
        self.bind("<Return>", lambda event:self.initiate_acquisition())

    def show_acquisition_view(self): #showing acquisition view
        self.connect_button.grid_remove()
        self.acquire_button.grid_remove()
        self.transfer_button.grid_remove()
        self.switch_local_frame.grid_remove()
        self.switch_merge.grid_remove()
        self.stop_button.grid()
        self.abort_button.grid()

    def show_main_view(self): #showing main view
        self.stop_button.grid_remove()
        self.abort_button.grid_remove()
        self.connect_button.grid()
        self.acquire_button.grid()
        self.transfer_button.grid()
        self.switch_local_frame.grid()
        self.switch_merge.grid()
    
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
            #print(f"Remote files for {connection.ip}: {remote_files}")  # Debugging statement
            csv_files = [file for file in remote_files if file.endswith('.csv') or file.endswith('.bin')]
            print(f"CSV files for {connection.ip}: {csv_files}")  # Debugging statement
            if len(csv_files) != 0:
                self.transfer_button.configure(state="normal")
            else:
                self.transfer_button.configure(state="disabled")
    

    def check_errors(self):
        try:
            error_message = self.error_queue.get_nowait() #checking if there is any error in queue
        except queue.Empty:
            pass
        else:
            self.show_error(error_message) #if there is show error message using tkinter messagebox
        self.after(100, self.check_errors)
    
    def get_Switch_bool(self,switch_var):
        bool_value = switch_var.get()
        bool_value = bool(int(bool_value))
        print(f"{switch_var}:{bool_value}")
        return bool_value


    def show_error(self,error_text): #simple method to pop up tkinter messagebox with error message
        tkinter.messagebox.showerror("Error",error_text)

    def initiate_acquisition(self): #method to open progress window and start acquisition on pitaya
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
                rp = ConnectionManager.ConnectionManager(self, ip, 'root', 'root') #creating connection manager object
                if rp.connect() and rp.client is not None: #if connection is successful add connection to connections list
                    self.connections.append(rp)
                    output = rp.execute_command(f"echo 'Connected to {ip}'") #sending command to pitaya to check if connection is successful it should display on user terminal
                    self.checkboxes_frame.update_label(ip, "Connected") #updating label in checkboxes
                    self.checkboxes_frame.show_disconnect_button(ip) #showing disconnect button
                    self.acquire_button.configure(state="normal") #enabling acquire button
                else:
                    raise Exception(f"Failed to connect to {ip}") #if connection failed raise exception and show error message
            except Exception as e:
                self.error_queue.put(str(e) + f" {ip}")
                self.checkboxes_frame.update_label(ip, "Failed to connect")
                self.connect_button.configure(state="normal")

    def start_acquisition_thread(self):
        threading.Thread(target=self.start_acquisition, args=(self.command,), daemon=True).start() #starting acquisition in separate thread

    def start_acquisition(self, command):
        self.status_line.start_timer()
        for connection in self.connections:
            threading.Thread(target=self.run_acquisition, args=(connection, command), daemon=True).start()


    def run_acquisition(self, connection, command): #running acquisition on pitaya
        self.acquire_button.configure(state="normal")
        try:
            params = self.inputboxes_frame.get()
            print(f"Parameters received: {params}")  # Debugging statement
            # Check if all required parameters are present
            required_params = ["Decimation", "Buffer size", "Delay", "Loops"]
            for param in required_params:
                if param not in params:
                    raise KeyError(f"Missing parameter: {param}")
            param_str = ' '.join([str(params[param]) for param in required_params])
            isLocal_str = str(self.get_Switch_bool(self.isLocal))
            full_command = f"{command} {param_str} {isLocal_str}"
            print(f"Executing command: {full_command}")  # Debugging statement
            stdout, stderr = connection.execute_command(full_command) #sending command to pitaya
            connection.start_listener() #starting listener for stdout and stderr
        except Exception as e:
            e_msg = f"{connection}: {str(e)}" #if error occurred show error message
            print(e_msg)
            self.error_queue.put(e_msg)
        finally:
            self.progress_window.close() 
            self.status_line.stop_timer() #closing progress window at the end of acquisition process
        self.check_transfer_button() #check if csv data to transfer is available
        connection.merge_csv_files(self.get_Switch_bool(self.isMerge),self.get_Switch_bool(self.isLocal),ENV_LOCALPATH, ENV_ARCHIVE_DIR,[pitaya_dict[connection.ip]])
        self.after(1000,self.status_line.update_status("Merging completed"))
        self.show_main_view()


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


if __name__ == "__main__":
    app = App()
    app.mainloop()
