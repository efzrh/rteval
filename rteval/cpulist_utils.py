# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2016 - Clark Williams <williams@redhat.com>
#   Copyright 2021 - John Kacur <jkacur@redhat.com>
#   Copyright 2023 - Tomas Glozar <tglozar@redhat.com>
#
"""Module providing utility functions for working with CPU lists"""

import os


cpupath = "/sys/devices/system/cpu"


def sysread(path, obj):
    """ Helper function for reading system files """
    with open(os.path.join(path, obj), "r") as fp:
        return fp.readline().strip()


def _online_file_exists():
    """ Check whether machine / kernel is configured with online file """
    # Note: some machines do not have cpu0/online so we check cpu1/online.
    # In the case of machines with a single CPU, there is no cpu1, but
    # that is not a problem, since a single CPU cannot be offline
    return os.path.exists(os.path.join(cpupath, "cpu1/online"))


def _isolated_file_exists():
    """ Check whether machine / kernel is configured with isolated file """
    return os.path.exists(os.path.join(cpupath, "isolated"))


def collapse_cpulist(cpulist):
    """
    Collapse a list of cpu numbers into a string range
    of cpus (e.g. 0-5, 7, 9)
    """
    cur_range = [None, None]
    result = []
    for cpu in cpulist + [None]:
        if cur_range[0] is None:
            cur_range[0] = cur_range[1] = cpu
            continue
        if cpu is not None and cpu == cur_range[1] + 1:
            # Extend currently processed range
            cur_range[1] += 1
        else:
            # Range processing finished, add range to string
            result.append(f"{cur_range[0]}-{cur_range[1]}"
                          if cur_range[0] != cur_range[1]
                          else str(cur_range[0]))
            # Reset
            cur_range[0] = cur_range[1] = cpu
    return ",".join(result)


def compress_cpulist(cpulist):
    """ return a string representation of cpulist """
    if not cpulist:
        return ""
    if isinstance(cpulist[0], int):
        return ",".join(str(e) for e in cpulist)
    return ",".join(cpulist)


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


def is_online(n):
    """ check whether cpu n is online """
    path = os.path.join(cpupath, f'cpu{n}')

    # Some hardware doesn't allow cpu0 to be turned off
    if not os.path.exists(path + '/online') and n == 0:
        return True

    return sysread(path, "online") == "1"


def online_cpulist(cpulist):
    """ Given a cpulist, return a cpulist of online cpus """
    # This only works if the sys online files exist
    if not _online_file_exists():
        return cpulist
    newlist = []
    for cpu in cpulist:
        if not _online_file_exists() and cpu == '0':
            newlist.append(cpu)
        elif is_online(int(cpu)):
            newlist.append(cpu)
    return newlist


def isolated_cpulist(cpulist):
    """Given a cpulist, return a cpulist of isolated CPUs"""
    if not _isolated_file_exists():
        return cpulist
    isolated_cpulist = sysread(cpupath, "isolated")
    isolated_cpulist = expand_cpulist(isolated_cpulist)
    return list(set(isolated_cpulist) & set(cpulist))


def nonisolated_cpulist(cpulist):
    """Given a cpulist, return a cpulist of non-isolated CPUs"""
    if not _isolated_file_exists():
        return cpulist
    isolated_cpulist = sysread(cpupath, "isolated")
    isolated_cpulist = expand_cpulist(isolated_cpulist)
    return list(set(cpulist).difference(set(isolated_cpulist)))
