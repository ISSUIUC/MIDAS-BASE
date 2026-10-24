import time
import threading
import serial
from midas_base.gss_combiner.hw.hwtypes import HwType

def is_port_taken(port):
    """
    Checks if a serial port is currently in use.

    Args:
        port (str): The name of the serial port to check (e.g., 'COM3' or '/dev/ttyUSB0').

    Returns:
        bool: True if the port is taken, False otherwise.
    """
    try:
        ser = serial.Serial()
        ser.port = port
        ser.write_timeout = 1
        ser.timeout = 2
        ser.dtr = False
        ser.rts = False
        ser.open()
        return False, ser  # Port is free
    except serial.SerialException as e:
        return True, None

class FeatherSubprocess:
    MAXIMUM_STDOUT_LINES = 300
    def __init__(self, port):
        self.__port: str = port
        self.__serial = None
        self.meta: str = ""
        self.stat: str = "NONE"
        self.type: HwType = "UNKNOWN"
        self.__is_active = False
        self.proc = None
        self.pipe_conn = None
        self.__ip = ""
        self.should_log = False
        self.stage_sel = ""

        self.has_errored = False

        self.main_stdout = []
        self.__terminal_outputs = []

        self._serial_buffer = ""

        #TODO: NEW STUFF
        # New properties for lifecycle and race condition management
        self.missing_polls = 0
        self._identify_cancelled = threading.Event()
        self._serial_lock = threading.Lock()

        print(f"Initializing new device on {self.__port}")
        
        # Identification uses a background thread to prevent blocking
        # the main process during the sleep/retry cycles.
        # self.stat = "IDENTIFYING..."
        self.check_type()

        # self.__identify_thread = threading.Thread(target=self.check_type, daemon=True)
        # self.__identify_thread.start()

    def get_stat(self):
        return self.__ip, self.should_log

    def set_terminal_output(self, outpt):
        self.__terminal_outputs.append(outpt)

    def set_ip(self, ip):
        self.__ip = ip

    def add_to_stdout(self, msg):
        self.main_stdout.append(msg)

        if len(self.main_stdout) > FeatherSubprocess.MAXIMUM_STDOUT_LINES:
            self.main_stdout = self.main_stdout[1:]

        for outpt in self.__terminal_outputs:
            outpt.configure(state="normal")
            msg_str: str = str(msg)
            if msg_str.startswith("[F]"):
                outpt.insert("end", f"{msg_str}\n", "raw_out")
            # elif msg_str.startswith(">> "):
            #     outpt.insert("end", f"{msg_str}\n", "user_in")
            else:
                outpt.insert("end", f"{msg_str}\n")
            outpt.configure(state="disabled")
            outpt.see("end")

    IDENT_BOOT_DELAY = 3
    IDENT_MAX_ATTEMPTS = 3

    def check_type(self):
        print("Check type invoked on ", self.__port)
        if self.__is_active:
            return # This will be taken over by another process already
        
        port_taken, self.__serial = is_port_taken(self.__port)
        if port_taken:
            self.stat = "NONE"
            self.type = "UNKNOWN"
            print("Sad!")
        else:
            self.stat = "IDENTIFYING..."
            self.type = "UNKNOWN"
            time.sleep(1.5)
            self.__serial.write("ident\n".encode())

            time.sleep(0.5)
            data = self.__serial.read_all().decode().splitlines()
            for line in data:
                print(f"[{self.__port}] {line}")
                if line.startswith("IDENT_RESPONSE:"):
                    ident_value = line[15:]
                    
                    if ident_value == "FEATHER_M0":
                        self.type = "FEATHER M0"
                        self.stat = "OFFLINE"
                        # self.__serial.close()
                        # self.__serial = None
                        return
                    
                    if ident_value == "FEATHER_DUO":
                        self.type = "FEATHER DUO"
                        self.stat = "OFFLINE"
                        # self.__serial.close()
                        # self.__serial = None
                        return

                    if ident_value == "MIDAS_MINI":
                        self.type = "MIDAS MINI"
                        self.stat = "OFFLINE"
                        # self.__serial.close()
                        # self.__serial = None
                        return
            
            self.type = "UNKNOWN"
            self.stat = "NONE"
            self.__serial.close()
            self.__serial = None

    def is_online(self):
        return self.stat.lower() == "online"

    def is_unidentified(self):
        return self.type == "UNKNOWN" and self.stat == "NONE"
        
    def clean_visual(self):
        self.set_ip("")
        self.stat = "OFFLINE"
        self.proc = None
        self.main_stdout = []

    def cleanup(self):
        print(f"[{self.__port}] FeatherSubprocess.cleanup invoked!")
        #TODO: NEW STUFF
        self._identify_cancelled.set()  # Signal background thread to stop

        if self.pipe_conn:
            self.pipe_conn.send("kill\n")
            
        self.clean_visual()

        if self.pipe_conn:
            self.pipe_conn.close()
        self.pipe_conn = None

        self.reset()

    def get_port(self):
        return self.__port
    
    def get_serial(self):
        return self.__serial

    def reset(self):
        #TODO: NEW STUFF
        with self._serial_lock:
            if self.__serial:
                try:
                    self.__serial.close()
                except Exception:
                    pass
                self.__serial = None

        # if self.__serial:
        #     try:
        #         self.__serial.close()
        #     except Exception:
        #         pass
        #     self.__serial = None

    def to_dict(self):
        return {"name": self.type, "port": self.__port, "status": self.stat, "server": self.__ip, "meta": self.meta}

    def send_serial_msg(self, msg):
        #TODO: NEW STUFF
        # with self._serial_lock:
        if self.__serial is None:
            raise serial.SerialException(f"No open serial connection on {self.__port}")
        self.__serial.write(msg)

    def read_serial_lines(self):
        #TODO: NEW STUFF
        with self._serial_lock:
            if self.__serial is None:
                return []
            
        raw_data = self.__serial.read_all().decode(errors="ignore")
        if not raw_data:
            return []
            
        # Append new data to our running buffer
        self._serial_buffer += raw_data
        
        lines = []
        # Only extract lines when a newline character guarantees the message is complete
        while '\n' in self._serial_buffer:
            line, self._serial_buffer = self._serial_buffer.split('\n', 1)
            line = line.replace('\r', '') # Clean up the carriage return
            if line:
                lines.append(line)
                
        return lines
