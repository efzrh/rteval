# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2016 - Clark Williams <williams@redhat.com>
#   Copyright 2021 - John Kacur <jkacur@redhat.com>
#
""" Module for querying cpu cores and nodes """

import os
import os.path
import glob

# Utility version of collapse_cpulist that doesn't require a CpuList object
def collapse_cpulist(cpulist):
    """ Collapse a list of cpu numbers into a string range
        of cpus (e.g. 0-5, 7, 9) """
    if len(cpulist) == 0:
        return ""
    idx = CpuList.longest_sequence(cpulist)
    if idx == 0:
        seq = str(cpulist[0])
    else:
        if idx == 1:
            seq = f"{cpulist[0]},{cpulist[idx]}"
        else:
            seq = f"{cpulist[0]}-{cpulist[idx]}"

    rest = collapse_cpulist(cpulist[idx+1:])
    if rest == "":
        return seq
    return ",".join((seq, rest))

def sysread(path, obj):
    """ Helper function for reading system files """
    with open(os.path.join(path, obj), "r") as fp:
        return fp.readline().strip()

def cpuinfo():
    ''' return a dictionary of cpu keys with various cpu information '''
    core = -1
    info = {}
    with open('/proc/cpuinfo') as fp:
        for l in fp:
            l = l.strip()
            if not l:
                continue
            # Split a maximum of one time. In case a model name has ':' in it
            key, val = [i.strip() for i in l.split(':', 1)]
            if key == 'processor':
                core = val
                info[core] = {}
                continue
            info[core][key] = val

    for (core, pcdict) in info.items():
        if not 'model name' in pcdict:
            # On Arm CPU implementer is present
            # Construct the model_name from the following fields
            if 'CPU implementer' in pcdict:
                model_name = [pcdict.get('CPU implementer')]
                model_name.append(pcdict.get('CPU architecture'))
                model_name.append(pcdict.get('CPU variant'))
                model_name.append(pcdict.get('CPU part'))
                model_name.append(pcdict.get('CPU revision'))

                # If a list item is None, remove it
                model_name = [name for name in model_name if name]

                # Convert the model_name list into a string
                model_name = " ".join(model_name)
                pcdict['model name'] = model_name
            else:
                pcdict['model name'] = 'Unknown'

    return info


#
# class to provide access to a list of cpus
#

class CpuList:
    "Object that represents a group of system cpus"

    cpupath = '/sys/devices/system/cpu'

    def __init__(self, cpulist):
        if isinstance(cpulist, list):
            self.cpulist = cpulist
        elif isinstance(cpulist, str):
            self.cpulist = self.expand_cpulist(cpulist)
        self.cpulist = self.online_cpulist(self.cpulist)
        self.cpulist.sort()

    def __str__(self):
        return self.__collapse_cpulist(self.cpulist)

    def __contains__(self, cpu):
        return cpu in self.cpulist

    def __len__(self):
        return len(self.cpulist)

    @staticmethod
    def online_file_exists():
        """ Check whether machine / kernel is configured with online file """
        if os.path.exists('/sys/devices/system/cpu/cpu1/online'):
            return True
        return False

    @staticmethod
    def isolated_file_exists():
        """ Check whether machine / kernel is configured with isolated file """
        return os.path.exists(os.path.join(CpuList.cpupath, "isolated"))

    @staticmethod
    def longest_sequence(cpulist):
        """ return index of last element of a sequence that steps by one """
        lim = len(cpulist)
        for idx, _ in enumerate(cpulist):
            if idx+1 == lim:
                break
            if int(cpulist[idx+1]) != (int(cpulist[idx])+1):
                return idx
        return lim - 1

    def __collapse_cpulist(self, cpulist):
        """ Collapse a list of cpu numbers into a string range
        of cpus (e.g. 0-5, 7, 9)
        """
        if len(cpulist) == 0:
            return ""
        idx = self.longest_sequence(cpulist)
        if idx == 0:
            seq = str(cpulist[0])
        else:
            if idx == 1:
                seq = f"{cpulist[0]},{cpulist[idx]}"
            else:
                seq = f"{cpulist[0]}-{cpulist[idx]}"

        rest = self.__collapse_cpulist(cpulist[idx+1:])
        if rest == "":
            return seq
        return ",".join((seq, rest))

    @staticmethod
    def compress_cpulist(cpulist):
        """ return a string representation of cpulist """
        if isinstance(cpulist[0], int):
            return ",".join(str(e) for e in cpulist)
        return ",".join(cpulist)

    @staticmethod
    def expand_cpulist(cpulist):
        """ expand a range string into an array of cpu numbers
        don't error check against online cpus
        """
        result = []

        if not cpulist:
            return result

        for part in cpulist.split(','):
            if '-' in part:
                a, b = part.split('-')
                a, b = int(a), int(b)
                result.extend(list(range(a, b + 1)))
            else:
                a = int(part)
                result.append(a)
        return [int(i) for i in list(set(result))]

    def getcpulist(self):
        """ return the list of cpus tracked """
        return self.cpulist

    def is_online(self, n):
        """ check whether cpu n is online """
        if n not in self.cpulist:
            raise RuntimeError(f"invalid cpu number {n}")
        path = os.path.join(CpuList.cpupath, f'cpu{n}')

        # Some hardware doesn't allow cpu0 to be turned off
        if not os.path.exists(path + '/online') and n == 0:
            return True

        return sysread(path, "online") == "1"

    def online_cpulist(self, cpulist):
        """ Given a cpulist, return a cpulist of online cpus """
        # This only works if the sys online files exist
        if not self.online_file_exists():
            return cpulist
        newlist = []
        for cpu in cpulist:
            if not self.online_file_exists() and cpu == '0':
                newlist.append(cpu)
            elif self.is_online(int(cpu)):
                newlist.append(cpu)
        return newlist

    @staticmethod
    def isolated_cpulist(cpulist):
        """Given a cpulist, return a cpulist of isolated CPUs"""
        if not CpuList.isolated_file_exists():
            return cpulist
        isolated_cpulist = sysread(CpuList.cpupath, "isolated")
        isolated_cpulist = CpuList.expand_cpulist(isolated_cpulist)
        return list(set(isolated_cpulist) & set(cpulist))

    @staticmethod
    def nonisolated_cpulist(cpulist):
        """Given a cpulist, return a cpulist of non-isolated CPUs"""
        if not CpuList.isolated_file_exists():
            return cpulist
        isolated_cpulist = sysread(CpuList.cpupath, "isolated")
        isolated_cpulist = CpuList.expand_cpulist(isolated_cpulist)
        return list(set(cpulist).difference(set(isolated_cpulist)))

#
# class to abstract access to NUMA nodes in /sys filesystem
#

class NumaNode:
    "class representing a system NUMA node"

    def __init__(self, path):
        """ constructor argument is the full path to the /sys node file
        e.g. /sys/devices/system/node/node0
        """
        self.path = path
        self.nodeid = int(os.path.basename(path)[4:].strip())
        self.cpus = CpuList(sysread(self.path, "cpulist"))
        self.getmeminfo()

    def __contains__(self, cpu):
        """ function for the 'in' operator """
        return cpu in self.cpus

    def __len__(self):
        """ allow the 'len' builtin """
        return len(self.cpus)

    def __str__(self):
        """ string representation of the cpus for this node """
        return self.getcpustr()

    def __int__(self):
        return self.nodeid

    def getmeminfo(self):
        """ read info about memory attached to this node """
        self.meminfo = {}
        with open(os.path.join(self.path, "meminfo"), "r") as fp:
            for l in fp:
                elements = l.split()
                key = elements[2][0:-1]
                val = int(elements[3])
                if len(elements) == 5 and elements[4] == "kB":
                    val *= 1024
                self.meminfo[key] = val

    def getcpustr(self):
        """ return list of cpus for this node as a string """
        return str(self.cpus)

    def getcpulist(self):
        """ return list of cpus for this node """
        return self.cpus.getcpulist()

class SimNumaNode(NumaNode):
    """class representing a simulated NUMA node.
    For systems which don't have NUMA enabled (no
    /sys/devices/system/node) such as Arm v7
    """

    cpupath = '/sys/devices/system/cpu'
    mempath = '/proc/meminfo'

    def __init__(self):
        self.nodeid = 0
        self.cpus = CpuList(sysread(SimNumaNode.cpupath, "possible"))
        self.getmeminfo()

    def getmeminfo(self):
        self.meminfo = {}
        with open(SimNumaNode.mempath, "r") as fp:
            for l in fp:
                elements = l.split()
                key = elements[0][0:-1]
                val = int(elements[1])
                if len(elements) == 3 and elements[2] == "kB":
                    val *= 1024
                self.meminfo[key] = val

#
# Class to abstract the system topology of numa nodes and cpus
#
class SysTopology:
    "Object that represents the system's NUMA-node/cpu topology"

    cpupath = '/sys/devices/system/cpu'
    nodepath = '/sys/devices/system/node'

    def __init__(self):
        self.nodes = {}
        self.getinfo()
        self.current = 0

    def __len__(self):
        return len(list(self.nodes.keys()))

    def __str__(self):
        s = f"{len(list(self.nodes.keys()))} node system "
        s += f"({(len(self.nodes[list(self.nodes.keys())[0]]))} cores per node)"
        return s

    def __contains__(self, node):
        """ inplement the 'in' function """
        for n in self.nodes:
            if self.nodes[n].nodeid == node:
                return True
        return False

    def __getitem__(self, key):
        """ allow indexing for the nodes """
        return self.nodes[key]

    def __iter__(self):
        """ allow iteration over the cpus for the node """
        return self

    def __next__(self):
        """ iterator function """
        if self.current >= len(self.nodes):
            raise StopIteration
        n = self.nodes[self.current]
        self.current += 1
        return n

    def getinfo(self):
        """ Initialize class Systopology """
        nodes = glob.glob(os.path.join(SysTopology.nodepath, 'node[0-9]*'))
        if nodes:
            nodes.sort()
            for n in nodes:
                node = int(os.path.basename(n)[4:])
                self.nodes[node] = NumaNode(n)
        else:
            self.nodes[0] = SimNumaNode()

    def getnodes(self):
        """ return a list of nodes """
        return list(self.nodes.keys())

    def getcpus(self, node):
        """ return a dictionary of cpus keyed with the node """
        return self.nodes[node].getcpulist()

    def online_cpus(self):
        """ return a list of integers of all online cpus """
        cpulist = []
        for n in self.nodes:
            cpulist += self.getcpus(n)
        cpulist.sort()
        return cpulist

    def isolated_cpus(self):
        """ return a list of integers of all isolated cpus """
        cpulist = []
        for n in self.nodes:
            cpulist += CpuList.isolated_cpulist(self.getcpus(n))
        cpulist.sort()
        return cpulist

    def default_cpus(self):
        """ return a list of integers of all default schedulable cpus, i.e. online non-isolated cpus """
        cpulist = []
        for n in self.nodes:
            cpulist += CpuList.nonisolated_cpulist(self.getcpus(n))
        cpulist.sort()
        return cpulist

    def online_cpus_str(self):
        """ return a list of strings of numbers of all online cpus """
        cpulist = [str(cpu) for cpu in self.online_cpus()]
        return cpulist

    def isolated_cpus_str(self):
        """ return a list of strings of numbers of all isolated cpus """
        cpulist = [str(cpu) for cpu in self.isolated_cpus()]
        return cpulist

    def default_cpus_str(self):
        """ return a list of strings of numbers of all default schedulable cpus """
        cpulist = [str(cpu) for cpu in self.default_cpus()]
        return cpulist

    def invert_cpulist(self, cpulist):
        """ return a list of online cpus not in cpulist """
        return [c for c in self.online_cpus() if c not in cpulist]

    def online_cpulist(self, cpulist):
        """ return a list of online cpus in cpulist """
        return [c for c in self.online_cpus() if c in cpulist]

if __name__ == "__main__":

    def unit_test():
        """ unit test, run python rteval/systopology.py """
        s = SysTopology()
        print(s)
        print(f"number of nodes: {len(s)}")
        for n in s:
            print(f"node[{n.nodeid}]: {n}")
        print(f"system has numa node 0: {0 in s}")
        print(f"system has numa node 2: {2 in s}")
        print(f"system has numa node 24: {24 in s}")

        cpus = {}
        print(f"nodes = {s.getnodes()}")
        for node in s.getnodes():
            cpus[node] = s.getcpus(int(node))
            print(f'cpus = {cpus}')

        onlcpus = s.online_cpus()
        print(f'onlcpus = {onlcpus}')
        onlcpus = collapse_cpulist(onlcpus)
        print(f'onlcpus = {onlcpus}')

        onlcpus_str = s.online_cpus_str()
        print(f'onlcpus_str = {onlcpus_str}')

        print(f"invert of [ 2, 4, 5 ] = {s.invert_cpulist([2, 3, 4])}")
    unit_test()
