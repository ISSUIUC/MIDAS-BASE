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
    force_safe_button = ttk.Button(parent, text="Force Safe", padding=(20, 20), command=force_safe)
    force_safe_button.place(x=20,y=250)

    pyro_test_button = ttk.Button(parent, text="Pyro Test", padding=(20, 20), command=pyro_test)
    pyro_test_button.place(x=150,y=250)

    fire_A_button = ttk.Button(parent, text="Fire A", padding=(20, 20), command=fire_A)
    fire_A_button.place(x=310,y=250)

    fire_B_button = ttk.Button(parent, text="Fire B", padding=(20, 20), command=fire_B)
    fire_B_button.place(x=430,y=250)
    
    fire_C_button = ttk.Button(parent, text="Fire C", padding=(20, 20), command=fire_C)
    fire_C_button.place(x=550,y=250)

    fire_D_button = ttk.Button(parent, text="Fire D", padding=(20, 20), command=fire_D)
    fire_D_button.place(x=670,y=250)

def force_safe():
    print("force safe")

def pyro_test():
    print("pyro test")

def fire_A():
    print("FIRE A")

def fire_B():
    print("FIRE B")

def fire_C():
    print("FIRE C")

def fire_D():
    print("FIRE D")
