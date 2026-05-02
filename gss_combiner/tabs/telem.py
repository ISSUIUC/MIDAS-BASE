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

    # 1. Create a container for the canvas and scrollbar
    container = ttk.Frame(parent)
    container.pack(fill="both", expand=True)

    # 2. Create the Canvas and Scrollbar as siblings in the container
    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
    
    # 3. Create the frame THAT WILL BE SCROLLED
    # Important: The parent is the CANVAS
    self.telem_frame = ttk.Frame(canvas)

    # 4. Configure scrolling
    self.telem_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # 5. Create the window inside the canvas
    # NO .pack() for self.telem_frame!
    canvas_window_id = canvas.create_window((0, 0), window=self.telem_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    # 6. Pack Canvas and Scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(canvas_window_id, width=e.width))
    scrollbar.pack(side="right", fill="y")

    # This label is outside the scroll area (packed into parent)
    self.input_file_thing = ttk.Label(parent, text="Input File")
    self.input_file_thing.pack()
    data = []
    if (self.input_file):
        with open(self.input_file, "r") as f:
            for line in f.readlines():
                data.append(json.loads(line))
    print(data)
