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

def _build_ejection_test_tab(self, parent, name):
    ttk.Label(parent,font=("Helvetica", 14)).pack(expand=True)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(BASE_DIR,"ali.png")
    img = tk.PhotoImage(file=img_path)
    label = ttk.Label(parent, image=img)
    label.image = img
    label.place(x=10, y=10)    

    warning = ttk.Label(parent, text="WARNING: Ensure area is clear before initiating pyro test")
    
    line = ttk.Label(parent, text="--------------------------------------------------------------------------------------------------------------")
    line.place(x = 0, y = 120)
    warning.place(x = 20, y = 10)
    force_safe_button = ttk.Button(parent, text="Force Safe", padding=(20, 20), command=lambda: print("Force Safe button clicked!"))
    force_safe_button.place(x=20,y=250)

    pyro_test_button = ttk.Button(parent, text="Pyro Test", padding=(20, 20), command=lambda: print("Pyro Test button clicked!"))
    pyro_test_button.place(x=150,y=250)

