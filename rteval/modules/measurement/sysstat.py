# SPDX-License-Identifier: GPL-2.0-or-later
#
#   sysstat.py - rteval measurment module collecting system statistics
#                using the sysstat utility
#
#   Copyright 2013          David Sommerseth <davids@redhat.com>
#

import os
import time
import subprocess
import base64
import bz2
import textwrap
import libxml2
from rteval.Log import Log
from rteval.modules import rtevalModulePrototype


class sysstat(rtevalModulePrototype):
    def __init__(self, config, logger=None):
        rtevalModulePrototype.__init__(self, 'measurement', 'sysstat', logger)
        self.__cfg = config
        self.__started = False
        self.__logentry = 0
        self.__bin_sadc = "/usr/lib64/sa/sadc" # FIXME: Do dynamically
        self.__datadir = os.path.join(self.__cfg.reportdir, 'sysstat')
        self.__datafile = os.path.join(self.__datadir, "sysstat.dat")


    def _WorkloadSetup(self):
        # Nothing to do here for sysstat
        pass


    def _WorkloadBuild(self):
        # Nothing to build
        self._setReady()


    def _WorkloadPrepare(self):
        os.mkdir(self.__datadir)


    def _WorkloadTask(self):
        # This workload will actually not run any process, but
        # it will update the data files each time rteval checks
        # if this workload is alive.
        #
        # Just add a single notification that rteval started
        if self.__logentry == 0:
            cmd = [self.__bin_sadc, "-S", "XALL", "-C", "rteval started", self.__datafile]
            subprocess.call(cmd)
            self.__logentry += 1


    def WorkloadAlive(self):
        # Here the sysstat tool will be called, which will update
        # the file containing the system information
        cmd = [self.__bin_sadc, "-S", "XALL", "1", "1", self.__datafile]
        subprocess.call(cmd)
        self.__logentry += 1
        return True


    def _WorkloadCleanup(self):
        # Add 'rteval stopped' comment line
        cmd = [self.__bin_sadc, "-S", "XALL", "-C", "rteval stopped", self.__datafile]
        subprocess.call(cmd)
        self.__logentry += 1
        self._setFinished()


    def MakeReport(self):
        rep_n = libxml2.newNode('sysstat')
        rep_n.newProp('command_line', '(sysstat specifics)')
        rep_n.newProp('num_entries', str(self.__logentry))

        fp = open(self.__datafile, "rb")
        compr = bz2.BZ2Compressor(9)
        cmpr = compr.compress(fp.read())
        data = base64.b64encode(cmpr + compr.flush()).decode('utf-8')
        data_n = rep_n.newTextChild(None, 'data', "\n"+"\n".join(textwrap.wrap(data, 75))+"\n")
        data_n.newProp('contents', 'sysstat/sar binary data')
        data_n.newProp('encoding', 'base64')
        data_n.newProp('compression', 'bz2')
        fp.close()
        del cmpr
        del compr

        # Return the report
        return rep_n



def ModuleParameters():
    return {}  # No arguments available



def create(params, logger):
    return sysstat(params, logger)


if __name__ == '__main__':
    from rteval.rtevalConfig import rtevalConfig

    l = Log()
    l.SetLogVerbosity(Log.INFO|Log.DEBUG|Log.ERR|Log.WARN)

    cfg = rtevalConfig({}, logger=l)
    prms = {}
    modprms = ModuleParameters()
    for c, p in list(modprms.items()):
        prms[c] = p['default']
    cfg.AppendConfig('MeasurementModuleTemplate', prms)

    cfg_ct = cfg.GetSection('MeasurementModuleTemplate')
    cfg_ct.reportdir = "."

    runtime = 10

    c = sysstat(cfg_ct, l)
    c._WorkloadSetup()
    c._WorkloadPrepare()
    c._WorkloadTask()
    print(f"Running for approx {runtime} seconds")
    while runtime > 0:
        c.WorkloadAlive()
        time.sleep(1)
        runtime -= 1
    c._WorkloadCleanup()
    rep_n = c.MakeReport()

    xml = libxml2.newDoc('1.0')
    xml.setRootElement(rep_n)
    xml.saveFormatFileEnc('-', 'UTF-8', 1)
