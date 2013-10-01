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

import eventlet
from novaclient import exceptions as nova_exceptions

from climate.openstack.common import log as logging
from climate.plugins import base
from climate.utils.openstack import nova

LOG = logging.getLogger(__name__)


class VMPlugin(base.BasePlugin):
    """Base plugin for VM reservation."""
    def __init__(self):
        self.name = 'basic.vm.plugin'
        self.resource_type = 'virtual:instance'

    def get_title(self):
        return "Basic VM Plugin"

    def get_description(self):
        description = (
            "This is basic plugin for VM management. "
            "It can start, snapshot and suspend VMs"
        )
        return description

    def wake_up(self, resource_id, ctx):
        nova.wake_up(resource_id, ctx)

    def delete(self, resource_id, ctx):
        try:
            try:
                # we'll catch exaption if we're trying to create image
                # from RESERVED instance
                nova.create_image(resource_id, ctx)
            except Exception:
                pass
            eventlet.sleep(5)
            while not self.check_active(resource_id, ctx):
                eventlet.sleep(1)
            nova.delete(resource_id, ctx)
        except nova_exceptions.NotFound:
            LOG.warning('Instance %s has been already deleted.' %
                        resource_id)

    def check_active(self, resource_id, ctx):
        instance = nova.get(resource_id, ctx)
        task_state = getattr(instance, "OS-EXT-STS:task_state")
        if task_state is None:
            return True

        if task_state.upper() in ['IMAGE_SNAPSHOT', 'IMAGE_PENDING_UPLOAD',
                                  'IMAGE_UPLOADING']:
            return False
        else:
            LOG.error('Nova reported unexpected task status %s for '
                      'instance %s' % (task_state, resource_id))
