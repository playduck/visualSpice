# PlotViewer.py
# by Robin Prillwitz
# 24.4.2020
#

import pyqtgraph as pg

class PlotViewer(object):
    def __init__(self, parent, units="V"):
        self.parent = parent
        super().__init__()

        pg.setConfigOptions(antialias=True, background=None, useWeave=True)

        self.win = pg.GraphicsWindow()
        self.win.setObjectName("plotWindow")
        self.plt = self.win.addPlot(enableMenu=False)

        self.plt.setLabel("left", units=units)
        self.plt.setLabel("bottom", units="s")
        self.plt.addLegend(offset=(2,2))

        self.plt.hideButtons()
        self.plt.autoRange(padding=0.2)

        self.plt.showGrid(True, True, 0.6)
        self.plt.vb.setLimits(minXRange=0.0001, minYRange=0.0001)
        # self.plt.vb.setAspectLocked(lock=True, ratio=1)
