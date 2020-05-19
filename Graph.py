# Graph.py
# by Robin Prillwitz
# 16.3.2020
#

from PyQt5 import QtGui, QtCore, QtWidgets
import pyqtgraph as pg
import numpy as np
from scipy import signal
import math

class Graph(pg.PlotDataItem):
    def __init__(self, *args, **kwds):
        pg.PlotDataItem.__init__(self, *args, **kwds)
        self.limit = 1.0 / 50000000

        self.data = None

    def setDownsampleData(self, x=None ,y=None):
        if x is None:
            if y is None:
                self.data = None
                pg.PlotDataItem.setData([])
                return
            else:
                x = np.linspace(0, len(y), len(y))

        # else:
        self.data = {"x": x, "y": y}
        # self.setData(x=x, y=y)
        self.updateDownsampling()

    def viewRangeChanged(self):
        self.updateDownsampling()


    # modified from the pyqtgraph example at
    # https://github.com/pyqtgraph/pyqtgraph/blob/develop/examples/hdf5.py
    def updateDownsampling(self):
        pass
        if self.data is None:
            self.setData([])
            return

        vb = self.getViewBox()
        if vb is None:
            return  # no ViewBox yet

        x = self.data["x"]
        y = self.data["y"]

        # xrange = vb.viewRange()[0]

        # # Determine what data range must be read
        # limits = [
        #     max(x[0],  xrange[0] ),
        #     min(x[-1], xrange[1] )]
        # start = np.min(limits)
        # stop = np.max(limits)

        # samples = math.ceil( (stop - start) / (x[-1] - x[0]) * len(x) )
        # newSamples = int(
        #     min(samples,
        #         max(10,
        #             min(4000,
        #                 math.ceil(1.0 / (self.limit * samples))
        #             )),
        #     ))

        self.setData(x=x, y=y)
