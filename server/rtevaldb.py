# SPDX-License-Identifier: GPL-2.0-or-later
#
#   rtevaldb.py
#   Function for registering a rteval summary.xml report into the database
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#

import os
from database import Database

def register_submission(config, clientid, filename, debug=False, noaction=False):
    "Registers a submission of a rteval report which signalises the rteval_parserd process"

    dbc = Database(host=config.db_server, port=config.db_port, database=config.database,
                   user=config.db_username, password=config.db_password,
                   debug=debug, noaction=noaction)

    submvars = {"table": "submissionqueue",
                "fields": ["clientid", "filename"],
                "records": [[clientid, filename]],
                "returning": "submid"
                }

    res = dbc.INSERT(submvars)
    if len(res) != 1:
        raise Exception("Could not register the submission")

    dbc.COMMIT()
    return res[0]

def database_status(config, debug=False, noaction=False):
    dbc = Database(host=config.db_server, port=config.db_port, database=config.database,
                   user=config.db_username, password=config.db_password,
                   debug=debug, noaction=noaction)
    if not dbc:
        return {"status": "No connection to pgsql://%s:%s/%s" % (config.db_server,
                                                                 config.db_port,
                                                                 config.database)}

    res = dbc.SELECT('rtevalruns',
                     ["to_char(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS') AS server_time",
                      "max(rterid) AS last_rterid",
                      "max(submid) AS last_submid"]
                     )
    if len(res) != 3:
        return {"status": "Could not query database pgsql://%s:%s/%s" % (config.db_server,
                                                                         config.db_port,
                                                                         config.database)}
    last_rterid = res['records'][0][1] and res['records'][0][1] or "(None)"
    last_submid = res['records'][0][1] and res['records'][0][2] or "(None)"
    return {"status": "OK",
            "server_time": res['records'][0][0],
            "last_rterid": last_rterid,
            "last_submid": last_submid
            }

