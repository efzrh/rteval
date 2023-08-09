# SPDX-License-Identifier: GPL-2.0-or-later
#
#   rtevalmailer.py - module for sending e-mails
#
#   Copyright 2009 - 2013   David Sommerseth <davids@redhat.com>
#

import smtplib
import email


class rtevalMailer(object):
    "rteval mailer - sends messages via an SMTP server to designated e-mail addresses"

    def __init__(self, cfg):
        # this configuration object needs to have the following attributes set:
        # * smtp_server
        # * from_address
        # * to_address
        #
        errmsg = ""
        if 'smtp_server' not in cfg:
            errmsg = "\n** Missing smtp_server in config"
        if 'from_address' not in cfg:
            errmsg += "\n** Missing from_address in config"
        if 'to_address' not in cfg:
            errmsg += "\n** Missing to_address in config"

        if not errmsg == "":
            raise LookupError(errmsg)

        self.config = cfg


    def __prepare_msg(self, subj, body):
        msg = email.MIMEText.MIMEText(body)
        msg['subject'] = subj;
        msg['From'] = "rteval mailer <" + self.config.from_address+">"
        msg['To'] = self.config.to_address
        return msg


    def SendMessage(self, subject, body):
        "Sends an e-mail to the configured mail server and recipient"

        msg = self.__prepare_msg(subject, body)
        srv = smtplib.SMTP()
        srv.connect(self.config.smtp_server)
        srv.sendmail(self.config.from_address, self.config.to_address, str(msg))
        srv.close()

