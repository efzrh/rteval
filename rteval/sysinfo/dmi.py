# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2009 - 2013   Clark Williams <williams@redhat.com>
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#   Copyright 2022          John Kacur <jkacur@redhat.com>
#   Copyright 2024          Tomas Glozar <tglozar@redhat.com>
#
""" dmi.py class to wrap DMI Table Information """

import sys
import os
import libxml2
import lxml.etree
import shutil
import re
from subprocess import Popen, PIPE, SubprocessError
from rteval.Log import Log
from rteval import xmlout
from rteval import rtevalConfig


def get_dmidecode_xml(dmidecode_executable):
    """
    Transform human-readable dmidecode output into machine-processable XML format
    :param dmidecode_executable: Path to dmidecode tool executable
    :return: Tuple of values with resulting XML and dmidecode warnings
    """
    proc = Popen(dmidecode_executable, text=True, stdout=PIPE, stderr=PIPE)
    outs, errs = proc.communicate()
    parts = outs.split("\n\n")
    if len(parts) < 2:
        raise RuntimeError("Parsing dmidecode output failed")
    header = parts[0]
    handles = parts[1:]
    root = lxml.etree.Element("dmidecode")
    # Parse dmidecode output header
    # Note: Only supports SMBIOS data currently
    regex = re.compile(r"# dmidecode (\d+\.\d+)\n"
                       r"Getting SMBIOS data from sysfs\.\n"
                       r"SMBIOS ((?:\d+\.)+\d+) present\.\n"
                       r"(?:(\d+) structures occupying (\d+) bytes\.\n)?"
                       r"Table at (0x[0-9A-Fa-f]+)\.", re.MULTILINE)
    match = re.match(regex, header)
    if match is None:
        raise RuntimeError("Parsing dmidecode output failed")
    root.attrib["dmidecodeversion"] = match.group(1)
    root.attrib["smbiosversion"] = match.group(2)
    if match.group(3) is not None:
        root.attrib["structures"] = match.group(3)
    if match.group(4) is not None:
        root.attrib["size"] = match.group(4)
    root.attrib["address"] = match.group(5)

    # Generate element per handle in dmidecode output
    for handle_text in handles:
        if not handle_text:
            # Empty line
            continue

        handle = lxml.etree.Element("Handle")
        lines = handle_text.splitlines()
        # Parse handle header
        if len(lines) < 2:
            raise RuntimeError("Parsing dmidecode handle failed")
        header, name, content = lines[0], lines[1], lines[2:]
        match = re.match(r"Handle (0x[0-9A-Fa-f]{4}), "
                         r"DMI type (\d+), (\d+) bytes", header)
        if match is None:
            raise RuntimeError("Parsing dmidecode handle failed")
        handle.attrib["address"] = match.group(1)
        handle.attrib["type"] = match.group(2)
        handle.attrib["bytes"] = match.group(3)
        handle.attrib["name"] = name

        # Parse all fields in handle and create an element for each
        list_field = None
        for index, line in enumerate(content):
            line = content[index]
            if line.rfind("\t") > 0:
                # We are inside a list field, add value to it
                value = lxml.etree.Element("Value")
                value.text = line.strip()
                list_field.append(value)
                continue
            line = line.lstrip().split(":", 1)
            if len(line) != 2:
                raise RuntimeError("Parsing dmidecode field failed")
            if not line[1] or (index + 1 < len(content) and
                               content[index + 1].rfind("\t") > 0):
                # No characters after : or next line is inside list field
                # means a list field
                # Note: there are list fields which specify a number of
                # items, for example "Installable Languages", so merely
                # checking for no characters after : is not enough
                list_field = lxml.etree.Element("List")
                list_field.attrib["Name"] = line[0].strip()
                handle.append(list_field)
            else:
                # Regular field
                field = lxml.etree.Element("Field")
                field.attrib["Name"] = line[0].strip()
                field.text = line[1].strip()
                handle.append(field)

        root.append(handle)

    return root, errs


class DMIinfo:
    '''class used to obtain DMI info via dmidecode'''

    def __init__(self, logger=None):
        self.__version = '0.6'
        self._log = logger

        dmidecode_executable = shutil.which("dmidecode")
        if dmidecode_executable is None:
            logger.log(Log.DEBUG, "DMI info unavailable,"
                                  " ignoring DMI tables")
            self.__fake = True
            return

        self.__fake = False
        try:
            self.__dmixml, self.__warnings = get_dmidecode_xml(
                dmidecode_executable)
        except (RuntimeError, OSError, SubprocessError) as error:
            logger.log(Log.DEBUG, "DMI info unavailable: {};"
                                  " ignoring DMI tables".format(str(error)))
            self.__fake = True
            return

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

    def ProcessWarnings(self):
        """Prints out warnings from dmidecode into log if there were any"""
        if self.__fake or self._log is None:
            return
        for warnline in self.__warnings.split('\n'):
            if len(warnline) > 0:
                self._log.log(Log.DEBUG, f"** DMI WARNING ** {warnline}")

    def MakeReport(self):
        """ Add DMI information to final report """
        if self.__fake:
            rep_n = libxml2.newNode("DMIinfo")
            rep_n.newProp("version", self.__version)
            rep_n.addContent("No DMI tables available")
            rep_n.newProp("not_available", "1")
            return rep_n
        rep_n = xmlout.convert_lxml_to_libxml2_nodes(self.__dmixml)
        rep_n.setName("DMIinfo")
        rep_n.newProp("version", self.__version)
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

        if os.getuid() != 0:
            print("** ERROR **  Must be root to run this unit_test()")
            return 1

        d = DMIinfo(logger=log)
        d.ProcessWarnings()
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
