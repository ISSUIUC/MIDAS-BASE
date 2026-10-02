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

def _build_export_tab(self, parent):
    self.export_frame = ttk.Frame(parent)
    self.export_frame.pack()

    ttk.Label(self.export_frame, text="Export to CSV", font=("Helvetica", 14)).pack()
    self.no_input_file_label = ttk.Label(self.export_frame, text="Please upload a file in TELEM tab")
    self.no_input_file_label.pack()

    self.export_file_button = ttk.Button(self.export_frame, text="Export to file", state="disabled", command=self.export_data)
    self.export_file_button.pack()