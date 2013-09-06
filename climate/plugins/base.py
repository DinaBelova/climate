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

import abc

from oslo.config import cfg

from climate.openstack.common import log as logging
from climate.utils import resources

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


def required(fun):
    return abc.abstractmethod(fun)


def required_with_default(fun):
    return fun


def optional(fun):
    fun.__not_implemented__ = True
    return fun


class BasePlugin(resources.BaseResource):
    __metaclass__ = abc.ABCMeta

    __resource_name__ = 'plugin'

    name = 'base_plugin'
    resource_type = 'none'

    @required_with_default
    def get_plugin_opts(self):
        """Plugin can expose some options that should be specified in conf file

        For example:

            def get_plugin_opts(self):
            return [
                cfg.StrOpt('mandatory-conf', required=True),
                cfg.StrOpt('optional_conf', default="42"),
            ]
        """
        return []

    @required_with_default
    def setup(self, conf):
        """Plugin initialization

        :param conf: plugin-specific configurations
        """
        pass

    @required
    def get_title(self):
        """Plugin title

        For example:

            "Dummy VM Plugin"
        """
        pass

    @required_with_default
    def get_description(self):
        """Optional description of the plugin

        This information is targeted to be displayed in UI.
        """
        pass

    def to_dict(self):
        return {
            'name': self.name,
            'resource_type': self.resource_type,
            'title': self.get_title(),
            'description': self.get_description(),
        }

    @required
    def delete(self, resource_id, ctx):
        """Delete resource."""
        pass

    @required
    def wake_up(self, resource_id, ctx):
        """Wake up resource."""
        pass
