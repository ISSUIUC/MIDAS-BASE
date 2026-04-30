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
import standalone

# Original UI here
def _build_home_tab(self, parent, devices):
        """This is the original create_widgets content, now inside the CONNECT tab."""

        # Main layout
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.num_devices_label = ttk.Label(main_frame, text=f"Num devices connected: {len(devices)}")
        self.num_devices_label.pack(pady=2)
        self.connect_btn = ttk.Button(main_frame, text="Start Ground Station", command=self.make_ground_station_thread, state="enabled")
        self.connect_btn.pack(pady=2)