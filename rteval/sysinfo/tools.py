# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-or-later
""" This Module consists of the single function getcmdpath() """
#
#   Copyright 2012 - 2013   Raphaël Beamonte <raphael.beamonte@gmail.com>
#

import os
import os.path

pathSave = {}
def getcmdpath(which):
    """
    getcmdpath is a method which allows finding an executable in the PATH
    directories to call it from full path
    """
    if which not in pathSave:
        for path in os.environ['PATH'].split(':'):
            cmdfile = os.path.join(path, which)
            if os.path.isfile(cmdfile) and os.access(cmdfile, os.X_OK):
                pathSave[which] = cmdfile
                break
        if not pathSave[which]:
            raise RuntimeError(f"Command '{which}' is unknown on this system")
    return pathSave[which]
