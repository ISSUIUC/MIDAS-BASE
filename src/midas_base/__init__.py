import tkinter as tk
from tkinter import ttk
import multiprocessing
import subprocess
from pathlib import Path
import sys
import os
from serial.tools.list_ports import comports
import time
from midas_base.gss_combiner.util.feather_subprocess import FeatherSubprocess
from midas_base.gss_combiner.util.commander import CommandSender
from midas_base.gss_combiner.hw.hwtypes import HwType
import serial
import json
import datetime
import csv
from pathlib import Path
import threading
import sys
import queue
from midas_base.gss_combiner.tabs.config import _build_config_tab
from midas_base.gss_combiner.tabs.connect import _build_connect_tab
from midas_base.gss_combiner.tabs.ejection_test import _build_ejection_test_tab
from midas_base.gss_combiner.tabs.telem import _build_telem_tab
from midas_base.gss_combiner.tabs.export import _build_export_tab

# TODO: 
# ADD this import line (right after the export import). The new Console tab
# lives in its own file:
#     from midas_base.gss_combiner.tabs.consoles import _build_consoles_tab

from tkinter import filedialog
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from midas_base.gss_combiner.util.canvas import Canvas, TELEM_DATA_KEYS, REVERSE_TELEM_DATA_KEYS

from midas_base.gss_combiner.tabs.home import _build_home_tab
import webbrowser

def get_feather_duo_ports():
    """
    Gets the ports of connected Feather Duos

    Returns:
        list: list of connected Feather Duos
    """
    FEATHER_DUO_PID = 4097
    return [port.device for port in comports() if port.pid == FEATHER_DUO_PID]

# TODO: 
# ADD a second function right below this one, named get_all_serial_ports().
# It should return every serial port on the system, not just Feather Duos.
# Same shape as get_feather_duo_ports, but no PID filter:
#     return [port.device for port in comports()]

def get_all_serial_ports():
    return [port.device for port in comports()]

devices: list[FeatherSubprocess] = [] #check if empty list works

def get_device(port):
    # get the device
    for _device in devices:
        if _device.get_port() == port:
            return _device
    return None

# TODO: 
# ADD a third module-level function right below get_device, named
# get_all_devices(). It just returns the global `devices` list so callers
# can iterate over every device without reaching for the global name.
# The Console tab builder needs this as its `get_devices` argument.

def get_all_devices():
    return devices

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

        # Graphing stuff
        self.input_file = None
        self.canvas = None

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

        # TODO
        # Wrap everything below (up to but NOT including the final
        # self.after(200, self.update_devices) line) in a try/except.
        # On exception `e`, print:
        #     print(f"[!] update_devices encountered an error: {e}")
        # This keeps a single flaky port from killing the whole polling
        # loop. The self.after(200, ...) call stays OUTSIDE the try so it
        # always runs and re-schedules the next poll.

        # Remove old ports that aren't connected

        try:
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
        except AssertionError as e:
            print(f"[!] update_devices encountered an error: {e}")

        
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
   
    # TODO:
    # ADD a new method called update_console_streams(self) right here,
    # between update_stdouts and parser_midas.
    #
    # Purpose: continuously drain whatever each device has sent back over
    # serial into its main_stdout history. This runs no matter which
    # device the Console tab currently has selected, so switching devices
    # in that tab always shows what actually happened while you weren't
    # looking.
    #
    # Algorithm:
    #     for each device in get_all_devices():
    #         if the device is not ready for console, or it has errored,
    #             continue
    #         try to read lines via device.read_serial_lines()
    #         for each line, feed it into the device's stdout history
    #             (via device.add_to_stdout)
    #         on exception, just log a message - the read failed
    #     schedule the next run: self.after(150, self.update_console_streams)
    #
    # Note the interval is different from update_stdouts (50ms) - console
    # reads can be slower, so 150ms gives the serial hardware a chance to
    # produce something between calls without hammering it.
    
    def update_console_streams(self):
        for device in get_all_devices():
            if not device.is_ready_for_console() or device.has_errored:
                continue

            try:
                lines = device.read_serial_lines()
                serial_no = -1
                for line in lines:
                    try:
                        serial_no = int(line)
                    except:
                        continue
                if serial_no == -1:
                    return
                else: 
                    device.add_to_stdout(line)
                    
            except Exception as e:
                print(f"[{device.get_port()}] Failed to read console stream: {e}")

        self.after(150, self.update_console_streams)      


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

        elif cmd.startswith("serial ") and cmd.endswith(" get"):
            # e.g. cmd = "serial 0 get", val = 008
            self._radio_serials = getattr(self, '_radio_serials', {})
            self._radio_serials[cmd.split()[1]] = val
            self._ejection_stage_dropdown['values'] = list(self._radio_serials.values())


    def update_device_list(self):
        # Clear treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Build a filtered list first so ports that never identified don't
        # show up. Something like:
        #     visible_devices = [d for d in devices if not d.is_unidentified()]
        # and then loop over visible_devices instead of devices below.
        # Same idea as the filter in update_devices - just don't touch
        # anything the user can't act on.

        visible_devices = [d for d in devices if not d.is_unidentified()]

        # Re-insert updated device info
        for _device in visible_devices:
            device = _device.to_dict()
            
            # Change the disabled check: it used to trigger on both "NONE"
            # and "IDENTIFYING...". Now it should only trigger on
            # "IDENTIFYING..." - unidentified devices are already filtered
            # out above, so anything still showing NONE is a real device
            # we just haven't reached yet, and shouldn't be greyed out.
            
            tags = ("disabled",) if device["status"].upper() in ("IDENTIFYING...") else ()
            if _device.is_online():
                tags = tags + ("connected",)
            if _device.has_errored:
                tags = tags + ("errored",)
            new_item = self.tree.insert(
                "", "end",
                # Drop the server column from the values tuple. New tuple:
                #     (device["port"], device["name"], device["status"], device["meta"])
                values=(device["port"], device["name"], device["status"], device["meta"]),
                tags=tags
            )

            if _device.get_port() == self.selected_device:
                # Add a comment here explaining WHY this line matters (in your own words):
                # the tree was just rebuilt from scratch, so the old item
                # id (and its native selection state) no longer exists.
                # Re-adding by the fresh item id restores the highlight
                # without changing what self.selected_device says.
                self.tree.selection_add(new_item)


        # Update stats
        # Change len(devices) to len(visible_devices) so the count matches
        # the rows actually shown in the tree.
        self.total_label.config(text=f"Total Devices: {len(visible_devices)}")
        # Same story for the online count: iterate over visible_devices
        # instead of devices.
        online_count = sum(1 for d in visible_devices if d.to_dict()["status"].lower() == "online")
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
        # Add a new frame for the Console tab, same style as the others:
        #     consoles_tab = ttk.Frame(self.notebook)

        self.notebook.add(home_tab, text="HOME")
        self.notebook.add(config_tab, text="CONFIG")
        self.notebook.add(test_tab, text="EJECTION_TEST")
        self.notebook.add(connect_tab, text="CONNECT ")
        self.notebook.add(telem_tab, text="TELEM")
        self.notebook.add(export_tab, text="EXPORT")
        # Add the Console tab to the notebook, right after EXPORT:
        #     self.notebook.add(consoles_tab, text="CONSOLE")

        # Default to MIDAS BASE
        self.notebook.select(home_tab)


        _build_connect_tab(self, connect_tab, devices)
        _build_config_tab(self, config_tab)
        
        _build_ejection_test_tab(self, test_tab, "TEST", devices)
        _build_telem_tab(self, telem_tab, "TELEM")
        _build_export_tab(self, export_tab)
        _build_home_tab(self, home_tab, devices)
        # Call the new Console tab builder here, after home_tab, passing
        # the get_all_devices function (not the devices list itself, since
        # the list object gets rebound on every update_devices tick):
        #     _build_consoles_tab(self, consoles_tab, get_all_devices)

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

        # Simplify the guard. The old version checked both `not target_device`
        # and `not target_device.pipe_conn`. Since _send_and_wait will fail
        # cleanly if there's no pipe, just check `if not target_device:`.

        if not target_device or not target_device.pipe_conn:
            print("No device connected")
            return

        # DELETE this line - no more raw pipe writes here, everything goes
        # through _send_and_wait now.
        target_device.pipe_conn.send("echo 0\n")

        cruise_lockout, main_alt, pyro_fire_t, serial_no, midas_telem_freq = self.get_globals()
        # Simplify: ternary instead of the if/else block
        #     cruise_lockout_num = 1 if cruise_lockout else 0
        cruise_lockout_num = 0
        if cruise_lockout:
            cruise_lockout_num = 1

        # Replace this whole GLOBALS section with a loop over a list of
        # command strings. Each command goes through self._send_and_wait
        # (a new helper - see below) instead of the old pipe_conn.send +
        # time.sleep(.2) pattern. The list should be:
        #
        #     [
        #         f"serial set {serial_no}",
        #         f"frequency set {midas_telem_freq}",
        #         f"fsm threshold CRUISE_LOCKOUT_EN {cruise_lockout_num}",
        #         f"fsm threshold MAIN_ALT {main_alt}",
        #         f"fsm threshold PYRO_FIRE_T {pyro_fire_t}",
        #     ]
        #
        # Then iterate: for cmd in that_list: self._send_and_wait(target_device, cmd)
        
        # GLOBALS_NEW
        commands_to_send = [f"serial set {serial_no}",
                            f"frequency set {midas_telem_freq}",
                            f"fsm threshold CRUISE_LOCKOUT_EN {cruise_lockout_num}",
                            f"fsm threshold MAIN_ALT {main_alt}",
                            f"fsm threshold PYRO_FIRE_T {pyro_fire_t}"
                            ]
        for cmd in commands_to_send:
            self._send_and_wait(target_device, cmd)


        
        
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
        # Same treatment here. Replace the pipe_conn.send + time.sleep
        # pattern with self._send_and_wait. Also simplify the ENABLE
        # branch: instead of the if statement setting varnum, use
        #     varnum = 1 if data[field] else 0
        # then build the command string once.
        # ___waiting on _send_and_wait method to finish___
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

        # Same simplification as flash_midas: drop the pipe_conn check
        # from the guard, keep only `if not target_device: return`.
        if not target_device:
            print("No device connected")
            return

        # Replace the whole body below with a call to _send_and_wait
        # followed by two loops:

        # DELETE this raw pipe send - the new version goes through
        # _send_and_wait("echo 0").
        target_device._send_and_wait("echo 0\n")

        globals_to_load = [
                ("serial get",                      self.serial_no),
                ("frequency get",                   self.midas_telem_freq),
                ("fsm threshold CRUISE_LOCKOUT_EN", self.cruise_lockout),
                ("fsm threshold MAIN_ALT",          self.main_alt),
                ("fsm threshold PYRO_FIRE_T",       self.pyro_fire_t),
            ]


        for cmd, var in globals_to_load:
            self._send_and_wait(target_device, cmd)

        # CHANNELS
        # Same treatment. For each channel and each field, build the
        # command "fsm {ch} {field}", call _send_and_wait, and if the
        # response isn't None, feed it to parser_midas. No more raw
        # pipe_conn.send + time.sleep pattern.
        
        for ch in self.channels:
            for field in self.fields:
                cmd = f"fsm {ch} {field}\n"
                self._send_and_wait(target_device, cmd)
                time.sleep(.2)

    # ADD a new helper method right here, between load_midas and on_select.
    # Name it _send_and_wait(self, device, cmd, timeout=1.5).
    #
    # It sends one command and waits for the board's response, replacing
    # all the pipe_conn.send + time.sleep(.2) patterns.
    #
    # Algorithm:
    #     - flush stale bytes: call device.read_serial_lines() and throw
    #       the result away, so we don't pick up leftovers from before
    #     - send the command: device.send_serial_msg((cmd + "\n").encode())
    #     - compute a deadline: time.time() + timeout
    #     - while now < deadline:
    #           read lines via device.read_serial_lines()
    #           for each line, strip it
    #           if the line is non-empty and "done" is not in it:
    #               return the line
    #     - if we got here, the deadline passed. Print a timeout error.
    #     - return None (so callers can check and skip on no response)
    def _send_and_wait(self):
        device.read_serial_lines()
        
        return

    def on_select(self, event):
        selected = self.tree.selection()

        # Simplify: bail early if nothing's selected, then the rest of the
        # function doesn't need to be indented inside an if-block.
        #     if not selected:
        #         return
        #     item = selected[0]
        #     ... rest at the top level

        if selected:
            item = selected[0]
            tags = self.tree.item(item, "tags")

            if "disabled" in tags:
                # Prevent selection visually
                self.tree.selection_remove(item)
                self.selected_device = None
                # Guard the device_label update with hasattr - the label
                # only exists if the connect tab has been built.
                #     if hasattr(self, "device_label"):
                #         self.device_label.config(text="Select a device")
                self.device_label.config(text="Select a device")
                # DELETE the four lines below that disable connect_btn,
                # inspect_btn, and do_log_checkbox. None of those widgets
                # live in this tab anymore.

            values = self.tree.item(item, "values")
            is_same_select = values[0] == self.selected_device
            self.selected_device = values[0]
            self.device_label.config(text=f"Selected: {self.selected_device}")
            # DELETE the connect_btn and do_log_checkbox state lines here too.
            self.connect_btn.config(state="normal")
            self.do_log_checkbox.config(state="normal")

            _device = get_device(self.selected_device)

            # DELETE the whole HwType-radio-button block below. All the
            # `if _device.type == HwType.XXX:` checks that enable/disable
            # the radio buttons and set stage_sel - none of that exists
            # in this tab anymore.
            if not is_same_select:
                if _device.type == HwType.MIDAS_MINI:
                    self.radio1.config(state="normal")
                    self.radio2.config(state="normal")
                    self.radio3.config(state="disabled")
                    self.mini.config(state="disabled")
                    self.stage_sel.set("sustainer")

                if _device.type == HwType.FEATHER_DUO:
                    self.radio1.config(state="disabled")
                    self.radio2.config(state="disabled")
                    self.radio3.config(state="normal")
                    self.stage_sel.set("duo")

                if _device.type == HwType.MIDAS_MINI:
                    self.radio1.config(state="disabled")
                    self.radio2.config(state="disabled")
                    self.radio3.config(state="disabled")
                    self.mini.config(state="normal")
                    self.stage_sel.set("midas")

                # DELETE this online branch too - no ip_entry, no stage_sel
                # setter. The whole "if _device.is_online():" block goes.
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
    
    def open_input_file(self):
        self.input_file = self.upload_file()
        if not self.input_file:
            return
        
        
        self.input_file_thing.config(text=f"Uploaded file: {self.input_file}")
        data = []
        if self.input_file.endswith(".txt"):
            with open(self.input_file, "r") as f:
                for line in f:
                    try:
                        clean_line = line[6:].replace("'", '"')
                        data.append(json.loads(clean_line))
                    except:
                        continue
            plt.cla()
            
            data = [dp["value"] 
                    for dp in data
                    if "value" in dp]
            
            self.data = data
            # Get the value from each data point
            self.update_export_frame()
            self.input_start_frame.config(to=len(self.data))
        elif self.input_file.endswith(".telem"):
            with open(self.input_file, "r") as f:
                for line in f:
                    try:
                        data.append(json.loads(line))
                    except:
                        continue
            plt.cla()
            self.data = []
            times = []
            for i, dp in enumerate(data):
                data_thing = dp["data"]["value"]
                time_stamp = dp["data"]["unix"]
                time_stamp_normalized = time_stamp - data[0]["data"]["unix"]
                self.data.append(data_thing)
                self.data[i]["unix"] = time_stamp_normalized
                times.append(time_stamp_normalized)
            
            self.input_start_frame.config(to=max(times))
            self.update_export_frame()
        else:
            print("Invalid file. Please try again.")
        self.telem_dropdown_changed() # refresh graph if applicable
    
    
    def update_export_frame(self):
        if self.input_file:
            self.export_file_button.configure(state="normal")
            self.no_input_file_label.configure(text="Export your file here")


        


    def export_data(self):
        filename = filedialog.asksaveasfilename()
        with open(filename, "w", newline="") as f:
            csvwriter = csv.writer(f)
            headers = ["Time"] + list(self.data[0].keys())
            csvwriter.writerow(headers)
            for i, dp in enumerate(self.data):
                row = []
                row.append(i)
                for header in headers[1:]:
                    row.append(dp.get(header) if dp.get(header) is not None else "")
                csvwriter.writerow(row)

        self.telem_frame.update_idletasks()
    
    
    def telem_dropdown_changed(self, event=None):
        new_val = self.telem_dropdown.get()
        print(f"the new val is {new_val}")
        data_key = REVERSE_TELEM_DATA_KEYS.get(new_val)
        if data_key is None:
            return
        
        if self.canvas is not None:
            self.canvas.destroy(plt)
        
        input_start_frame = 0
        try:
            input_start_frame = int(self.input_start_frame.get())
        except:
            print("Please input a valid number.")
        
        ydata = [dp[data_key]
                    for dp in self.data
                    if data_key in dp]
        xdata = [i for i in range(len(ydata))]
        if self.data[0].get("unix") is not None:
            xdata = [dp["unix"] for dp in self.data]
        actual_xdata = []
        actual_ydata = []
        for x, y in zip(xdata, ydata):
            if (x >= input_start_frame):
                actual_xdata.append(x)
                actual_ydata.append(y)

        
        new_canvas = Canvas(plt, self.telem_frame, actual_xdata, actual_ydata, **TELEM_DATA_KEYS[data_key])
        new_canvas.plot(plt)
        self.canvas = new_canvas
        




#def set_terminal_output(self, outpt):
       # self.__terminal_outputs.append(outpt)

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
    def upload_file(self):
        # Opens a file dialog and captures the selected path
        file_path = tk.filedialog.askopenfilename(
            title="Select a file",
            filetypes=[("Telem Files", "*.telem *.txt"), ("All files", "*.*")]
        )
        if file_path:
            print(f"Selected file: {file_path}")
            return file_path

#   Lowkey wont need these serial things anymore
    def load_serial_no(self):
        if self.selected_device is None:
            return False
        device = get_device(self.selected_device)
        if device is None:
            return False
        device.send_serial_msg("serial get\n".encode())
        time.sleep(0.2)
        data = device.read_serial_lines()
        serial_no = -1
        for line in data:
            try:
                serial_no = int(line)
            except:
                continue
        if serial_no == -1:
            return
        self.serial_no.set(str(serial_no).zfill(3))
    def set_serial_no(self):
        if self.selected_device is None:
            return False
        device = get_device(self.selected_device)
        if device is None:
            return False
        try:
            serial_no = int(self.serial_no.get())
        except:
            return False
        device.send_serial_msg(f"serial set {serial_no}\n".encode())
        time.sleep(0.2)
        self.load_serial_no()



def main() -> None:
    app = DeviceApp()
    app.after(1000, app.update_devices)
    app.after(50, app.update_stdouts)
    # Add one more scheduled call right here, to kick off the console
    # stream loop that drains serial output for every connected device:
    #     app.after(150, app.update_console_streams)
    app.mainloop()