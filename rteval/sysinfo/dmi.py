# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2009 - 2013   Clark Williams <williams@redhat.com>
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#   Copyright 2022          John Kacur <jkacur@redhat.com>
#
""" dmi.py class to wrap DMI Table Information """

import sys
import os
import libxml2
import lxml.etree
from rteval.Log import Log
from rteval import xmlout
from rteval import rtevalConfig

try:
    import dmidecode
    dmidecode_avail = True
except ModuleNotFoundError:
    dmidecode_avail = False

def set_dmidecode_avail(val):
    """ Used to set global variable dmidecode_avail from a function """
    global dmidecode_avail
    dmidecode_avail = val

def ProcessWarnings(logger=None):
    """ Process Warnings from dmidecode """

    if not dmidecode_avail:
        return

    if not hasattr(dmidecode, 'get_warnings'):
        return

    warnings = dmidecode.get_warnings()
    if warnings is None:
        return

    ignore1  = '/dev/mem: Permission denied'
    ignore2 = 'No SMBIOS nor DMI entry point found, sorry.'
    ignore3 = 'Failed to open memory buffer (/dev/mem): Permission denied'
    ignore = (ignore1, ignore2, ignore3)
    for warnline in warnings.split('\n'):
        # Ignore these warnings, as they are "valid" if not running as root
        if warnline in ignore:
            continue

        # All other warnings will be printed
        if len(warnline) > 0:
            logger.log(Log.DEBUG, f"** DMI WARNING ** {warnline}")
            set_dmidecode_avail(False)

    dmidecode.clear_warnings()


class DMIinfo:
    '''class used to obtain DMI info via python-dmidecode'''

    def __init__(self, logger=None):
        self.__version = '0.6'
        self._log = logger

        if not dmidecode_avail:
            logger.log(Log.DEBUG, "DMI info unavailable, ignoring DMI tables")
            self.__fake = True
            return

        self.__fake = False
        self.__dmixml = dmidecode.dmidecodeXML()

        self.__xsltparser = self.__load_xslt('rteval_dmi.xsl')

    @staticmethod
    def __load_xslt(fname):
        xsltf = None
        if os.path.exists(fname):
            xsltf = fname
        else:
            xsltf = rtevalConfig.default_config_search([fname], os.path.isfile)

        if xsltf:
            with open(xsltf, "r") as xsltfile:
                xsltdoc = lxml.etree.parse(xsltfile)
                ret = lxml.etree.XSLT(xsltdoc)
            return ret

        raise RuntimeError(f'Could not locate XSLT template for DMI data ({fname})')

    def MakeReport(self):
        """ Add DMI information to final report """
        rep_n = libxml2.newNode("DMIinfo")
        rep_n.newProp("version", self.__version)
        if self.__fake:
            rep_n.addContent("No DMI tables available")
            rep_n.newProp("not_available", "1")
        else:
            self.__dmixml.SetResultType(dmidecode.DMIXML_DOC)
            try:
                dmiqry = xmlout.convert_libxml2_to_lxml_doc(self.__dmixml.QuerySection('all'))
            except Exception as ex1:
                self._log.log(Log.DEBUG, f'** EXCEPTION {str(ex1)}, will query BIOS only')
                try:
                    # If we can't query 'all', at least query 'bios'
                    dmiqry = xmlout.convert_libxml2_to_lxml_doc(self.__dmixml.QuerySection('bios'))
                except Exception as ex2:
                    rep_n.addContent("No DMI tables available")
                    rep_n.newProp("not_available", "1")
                    self._log.log(Log.DEBUG, f'** EXCEPTION {str(ex2)}, dmi info will not be reported')
                    return rep_n
            resdoc = self.__xsltparser(dmiqry)
            dmi_n = xmlout.convert_lxml_to_libxml2_nodes(resdoc.getroot())
            rep_n.addChild(dmi_n)
        return rep_n

def unit_test(rootdir):
    """ unit_test for dmi.py """

    class UnittestConfigDummy:
        def __init__(self, rootdir):
            self.config = {'installdir': '/usr/share/rteval'}
            self.__update_vars()

        def __update_vars(self):
            for k in list(self.config.keys()):
                self.__dict__[k] = self.config[k]

    try:
        log = Log()
        log.SetLogVerbosity(Log.DEBUG|Log.INFO)

        ProcessWarnings(logger=log)
        if os.getuid() != 0:
            print("** ERROR **  Must be root to run this unit_test()")
            return 1

        d = DMIinfo(logger=log)
        dx = d.MakeReport()
        x = libxml2.newDoc("1.0")
        x.setRootElement(dx)
        x.saveFormatFileEnc("-", "UTF-8", 1)
        return 0
    except Exception as e:
        print(f"** EXCEPTION: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(unit_test('.'))
