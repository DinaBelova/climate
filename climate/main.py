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
import flask
from keystoneclient.middleware import auth_token
from oslo.config import cfg
from werkzeug import exceptions as werkzeug_exceptions

from climate.api import v10 as api_v10
from climate import context
from climate.openstack.common import log
from climate.openstack.common.middleware import debug
from climate.utils import api as api_utils

LOG = log.getLogger(__name__)

eventlet.monkey_patch(
    os=True, select=True, socket=True, thread=True, time=True)

CONF = cfg.CONF


def make_app():
    """App builder (wsgi).

    Entry point for Climate REST API server.
    """
    app = flask.Flask('climate.api')

    @app.route('/', methods=['GET'])
    def version_list():
        context.set_ctx(None)
        return api_utils.render({
            "versions": [
                {"id": "v1.0", "status": "CURRENT"}
            ]
        })

    @app.teardown_request
    def teardown_request(_ex=None):
        context.set_ctx(None)

    app.register_blueprint(api_v10.rest, url_prefix='/v1')

    def make_json_error(ex):
        status_code = (ex.code
                       if isinstance(ex, werkzeug_exceptions.HTTPException)
                       else 500)
        description = (ex.description
                       if isinstance(ex, werkzeug_exceptions.HTTPException)
                       else str(ex))
        return api_utils.render({'error': status_code,
                                 'error_message': description},
                                status=status_code)

    for code in werkzeug_exceptions.default_exceptions.iterkeys():
        app.error_handler_spec[None][code] = make_json_error

    if CONF.debug and not CONF.log_exchange:
        LOG.debug('Logging of request/response exchange could be enabled using'
                  ' flag --log-exchange')

    if CONF.log_exchange:
        app.wsgi_app = debug.Debug.factory(app.config)(app.wsgi_app)

    app.wsgi_app = auth_token.filter_factory(
        app.config,
        auth_host=CONF.os_auth_host,
        auth_port=CONF.os_auth_port,
        auth_protocol=CONF.os_auth_protocol,
        admin_user=CONF.os_admin_username,
        admin_password=CONF.os_admin_password,
        admin_tenant_name=CONF.os_admin_tenant_name,
        auth_version=CONF.os_auth_version,
    )(app.wsgi_app)

    return app
