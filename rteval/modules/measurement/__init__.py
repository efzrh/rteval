# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2012 - 2013   David Sommerseth <davids@redhat.com>
#

import libxml2
from rteval.modules import RtEvalModules, ModuleContainer
from rteval.systopology import parse_cpulist_from_config
import rteval.cpulist_utils as cpulist_utils

class MeasurementProfile(RtEvalModules):
    """Keeps and controls all the measurement modules with the same measurement profile"""

    def __init__(self, config, modules_root, logger):
        self._module_type = "measurement"
        self._module_config = "measurement"
        self._report_tag = "Profile"
        RtEvalModules.__init__(self, config, modules_root, logger)


    def ImportModule(self, module):
        "Imports an exported module from a ModuleContainer() class"
        return self._ImportModule(module)


    def Setup(self, modname):
        "Instantiates and prepares a measurement module"

        modobj = self._InstantiateModule(modname, self._cfg.GetSection(modname))
        self._RegisterModuleObject(modname, modobj)


class MeasurementModules:
    """Class which takes care of all measurement modules and groups them into
measurement profiles, based on their characteristics"""

    def __init__(self, config, logger):
        self.__cfg = config
        self.__logger = logger
        self.__measureprofiles = []
        self.__modules_root = "modules.measurement"
        self.__iter_item = None

        # Temporary module container, which is used to evalute measurement modules.
        # This will container will be destroyed after Setup() has been called
        self.__container = ModuleContainer(self.__modules_root, self.__logger)
        self.__LoadModules(self.__cfg.GetSection("measurement"))


    def __LoadModules(self, modcfg):
        "Loads and imports all the configured modules"

        for m in modcfg:
            # hope to eventually have different kinds but module is only on
            # for now (jcw)
            if m[1].lower() == 'module':
                self.__container.LoadModule(m[0])


    def GetProfile(self):
        "Returns the appropriate MeasurementProfile object, based on the profile type"

        for p in self.__measureprofiles:
            return p
        return None


    def SetupModuleOptions(self, parser):
        "Sets up all the measurement modules' parameters for the option parser"
        grparser = self.__container.SetupModuleOptions(parser, self.__cfg)

        # Set up options specific for measurement module group
        grparser.add_argument("--measurement-run-on-isolcpus",
                              dest="measurement___run_on_isolcpus",
                              action="store_true",
                              default=self.__cfg.GetSection("measurement").setdefault("run-on-isolcpus", "false").lower()
                                      == "true",
                              help="Include isolated CPUs in default cpulist")


    def Setup(self, modparams):
        "Loads all measurement modules and group them into different measurement profiles"

        if not isinstance(modparams, dict):
            raise TypeError("modparams attribute is not of a dictionary type")

        modcfg = self.__cfg.GetSection("measurement")
        cpulist = modcfg.cpulist
        run_on_isolcpus = modcfg.run_on_isolcpus
        if cpulist is None:
            # Get default cpulist value
            cpulist = cpulist_utils.collapse_cpulist(parse_cpulist_from_config("", run_on_isolcpus))

        for (modname, modtype) in modcfg:
            if isinstance(modtype, str) and modtype.lower() == 'module':  # Only 'module' will be supported (ds)
                self.__container.LoadModule(modname)

                # Get the correct measurement profile container for this module
                mp = self.GetProfile()
                if mp is None:
                    # If not found, create a new measurement profile
                    mp = MeasurementProfile(self.__cfg,
                                            self.__modules_root, self.__logger)
                    self.__measureprofiles.append(mp)

                    # Export the module imported here and transfer it to the
                    # measurement profile
                    mp.ImportModule(self.__container.ExportModule(modname))

                # Setup this imported module inside the appropriate measurement profile
                self.__cfg.AppendConfig(modname, modparams)
                self.__cfg.AppendConfig(modname, {'cpulist':cpulist})
                self.__cfg.AppendConfig(modname, {'run-on-isolcpus':run_on_isolcpus})
                mp.Setup(modname)

        del self.__container


    def MakeReport(self):
        "Generates an XML report for all measurement profiles"

        # Get the reports from all meaurement modules in all measurement profiles
        rep_n = libxml2.newNode("Measurements")
        cpulist = self.__cfg.GetSection("measurement").cpulist
        run_on_isolcpus = self.__cfg.GetSection("measurement").run_on_isolcpus
        cpulist = parse_cpulist_from_config(cpulist, run_on_isolcpus)
        rep_n.newProp("measurecpus", cpulist_utils.collapse_cpulist(cpulist))

        for mp in self.__measureprofiles:
            mprep_n = mp.MakeReport()
            if mprep_n:
                rep_n.addChild(mprep_n)

        return rep_n


    def __iter__(self):
        "Initiates an iteration loop for MeasurementProfile objects"

        self.__iter_item = len(self.__measureprofiles)
        return self


    def __next__(self):
        """Internal Python iterating method, returns the next
MeasurementProfile object to be processed"""

        if self.__iter_item == 0:
            self.__iter_item = None
            raise StopIteration

        self.__iter_item -= 1
        return self.__measureprofiles[self.__iter_item]
