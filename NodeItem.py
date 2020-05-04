# NodeItem.py
# by Robin Prillwitz
# 24.4.2020
#

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from pyqtgraph import flowchart as fc
import pyqtgraph as pg
import numpy as np
from scipy.io import wavfile
import pandas as pd

from Nodz import nodz_main

import Config
import Interface
import Graph

class AbstractNodeItem(fc.Node):

    createAttributeSig = QtCore.pyqtSignal("QString", dict)

    def __init__(self, name):
        fc.Node.__init__(self, name)
        self.optionWidget = QtWidgets.QWidget()

    def getOptionWidget(self):
        return self.optionWidget

    def process(self, **kwds):
        # kwds will have one keyword argument per input terminal.
        kwds = { k.replace('/S/', ''): v for k, v in kwds.items() }
        print("PROCESS", self.name(), kwds.keys())
        return kwds

    def delete(self):
        del self

class SimulationNode(AbstractNodeItem):
    def __init__(self, name, simFile):
        super().__init__(name)
        self._initSettings()
        self.interface = Interface.Interface(simFile)
        self.simFile = simFile

        t = np.linspace(0, 0.1, 5)
        self.interface.prepareSimulation(
            time=t,
            value=t
        )
        self.interface.runSim()

    def process(self, **kwds):
        kwds = super().process(**kwds)
        if not "time" in kwds or not "v(input)" in kwds:
            raise Exception(self.name(), "unconnected inputs")

        self.interface.prepareSimulation(time=kwds.get("time"), value=kwds.get("v(input)")) # TODO automate
        self.interface.runSim()
        self.readData()

        return { k+"/P/": v for k, v in self.data.items() }

    def readData(self):
        data = self.interface.readRaw()

        self.data = data

        for var in self.data.keys():
            print(len(self.data[var]))
            if "IN" in var.upper():
                socket = True
                plug = True
            elif var.upper() == "TIME":
                socket = True
                plug = True
            else:
                socket = False
                plug = True

            if "V(" in var.upper():
                preset = "attr_preset_2"
            elif "I(" in var.upper():
                preset = "attr_preset_3"
            else:
                preset = "attr_preset_1"

            self.createAttributeSig.emit( self.name(),
                {"name":var, "index":-1, "preset":preset, "plug":plug, "socket":socket, "dataType":int}
            )

    def _initSettings(self):
        optionLayout = QtWidgets.QFormLayout()

        optionLayout.addRow(
            QtWidgets.QLabel("Label:"),
            QtWidgets.QComboBox()
        )

        self.optionWidget.setLayout(optionLayout)


class PlotNode(AbstractNodeItem):
    def __init__(self, name, plotViewer, color=None):
        super().__init__(name)

        self.plotViewer = plotViewer
        self.plot = Graph.Graph(name=name, clipToView=True,  downsampleMethod="subsample")

        self.color = color

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
        self.plotViewer.plt.vb.removeItem(self.plot)
        self.plotViewer.plt.legend.removeItem(self.name())
        self.plotViewer.plt.removeItem(self.plot)
        return super().delete()

    def process(self, **kwds):
        kwds = super().process(**kwds)

        if "x-Achse" in kwds and "y-Achse" in kwds:
            self.plot.setDownsampleData(
                x=np.array(kwds["x-Achse"]),
                y=np.array(kwds["y-Achse"])
            )
        elif "y-Achse" in kwds:
            self.plot.setDownsampleData(y=kwds["y-Achse"])
        else:
            self.plot.setDownsampleData(x=[0,0.001], y=[0,0])


class DataNode(AbstractNodeItem):
    def __init__(self, name, filename):
        super().__init__(name)
        self.filename = filename
        self.data = dict()

    def parseFile(self):
        if ".wav" in self.filename:
            try:
                fs, data = wavfile.read(self.filename)
            except:
                return

            self.data["Zeit"] = np.linspace(0, len(data) / fs, len(data))
            self.createAttributeSig.emit(
                self.name(),
                {"name":"Zeit", "index":-1, "preset":"attr_preset_1", "plug":True, "socket":False, "dataType":int}
            )

            if len(data.shape) > 1:
                length = data.shape[1]
            else:
                length = 1

            for i in range(0, length):
                self.data["Kanal "+str(i)] = data

                self.createAttributeSig.emit(
                    self.name(),
                    {"name":"Kanal "+ str(i), "index":-1, "preset":"attr_preset_2", "plug":True, "socket":False, "dataType":int}
                )
            print(self.data)
        else:
            print("unknown file format")

    def process(self, **kwds):
        kwds = super().process(**kwds)
        return { k+"/P/": v for k, v in self.data.items() }
