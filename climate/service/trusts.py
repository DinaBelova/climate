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

from climate import context
from climate.utils.openstack import keystone

CONF = cfg.CONF


def create_trust():
    """Creates trust via Keystone API v3 to use in plugins."""
    client = keystone.client()
    ctx = context.current()

    trustee_id = keystone.client(username=CONF.os_admin_username,
                                 password=CONF.os_admin_password,
                                 tenant=CONF.os_admin_tenant_name).user_id

    trust = client.trusts.create(trustor_user=client.user_id,
                                 trustee_user=trustee_id,
                                 impersonation=False,
                                 role_names=ctx.roles,
                                 project=client.tenant_id)
    return trust


def delete_trust(lease):
    """Deletes trust for the specified lease."""
    if lease.trust_id:
        keystone_client = keystone.client(trust_id=lease.trust_id)
        keystone_client.trusts.delete(lease.trust_id)
