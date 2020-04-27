# NodeScene.py
# by Robin Prillwitz
# 24.4.2020
#

from PyQt5 import QtCore, QtWidgets
from Nodz import nodz_main

import Config

class NodeScene(object):
    def __init__(self):
        self.scene = nodz_main.Nodz(None)
        self.scene.loadConfig(filePath=Config.getResource("assets/nodz_config.json"))
        self.scene.initialize()
        self.scene.gridVisToggle = True
        self.scene.gridSnapToggle = False

        # Node A
        nodeA = self.scene.createNode(name='nodeA', preset='node_preset_1', position=None)
        self.scene.createAttribute(node=nodeA, name='Aattr1', index=-1, preset='attr_preset_1',
                            plug=True, socket=False, dataType=str)
        self.scene.createAttribute(node=nodeA, name='Aattr2', index=-1, preset='attr_preset_1',
                            plug=False, socket=False, dataType=int)
        self.scene.createAttribute(node=nodeA, name='Aattr3', index=-1, preset='attr_preset_2',
                            plug=True, socket=True, dataType=int)
        self.scene.createAttribute(node=nodeA, name='Aattr4', index=-1, preset='attr_preset_2',
                            plug=True, socket=True, dataType=str)
        self.scene.createAttribute(node=nodeA, name='Aattr5', index=-1, preset='attr_preset_3',
                            plug=True, socket=True, dataType=int, plugMaxConnections=1, socketMaxConnections=-1)
        self.scene.createAttribute(node=nodeA, name='Aattr6', index=-1, preset='attr_preset_3',
                            plug=True, socket=True, dataType=int, plugMaxConnections=1, socketMaxConnections=-1)

        # Node B
        nodeB = self.scene.createNode(name='nodeB', preset='node_preset_1')
        self.scene.createAttribute(node=nodeB, name='Battr1', index=-1, preset='attr_preset_1',
                            plug=True, socket=False, dataType=str)
        self.scene.createAttribute(node=nodeB, name='Battr2', index=-1, preset='attr_preset_1',
                            plug=True, socket=True, dataType=int)
        self.scene.createAttribute(node=nodeB, name='Battr3', index=-1, preset='attr_preset_2',
                            plug=True, socket=True, dataType=int)
        self.scene.createAttribute(node=nodeB, name='Battr4', index=-1, preset='attr_preset_3',
                            plug=True, socket=False, dataType=int, plugMaxConnections=1, socketMaxConnections=-1)

        # Connection creation
        self.scene.createConnection('nodeB', 'Battr2', 'nodeA', 'Aattr3')
        self.scene.createConnection('nodeB', 'Battr1', 'nodeA', 'Aattr4')

        # Graph
        print(">>> EVAL",  self.scene.evaluateGraph() )
        print(self.scene.scene().nodes)
