# Copyright (c) 2013 Mirantis Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import smtplib
from oslo.config import cfg

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText

from climate.notifications import base

CONF = cfg.CONF


class EmailNotifier(base.BaseNotifier):

    def __init__(self):
        self.name = 'email.notifier'

    def notify(self, to, subject, text):
        msg = MIMEMultipart()

        msg['From'] = CONF.mail_user
        msg['To'] = to
        msg['Subject'] = subject

        msg.attach(MIMEText(text))

        mailServer = smtplib.SMTP(CONF.mail_server, 587)
        mailServer.ehlo()
        mailServer.starttls()
        mailServer.ehlo()
        mailServer.login(CONF.mail_user, CONF.mail_user_password)
        mailServer.sendmail(CONF.mail_user, to, msg.as_string())
        mailServer.close()
