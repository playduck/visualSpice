# Config.py
# by Robin Prillwitz
# 27.4.2020
#

import os
import sys
from pathlib import Path

def getResource(path):
    if getattr(sys, 'frozen', False):
        root = Path(sys._MEIPASS) # sys has attribute if it's frozen
    else:
        root = Path()

    return str(root / path)

COLORS = [
    [192, 58, 94],
    [312, 58, 94],
    [72, 58, 94]
]

TEMP_DIR = os.path.abspath("./temp") + "/"
template = "./ltspice_template.net"
simulator = "LTSPICE"
