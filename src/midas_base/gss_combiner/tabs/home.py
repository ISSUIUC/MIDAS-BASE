import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import multiprocessing
import subprocess
from pathlib import Path
import sys
import os
import serial
from serial.tools.list_ports import comports
import time
import json
import datetime
import threading
import queue
import midas_base.gss_combiner.standalone as standalone

def _build_home_tab(self, parent, devices):
    
    # Ensure dark mode is active
    ctk.set_appearance_mode("dark")
    
    # Main container 
    main_frame = ctk.CTkFrame(
        parent, 
        fg_color="#0e1117",        
        corner_radius=4,            
        border_width=1,             
        border_color="#00f0ff"     
    )
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)

    # section header
    title_label = ctk.CTkLabel(
        main_frame, 
        text="[ COMMAND_CENTER // STATUS ]", 
        font=("Consolas", 14, "bold"),
        text_color="#00f0ff"        
    )
    title_label.pack(pady=(20, 10))

    # Active devices tracker 
    device_count = len(devices)
    self.num_devices_label = ctk.CTkLabel(
        main_frame, 
        text=f"> ACTIVE_DEVICES_DETECTED: [ {device_count} ]", 
        font=("Consolas", 12),
        text_color="#00ff66"        
    )
    self.num_devices_label.pack(pady=(5, 20))

    self.connect_btn = ctk.CTkButton(
        main_frame, 
        text="INITIALIZE GROUND STATION", 
        command=self.make_ground_station_thread,
        state="normal",
        font=("Consolas", 12, "bold"),
        fg_color="#0533bf",         
        hover_color="#cc0066",     
        text_color="#ffffff",
        corner_radius=4,            
        height=40
    )
    self.connect_btn.pack(pady=10, ipadx=10)