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
    
    # line = ttk.Label(parent, text="--------------------------------------------------------------------------------------------------------------")
    # line.place(x = 0, y = 120)
    warning.place(x = 20, y = 10)
    force_safe_button = ttk.Button(parent, text="Force Safe", padding=(20, 20), command=lambda: force_safe(self))
    force_safe_button.place(x=20,y=250)

    pyro_test_button = ttk.Button(parent, text="Pyro Test", padding=(20, 20), command=lambda: pyro_test(self))
    pyro_test_button.place(x=150,y=250)

    self.fire_A_button = ttk.Button(parent, text="Fire A", state="disabled", padding=(20, 20), command=fire_A)
    self.fire_A_button.place(x=310,y=250)

    self.fire_B_button = ttk.Button(parent, text="Fire B", state="disabled", padding=(20, 20), command=fire_B)
    self.fire_B_button.place(x=430,y=250)
    
    self.fire_C_button = ttk.Button(parent, text="Fire C", state="disabled", padding=(20, 20), command=fire_C)
    self.fire_C_button.place(x=550,y=250)

    self.fire_D_button = ttk.Button(parent, text="Fire D", state="disabled", padding=(20, 20), command=fire_D)
    self.fire_D_button.place(x=670,y=250)

def force_safe(self):
    self.fire_A_button.config(state="disabled")
    self.fire_B_button.config(state="disabled")
    self.fire_C_button.config(state="disabled")
    self.fire_D_button.config(state="disabled")
    print("force safe")

def pyro_test(self):
    self.fire_A_button.config(state="normal")
    self.fire_B_button.config(state="normal")
    self.fire_C_button.config(state="normal")
    self.fire_D_button.config(state="normal")
    print("pyro test")

def fire_A():
    print("FIRE A")

def fire_B():
    print("FIRE B")

def fire_C():
    print("FIRE C")

def fire_D():
    print("FIRE D")
