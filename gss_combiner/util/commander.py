from util.feather_subprocess import FeatherSubprocess
"""
A class for sending commands to a specific device and stuff
"""
class CommandSender:
    def __init__(self, devices: list[FeatherSubprocess]):
        self.devices = devices

def send_telemetry_command(command: str, stage: str):
        # We can just write to all devices?

        # Then write to the device
        ...


