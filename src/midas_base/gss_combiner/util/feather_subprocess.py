import time
# Add an import for `threading` here. We'll need it to run the
# identification step on a background thread instead of blocking the GUI.
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

        print(f"Initializing new device on {self.__port}")
        # Don't call check_type() directly here anymore. The identification
        # step sleeps for several seconds while it talks to real hardware,
        # and doing that on the main thread froze the entire GUI every time
        # a new device appeared. Instead:
        #
        #   1. Set self.stat to "IDENTIFYING..." immediately, so the device
        #      still shows up right away in the UI (just greyed out).
        #   2. Create a daemon thread whose target is self.check_type, and
        #      start it. Daemon so it won't keep the program alive if
        #      something goes wrong.
        #
        # Store the thread on the instance (e.g. self.__identify_thread)
        # in case we ever want to join it later.
        self.check_type()
    
    def get_stat(self):
        return self.__ip, self.should_log

    def set_terminal_output(self, outpt):
        self.__terminal_outputs.append(outpt)

    # Add a new method here, something like remove_terminal_output(self, outpt).
    # It should check whether the given widget is in self.__terminal_outputs
    # and, if so, remove it. This is used when the Console tab switches to a
    # different device - we don't want to keep shoving lines into a Text
    # widget that's no longer on screen.

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
            # Add an `elif` branch here, between the "[F]" check and the
            # final `else`. It should trigger when the message starts with
            # ">> " - that's the prefix we use for commands the user typed
            # themselves and we're echoing locally. Insert the line with the
            # tag "user_in" instead of no tag, so the console can style our
            # own input differently from what the board sends back.
            else:
                outpt.insert("end", f"{msg_str}\n")
            outpt.config(state="disabled")
            outpt.see("end")

    # Add two class-level constants right before check_type():
    #
    #   IDENT_BOOT_DELAY = 3
    #       How long to wait after opening the port before sending the
    #       first "ident". Most boards reset when the port opens and need a
    #       few seconds to finish booting before they'll respond to anything.
    #
    #   IDENT_MAX_ATTEMPTS = 3
    #       How many times to (re)send "ident" before giving up on a port
    #       that never answers, so one silent board can't hang this forever.

    def check_type(self):
        print("Check type invoked on ", self.__port)
        if self.__is_active:
            return # This will be taken over by another process already 
        
        port_taken, self.__serial = is_port_taken(self.__port)
        if port_taken:
            self.stat = "NONE"
            self.type = "UNKNOWN"
            print("Sad!")
            # Add an explicit `return` here. In the old version this branch
            # fell straight through into the identification code below even
            # though the port was already taken, which was wrong.
        else:
            self.stat = "IDENTIFYING..."
            self.type = "UNKNOWN"
            time.sleep(0.5)

            self.__serial.write("ident\n".encode())

            time.sleep(0.5)

            #How to send a shell command to device without first being connected to it. Lets try!!
            # self.__serial.write("ident\r".encode()) #Maybe this could work im not sure!!

            time.sleep(0.5)
            data = self.__serial.read_all().decode().splitlines()
            break_out_of_while = False
            while not break_out_of_while:
                for line in data:
                    print(f"[{self.__port}] {line}")
                    if line.startswith("IDENT_RESPONSE:"):
                        ident_value = line[15:]
                        
                        if ident_value == "FEATHER_M0":
                            self.type = HwType.FEATHER_M0
                            self.stat = "OFFLINE"
                            # Delete the two lines below. The serial handle
                            # is now kept open after identification so the
                            # Console tab can read/write it directly, so
                            # there's no reason to close it here.
                            self.__serial.close()
                            self.__serial = None
                            return
                        
                        if ident_value == "FEATHER_DUO":
                            self.type = HwType.FEATHER_DUO
                            self.stat = "OFFLINE"
                            # Delete the two lines below too, same reason.
                            self.__serial.close()
                            self.__serial = None
                            return
                        
                        if ident_value == "MIDAS_MINI":
                            self.type = HwType.MIDAS_MINI
                            self.stat = "OFFLINE"
                            return
                    elif line.startswith("<done> 3"):
                        time.sleep(0.5)
                        self.__serial.write("ident\n".encode())
                        # Add another time.sleep(0.5) right after the write
                        # above, to give the board a moment to respond
                        # before the next read.
                        continue
                    else:
                        break_out_of_while = True
            
            self.type = "UNKNOWN"
            self.stat = "NONE"
            # This close/serialize-to-None pair is going away - cleanup now
            # happens in a dedicated block at the very end of the rewritten
            # check_type (see the big note below).
            self.__serial.close()
            self.__serial = None

    
    # check_type() gets rewritten. Here's the shape of it, in words:
    #
    # 1. Delete everything inside the `else:` branch (the block that
    #    starts with `self.stat = "IDENTIFYING..."` and ends with
    #    `self.__serial = None`).
    #
    # 2. Replace it with a `try:` block. The very first thing inside the
    #    try should be a sleep equal to FeatherSubprocess.IDENT_BOOT_DELAY,
    #    so the board has time to finish booting.
    #
    # 3. After that sleep, loop up to FeatherSubprocess.IDENT_MAX_ATTEMPTS
    #    times. Each attempt should:
    #       - Write "ident\n" to the serial port.
    #       - Sleep half a second.
    #       - Read everything back and split it into lines. When decoding,
    #         pass errors="ignore" so a junk byte can't crash us.
    #       - If nothing came back, `continue` to the next attempt instead
    #         of spinning forever on an empty list.
    #       - Otherwise, walk through the lines exactly like before - same
    #         "IDENT_RESPONSE:" handling and same "<done> 3" handling,
    #         including the extra half-second sleep after the re-write in
    #         the "<done> 3" branch. On a successful match, still return
    #         immediately WITHOUT closing the serial port.
    #
    # 4. After the loop finishes (meaning we ran out of attempts without a
    #    usable response): set self.type to "UNKNOWN", self.stat to "NONE",
    #    and - only if self.__serial is not None - close it and set it back
    #    to None.
    #
    # 5. Add an `except (serial.SerialException, OSError) as e:` clause.
    #    A write/read timeout or a port that vanishes mid-identify should
    #    never take down the polling loop. Inside the except:
    #       - Print something like "[<port>] Failed to identify device: <e>".
    #       - Set type to "UNKNOWN" and stat to "NONE".
    #       - If self.__serial is not None, close it inside a nested
    #         try/except (so a second failure during close doesn't
    #         propagate), then set it to None.
    # 

    def is_online(self):
        return self.stat.lower() == "online"

    # Add two new methods right after is_online:
    #
    # is_unidentified(self):
    #     Return True only when self.type == "UNKNOWN" and self.stat ==
    #     "NONE". That combination means the port was checked and never
    #     produced a usable ident response - a Bluetooth virtual port, an
    #     unrelated device, or a board that just didn't answer. The UI
    #     hides these so they don't clutter the device list.
    #
    # is_ready_for_console(self):
    #     Return True once identification has fully finished (success or
    #     failure) AND self.get_serial() is not None. In other words: stat
    #     is not "IDENTIFYING..." and we actually have a serial handle.
    #     This is what tells the Console tab it's safe to grab the port and
    #     read/write directly. While check_type is still running on its
    #     background thread, nothing else should touch the port.

    def is_ready_for_console(self):
        if not self.is_unidentified() and self.get_serial() is not None:
            return True
        
        

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

        # Call self.reset() down here. Now that we keep the serial handle
        # open after identification (so the console can use it), we have
        # to explicitly release it on cleanup - otherwise it leaks every
        # time a device is unplugged.

    def get_port(self):
        return self.__port
    
    def get_serial(self):
        return self.__serial

    def reset(self):
        # Change this method so it: (a) checks that self.__serial is
        # truthy, (b) wraps the close() call in a try/except so a close
        # failure doesn't blow up the caller, and (c) sets self.__serial
        # back to None afterwards. The original left the handle dangling
        # after close and didn't guard against exceptions.
        if self.__serial:
            self.__serial.close()


    def to_dict(self):
        return {"name": self.type, "port": self.__port, "status": self.stat, "server": self.__ip, "meta": self.meta}

    def send_serial_msg(self, msg):
        # Add a None check at the top. If self.__serial is None, raise a
        # serial.SerialException with a helpful message that includes the
        # port name. In the old version, calling this on a closed port
        # raised a bare AttributeError, which was much harder to diagnose.
        # Only after that check should we actually write.
        self.__serial.write(msg)

    def read_serial_lines(self):
        # Two changes here:
        #   1. If self.__serial is None, return an empty list right away.
        #      This can happen during teardown now that we keep the handle
        #      open across identification.
        #   2. Pass errors="ignore" to .decode() so a stray non-UTF8 byte
        #      from the board doesn't crash the read.
        data = self.__serial.read_all().decode().splitlines()
        return data