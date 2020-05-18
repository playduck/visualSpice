# Interface.py
# by Robin Prillwitz
# 27.4.2020
#

import os
import re
import sys
import fileinput
import subprocess
import shutil

import numpy as np
import pandas as pd
import ltspice

import Config

class Interface(object):
    def __init__(self, cirFilename):
        super().__init__()

        self.simFile = cirFilename
        self.filename = os.path.basename(os.path.splitext(cirFilename)[0])

    def _replaceInFile(self, find, replace, file=None):
        if file == None:
            file = self.simFile
        for i, line in enumerate(fileinput.input(file, inplace=1)):
            sys.stdout.write(line.replace(find, replace))

    def prepareSimulation(self, time=None, value=None):
        values = pd.DataFrame({"time": time, "value": value})
        values.to_csv(Config.TEMP_DIR+"input.m", sep=" ", header=False, index=False, float_format="%.6e")

        if Config.simulator == "LTSPICE":
            shutil.copyfile(
                self.simFile,
                Config.TEMP_DIR+self.filename+".net"
            )
            self._replaceInFile("__INPUT_FILE__", Config.TEMP_DIR+"input.m", Config.TEMP_DIR+self.filename+".net")
        else:
            self._replaceInFile("__INPUT_FILE__", Config.TEMP_DIR+"input.m")

    def runSim(self):
        # delete previous .raw file(s)
        for file in os.listdir(Config.TEMP_DIR):
            if file.endswith(".raw"):
                os.remove(Config.TEMP_DIR+file)

        if Config.simulator == "LTSPICE":
            process = "/Applications/LTspice.app/Contents/MacOS/LTspice"
            out = subprocess.run([
                process,
                "-b", Config.TEMP_DIR+self.filename+".net"
            ])
            self._replaceInFile("__INPUT_FILE__", Config.TEMP_DIR+"input.m", Config.TEMP_DIR+self.filename+".net")

            with open(Config.TEMP_DIR + self.filename + ".log" , 'r+') as f:
                for line in f:
                    if "error" in line:
                        print("Simulation failed")
                        raise Exception("Simulation Failed")

        elif Config.simulator == "NGSPICE":
            process = "ngspice"
            out = subprocess.run([
                process,
                "-r", Config.TEMP_DIR + self.filename +".raw",
                "-o", Config.TEMP_DIR + self.filename +".log",
                "-b -a", self.simFile
            ])

            self._replaceInFile(Config.TEMP_DIR+"input.m", "__INPUT_FILE__")

            # parse log
            with open(Config.TEMP_DIR + self.filename + ".log" , 'r+') as f:
                for line in f:
                    if "run simulation(s) aborted" in line or "cannot open file" in line or "error" in line:
                        print("Simulation failed")
                        raise Exception("Simulation Failed")

    def readRaw(self):
        if Config.simulator == "LTSPICE":
            print("PATH", Config.TEMP_DIR+self.filename+".raw")
            raw = ltspice.Ltspice(Config.TEMP_DIR+self.filename+".raw")
            raw.parse()

            print("\n\nvarnames",raw.getVariableNames(),
             len(raw.getVariableNames()), raw.getVariableNumber(), "\n\n")

            d = dict()
            for var in raw.getVariableNames():
                try:
                    d[var] = np.array(raw.getData(var))
                except Exception as e:
                    print(e)

            print("\n\nD",d.keys(),"\n\n")
            del raw
            return d

        elif Config.simulator == "NGSPICE_WRDATA":
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
