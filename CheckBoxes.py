from tkinter import *
import customtkinter as ctk

#checkboxes class handling labels and disconnect buttons

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

        for i, ips in enumerate(self.ips): #creating checkboxes for each ip
            checkbox = ctk.CTkCheckBox(self, text=ips)
            checkbox.grid(row=i + 1, column=0, padx=10, pady=(15, 15), sticky="w")
            self.checkboxes.append(checkbox)

            disconnect_button = ctk.CTkButton(self, text="Disconnect", command=lambda ip=ips: self.master.disconnect_from_device(ip)) #creating disconnect button for each ip
            disconnect_button.grid(row=i + 1, column=0, padx=10, pady=10, sticky="w")
            disconnect_button.grid_remove() #hiding disconnect buttons
            self.disconnect_buttons[ips] = disconnect_button

            label = ctk.CTkLabel(self, text="Disconnected", fg_color="red") #creating status label for each ip
            label.grid(row=i + 1, column=1, padx=10, pady=(10, 0), sticky="ew")
            self.labels.append(label)

        self.title = ctk.CTkLabel(self, text=self.title, fg_color="gray30", corner_radius=5)
        self.title.grid(row=0, column=0, padx=10, pady=(10, 0), sticky="ew")

    def show_disconnect_button(self, ip): #method for showing disconnect button for connected ip
        self.disconnect_buttons[ip].grid()
    
    def hide_disconnect_button(self, ip): #method for hiding disconnect button 
        self.disconnect_buttons[ip].grid_remove()

    def get(self): #getter for selected checkboxes
        selected_ips = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                selected_ips.append(checkbox.cget("text")) #adding selected ip to the list
        return selected_ips 

    def update_label(self, ip, status): #method for updating status label, if connected then green, if disconnected then red
        for i, checkbox in enumerate(self.checkboxes):
            if checkbox.cget("text") == ip:
                self.labels[i].configure(text=status)
                if status == "Connected":
                    self.labels[i].configure(fg_color="green")
                else:
                    self.labels[i].configure(fg_color="red")
                break