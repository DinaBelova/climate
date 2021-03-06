#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# Copyright © 2013  Julien Danjou <julien@danjou.info>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import eventlet
eventlet.monkey_patch()
import sys

from oslo.config import cfg

from climate.openstack.common import service
from climate.scheduler import service as scheduler_service
from climate.utils import service as service_utils


def main():
    service_utils.prepare_service(sys.argv)
    service.launch(
        scheduler_service.SchedulerService(cfg.CONF.host,
                                           'climate.scheduler')
    ).wait()

if __name__ == '__main__':
    main()
