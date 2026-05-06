from enum import StrEnum, auto

"""
Hardware types
"""
class HwType(StrEnum):
    MIDAS_MINI = "MIDAS MINI"
    FEATHER_M0 = "FEATHER M0"
    FEATHER_DUO = "FEATHER DUO"
    UNKNOWN = "UNKNOWN"

    def get_hardwares():
        return [e for e in HwType]

class HardwareInterface:
    def __init__(self):
        ...
