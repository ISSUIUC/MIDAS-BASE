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

def _build_connect_tab(self, parent, devices):
        # Main layout
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Title
        title = ttk.Label(main_frame, text="Connected Devices", font=("Helvetica", 14))
        title.pack(pady=5)

        # Treeview Setup
        columns = ("Port", "Type", "Status", "Meta")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings")
        
        # Tag configuration (All in one spot)
        self.tree.tag_configure("disabled", foreground="gray")
        self.tree.tag_configure("connected", background="#d2ffd2")
        self.tree.tag_configure("errored", background="#ffd2d2")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        # Filter out phantom/dead ports manually since is_unidentified() was removed
        visible_devices = [d for d in devices if not d.is_unidentified()]

        # Populate the tree
        for _device in visible_devices:
            device = _device.to_dict()

            # Dynamic tag logic
            tags = []
            if device["status"].upper() == "IDENTIFYING...":
                tags.append("disabled")
            if _device.is_online():
                tags.append("connected")
            if getattr(_device, 'has_errored', False):
                tags.append("errored")

            new_item = self.tree.insert(
                "", "end",
                values=(device["port"], device["name"], device["status"], device["meta"]),
                tags=tuple(tags)
            )

            # Preserve selection across UI refreshes
            if hasattr(self, 'selected_device') and _device.get_port() == self.selected_device:
                self.tree.selection_add(new_item)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.pack(fill="both", expand=True)

        # --- Stats section (Replaces the entire right-hand control panel) ---
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(fill="x", pady=(10, 0))

        self.total_label = ttk.Label(stats_frame, text=f"Total Devices: {len(visible_devices)}")
        self.total_label.pack(side="left", padx=(0, 20))

        online_count = sum(1 for d in visible_devices if d.is_online())
        self.online_label = ttk.Label(stats_frame, text=f"Online: {online_count}")
        self.online_label.pack(side="left")

        # --- Device label ---
        self.device_label = ttk.Label(main_frame, text="Select a device")
        self.device_label.pack(pady=(10, 0))