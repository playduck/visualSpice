# Interface.py
# by Robin Prillwitz
# 27.4.2020
#

import os
import sys
import fileinput
import subprocess

import numpy as np
import pandas as pd
import ltspice

import Config

class Interface(object):
    def __init__(self, cirFilename):
        super().__init__()

        self.simFile = cirFilename
        self.filename = os.path.basename(os.path.splitext(cirFilename)[0])

    def _replaceInFile(self, find, replace):
        for i, line in enumerate(fileinput.input(self.simFile, inplace=1)):
            sys.stdout.write(line.replace(find, replace))

    def prepareSimulation(self, time=None, value=None):
        values = pd.DataFrame({"time": time, "value": value})

        if Config.simulator == "LTSPICE":
            pass
        elif Config.simulator == "NGSPICE":
            values.to_csv(Config.TEMP_DIR+"input.m", sep=" ", header=True, index=False, float_format="%.6e")
            self._replaceInFile("__INPUT_FILE__", Config.TEMP_DIR+"input.m")

    def runSim(self):
        if Config.simulator == "LTSPICE":
            pass # TODO
        elif Config.simulator == "NGSPICE":
            process = "NGSPICE"

            out = subprocess.run([
                process,
                "-r", Config.TEMP_DIR + self.filename +".raw",
                "-o", Config.TEMP_DIR + self.filename +".log",
                "-b -a", self.simFile
            ])

            # print("OUT", out)
            # print()

            self._replaceInFile(Config.TEMP_DIR+"input.m", "__INPUT_FILE__")

            # parse log
            with open(Config.TEMP_DIR + self.filename + ".log" , 'r+') as f:
                for line in f:
                    if "run simulation(s) aborted" in line or "cannot open file" in line or "error" in line:
                        print("Simulation failed")
                        raise Exception("Simulation Failed")

    def readRaw(self):
        if Config.simulator == "LTSPICE":
            data = ltspice.Ltspice(self.filename)
            data.parse()

            return data

        elif Config.simulator == "ngspice_wrdata":
            read = pd.read_csv(Config.TEMP_DIR+"output.m", delimiter="\s+")

            d = dict()
            for col in read.columns:
                d[col] = np.array(read[col], dtype=np.float64)

            return d

        elif Config.simulator == "NGSPICE":
            # shameless rip from
            # https://gist.github.com/snmishra/27dcc624b639c2626137

            BSIZE_SP = 512
            MDATA_LIST = [b'title', b'date', b'plotname', b'flags', b'no. variables',
                                b'no. points', b'dimensions', b'command', b'option']

            try:
                fp = open(Config.TEMP_DIR+self.filename+".raw", 'rb')
            except:
                print("NO RAW FILE")
                return {"None": [None]}

            plot = {}
            count = 0
            arrs = []
            plots = []

            while (True):
                try:
                    mdata = fp.readline(BSIZE_SP).split(b':', maxsplit=1)
                except:
                    raise
                if len(mdata) == 2:
                    if mdata[0].lower() in MDATA_LIST:
                        plot[mdata[0].lower()] = mdata[1].strip()
                    if mdata[0].lower() == b'variables':
                        nvars = int(plot[b'no. variables'])
                        npoints = int(plot[b'no. points'])
                        plot['varnames'] = []
                        plot['varunits'] = []
                        for varn in range(nvars):
                            varspec = (fp.readline(BSIZE_SP).strip()
                                    .decode('ascii').split())
                            assert(varn == int(varspec[0]))
                            plot['varnames'].append(varspec[1])
                            plot['varunits'].append(varspec[2])
                    if mdata[0].lower() == b'binary':
                        dtype = [np.complex_ if b'complex' in plot.get(b'flags') else np.float_]*nvars

                        rowdtype = np.dtype({
                            "names": plot["varnames"],
                            "formats": dtype
                        })
                        # We should have all the metadata by now
                        arrs.append(np.fromfile(fp, dtype=rowdtype, count=npoints))
                        plots.append(plot)
                        fp.readline() # Read to the end of line
                else:
                    break

            arr = dict()
            for i, var in  enumerate(plots[0]["varnames"]):
                arr[var] = list()
                for data in arrs[0]:
                    arr[var].append(data[i].real)
                arr[var] = np.array(arr[var])


            return arr
