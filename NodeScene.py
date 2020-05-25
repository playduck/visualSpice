# NodeScene.py
# by Robin Prillwitz
# 24.4.2020
#

from PyQt5 import QtCore, QtWidgets
from Nodz import nodz_main

import Config
import NodeItem

class NodeScene(nodz_main.Nodz):
    def __init__(self):
        super().__init__(None, configPath=Config.getResource("assets/nodz_config.json"))
        # self.scene = nodz_main.Nodz(None)
        self.initialize()
        self.gridVisToggle = True
        self.gridSnapToggle = False

        # self.fc.connectTerminals(self.fc.inputNode, self.fc.outputNode)
