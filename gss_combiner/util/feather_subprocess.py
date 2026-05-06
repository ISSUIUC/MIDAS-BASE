import time
import serial

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
        self.type: str = "UNKNOWN"
        self.__is_active = False
        self.proc = None
        self.pipe_conn = None
        self.__ip = ""
        self.should_log = False
        self.stage_sel = ""

        self.has_errored = False

        self.main_stdout = []
        self.__terminal_outputs = []

        print(f"Initializing new device on {self.__port}")
        self.check_type()
    
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
            outpt.config(state="normal")
            msg_str: str = str(msg)
            if msg_str.startswith("[F]"):
                outpt.insert("end", f"{msg_str}\n", "raw_out")
            else:
                outpt.insert("end", f"{msg_str}\n")
            outpt.config(state="disabled")
            outpt.see("end")

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

            self.__serial.write("IDENT\n".encode())

            time.sleep(0.5)
            data = self.__serial.read_all().decode().splitlines()
            for line in data:
                print(f"[{self.__port}] {line}")
                if line.startswith("IDENT_RESPONSE:"):
                    ident_value = line[15:]
                    
                    if ident_value == "FEATHER_M0":
                        self.type = "FEATHER M0"
                        self.stat = "OFFLINE"
                        self.__serial.close()
                        self.__serial = None
                        return
                    
                    if ident_value == "FEATHER_DUO":
                        self.type = "FEATHER DUO"
                        self.stat = "OFFLINE"
                        self.__serial.close()
                        self.__serial = None
                        return
                    
                    if ident_value == "MIDAS_MINI":
                        self.type = "MIDAS MINI"
                        self.stat = "OFFLINE"
                        return
            
            self.type = "UNKNOWN"
            self.stat = "NONE"
            self.__serial.close()
            self.__serial = None

    def is_online(self):
        return self.stat.lower() == "online"
    
    def clean_visual(self):
        self.set_ip("")
        self.stat = "OFFLINE"
        self.proc = None
        self.main_stdout = []


    def cleanup(self):
        print(f"[{self.__port}] FeatherSubprocess.cleanup invoked!")
        if self.pipe_conn:
            self.pipe_conn.send("kill\n")
            
        self.clean_visual()

        if self.pipe_conn:
            self.pipe_conn.close()
        self.pipe_conn = None



    def get_port(self):
        return self.__port
    
    def get_serial(self):
        return self.__serial

    def reset(self):
        if self.__serial:
            self.__serial.close()


    def to_dict(self):
        return {"name": self.type, "port": self.__port, "status": self.stat, "server": self.__ip, "meta": self.meta}

