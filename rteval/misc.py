#!/usr/bin/python3 -tt
#
# Copyright (C) 2015 Clark Williams <clark.williams@gmail.com>
# Copyright (C) 2015 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
''' Functions for operating on a cpulists '''


import os
import glob

# expand a string range into a list
# don't error check against online cpus
def expand_cpulist(cpulist):
    '''expand a range string into an array of cpu numbers'''
    result = []
    for part in cpulist.split(','):
        if '-' in part:
            a, b = part.split('-')
            a, b = int(a), int(b)
            result.extend(list(range(a, b + 1)))
        else:
            a = int(part)
            result.append(a)
    return [str(i) for i in list(set(result))]

def online_cpus():
    ''' Collapse a list of cpu numbers into a string range '''
    online_cpus = []
    # Check for the online file with cpu1 since cpu0 can't always be offlined
    if os.path.exists('/sys/devices/system/cpu/cpu1/online'):
        for c in glob.glob('/sys/devices/system/cpu/cpu[0-9]*'):
            num = str(c.replace('/sys/devices/system/cpu/cpu', ''))
            # On some machine you can't turn off cpu0
            if not os.path.exists(c + '/online') and num == "0":
                online_cpus.append(num)
            else:
                with open(c + '/online') as f:
                    is_online = f.read().rstrip('\n')
                if is_online == "1":
                    online_cpus.append(num)
    else: # use the old heuristic
        for c in glob.glob('/sys/devices/system/cpu/cpu[0-9]*'):
            num = str(c.replace('/sys/devices/system/cpu/cpu', ''))
            online_cpus.append(num)
    return online_cpus

def invert_cpulist(cpulist):
    ''' return a list of online cpus not in cpulist '''
    return [c for c in online_cpus() if c not in cpulist]

def compress_cpulist(cpulist):
    ''' return a string representation of cpulist '''
    if isinstance(cpulist[0], int):
        return ",".join(str(e) for e in cpulist)
    return ",".join(cpulist)

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

if __name__ == "__main__":

    info = cpuinfo()
    idx = sorted(info.keys())
    for i in idx:
        print("%s: %s" % (i, info[i]))

    print("0: %s" % (info['0']['model name']))
