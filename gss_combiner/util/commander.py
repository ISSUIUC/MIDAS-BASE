from util.feather_subprocess import FeatherSubprocess
"""
A class for sending commands to a specific device and stuff
"""
class CommandSender:
    def __init__(self, devices: list[FeatherSubprocess]):
        self.devices = devices

    def send_telemetry_command(self, command: str, stage: str, args: str):
        # We can just write to all devices?
        for device in self.devices:
            if device.type != "FEATHER DUO":
                continue
            device.add_to_stdout(f"{command} {stage} {args}")
        # Then write to the device



