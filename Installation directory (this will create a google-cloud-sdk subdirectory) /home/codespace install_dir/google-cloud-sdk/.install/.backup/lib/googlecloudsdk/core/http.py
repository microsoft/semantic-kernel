# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""A module to get an unauthenticated http object."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import enum
import google_auth_httplib2

from googlecloudsdk.core import context_aware
from googlecloudsdk.core import http_proxy
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.util import encoding

import httplib2
import six


def Http(timeout='unset', response_encoding=None, ca_certs=None):
  """Get an httplib2.Http client that is properly configured for use by gcloud.

  This method does not add credentials to the client.  For an Http client that
  has been authenticated, use core.credentials.http.Http().

  Args:
    timeout: double, The timeout in seconds to pass to httplib2.  This is the
        socket level timeout.  If timeout is None, timeout is infinite.  If
        default argument 'unset' is given, a sensible default is selected using
        transport.GetDefaultTimeout().
    response_encoding: str, the encoding to use to decode the response.
    ca_certs: str, absolute filename of a ca_certs file that overrides the
        default. The gcloud config property for ca_certs, in turn, overrides
        this argument.

  Returns:
    An httplib2.Http client object configured with all the required settings
    for gcloud.
  """
  http_client = _CreateRawHttpClient(timeout, ca_certs)
  http_client = RequestWrapper().WrapWithDefaults(http_client,
                                                  response_encoding)
  return http_client


def HttpClient(
    timeout=None,
    proxy_info=httplib2.proxy_info_from_environment,
    ca_certs=httplib2.CA_CERTS,
    disable_ssl_certificate_validation=False):
  """Returns a httplib2.Http subclass.

  Args:
    timeout: float, Request timeout, in seconds.
    proxy_info: httplib2.ProxyInfo object or callable
    ca_certs: str, absolute filename of a ca_certs file
    disable_ssl_certificate_validation: bool, If true, disable ssl certificate
        validation.

  Returns: A httplib2.Http subclass
  """
  if properties.VALUES.proxy.use_urllib3_via_shim.GetBool():
    import httplib2shim  # pylint:disable=g-import-not-at-top
    http_class = httplib2shim.Http
  else:
    http_class = httplib2.Http

  result = http_class(
      timeout=timeout,
      proxy_info=proxy_info,
      ca_certs=ca_certs,
      disable_ssl_certificate_validation=disable_ssl_certificate_validation)

  ca_config = context_aware.Config()
  if ca_config and ca_config.config_type == context_aware.ConfigType.ON_DISK_CERTIFICATE:
    log.debug('Using client certificate %s',
              ca_config.encrypted_client_cert_path)
    result.add_certificate(ca_config.encrypted_client_cert_path,
                           ca_config.encrypted_client_cert_path, '',
                           password=ca_config.encrypted_client_cert_password)

  return result


def _CreateRawHttpClient(timeout='unset', ca_certs=None):
  """Create an HTTP client matching the appropriate gcloud properties."""
  # Compared with setting the default timeout in the function signature (i.e.
  # timeout=300), this lets you test with short default timeouts by mocking
  # GetDefaultTimeout.
  if timeout != 'unset':
    effective_timeout = timeout
  else:
    effective_timeout = transport.GetDefaultTimeout()

  no_validate = properties.VALUES.auth.disable_ssl_validation.GetBool() or False
  ca_certs_property = properties.VALUES.core.custom_ca_certs_file.Get()
  # Believe an explicitly-set ca_certs property over anything we added.
  if ca_certs_property:
    ca_certs = ca_certs_property
  if no_validate:
    ca_certs = None
  return HttpClient(timeout=effective_timeout,
                    proxy_info=http_proxy.GetHttpProxyInfo(),
                    ca_certs=ca_certs,
                    disable_ssl_certificate_validation=no_validate)


class Request(transport.Request):
  """Encapsulates parameters for making a general HTTP request.

  This implementation does additional manipulation to ensure that the request
  parameters are specified in the same way as they were specified by the
  caller. That is, if the user calls:
      request('URI', 'GET', None, {'header': '1'})

  After modifying the request, we will call request using positional
  parameters, instead of transforming the request into:
      request('URI', method='GET', body=None, headers={'header': '1'})
  """

  @classmethod
  def FromRequestArgs(cls, *args, **kwargs):
    return cls(*args, **kwargs)

  def __init__(self, *args, **kwargs):
    self._args = args
    self._kwargs = kwargs

    uri = RequestParam.URI.Get(args, kwargs)
    if not six.PY2:
      # httplib2 needs text under Python 3.
      uri = encoding.Decode(uri)
    method = RequestParam.METHOD.Get(args, kwargs)
    headers = RequestParam.HEADERS.Get(args, kwargs) or {}
    body = RequestParam.BODY.Get(args, kwargs)
    super(Request, self).__init__(uri, method, headers, body)

  def ToRequestArgs(self):
    args, kwargs = list(self._args), dict(self._kwargs)
    RequestParam.URI.Set(args, kwargs, self.uri)
    if self.method:
      RequestParam.METHOD.Set(args, kwargs, self.method)
    if self.headers:
      RequestParam.HEADERS.Set(args, kwargs, self.headers)
    if self.body:
      RequestParam.BODY.Set(args, kwargs, self.body)
    return args, kwargs


class Response(transport.Response):
  """Encapsulates responses from making a general HTTP request."""

  @classmethod
  def FromResponse(cls, response):
    resp, content = response
    headers = {h: v for h, v in six.iteritems(resp) if h != 'status'}
    return cls(resp.get('status'), headers, content)


class RequestWrapper(transport.RequestWrapper):
  """Class for wrapping httplib.Httplib2 requests."""

  request_class = Request
  response_class = Response

  def DecodeResponse(self, response, response_encoding):
    response, content = response
    content = content.decode(response_encoding)
    return response, content


class RequestParam(enum.Enum):
  """Encapsulates parameters to a request() call and how to extract them.

  http.request has the following signature:
    request(self, uri, method="GET", body=None, headers=None, ...)
  """
  URI = ('uri', 0)
  METHOD = ('method', 1)
  BODY = ('body', 2)
  HEADERS = ('headers', 3)

  def __init__(self, arg_name, index):
    self.arg_name = arg_name
    self.index = index

  def Get(self, args, kwargs):
    if len(args) > self.index:
      return args[self.index]
    if self.arg_name in kwargs:
      return kwargs[self.arg_name]
    return None

  def Set(self, args, kwargs, value):
    if len(args) > self.index:
      args[self.index] = value
    else:
      kwargs[self.arg_name] = value


def GoogleAuthRequest():
  """A Request object for google-auth library.

  Returns:
    A http request which implements google.auth.transport.Request and uses
      gcloud's http object in the core.
  """
  return google_auth_httplib2.Request(Http())
