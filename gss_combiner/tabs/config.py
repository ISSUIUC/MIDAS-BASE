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

def _build_config_tab(self, parent):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Top selector ──
        selector_frame = ttk.Frame(container)
        selector_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(selector_frame, text="Board Type:", font=("Helvetica", 12)).pack(side="left")

        self.board_type = tk.StringVar(value="MIDAS")

        board_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.board_type,
            values=["MIDAS", "Feather Duo"],
            state="readonly",
            width=15
        )
        board_dropdown.pack(side="left", padx=10)

        # ── View container (stacked frames) ──
        self.config_views = {}

        view_container = ttk.Frame(container)
        view_container.pack(fill="both", expand=True)

        # MIDAS view
        midas_frame = ttk.Frame(view_container)
        # Feather Duo view
        feather_frame = ttk.Frame(view_container)
        ttk.Label(feather_frame, text="Feather Duo Config View", font=("Helvetica", 14)).pack(pady=20)

        

        # ── TITLE (CENTERED) ──
        ttk.Label(
            midas_frame,
            text="MIDAS CONFIG",
            font=("Helvetica", 16, "bold")
        ).pack(pady=10)

        # ── MAIN HORIZONTAL SPLIT ──
        main_row = ttk.Frame(midas_frame)
        main_row.pack(fill="both", expand=True, padx=10, pady=10)

        # LEFT: GLOBAL / PYRO
        left_frame = ttk.LabelFrame(main_row, text="Global / Pyro Settings")
        left_frame.pack(side="left", fill="both", expand=True, padx=5)

        # RIGHT: CHANNEL CONFIG
        right_frame = ttk.Frame(main_row)
        right_frame.pack(side="right", fill="both", expand=True, padx=5)


        def add_row(parent, label):
            frame = ttk.Frame(parent)
            frame.pack(fill="x", pady=2)
            ttk.Label(frame, text=label, width=30).pack(side="left")
            entry = ttk.Entry(frame)
            entry.pack(side="left", fill="x", expand=True)
            return entry


        # ── LEFT SIDE (GLOBAL / PYRO) ──
        self.cruise_lockout = add_row(left_frame, "CRUISE_LOCKOUT_EN (bool)")
        self.main_alt = add_row(left_frame, "MAIN_ALT (float)")
        self.pyro_fire_t = add_row(left_frame, "PYRO_FIRE_T (float)")


        # ── RIGHT SIDE (CHANNEL) ──

        # Channel selector
        selector_frame = ttk.Frame(right_frame)
        selector_frame.pack(fill="x", pady=5)

        ttk.Label(selector_frame, text="Channel:", width=10).pack(side="left")

        self.selected_channel = tk.StringVar(value="A")

        channel_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.selected_channel,
            values=["A", "B", "C", "D"],
            state="readonly",
            width=5
        )
        channel_dropdown.pack(side="left")


        # Channel fields
        channel_config = ttk.LabelFrame(right_frame, text="Channel Config")
        channel_config.pack(fill="both", expand=True, pady=5)

        self.channel_entries_ui = {}
        self.channel_entries_data = {ch: {} for ch in ["A", "B", "C", "D"]}

        fields = [
            ("ENABLE", "(bool)"),
            ("FSM_TRIGGER", "(int)"),
            ("DELAY", "(float)"),
            ("MAX_TILT", "(float)"),
            ("AFTER_MOTOR", "(uint8)"),
            ("LAUNCH_T_GT", "(float)"),
            ("LAUNCH_T_LT", "(float)"),
            ("VX_MIN", "(float)"),
            ("VX_MAX", "(float)")
        ]

        for name, typ in fields:
            self.channel_entries_ui[name] = add_row(channel_config, f"{name} {typ}")


        # SAVE current channel
        def save_current_channel():
            ch = self.selected_channel.get()
            for key, entry in self.channel_entries_ui.items():
                self.channel_entries_data[ch][key] = entry.get()

        # LOAD channel
        def load_channel(ch):
            data = self.channel_entries_data[ch]
            for key, entry in self.channel_entries_ui.items():
                entry.delete(0, tk.END)
                if key in data:
                    entry.insert(0, data[key])
                    
        # ── THRESHOLD CONFIG (under pyro) ──
        threshold_frame = ttk.LabelFrame(left_frame, text="Threshold Config")
        threshold_frame.pack(fill="both", expand=True, pady=10)

        self.threshold_entries = {}

        threshold_fields = [
            ("fsms_pt_disarm_t", "(float)"),
            ("fsms_boost_xl", "(float)"),
            ("fsms_boost_lockin_t", "(float)"),
            ("fsms_burnout_xl", "(float)"),
            ("fsms_burnout_lockin_t", "(float)"),
            ("fsms_apogee_detect_spd", "(float)"),
            ("fsms_apogee_lockin_t", "(float)"),
            ("fsms_main_lockout_t", "(float)"),
            ("fsms_landed_entry_t", "(float)"),
            ("fsms_landed_t", "(float)"),
            ("fsms_landed_detect_spd", "(float)"),
            ("fsms_landed_t_lockout", "(float)"),
            ("fsms_cruise_lockout_spd", "(float)")
        ]

        for name, typ in threshold_fields:
            self.threshold_entries[name] = add_row(
                threshold_frame,
                f"{name} {typ}"
            )
        # SWITCH
        def on_channel_change(event=None):
            save_current_channel()
            load_channel(self.selected_channel.get())

        channel_dropdown.bind("<<ComboboxSelected>>", on_channel_change)

        # Init
        load_channel("A")


        # ── FLASH BUTTON (CENTERED BELOW) ──
        flash_btn = ttk.Button(
            midas_frame,
            text="FLASH",
            command=self.flash_midas,
            width=20
        )
        flash_btn.pack(pady=20)
        
        self.config_views["MIDAS"] = midas_frame
        self.config_views["Feather Duo"] = feather_frame

        # Place all frames in same spot
        for frame in self.config_views.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Function to switch views
        def switch_view(*args):
            selected = self.board_type.get()
            for name, frame in self.config_views.items():
                if name == selected:
                    frame.lift()

        # Bind dropdown change
        board_dropdown.bind("<<ComboboxSelected>>", switch_view)

        # Show default view
        switch_view()
