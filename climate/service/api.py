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

from climate import context
from climate import exceptions
from climate.manager import rpcapi as manager_rpcapi
from climate.openstack.common import log as logging
from climate.service import trusts

LOG = logging.getLogger(__name__)


class API(object):
    def __init__(self):
        self.manager_rpcapi = manager_rpcapi.ManagerRPCAPI()

    def get_leases(self):
        """List all existing leases."""
        return self.manager_rpcapi.list_leases(context.ctx())

    def create_lease(self, data):
        """Create new lease.

        :param data: New lease characteristics.
        :type data: dict
        """
        trust = trusts.create_trust()
        trust_id = trust.id
        data.update({'trust_id': trust_id})

        return self.manager_rpcapi.create_lease(context.ctx(), data)

    def get_lease(self, lease_id):
        """Get lease by its ID.

        :param lease_id: ID of the lease in Climate DB.
        :type lease_id: str
        """
        return self.manager_rpcapi.get_lease(context.ctx(), lease_id)

    def update_lease(self, lease_id, data):
        """Update lease. Only name changing and prolonging may be proceeded.

        :param lease_id: ID of the lease in Climate DB.
        :type lease_id: str
        :param data: New lease characteristics.
        :type data: dict
        """
        new_name = data.pop('name', None)
        prolong = data.pop('prolong_for', None)
        if len(data) > 0:
            raise exceptions.ClimateException('Only name changing and '
                                              'prolonging may be proceeded.')
        data = {}
        if new_name:
            data['name'] = new_name
        if prolong:
            data['prolong_for'] = prolong
        return self.manager_rpcapi.update_lease(context.ctx(),
                                                lease_id,
                                                data)

    def delete_lease(self, lease_id):
        """Delete specified lease.

        :param lease_id: ID of the lease in Climate DB.
        :type lease_id: str
        """
        self.manager_rpcapi.delete_lease(context.ctx(), lease_id)

    def get_plugins(self):
        """List all possible plugins."""
        pass
