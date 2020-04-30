# visualSpice.py
# by Robin Prillwitz
# 24.4.2020
#

import sys
import os.path
import copy
from pathlib import Path
import json

import Config
import PlotViewer
import NodeScene
import NodeItem

import pyqtgraph as pg
from pyqtgraph import flowchart as fl

import pandas as pd
import numpy as np
from scipy.io import wavfile
from PyQt5 import QtGui, QtCore, QtWidgets, uic
import qtmodern.styles
import qtmodern.windows


class visualSpiceWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(visualSpiceWindow, self).__init__()

        uic.loadUi(Config.getResource("ui/main.ui"), self)
        self.setWindowTitle("visualSpice")
        self.setGeometry(50, 50, 800, 600)

        # Set Window to screen center
        geometry = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        center = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        geometry.moveCenter(center)
        self.move(geometry.topLeft())

        # add Plot Viewer
        self.plotViewer = PlotViewer.PlotViewer(self)
        self.plotDockWidget.setWidget(self.plotViewer.win)

        # add nodeScene
        self.mainNodeScene = NodeScene.NodeScene()
        self.sceneTabWidget.addTab(self.mainNodeScene, "Main")
        self.mainNodeScene.signal_NodeSelected.connect(self._nodeSelected)
        self.mainNodeScene.signal_NodeDeleted.connect(self._nodeDeleted)

        # populate toolbar
        self.addDataInBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_data.png")), "Daten")
        self.addDataInBtn.clicked.connect(self.addData)

        self.addNewSimBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_sim.png")), "Simulation")
        self.addNewSimBtn.clicked.connect(self.addNewSim)

        self.addNewViewBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_plot.png")), "Plot")
        self.addNewViewBtn.clicked.connect(self.addNewPlot)

        self.deleteSelectedBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/delete.png")), "Löschen")
        self.deleteSelectedBtn.clicked.connect(self.deleteSelected)
        self.deleteSelectedBtn.setDisabled(True)

        self.focusBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/focus.png")), "Focus")
        self.focusBtn.clicked.connect(lambda: self.sceneTabWidget.currentWidget()._focus() )

        self.runSimBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/start.png")), "Start")
        self.runSimBtn.clicked.connect(self.run)

        self.toolBar.addWidget(self.addDataInBtn)
        self.toolBar.addWidget(self.addNewSimBtn)
        self.toolBar.addWidget(self.addNewViewBtn)
        self.toolBar.addWidget(self.deleteSelectedBtn)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.focusBtn)

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolBar.addWidget(spacer)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.runSimBtn)

        self.show()
        # self.mainNodeScene._focus()

    def _getActiveScene(self):
        return self.sceneTabWidget.currentWidget()

    def _refocus(self):
        activeScene = self._getActiveScene()
        if len(activeScene.scene().nodes) == 1:
            activeScene._focus()

    def _nodeSelected(self, selectedNodes):
        self.settingsDockWidget.setWidget(QtWidgets.QWidget())
        self.deleteSelectedBtn.setDisabled(selectedNodes == [])

        if len(selectedNodes) > 1 or selectedNodes == []:
            return

        selectedNode = selectedNodes[0]
        for node in self._getActiveScene().scene().nodes.values():
            if selectedNode == node.name:
                self.settingsDockWidget.setWidget(node.userData.getOptionWidget())

    def _nodeDeleted(self, deletedNodes):
        for deletedNode in deletedNodes:
            deletedNode.userData.delete()

    def deleteSelected(self):
        self._getActiveScene()._deleteSelectedNodes()

    def addNewSim(self):
        simFile = "./test"
        activeScene = self._getActiveScene()

        userData = NodeItem.SimulationNode(os.path.basename(simFile), simFile)

        position = activeScene.mapToScene(self.sceneTabWidget.width() / 2, self.sceneTabWidget.height() / 2)

        node = activeScene.createNode(name='test', preset='node_preset_1', position=position, userData=userData)
        activeScene.createAttribute(node=node, name='Battr1', index=-1, preset='attr_preset_1',
                            plug=True, socket=False, dataType=str)
        activeScene.createAttribute(node=node, name='Battr2', index=-1, preset='attr_preset_1',
                            plug=True, socket=True, dataType=int)
        activeScene.createAttribute(node=node, name='Battr3', index=-1, preset='attr_preset_2',
                            plug=True, socket=True, dataType=int)
        activeScene.createAttribute(node=node, name='Battr4', index=-1, preset='attr_preset_3',
                            plug=True, socket=False, dataType=int, plugMaxConnections=1, socketMaxConnections=-1)

        self._refocus()

    def addNewPlot(self):
        activeScene = self._getActiveScene()

        userData = NodeItem.PlotNode("plotViewer", self.plotViewer)

        position = activeScene.mapToScene(self.sceneTabWidget.width() / 2, self.sceneTabWidget.height() / 2)

        node = activeScene.createNode(name='plotViewer', preset='node_preset_1', position=position, userData=userData)
        activeScene.createAttribute(node=node, name='x-Achse', index=-1, preset='attr_preset_1',
                            plug=False, socket=True, dataType=int)
        activeScene.createAttribute(node=node, name='y-Achse', index=-1, preset='attr_preset_1',
                            plug=False, socket=True, dataType=int)

        self._refocus()

    def addData(self):
        activeScene = self._getActiveScene()
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Datei Hinzufügen", "",
                "Wave Datei (*.wav);;CSV Datei (*.csv);;Alle Dateinen (*)")

        if filename:
            userData = NodeItem.DataNode(os.path.basename(filename))
            position = activeScene.mapToScene(self.sceneTabWidget.width() / 2, self.sceneTabWidget.height() / 2)
            node = activeScene.createNode(name=os.path.basename(filename), preset='node_preset_1', position=position, userData=userData)

            if ".wav" in filetype:
                try:
                    fs, data = wavfile.read(filename)
                except:
                    return

                userData.data["Zeit"] = np.linspace(0, len(data) / fs, len(data))
                activeScene.createAttribute(node=node, name="Zeit",
                    index=-1, preset='attr_preset_1', plug=True, socket=False, dataType=int)

                if len(data.shape) > 1:
                    length = data.shape[1]
                else:
                    length = 1

                for i in range(0, length):
                    userData.data["Kanal "+str(i)] = data
                    activeScene.createAttribute(node=node, name="Kanal "+ str(i),
                        index=-1, preset='attr_preset_2', plug=True, socket=False, dataType=int)

        self._refocus()

    def run(self):
        evaluated = self.mainNodeScene.evaluateGraph()

        fc = fl.Flowchart()
        # add nodes and build terminals
        for node in self.mainNodeScene.scene().nodes.values():
            fc.addNode(node.userData, node.userData.name())
            for socket in node.sockets:
                node.userData.addInput(socket)
            for plug in node.plugs:
                node.userData.addOutput(plug)

        # build connections
        for connection in evaluated:
            fc.connectTerminals(
                connection[0][0].userData.terminals[connection[0][2]],
                connection[1][0].userData.terminals[connection[1][2]]
            )

        # # debug pg fc interface
        # dialog = QtWidgets.QDialog()
        # layout = QtWidgets.QVBoxLayout()
        # layout.addWidget(fc.widget())
        # dialog.setLayout(layout)
        # dialog.show()
        # dialog.exec_()

        # run fc
        fc.process()

        # cleanup
        fc.clear()
        fc.close()
        del fc


if __name__ == "__main__":

    # set paths for frozen mode
    root = Path()
    if getattr(sys, 'frozen', False):
        root = Path(sys._MEIPASS) # sys has attribute if it's frozen
        qtmodern.styles._STYLESHEET = root / 'qtmodern/style.qss'
        qtmodern.windows._FL_STYLESHEET = root / 'qtmodern/frameless.qss'

    # setup High DPI Support
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    # Create main App
    app = QtWidgets.QApplication(sys.argv)

    app.setApplicationName("visualSpice")
    # app.setWindowIcon(QtGui.QIcon(Config.getResource("assets/icon-512.png"))) # TODO

    # show splash screen
    splashImg = QtGui.QPixmap(Config.getResource("assets/splash.jpg"))
    splash = QtGui.QSplashScreen(
        splashImg.scaledToWidth(
            app.primaryScreen().size().width() / 2,
            QtCore.Qt.SmoothTransformation
        ),
        QtCore.Qt.WindowStaysOnTopHint
    )
    splash.show()

    # set style (order is important)
    qtmodern.styles.dark(app)
    # initialize program
    gui = visualSpiceWindow()

    # start qtmodern
    mw = qtmodern.windows.ModernWindow(gui)
    # close splash on completion
    splash.finish(mw)
    # restore native window frame
    # hacky but works until an official implementation exists
    mw.setWindowFlags(QtCore.Qt.Window)
    mw.titleBar.hide()
    # add handler for global positioning
    gui.window = mw

    pallete = QtGui.QPalette()
    pallete.setColor(QtGui.QPalette.Highlight, QtGui.QColor(100, 212, 240))
    pallete.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(100, 212, 240))
    app.setPalette(pallete)

    # load custom styles
    with open(Config.getResource("assets/style.qss"), "r") as fh:
        gui.setStyleSheet(fh.read())

    mw.show()

    # trigger event loop all 100ms
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(100)

    sys.exit(app.exec_())
