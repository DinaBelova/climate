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

import socket

from oslo.config import cfg

cli_opts = [
    cfg.StrOpt('host', default=socket.getfqdn(),
               help='Name of this node.  This can be an opaque identifier.  '
               'It is not necessarily a hostname, FQDN, or IP address. '
               'However, the node name must be valid within '
               'an AMQP key, and if using ZeroMQ, a valid '
               'hostname, FQDN, or IP address'),
    cfg.IntOpt('port', default=1234,
               help='Port that will be used to listen on'),
    cfg.BoolOpt('log-exchange', default=False,
                help='Log request/response exchange details: environ, '
                     'headers and bodies')
]

manager_opts = [
    cfg.StrOpt('manager_rpc_topic',
               default='climate.manager',
               help='The topic Climate uses for climate-manager messages.'),
    cfg.ListOpt('additional_methods',
                default=[],
                help='All methods to expose in RPC Manager service.'),
    cfg.ListOpt('plugins',
                default=['dummy.vm.plugin'],
                help='All plugins to use (one for every resource type to '
                     'support.)')
]

os_opts = [
    cfg.StrOpt('os_auth_protocol',
               default='http',
               help='Protocol used to access OpenStack Identity service'),
    cfg.StrOpt('os_auth_host',
               default='127.0.0.1',
               help='IP or hostname of machine on which OpenStack Identity '
                    'service is located'),
    cfg.StrOpt('os_auth_port',
               default='35357',
               help='Port of OpenStack Identity service'),
    cfg.StrOpt('os_admin_username',
               default='admin',
               help='This OpenStack user is used to verify provided tokens. '
                    'The user must have admin role in <os_admin_tenant_name> '
                    'tenant'),
    cfg.StrOpt('os_admin_password',
               default='nova',
               help='Password of the admin user'),
    cfg.StrOpt('os_admin_tenant_name',
               default='admin',
               help='Name of tenant where the user is admin'),
    cfg.StrOpt('os_auth_version',
               default='v3.0',
               help='We use API v3 to allow trusts using.'),
]

notification_opts = [
    cfg.StrOpt('notify_to',
               default='',
               help='Defines user to send notification to.'),
    cfg.ListOpt('notifications',
                default=[],
                help='Times for the notifications to '
                     'appear.')
]

email_opts = [
    cfg.StrOpt('mail_user',
               default='climate.no.reply@gmail.com',
               help='Email user to send notifications from.'),
    cfg.StrOpt('mail_user_password',
               default='climatenoreply',
               help='Password for user to send notifications from.'),
    cfg.StrOpt('mail_server',
               default='smtp.gmail.com',
               help='SMTP server to use.')
]


CONF = cfg.CONF
CONF.register_cli_opts(cli_opts)
CONF.register_cli_opts(manager_opts)
CONF.register_cli_opts(os_opts)
CONF.register_cli_opts(notification_opts)
CONF.register_cli_opts(email_opts)

ARGV = []


def parse_configs(argv=None, conf_files=None):
    """Parse Climate configuration file."""
    if argv is not None:
        global ARGV
        ARGV = argv
    try:
        CONF(ARGV, project='climate', default_config_files=conf_files)
    except cfg.RequiredOptError as roe:
        raise RuntimeError("Option '%s' is required for config group "
                           "'%s'" % (roe.opt_name, roe.group.name))
