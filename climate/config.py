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
               help='Port that will be used to listen on')
]

CONF = cfg.CONF
CONF.register_cli_opts(cli_opts)

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