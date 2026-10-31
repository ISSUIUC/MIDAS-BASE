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
    content = ttk.Frame(parent)
    content.pack(fill="both", expand=True, padx=22, pady=20)

    ttk.Label(content, text="DATA EXPORT", style="Title.TLabel").pack(anchor="w")
    ttk.Label(
        content,
        text="Create a clean CSV from the telemetry data currently loaded in the analysis view.",
        style="Muted.TLabel",
    ).pack(anchor="w", pady=(4, 18))

    self.export_frame = ttk.LabelFrame(content, text="CSV OUTPUT", padding=(24, 22))
    self.export_frame.pack(fill="x", anchor="n")

    ttk.Label(self.export_frame, text="01  /  SOURCE", style="Section.TLabel").pack(anchor="w")
    self.no_input_file_label = ttk.Label(
        self.export_frame,
        text="Load a telemetry file from the TELEM tab to enable export.",
        style="Muted.TLabel",
        wraplength=560,
    )
    self.no_input_file_label.pack(anchor="w", pady=(7, 18))

    ttk.Separator(self.export_frame, orient="horizontal").pack(fill="x", pady=(0, 18))
    ttk.Label(self.export_frame, text="02  /  GENERATE FILE", style="Section.TLabel").pack(anchor="w")
    ttk.Label(
        self.export_frame,
        text="Save the loaded telemetry data as a comma-separated values file.",
        style="Muted.TLabel",
        wraplength=560,
    ).pack(anchor="w", pady=(7, 14))
    self.export_file_button = ttk.Button(
        self.export_frame,
        text="EXPORT TELEMETRY TO CSV",
        style="Accent.TButton",
        state="disabled",
        command=self.export_data,
    )
    self.export_file_button.pack(anchor="w")