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

from oslo.config import cfg

import climate.openstack.common.rpc.proxy as rpc_proxy

CONF = cfg.CONF


class ManagerRPCAPI(rpc_proxy.RpcProxy):
    """Client side for the Manager RPC API.

    Used from other services to communicate with climate-manager service.
    """
    BASE_RPC_API_VERSION = '1.0'

    def __init__(self):
        """Initiate RPC API client with needed topic and RPC version."""
        super(ManagerRPCAPI, self).__init__(
            topic=CONF.manager_rpc_topic,
            default_version=self.BASE_RPC_API_VERSION
        )

    def get_lease(self, context, lease_id):
        """Get detailed info about some lease."""
        return self.call(context, self.make_msg('get_lease',
                                                lease_id=lease_id))

    def list_leases(self, context):
        """List all leases."""
        return self.call(context, self.make_msg('list_leases'))

    def create_lease(self, context, lease_values):
        """Create lease with specified parameters."""
        return self.call(context, self.make_msg('create_lease',
                                                lease_values=lease_values))

    def update_lease(self, context, lease_id, values):
        """Update lease with passes values dictionary."""
        return self.call(context, self.make_msg('update_lease',
                                                lease_id=lease_id,
                                                values=values))

    def delete_lease(self, context, lease_id):
        """Delete specified lease."""
        return self.cast(context, self.make_msg('delete_lease',
                                                lease_id=lease_id))
