# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2009 - 2013   Clark Williams <williams@redhat.com>
#   Copyright 2012 - 2013   David Sommerseth <davids@redhat.com>
#

from glob import glob
import libxml2

class MemoryInfo:
    numa_nodes = None

    def __init__(self):
        pass


    def mem_get_numa_nodes(self):
        if self.numa_nodes is None:
            self.numa_nodes = len(glob('/sys/devices/system/node/node*'))
        return self.numa_nodes


    @staticmethod
    def mem_get_size():
        '''find out how much memory is installed'''
        f = open('/proc/meminfo')
        rawsize = 0
        for l in f:
            if l.startswith('MemTotal:'):
                parts = l.split()
                if parts[2].lower() != 'kb':
                    raise RuntimeError(f"Units changed from kB! ({parts[2]})")
                rawsize = int(parts[1])
                f.close()
                break
        if rawsize == 0:
            raise RuntimeError("can't find memtotal in /proc/meminfo!")

        # Get a more readable result
        # Note that this depends on  /proc/meminfo starting in Kb
        units = ('KB', 'MB', 'GB', 'TB')
        size = rawsize
        for unit in units:
            if size < (1024*1024):
                break
            size = float(size) / 1024
        return (size, unit)


    def MakeReport(self):
        rep_n = libxml2.newNode("Memory")

        numa_n = libxml2.newNode("numa_nodes")
        numa_n.addContent(str(self.mem_get_numa_nodes()))
        rep_n.addChild(numa_n)

        memsize = self.mem_get_size()
        mem_n = libxml2.newNode("memory_size")
        mem_n.addContent(f"{memsize[0]:.3f}")
        mem_n.newProp("unit", memsize[1])
        rep_n.addChild(mem_n)

        return rep_n



def unit_test(rootdir):
    import sys
    try:
        mi = MemoryInfo()
        print(f"Numa nodes: {mi.mem_get_numa_nodes()}")
        print(f"Memory: {int(mi.mem_get_size()[0])} {mi.mem_get_size()[1]}")
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        print("** EXCEPTION %s", str(e))
        return 1
    return 0

if __name__ == '__main__':
    unit_test(None)
