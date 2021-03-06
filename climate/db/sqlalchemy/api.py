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

"""Implementation of SQLAlchemy backend."""

import sys

import sqlalchemy as sa
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc

from climate.db.sqlalchemy import models
from climate.openstack.common.db import exception as db_exc
from climate.openstack.common.db.sqlalchemy import session as db_session
from climate.openstack.common import log as logging


LOG = logging.getLogger(__name__)

get_engine = db_session.get_engine
get_session = db_session.get_session


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def model_query(model, context, session=None, project_only=None):
    """Query helper.

    :param model: base model to query
    :param context: context to query under
    :param project_only: if present and context is user-type, then restrict
            query to match the context's project_id.
    """
    session = session or get_session()

    query = session.query(model)

    if project_only:
        query = query.filter_by(tenant_id=context.project_id)

    return query


def column_query(context, *columns, **kwargs):
    session = kwargs.get("session") or get_session()

    query = session.query(*columns)

    if kwargs.get("project_only"):
        query = query.filter_by(tenant_id=context.tenant_id)

    return query


def setup_db():
    try:
        engine = db_session.get_engine(sqlite_fk=True)
        models.Lease.metadata.create_all(engine)
    except sa.exc.OperationalError as e:
        LOG.error("Database registration exception: %s", e)
        return False
    return True


def drop_db():
    try:
        engine = db_session.get_engine(sqlite_fk=True)
        models.Lease.metadata.drop_all(engine)
    except Exception as e:
        LOG.error("Database shutdown exception: %s", e)
        return False
    return True


## Helpers for building constraints / equality checks


def constraint(**conditions):
    return Constraint(conditions)


def equal_any(*values):
    return EqualityCondition(values)


def not_equal(*values):
    return InequalityCondition(values)


class Constraint(object):
    def __init__(self, conditions):
        self.conditions = conditions

    def apply(self, model, query):
        for key, condition in self.conditions.iteritems():
            for clause in condition.clauses(getattr(model, key)):
                query = query.filter(clause)
        return query


class EqualityCondition(object):
    def __init__(self, values):
        self.values = values

    def clauses(self, field):
        return sa.or_([field == value for value in self.values])


class InequalityCondition(object):
    def __init__(self, values):
        self.values = values

    def clauses(self, field):
        return [field != value for value in self.values]


#Reservation
def _reservation_get(context, session, reservation_id):
    query = model_query(models.Reservation, context, session)
    return query.filter_by(id=reservation_id).first()


def reservation_get(context, reservation_id):
    return _reservation_get(context, get_session(), reservation_id)


def reservation_get_all(context):
    query = model_query(models.Reservation, context, get_session())
    return query.all()


def reservation_get_all_by_lease_id(context, lease_id):
    reservations = model_query(models.Reservation, context, get_session()).\
        filter_by(lease_id=lease_id)

    return reservations.all()


def reservation_create(context, values):
    values = values.copy()
    reservation = models.Reservation()
    reservation.update(values)

    session = get_session()
    with session.begin():
        try:
            reservation.save(session=session)
        except db_exc.DBDuplicateEntry as e:
            # raise exception about duplicated columns (e.columns)
            raise RuntimeError("DBDuplicateEntry: %s" % e.columns)

    return reservation_get(context, reservation.id)


def reservation_update(context, reservation_id, values):
    session = get_session()

    with session.begin():
        reservation = _reservation_get(context, session, reservation_id)
        reservation.update(values)
        reservation.save(session=session)

    return reservation_get(context, reservation_id)


def reservation_destroy(context, reservation_id):
    session = get_session()
    with session.begin():
        reservation = _reservation_get(context, session, reservation_id)

        if not reservation:
            # raise not found error
            raise RuntimeError("Reservation not found!")

        session.delete(reservation)


#Lease
def _lease_get(context, session, lease_id):
    query = model_query(models.Lease, context, session)
    return query.filter_by(id=lease_id).first()


def lease_get(context, lease_id):
    return _lease_get(context, get_session(), lease_id)


def lease_get_all(context):
    query = model_query(models.Lease, context, get_session())
    return query.all()


def lease_get_all_by_tenant(context, tenant_id):
    raise NotImplementedError


def lease_get_all_by_user(context, user_id):
    raise NotImplementedError


def lease_list(context):
    return model_query(models.Lease, context, get_session()).all()


def lease_create(context, values):
    values = values.copy()
    lease = models.Lease()
    reservations = values.pop("reservations", [])
    events = values.pop("events", [])
    lease.update(values)

    session = get_session()
    with session.begin():
        try:
            lease.save(session=session)

            for r in reservations:
                reservation = models.Reservation()
                reservation.update({"lease_id": lease.id})
                reservation.update(r)
                reservation.save(session=session)

            for e in events:
                event = models.Event()
                event.update({"lease_id": lease.id,
                              "status": 'UNDONE'})
                event.update(e)
                event.save(session=session)

        except db_exc.DBDuplicateEntry as e:
            # raise exception about duplicated columns (e.columns)
            raise RuntimeError("DBDuplicateEntry: %s" % e.columns)

    return lease_get(context, lease.id)


def lease_update(context, lease_id, values):
    session = get_session()

    with session.begin():
        lease = _lease_get(context, session, lease_id)
        lease.update(values)
        lease.save(session=session)

    return lease_get(context, lease_id)


def lease_destroy(context, lease_id):
    session = get_session()
    with session.begin():
        lease = _lease_get(context, session, lease_id)

        if not lease:
            # raise not found error
            raise RuntimeError("Lease not found!")

        session.delete(lease)


#Event
def _event_get(context, session, event_id):
    query = model_query(models.Event, context, session)
    return query.filter_by(id=event_id).first()


def _event_get_all(context, session):
    query = model_query(models.Event, context, session)
    return query


def event_get(context, event_id):
    return _event_get(context, get_session(), event_id)


def event_get_all(context):
    return _event_get_all(context, get_session()).all()


def event_get_all_sorted_by_filters(context, sort_key, sort_dir, filters):
    """Return events filtered and sorted by name of the field."""

    sort_fn = {'desc': desc, 'asc': asc}

    events_query = _event_get_all(context, get_session())

    if 'status' in filters:
        events_query = \
            events_query.filter(models.Event.status.in_(filters['status']))
    if 'lease_id' in filters:
        events_query = \
            events_query.filter(models.Event.lease_id == filters['lease_id'])
    if 'event_type' in filters:
        events_query = events_query.filter(models.Event.event_type.in_(
            filters['event_type'])
        )

    events_query = events_query.order_by(
        sort_fn[sort_dir](getattr(models.Event, sort_key))
    )

    return events_query.all()


def event_list(context):
    return model_query(models.Event.id, context, get_session()).all()


def event_create(context, values):
    values = values.copy()
    event = models.Event()
    event.update(values)

    session = get_session()
    with session.begin():
        try:
            event.save(session=session)
        except db_exc.DBDuplicateEntry as e:
            # raise exception about duplicated columns (e.columns)
            raise RuntimeError("DBDuplicateEntry: %s" % e.columns)

    return event_get(context, event.id)


def event_update(context, event_id, values):
    session = get_session()

    with session.begin():
        event = _event_get(context, session, event_id)
        event.update(values)
        event.save(session=session)

    return event_get(context, event_id)


def event_destroy(context, event_id):
    session = get_session()
    with session.begin():
        event = _event_get(context, session, event_id)

        if not event:
            # raise not found error
            raise RuntimeError("Event not found!")

        session.delete(event)
