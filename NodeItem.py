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

import fileinput
import os
import re

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
        print("PROCESS", self.name(), kwds)
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
        name = self.name().replace(" ", "_").replace(".","_")

        parsed_models = list()
        nets = list()

        fobj = open(self.simFile, "r")
        text = fobj.read()
        parsed_models = re.findall("(\.(MODEL|model) (\S+) (.*\n\+.*)+)", text, re.MULTILINE)

        for line in text.splitlines():
            n = re.search("^([A-Za-z]+[0-9]+)\s([a-zA-Z0-9|_]+)\s([a-zA-Z0-9|_]+)\s(.*)$", line, re.M)
            if n is not None:
                nets.append(n.groups())

        models = list()
        for m in parsed_models:
            if "filesrc" not in m[2]:
                new_name = name+"_"+m[2]
                models.append({
                    "name": m[2],
                    "new_name": new_name,
                    "body": m[0].replace(m[2], new_name, 1) + "\n"
                })

        net_names = dict()
        template = ""
        # replace names with unique names or connected ones
        print(kwds)
        for component in nets:
            print(component)
            cname = "{0}_{1}".format(component[0], name)
            if component[0].startswith("V"):
                # skip voltage sources
                continue

            cfrom = "0"
            if "V("+component[1]+")" in kwds:
                cfrom = kwds.get("V("+component[1]+")")
            elif component[1] != "0":
                cfrom = "{0}_{1}".format(component[1], name)

            cto = "0"
            if "V("+component[2]+")" in kwds:
                cto = kwds.get("V("+component[2]+")")
            elif component[2] != "0":
                cto = "{0}_{1}".format(component[2], name)

            val = component[3]
            for model in models:
                if model["name"] == component[3].strip():
                    val =  model["new_name"]
                    break

            template += "{0} {1} {2} {3}\n".format(cname, cfrom, cto, val)

            if component[1] != "0":
                net_names["V("+component[1]+")"] = cfrom
            if component[2] != "0":
                net_names["V("+component[2]+")"] = cto

        insertIntoTemplate(template, "nets")
        for model in models:
            insertIntoTemplate(model["body"], "models")

        # don't know why, but it fails doing it otherwise
        new_names = dict()
        for k in net_names.keys():
            new_names[k + "/P/"] = net_names.get(k)

        return new_names

    def readData(self):
        data = self.interface.readRaw()

        self.data = data

        for var in self.data.keys():
            if "TIME" in var.upper():
                continue
            elif "V(" in var.upper():
                var = "V"+ var[1:] # capitalize V
                preset = "attr_preset_2"
            elif "I(" in var.upper():
                var = "I"+ var[1:]
                preset = "attr_preset_3"
                continue # TODO?
            else:
                preset = "attr_preset_1"
                print("unknown", var)


            self.createAttributeSig.emit( self.name(),
                {"name":var, "index":-1, "preset":preset, "plug":True, "socket":True, "dataType":int}
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

        self.sig = "V("+ kwds.get("Signal") +")"
        self.ref = kwds.get("Ref")
        if self.ref is not None:
            self.ref = "V("+self.ref+")"

        print("PLOT", self.sig, self.ref, kwds)

    def setData(self, data):
        x = data.get("time", None)
        sig = data.get(self.sig, None)
        ref = data.get(self.ref, None)

        if ref is not None:
            sig = np.array(sig) - np.array(ref)

        if sig is not None and x is not None:
            self.plot.setDownsampleData(
                x=np.array(x),
                y=np.array(sig)
            )
        elif sig is not None:
            self.plot.setDownsampleData(y=sig)
        else:
            self.plot.setDownsampleData(x=[0,0.001], y=[0,0])


class DataNode(AbstractNodeItem):
    def __init__(self, name, filename):
        super().__init__(name)
        self.filename = filename

        self.time = None
        self.data = dict()

    def parseFile(self):
        if ".wav" in self.filename:
            try:
                fs, data = wavfile.read(self.filename)
            except:
                return

            self.time = np.linspace(0, len(data) / fs, len(data))

            if len(data.shape) > 1:
                length = data.shape[1]
            else:
                length = 1

            for i in range(0, length):
                self.data["Kanal "+str(i)+" +"] = data

                self.createAttributeSig.emit(
                    self.name(),
                    {"name":"Kanal "+str(i)+" +", "index":-1, "preset":"attr_preset_2", "plug":True, "socket":False, "dataType":int}
                )
                self.createAttributeSig.emit(
                    self.name(),
                    {"name":"Kanal "+str(i)+" -", "index":-1, "preset":"attr_preset_1", "plug":True, "socket":False, "dataType":int}
                )
        else:
            print("unknown file format")

    def process(self, **kwds):
        kwds = super().process(**kwds)
        name = self.name().replace(" ", "_").replace(".","_")

        # generate input files for all possible channels
        net_names = dict()
        outputs = self.outputs()
        for i, val in enumerate(self.data):
            # generate file
            filename = "{0}_input_{1}.m".format(
                name,
                str(i)
            )
            # populate file with own timestamp
            values = np.array(self.data[val], dtype=np.float64)
            time = self.time
            df = pd.DataFrame({
                "time": time,
                "val": values
            })
            df.to_csv(os.path.abspath(Config.TEMP_DIR+filename),
                    sep=" ", header=False, index=False, float_format="%0.06e")

            # generate net names
            net_names[val] = "{0}_input_{1}".format(name, str(i))
            # generate refrence net names if used
            ref_net = outputs.get("Kanal "+str(i)+ " -/P/", None)
            if ref_net is not None:
                if len(ref_net.connections()) > 0:
                    net_names["Kanal "+str(i)+ " -"] = "{0}_refrence_{1}".format(name, str(i))

            # write sources to .net
            signal_net_name =   net_names.get("Kanal "+str(i)+ " +")
            ref_net_name =      net_names.get("Kanal "+str(i)+ " -", "0")

            template = getSrcTemplate("{0}_{1}".format(name, str(i)),
                    Config.TEMP_DIR+filename, signal_net_name, ref_net_name)

            insertIntoTemplate(template, "sources")

        # prepend port identifier to data
        names = dict()
        for n in net_names.keys():
            names[n+"/P/"] = net_names.get(n)
        return names

def getSrcTemplate(number, filename, signal, ref):
    if Config.simulator == "LTSPICE":
        return getLTSrcTemplate(number, filename, signal, ref)
    else:
        return getNGSrcTemplate(number, filename, signal, ref)


def getLTSrcTemplate(number, filename, signal, ref): # FIXME VAL SCALE SHOULD BE 1
    return """* INPUT SOURCE {0}
V{0} {2} {3} PWL TIME_SCALE_FACTOR=1 VALUE_SCALE_FACTOR=0.001 (FILE={1})
""".format(number, filename, signal, ref)


def getNGSrcTemplate(number, filename, signal, ref): # FIXME AMPSCALE SHOULD BE 1
    return """* INPUT SOURCE {0}
.model filesrc filesource (file="{1}" amploffset=[0] amplscale=[0.001]
+                           timeoffset=0 timescale=1
+                           timerelative=false amplstep=false)
a{0} %vd([{2}, {3}]) filesrc
""".format(number, filename, signal, ref)


def insertIntoTemplate(insert, section):
    if "sources" in section:
        divider = "*-----BEGIN USER SOURCES-----*"
    elif "nets" in section:
        divider = "*-----BEGIN USER NETLIST-----*"
    elif "models" in section:
        divider = "*-----BEGIN USER MODELS-----*"
    else:
        divider = section
        print("unknown section")

    for line in fileinput.FileInput(Config.TEMP_DIR + Config.template, inplace=1):
        if divider in line:
            line=line.replace(line,line+"\n"+insert)
        print(line, end="")
