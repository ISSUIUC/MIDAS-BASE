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
from util.feather_subprocess import FeatherSubprocess
from util.commander import CommandSender

import threading
import sys
import queue
from tabs.config import _build_config_tab
from tabs.connect import _build_connect_tab
from tabs.ejection_test import _build_ejection_test_tab
from tabs.telem import _build_telem_tab
from tabs.export import _build_export_tab
from tabs.home import _build_home_tab
import webbrowser

def get_feather_duo_ports():
    """
    Gets the ports of connected Feather Duos

    Returns:
        list: list of connected Feather Duos
    """
    FEATHER_DUO_PID = 4097
    return [port.device for port in comports() if port.pid == FEATHER_DUO_PID]


devices: list[FeatherSubprocess] = [] #check if empty list works

def get_device(port):
    # get the device
    for _device in devices:
        if _device.get_port() == port:
            return _device
    return None

def run_standalone_worker(pipe_conn, ip, port, stage_sel, do_log):
    # Add real logic here
    script_path = os.path.join(os.path.dirname(__file__), "standalone.py")
    print("Begin Subprocess:")
    log_t = "" if do_log else "--no-log"
    print(f"{sys.executable} {script_path} --ip {ip} --port {port} --{stage_sel} {log_t}")

    args = [
        sys.executable, script_path,
        "--ip", ip,
        "--port", port,
        f"--{stage_sel}"
    ]

    if not do_log:
        args.append("--no-log")

    proc = subprocess.Popen(args,  stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1)

    # subprocess.run([sys.executable, script_path, "--ip", ip, "--port", port, f"--{stage_sel}"])

    stdin_q = queue.Queue()

    def read_stdout():
        for line in proc.stdout:
            stdin_q.put(line)

    thd = threading.Thread(target=read_stdout, daemon=True).start()

    while True:
        if pipe_conn.poll():
            msg = pipe_conn.recv()
            if msg == "kill\n":
                break
            proc.stdin.write(msg)
            proc.stdin.flush()
        
        if not stdin_q.empty():
            line = stdin_q.get()
            pipe_conn.send(line.strip())

        time.sleep(0.01)
    
    # End loop and clean up
    proc.kill()
    pipe_conn.close()
    print(f"[{port}] Cleaning up process")


class DeviceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Home")
        self.geometry("800x550")
        self.selected_device = None
        self.windows = []

        # MIDAS BASE state
        self.gss_running = False
        self.gss_uptime_start = None
        self.gss_process = None  # TODO: hold actual server process

        # CONFIG state — which device is selected for config
        self.cfg_selected_port = None
        self.command_sender = CommandSender(devices)

        self.create_widgets()

    def update_devices(self):
        global devices
        ports = get_feather_duo_ports()
        existing_ports = [d.get_port() for d in devices]

        # Remove old ports that aren't connected
        for d in devices:
            if d.get_port() not in ports:
                print("[!] Deleting ", d.get_port())
                d.cleanup()

                for window in self.windows:
                    _device, _window = window
                    if d.get_port() == _device:
                        _window.destroy()

        devices = [d for d in devices if d.get_port() in ports]
        for p in ports:
            # Check if this port is already in devices:
            if p not in existing_ports:
                # Create a new one!
                devices.append(FeatherSubprocess(p))
        
        self.update_device_list()
        self.after(200, self.update_devices)

    def update_stdouts(self):
        global devices
        for device in devices:
            if device.pipe_conn is None or device.proc is None:
                continue
            
            try:
                while device.pipe_conn.poll():
                    msg = device.pipe_conn.recv()
                    if msg.startswith("REPORT_OK:"):
                        ip = msg[10:]
                        device.stat = "ONLINE"
                        device.set_ip(ip)

                    if msg.startswith("REPORT_ERR"):
                        print(f"[!] Process {device.get_port()} flagged an error and exited.")
                        device.cleanup()
                        print(f"[!] Process {device.get_port()} Triggering a device cleanup:")
                        continue

                    if msg.startswith("[TO MIDAS]"):
                        self._last_cmd = msg[11:].strip()

                    elif msg.startswith("[F]"):

                        val = msg[3:].strip() #the stupid F bro i swear, ts was breaking everything

                        self.parser_midas(self._last_cmd, val)

                        self._last_cmd = None

                    device.add_to_stdout(msg)
            except:
                print(f"[{device.get_port()}] Detected an unexpected pipe closure, but process isn't cleaned up!")
                device.meta = "ERR: UNEXPECTED TERM"
                device.has_errored = True
                device.pipe_conn = None
                device.cleanup()

                for window in self.windows:
                    _device, _window = window
                    if device.get_port() == _device:
                        _window.destroy()


        self.after(50, self.update_stdouts)


    def parser_midas(self, cmd, val):

        for unit in [" MHz", " m/s", " ms", " m", " degrees"]:
            val = val.replace(unit, "")
        val = val.strip()

        if "(true)" in val:
            val = True
        elif "(false)" in val:
            val = False

        if cmd == "serial get":
            self.serial_no.set(val)
        elif cmd == "frequency get":
            self.midas_telem_freq.set(val)
        elif cmd == "fsm threshold CRUISE_LOCKOUT_EN":
            self.cruise_lockout.set(val)
        elif cmd == "fsm threshold MAIN_ALT":
            self.main_alt.set(val)
        elif cmd == "fsm threshold PYRO_FIRE_T":
            self.pyro_fire_t.set(val)

        elif cmd.startswith("fsm ") and len(cmd.split()) == 3:

            fsm, ch, field = cmd.split()

            self.channel_entries_data[ch][field] = val

            if self.selected_channel.get() == ch:
                self.load_channel(ch)


    def update_device_list(self):
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Re-insert updated device info
        for _device in devices:
            device = _device.to_dict()
            tags = ("disabled",) if device["status"].upper() in ("NONE", "IDENTIFYING...") else ()
            if _device.is_online():
                tags = tags + ("connected",)
            if _device.has_errored:
                tags = tags + ("errored",)
            new_item = self.tree.insert(
                "", "end",
                values=(device["port"], device["name"], device["status"], device["server"], device["meta"]),
                tags=tags
            )

            if _device.get_port() == self.selected_device:
                self.tree.selection_add(new_item)

                if _device.is_online():
                    self.inspect_btn.config(state="normal")
                    self.connect_btn.config(text="Disconnect")
                else:
                    self.inspect_btn.config(state="disabled")
                    self.connect_btn.config(text="Connect")

        # Update stats
        self.total_label.config(text=f"Total Devices: {len(devices)}")
        online_count = sum(1 for d in devices if d.to_dict()["status"].lower() == "online")
        self.online_label.config(text=f"Online: {online_count}")

    def create_widgets(self):
        # Menu Bar
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Add tabs here
        home_tab = ttk.Frame(self.notebook)
        config_tab = ttk.Frame(self.notebook)
        test_tab = ttk.Frame(self.notebook)
        connect_tab = ttk.Frame(self.notebook)
        telem_tab = ttk.Frame(self.notebook)
        export_tab = ttk.Frame(self.notebook)

        self.notebook.add(home_tab, text="HOME")
        self.notebook.add(config_tab, text="CONFIG")
        self.notebook.add(test_tab, text="EJECTION_TEST")
        self.notebook.add(connect_tab, text="CONNECT ")
        self.notebook.add(telem_tab, text="TELEM")
        self.notebook.add(export_tab, text="EXPORT")

        # Default to MIDAS BASE
        self.notebook.select(home_tab)


        _build_connect_tab(self, connect_tab, devices)
        _build_config_tab(self, config_tab)
        
        _build_ejection_test_tab(self, test_tab, "TEST")
        _build_telem_tab(self, telem_tab, "TELEM")
        _build_export_tab(self, export_tab, "EXPORT")
        _build_home_tab(self, home_tab, devices)

    def _build_poop(self, parent, name):
        ttk.Label(parent, text=f"{name} Temporary", font=("Helvetica", 14)).pack(expand=True)

    channels = ["A", "B", "C", "D"]
    fields = [
        "ENABLE",
        "FSM_TRIGGER",
        "DELAY",
        "MAX_TILT",
        "AFTER_MOTOR",
        "LAUNCH_T_GT",
        "LAUNCH_T_LT",
        "VX_MIN",
        "VX_MAX"
    ]

    def flash_midas(self):
        target_device = get_device(self.selected_device)

        if not target_device or not target_device.pipe_conn:
            print("No device connected")
            return

        target_device.pipe_conn.send("echo 0\n")

        cruise_lockout, main_alt, pyro_fire_t, serial_no, midas_telem_freq = self.get_globals()
        cruise_lockout_num = 0
        if cruise_lockout:
            cruise_lockout_num = 1

        #GLOBALS
        target_device.pipe_conn.send(f"serial set {serial_no}\n")
        time.sleep(.2)
        #print(f"serial set {serial_no}\n")


        target_device.pipe_conn.send(f"frequency set {midas_telem_freq}\n")
        time.sleep(.2)
        #print(f"frequency set {midas_telem_freq}\n")

        target_device.pipe_conn.send(f"fsm threshold CRUISE_LOCKOUT_EN {cruise_lockout_num}\n")
        # time.sleep(.2)
        #print(f"fsm threshold CRUISE_LOCKOUT_EN {cruise_lockout_num}\n")

        target_device.pipe_conn.send(f"fsm threshold MAIN_ALT {main_alt}\n")
        time.sleep(.2)
        #print(f"fsm threshold MAIN_ALT {main_alt}\n")

        target_device.pipe_conn.send(f"fsm threshold PYRO_FIRE_T {pyro_fire_t}\n")
        time.sleep(.2)
        #print(f"fsm threshold MAIN_ALT {pyro_fire_t}\n")

        # CHANNELS
        

        for ch in self.channels:
            for field in self.fields:
                data = self.channel_entries_data[ch]

                varnum = 0
                if field == "ENABLE":
                    if data[field]:
                        varnum = 1
                    cmd = f"fsm {ch} {field} {varnum}\n"
                else:
                    cmd = f"fsm {ch} {field} {data[field]}\n"
                #print(cmd)
                target_device.pipe_conn.send(cmd)
                time.sleep(.2)



    def load_midas(self):
        target_device = get_device(self.selected_device)

        if not target_device or not target_device.pipe_conn:
            print("No device connected")
            return

        target_device.pipe_conn.send("echo 0\n")

        #GLOBALS
        target_device.pipe_conn.send("serial get\n")
        time.sleep(.2)

        target_device.pipe_conn.send("frequency get\n")
        time.sleep(.2)

        target_device.pipe_conn.send("fsm threshold CRUISE_LOCKOUT_EN\n")
        time.sleep(.2)

        target_device.pipe_conn.send("fsm threshold MAIN_ALT\n")
        time.sleep(.2)

        target_device.pipe_conn.send("fsm threshold PYRO_FIRE_T\n")
        time.sleep(.2)

        # CHANNELS
        

        for ch in self.channels:
            for field in self.fields:
                cmd = f"fsm {ch} {field}\n"
                target_device.pipe_conn.send(cmd)
                time.sleep(.2)


    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            item = selected[0]
            tags = self.tree.item(item, "tags")

            if "disabled" in tags:
                # Prevent selection visually
                self.tree.selection_remove(item)
                self.selected_device = None
                self.device_label.config(text="Select a device")
                self.connect_btn.config(state="disabled")
                self.inspect_btn.config(state="disabled")
                self.do_log_checkbox.config(state="disabled")
                return

            values = self.tree.item(item, "values")
            is_same_select = values[0] == self.selected_device
            self.selected_device = values[0]
            self.device_label.config(text=f"Selected: {self.selected_device}")
            self.connect_btn.config(state="normal")
            self.do_log_checkbox.config(state="normal")

            _device = get_device(self.selected_device)

            if not is_same_select:
                if _device.type == "FEATHER M0":
                    self.radio1.config(state="normal")
                    self.radio2.config(state="normal")
                    self.radio3.config(state="disabled")
                    self.mini.config(state="disabled")
                    self.stage_sel.set("sustainer")

                if _device.type == "FEATHER DUO":
                    self.radio1.config(state="disabled")
                    self.radio2.config(state="disabled")
                    self.radio3.config(state="normal")
                    self.stage_sel.set("duo")

                if _device.type == "MIDAS MINI":
                    self.radio1.config(state="disabled")
                    self.radio2.config(state="disabled")
                    self.radio3.config(state="disabled")
                    self.mini.config(state="normal")
                    self.stage_sel.set("midas")

                if _device.is_online():
                    dev_ip, dev_sl = _device.get_stat()
                    self.do_log.set(dev_sl)
                    self.ip_entry.delete(0, tk.END) # Clear existing content
                    self.ip_entry.insert(0, dev_ip)
                    self.stage_sel.set(_device.stage_sel)


    def make_ground_station_thread(self):
        self.ground_station_thread = threading.Thread(group=None, target=self.start_ground_station)
        self.ground_station_thread.start()

    def start_ground_station(self):
        # input("Open Docker Desktop and then press enter ")
        print("Trying to start Ground Station Docker Container...")
        current_path = Path(__file__).resolve().parent / "GroundStation" / "compose.yml"
        with subprocess.Popen(["docker-compose", "-f", current_path.absolute(), "up", "--build"], stdout=subprocess.PIPE, text=True, bufsize=1, stderr=subprocess.STDOUT) as proc:
            opened_browser = False
            for line in proc.stdout:
                print(line)
                if "127.0.0.1" in str(line) and not(opened_browser):
                    print("Opening localhost")
                    webbrowser.open("http://localhost")

        # os.system(f"docker-compose -f {current_path.absolute()} up --build")


    def perform_action(self):
        global devices
        if self.selected_device:
            target_device = get_device(self.selected_device)

            if target_device.is_online():
                # disconnect & close windows
                target_device.cleanup()

                target_device.proc = None
                target_device.meta = ""

                for window in self.windows:
                    _device, _window = window
                    if self.selected_device == _device:
                        _window.destroy()
                return

            if target_device.pipe_conn is not None or target_device.proc is not None:
                print("Cleaned up device.")
                target_device.cleanup()
                target_device.pipe_conn = None
                target_device.proc = None

            ip = self.ip_entry.get()
            print(f"Running device {self.selected_device}")
            print(f"Connecting to... {self.ip_entry.get()}")

            # self.open_terminal_window(self.selected_device)

            should_log = self.do_log.get()

            target_device.should_log = should_log

            target_device.has_errored = False
            target_device.reset()
            target_device.stat = "STARTUP..."
            log_str = "NO"
            if should_log:
                log_str = "YES"
            target_device.meta = f"{self.stage_sel.get().upper()} (LOG: {log_str})"
            target_device.stage_sel = self.stage_sel.get()
            target_device.pipe_conn, child_conn = multiprocessing.Pipe()
            target_device.proc = multiprocessing.Process(target=run_standalone_worker, args=(child_conn, ip, self.selected_device, self.stage_sel.get(), should_log))
            target_device.proc.start()

    def inspect_window(self):
        if self.selected_device:
            print("Opening terminal window")
            self.open_terminal_window(self.selected_device)
            # Add real logic here

    def open_terminal_window(self, device):
        global devices
        term_win = tk.Toplevel(self)
        term_win.title("Network console: " + device)
        term_win.geometry("500x300")

        self.windows.append((device, term_win))

        # get the device
        target_device = get_device(device)

        # Output area (read-only text box with scrollbar)
        output_frame = ttk.Frame(term_win)
        output_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(output_frame)
        scrollbar.pack(side="right", fill="y")

        output = tk.Text(output_frame, wrap="word", bg="black", fg="white", insertbackground="lime")
        target_device.set_terminal_output(output)
        output.pack(fill="both", expand=True)
        output.insert("end", "<BEGINNING OF INPUT STREAM>\n")

        for stdout_line in target_device.main_stdout:
            output.insert("end", f"{stdout_line}\n")

        output.insert("end", f"<NEW SESSION>\n", "user_in")

        output.config(state="disabled", yscrollcommand=scrollbar.set)
        scrollbar.config(command=output.yview)

        # Input field
        input_frame = ttk.Frame(term_win)
        input_frame.pack(fill="x", padx=5, pady=5)

        input_var = tk.StringVar()
        input_entry = tk.Entry(input_frame, textvariable=input_var, bg="black", fg="white", insertbackground="white")
        input_entry.pack(side="left", fill="x", expand=True)

        output.tag_configure("user_in", foreground="green2")
        output.tag_configure("raw_out", foreground="SkyBlue1")

        def send_command(event=None):
            command = input_var.get().strip()
            if command:
                output.config(state="normal")
                output.insert("end", f">> {command}\n", "user_in")
                output.config(state="disabled")
                output.see("end")
                
                target_device.pipe_conn.send(command + "\n")
                input_var.set("")

        input_entry.bind("<Return>", send_command)

        submit_btn = ttk.Button(input_frame, text="Send", command=send_command)
        submit_btn.pack(side="right", padx=5)

        input_entry.focus_set()


if __name__ == "__main__":
    app = DeviceApp()
    app.after(1000, app.update_devices)
    app.after(50, app.update_stdouts)
    app.mainloop()
