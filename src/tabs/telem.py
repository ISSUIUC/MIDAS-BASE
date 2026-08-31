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
from util.canvas import TELEM_DATA_KEYS, REVERSE_TELEM_DATA_KEYS


def _build_telem_tab(self, parent, name):
    ttk.Label(parent, text="Telemetry", font=("Helvetica", 14)).pack()
    ttk.Button(parent, text="Upload File", command=self.open_input_file).pack()
    ttk.Label(parent, text="Start value:").pack()
    self.input_start_frame = ttk.Spinbox(parent, from_=0, to=10000, command=self.telem_dropdown_changed, increment=100)
    self.input_start_frame.pack()


    self.telem_frame = ttk.Frame(parent)
    self.telem_frame.pack(expand=True)

    dropdown_options = [value["title"] for key, value in TELEM_DATA_KEYS.items() if value.get("title") is not None]
    self.telem_dropdown = ttk.Combobox(self.telem_frame, values=dropdown_options)
    self.telem_dropdown.bind("<<ComboboxSelected>>", self.telem_dropdown_changed)
    self.telem_dropdown.pack()

    self.input_file_thing = ttk.Label(self.telem_frame, text="Input File")
    self.input_file_thing.pack()