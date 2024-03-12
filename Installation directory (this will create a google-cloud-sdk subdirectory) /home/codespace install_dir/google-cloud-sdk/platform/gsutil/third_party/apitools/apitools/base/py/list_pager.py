#!/usr/bin/env python
#
# Copyright 2015 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A helper function that executes a series of List queries for many APIs."""

from apitools.base.py import encoding
import six

__all__ = [
    'YieldFromList',
]


def _GetattrNested(message, attribute):
    """Gets a possibly nested attribute.

    Same as getattr() if attribute is a string;
    if attribute is a tuple, returns the nested attribute referred to by
    the fields in the tuple as if they were a dotted accessor path.

    (ex _GetattrNested(msg, ('foo', 'bar', 'baz')) gets msg.foo.bar.baz
    """
    if isinstance(attribute, six.string_types):
        return getattr(message, attribute)
    elif len(attribute) == 0:
        return message
    else:
        return _GetattrNested(getattr(message, attribute[0]), attribute[1:])


def _SetattrNested(message, attribute, value):
    """Sets a possibly nested attribute.

    Same as setattr() if attribute is a string;
    if attribute is a tuple, sets the nested attribute referred to by
    the fields in the tuple as if they were a dotted accessor path.

    (ex _SetattrNested(msg, ('foo', 'bar', 'baz'), 'v') sets msg.foo.bar.baz
    to 'v'
    """
    if isinstance(attribute, six.string_types):
        return setattr(message, attribute, value)
    elif len(attribute) < 1:
        raise ValueError("Need an attribute to set")
    elif len(attribute) == 1:
        return setattr(message, attribute[0], value)
    else:
        return setattr(_GetattrNested(message, attribute[:-1]),
                       attribute[-1], value)


def YieldFromList(
        service, request, global_params=None, limit=None, batch_size=100,
        method='List', field='items', predicate=None,
        current_token_attribute='pageToken',
        next_token_attribute='nextPageToken',
        batch_size_attribute='maxResults',
        get_field_func=_GetattrNested):
    """Make a series of List requests, keeping track of page tokens.

    Args:
      service: apitools_base.BaseApiService, A service with a .List() method.
      request: protorpc.messages.Message, The request message
          corresponding to the service's .List() method, with all the
          attributes populated except the .maxResults and .pageToken
          attributes.
      global_params: protorpc.messages.Message, The global query parameters to
           provide when calling the given method.
      limit: int, The maximum number of records to yield. None if all available
          records should be yielded.
      batch_size: int, The number of items to retrieve per request.
      method: str, The name of the method used to fetch resources.
      field: str, The field in the response that will be a list of items.
      predicate: lambda, A function that returns true for items to be yielded.
      current_token_attribute: str or tuple, The name of the attribute in a
          request message holding the page token for the page being
          requested. If a tuple, path to attribute.
      next_token_attribute: str or tuple, The name of the attribute in a
          response message holding the page token for the next page. If a
          tuple, path to the attribute.
      batch_size_attribute: str or tuple, The name of the attribute in a
          response message holding the maximum number of results to be
          returned. None if caller-specified batch size is unsupported.
          If a tuple, path to the attribute.
      get_field_func: Function that returns the items to be yielded. Argument
          is response message, and field.

    Yields:
      protorpc.message.Message, The resources listed by the service.

    """
    request = encoding.CopyProtoMessage(request)
    _SetattrNested(request, current_token_attribute, None)
    while limit is None or limit:
        if batch_size_attribute:
            # On Py3, None is not comparable so min() below will fail.
            # On Py2, None is always less than any number so if batch_size
            # is None, the request_batch_size will always be None regardless
            # of the value of limit. This doesn't generally strike me as the
            # correct behavior, but this change preserves the existing Py2
            # behavior on Py3.
            if batch_size is None:
                request_batch_size = None
            else:
                request_batch_size = min(batch_size, limit or batch_size)
            _SetattrNested(request, batch_size_attribute, request_batch_size)
        response = getattr(service, method)(request,
                                            global_params=global_params)
        items = get_field_func(response, field)
        if predicate:
            items = list(filter(predicate, items))
        for item in items:
            yield item
            if limit is None:
                continue
            limit -= 1
            if not limit:
                return
        token = _GetattrNested(response, next_token_attribute)
        if not token:
            return
        _SetattrNested(request, current_token_attribute, token)
