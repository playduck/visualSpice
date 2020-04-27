# Config.py
# by Robin Prillwitz
# 27.4.2020
#

import sys
from pathlib import Path

def getResource(path):
    if getattr(sys, 'frozen', False):
        root = Path(sys._MEIPASS) # sys has attribute if it's frozen
    else:
        root = Path()

    return str(root / path)
