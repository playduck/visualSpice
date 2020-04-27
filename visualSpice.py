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

import pyqtgraph as pg
import pandas as pd
import numpy as np
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

        # populate toolbar
        self.addNewSim = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_sim.png")), "Simulation")
        self.addNewView = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/add_plot.png")), "Plot")
        self.deleteSelected = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/delete.png")), "Löschen")
        self.runSim = QtWidgets.QPushButton(QtGui.QIcon(Config.getResource("assets/start.png")), "Start")

        self.toolBar.addWidget(self.addNewSim)
        self.toolBar.addWidget(self.addNewView)
        self.toolBar.addWidget(self.deleteSelected)
        self.toolBar.addSeparator()

        spacer = QtWidgets.QWidget()
        spacer.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.toolBar.addWidget(spacer)
        self.toolBar.addSeparator()

        self.toolBar.addWidget(self.runSim)

        # add Plot Viewer
        self.plotViewer = PlotViewer.PlotViewer(self)
        self.plotDockWidget.setWidget(self.plotViewer.win)

        # add nodeScene
        self.mainNodeScene = NodeScene.NodeScene()

        self.sceneTabWidget.addTab(self.mainNodeScene.scene, "Main")

        self.show()

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
    pallete.setColor(QtGui.QPalette.Highlight, QtGui.QColor(255, 50, 200))
    pallete.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor(255, 50, 200))
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
