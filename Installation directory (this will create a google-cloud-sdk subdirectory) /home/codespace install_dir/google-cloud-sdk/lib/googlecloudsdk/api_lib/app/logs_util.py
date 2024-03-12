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
"""General formatting utils, App Engine specific formatters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.logging import util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.util import times
import six


LOG_LEVELS = ['critical', 'error', 'warning', 'info', 'debug', 'any']

# Request logs come from different sources if the app is Flex or Standard.
FLEX_REQUEST = 'nginx.request'
STANDARD_REQUEST = 'request_log'
DEFAULT_LOGS = ['stderr', 'stdout', 'crash.log',
                FLEX_REQUEST, STANDARD_REQUEST]
NGINX_LOGS = [
    'appengine.googleapis.com/nginx.request',
    'appengine.googleapis.com/nginx.health_check']


def GetFilters(project, log_sources, service=None, version=None, level='any'):
  """Returns filters for App Engine app logs.

  Args:
    project: string name of project ID.
    log_sources: List of streams to fetch logs from.
    service: String name of service to fetch logs from.
    version: String name of version to fetch logs from.
    level: A string representing the severity of logs to fetch.

  Returns:
    A list of filter strings.
  """
  filters = ['resource.type="gae_app"']
  if service:
    filters.append('resource.labels.module_id="{0}"'.format(service))
  if version:
    filters.append('resource.labels.version_id="{0}"'.format(version))
  if level != 'any':
    filters.append('severity>={0}'.format(level.upper()))

  log_ids = []
  for log_type in sorted(log_sources):
    log_ids.append('appengine.googleapis.com/{0}'.format(log_type))
    if log_type in ('stderr', 'stdout'):
      log_ids.append(log_type)
  res = resources.REGISTRY.Parse(
      project, collection='appengine.projects').RelativeName()

  filters.append(_LogFilterForIds(log_ids, res))
  return filters


def _LogFilterForIds(log_ids, parent):
  """Constructs a log filter expression from the log_ids and parent name."""
  if not log_ids:
    return None
  log_names = ['"{0}"'.format(util.CreateLogResourceName(parent, log_id))
               for log_id in log_ids]
  log_names = ' OR '.join(log_names)
  if len(log_ids) > 1:
    log_names = '(%s)' % log_names
  return 'logName=%s' % log_names


def FormatAppEntry(entry):
  """App Engine formatter for `LogPrinter`.

  Args:
    entry: A log entry message emitted from the V2 API client.

  Returns:
    A string representing the entry or None if there was no text payload.
  """
  # TODO(b/36056460): Output others than text here too?
  if entry.resource.type != 'gae_app':
    return None
  if entry.protoPayload:
    text = six.text_type(entry.protoPayload)
  elif entry.jsonPayload:
    text = six.text_type(entry.jsonPayload)
  else:
    text = entry.textPayload
  service, version = _ExtractServiceAndVersion(entry)
  return '{service}[{version}]  {text}'.format(service=service,
                                               version=version,
                                               text=text)


def FormatRequestLogEntry(entry):
  """App Engine request_log formatter for `LogPrinter`.

  Args:
    entry: A log entry message emitted from the V2 API client.

  Returns:
    A string representing the entry if it is a request entry.
  """
  if entry.resource.type != 'gae_app':
    return None
  log_id = util.ExtractLogId(entry.logName)
  if log_id != 'appengine.googleapis.com/request_log':
    return None
  service, version = _ExtractServiceAndVersion(entry)
  def GetStr(key):
    return next((x.value.string_value for x in
                 entry.protoPayload.additionalProperties
                 if x.key == key), '-')
  def GetInt(key):
    return next((x.value.integer_value for x in
                 entry.protoPayload.additionalProperties
                 if x.key == key), '-')
  msg = ('"{method} {resource} {http_version}" {status}'
         .format(
             method=GetStr('method'),
             resource=GetStr('resource'),
             http_version=GetStr('httpVersion'),
             status=GetInt('status')))
  return '{service}[{version}]  {msg}'.format(service=service,
                                              version=version,
                                              msg=msg)


def FormatNginxLogEntry(entry):
  """App Engine nginx.* formatter for `LogPrinter`.

  Args:
    entry: A log entry message emitted from the V2 API client.

  Returns:
    A string representing the entry if it is a request entry.
  """
  if entry.resource.type != 'gae_app':
    return None
  log_id = util.ExtractLogId(entry.logName)
  if log_id not in NGINX_LOGS:
    return None
  service, version = _ExtractServiceAndVersion(entry)
  msg = ('"{method} {resource}" {status}'
         .format(
             method=entry.httpRequest.requestMethod or '-',
             resource=entry.httpRequest.requestUrl or '-',
             status=entry.httpRequest.status or '-'))
  return '{service}[{version}]  {msg}'.format(service=service,
                                              version=version,
                                              msg=msg)


def _ExtractServiceAndVersion(entry):
  """Extract service and version from a App Engine log entry.

  Args:
    entry: An App Engine log entry.

  Returns:
    A 2-tuple of the form (service_id, version_id)
  """
  # TODO(b/36051034): If possible, extract instance ID too
  ad_prop = entry.resource.labels.additionalProperties
  service = next(x.value
                 for x in ad_prop
                 if x.key == 'module_id')
  version = next(x.value
                 for x in ad_prop
                 if x.key == 'version_id')
  return (service, version)


class LogPrinter(object):
  """Formats V2 API log entries to human readable text on a best effort basis.

  A LogPrinter consists of a collection of formatter functions which attempts
  to format specific log entries in a human readable form. The `Format` method
  safely returns a human readable string representation of a log entry, even if
  the provided formatters fails.

  The output format is `{timestamp} {log_text}`, where `timestamp` has a
  configurable but consistent format within a LogPrinter whereas `log_text` is
  emitted from one of its formatters (and truncated if necessary).

  See https://cloud.google.com/logging/docs/api/introduction_v2

  Attributes:
    api_time_format: str, the output format to print. See datetime.strftime()
    max_length: The maximum length of a formatted log entry after truncation.
  """

  def __init__(self, api_time_format='%Y-%m-%d %H:%M:%S', max_length=None):
    self.formatters = []
    self.api_time_format = api_time_format
    self.max_length = max_length

  def Format(self, entry):
    """Safely formats a log entry into human readable text.

    Args:
      entry: A log entry message emitted from the V2 API client.

    Returns:
      A string without line breaks respecting the `max_length` property.
    """
    text = self._LogEntryToText(entry)
    text = text.strip().replace('\n', '  ')

    try:
      time = times.FormatDateTime(times.ParseDateTime(entry.timestamp),
                                  self.api_time_format)
    except times.Error:
      log.warning('Received timestamp [{0}] does not match expected'
                  ' format.'.format(entry.timestamp))
      time = '????-??-?? ??:??:??'

    out = '{timestamp} {log_text}'.format(
        timestamp=time,
        log_text=text)
    if self.max_length and len(out) > self.max_length:
      out = out[:self.max_length - 3] + '...'
    return out

  def RegisterFormatter(self, formatter):
    """Attach a log entry formatter function to the printer.

    Note that if multiple formatters are attached to the same printer, the first
    added formatter that successfully formats the entry will be used.

    Args:
      formatter: A formatter function which accepts a single argument, a log
          entry. The formatter must either return the formatted log entry as a
          string, or None if it is unable to format the log entry.
          The formatter is allowed to raise exceptions, which will be caught and
          ignored by the printer.
    """
    self.formatters.append(formatter)

  def _LogEntryToText(self, entry):
    """Use the formatters to convert a log entry to unprocessed text."""
    out = None
    for fn in self.formatters + [self._FallbackFormatter]:
      # pylint:disable=bare-except
      try:
        out = fn(entry)
        if out:
          break
      except KeyboardInterrupt as e:
        raise e
      except:
        pass
    if not out:
      log.debug('Could not format log entry: %s %s %s', entry.timestamp,
                entry.logName, entry.insertId)
      out = ('< UNREADABLE LOG ENTRY {0}. OPEN THE DEVELOPER CONSOLE TO '
             'INSPECT. >'.format(entry.insertId))
    return out

  def _FallbackFormatter(self, entry):
    # TODO(b/36057358): Is there better serialization for messages than
    # six.text_type()?
    if entry.protoPayload:
      return six.text_type(entry.protoPayload)
    elif entry.jsonPayload:
      return six.text_type(entry.jsonPayload)
    else:
      return entry.textPayload

