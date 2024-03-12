# -*- coding: utf-8 -*-
# Copyright 2014 Google Inc. All Rights Reserved.
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
"""Media helper functions and classes for Google Cloud Storage JSON API."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import copy
import logging
import re
import socket
import types

import six
from six.moves import http_client
from six.moves import urllib
from six.moves import cStringIO

from apitools.base.py import exceptions as apitools_exceptions

from gslib.cloud_api import BadRequestException
from gslib.lazy_wrapper import LazyWrapper
from gslib.progress_callback import ProgressCallbackWithTimeout
from gslib.utils.constants import DEBUGLEVEL_DUMP_REQUESTS
from gslib.utils.constants import SSL_TIMEOUT_SEC
from gslib.utils.constants import TRANSFER_BUFFER_SIZE
from gslib.utils.constants import UTF8
from gslib.utils import text_util
import httplib2
from httplib2 import parse_uri

if six.PY3:
  long = int

# A regex for matching any series of decimal digits.
DECIMAL_REGEX = LazyWrapper(lambda: (re.compile(r'\d+')))


class BytesTransferredContainer(object):
  """Container class for passing number of bytes transferred to lower layers.

  For resumed transfers or connection rebuilds in the middle of a transfer, we
  need to rebuild the connection class with how much we've transferred so far.
  For uploads, we don't know the total number of bytes uploaded until we've
  queried the server, but we need to create the connection class to pass to
  httplib2 before we can query the server. This container object allows us to
  pass a reference into Upload/DownloadCallbackConnection.
  """

  def __init__(self):
    self.__bytes_transferred = 0

  @property
  def bytes_transferred(self):
    return self.__bytes_transferred

  @bytes_transferred.setter
  def bytes_transferred(self, value):
    self.__bytes_transferred = value


class UploadCallbackConnectionClassFactory(object):
  """Creates a class that can override an httplib2 connection.

  This is used to provide progress callbacks and disable dumping the upload
  payload during debug statements. It can later be used to provide on-the-fly
  hash digestion during upload.
  """

  def __init__(self,
               bytes_uploaded_container,
               buffer_size=TRANSFER_BUFFER_SIZE,
               total_size=0,
               progress_callback=None,
               logger=None,
               debug=0):
    self.bytes_uploaded_container = bytes_uploaded_container
    self.buffer_size = buffer_size
    self.total_size = total_size
    self.progress_callback = progress_callback
    self.logger = logger
    self.debug = debug

  def GetConnectionClass(self):
    """Returns a connection class that overrides send."""
    outer_bytes_uploaded_container = self.bytes_uploaded_container
    outer_buffer_size = self.buffer_size
    outer_total_size = self.total_size
    outer_progress_callback = self.progress_callback
    outer_logger = self.logger
    outer_debug = self.debug

    class UploadCallbackConnection(httplib2.HTTPSConnectionWithTimeout):
      """Connection class override for uploads."""
      bytes_uploaded_container = outer_bytes_uploaded_container
      # After we instantiate this class, apitools will check with the server
      # to find out how many bytes remain for a resumable upload.  This allows
      # us to update our progress once based on that number.
      processed_initial_bytes = False
      GCS_JSON_BUFFER_SIZE = outer_buffer_size
      callback_processor = None
      size = outer_total_size
      header_encoding = ''
      header_length = None
      header_range = None
      size_modifier = 1.0

      def __init__(self, *args, **kwargs):
        kwargs['timeout'] = SSL_TIMEOUT_SEC
        httplib2.HTTPSConnectionWithTimeout.__init__(self, *args, **kwargs)

      # Override httplib.HTTPConnection._send_output for debug logging.
      # Because the distinction between headers and message body occurs
      # only in this httplib function, we can only differentiate them here.
      def _send_output(self, message_body=None, encode_chunked=False):
        r"""Send the currently buffered request and clear the buffer.

        Appends an extra \r\n to the buffer.

        Args:
          message_body: if specified, this is appended to the request.
        """
        # TODO: Presently, apitools will set http2lib2.debuglevel to 0
        # (no prints) or 4 (dump upload payload, httplib prints to stdout).
        # Refactor to allow our media-handling functions to handle
        # debuglevel == 4 and print messages to stderr.
        self._buffer.extend((b'', b''))
        if six.PY2:
          items = self._buffer
        else:
          items = []
          for item in self._buffer:
            if isinstance(item, bytes):
              items.append(item)
            else:
              items.append(item.encode(UTF8))
        msg = b'\r\n'.join(items)
        num_metadata_bytes = len(msg)
        if outer_debug == DEBUGLEVEL_DUMP_REQUESTS and outer_logger:
          outer_logger.debug('send: %s' % msg)
        del self._buffer[:]
        # If msg and message_body are sent in a single send() call,
        # it will avoid performance problems caused by the interaction
        # between delayed ack and the Nagle algorithm.
        if isinstance(message_body, str):
          msg += message_body
          message_body = None
        self.send(msg, num_metadata_bytes=num_metadata_bytes)
        if message_body is not None:
          # message_body was not a string (i.e. it is a file) and
          # we must run the risk of Nagle
          self.send(message_body)

      def putheader(self, header, *values):
        """Overrides HTTPConnection.putheader.

        Send a request header line to the server. For example:
        h.putheader('Accept', 'text/html').

        This override records the content encoding, length, and range of the
        payload. For uploads where the content-range difference does not match
        the content-length, progress printing will under-report progress. These
        headers are used to calculate a multiplier to correct the progress.

        For example: the content-length for gzip transport encoded data
        represents the compressed size of the data while the content-range
        difference represents the uncompressed size. Dividing the
        content-range difference by the content-length gives the ratio to
        multiply the progress by to correctly report the relative progress.

        Args:
          header: The header.
          *values: A set of values for the header.
        """
        if header == 'content-encoding':
          value = ''.join([str(v) for v in values])
          self.header_encoding = value
          if outer_debug == DEBUGLEVEL_DUMP_REQUESTS and outer_logger:
            outer_logger.debug(
                'send: Using gzip transport encoding for the request.')
        elif header == 'content-length':
          try:
            value = int(''.join([str(v) for v in values]))
            self.header_length = value
          except ValueError:
            pass
        elif header == 'content-range':
          try:
            # There are 3 valid header formats:
            #  '*/%d', '%d-%d/*', and '%d-%d/%d'
            value = ''.join([str(v) for v in values])
            ranges = DECIMAL_REGEX().findall(value)
            # If there are 2 or more range values, they will always
            # correspond to the start and end ranges in the header.
            if len(ranges) > 1:
              # Subtract the end position from the start position.
              self.header_range = (int(ranges[1]) - int(ranges[0])) + 1
          except ValueError:
            pass
        # If the content header is gzip, and a range and length are set,
        # update the modifier.
        if (self.header_encoding == 'gzip' and self.header_length and
            self.header_range):
          # Update the modifier
          self.size_modifier = self.header_range / float(self.header_length)
          # Reset the headers
          self.header_encoding = ''
          self.header_length = None
          self.header_range = None
          # Log debug information to catch in tests.
          if outer_debug == DEBUGLEVEL_DUMP_REQUESTS and outer_logger:
            outer_logger.debug('send: Setting progress modifier to %s.' %
                               (self.size_modifier))
        # Propagate header values.
        http_client.HTTPSConnection.putheader(self, header, *values)

      def send(self, data, num_metadata_bytes=0):
        """Overrides HTTPConnection.send.

        Args:
          data: string or file-like object (implements read()) of data to send.
          num_metadata_bytes: number of bytes that consist of metadata
              (headers, etc.) not representing the data being uploaded.
        """
        if not self.processed_initial_bytes:
          self.processed_initial_bytes = True
          if outer_progress_callback:
            self.callback_processor = ProgressCallbackWithTimeout(
                outer_total_size, outer_progress_callback)
            self.callback_processor.Progress(
                self.bytes_uploaded_container.bytes_transferred)
        # httplib.HTTPConnection.send accepts either a string or a file-like
        # object (anything that implements read()).
        if isinstance(data, six.text_type):
          full_buffer = cStringIO(data)
        elif isinstance(data, six.binary_type):
          full_buffer = six.BytesIO(data)
        else:
          full_buffer = data
        partial_buffer = full_buffer.read(self.GCS_JSON_BUFFER_SIZE)
        while partial_buffer:
          if six.PY2:
            httplib2.HTTPSConnectionWithTimeout.send(self, partial_buffer)
          else:
            if isinstance(partial_buffer, bytes):
              httplib2.HTTPSConnectionWithTimeout.send(self, partial_buffer)
            else:
              httplib2.HTTPSConnectionWithTimeout.send(
                  self, partial_buffer.encode(UTF8))
          sent_data_bytes = len(partial_buffer)
          if num_metadata_bytes:
            if num_metadata_bytes <= sent_data_bytes:
              sent_data_bytes -= num_metadata_bytes
              num_metadata_bytes = 0
            else:
              num_metadata_bytes -= sent_data_bytes
              sent_data_bytes = 0
          if self.callback_processor:
            # Modify the sent data bytes by the size modifier. These are
            # stored as floats, so the result should be floored.
            sent_data_bytes = int(sent_data_bytes * self.size_modifier)
            # TODO: We can't differentiate the multipart upload
            # metadata in the request body from the actual upload bytes, so we
            # will actually report slightly more bytes than desired to the
            # callback handler. Get the number of multipart upload metadata
            # bytes from apitools and subtract from sent_data_bytes.
            self.callback_processor.Progress(sent_data_bytes)
          partial_buffer = full_buffer.read(self.GCS_JSON_BUFFER_SIZE)

    return UploadCallbackConnection


def WrapUploadHttpRequest(upload_http):
  """Wraps upload_http so we only use our custom connection_type on PUTs.

  POSTs are used to refresh oauth tokens, and we don't want to process the
  data sent in those requests.

  Args:
    upload_http: httplib2.Http instance to wrap
  """
  request_orig = upload_http.request

  def NewRequest(uri,
                 method='GET',
                 body=None,
                 headers=None,
                 redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                 connection_type=None):
    if method == 'PUT' or method == 'POST':
      override_connection_type = connection_type
    else:
      override_connection_type = None
    return request_orig(uri,
                        method=method,
                        body=body,
                        headers=headers,
                        redirections=redirections,
                        connection_type=override_connection_type)

  # Replace the request method with our own closure.
  upload_http.request = NewRequest


class DownloadCallbackConnectionClassFactory(object):
  """Creates a class that can override an httplib2 connection.

  This is used to provide progress callbacks, disable dumping the download
  payload during debug statements, and provide on-the-fly hash digestion during
  download. On-the-fly digestion is particularly important because httplib2
  will decompress gzipped content on-the-fly, thus this class provides our
  only opportunity to calculate the correct hash for an object that has a
  gzip hash in the cloud.
  """

  def __init__(self,
               bytes_downloaded_container,
               buffer_size=TRANSFER_BUFFER_SIZE,
               total_size=0,
               progress_callback=None,
               digesters=None):
    self.buffer_size = buffer_size
    self.total_size = total_size
    self.progress_callback = progress_callback
    self.digesters = digesters
    self.bytes_downloaded_container = bytes_downloaded_container

  def GetConnectionClass(self):
    """Returns a connection class that overrides getresponse."""

    class DownloadCallbackConnection(httplib2.HTTPSConnectionWithTimeout):
      """Connection class override for downloads."""
      outer_total_size = self.total_size
      outer_digesters = self.digesters
      outer_progress_callback = self.progress_callback
      outer_bytes_downloaded_container = self.bytes_downloaded_container
      processed_initial_bytes = False
      callback_processor = None

      def __init__(self, *args, **kwargs):
        kwargs['timeout'] = SSL_TIMEOUT_SEC
        httplib2.HTTPSConnectionWithTimeout.__init__(self, *args, **kwargs)

      def getresponse(self, buffering=False):
        """Wraps an HTTPResponse to perform callbacks and hashing.

        In this function, self is a DownloadCallbackConnection.

        Args:
          buffering: Unused. This function uses a local buffer.

        Returns:
          HTTPResponse object with wrapped read function.
        """
        orig_response = http_client.HTTPConnection.getresponse(self)
        if orig_response.status not in (http_client.OK,
                                        http_client.PARTIAL_CONTENT):
          return orig_response
        orig_read_func = orig_response.read

        def read(amt=None):  # pylint: disable=invalid-name
          """Overrides HTTPConnection.getresponse.read.

          This function only supports reads of TRANSFER_BUFFER_SIZE or smaller.

          Args:
            amt: Integer n where 0 < n <= TRANSFER_BUFFER_SIZE. This is a
                 keyword argument to match the read function it overrides,
                 but it is required.

          Returns:
            Data read from HTTPConnection.
          """
          if not amt or amt > TRANSFER_BUFFER_SIZE:
            raise BadRequestException(
                'Invalid HTTP read size %s during download, expected %s.' %
                (amt, TRANSFER_BUFFER_SIZE))
          else:
            amt = amt or TRANSFER_BUFFER_SIZE

          if not self.processed_initial_bytes:
            self.processed_initial_bytes = True
            if self.outer_progress_callback:
              self.callback_processor = ProgressCallbackWithTimeout(
                  self.outer_total_size, self.outer_progress_callback)
              self.callback_processor.Progress(
                  self.outer_bytes_downloaded_container.bytes_transferred)

          data = orig_read_func(amt)
          read_length = len(data)
          if self.callback_processor:
            self.callback_processor.Progress(read_length)
          if self.outer_digesters:
            for alg in self.outer_digesters:
              self.outer_digesters[alg].update(data)
          return data

        orig_response.read = read

        return orig_response

    return DownloadCallbackConnection


def WrapDownloadHttpRequest(download_http):
  """Overrides download request functions for an httplib2.Http object.

  Args:
    download_http: httplib2.Http.object to wrap / override.

  Returns:
    Wrapped / overridden httplib2.Http object.
  """

  # httplib2 has a bug (https://github.com/httplib2/httplib2/issues/75) where
  # custom connection_type is not respected after redirects.  This function is
  # copied from httplib2 and overrides the request function so that the
  # connection_type is properly passed through (everything here should be
  # identical to the _request method in httplib2, with the exception of the line
  # below marked by the "BUGFIX" comment).
  # pylint: disable=protected-access,g-inconsistent-quotes,unused-variable
  # pylint: disable=g-equals-none,g-doc-return-or-yield
  # pylint: disable=g-short-docstring-punctuation,g-doc-args
  # pylint: disable=too-many-statements
  # yapf: disable
  def OverrideRequest(self, conn, host, absolute_uri, request_uri, method,
                      body, headers, redirections, cachekey):
    """Do the actual request using the connection object.
    Also follow one level of redirects if necessary.
    """

    auths = ([(auth.depth(request_uri), auth) for auth in self.authorizations
              if auth.inscope(host, request_uri)])
    auth = auths and sorted(auths)[0][1] or None
    if auth:
      auth.request(method, request_uri, headers, body)

    (response, content) = self._conn_request(conn, request_uri, method, body,
                                             headers)

    if auth:
      if auth.response(response, body):
        auth.request(method, request_uri, headers, body)
        (response, content) = self._conn_request(conn, request_uri, method,
                                                 body, headers)
        response._stale_digest = 1

    if response.status == 401:
      for authorization in self._auth_from_challenge(
          host, request_uri, headers, response, content):
        authorization.request(method, request_uri, headers, body)
        (response, content) = self._conn_request(conn, request_uri, method,
                                                 body, headers)
        if response.status != 401:
          self.authorizations.append(authorization)
          authorization.response(response, body)
          break

    if (self.follow_all_redirects or (method in ["GET", "HEAD"])
        or response.status == 303):
      if self.follow_redirects and response.status in [300, 301, 302,
                                                       303, 307]:
        # Pick out the location header and basically start from the beginning
        # remembering first to strip the ETag header and decrement our 'depth'
        if redirections:
          if 'location' not in response and response.status != 300:
            raise httplib2.RedirectMissingLocation(
                "Redirected but the response is missing a Location: header.",
                response, content)
          # Fix-up relative redirects (which violate an RFC 2616 MUST)
          if 'location' in response:
            location = response['location']
            (scheme, authority, path, query, fragment) = parse_uri(location)
            if authority is None:
              response['location'] = urllib.parse.urljoin(absolute_uri, location)
          if response.status == 301 and method in ["GET", "HEAD"]:
            response['-x-permanent-redirect-url'] = response['location']
            if 'content-location' not in response:
              response['content-location'] = absolute_uri
            httplib2._updateCache(headers, response, content, self.cache,
                                  cachekey)
          if 'if-none-match' in headers:
            del headers['if-none-match']
          if 'if-modified-since' in headers:
            del headers['if-modified-since']
          if ('authorization' in headers and
              not self.forward_authorization_headers):
            del headers['authorization']
          if 'location' in response:
            location = response['location']
            old_response = copy.deepcopy(response)
            if 'content-location' not in old_response:
              old_response['content-location'] = absolute_uri
            redirect_method = method
            if response.status in [302, 303]:
              redirect_method = "GET"
              body = None
            (response, content) = self.request(
                location, redirect_method, body=body, headers=headers,
                redirections=redirections-1,
                # BUGFIX (see comments at the top of this function):
                connection_type=conn.__class__)
            response.previous = old_response
        else:
          raise httplib2.RedirectLimit(
              "Redirected more times than redirection_limit allows.",
              response, content)
      elif response.status in [200, 203] and method in ["GET", "HEAD"]:
        # Don't cache 206's since we aren't going to handle byte range
        # requests
        if 'content-location' in response:
          response['content-location'] = absolute_uri
        httplib2._updateCache(headers, response, content, self.cache,
                              cachekey)

    return (response, content)

  # Wrap download_http so we do not use our custom connection_type
  # on POSTS, which are used to refresh oauth tokens. We don't want to
  # process the data received in those requests.
  request_orig = download_http.request
  def NewRequest(uri, method='GET', body=None, headers=None,
                 redirections=httplib2.DEFAULT_MAX_REDIRECTS,
                 connection_type=None):
    if method == 'POST':
      return request_orig(uri, method=method, body=body,
                          headers=headers, redirections=redirections,
                          connection_type=None)
    else:
      return request_orig(uri, method=method, body=body,
                          headers=headers, redirections=redirections,
                          connection_type=connection_type)

  # Replace the request methods with our own closures.
  download_http._request = types.MethodType(OverrideRequest, download_http)
  download_http.request = NewRequest

  return download_http


class HttpWithNoRetries(httplib2.Http):
  """httplib2.Http variant that does not retry.

  httplib2 automatically retries requests according to httplib2.RETRIES, but
  in certain cases httplib2 ignores the RETRIES value and forces a retry.
  Because httplib2 does not handle the case where the underlying request body
  is a stream, a retry may cause a non-idempotent write as the stream is
  partially consumed and not reset before the retry occurs.

  Here we override _conn_request to disable retries unequivocally, so that
  uploads may be retried at higher layers that properly handle stream request
  bodies.
  """

  def _conn_request(self, conn, request_uri, method, body, headers):  # pylint: disable=too-many-statements

    try:
      if hasattr(conn, 'sock') and conn.sock is None:
        conn.connect()
      conn.request(method, request_uri, body, headers)
    except socket.timeout:
      raise
    except socket.gaierror:
      conn.close()
      raise httplib2.ServerNotFoundError('Unable to find the server at %s' %
                                         conn.host)
    except httplib2.ssl.SSLError:
      conn.close()
      raise
    except socket.error as e:
      err = 0
      if hasattr(e, 'args'):
        err = getattr(e, 'args')[0]
      else:
        err = e.errno
      if err == httplib2.errno.ECONNREFUSED:  # Connection refused
        raise
    except http_client.HTTPException:
      conn.close()
      raise
    try:
      response = conn.getresponse()
    except (socket.error, http_client.HTTPException):
      conn.close()
      raise
    else:
      content = ''
      if method == 'HEAD':
        conn.close()
      else:
        content = response.read()
      response = httplib2.Response(response)
      if method != 'HEAD':
        # pylint: disable=protected-access
        content = httplib2._decompressContent(response, content)
    return (response, content)


class HttpWithDownloadStream(httplib2.Http):
  """httplib2.Http variant that only pushes bytes through a stream.

  httplib2 handles media by storing entire chunks of responses in memory, which
  is undesirable particularly when multiple instances are used during
  multi-threaded/multi-process copy. This class copies and then overrides some
  httplib2 functions to use a streaming copy approach that uses small memory
  buffers.

  Also disables httplib2 retries (for reasons stated in the HttpWithNoRetries
  class doc).
  """

  def __init__(self, *args, **kwds):
    self._stream = None
    self._logger = logging.getLogger()
    super(HttpWithDownloadStream, self).__init__(*args, **kwds)

  @property
  def stream(self):
    return self._stream

  @stream.setter
  def stream(self, value):
    self._stream = value

  # pylint: disable=too-many-statements
  def _conn_request(self, conn, request_uri, method, body, headers):
    try:
      if hasattr(conn, 'sock') and conn.sock is None:
        conn.connect()
      conn.request(method, request_uri, body, headers)
    except socket.timeout:
      raise
    except socket.gaierror:
      conn.close()
      raise httplib2.ServerNotFoundError('Unable to find the server at %s' %
                                         conn.host)
    except httplib2.ssl.SSLError:
      conn.close()
      raise
    except socket.error as e:
      err = 0
      if hasattr(e, 'args'):
        err = getattr(e, 'args')[0]
      else:
        err = e.errno
      if err == httplib2.errno.ECONNREFUSED:  # Connection refused
        raise
    except http_client.HTTPException:
      # Just because the server closed the connection doesn't apparently mean
      # that the server didn't send a response.
      conn.close()
      raise
    try:
      response = conn.getresponse()
    except (socket.error, http_client.HTTPException) as e:
      conn.close()
      raise
    else:
      content = ''
      if method == 'HEAD':
        conn.close()
        response = httplib2.Response(response)
      elif method == 'GET' and response.status in (http_client.OK,
                                                   http_client.PARTIAL_CONTENT):
        content_length = None
        if hasattr(response, 'msg'):
          content_length = response.getheader('content-length')
        http_stream = response
        bytes_read = 0
        while True:
          new_data = http_stream.read(TRANSFER_BUFFER_SIZE)
          if new_data:
            if self.stream is None:
              raise apitools_exceptions.InvalidUserInputError(
                  'Cannot exercise HttpWithDownloadStream with no stream')
            text_util.write_to_fd(self.stream, new_data)
            bytes_read += len(new_data)
          else:
            break

        if (content_length is not None and
            long(bytes_read) != long(content_length)):
          # The input stream terminated before we were able to read the
          # entire contents, possibly due to a network condition. Set
          # content-length to indicate how many bytes we actually read.
          self._logger.log(
              logging.DEBUG, 'Only got %s bytes out of content-length %s '
              'for request URI %s. Resetting content-length to match '
              'bytes read.', bytes_read, content_length, request_uri)
          # Failing to delete existing headers before setting new values results
          # in the header being set twice, see https://docs.python.org/3/library/email.compat32-message.html#email.message.Message.__setitem__.
          # This trips apitools up when executing a retry, so the line below is
          # essential:
          del response.msg['content-length']
          response.msg['content-length'] = str(bytes_read)
        response = httplib2.Response(response)
      else:
        # We fall back to the current httplib2 behavior if we're
        # not processing download bytes, e.g., it's a redirect, an
        # oauth2client POST to refresh an access token, or any HTTP
        # status code that doesn't include object content.
        content = response.read()
        response = httplib2.Response(response)
        # pylint: disable=protected-access
        content = httplib2._decompressContent(response, content)
    return (response, content)

  # pylint: enable=too-many-statements
