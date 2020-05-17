# visualSpice.py
# by Robin Prillwitz
# 24.4.2020
#

import sys
import os.path
import copy
from pathlib import Path
import shutil

import Config
import PlotViewer
import NodeScene
import NodeItem
import Interface

import pyqtgraph as pg
from pyqtgraph import flowchart as fl

import pandas as pd
import numpy as np
from PyQt5 import QtGui, QtCore, QtWidgets, uic
import qtmodern.styles
import qtmodern.windows


class visualSpiceWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(visualSpiceWindow, self).__init__()

        # generate TEMP DIR for simulations
        shutil.rmtree(Config.TEMP_DIR)
        Path(Config.TEMP_DIR).mkdir(parents=True, exist_ok=True)

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

        self.settingsBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/settings.png")), "Einstellungen")

        self.runSimBtn = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/start.png")), "Start")
        self.runSimBtn.clicked.connect(self.run)

        self.toolBar.addWidget(self.addDataInBtn)
        self.toolBar.addWidget(self.addNewSimBtn)
        self.toolBar.addWidget(self.addNewViewBtn)
        self.toolBar.addWidget(self.deleteSelectedBtn)
        self.toolBar.addSeparator()
        self.toolBar.addWidget(self.focusBtn)
        self.toolBar.addWidget(self.settingsBtn)

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

    def _getColor(self):
        i = len(self._getActiveScene().scene().nodes)
        if i < len(Config.COLORS):
            color = Config.COLORS[i].copy()
        else:
            color = Config.COLORS[i % len(Config.COLORS)].copy()
            color[0] = (color[0] + 10 + 10 * i) % 360

        qc = QtGui.QColor()
        # print(color)
        qc.setHsv(color[0], color[1] * 2.55, color[2] * 2.55)
        return qc

    def _createAttribute(self, nodeName, params):
        activeScene = self._getActiveScene()
        for node in activeScene.scene().nodes:
            if node== nodeName:
                activeScene.createAttribute(node=activeScene.scene().nodes[node],
                    name=params.get("name"), index=params.get("index"), preset=params.get("preset"),
                    plug=params.get("plug"), socket=params.get("socket"), dataType=params.get("dataType"))

    def deleteSelected(self):
        self._getActiveScene()._deleteSelectedNodes()

    def getFreeName(self, name, count=0):
        activeScene = self._getActiveScene()

        if name + " " + str(count) in activeScene.scene().nodes.keys():
            return self.getFreeName(name, count+1)
        else:
            return name + " " + str(count)


    def addNewSim(self):
        activeScene = self._getActiveScene()
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Datei Hinzufügen", "",
                "circuit (*.net);;Alle Dateinen (*)")

        if filename:
            userData = NodeItem.SimulationNode(self.getFreeName(os.path.basename(filename)), filename)
            userData.createAttributeSig.connect(self._createAttribute)

            position = activeScene.mapToScene(self.sceneTabWidget.width() / 2, self.sceneTabWidget.height() / 2)
            node = activeScene.createNode(name=userData.name(), preset='node_preset_1', position=position, userData=userData)

            userData.readData()

            self._refocus()

    def addNewPlot(self):
        activeScene = self._getActiveScene()

        userData = NodeItem.PlotNode(self.getFreeName("plotViewer"), self.plotViewer, self._getColor())

        position = activeScene.mapToScene(self.sceneTabWidget.width() / 2, self.sceneTabWidget.height() / 2)
        node = activeScene.createNode(name=userData.name(), preset='node_preset_1', position=position, userData=userData)

        # no need to use attrribute createion via signal since these attributes are always static
        # activeScene.createAttribute(node=node, name='x-Achse', index=-1, preset='attr_preset_1',
        #                     plug=False, socket=True, dataType=int)
        # activeScene.createAttribute(node=node, name='y-Achse', index=-1, preset='attr_preset_1',
        #                     plug=False, socket=True, dataType=int)
        activeScene.createAttribute(node=node, name='Signal', index=-1, preset='attr_preset_1',
                            plug=False, socket=True, dataType=int)
        activeScene.createAttribute(node=node, name='Ref', index=-1, preset='attr_preset_1',
                            plug=False, socket=True, dataType=int)

        self._refocus()

    def addData(self):
        activeScene = self._getActiveScene()
        filename, filetype = QtWidgets.QFileDialog.getOpenFileName(self, "Datei Hinzufügen", "",
                "Wave Datei (*.wav);;CSV Datei (*.csv);;Alle Dateinen (*)")

        if filename:
            userData = NodeItem.DataNode(self.getFreeName(os.path.basename(filename)), filename)
            userData.createAttributeSig.connect(self._createAttribute)

            position = activeScene.mapToScene(self.sceneTabWidget.width() / 2, self.sceneTabWidget.height() / 2)
            node = activeScene.createNode(name=userData.name(), preset='node_preset_1', position=position, userData=userData)

            userData.parseFile()

        self._refocus()


    def run(self):
        progress = pg.ProgressDialog("simuliert...")
        evaluated = self.mainNodeScene.evaluateGraph()
        progress += 10

        fc = fl.Flowchart()
        # add nodes and build terminals
        for node in self.mainNodeScene.scene().nodes.values():
            fc.addNode(node.userData, node.userData.name())
            for socket in node.sockets:
                node.userData.addInput(socket + "/S/")
            for plug in node.plugs:
                node.userData.addOutput(plug + "/P/")
        progress += 10

        # build connections
        for connection in evaluated:
            fc.connectTerminals(
                connection[0][0].userData.terminals[connection[0][2]+"/P/"],
                connection[1][0].userData.terminals[connection[1][2]+"/S/"]
            )
        progress += 10

        # # debug pg fc interface
        # dialog = QtWidgets.QDialog()
        # layout = QtWidgets.QVBoxLayout()
        # layout.addWidget(fc.widget())
        # dialog.setLayout(layout)
        # dialog.show()
        # dialog.exec_()

        # generate sim file
        shutil.copyfile(
            os.path.abspath(Config.template),
            Config.TEMP_DIR + Config.template
        )
        # TODO Apply Settings

        # run fc
        try:
            fc.process()
            progress += 10
        except Exception as e:
            print("\n>>> Cannot process fc")
            print(e)
            print("\n")
        else:
            sim = Interface.Interface(Config.TEMP_DIR + Config.template)
            try:
                sim.runSim()
            except Exception as e:
                print("\n>>> Cannot execute sim")
                print(e)
                print("\n")
            else:
                progress += 10

                data = sim.readRaw()
                print("DATA")
                print(data)
                print()
                progress += 10

                for node in self.mainNodeScene.scene().nodes.values():
                    if isinstance(node.userData, NodeItem.PlotNode):
                        node.userData.setData(data)

                self.plotViewer.plt.vb.autoRange()
        finally:
            # remove node terminals, cannot use for loop, since terminals dict will be mutated in iterations
            for node in self.mainNodeScene.scene().nodes.values():
                while len(node.userData.terminals) > 1:
                    node.userData.removeTerminal(node.userData.terminals[next(iter(node.userData.terminals))])

            # cleanup
            progress.setValue(100)
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
