# SPDX-License-Identifier: GPL-2.0-or-later
#
#   Copyright 2012 - 2013   David Sommerseth <davids@redhat.com>
#

import sys

class Log:
    NONE = 0
    ALWAYS = 0
    INFO = 1<<0
    WARN = 1<<1
    ERR = 1<<2
    DEBUG = 1<<3


    def __init__(self, logfile=None):
        if logfile is not None:
            self.__logfile = open(logfile, "w")
        else:
            self.__logfile = sys.stdout
        self.__logverb = self.INFO


    def __logtype_str(self, ltype):
        if ltype == self.ALWAYS:
            return ""
        if ltype == self.INFO:
            return "[INFO] "
        elif ltype == self.WARN:
            return "[WARNING] "
        elif ltype == self.ERR:
            return "[ERROR] "
        elif ltype == self.DEBUG:
            return "[DEBUG] "


    def SetLogVerbosity(self, logverb):
        self.__logverb = logverb


    def log(self, logtype, msg):
        if (logtype & self.__logverb) or logtype == self.ALWAYS:
            self.__logfile.write(f"{self.__logtype_str(logtype)}{msg}\n")



def unit_test(rootdir):
    from itertools import takewhile, count

    logtypes = (Log.ALWAYS, Log.INFO, Log.WARN, Log.ERR, Log.DEBUG)
    logtypes_s = ("ALWAYS", "INFO", "WARN", "ERR", "DEBUG")

    def test_log(l, msg):
        for lt in logtypes:
            l.log(lt, msg)

    def run_log_test(l):
        for lt in range(min(logtypes), max(logtypes)*2):
            test = ", ".join([logtypes_s[logtypes.index(i)] for i in [p for p in takewhile(lambda x: x <= lt, (2**i for i in count())) if p & lt]])
            print(f"Testing verbosity flags set to: ({lt}) {test}")
            msg = f"Log entry when verbosity is set to {lt} [{test}]"
            l.SetLogVerbosity(lt)
            test_log(l, msg)
            print("-"*20)

    try:
        print("** Testing stdout")
        l = Log()
        run_log_test(l)

        print("** Testing file logging - using test.log")
        l = Log("test.log")
        run_log_test(l)

        return 0
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        print("** EXCEPTION %s", str(e))
        return 1



if __name__ == '__main__':
    unit_test(None)
