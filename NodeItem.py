# NodeItem.py
# by Robin Prillwitz
# 24.4.2020
#

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from pyqtgraph import flowchart as fc
import pyqtgraph as pg
from Nodz import nodz_main

import Config

class AbstractNodeItem(fc.Node):
    def __init__(self, name):
        fc.Node.__init__(self, name)
        self.optionWidget = QtWidgets.QWidget()

    def getOptionWidget(self):
        return self.optionWidget

    def process(self, **kwds):
        # kwds will have one keyword argument per input terminal.
        print("PROCESS", self.name(), kwds)
        # print(self.terminals)
        return {'outputTerminalName': [1]}

    def delete(self):
        del self

class SimulationNode(AbstractNodeItem):
    def __init__(self, name, simFile):
        super().__init__(name)
        self._initSettings()

        self.simFile = simFile

    def _initSettings(self):
        optionLayout = QtWidgets.QFormLayout()

        optionLayout.addRow(
            QtWidgets.QLabel("Label:"),
            QtWidgets.QComboBox()
        )

        self.optionWidget.setLayout(optionLayout)


class PlotNode(AbstractNodeItem):
    def __init__(self, name, plotViewer):
        super().__init__(name)

        self.plotViewer = plotViewer
        self.plot = pg.PlotDataItem()
        self.color = QtGui.QColor(100, 212, 240)

        self.plotViewer.plt.addItem(self.plot)

        self.optionWidget = uic.loadUi(Config.getResource("ui/plotSettings.ui"))
        self.colorButton = pg.ColorButton(color=self.color)
        self.colorButton.sigColorChanged.connect(lambda val: self.applyChange("color", val.color()))
        self.optionWidget.colorBtnLayout.addWidget(self.colorButton)

        self.applyChange("color", self.color)

    def applyChange(self, who, val):
        if who == "color":
            self.color = val
            self.plot.setPen(pg.mkPen(color=self.color, width=2))

    def delete(self):
        self.plotViewer.plt.removeItem(self.plot)
        return super().delete()

    def process(self, **kwds):
        super().process(**kwds)

        self.plot.setData([0,0.001], [0,0])
        if "x-Achse" in kwds and "y-Achse" in kwds:
            self.plot.setData(kwds["x-Achse"], kwds["y-Achse"])
        elif "y-Achse" in kwds:
            self.plot.setData(kwds["y-Achse"])


class DataNode(AbstractNodeItem):
    def __init__(self, name):
        super().__init__(name)
        self.data = dict()

    def process(self, **kwds):
        super().process(**kwds)
        # print("DATA", self.data)
        return self.data
