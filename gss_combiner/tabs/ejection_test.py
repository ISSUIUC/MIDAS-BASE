import tkinter as tk
from tkinter import ttk

def _build_ejection_test_tab(self, parent, name):
    ttk.Label(parent,font=("Helvetica", 14)).pack(expand=True)

    warning = ttk.Label(parent, text="WARNING: Ensure area is clear before initiating pyro test")
    warning.place(relx=0.5, y=90, anchor="n")

    stage_label = ttk.Label(parent, text="Stage:")
    stage_label.place(x=20, y=80)

    self.stage_options = ["Booster", "Sustainer"]

    self.stage_var = tk.StringVar(value=self.stage_options[0])

    stage_dropdown = ttk.Combobox(
        parent,
        textvariable=self.stage_var,
        values=self.stage_options,
        state="readonly",
        width=15
    )
    stage_dropdown.place(x=80, y=80)

    force_safe_button = ttk.Button(
        parent, 
        text="Force Safe", 
        padding=(20, 20), 
        command=lambda: force_safe(self)
    )
    force_safe_button.place(x=20, y=250)

    pyro_test_button = ttk.Button(
        parent, 
        text="Pyro Test", 
        padding=(20, 20), 
        command=lambda: pyro_test(self)
    )
    pyro_test_button.place(x=150, y=250)

    self.fire_A_button = ttk.Button(
        parent, 
        text="Fire A", 
        state="disabled", 
        padding=(20, 20), 
        command=lambda: fire_A(self)
    )
    self.fire_A_button.place(x=310, y=250)

    self.fire_B_button = ttk.Button(
        parent, 
        text="Fire B", 
        state="disabled", 
        padding=(20, 20), 
        command=lambda: fire_B(self)
    )
    self.fire_B_button.place(x=430, y=250)
    
    self.fire_C_button = ttk.Button(
        parent, 
        text="Fire C", 
        state="disabled", 
        padding=(20, 20), 
        command=lambda: fire_C(self)
    )
    self.fire_C_button.place(x=550, y=250)

    self.fire_D_button = ttk.Button(
        parent, 
        text="Fire D", 
        state="disabled", 
        padding=(20, 20), 
        command=lambda: fire_D(self)
    )
    self.fire_D_button.place(x=670, y=250)

def send_command(self, command, stage_var):
    if hasattr(self, 'command_sender'):
        self.command_sender.send_telemetry_command(command, stage_var)

def force_safe(self):
    self.fire_A_button.config(state="disabled")
    self.fire_B_button.config(state="disabled")
    self.fire_C_button.config(state="disabled")
    self.fire_D_button.config(state="disabled")
    print("force safe")

    if hasattr(self, "pyro_timer"):
        self.after_cancel(self.pyro_timer)

    send_command(self, "safe ", self.stage_var.get().lower())
    print("force safe command sent")


def pyro_test(self):
    stage = self.stage_var.get()
    print(f"pyro test on {stage}")
    self.fire_A_button.config(state="normal")
    self.fire_B_button.config(state="normal")
    self.fire_C_button.config(state="normal")
    self.fire_D_button.config(state="normal")
    print("pyro test")

    if hasattr(self, "pyro_timer"):
        self.after_cancel(self.pyro_timer)

    send_command(self, "pyro_test ", self.stage_var.get().lower())

    self.pyro_timer = self.after(10000, lambda: force_safe(self))

def fire_A(self):
    print("FIRE A")
    send_command(self, "fire A", self.stage_var.get().lower())


def fire_B(self):
    print("FIRE B")
    send_command(self, "fire B", self.stage_var.get().lower())


def fire_C(self):
    print("FIRE C")
    send_command(self, "fire C", self.stage_var.get().lower())


def fire_D(self):
    print("FIRE D")
    send_command(self, "fire D", self.stage_var.get().lower())
