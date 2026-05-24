import tkinter as tk
from tkinter import ttk

def _build_ejection_test_tab(self, parent, name, devices):
    ttk.Label(parent,font=("Helvetica", 14)).pack(expand=True)

    warning = ttk.Label(parent, text="WARNING: Ensure area is clear before initiating pyro test")
    warning.place(relx=0.5, y=90, anchor="n")

    stage_label = ttk.Label(parent, text="Stage:")
    stage_label.place(x=20, y=80)

    #Stage options will become Serial no.
    #Serial no.
    #There are 2 radios currently, 0 and 1

    #These must be populated with MIDAS serial no. only
    #Should only send serial identify command to feather duo
    #The command is serial radio get
    self.stage_options = []

    self.stage_var = tk.StringVar(value="")

    stage_dropdown = ttk.Combobox(
        parent,
        textvariable=self.stage_var,
        values=self.stage_options,
        state="readonly",
        width=15
    )
    stage_dropdown.place(x=80, y=80)

    refresh_btn = ttk.Button(
        parent,
        text="Detect",
        width=15,
        command=lambda: refresh_serials(self, devices)
    )
    self.ejection_stage_dropdown = stage_dropdown

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


def refresh_serials(self, devices):
    from util.feather_subprocess import FeatherSubprocess
    
    # Find the connected Feather Duo device
    target_device = None

    for d in devices: #ts may be extremely broken
        if d.is_online() and d.pipe_conn:
            target_device = d
            break

    if not target_device:
        print("No online device found")
        return

    # Query both radio slots
    self._pending_serials = {}
    self._serial_refresh_device = target_device

    for radio in range(2): #We currently have 2 radios
        target_device.pipe_conn.send(f"serial {radio} get\n")


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

    send_command(self, f"safe {self.stage_var.get()}", self.stage_var.get().lower())
    print("force safe command sent")


#fire pyros commands need to be tested.!!
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

    send_command(self, f"pt {self.stage_var.get()}", self.stage_var.get().lower())

    self.pyro_timer = self.after(10000, lambda: force_safe(self))

def fire_A(self):
    print("FIRE A")
    send_command(self, f"fire {self.stage_var.get()} A", self.stage_var.get().lower())


def fire_B(self):
    print("FIRE B")
    send_command(self, f"fire {self.stage_var.get()} B", self.stage_var.get().lower())


def fire_C(self):
    print("FIRE C")
    send_command(self, f"fire {self.stage_var.get()} C", self.stage_var.get().lower())


def fire_D(self):
    print("FIRE D")
    send_command(self, f"fire {self.stage_var.get()} D", self.stage_var.get().lower())
