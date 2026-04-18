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

def _build_export_tab(self, parent, name):
    ttk.Label(parent, text=f"{name} Temporary", font=("Helvetica", 14)).pack(expand=True)