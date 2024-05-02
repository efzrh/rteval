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
import math
import sys
import libxml2
from rteval.Log import Log
from rteval.modules import rtevalModulePrototype
from rteval.systopology import cpuinfo, SysTopology
from rteval.cpulist_utils import expand_cpulist, collapse_cpulist

class TLRunData:
    ''' class to store instance data from a timerlat run '''
    def __init__(self, coreid, datatype, priority, logfnc):
        self.__id = coreid
        self.__type = datatype
        self.__priority = int(priority)
        self.description = ''
        self._log = logfnc
        self.duration = ''
        # histogram data, irqs, kernel threads and user threads per core
        self.irqs = {}
        self.thrs = {}
        self.usrs = {}
        self.__samples = {}
        self.__numsamples = 0
        self.min = 100000000
        self.max = 0
        self.__stddev = 0.0
        self.__mean = 0.0
        self.__mode = 0.0
        self.__median = 0.0
        self.__range = 0.0

    def update_max(self, value):
        """ highest bucket with a value """
        if value > self.max:
            self.max = value

    def update_min(self, value):
        """ lowest bucket with a value """
        if value < self.min:
            self.min = value

    def bucket(self, index, val1, val2, val3):
        """ Store results index=bucket number, val1=IRQ, val2=thr, val3=usr """
        values = val1 + val2 + val3
        self.__samples[index] = self.__samples.setdefault(index, 0) + values
        self.irqs[index] = val1
        self.thrs[index] = val2
        self.usrs[index] = val3
        if values:
            self.update_max(index)
            self.update_min(index)
        self.__numsamples += values

    def reduce(self):
        """ Calculate statistics """
        # Check to see if we have any samples. If there are 1 or 0, return
        if self.__numsamples <= 1:
            self._log(Log.DEBUG, f"skipping {self.__id} ({self.__numsamples} sampples)")
            self.__mad = 0
            self.__stddev = 0
            return

        self._log(Log.INFO, f"reducing {self.__id}")
        total = 0   # total number of samples
        total_us = 0
        keys = list(self.__samples.keys())
        keys.sort()

        # if numsamples is odd, then + 1 gives us the actual mid
        # if numsamples is even, we avg mid and mid + 1, so we actually
        # want to know mid + 1 since we will combine it with mid and
        # the lastkey if the last key is at the end of a previous bucket
        mid = int(self.__numsamples / 2) + 1

        # mean, mode and median
        occurances = 0
        lastkey = -1
        for i in keys:
            if mid > total and mid <= total + self.__samples[i]:
                # Test if numsamples is even and if mid+1 is the next bucket
                if self.__numsamples & 1 != 0 and mid == total+1:
                    self.__median = (lastkey + i) / 2
                else:
                    self.__median = i
            lastkey = i
            total += self.__samples[i]
            total_us += i * self.__samples[i]
            if self.__samples[i] > occurances:
                occurances = self.__samples[i]
                self.__mode = i
        self.__mean = float(total_us) / float(self.__numsamples)

        # range
        for i in keys:
            if self.__samples[i]:
                low = i
                break
        high = keys[-1]
        while high and self.__samples.get(high, 0) == 0:
            high -= 1
        self.__range = high - low

        # Mean Absolute Deviation and Standard Deviation
        madsum = 0
        varsum = 0
        for i in keys:
            madsum += float(abs(float(i) - self.__mean) * self.__samples[i])
            varsum += float(((float(i) - self.__mean) ** 2) * self.__samples[i])
        self.__mad = madsum / self.__numsamples
        self.__stddev = math.sqrt(varsum / (self.__numsamples - 1))


    def MakeReport(self):
        rep_n = libxml2.newNode(self.__type)

        if self.__type == 'system':
            rep_n.newProp('description', self.description)
        else:
            rep_n.newProp('id', str(self.__id))
            rep_n.newProp('priority', str(self.__priority))

        stat_n = rep_n.newChild(None, 'statistics', None)
        stat_n.newTextChild(None, 'samples', str(self.__numsamples))

        if self.__numsamples > 0:
            n = stat_n.newTextChild(None, 'minimum', str(self.min))
            n.newProp('unit', 'us')

            n = stat_n.newTextChild(None, 'maximum', str(self.max))
            n.newProp('unit', 'us')

            n = stat_n.newTextChild(None, 'median', str(self.__median))
            n.newProp('unit', 'us')

            n = stat_n.newTextChild(None, 'mode', str(self.__mode))
            n.newProp('unit', 'us')

            n = stat_n.newTextChild(None, 'range', str(self.__range))
            n.newProp('unit', 'us')

            n = stat_n.newTextChild(None, 'mean', str(self.__mean))
            n.newProp('unit', 'us')

            n = stat_n.newTextChild(None, 'mean_absolute_deviation', str(self.__mad))
            n.newProp('unit', 'us')

            n = stat_n.newTextChild(None, 'standard_deviation', str(self.__stddev))
            n.newProp('unit', 'us')

        hist_n = rep_n.newChild(None, 'histogram', None)
        hist_n.newProp('nbuckets', str(len(self.__samples)))

        keys = list(self.__samples.keys())
        keys.sort()
        for k in keys:
            if self.__samples[k] == 0:
                # Don't report buckets without any samples
                continue
            b_n = hist_n.newChild(None, 'bucket', None)
            b_n.newProp('index', str(k))
            b_n.newProp('value', str(self.__samples[k]))

        return rep_n

class Timerlat(rtevalModulePrototype):
    """ measurement modules for rteval """
    def __init__(self, config, logger=None):
        rtevalModulePrototype.__init__(self, 'measurement', 'timerlat', logger)

        self.__cfg = config

        self.__numanodes = int(self.__cfg.setdefault('numanodes', 0))
        self.__priority = int(self.__cfg.setdefault('priority', 95))
        default_buckets = ModuleParameters()["buckets"]["default"]
        self.__buckets = int(self.__cfg.setdefault('buckets', default_buckets))

        self.__cpulist = self.__cfg.setdefault('cpulist', "")
        self.__cpus = [str(c) for c in expand_cpulist(self.__cpulist)]
        self.__numcores = len(self.__cpus)

        self.__timerlat_out = None
        self.__timerlat_err = None
        self.__started = False

        # Create a TLRunData object for each core we'll measure
        info = cpuinfo()
        self.__timerlatdata = {}
        for core in self.__cpus:
            self.__timerlatdata[core] = TLRunData(core, 'core', self.__priority,
                                                logfnc=self._log)
            self.__timerlatdata[core].description = info[core]['model name']

        # Create a TLRunData object for the overall system
        self.__timerlatdata['system'] = TLRunData('system', 'system',
                                                  self.__priority,
                                                  logfnc=self._log)
        self.__timerlatdata['system'].description = (f"({self.__numcores} cores) ") + info['0']['model name']
        self._log(Log.DEBUG, f"system using {self.__numcores} cpu cores")


    def _WorkloadSetup(self):
        self.__timerlat_process = None

    def _WorkloadBuild(self):
        self._setReady()

    def _WorkloadPrepare(self):
        self.__cmd = ['rtla', 'timerlat', 'hist', '-P', f'f:{int(self.__priority)}', '-u']
        self.__cmd.append(f'-c{self.__cpulist}')
        self.__cmd.append(f'-E{self.__buckets}')
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

        # Parse histogram output
        self.__timerlat_out.seek(0)
        for line in self.__timerlat_out:
            line = bytes.decode(line)

            # Skip any blank lines
            if not line:
                continue

            if line.startswith('#'):
                if line.startswith('# Duration:'):
                    duration = line.split()[2]
                    duration += line.split()[3]
                    self.__timerlatdata['system'].duration = duration
                continue
            elif line.startswith('Index'):
                #print(line)
                continue
            elif line.startswith('over:'):
                #print(line)
                continue
            elif line.startswith('count:'):
                #print(line)
                continue
            elif line.startswith('min:'):
                #print(line)
                continue
            elif line.startswith('avg:'):
                #print(line)
                continue
            elif line.startswith('max:'):
                #print(line)
                continue
            else:
                pass
                #print(line)

            vals = line.split()
            if not vals:
                # If we don't have any values, don't try parsing
                continue
            try:
                # The index corresponds to the bucket number
                index = int(vals[0])
            except:
                self._log(Log.DEBUG, f'timerlat: unexpected output: {line}')
                continue

            for i, core in enumerate(self.__cpus):
                self.__timerlatdata[core].bucket(index, int(vals[i*3+1]),
                                                 int(vals[i*3+2]),
                                                 int(vals[i*3+3]))
                self.__timerlatdata['system'].bucket(index, int(vals[i*3+1]),
                                                 int(vals[i*3+2]),
                                                 int(vals[i*3+3]))
        # Generate statistics for each RunData object
        for n in list(self.__timerlatdata.keys()):
            self.__timerlatdata[n].reduce()

        self.__timerlat_out.close()

        self._setFinished()
        self.__started = False

    def MakeReport(self):
        rep_n = libxml2.newNode('timerlat')
        rep_n.newProp('command_line', ' '.join(self.__cmd))

        rep_n.addChild(self.__timerlatdata['system'].MakeReport())
        for thr in self.__cpus:
            if str(thr) not in self.__timerlatdata:
                continue
            rep_n.addChild(self.__timerlatdata[str(thr)].MakeReport())

        return rep_n


def ModuleInfo():
    """ Required measurement module information """
    return {"parallel": True,
            "loads": True}

def ModuleParameters():
    """ default parameters """
    return {"priority": {"descr": "Run rtla timerlat with this priority",
                         "default": 95,
                         "metavar": "PRIO" },
            "buckets":  {"descr": "Number of buckets",
                         "default": 3500,
                         "metavar": "NUM"}
           }

def create(params, logger):
    """ Instantiate a Timerlat measurement module object"""
    return Timerlat(params, logger)

if __name__ == '__main__':
    from rteval.rtevalConfig import rtevalConfig

    if os.getuid() != 0:
        print("Must be root to run timerlat!")
        sys.exit(1)

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
    rep_n = tl.MakeReport()

    xml = libxml2.newDoc('1.0')
    xml.setRootElement(rep_n)
    xml.saveFormatFileEnc('-', 'UTF-8', 1)
