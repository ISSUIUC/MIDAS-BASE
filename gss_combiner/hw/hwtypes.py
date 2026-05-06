from enum import StrEnum, auto

"""
Hardware types
"""
class HwTypes(StrEnum):
    MIDAS_MINI = "MIDAS MINI"
    FEATHER_M0 = "FEATHER M0"
    FEATHER_DUO = "FEATHER DUO"

    def get_hardwares():
        return [e for e in HwTypes]

class Hardware:
    def __init__(self):
        ...
