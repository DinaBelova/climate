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

import datetime

from oslo.config import cfg
from stevedore import extension

from climate import config
from climate import context
from climate.db import api as db_api
from climate import exceptions
from climate.openstack.common import log as logging
from climate.openstack.common.rpc import service as rpc_service
from climate.utils.openstack import keystone

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class ManagerService(rpc_service.Service):
    """Service class for the climate-manager service.

    Responsible for working with Climate DB, scheduling logic, running events,
    working with plugins, etc.
    """

    RPC_API_VERSION = '1.0'

    def __init__(self, host, topic):
        super(ManagerService, self).__init__(host, topic)
        self.extension_manager = extension.ExtensionManager(
            namespace='climate.resource.plugins',
            invoke_on_load=True
        )
        self.plugins = self._get_plugins()
        self.internal_context = context.Context(None, None, None, None)
        self.resource_actions = self._setup_actions()
        self._setup_methods()

    def start(self):
        super(ManagerService, self).start()
        self.tg.add_timer(10, self._event)

    def _get_plugins(self):
        """Return dict of resource-plugin class pairs."""
        available_plugins = self.extension_manager.extensions
        config_plugins = CONF.plugins
        plugins = {}

        for plugin in config_plugins:
            needed_plugin = None
            for available_plugin in available_plugins:
                if available_plugin.name == plugin:
                    needed_plugin = available_plugin
                    break

            if needed_plugin is not None:
                plugins[needed_plugin.obj.resource_type] = needed_plugin.obj

        if len(plugins) < len(config_plugins):
            raise exceptions.ClimateException('Not all requested plugins are '
                                              'loaded.')

        return plugins

    def _setup_actions(self):
        """Setup actions for each resource type supported.

        Actions are described in climate.conf file in the section describing
        appropriate resource type. This section looks like the following:

        [virtual:instance]
            on_start = wake_up
            on_end = delete

        Waking up and deleting are the default actions to commit for every
        resource type.
        """
        actions = {}

        for resource_type in self.plugins:
            opts = [cfg.StrOpt('on_start', required=True),
                    cfg.StrOpt('on_end', required=True)]
            CONF.register_opts(opts, group=resource_type)
        config.parse_configs()

        for resource_type in self.plugins:
            conf_section = CONF.get(resource_type)
            plugin = self.plugins[resource_type]

            for action_time in conf_section:
                action_name = conf_section[action_time]
                action_func = getattr(plugin, action_name, None)
                if action_func is None:
                    raise exceptions.ClimateException(
                        'No action %s implemented in plugin %s' %
                        (action_name, plugin.name)
                    )
                if not actions.get(resource_type):
                    actions[resource_type] = {}
                actions[resource_type][action_time] = action_func

            if 'on_start' not in actions[resource_type]:
                default_on_start_fn = getattr(plugin, 'wake_up', None)
                if default_on_start_fn is None:
                    raise NotImplementedError("Default on start method is "
                                              "not implemented in plugin %s" %
                                              plugin.name)
                actions[resource_type]['on_start'] = default_on_start_fn
            if 'on_end' not in actions[resource_type]:
                default_on_end_fn = getattr(plugin, 'delete', None)
                if default_on_end_fn is None:
                    raise NotImplementedError("Default on end method is "
                                              "not implemented in plugin %s" %
                                              plugin.name)
                actions[resource_type]['on_start'] = default_on_end_fn

        return actions

    def _setup_methods(self):
        """Setup additional methods.
        Format:
            module:method
        """
        for parameter in CONF.additional_methods:
            module_method = parameter.split(':')
            module_method = filter(None, module_method)
            if len(module_method) == 2:
                method = getattr(__import__(module_method[0]),
                                 module_method[1])
                setattr(self, module_method[1], method)
            else:
                raise exceptions.ClimateException(
                    'Invalid additional method format: %s' % parameter
                )

    def _event(self):
        """Tries to commit event.

        If there is an event in Climate DB to be done, do it and change its
        status to 'DONE'.
        """
        LOG.debug('Trying to get event from DB.')
        events = db_api.event_get_all_sorted_by_filters(
            self.internal_context,
            sort_key='time',
            sort_dir='asc',
            filters={'status': 'UNDONE'}
        )

        if not events:
            return

        event = events[0]

        if event['time'] < datetime.datetime.utcnow():
            db_api.event_update(self.internal_context,
                                event['id'], {'status': 'IN_PROGRESS'})
            event_type = event['event_type']
            event_fn = getattr(self, event_type, None)
            if event_fn is None:
                raise exceptions.ClimateException('Event type %s is not '
                                                  'supported' % event_type)
            try:
                event_fn(event['lease_id'])
            except Exception:
                db_api.event_update(self.internal_context,
                                    event['id'], {'status': 'ERROR'})
                LOG.exception('Error occurred while event handling.')

            if event_type != 'end_lease':
                db_api.event_update(self.internal_context,
                                    event['id'], {'status': 'DONE'})

    def get_lease(self, ctx, lease_id):
        return db_api.lease_get(ctx, lease_id)

    def list_leases(self, ctx):
        return db_api.lease_list(ctx)

    def create_lease(self, ctx, lease_values):
        start_date = lease_values['start_date']
        end_date = lease_values['end_date']

        if start_date == 'now':
            start_date = datetime.datetime.utcnow()
        else:
            start_date = datetime.datetime.strptime(start_date,
                                                    "%Y-%m-%d %H:%M")
        end_date = datetime.datetime.strptime(end_date, "%Y-%m-%d %H:%M")

        lease_values['start_date'] = start_date
        lease_values['end_date'] = end_date

        lease = db_api.lease_create(ctx, lease_values)

        db_api.event_create(ctx, {'lease_id': lease['id'],
                                  'event_type': 'start_lease',
                                  'time': lease['start_date'],
                                  'status': 'UNDONE'})

        db_api.event_create(ctx, {'lease_id': lease['id'],
                                  'event_type': 'end_lease',
                                  'time': lease['end_date'],
                                  'status': 'UNDONE'})

        return db_api.lease_get(ctx, lease['id'])

    def update_lease(self, ctx, lease_id, values):
        # prolong_for variable will be in seconds. Climate client provides
        # flags to set days, hours, etc.
        prolong_for = values.pop('prolong_for', None)
        if prolong_for:
            lease_event = db_api.event_get_all_sorted_by_filters(
                ctx,
                sort_key='time',
                sort_dir='asc',
                filters={'lease_id': lease_id, 'event_type': 'end_lease'}
            )[0]

            end_date = self.get_lease(ctx, lease_id)['end_date']
            prolong_delta = datetime.timedelta(seconds=int(prolong_for))
            new_end_time = end_date + prolong_delta
            values['end_date'] = new_end_time

            db_api.event_update(ctx,
                                lease_event['id'],
                                {'time': new_end_time})

        if values:
            db_api.lease_update(ctx, lease_id, values)
        return db_api.lease_get(ctx, lease_id)

    def delete_lease(self, ctx, lease_id):
        lease = self.get_lease(ctx, lease_id)
        keystone.create_ctx_from_trust(lease['trust_id'])
        for reservation in lease['reservations']:
            self.plugins[reservation['resource_type']]\
                .delete(reservation['resource_id'], context.current())
        db_api.lease_destroy(ctx, lease_id)

    def start_lease(self, lease_id):
        self._basic_action(lease_id, 'on_start', 'active')

    def end_lease(self, lease_id):
        self._basic_action(lease_id, 'on_end', 'deleted')

    def _basic_action(self, lease_id, action_time, reservation_status=None):
        """Commits basic lease actions such as starting and ending."""
        lease = self.get_lease(self.internal_context, lease_id)
        keystone.create_ctx_from_trust(lease['trust_id'])

        for reservation in lease['reservations']:
            resource_type = reservation['resource_type']
            self.resource_actions[resource_type][action_time](
                reservation['resource_id'],
                context.current()
            )

            if reservation_status is not None:
                db_api.reservation_update(self.internal_context,
                                          reservation['id'],
                                          {'status': reservation_status})
