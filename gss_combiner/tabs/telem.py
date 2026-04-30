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
    self.telem_frame = ttk.Frame(parent)
    self.telem_frame.pack()
    self.input_file_thing = ttk.Label(parent, text="Input File")
    self.input_file_thing.pack()
    data = []
    if (self.input_file):
        with open(self.input_file, "r") as f:
            for line in f.readlines():
                data.append(json.loads(line))
    print(data)
