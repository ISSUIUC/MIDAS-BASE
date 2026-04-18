import tkinter as tk
from tkinter import ttk
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
import sys
import queue


# Elements to add
# 

# Original UI here
def _build_home_tab(self, parent, name):
    # ttk.Label(parent, text=f"{name} Temporary HOME 2", font=("Helvetica", 14)).pack(expand=True)
    
    # container = ttk.Frame(parent)
    # container.pack(fill="both", expand=True, padx=10, pady=10)

    # view_container = ttk.Frame(container)
    # view_container.pack(fill="both", expand=True)
    
    
    # ── GROUND STATION BUTTON (CENTERED BELOW) ──
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True, padx=10, pady=10)
    midas_frame = ttk.Frame(container)
    midas_frame.pack()
    grnd_stat_btn = ttk.Button(
        midas_frame,
        text="Start Ground Station",
    )
    grnd_stat_btn.pack()

    clients_frame = ttk.Frame(container)
    clients_frame.pack(fill="both", expand=True, padx=10, pady=10)

    clients_header = ttk.Label(clients_frame, text="Clients", font=("Arial", 10, "bold"))
    clients_header.pack(anchor="w", pady=(0, 5))
    clients_listbox = tk.Listbox(clients_frame, height=6)
    clients_listbox.pack(fill="both", expand=True)

    devices_frame = ttk.Frame(container)
    devices_frame.pack(fill="both", expand=True, padx=10, pady=10)

    devices_header = ttk.Label(devices_frame, text="Devices", font=("Arial", 10, "bold"))
    devices_header.pack(anchor="w", pady=(0, 5))
    devices_listbox = tk.Listbox(devices_frame, height=6)
    devices_listbox.pack(fill="both", expand=True)
