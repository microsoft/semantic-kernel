# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A module that converts API exceptions to core exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import io
import json
import logging
import string
from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.util import resource as resource_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_lex
from googlecloudsdk.core.resource import resource_printer
from googlecloudsdk.core.resource import resource_property
from googlecloudsdk.core.util import encoding

import six


# Some formatter characters are special inside {...}. The _Escape / _Expand pair
# escapes special chars inside {...} and ignores them outside.
_ESCAPE = '~'  # '\x01'
_ESCAPED_COLON = 'C'
_ESCAPED_ESCAPE = 'E'
_ESCAPED_LEFT_CURLY = 'L'
_ESCAPED_RIGHT_CURLY = 'R'

# ErrorInfo identifier used for extracting domain based handlers.
ERROR_INFO_SUFFIX = 'google.rpc.ErrorInfo'


def _Escape(s):
  """Return s with format special characters escaped."""
  r = []
  n = 0
  for c in s:
    if c == _ESCAPE:
      r.append(_ESCAPE + _ESCAPED_ESCAPE + _ESCAPE)
    elif c == ':':
      r.append(_ESCAPE + _ESCAPED_COLON + _ESCAPE)
    elif c == '{':
      if n > 0:
        r.append(_ESCAPE + _ESCAPED_LEFT_CURLY + _ESCAPE)
      else:
        r.append('{')
      n += 1
    elif c == '}':
      n -= 1
      if n > 0:
        r.append(_ESCAPE + _ESCAPED_RIGHT_CURLY + _ESCAPE)
      else:
        r.append('}')
    else:
      r.append(c)
  return ''.join(r)


def _Expand(s):
  """Return s with escaped format special characters expanded."""
  r = []
  n = 0
  i = 0
  while i < len(s):
    c = s[i]
    i += 1
    if c == _ESCAPE and i + 1 < len(s) and s[i + 1] == _ESCAPE:
      c = s[i]
      i += 2
      if c == _ESCAPED_LEFT_CURLY:
        if n > 0:
          r.append(_ESCAPE + _ESCAPED_LEFT_CURLY)
        else:
          r.append('{')
        n += 1
      elif c == _ESCAPED_RIGHT_CURLY:
        n -= 1
        if n > 0:
          r.append(_ESCAPE + _ESCAPED_RIGHT_CURLY)
        else:
          r.append('}')
      elif n > 0:
        r.append(s[i - 3:i])
      elif c == _ESCAPED_COLON:
        r.append(':')
      elif c == _ESCAPED_ESCAPE:
        r.append(_ESCAPE)
    else:
      r.append(c)
  return ''.join(r)


class _JsonSortedDict(dict):
  """A dict with a sorted JSON string representation."""

  def __str__(self):
    return json.dumps(self, sort_keys=True)


class FormattableErrorPayload(string.Formatter):
  """Generic payload for an HTTP error that supports format strings.

  Attributes:
    content: The dumped JSON content.
    message: The human readable error message.
    status_code: The HTTP status code number.
    status_description: The status_code description.
    status_message: Context specific status message.
  """

  def __init__(self, http_error):
    """Initialize a FormattableErrorPayload instance.

    Args:
      http_error: An Exception that subclasses can use to populate class
        attributes, or a string to use as the error message.
    """
    super(FormattableErrorPayload, self).__init__()
    self._value = '{?}'
    self.content = {}
    self.status_code = 0
    self.status_description = ''
    self.status_message = ''
    if isinstance(http_error, six.string_types):
      self.message = http_error
    else:
      self.message = self._MakeGenericMessage()

  def get_field(self, field_name, unused_args, unused_kwargs):
    r"""Returns the value of field_name for string.Formatter.format().

    Args:
      field_name: The format string field name to get in the form
        name - the value of name in the payload, '' if undefined
        name?FORMAT - if name is non-empty then re-formats with FORMAT, where
          {?} is the value of name. For example, if name=NAME then
          {name?\nname is "{?}".} expands to '\nname is "NAME".'.
        .a.b.c - the value of a.b.c in the JSON decoded payload contents.
          For example, '{.errors.reason?[{?}]}' expands to [REASON] if
          .errors.reason is defined.
      unused_args: Ignored.
      unused_kwargs: Ignored.

    Returns:
      The value of field_name for string.Formatter.format().
    """
    field_name = _Expand(field_name)
    if field_name == '?':
      return self._value, field_name
    parts = field_name.split('?', 1)
    subparts = parts.pop(0).split(':', 1)
    name = subparts.pop(0)
    printer_format = subparts.pop(0) if subparts else None
    recursive_format = parts.pop(0) if parts else None
    name, value = self._GetField(name)
    if not value and not isinstance(value, (int, float)):
      return '', name
    if printer_format or not isinstance(
        value, (six.text_type, six.binary_type, float) + six.integer_types):
      buf = io.StringIO()
      resource_printer.Print(
          value, printer_format or 'default', out=buf, single=True)
      value = buf.getvalue().strip()
    if recursive_format:
      self._value = value
      value = self.format(_Expand(recursive_format))
    return value, name

  def _GetField(self, name):
    """Gets the value corresponding to name in self.content or class attributes.

    If `name` starts with a period, treat it as a key in self.content and get
    the corresponding value. Otherwise get the value of the class attribute
    named `name` first and fall back to checking keys in self.content.

    Args:
      name (str): The name of the attribute to return the value of.

    Returns:
      A tuple where the first value is `name` with any leading periods dropped,
      and the second value is the value of a class attribute or key in
      self.content.
    """
    if '.' in name:
      if name.startswith('.'):
        # Only check self.content.
        check_payload_attributes = False
        name = name[1:]
      else:
        # Check the payload attributes first, then self.content.
        check_payload_attributes = True
      key = resource_lex.Lexer(name).Key()
      content = self.content
      if check_payload_attributes and key:
        value = self.__dict__.get(key[0], None)
        if value:
          content = {key[0]: value}
      value = resource_property.Get(content, key, None)
    elif name:
      value = self.__dict__.get(name, None)
    else:
      value = None

    return name, value

  def _MakeGenericMessage(self):
    """Makes a generic human readable message from the HttpError."""
    description = self._MakeDescription()
    if self.status_message:
      return '{0}: {1}'.format(description, self.status_message)
    return description

  def _MakeDescription(self):
    """Makes description for error by checking which fields are filled in."""
    description = self.status_description
    if description:
      if description.endswith('.'):
        description = description[:-1]
      return description
    # Example: 'HTTPError 403'
    return 'HTTPError {0}'.format(self.status_code)


class HttpErrorPayload(FormattableErrorPayload):
  r"""Converts apitools HttpError payload to an object.

  Attributes:
    api_name: The url api name.
    api_version: The url version.
    content: The dumped JSON content.
    details: A list of {'@type': TYPE, 'detail': STRING} typed details.
    domain_details: ErrorInfo metadata Indexed by domain.
    violations: map of subject to error message for that subject.
    field_violations: map of field name to error message for that field.
    error_info: content['error'].
    instance_name: The url instance name.
    message: The human readable error message.
    resource_item: The resource type.
    resource_name: The url resource name.
    resource_version: The resource version.
    status_code: The HTTP status code number.
    status_description: The status_code description.
    status_message: Context specific status message.
    type_details: ErrorDetails Indexed by type.
    url: The HTTP url.
    .<a>.<b>...: The <a>.<b>... attribute in the JSON content (synthesized in
      get_field()).

  Examples:
    error_format values and resulting output:

    'Error: [{status_code}] {status_message}{url?\n{?}}{.debugInfo?\n{?}}'

      Error: [404] Not found
      http://dotcom/foo/bar
      <content.debugInfo in yaml print format>

    'Error: {status_code} {details?\n\ndetails:\n{?}}'

      Error: 404

      details:
      - foo
      - bar

     'Error [{status_code}] {status_message}\n'
     '{.:value(details.detail.list(separator="\n"))}'

       Error [400] Invalid request.
       foo
       bar
  """

  def __init__(self, http_error):
    super(HttpErrorPayload, self).__init__(http_error)
    self.api_name = ''
    self.api_version = ''
    self.details = []
    self.violations = {}
    self.field_violations = {}
    self.error_info = None
    self.instance_name = ''
    self.resource_item = ''
    self.resource_name = ''
    self.resource_version = ''
    self.url = ''
    if not isinstance(http_error, six.string_types):
      self._ExtractResponseAndJsonContent(http_error)
      self._ExtractUrlResourceAndInstanceNames(http_error)
      self.message = self._MakeGenericMessage()

  def _GetField(self, name):
    if name.startswith('field_violations.'):
      _, field = name.split('.', 1)
      value = self.field_violations.get(field)
    elif name.startswith('violations.'):
      _, subject = name.split('.', 1)
      value = self.violations.get(subject)
    else:
      name, value = super(HttpErrorPayload, self)._GetField(name)
    return name, value

  def _ExtractResponseAndJsonContent(self, http_error):
    """Extracts the response and JSON content from the HttpError."""
    response = getattr(http_error, 'response', None)
    if response:
      self.status_code = int(response.get('status', 0))
      self.status_description = encoding.Decode(response.get('reason', ''))
    content = encoding.Decode(http_error.content)
    try:
      # X-GOOG-API-FORMAT-VERSION: 2
      self.content = _JsonSortedDict(json.loads(content))
      self.error_info = _JsonSortedDict(self.content['error'])
      if not self.status_code:  # Could have been set above.
        self.status_code = int(self.error_info.get('code', 0))
      if not self.status_description:  # Could have been set above.
        self.status_description = self.error_info.get('status', '')
      self.status_message = self.error_info.get('message', '')
      self.details = self.error_info.get('details', [])
      self.violations = self._ExtractViolations(self.details)
      self.field_violations = self._ExtractFieldViolations(self.details)
      self.type_details = self._IndexErrorDetailsByType(self.details)
      self.domain_details = self._IndexErrorInfoByDomain(self.details)
    except (KeyError, TypeError, ValueError):
      self.status_message = content
    except AttributeError:
      pass

  def _IndexErrorDetailsByType(self, details):
    """Extracts and indexes error details list by the type attribute."""
    type_map = collections.defaultdict(list)
    for item in details:
      error_type = item.get('@type', None)
      if error_type:
        error_type_suffix = error_type.split('.')[-1]
        type_map[error_type_suffix].append(item)
    return type_map

  def _IndexErrorInfoByDomain(self, details):
    """Extracts and indexes error info list by the domain attribute."""
    domain_map = collections.defaultdict(list)
    for item in details:
      error_type = item.get('@type', None)
      if error_type.endswith(ERROR_INFO_SUFFIX):
        domain = item.get('domain', None)
        if domain:
          domain_map[domain].append(item)
    return domain_map

  def _ExtractUrlResourceAndInstanceNames(self, http_error):
    """Extracts the url resource type and instance names from the HttpError."""
    self.url = http_error.url
    if not self.url:
      return

    try:
      name, version, resource_path = resource_util.SplitEndpointUrl(
          self.url)
    except resource_util.InvalidEndpointException:
      return

    if name:
      self.api_name = name
    if version:
      self.api_version = version

    # We do not attempt to parse this, as generally it doesn't represent a
    # resource uri.
    resource_parts = resource_path.split('/')
    if not 1 < len(resource_parts) < 4:
      return
    self.resource_name = resource_parts[0]
    instance_name = resource_parts[1]

    self.instance_name = instance_name.split('?')[0]
    self.resource_item = '{} instance'.format(self.resource_name)

  def _MakeDescription(self):
    """Makes description for error by checking which fields are filled in."""
    if self.status_code and self.resource_item and self.instance_name:
      if self.status_code == 403:
        return ('User [{0}] does not have permission to access {1} [{2}] (or '
                'it may not exist)').format(
                    properties.VALUES.core.account.Get(),
                    self.resource_item, self.instance_name)
      if self.status_code == 404:
        return '{0} [{1}] not found'.format(
            self.resource_item.capitalize(), self.instance_name)
      if self.status_code == 409:
        if self.resource_name == 'projects':
          return ('Resource in projects [{0}] '
                  'is the subject of a conflict').format(self.instance_name)
        else:
          return '{0} [{1}] is the subject of a conflict'.format(
              self.resource_item.capitalize(), self.instance_name)

    return super(HttpErrorPayload, self)._MakeDescription()

  def _ExtractViolations(self, details):
    """Extracts a map of violations from the given error's details.

    Args:
      details: JSON-parsed details field from parsed json of error.

    Returns:
      Map[str, str] sub -> error description. The iterator of it is ordered by
      the order the subjects first appear in the errror.
    """
    results = collections.OrderedDict()
    for detail in details:
      if 'violations' not in detail:
        continue
      violations = detail['violations']
      if not isinstance(violations, list):
        continue
      sub = detail.get('subject')
      for violation in violations:
        try:
          local_sub = violation.get('subject')
          subject = sub or local_sub
          if subject:
            if subject in results:
              results[subject] += '\n' + violation['description']
            else:
              results[subject] = violation['description']
        except (KeyError, TypeError):
          # If violation or description are the wrong type or don't exist.
          pass
    return results

  def _ExtractFieldViolations(self, details):
    """Extracts a map of field violations from the given error's details.

    Args:
      details: JSON-parsed details field from parsed json of error.

    Returns:
      Map[str, str] field (in dotted format) -> error description.
      The iterator of it is ordered by the order the fields first
      appear in the error.
    """
    results = collections.OrderedDict()
    for deet in details:
      if 'fieldViolations' not in deet:
        continue
      violations = deet['fieldViolations']
      if not isinstance(violations, list):
        continue
      f = deet.get('field')
      for viol in violations:
        try:
          local_f = viol.get('field')
          field = f or local_f
          if field:
            if field in results:
              results[field] += '\n' + viol['description']
            else:
              results[field] = viol['description']
        except (KeyError, TypeError):
          # If violation or description are the wrong type or don't exist.
          pass
    return results


class HttpException(core_exceptions.Error):
  """Transforms apitools HttpError to api_lib HttpException.

  Attributes:
    error: The original HttpError.
    error_format: An HttpErrorPayload format string.
    payload: The HttpErrorPayload object.
  """

  def __init__(self, error, error_format=None, payload_class=HttpErrorPayload):
    super(HttpException, self).__init__('')
    self.error = error
    self.error_format = error_format
    self.payload = payload_class(error)

  def __str__(self):
    error_format = self.error_format
    if error_format is None:
      error_format = '{message}'
      if properties.VALUES.core.parse_error_details.GetBool():
        error_format += ('\n{type_details.LocalizedMessage'
                         ':value(message.list(separator="\n"))}')
      else:
        error_format += '{details?\n{?}}'
      if log.GetVerbosity() <= logging.DEBUG:
        error_format += '{.debugInfo?\n{?}}'
    return _Expand(self.payload.format(_Escape(error_format)))

  @property
  def message(self):
    return six.text_type(self)

  def __hash__(self):
    return hash(self.message)

  def __eq__(self, other):
    if isinstance(other, HttpException):
      return self.message == other.message
    return False


def CatchHTTPErrorRaiseHTTPException(format_str=None):
  """Decorator that catches an HttpError and returns a custom error message.

  It catches the raw Http Error and runs it through the given format string to
  get the desired message.

  Args:
    format_str: An HttpErrorPayload format string. Note that any properties that
    are accessed here are on the HTTPErrorPayload object, and not the raw
    object returned from the server.

  Returns:
    A custom error message.

  Example:
    @CatchHTTPErrorRaiseHTTPException('Error [{status_code}]')
    def some_func_that_might_throw_an_error():
      ...
  """

  def CatchHTTPErrorRaiseHTTPExceptionDecorator(run_func):
    # Need to define a secondary wrapper to get an argument to the outer
    # decorator.
    def Wrapper(*args, **kwargs):
      try:
        return run_func(*args, **kwargs)
      except apitools_exceptions.HttpError as error:
        exc = HttpException(error, format_str)
        core_exceptions.reraise(exc)
    return Wrapper

  return CatchHTTPErrorRaiseHTTPExceptionDecorator
