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


# Original UI here
def _build_connect_tab(self, parent, devices):
        """This is the original create_widgets content, now inside the CONNECT tab."""

        # Main layout
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left side: device list
        # DELETE this list_frame entirely in the new version. Everything
        # that used to go inside it now packs directly into main_frame.
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(side="left", fill="both", expand=True)

        # Keep the title but change two things:
        #   - pack it into main_frame instead of list_frame
        #   - change the text from "COM List" to "Connected Devices"
        # Keep the font and pady the same.
        title = ttk.Label(list_frame, text="COM List", font=("Helvetica", 14))
        title.pack(pady=5)

        # Rename the columns. Drop "Streaming to" (nobody was using it)
        # and rename "Device Port" to "Port". The new tuple should be:
        #     ("Port", "Type", "Status", "Meta")
        #
        # Also create the Treeview against main_frame now, not list_frame.
        columns = ("Device Port", "Type", "Status", "Streaming to", "Meta")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        self.tree.tag_configure("disabled", foreground="gray")
        
        # MOVE the two tag_configure calls that were down below (the
        # "connected" and "errored" ones) UP to right here, next to the
        # "disabled" tag config. Same colors, just relocated so all the
        # tag setup is in one spot instead of being scattered.

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        # The insertion loop needs three changes:
        #
        # 1. Skip unidentified devices. Right at the top of the loop body,
        #    add a check: if _device.is_unidentified() is True, `continue`
        #    to the next device. Those are ports that never produced a
        #    usable ident response - Bluetooth virtual ports, unrelated
        #    hardware, silent boards - and the user can't act on them. No
        #    point showing them.
        #
        # 2. Update the tag logic. Old line was:
        #        tags = ("disabled",) if status is NONE or IDENTIFYING... else ()
        #    New logic:
        #        - start with ("disabled",) if status is IDENTIFYING...
        #          (NONE no longer gets the disabled tag - unidentified
        #          devices are already filtered out above, so anything
        #          still showing as NONE is a real device we just haven't
        #          reached yet)
        #        - then append ("connected",) if _device.is_online()
        #        - then append ("errored",) if _device.has_errored
        #
        # 3. Preserve selection across refreshes. Capture the item id
        #    returned by self.tree.insert, then if
        #    _device.get_port() == self.selected_device, call
        #    self.tree.selection_add(new_item) on it. Without this, every
        #    time the tree repopulates the user's selection jumps to
        #    nothing.
        #
        # Also: the values passed to insert no longer include the server
        # (Streaming to) column. New values tuple is:
        #     (device["port"], device["name"], device["status"], device["meta"])
        for _device in devices:
            device = _device.to_dict()

            tags = ("disabled",) if device["status"].upper() == "NONE" or device["status"].upper() == "IDENTIFYING..." else ()
            self.tree.insert("", "end", values=(device["port"], device["name"], device["status"], device["server"], device["meta"]), tags=tags)

        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        self.tree.pack(fill="both", expand=True)

        # DELETE these two tag_configure calls here - they get moved up
        # above, right after the "disabled" tag config.
        self.tree.tag_configure("connected", background="#d2ffd2")
        self.tree.tag_configure("errored", background="#ffd2d2")

        # DELETE this entire right-hand control panel. Everything from
        # here down through the <Escape> binding at the bottom of this
        # function goes away:
        #   - control_frame and its "Input" title
        #   - the "Select a device" label (it moves - see below)
        #   - the stage_sel StringVar and its radio buttons
        #   - the do_log BooleanVar and its checkbox
        #   - the separator, Network section, GSS IP entry, Connect
        #     button, and Console button
        #   - the deselect() function and self.bind("<Escape>", ...)
        #
        # What replaces it:
        #
        # --- Stats section ---
        # Make a new frame inside main_frame:
        #     stats_frame = ttk.Frame(main_frame)
        #     pack fill="x", pady=(10, 0)
        #
        # Build a filtered device list to count against, so the numbers
        # match what's in the tree (which also hides unidentified):
        #     visible_devices = [d for d in devices if not d.is_unidentified()]
        #
        # Total Devices label - text is f"Total Devices: {len(visible_devices)}",
        # pack side="left" with padx=(0, 20) for spacing.
        #
        # Online label - count is sum(1 for d in visible_devices if d.is_online()),
        # text is f"Online: {online_count}", pack side="left".
        #
        # Both go on self as self.total_label and self.online_label, same
        # as before, so the polling loop can update them.
        #
        # --- Device label ---
        # The "Select a device" label needs to exist (on_select writes to
        # it), but it belongs at the bottom of main_frame now, not in a
        # side panel:
        #     self.device_label = ttk.Label(main_frame, text="Select a device")
        #     self.device_label.pack(pady=(10, 0))

        # Right side: control panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(side="right", fill="y", padx=10, pady=5)

        control_title = ttk.Label(control_frame, text="Input", font=("Helvetica", 14))
        control_title.pack(pady=5)

        self.device_label = ttk.Label(control_frame, text="Select a device")
        self.device_label.pack(pady=5)

        self.stage_sel = tk.StringVar(value="sustainer")  # Default selected value

        radio_label = ttk.Label(control_frame, text="Stage Select:")
        radio_label.pack(pady=5)

        self.radio1 = ttk.Radiobutton(control_frame, text="Sustainer", variable=self.stage_sel, value="sustainer")
        self.radio1.pack()

        self.radio2 = ttk.Radiobutton(control_frame, text="Booster", variable=self.stage_sel, value="booster")
        self.radio2.pack()

        self.radio3 = ttk.Radiobutton(control_frame, text="Duo", variable=self.stage_sel, value="duo")
        self.radio3.pack()

        self.mini = ttk.Radiobutton(control_frame, text="Midas", variable=self.stage_sel, value="midas")
        self.mini.pack()

        self.do_log = tk.BooleanVar(value=True)

        self.do_log_checkbox = ttk.Checkbutton(control_frame, text="Generate Log File", variable=self.do_log)
        self.do_log_checkbox.pack(pady=(0, 5))


        self.radio1.config(state="disabled")
        self.radio2.config(state="disabled")
        self.radio3.config(state="disabled")
        self.do_log_checkbox.config(state="disabled")
        # Separator
        ttk.Separator(control_frame, orient="horizontal").pack(fill="x", pady=15)

        stats_title = ttk.Label(control_frame, text="Network", font=("Helvetica", 12, "underline"))
        stats_title.pack(pady=(0, 5))

        label = ttk.Label(control_frame, text="GSS IP:")
        label.pack(pady=5)

        self.ip_entry = tk.Entry(control_frame)
        self.ip_entry.pack(pady=5)

        self.connect_btn = ttk.Button(control_frame, text="Connect", command=self.perform_action, state="disabled")
        self.connect_btn.pack(pady=2)

        self.inspect_btn = ttk.Button(control_frame, text="Console", command=self.inspect_window, state="disabled")
        self.inspect_btn.pack(pady=2)


        stats_title = ttk.Label(control_frame, text="System", font=("Helvetica", 12, "underline"))
        stats_title.pack(pady=(20, 5))

        self.total_label = ttk.Label(control_frame, text=f"Total Devices: {len(devices)}")
        self.total_label.pack(anchor="w")

        online_count = sum(1 for d in devices if d.to_dict()["status"].lower() == "online")
        self.online_label = ttk.Label(control_frame, text=f"Online: {online_count}")
        self.online_label.pack(anchor="w")

        def deselect(event=None):
            self.selected_device = None
            self.tree.selection_remove(self.tree.selection())
            self.device_label.config(text="Select a device")
            self.radio1.config(state="disabled")
            self.radio2.config(state="disabled")
            self.radio3.config(state="disabled")
            self.inspect_btn.config(state="disabled")
            self.connect_btn.config(state="disabled")
            self.do_log_checkbox.config(state="disabled")
        self.bind("<Escape>", deselect)