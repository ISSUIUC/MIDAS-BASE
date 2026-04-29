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
import standalone

# Original UI here
def _build_home_tab(self, parent, devices):
        """This is the original create_widgets content, now inside the CONNECT tab."""

        # Main layout
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.num_devices_label = ttk.Label(main_frame, text=f"Num devices connected: {len(devices)}")
        self.num_devices_label.pack(pady=2)
        self.connect_btn = ttk.Button(main_frame, text="Start Ground Station", command=self.start_server_with_all_devices, state="enabled" if len(devices) else "disabled")
        self.connect_btn.pack(pady=2)

        


        


        # # Left side: device list
        # list_frame = ttk.Frame(main_frame)
        # list_frame.pack(side="left", fill="both", expand=True)

        # title = ttk.Label(list_frame, text="COM List", font=("Helvetica", 14))
        # title.pack(pady=5)

        # columns = ("Device Port", "Type", "Status", "Streaming to", "Meta")
        # self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        # self.tree.tag_configure("disabled", foreground="gray")
        
        # for col in columns:
        #     self.tree.heading(col, text=col)
        #     self.tree.column(col, width=120)

        # for _device in devices:
        #     device = _device.to_dict()

        #     tags = ("disabled",) if device["status"].upper() == "NONE" or device["status"].upper() == "IDENTIFYING..." else ()
        #     self.tree.insert("", "end", values=(device["port"], device["name"], device["status"], device["server"], device["meta"]), tags=tags)

        # self.tree.bind("<<TreeviewSelect>>", self.on_select)
        # self.tree.pack(fill="both", expand=True)

        # self.tree.tag_configure("connected", background="#d2ffd2")
        # self.tree.tag_configure("errored", background="#ffd2d2")

        # # Right side: control panel
        # control_frame = ttk.Frame(main_frame)
        # control_frame.pack(side="right", fill="y", padx=10, pady=5)

        # control_title = ttk.Label(control_frame, text="Input", font=("Helvetica", 14))
        # control_title.pack(pady=5)

        # self.device_label = ttk.Label(control_frame, text="Select a device")
        # self.device_label.pack(pady=5)

        # self.stage_sel = tk.StringVar(value="sustainer")  # Default selected value

        # radio_label = ttk.Label(control_frame, text="Stage Select:")
        # radio_label.pack(pady=5)

        # self.radio1 = ttk.Radiobutton(control_frame, text="Sustainer", variable=self.stage_sel, value="sustainer")
        # self.radio1.pack()

        # self.radio2 = ttk.Radiobutton(control_frame, text="Booster", variable=self.stage_sel, value="booster")
        # self.radio2.pack()

        # self.radio3 = ttk.Radiobutton(control_frame, text="Duo", variable=self.stage_sel, value="duo")
        # self.radio3.pack()

        # self.do_log = tk.BooleanVar(value=True)

        # self.do_log_checkbox = ttk.Checkbutton(control_frame, text="Generate Log File", variable=self.do_log)
        # self.do_log_checkbox.pack(pady=(0, 5))


        # self.radio1.config(state="disabled")
        # self.radio2.config(state="disabled")
        # self.radio3.config(state="disabled")
        # self.do_log_checkbox.config(state="disabled")
        # # Separator
        # ttk.Separator(control_frame, orient="horizontal").pack(fill="x", pady=15)

        # stats_title = ttk.Label(control_frame, text="Network", font=("Helvetica", 12, "underline"))
        # stats_title.pack(pady=(0, 5))

        # label = ttk.Label(control_frame, text="GSS IP:")
        # label.pack(pady=5)

        # self.ip_entry = tk.Entry(control_frame)
        # self.ip_entry.pack(pady=5)

        # self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.perform_action, state="disabled")
        # self.connect_btn.pack(pady=2)

        # self.inspect_btn = ttk.Button(control_frame, text="Console", command=self.inspect_window, state="disabled")
        # self.inspect_btn.pack(pady=2)


        # stats_title = ttk.Label(control_frame, text="System", font=("Helvetica", 12, "underline"))
        # stats_title.pack(pady=(20, 5))

        # self.total_label = ttk.Label(control_frame, text=f"Total Devices: {len(devices)}")
        # self.total_label.pack(anchor="w")

        # online_count = sum(1 for d in devices if d.to_dict()["status"].lower() == "online")
        # self.online_label = ttk.Label(control_frame, text=f"Online: {online_count}")
        # self.online_label.pack(anchor="w")

        


        # def deselect(event=None):
        #     self.selected_device = None
        #     self.tree.selection_remove(self.tree.selection())
        #     self.device_label.config(text="Select a device")
        #     self.radio1.config(state="disabled")
        #     self.radio2.config(state="disabled")
        #     self.radio3.config(state="disabled")
        #     self.inspect_btn.config(state="disabled")
        #     self.connect_btn.config(state="disabled")
        #     self.do_log_checkbox.config(state="disabled")
        # self.bind("<Escape>", deselect)
