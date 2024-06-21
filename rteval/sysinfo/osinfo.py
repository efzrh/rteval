# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2009 - 2013   Clark Williams <williams@redhat.com>
#   Copyright 2012 - 2013   David Sommerseth <davids@redhat.com>
#

import os
import shutil
import subprocess
from glob import glob
import libxml2
from rteval.Log import Log

class OSInfo:
    def __init__(self, logger):
        self.__logger = logger


    def get_base_os(self):
        '''record what userspace we're running on'''
        distro = "unknown"
        for f in ('redhat-release', 'fedora-release'):
            p = os.path.join('/etc', f)
            if os.path.exists(p):
                f = open(p, 'r')
                distro = f.readline().strip()
                f.close()
                break
        return distro


    def copy_dmesg(self, repdir):
        dpath = "/var/log/dmesg"
        if os.path.exists(dpath):
            shutil.copyfile(dpath, os.path.join(repdir, "dmesg"))
            return
        if os.path.exists('/usr/bin/dmesg'):
            subprocess.call(f'/usr/bin/dmesg > {os.path.join(repdir, "dmesg")}', shell=True)
            return
        print(f"dmesg file not found at {dpath} and no dmesg exe found!")



    def run_sysreport(self, repdir):
        if os.path.exists('/usr/sbin/sos'):
            exe = '/usr/sbin/sos report'
        elif os.path.exists('/usr/bin/sos'):
            exe = '/usr/bin/sos report'
        elif os.path.exists('/usr/sbin/sosreport'):
            exe = '/usr/sbin/sosreport'
        elif os.path.exists('/usr/bin/sosreport'):
            exe = '/usr/bin/sosreport'
        elif os.path.exists('/usr/sbin/sysreport'):
            exe = '/usr/sbin/sysreport'
        elif os.path.exists('/usr/bin/sysreport'):
            exe = '/usr/bin/sysreport'
        else:
            raise RuntimeError("Can't find sos/sosreport/sysreport")

        self.__logger.log(Log.DEBUG, f"report tool: {exe}")
        options = ['-k', 'rpm.rpmva=off',
                   '--name=rteval',
                   '--batch']

        self.__logger.log(Log.INFO, "Generating SOS report")
        self.__logger.log(Log.INFO, f"using command {' '.join(exe.split()+options)}")
        subprocess.call(exe.split() + options)
        for s in glob('/tmp/s?sreport-rteval-*'):
            self.__logger.log(Log.DEBUG, f"moving {s} to {repdir}")
            shutil.move(s, repdir)


    def MakeReport(self):
        rep_n = libxml2.newNode("uname")

        baseos_n = libxml2.newNode("baseos")
        baseos_n.addContent(self.get_base_os())
        rep_n.addChild(baseos_n)

        (sys, node, release, ver, machine) = os.uname()
        isrt = 1
        if 'RT ' not in ver:
            isrt = 0

        node_n = libxml2.newNode("node")
        node_n.addContent(node)
        rep_n.addChild(node_n)

        arch_n = libxml2.newNode("arch")
        arch_n.addContent(machine)
        rep_n.addChild(arch_n)

        kernel_n = libxml2.newNode("kernel")
        kernel_n.newProp("is_RT", str(isrt))
        kernel_n.addContent(release)
        rep_n.addChild(kernel_n)

        return rep_n



def unit_test(rootdir):
    import sys

    try:
        log = Log()
        log.SetLogVerbosity(Log.DEBUG|Log.INFO)
        osi = OSInfo(logger=log)
        print(f"Base OS: {osi.get_base_os()}")

        print("Testing OSInfo::copy_dmesg('/tmp'): ", end=' ')
        osi.copy_dmesg('/tmp')
        if os.path.isfile("/tmp/dmesg") and os.path.isfile("/var/log/dmesg"):
            md5orig = subprocess.check_output(("md5sum", "/var/log/dmesg"))
            md5copy = subprocess.check_output(("md5sum", "/tmp/dmesg"))
            if md5orig.split(" ")[0] == md5copy.split(" ")[0]:
                print("PASS")
            else:
                print("FAIL (md5sum)")
            os.unlink("/tmp/dmesg")
        else:
            print("FAIL (copy failed)")

        print("Running sysreport/sosreport with output to current dir")
        osi.run_sysreport(".")

        osinfo_xml = osi.MakeReport()
        xml_d = libxml2.newDoc("1.0")
        xml_d.setRootElement(osinfo_xml)
        xml_d.saveFormatFileEnc("-", "UTF-8", 1)

    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        print("** EXCEPTION %s", str(e))
        return 1

if __name__ == '__main__':
    unit_test(None)
