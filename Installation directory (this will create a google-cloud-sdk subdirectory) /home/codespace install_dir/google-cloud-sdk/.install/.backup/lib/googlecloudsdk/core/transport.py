# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Module for common transport utilities, such as request wrapping."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc
import platform
import re
import time
import uuid

from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import platforms
import six
from six.moves import urllib
from six.moves import zip  # pylint: disable=redefined-builtin

ENCODING = None if six.PY2 else 'utf-8'
INVOCATION_ID = uuid.uuid4().hex

TOKEN_URIS = [
    'https://accounts.google.com/o/oauth2/token',
    'https://www.googleapis.com/oauth2/v3/token',
    'https://www.googleapis.com/oauth2/v4/token',
    'https://oauth2.googleapis.com/token',
    'https://oauth2.googleapis.com/oauth2/v4/token'
]


class Request(six.with_metaclass(abc.ABCMeta, object)):
  """Encapsulates parameters for making a general HTTP request.

  Attributes:
    uri: URI of the HTTP resource.
    method: HTTP method to perform, such as GET, POST, DELETE, etc.
    headers: Additional headers to include in the request.
    body: Body of the request.
  """

  def __init__(self, uri, method, headers, body):
    """Instantiates a Request object.

    Args:
      uri: URI of the HTTP resource.
      method: HTTP method to perform, such as GET, POST, DELETE, etc.
      headers: Additional headers to include in the request.
      body: Body of the request.

    Returns:
      Request
    """
    self.uri = uri
    self.method = method
    self.headers = headers
    self.body = body

  @classmethod
  @abc.abstractmethod
  def FromRequestArgs(cls, *args, **kwargs):
    """Returns a Request object.

    Args:
      *args: args to be passed into http.request
      **kwargs: dictionary of kwargs to be passed into http.request

    Returns:
      Request
    """

  @abc.abstractmethod
  def ToRequestArgs(self):
    """Returns the args and kwargs to be used when calling http.request."""


class Response(six.with_metaclass(abc.ABCMeta, object)):
  """Encapsulates responses from making a general HTTP request.

  Attributes:
    status_code:
    headers: Headers of the response.
    body: Body of the response.
  """

  def __init__(self, status_code, headers, body):
    """Instantiates a Response object.

    Args:
      status_code:
      headers: Headers of the response.
      body: Body of the response.

    Returns:
      Response
    """
    self.status_code = status_code
    self.headers = headers
    self.body = body

  @classmethod
  @abc.abstractmethod
  def FromResponse(cls, response):
    """Returns a Response object.

    Args:
      response: raw response from calling http.request.

    Returns:
      Response
    """


class RequestWrapper(six.with_metaclass(abc.ABCMeta, object)):
  """Class for wrapping http requests.

  The general process is that you can define a series of handlers that get
  executed before and after the original http request you are mapping. All the
  request handlers are executed in the order provided. Request handlers must
  return a result that is used when invoking the corresponding response handler.
  Request handlers don't actually execute the request but rather just modify the
  request arguments. After all request handlers are executed, the original http
  request is executed. Finally, all response handlers are executed in order,
  getting passed both the http response as well as the result from their
  corresponding request handler.

  Attributes:
    request_class: Class used to represent a generic HTTP request.
    response_class: Class used to represent a generic HTTP request.
  """
  request_class = Request
  response_class = Response

  @abc.abstractmethod
  def DecodeResponse(self, response, response_encoding):
    """Decodes the response body according to response_encoding."""

  def WrapWithDefaults(self,
                       http_client,
                       response_encoding=None,
                       streaming_response_body=False,
                       redact_request_body_reason=None):
    """Wraps request with user-agent, and trace reporting.

    Args:
      http_client: The original http client to be wrapped.
      response_encoding: str, the encoding to use to decode the response.
      streaming_response_body: bool, True indicates that the response body will
          be a streaming body.
      redact_request_body_reason: str, the reason why the request body must be
          redacted if --log-http is used. If None, the body is not redacted.

    Returns:
      http, The same http object but with the request method wrapped.
    """
    gcloud_ua = MakeUserAgentString(
        properties.VALUES.metrics.command_name.Get())
    handlers = [
        Handler(RecordStartTime(), ReportDuration()),
        # TODO(b/160008076): The CLOUDSDK_USER_AGENT prefix may already be
        # provided by the upper stack before the plan of b/160008076 is
        # finished. The transport will not duplicate this string if this is the
        # case. Update MaybePrependToHeader() to PrependToHeader() in the step 4
        # of b/160008076.
        # More details in the 'Plan of record' section of b/160008076.
        Handler(MaybePrependToHeader('user-agent', config.CLOUDSDK_USER_AGENT)),
        Handler(AppendToHeader('user-agent', gcloud_ua))
    ]

    trace_value = GetTraceValue()
    if trace_value:
      handlers.append(Handler(AddQueryParam('trace', trace_value)))

    request_reason = properties.VALUES.core.request_reason.Get()
    if request_reason:
      handlers.append(
          Handler(SetHeader('X-Goog-Request-Reason', request_reason)))

    request_org_restriction_headers = properties.VALUES.resource_policy.org_restriction_header.Get(
    )
    if request_org_restriction_headers:
      handlers.append(
          Handler(
              SetHeader('X-Goog-Allowed-Resources',
                        request_org_restriction_headers)))

    # Do this one last so that it sees the effects of the other modifiers.
    if properties.VALUES.core.log_http.GetBool():
      redact_token = properties.VALUES.core.log_http_redact_token.GetBool()
      show_request_body = (
          properties.VALUES.core.log_http_show_request_body.GetBool())
      handlers.append(
          Handler(
              LogRequest(redact_token,
                         redact_request_body_reason if not show_request_body
                         else None),
              LogResponse(streaming_response_body)))

    self.WrapRequest(http_client, handlers, response_encoding=response_encoding)
    return http_client

  def WrapRequest(self,
                  http_client,
                  handlers,
                  exc_handler=None,
                  exc_type=Exception,
                  response_encoding=None):
    """Wraps an http client with request modifiers.

    Args:
      http_client: The original http client to be wrapped.
      handlers: [Handler], The handlers to execute before and after the original
        request.
      exc_handler: f(e), A function that takes an exception and handles it. It
        should also throw an exception if you don't want it to be swallowed.
      exc_type: The type of exception that should be caught and given to the
        handler. It could be a tuple to catch more than one exception type.
      response_encoding: str, the encoding to use to decode the response.
    """
    orig_request = http_client.request

    def WrappedRequest(*args, **kwargs):
      """Replacement http_client.request() method."""
      handler_request = self.request_class.FromRequestArgs(*args, **kwargs)

      # Encode request headers
      headers = {h: v for h, v in six.iteritems(handler_request.headers)}
      handler_request.headers = {}
      for h, v in six.iteritems(headers):
        h, v = _EncodeHeader(h, v)
        handler_request.headers[h] = v

      modifier_data = []
      for handler in handlers:
        modifier_result = handler.request(handler_request)
        modifier_data.append(modifier_result)

      try:
        modified_args, modified_kwargs = handler_request.ToRequestArgs()
        response = orig_request(*modified_args, **modified_kwargs)
      except exc_type as e:  # pylint: disable=broad-except
        response = None
        if exc_handler:
          exc_handler(e)
          return
        else:
          raise

      if response_encoding is not None:
        response = self.DecodeResponse(response, response_encoding)

      handler_response = self.response_class.FromResponse(response)
      for handler, data in zip(handlers, modifier_data):
        if handler.response:
          handler.response(handler_response, data)

      return response

    http_client.request = WrappedRequest


class Handler(object):
  """A holder object for a pair of request and response handlers.

  Request handlers are invoked before the original http request, response
  handlers are invoked after.
  """

  def __init__(self, request, response=None):
    """Creates a new Handler.

    Args:
      request: f(request) -> data, A function that gets called before the
        original http request gets called. It is passed a Request object that
        encapsulates the parameters of an http request. It returns data to be
        passed to its corresponding response hander.
      response: f(response, data), A function that gets called after the
        original http request. It is passed a Response object that encapsulates
        the response of an http request as well as whatever the request handler
        returned as data.
    """
    self.request = request
    self.response = response


def _EncodeHeader(header, value):
  if isinstance(header, six.text_type):
    header = header.encode('utf-8')
  if isinstance(value, six.text_type):
    value = value.encode('utf-8')
  return header, value


def MaybePrependToHeader(header, value):
  """Prepends the given value if the existing header does not start with it.

  Args:
    header: str, The name of the header to prepend to.
    value: str, The value to prepend to the existing header value.

  Returns:
    A function that can be used in a Handler.request.
  """
  header, value = _EncodeHeader(header, value)

  def _MaybePrependToHeader(request):
    """Maybe prepends a value to a header on a request."""
    headers = request.headers
    current_value = b''
    for hdr, v in six.iteritems(headers):
      if hdr.lower() == header.lower():
        current_value = v
        del headers[hdr]
        break

    if not current_value.startswith(value):
      current_value = (value + b' ' + current_value).strip()
    headers[header] = current_value

  return _MaybePrependToHeader


def AppendToHeader(header, value):
  """Appends the given value to the existing value in the http request.

  Args:
    header: str, The name of the header to append to.
    value: str, The value to append to the existing header value.

  Returns:
    A function that can be used in a Handler.request.
  """
  header, value = _EncodeHeader(header, value)

  def _AppendToHeader(request):
    """Appends a value to a header on a request."""
    headers = request.headers
    current_value = b''
    for hdr, v in six.iteritems(headers):
      if hdr.lower() == header.lower():
        current_value = v
        del headers[hdr]
        break

    headers[header] = ((current_value + b' ' +
                        value).strip() if current_value else value)

  return _AppendToHeader


def SetHeader(header, value):
  """Sets the given header value in the http request.

  Args:
    header: str, The name of the header to set to.
    value: str, The new value of the header.

  Returns:
    A function that can be used in a Handler.request.
  """
  header, value = _EncodeHeader(header, value)

  def _SetHeader(request):
    """Sets a header on a request."""
    headers = request.headers
    for hdr in six.iterkeys(headers):
      if hdr.lower() == header.lower():
        del headers[hdr]
        break

    headers[header] = value

  return _SetHeader


def AddQueryParam(param, value):
  """Adds the given query parameter to the http request.

  Args:
    param: str, The name of the parameter.
    value: str, The value of the parameter.

  Returns:
    A function that can be used in a Handler.request.
  """

  def _AddQueryParam(request):
    """Sets a query parameter on a request."""
    url_parts = urllib.parse.urlsplit(request.uri)
    query_params = urllib.parse.parse_qs(url_parts.query)
    query_params[param] = value
    # Need to do this to convert a SplitResult into a list so it can be
    # modified.
    url_parts = list(url_parts)
    # pylint:disable=redundant-keyword-arg, this is valid syntax for this lib
    url_parts[3] = urllib.parse.urlencode(query_params, doseq=True)

    # pylint:disable=too-many-function-args, This is just bogus.
    new_url = urllib.parse.urlunsplit(url_parts)
    request.uri = new_url

  return _AddQueryParam


def LogRequest(redact_token=True, redact_request_body_reason=None):
  """Logs the contents of the http request.

  Args:
    redact_token: bool, True to redact auth tokens.
    redact_request_body_reason: str, the reason why the request body must be
        redacted if --log-http is used. If None, the body is not redacted.

  Returns:
    A function that can be used in a Handler.request.
  """

  def _LogRequest(request):
    """Logs a request."""
    uri = request.uri
    method = request.method
    headers = request.headers
    body = request.body or ''

    # If set, these prevent the printing of the http body and replace it with
    # the reason the body is not being printed.
    redact_req_body_reason = None
    redact_resp_body_reason = None

    if redact_token and IsTokenUri(uri):
      redact_req_body_reason = (
          'Contains oauth token. Set log_http_redact_token property to false '
          'to print the body of this request.')
      redact_resp_body_reason = (
          'Contains oauth token. Set log_http_redact_token property to false '
          'to print the body of this response.')
    elif redact_request_body_reason is not None:
      redact_req_body_reason = redact_request_body_reason

    log.status.Print('=======================')
    log.status.Print('==== request start ====')
    log.status.Print('uri: {uri}'.format(uri=uri))
    log.status.Print('method: {method}'.format(method=method))
    log.status.Print('== headers start ==')
    for h, v in sorted(six.iteritems(headers)):
      if redact_token and h.lower() in (b'authorization',
                                        b'x-goog-iam-authorization-token'):
        v = '--- Token Redacted ---'
      log.status.Print('{0}: {1}'.format(h, v))
    log.status.Print('== headers end ==')
    log.status.Print('== body start ==')
    if redact_req_body_reason is None:
      log.status.Print(body)
    else:
      log.status.Print('Body redacted: {}'.format(redact_req_body_reason))
    log.status.Print('== body end ==')
    log.status.Print('==== request end ====')

    return {
        'start_time': time.time(),
        'redact_resp_body_reason': redact_resp_body_reason,
    }

  return _LogRequest


def LogResponse(streaming_response_body=False):
  """Logs the contents of the http response.

  Args:
    streaming_response_body: bool, True indicates that the response body will be
      a streaming body.

  Returns:
    A function that can be used in a Handler.response.
  """

  def _LogResponse(response, data):
    """Logs a response."""
    redact_resp_body_reason = data['redact_resp_body_reason']
    time_taken = time.time() - data['start_time']
    log.status.Print('---- response start ----')
    log.status.Print('status: {0}'.format(response.status_code))
    log.status.Print('-- headers start --')
    for h, v in sorted(six.iteritems(response.headers)):
      log.status.Print('{0}: {1}'.format(h, v))
    log.status.Print('-- headers end --')
    log.status.Print('-- body start --')
    if streaming_response_body:
      log.status.Print('<streaming body>')
    elif redact_resp_body_reason is None:
      log.status.Print(response.body)
    else:
      log.status.Print('Body redacted: {}'.format(redact_resp_body_reason))
    log.status.Print('-- body end --')
    log.status.Print(
        'total round trip time (request+response): {0:.3f} secs'.format(
            time_taken))
    log.status.Print('---- response end ----')
    log.status.Print('----------------------')

  return _LogResponse


def RecordStartTime():
  """Records the time at which the request was started.

  Returns:
    A function that can be used in a Handler.request.
  """

  def _RecordStartTime(request):
    """Records the start time of a request."""
    del request  # Unused.
    return {'start_time': time.time()}

  return _RecordStartTime


def ReportDuration():
  """Reports the duration of response to the metrics module.

  Returns:
    A function that can be used in a Handler.response.
  """

  def _ReportDuration(response, data):
    """Records the duration of a request."""
    del response  # Unused.
    duration = time.time() - data['start_time']
    metrics.RPCDuration(duration)

  return _ReportDuration


def GetAndCacheArchitecture(user_platform):
  """Get and cache architecture of client machine.

  For M1 Macs running x86_64 Python using Rosetta, user_platform.architecture
  (from platform.machine()) returns x86_64. We can use
  IsActuallyM1ArmArchitecture() to determine the underlying hardware; however,
  it requires a system call that might take ~5ms.
  To mitigate this, we will persist this value as an internal property with
  INSTALLATION scope.

  Args:
    user_platform: platforms.Platform.Current()

  Returns:
    client machine architecture
  """

  active_config_store = config.GetConfigStore()
  if active_config_store and active_config_store.Get('client_arch'):
    return active_config_store.Get('client_arch')

  # Determine if this is an M1 Mac Python using x86_64 emulation.
  if (user_platform.operating_system == platforms.OperatingSystem.MACOSX and
      user_platform.architecture == platforms.Architecture.x86_64 and
      platforms.Platform.IsActuallyM1ArmArchitecture()):
    arch = '{}_{}'.format(
        platforms.Architecture.x86_64, platforms.Architecture.arm)
  else:
    arch = str(user_platform.architecture)

  if active_config_store:
    active_config_store.Set('client_arch', arch)
  return arch


def MakeUserAgentString(cmd_path=None):
  """Return a user-agent string for this request.

  Contains 'gcloud' in addition to several other product IDs used for tracing in
  metrics reporting.

  Args:
    cmd_path: str representing the current command for tracing.

  Returns:
    str, User Agent string.
  """
  user_platform = platforms.Platform.Current()
  architecture = GetAndCacheArchitecture(user_platform)

  return (
      'gcloud/{version}'
      ' command/{cmd}'
      ' invocation-id/{inv_id}'
      ' environment/{environment}'
      ' environment-version/{env_version}'
      ' client-os/{os}'
      ' client-os-ver/{os_version}'
      ' client-pltf-arch/{architecture}'
      ' interactive/{is_interactive}'
      ' from-script/{from_script}'
      ' python/{py_version}'
      ' term/{term}'
      ' {ua_fragment}'
  ).format(
      version=config.CLOUD_SDK_VERSION.replace(' ', '_'),
      cmd=(cmd_path or properties.VALUES.metrics.command_name.Get()),
      inv_id=INVOCATION_ID,
      environment=properties.GetMetricsEnvironment(),
      env_version=properties.VALUES.metrics.environment_version.Get(),
      os=user_platform.operating_system,
      os_version=user_platform.operating_system.clean_version
      if user_platform.operating_system
      else None,
      architecture=architecture,
      is_interactive=console_io.IsInteractive(error=True, heuristic=True),
      py_version=platform.python_version(),
      ua_fragment=user_platform.UserAgentFragment(),
      from_script=console_io.IsRunFromShellScript(),
      term=console_attr.GetConsoleAttr().GetTermIdentifier(),
  )


def GetDefaultTimeout():
  return properties.VALUES.core.http_timeout.GetInt() or 300


def GetTraceValue():
  """Return a value to be used for the trace header."""
  # Token to be used to route service request traces.
  trace_token = properties.VALUES.core.trace_token.Get()
  # Username to which service request traces should be sent.
  trace_email = properties.VALUES.core.trace_email.Get()
  # Enable/disable server side logging of service requests.
  trace_log = properties.VALUES.core.trace_log.GetBool()

  if trace_token:
    return 'token:{0}'.format(trace_token)
  elif trace_email:
    return 'email:{0}'.format(trace_email)
  elif trace_log:
    return 'log'
  return None


def IsTokenUri(uri):
  """Determine if the given URI is for requesting an access token."""
  if uri in TOKEN_URIS:
    return True

  metadata_regexp = ('(metadata.google.internal|169.254.169.254)/'
                     'computeMetadata/.*?/instance/service-accounts/.*?/token')

  impersonate_service_account = ('iamcredentials.googleapis.com/v.*?/projects/'
                                 '-/serviceAccounts/.*?:generateAccessToken')

  if re.search(metadata_regexp, uri) is not None:
    return True

  if re.search(impersonate_service_account, uri) is not None:
    return True

  return False
