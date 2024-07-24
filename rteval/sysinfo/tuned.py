# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2024          Tomas Glozar <tglozar@redhat.com>
#
"""tuned sysinfo module"""
import shutil
import subprocess
import sys
import libxml2
from rteval.Log import Log

TUNED_ADM = "tuned-adm"
TUNED_LOG_PATH = "/var/log/tuned/tuned.log"
TUNED_VERIFY_START_LINE = "INFO     tuned.daemon.daemon: verifying " \
                          "profile(s): realtime"


def tuned_present():
    """
    Checks if tuned is present on the system
    :return: True if tuned is present, False otherwise
    """
    return shutil.which(TUNED_ADM) is not None


def tuned_active_profile():
    """
    Gets tuned active profile.
    :return: Tuned profile (as a string) or "unknown"
    """
    try:
        result = subprocess.check_output([TUNED_ADM, "active"])
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    result = result.decode("utf-8")
    split_result = result.split(": ")
    if len(split_result) < 2:
        return "unknown"
    return split_result[1].strip()


def tuned_verify():
    """
    Verifies if tuned profile is applied properly
    :return: "success", "failure" or "unknown"
    """
    try:
        result = subprocess.run([TUNED_ADM, "verify"],
                                stdout=subprocess.PIPE, check=False).stdout
    except (OSError, subprocess.CalledProcessError):
        return "unknown"
    result = result.decode("utf-8")
    if result.startswith("Verification succeeded"):
        return "success"
    if result.startswith("Verification failed"):
        return "failure"
    return "unknown"


def tuned_get_log():
    """
    Read entries related to last profile verification from tuned log
    :return: List of strings containing the entires, or None if no
    verification is found in the log
    """
    try:
        with open(TUNED_LOG_PATH, "r", encoding="utf-8") as file:
            lines = file.readlines()
            # Find start of last verification
            start = None
            for i in reversed(range(len(lines))):
                if TUNED_VERIFY_START_LINE in lines[i]:
                    start = i
                    break
            if start is None:
                return None
            return lines[start:]
    except OSError:
        return None


class TunedInfo:
    """
    Gather information about tuned and make an XML report.
    Collected information:
    - whether tuned is present
    - which tuned profile is active
    - whether the tuned profile is applied correctly
    - if not applied correctly, collect relevant info from log
    """
    def __init__(self, logger=None):
        self.__logger = logger

    def __log(self, logtype, msg):
        if self.__logger:
            self.__logger.log(logtype, msg)

    def tuned_state_get(self):
        """
        Gets the state of tuned on the machine
        :return: A dictionary describing the tuned state
        """
        result = {
            "present": tuned_present()
        }
        if not result["present"]:
            self.__log(Log.DEBUG, "tuned-adm not found; skipping tuned "
                                  "sysinfo collection")
            return result
        result["active_profile"] = tuned_active_profile()
        if result["active_profile"] == "unknown":
            self.__log(Log.DEBUG, "could not retrieve tuned active profile")
            return result
        result["verified"] = tuned_verify()
        if result["verified"] == "unknown":
            self.__log(Log.DEBUG, "could not verify tuned state")
        if result["verified"] == "failure":
            # Include log to see cause to failure
            result["verification_log"] = tuned_get_log()

        return result

    def MakeReport(self):
        """
        Create XML report
        :return: libxml2 node containing the report
        """
        tuned = self.tuned_state_get()

        rep_n = libxml2.newNode("Tuned")
        rep_n.newProp("present", str(int(tuned["present"])))
        for key, value in tuned.items():
            if key == "present":
                continue
            child = libxml2.newNode(key)
            if key == "verification_log":
                if value is None:
                    self.__log(Log.WARN, "could not get verification log")
                    continue
                for line in value:
                    # <date> <time> <log-level>    <message>
                    line = line.split(" ", 3)
                    if len(line) != 4:
                        continue
                    line_child = libxml2.newNode("entry")
                    line_child.newProp("date", line[0])
                    line_child.newProp("time", line[1])
                    line_child.newProp("level", line[2])
                    line_child.setContent(line[3].strip())
                    child.addChild(line_child)
            else:
                child.setContent(value)
            rep_n.addChild(child)

        return rep_n


def unit_test(rootdir):
    try:
        # Helper function tests
        result = tuned_present()
        print("tuned present:", result)
        assert isinstance(result, bool), "__tuned_present() should return bool"
        result = tuned_active_profile()
        print("tuned active profile:", result)
        assert isinstance(result, str), "__tuned_active_profile() should " \
                                        "return string"
        result = tuned_verify()
        print("tuned verification state:", result)
        assert isinstance(result, str), "__tuned_verify() should return string"
        result = tuned_get_log()
        assert isinstance(result, list) or result is None, \
            "__tuned_get_log() should return list or None"

        # Class tests
        tuned = TunedInfo()
        result = tuned.tuned_state_get()
        print(result)
        assert isinstance(result, dict), "TunedInfo.tuned_state_get() " \
                                         "should return dict"
        tuned.MakeReport()

        return 0
    except Exception as err:
        print(f"** EXCEPTION: {str(err)}")
        return 1


if __name__ == '__main__':
    sys.exit(unit_test(None))
