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
import json

def _build_telem_tab(self, parent, name):
    ttk.Label(parent, text="Telemetry", font=("Helvetica", 14)).pack()
    ttk.Button(parent, text="Upload File", command=self.open_input_file).pack()

    # container for the canvas and scrollbar
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)

    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    
    self.telem_frame = ttk.Frame(canvas)
    self.telem_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    canvas_window_id = canvas.create_window((0, 0), window=self.telem_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(canvas_window_id, width=e.width))
    scrollbar.pack(side="right", fill="y")

    self.input_file_thing = ttk.Label(parent, text="Input File")
    self.input_file_thing.pack()
