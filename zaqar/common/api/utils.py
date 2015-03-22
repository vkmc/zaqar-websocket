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

import functools

import zaqar.common.api.errors as api_errors
import zaqar.common.api.response as response
from zaqar.i18n import _
import zaqar.openstack.common.log as logging
from zaqar.transport import utils

JSONObject = dict
"""Represents a JSON object in Python."""

JSONArray = list
"""Represents a JSON array in Python."""

LOG = logging.getLogger(__name__)


def deserialize(stream, len):
    """Deserializes JSON from a file-like stream.

    This function deserializes JSON from a stream, including
    translating read and parsing errors to generic error types.

    :param stream: file-like object from which to read an object or
        array of objects.
    :param len: number of bytes to read from stream
    :raises: BadRequest, ServiceUnavailable
    """

    if len is None:
        description = _(u'Request body can not be empty')
        raise api_errors.BadRequestBody(description)

    try:
        # TODO(kgriffs): read_json should stream the resulting list
        # of messages, returning a generator rather than buffering
        # everything in memory (bp/streaming-serialization).
        return utils.read_json(stream, len)

    except utils.MalformedJSON as ex:
        LOG.debug(ex)
        description = _(u'Request body could not be parsed.')
        raise api_errors.BadRequestBody(description)
    except utils.OverflowedJSONInteger as ex:
        LOG.debug(ex)
        description = _(u'JSON contains integer that is too large.')
        raise api_errors.BadRequestBody(description)
    except Exception as ex:
        # Error while reading from the network/server
        LOG.exception(ex)
        description = _(u'Request body could not be read.')
        raise api_errors.ServiceUnavailable(description)


def sanitize(document, spec=None, doctype=JSONObject):
    """Validates a document and drops undesired fields.

    :param document: A dict to verify according to `spec`.
    :param spec: (Default None) Iterable describing expected fields,
        yielding tuples with the form of:

            (field_name, value_type, default_value)

        Note that value_type may either be a Python type, or the
        special string '*' to accept any type. default_value is the
        default to give the field if it is missing, or None to require
        that the field be present.

        If spec is None, the incoming documents will not be validated.
    :param doctype: type of document to expect; must be either
        JSONObject or JSONArray.
    :raises: DocumentTypeNotSupported, TypeError
    :returns: A sanitized, filtered version of the document. If the
        document is a list of objects, each object will be filtered
        and returned in a new list. If, on the other hand, the document
        is expected to contain a single object, that object's fields will
        be filtered and the resulting object will be returned.
    """

    if doctype is JSONObject:
        if not isinstance(document, JSONObject):
            raise api_errors.DocumentTypeNotSupported()

        return document if spec is None else filter(document, spec)

    if doctype is JSONArray:
        if not isinstance(document, JSONArray):
            raise api_errors.DocumentTypeNotSupported()

        if spec is None:
            return document

        return [filter(obj, spec) for obj in document]

    raise TypeError('doctype must be either a JSONObject or JSONArray')


def raises_conn_error(func):
    """Handles generic Exceptions

    This decorator catches generic Exceptions and returns a generic
    Response.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as ex:
            LOG.exception(ex)
            error = _("Unexpected error.")
            req = kwargs.get('req')
            return error_response(req, ex, error)

    return wrapper


def error_response(req, exception, headers=None, error=None):
    body = {'exception': exception, 'error': error}
    resp = response.Response(req, body, headers)
    return resp


def format_message(message):
    return {
        'id': message['id'],
        'ttl': message['ttl'],
        'age': message['age'],
        'body': message['body'],
    }