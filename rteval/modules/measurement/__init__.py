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

    def __init__(self, config, with_load, run_parallel, modules_root, logger):
        self.__with_load = with_load
        self.__run_parallel = run_parallel

        # Only used when running modules serialised
        self.__run_serialised_mods = None

        self._module_type = "measurement"
        self._module_config = "measurement"
        self._report_tag = "Profile"
        RtEvalModules.__init__(self, config, modules_root, logger)


    def GetProfile(self):
        "Returns the profile characteristic as (with_load, run_parallel)"
        return (self.__with_load, self.__run_parallel)


    def ImportModule(self, module):
        "Imports an exported module from a ModuleContainer() class"
        return self._ImportModule(module)


    def Setup(self, modname):
        "Instantiates and prepares a measurement module"

        modobj = self._InstantiateModule(modname, self._cfg.GetSection(modname))
        self._RegisterModuleObject(modname, modobj)


    def Unleash(self):
        """Unleashes all the measurement modules"""

        if self.__run_parallel:
            # Use the inherrited method if running
            # measurements in parallel
            return RtEvalModules.Unleash(self)

        # Get a list of all registered modules,
        # and start the first one
        self.__serialised_mods = self.GetModulesList()
        mod = self.GetNamedModuleObject(self.__serialised_mods[0])
        mod.setStart()
        return 1


    def MakeReport(self):
        "Generates an XML report for all run measurement modules in this profile"
        rep_n = RtEvalModules.MakeReport(self)
        rep_n.newProp("loads", self.__with_load and "1" or "0")
        rep_n.newProp("parallel", self.__run_parallel and "1" or "0")
        return rep_n


    def isAlive(self):
        """Returns True if all modules which are supposed to run runs"""

        if self.__run_parallel:
            return self._isAlive()

        if self.__serialised_mods:
            # If running serialised, first check if measurement is still running,
            # if so - return True.
            mod = self.GetNamedModuleObject(self.__serialised_mods[0])
            if mod.WorkloadAlive():
                return True

            # If not, go to next on the list and kick it off
            self.__serialised_mods.remove(self.__serialised_mods[0])
            if self.__serialised_mods:
                mod = self.GetNamedModuleObject(self.__serialised_mods[0])
                mod.setStart()
                return True

        # If we've been through everything, nothing is running
        return False


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


    def GetProfile(self, with_load, run_parallel):
        "Returns the appropriate MeasurementProfile object, based on the profile type"

        for p in self.__measureprofiles:
            mp = p.GetProfile()
            if mp == (with_load, run_parallel):
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

        for (modname, modtype) in modcfg:
            if isinstance(modtype, str) and modtype.lower() == 'module':  # Only 'module' will be supported (ds)
                # Extract the measurement modules info
                modinfo = self.__container.ModuleInfo(modname)

                # Get the correct measurement profile container for this module
                mp = self.GetProfile(modinfo["loads"], modinfo["parallel"])
                if mp is None:
                    # If not found, create a new measurement profile
                    mp = MeasurementProfile(self.__cfg,
                                            modinfo["loads"], modinfo["parallel"],
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
