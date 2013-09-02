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
from eventlet import corolocal

from climate.openstack.common import log as logging


LOG = logging.getLogger(__name__)


class Context(object):
    """Context class for the Climate operations."""
    def __init__(self, user_id=None, tenant_id=None, auth_token=None,
                 service_catalog=None, user_name=None, tenant_name=None,
                 roles=None, **kwargs):
        if kwargs:
            LOG.warn('Arguments dropped when creating context: %s', kwargs)

        self.user_id = user_id
        self.user_name = user_name
        self.tenant_id = tenant_id
        self.tenant_name = tenant_name
        self.auth_token = auth_token
        self.service_catalog = service_catalog
        self.roles = roles
        self._db_session = None

    def clone(self):
        return Context(self.user_id,
                       self.tenant_id,
                       self.auth_token,
                       self.service_catalog,
                       self.user_name,
                       self.tenant_name,
                       self.roles)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant_name,
            'auth_token': self.auth_token,
            'service_catalog': self.service_catalog,
            'roles': self.roles,
        }


_CURR_CTXS = {}


def has_ctx():
    ident = corolocal.get_ident()
    return ident in _CURR_CTXS and _CURR_CTXS[ident]


def ctx():
    if not has_ctx():
        raise RuntimeError("Context isn't available here")
    return _CURR_CTXS[corolocal.get_ident()]


def current():
    return ctx()


def set_ctx(new_ctx):
    ident = corolocal.get_ident()

    if not new_ctx and ident in _CURR_CTXS:
        del _CURR_CTXS[ident]

    if new_ctx:
        _CURR_CTXS[ident] = new_ctx


def spawn(thread_description, func, *args, **kwargs):
    ctx = current().clone()

    def wrapper(ctx, func, *args, **kwargs):
        try:
            set_ctx(ctx)
            func(*args, **kwargs)
            set_ctx(None)
        except Exception as e:
            LOG.exception("Thread '%s' fails with exception: '%s'"
                          % (thread_description, e))

    eventlet.spawn(wrapper, ctx, func, *args, **kwargs)


def sleep(seconds=0):
    eventlet.sleep(seconds)
