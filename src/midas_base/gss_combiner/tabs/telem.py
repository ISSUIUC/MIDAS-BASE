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
import json
from midas_base.gss_combiner.util.canvas import TELEM_DATA_KEYS, REVERSE_TELEM_DATA_KEYS


def _build_telem_tab(self, parent, name):
    content = ttk.Frame(parent)
    content.pack(fill="both", expand=True, padx=22, pady=20)
    ttk.Label(content, text="TELEMETRY ANALYSIS", style="Title.TLabel").pack(anchor="w")
    ttk.Label(
        content,
        text="Load a flight data file, choose a signal, and inspect its plotted values.",
        style="Muted.TLabel",
    ).pack(anchor="w", pady=(4, 16))

    # --- SEZIONE DATA SOURCE (File + Caselle Start/End) ---
    controls = ttk.LabelFrame(content, text="DATA SOURCE", padding=(14, 12))
    controls.pack(fill="x", pady=(0, 14))

    ttk.Label(controls, text="FILE", style="Section.TLabel").grid(row=0, column=0, sticky="w")
    ttk.Button(
        controls,
        text="SELECT TELEMETRY FILE",
        style="Accent.TButton",
        command=self.open_input_file,
    ).grid(row=1, column=0, sticky="w", pady=(7, 0))

    # Casella START FRAME
    ttk.Label(controls, text="START FRAME", style="Section.TLabel").grid(
        row=0, column=1, sticky="w", padx=(28, 0)
    )
    self.input_start_frame = ttk.Spinbox(
        controls,
        from_=0,
        to=10000,
        command=self.range_change,
        increment=100,
        width=12,
    )
    self.input_start_frame.set(0)
    self.input_start_frame.grid(row=1, column=1, sticky="w", padx=(28, 0), pady=(7, 0))

    # Casella END FRAME (Aggiunta per il punto di fine)
    ttk.Label(controls, text="END FRAME", style="Section.TLabel").grid(
        row=0, column=2, sticky="w", padx=(28, 0)
    )
    self.input_end_frame = ttk.Spinbox(
        controls,
        from_=0,
        to=10000,
        command=self.range_change,
        increment=100,
        width=12,
    )
    self.input_end_frame.set(100)
    self.input_end_frame.grid(row=1, column=2, sticky="w", padx=(28, 0), pady=(7, 0))

    # Collega il tasto Invio alla casella di inizio
    self.input_start_frame.bind("<Return>", self.Sync_boxes_to_sliders)
    self.input_start_frame.configure(command=self.Sync_boxes_to_sliders)

    # Etichetta e casella per END FRAME (colonna 2)
    ttk.Label(controls, text="END FRAME", style="Section.TLabel").grid(
        row=0, column=2, sticky="w", padx=(28, 0)
    )
    self.input_end_frame = ttk.Spinbox(
        controls,
        from_=0,
        to=10000,
        command=self.Sync_boxes_to_sliders,
        increment=100,
        width=12,
    )
    self.input_end_frame.grid(row=1, column=2, sticky="w", padx=(28, 0), pady=(7, 0))
    self.input_end_frame.bind("<Return>", self.Sync_boxes_to_sliders)

    controls.columnconfigure(3, weight=1)

    # --- SEZIONE SIGNAL VIEW (prima creiamo plot_panel, poi ci mettiamo gli oggetti) ---
    plot_panel = ttk.LabelFrame(content, text="SIGNAL VIEW", padding=(14, 12))
    plot_panel.pack(fill="both", expand=True)

    plot_header = ttk.Frame(plot_panel)
    plot_header.pack(fill="x", pady=(0, 10))

    self.input_file_thing = ttk.Label(
        plot_header,
        text="NO FILE LOADED",
        style="Muted.TLabel",
        wraplength=340,
        justify="right",
    )
    self.input_file_thing.pack(side="right", padx=(12, 0))

    # Creiamo gli slider dentro plot_panel (DOPO che plot_panel esiste)
    self.start_label = ttk.Label(plot_panel, text="Start Value", font=("Helvetica", 14))
    self.start_label.pack()
    self.super_slider = ttk.LabeledScale(plot_panel, from_=0, to=100)
    self.super_slider.pack()

    self.end_label = ttk.Label(plot_panel, text="End Value", font=("Helvetica", 14))
    self.end_label.pack()
    self.infra_slider = ttk.LabeledScale(plot_panel, from_=0, to=100)
    self.infra_slider.pack()

    self.infra_slider.scale.configure(command=self.range_change)
    self.super_slider.scale.configure(command=self.range_change)

    # Creiamo telem_frame PRIMA di metterci dentro telem_dropdown
    self.telem_frame = ttk.Frame(plot_panel)
    self.telem_frame.pack(fill="both", expand=True)

    dropdown_options = [
        value["title"] for key, value in TELEM_DATA_KEYS.items() if value.get("title") is not None
    ]
    self.telem_dropdown = ttk.Combobox(self.telem_frame, values=dropdown_options)
    self.telem_dropdown.bind("<<ComboboxSelected>>", self.range_change)
    self.telem_dropdown.pack()