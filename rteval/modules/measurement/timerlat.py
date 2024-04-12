# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2024  John Kacur <jkacur@redhat.com>
#
""" timerlat.py - objectd to manage rtla timerlat """
import os
import subprocess
import signal
import time
import tempfile
import libxml2
from rteval.Log import Log
from rteval.modules import rtevalModulePrototype
from rteval.systopology import cpuinfo, SysTopology
from rteval.cpulist_utils import expand_cpulist, collapse_cpulist

class Timerlat(rtevalModulePrototype):
    """ measurement modules for rteval """
    def __init__(self, config, logger=None):
        rtevalModulePrototype.__init__(self, 'measurement', 'timerlat', logger)

        self.__cfg = config

        self.__numanodes = int(self.__cfg.setdefault('numanodes', 0))
        self.__priority = int(self.__cfg.setdefault('priority', 95))

        self.__cpulist = self.__cfg.setdefault('cpulist', "")
        self.__cpus = [str(c) for c in expand_cpulist(self.__cpulist)]
        self.__numcores = len(self.__cpus)

        self.__timerlat_out = None
        self.__timerlat_err = None
        self.__started = False
        self._log(Log.DEBUG, f"system using {self.__numcores} cpu cores")


    def _WorkloadSetup(self):
        self.__timerlat_process = None

    def _WorkloadBuild(self):
        self._setReady()

    def _WorkloadPrepare(self):
        self.__cmd = ['rtla', 'timerlat', 'hist', '-P', f'f:{int(self.__priority)}', '-u']
        self.__cmd.append(f'-c{self.__cpulist}')
        self._log(Log.DEBUG, f'self.__cmd = {self.__cmd}')
        self.__timerlat_out = tempfile.SpooledTemporaryFile(mode='w+b')
        self.__timerlat_err = tempfile.SpooledTemporaryFile(mode='w+b')

    def _WorkloadTask(self):
        if self.__started:
            return

        self._log(Log.DEBUG, f'starting with cmd: {" ".join(self.__cmd)}')

        self.__timerlat_out.seek(0)
        self.__timerlat_err.seek(0)
        try:
            self.__timerlat_process = subprocess.Popen(self.__cmd,
                                                       stdout=self.__timerlat_out,
                                                       stderr=self.__timerlat_err,
                                                       stdin=None)
            self.__started = True
        except OSError:
            self.__started = False

    def WorkloadAlive(self):
        if self.__started:
            return self.__timerlat_process.poll() is None
        return False

    def _WorkloadCleanup(self):
        if not self.__started:
            return
        while self.__timerlat_process.poll() is None:
            self._log(Log.DEBUG, "Sending SIGINT")
            os.kill(self.__timerlat_process.pid, signal.SIGINT)
            time.sleep(2)

        self._setFinished()
        self.__started = False

    def MakeReport(self):
        self.__timerlat_out.seek(0)
        for line in self.__timerlat_out:
            line = bytes.decode(line)
            print(line)
        self.__timerlat_out.close()


def ModuleInfo():
    """ Required measurement module information """
    return {"parallel": True,
            "loads": True}

def ModuleParameters():
    """ default parameters """
    return {"priority": {"descr": "Run rtla timerlat with this priority",
                         "default": 95,
                         "metavar": "PRIO" }
           }

def create(params, logger):
    """ Instantiate a Timerlat measurement module object"""
    return Timerlat(params, logger)

if __name__ == '__main__':
    from rteval.rtevalConfig import rtevalConfig

    l = Log()
    l.SetLogVerbosity(Log.INFO|Log.DEBUG|Log.ERR|Log.WARN)

    cfg = rtevalConfig({}, logger=l)
    prms = {}
    modprms = ModuleParameters()
    for c, p in list(modprms.items()):
        prms[c] = p['default']
    cfg.AppendConfig('timerlat', prms)

    cfg_tl = cfg.GetSection('timerlat')
    cfg_tl.cpulist = collapse_cpulist(SysTopology().online_cpus())

    RUNTIME = 10

    tl = Timerlat(cfg_tl, l)
    tl._WorkloadSetup()
    tl._WorkloadPrepare()
    tl._WorkloadTask()
    time.sleep(RUNTIME)
    tl._WorkloadCleanup()
    tl.MakeReport()
