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

from climate.plugins import base


class DummyVMPlugin(base.BasePlugin):
    """Plugin for VM resource that does nothing."""
    def __init__(self):
        self.name = 'dummy.vm.plugin'
        self.resource_type = 'virtual:instance'

    def get_title(self):
        """Plugin title."""
        return "Dummy VM Plugin"

    def get_description(self):
        """Optional description of the plugin

        This information is targeted to be displayed in UI.
        """
        return "This plugin does nothing."

    def wake_up(self, resource_id, ctx):
        """Dummy VM plugin does nothing."""
        return 'VM %s should be waked up this moment.' % resource_id

    def delete(self, resource_id, ctx):
        """Dummy VM plugin does nothing."""
        return 'VM %s should be deleted this moment.' % resource_id
