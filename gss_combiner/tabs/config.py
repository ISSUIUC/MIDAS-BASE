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
from hw.hwtypes import HwType
import threading
import sys
import queue


def add_row(parent, label):
    frame = ttk.Frame(parent)
    frame.pack(fill="x", pady=2)
    ttk.Label(frame, text=label, width=30).pack(side="left")

    if "(bool)" in label:
        var = tk.BooleanVar()

        entry = ttk.Checkbutton(frame, variable=var)
    else:
        var = tk.StringVar()
        
        entry = ttk.Entry(frame, textvariable=var)

    entry.pack(side="left", fill="x", expand=True)

    return var


def _build_midas_tab(self, parent, view_container):
    midas_frame = ttk.Frame(view_container)


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

    # ── LEFT SIDE (GLOBAL / PYRO) ──
    self.cruise_lockout = add_row(left_frame, "CRUISE_LOCKOUT_EN (bool)")
    self.main_alt = add_row(left_frame, "MAIN_ALT (float)")
    self.pyro_fire_t = add_row(left_frame, "PYRO_FIRE_T (float)")
    self.serial_no = add_row(left_frame, "MIDAS Serial No")
    self.midas_telem_freq = add_row(left_frame, "MIDAS Telemetry Frequency")

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
        for key, var in self.channel_entries_ui.items():
            self.channel_entries_data[ch][key] = var.get()
    
    def load_channel(ch):
        data = self.channel_entries_data[ch]
        for key, var in self.channel_entries_ui.items():
            if key in data:
                var.set(data[key])
                

    # SWITCH
    def on_channel_change(event):
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
    flash_btn.pack(side="right", pady=20)

    load_btn = ttk.Button(
        midas_frame,
        text="LOAD",
        command=self.load_midas,
        width=20
    )
    load_btn.pack(side="left", pady=20)

    load_btn = ttk.Button(
        midas_frame,
        text="SAVE",
        command=save_current_channel,
        width=20
    )
    load_btn.pack(side="left", pady=20)

    self.load_channel = load_channel
    self.save_current_channel = save_current_channel
    return midas_frame


def _build_feather_duo_tab(self, parent, view_container):
    feather_frame = ttk.Frame(view_container)
    ttk.Label(feather_frame, text="Feather Duo Config View", font=("Helvetica", 14)).pack(pady=20)

    return feather_frame

def _build_config_tab(self, parent):
        container = ttk.Frame(parent)
        container.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Top selector ──
        selector_frame = ttk.Frame(container)
        selector_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(selector_frame, text="Board Type:", font=("Helvetica", 12)).pack(side="left")

        self.board_type = tk.StringVar(value=HwType.get_hardwares()[0].value)

        board_dropdown = ttk.Combobox(
            selector_frame,
            textvariable=self.board_type,
            values=[HwType.MIDAS_MINI.value, HwType.FEATHER_DUO],
            state="readonly",
            width=15
        )
        board_dropdown.pack(side="left", padx=10)

        # ── View container (stacked frames) ──
        self.config_views = {}

        view_container = ttk.Frame(container)
        view_container.pack(fill="both", expand=True)

        # MIDAS view
        midas_frame = _build_midas_tab(self, parent, view_container)
        # Feather Duo view
        feather_frame = _build_feather_duo_tab(self, parent, view_container)

        def get_globals():
            return self.cruise_lockout.get(), self.main_alt.get(), self.pyro_fire_t.get(), self.serial_no.get(), self.midas_telem_freq.get()

        self.config_views[HwType.MIDAS_MINI.value] = midas_frame
        self.config_views[HwType.FEATHER_DUO.value] = feather_frame

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

        self.get_globals = get_globals