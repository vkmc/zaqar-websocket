# Copyright (c) 2015 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License.  You may obtain a copy
# of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

from zaqar.common.api import response
from zaqar.common.api import utils as api_utils
from zaqar.i18n import _
import zaqar.openstack.common.log as logging
from zaqar.storage import errors as storage_errors
from zaqar.transport import validation

LOG = logging.getLogger(__name__)


class Endpoints(object):
    """v1.1 API Endpoints."""

    def __init__(self, storage, control, validate):
        self._queue_controller = storage.queue_controller
        self._message_controller = storage.message_controller
        self._claim_controller = storage.claim_controller

        self._pools_controller = control.pools_controller
        self._flavors_controller = control.flavors_controller

        self._validate = validate

    # Queues
    @api_utils.raises_conn_error
    def queue_list(self, req):
        """Gets a list of queues

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')

        LOG.debug(u'Queue list - project: %(project)s',
                  {'project': project_id})

        kwargs = {}

        if req._body.get('marker') is not None:
            kwargs['marker'] = req._body.get('marker')

        if req._body.get('limit') is not None:
            kwargs['limit'] = int(req._body.get('limit'))

        if req._body.get('detailed') is not None:
            kwargs['detailed'] = 'true' == req._body.get('detailed')

        try:
            self._validate.queue_listing(**kwargs)
            results = self._queue_controller.list(
                project=project_id, **kwargs)
        except validation.ValidationFailed as ex:
            LOG.debug(ex)
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers)
        except storage_errors.BaseException as ex:
            LOG.exception(ex)
            error = 'Queues could not be listed.'
            headers = {'status': 503}
            return api_utils.error_response(req, ex, error, headers)

        # Buffer list of queues
        queues = list(next(results))

        # Got some. Prepare the response.
        body = {'queues': queues}
        headers = {'status': 200}

        resp = response.Response(req, body, headers)

        return resp

    @api_utils.raises_conn_error
    def queue_create(self, req):
        """Creates a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')
        metadata = req._body.get('metadata')

        LOG.debug(u'Queue create - queue: %(queue)s, project: %(project)s',
                  {'queue': queue_name,
                   'project': project_id})

        try:
            self._validate.queue_identification(queue_name, project_id)
            self._validate.queue_metadata_length(len(metadata))
            created = self._queue_controller.create(queue_name,
                                                    metadata=metadata,
                                                    project=project_id)
        except validation.ValidationFailed as ex:
            LOG.debug(ex)
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers)
        except storage_errors.BaseException as ex:
            LOG.exception(ex)
            error = _('Queue "%s" could not be created.') % queue_name
            headers = {'status': 503}
            return api_utils.error_response(req, ex, headers, error)
        else:
            body = _('Queue "%s" created.') % queue_name
            headers = {'status': 201} if created else {'status': 204}
            resp = response.Response(req, body, headers)
            return resp

    @api_utils.raises_conn_error
    def queue_delete(self, req):
        """Deletes a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')

        LOG.debug(u'Queue delete - queue: %(queue)s, project: %(project)s',
                  {'queue': queue_name, 'project': project_id})
        try:
            self._queue_controller.delete(queue_name, project=project_id)
        except storage_errors.BaseException as ex:
            LOG.exception(ex)
            error = _('Queue "%s" could not be deleted.') % queue_name
            headers = {'status': 503}
            return api_utils.error_response(req, ex, headers, error)
        else:
            body = _('Queue "%s" removed.') % queue_name
            headers = {'status': 204}
            resp = response.Response(req, body, headers)
            return resp

    @api_utils.raises_conn_error
    def queue_get(self, req):
        """Gets a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')

        LOG.debug(u'Queue get - queue: %(queue)s, '
                  u'project: %(project)s',
                  {'queue': queue_name, 'project': project_id})

        try:
            resp_dict = self._queue_controller.get(queue_name,
                                                   project=project_id)
        except storage_errors.DoesNotExist as ex:
            LOG.debug(ex)
            error = _('Queue "%s" does not exist.') % queue_name
            headers = {'status': 404}
            return api_utils.error_response(req, ex, headers, error)
        except storage_errors.BaseException as ex:
            LOG.exception(ex)
            headers = {'status': 503}
            error = _('Cannot retrieve queue "%s".') % queue_name
            return api_utils.error_response(req, ex, headers, error)
        else:
            body = resp_dict
            headers = {'status': 200}
            resp = response.Response(req, body, headers)
            return resp

    @api_utils.raises_conn_error
    def queue_get_stats(self, req):
        """Gets queue stats

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')

        LOG.debug(u'Queue get stats - queue: %(queue)s, '
                  u'project: %(project)s',
                  {'queue': queue_name, 'project': project_id})

        try:
            resp_dict = self._queue_controller.stats(queue_name,
                                                     project=project_id)
            body = resp_dict
        except storage_errors.QueueDoesNotExist as ex:
            LOG.exception(ex)
            resp_dict = {
                'messages': {
                    'claimed': 0,
                    'free': 0,
                    'total': 0
                }
            }
            body = resp_dict
            headers = {'status': 404}
            resp = response.Response(req, body, headers)
            return resp
        except storage_errors.BaseException as ex:
            LOG.exception(ex)
            error = _('Cannot retrieve queue "%s" stats.') % queue_name
            headers = {'status': 503}
            return api_utils.error_response(req, ex, headers, error)
        else:
            headers = {'status': 200}
            resp = response.Response(req, body, headers)
            return resp

    # Messages
    @api_utils.raises_conn_error
    def message_list(self, req):
        """Gets a list of messages on a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        client_uuid = req._headers.get('Client-ID')
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')

        LOG.debug(u'Message list - queue: %(queue)s, '
                  u'project: %(project)s',
                  {'queue': queue_name, 'project': project_id})

        kwargs = {}

        if req._body.get('marker') is not None:
            kwargs['marker'] = req._body.get('marker')

        if req._body.get('limit') is not None:
            kwargs['limit'] = int(req._body.get('limit'))

        if req._body.get('echo') is not None:
            kwargs['echo'] = 'true' == req._body.get('echo')

        if req._body.get('include_claimed') is not None:
            kwargs['include_claimed'] = ('true' ==
                                         req._body.get('include_claimed'))

        try:
            self._validate.message_listing(**kwargs)
            results = self._message_controller.list(
                queue_name,
                project=project_id,
                client_uuid=client_uuid,
                **kwargs)

            # Buffer messages
            cursor = next(results)
            messages = list(cursor)

        except validation.ValidationFailed as ex:
            LOG.debug(ex)
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers)
        except storage_errors.DoesNotExist as ex:
            LOG.debug(ex)
            headers = {'status': 404}
            return api_utils.error_response(req, ex, headers)
        except Exception as ex:
            LOG.exception(ex)
            error = _(u'Messages could not be listed.')
            headers = {'status': 500}
            return api_utils.error_response(req, ex, headers, error)

        if not messages:
            messages = []

        else:
            # Found some messages, so prepare the response
            kwargs['marker'] = next(results)
            messages = [api_utils.format_message(message)
                        for message in messages]

        headers = {'status': 200}
        body = {'messages': messages}

        resp = response.Response(req, body, headers)
        return resp

    @api_utils.raises_conn_error
    def message_get(self, req):
        """Gets a message from a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')
        message_id = req._body.get('message_id')

        LOG.debug(u'Message get - message: %(message)s, '
                  u'queue: %(queue)s, project: %(project)s',
                  {'message': message_id,
                   'queue': queue_name,
                   'project': project_id})
        try:
            message = self._message_controller.get(
                queue_name,
                message_id,
                project=project_id)

        except storage_errors.DoesNotExist as ex:
            LOG.debug(ex)
            headers = {'status': 404}
            return api_utils.error_response(req, ex, headers)
        except Exception as ex:
            LOG.exception(ex)
            error = _(u'Message could not be retrieved.')
            headers = {'status': 500}
            return api_utils.error_response(req, ex, headers, error)

        # Prepare response
        message = api_utils.format_message(message)

        headers = {'status': 200}
        body = {'messages': message}

        resp = response.Response(req, body, headers)
        return resp

    @api_utils.raises_conn_error
    def message_get_many(self, req):
        """Gets a set of messages from a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')
        message_ids = list(req._body('message_ids'))

        LOG.debug(u'Message get - queue: %(queue)s, '
                  u'project: %(project)s',
                  {'queue': queue_name, 'project': project_id})

        try:
            self._validate.message_listing(limit=len(message_ids))
            messages = self._message_controller.bulk_get(
                queue_name,
                message_ids=message_ids,
                project=project_id)

        except validation.ValidationFailed as ex:
            LOG.debug(ex)
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers)
        except Exception as ex:
            LOG.exception(ex)
            error = _(u'Message could not be retrieved.')
            headers = {'status': 500}
            return api_utils.error_response(req, error, headers, ex)

        # Prepare response
        messages = list(messages)
        if not messages:
            messages = []

        messages = [api_utils.format_message(message)
                    for message in messages]

        headers = {'status': 200}
        body = {'messages': messages}

        resp = response.Response(req, body, headers)
        return resp

    @api_utils.raises_conn_error
    def message_post(self, req):
        """Post a set of messages to a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        client_uuid = req._headers.get('Client-ID')
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')

        LOG.debug(u'Messages post - queue:  %(queue)s, '
                  u'project: %(project)s',
                  {'queue': queue_name, 'project': project_id})

        try:
            # Place JSON size restriction before parsing
            self._validate.message_length(req.content_length)
        except validation.ValidationFailed as ex:
            LOG.debug(ex)
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers)

        # Deserialize and validate the incoming messages
        document = api_utils.deserialize(req.stream, req.content_length)

        if 'messages' not in document:
            ex = _(u'Invalid request.')
            error = _(u'No messages were found in the request body.')
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers, error)

        # FIXME(vkmc): Use default TTL
        _message_post_spec = (
            ('ttl', int, 300),
            ('body', '*', None),
        )
        messages = api_utils.sanitize(document['messages'],
                                      _message_post_spec,
                                      doctype=api_utils.JSONArray)

        try:
            self._validate.message_posting(messages)

            if not self._queue_controller.exists(queue_name, project_id):
                self._queue_controller.create(queue_name, project=project_id)

            message_ids = self._message_controller.post(
                queue_name,
                messages=messages,
                project=project_id,
                client_uuid=client_uuid)

        except validation.ValidationFailed as ex:
            LOG.debug(ex)
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers)
        except storage_errors.DoesNotExist as ex:
            LOG.debug(ex)
            headers = {'status': 404}
            return api_utils.error_response(req, ex, headers)
        except storage_errors.MessageConflict as ex:
            LOG.exception(ex)
            error = _(u'No messages could be enqueued.')
            headers = {'status': 500}
            return api_utils.error_response(req, ex, headers, error)
        except Exception as ex:
            LOG.exception(ex)
            error = _(u'Messages could not be enqueued.')
            headers = {'status': 500}
            return api_utils.error_response(req, ex, headers, error)

        # Prepare the response
        headers = {'status': 201}
        ids_value = ','.join(message_ids)
        body = {'message_ids': ids_value}

        resp = response.Response(req, body, headers)
        return resp

    @api_utils.raises_conn_error
    def message_delete(self, req):
        """Delete a message from a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')
        message_id = req._body.get('message_id')

        LOG.debug(u'Messages item DELETE - message: %(message)s, '
                  u'queue: %(queue)s, project: %(project)s',
                  {'message': message_id,
                   'queue': queue_name,
                   'project': project_id})

        claim_id = req._body.get('claim_id')

        try:
            self._message_controller.delete(
                queue_name,
                message_id=message_id,
                project=project_id,
                claim=claim_id)
        except storage_errors.MessageNotClaimed as ex:
            LOG.debug(ex)
            error = _(u'A claim was specified, but the message '
                      u'is not currently claimed.')
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers, error)
        except storage_errors.ClaimDoesNotExist as ex:
            LOG.debug(ex)
            error = _(u'The specified claim does not exist or '
                      u'has expired.')
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers, error)

        except storage_errors.NotPermitted as ex:
            LOG.debug(ex)
            error = _(u'This message is claimed; it cannot be '
                      u'deleted without a valid claim ID.')
            headers = {'status': 403}
            return api_utils.error_response(req, ex, headers, error)
        except Exception as ex:
            LOG.exception(ex)
            error = _(u'Message could not be deleted.')
            headers = {'status': 500}
            return api_utils.error_response(req, ex, headers, error)

        headers = {'status': 204}
        body = {}

        resp = response.Response(req, body, headers)
        return resp

    @api_utils.raises_conn_error
    def message_delete_many(self, req):
        """Deletes a set of messages from a queue

        :param req: Request instance ready to be sent.
        :type req: `api.common.Request`
        :return: resp: Response instance
        :type: resp: `api.common.Response`
        """
        project_id = req._headers.get('X-Project-ID')
        queue_name = req._body.get('queue_name')

        LOG.debug(u'Messages collection DELETE - queue: %(queue)s, '
                  u'project: %(project)s',
                  {'queue': queue_name, 'project': project_id})

        message_ids = list(req._body.get('message_ids'))
        pop_limit = int(req._body.get('pop'))

        try:
            self._validate.message_deletion(message_ids, pop_limit)

        except validation.ValidationFailed as ex:
            LOG.debug(ex)
            headers = {'status': 400}
            return api_utils.error_response(req, ex, headers)

        if message_ids:
            return self._delete_messages_by_id(req, queue_name, message_ids,
                                               project_id)
        elif pop_limit:
            return self._pop_messages(req, queue_name, project_id, pop_limit)

    @api_utils.raises_conn_error
    def _delete_messages_by_id(self, req, queue_name, ids, project_id):
        try:
            self._message_controller.bulk_delete(
                queue_name,
                message_ids=ids,
                project=project_id)

        except Exception as ex:
            LOG.exception(ex)
            error = _(u'Messages could not be deleted.')
            headers = {'status': 500}
            return api_utils.error_response(req, ex, headers, error)

        headers = {'status': 204}
        body = {}

        resp = response.Response(req, body, headers)
        return resp

    @api_utils.raises_conn_error
    def _pop_messages(self, req, queue_name, project_id, pop_limit):
        try:
            LOG.debug(u'POP messages - queue: %(queue)s, '
                      u'project: %(project)s',
                      {'queue': queue_name, 'project': project_id})

            messages = self._message_controller.pop(
                queue_name,
                project=project_id,
                limit=pop_limit)

        except Exception as ex:
            LOG.exception(ex)
            error = _(u'Messages could not be popped.')
            headers = {'status': 500}
            return api_utils.error_response(req, ex, headers, error)

        # Prepare response
        if not messages:
            messages = []

        headers = {'status': 200}
        body = {'messages': messages}

        resp = response.Response(req, body, headers)
        return resp