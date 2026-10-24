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
    colors = self.theme_colors
    
    # Main container 
    main_frame = ctk.CTkFrame(
        parent, 
        fg_color=colors["surface"],
        corner_radius=10,
        border_width=1,             
        border_color=colors["border"],
    )
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)

    # section header
    title_label = ctk.CTkLabel(
        main_frame, 
        text="MIDAS BASE  //  SYSTEM STATUS",
        font=("Segoe UI", 18, "bold"),
        text_color=colors["accent"],
    )
    title_label.pack(pady=(48, 12))

    # Active devices tracker 
    device_count = len(devices)
    self.num_devices_label = ctk.CTkLabel(
        main_frame, 
        text=f"ACTIVE DEVICES  //  {device_count}",
        font=("Consolas", 12),
        text_color=colors["success"],
    )
    self.num_devices_label.pack(pady=(4, 28))

    self.connect_btn = ctk.CTkButton(
        main_frame, 
        text="START GROUND STATION",
        command=self.make_ground_station_thread,
        state="normal",
        font=("Segoe UI", 10, "bold"),
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        text_color=colors["background"],
        corner_radius=7,
        height=44,
    )
    self.connect_btn.pack(pady=10, ipadx=18)