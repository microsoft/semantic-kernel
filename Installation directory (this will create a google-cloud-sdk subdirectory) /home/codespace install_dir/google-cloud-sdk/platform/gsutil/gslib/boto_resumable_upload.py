# -*- coding: utf-8 -*-
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
"""Boto translation layer for resumable uploads.

See https://cloud.google.com/storage/docs/resumable-uploads-xml
for details.

Resumable uploads will retry interrupted uploads, resuming at the byte
count completed by the last upload attempt. If too many retries happen with
no progress (per configurable num_retries param), the upload will be
aborted in the current process.

Unlike the boto implementation of resumable upload handler, this class does
not directly interact with tracker files.

Originally Google wrote and contributed this code to the boto project,
then copied that code back into gsutil on the release of gsutil 4.0 which
supports both boto and non-boto codepaths for resumable uploads.  Any bug
fixes made to this file should also be integrated to resumable_upload_handler.py
in boto, where applicable.

TODO: gsutil-beta: Add a similar comment to the boto code.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

import errno
import random
import re
import socket
import time

import six
from six.moves import urllib
from six.moves import http_client
from boto import config
from boto import UserAgent
from boto.connection import AWSAuthConnection
from boto.exception import ResumableTransferDisposition
from boto.exception import ResumableUploadException

from gslib.exception import InvalidUrlError
from gslib.utils.boto_util import GetMaxRetryDelay
from gslib.utils.boto_util import GetNumRetries
from gslib.utils.constants import XML_PROGRESS_CALLBACKS
from gslib.utils.constants import UTF8

if six.PY3:
  long = int


class BotoResumableUpload(object):
  """Upload helper class for resumable uploads via boto."""

  BUFFER_SIZE = 8192
  RETRYABLE_EXCEPTIONS = (http_client.HTTPException, IOError, socket.error,
                          socket.gaierror)

  # (start, end) response indicating service has nothing (upload protocol uses
  # inclusive numbering).
  SERVICE_HAS_NOTHING = (0, -1)

  def __init__(self,
               tracker_callback,
               logger,
               resume_url=None,
               num_retries=None):
    """Constructor. Instantiate once for each uploaded file.

    Args:
      tracker_callback: Callback function that takes a string argument.  Used
                        by caller to track this upload across upload
                        interruption.
      logger: logging.logger instance to use for debug messages.
      resume_url: If present, attempt to resume the upload at this URL.
      num_retries: Number of times to retry the upload making no progress.
                   This count resets every time we make progress, so the upload
                   can span many more than this number of retries.
    """
    if resume_url:
      self._SetUploadUrl(resume_url)
    else:
      self.upload_url = None
    self.num_retries = num_retries
    self.service_has_bytes = 0  # Byte count at last service check.
    # Save upload_start_point in instance state so caller can find how
    # much was transferred by this ResumableUploadHandler (across retries).
    self.upload_start_point = None
    self.tracker_callback = tracker_callback
    self.logger = logger

  def _SetUploadUrl(self, url):
    """Saves URL and resets upload state.

    Called when we start a new resumable upload or get a new tracker
    URL for the upload.

    Args:
      url: URL string for the upload.

    Raises InvalidUrlError if URL is syntactically invalid.
    """
    parse_result = urllib.parse.urlparse(url)
    if (parse_result.scheme.lower() not in ['http', 'https'] or
        not parse_result.netloc):
      raise InvalidUrlError('Invalid upload URL (%s)' % url)
    self.upload_url = url
    self.upload_url_host = (config.get('Credentials', 'gs_host', None) or
                            parse_result.netloc)
    self.upload_url_path = '%s?%s' % (parse_result.path, parse_result.query)
    self.service_has_bytes = 0

  def _BuildContentRangeHeader(self, range_spec='*', length_spec='*'):
    return 'bytes %s/%s' % (range_spec, length_spec)

  def _QueryServiceState(self, conn, file_length):
    """Queries service to find out state of given upload.

    Note that this method really just makes special case use of the
    fact that the upload service always returns the current start/end
    state whenever a PUT doesn't complete.

    Args:
      conn: HTTPConnection to use for the query.
      file_length: Total length of the file.

    Returns:
      HTTP response from sending request.

    Raises:
      ResumableUploadException if problem querying service.
    """
    # Send an empty PUT so that service replies with this resumable
    # transfer's state.
    put_headers = {
        'Content-Range': (self._BuildContentRangeHeader('*', file_length)),
        'Content-Length': '0'
    }
    return AWSAuthConnection.make_request(conn,
                                          'PUT',
                                          path=self.upload_url_path,
                                          auth_path=self.upload_url_path,
                                          headers=put_headers,
                                          host=self.upload_url_host)

  def _QueryServicePos(self, conn, file_length):
    """Queries service to find out what bytes it currently has.

    Args:
      conn: HTTPConnection to use for the query.
      file_length: Total length of the file.

    Returns:
      (service_start, service_end), where the values are inclusive.
      For example, (0, 2) would mean that the service has bytes 0, 1, *and* 2.

    Raises:
      ResumableUploadException if problem querying service.
    """
    resp = self._QueryServiceState(conn, file_length)
    if resp.status == 200:
      # To handle the boundary condition where the service has the complete
      # file, we return (service_start, file_length-1). That way the
      # calling code can always simply read up through service_end. (If we
      # didn't handle this boundary condition here, the caller would have
      # to check whether service_end == file_length and read one fewer byte
      # in that case.)
      return (0, file_length - 1)  # Completed upload.
    if resp.status != 308:
      # This means the service didn't have any state for the given
      # upload ID, which can happen (for example) if the caller saved
      # the upload URL to a file and then tried to restart the transfer
      # after that upload ID has gone stale. In that case we need to
      # start a new transfer (and the caller will then save the new
      # upload URL to the tracker file).
      raise ResumableUploadException(
          'Got non-308 response (%s) from service state query' % resp.status,
          ResumableTransferDisposition.START_OVER)
    got_valid_response = False
    range_spec = resp.getheader('range')
    if range_spec:
      # Parse 'bytes=<from>-<to>' range_spec.
      m = re.search(r'bytes=(\d+)-(\d+)', range_spec)
      if m:
        service_start = long(m.group(1))
        service_end = long(m.group(2))
        got_valid_response = True
    else:
      # No Range header, which means the service does not yet have
      # any bytes. Note that the Range header uses inclusive 'from'
      # and 'to' values. Since Range 0-0 would mean that the service
      # has byte 0, omitting the Range header is used to indicate that
      # the service doesn't have any bytes.
      return self.SERVICE_HAS_NOTHING
    if not got_valid_response:
      raise ResumableUploadException(
          'Couldn\'t parse upload service state query response (%s)' %
          str(resp.getheaders()), ResumableTransferDisposition.START_OVER)
    if conn.debug >= 1:
      self.logger.debug('Service has: Range: %d - %d.', service_start,
                        service_end)
    return (service_start, service_end)

  def _StartNewResumableUpload(self, key, headers=None):
    """Starts a new resumable upload.

    Args:
      key: Boto Key representing the object to upload.
      headers: Headers to use in the upload requests.

    Raises:
      ResumableUploadException if any errors occur.
    """
    conn = key.bucket.connection
    if conn.debug >= 1:
      self.logger.debug('Starting new resumable upload.')
    self.service_has_bytes = 0

    # Start a new resumable upload by sending a POST request with an
    # empty body and the "X-Goog-Resumable: start" header. Include any
    # caller-provided headers (e.g., Content-Type) EXCEPT Content-Length
    # (and raise an exception if they tried to pass one, since it's
    # a semantic error to specify it at this point, and if we were to
    # include one now it would cause the service to expect that many
    # bytes; the POST doesn't include the actual file bytes  We set
    # the Content-Length in the subsequent PUT, based on the uploaded
    # file size.
    post_headers = {}
    for k in headers:
      if k.lower() == 'content-length':
        raise ResumableUploadException(
            'Attempt to specify Content-Length header (disallowed)',
            ResumableTransferDisposition.ABORT)
      post_headers[k] = headers[k]
    post_headers[conn.provider.resumable_upload_header] = 'start'

    resp = conn.make_request('POST', key.bucket.name, key.name, post_headers)
    # Get upload URL from response 'Location' header.
    body = resp.read()

    # Check for various status conditions.
    if resp.status in [429, 500, 503]:
      # Retry after a delay.
      raise ResumableUploadException(
          'Got status %d from attempt to start resumable upload. '
          'Will wait/retry' % resp.status,
          ResumableTransferDisposition.WAIT_BEFORE_RETRY)
    elif resp.status != 200 and resp.status != 201:
      raise ResumableUploadException(
          'Got status %d from attempt to start resumable upload. '
          'Aborting' % resp.status, ResumableTransferDisposition.ABORT)

    # Else we got 200 or 201 response code, indicating the resumable
    # upload was created.
    upload_url = resp.getheader('Location')
    if not upload_url:
      raise ResumableUploadException(
          'No resumable upload URL found in resumable initiation '
          'POST response (%s)' % body,
          ResumableTransferDisposition.WAIT_BEFORE_RETRY)
    self._SetUploadUrl(upload_url)
    self.tracker_callback(upload_url)

  def _UploadFileBytes(self, conn, http_conn, fp, file_length,
                       total_bytes_uploaded, cb, num_cb, headers):
    """Attempts to upload file bytes.

    Makes a single attempt using an existing resumable upload connection.

    Args:
      conn: HTTPConnection from the boto Key.
      http_conn: Separate HTTPConnection for the transfer.
      fp: File pointer containing bytes to upload.
      file_length: Total length of the file.
      total_bytes_uploaded: The total number of bytes uploaded.
      cb: Progress callback function that takes (progress, total_size).
      num_cb: Granularity of the callback (maximum number of times the
              callback will be called during the file transfer). If negative,
              perform callback with each buffer read.
      headers: Headers to be used in the upload requests.

    Returns:
      (etag, generation, metageneration) from service upon success.

    Raises:
      ResumableUploadException if any problems occur.
    """
    buf = fp.read(self.BUFFER_SIZE)
    if cb:
      # The cb_count represents the number of full buffers to send between
      # cb executions.
      if num_cb > 2:
        cb_count = file_length / self.BUFFER_SIZE / (num_cb - 2)
      elif num_cb < 0:
        cb_count = -1
      else:
        cb_count = 0
      i = 0
      cb(total_bytes_uploaded, file_length)

    # Build resumable upload headers for the transfer. Don't send a
    # Content-Range header if the file is 0 bytes long, because the
    # resumable upload protocol uses an *inclusive* end-range (so, sending
    # 'bytes 0-0/1' would actually mean you're sending a 1-byte file).
    put_headers = headers.copy() if headers else {}
    if file_length:
      if total_bytes_uploaded == file_length:
        range_header = self._BuildContentRangeHeader('*', file_length)
      else:
        range_header = self._BuildContentRangeHeader(
            '%d-%d' % (total_bytes_uploaded, file_length - 1), file_length)
      put_headers['Content-Range'] = range_header
    # Set Content-Length to the total bytes we'll send with this PUT.
    put_headers['Content-Length'] = str(file_length - total_bytes_uploaded)
    http_request = AWSAuthConnection.build_base_http_request(
        conn,
        'PUT',
        path=self.upload_url_path,
        auth_path=None,
        headers=put_headers,
        host=self.upload_url_host)
    http_conn.putrequest('PUT', http_request.path)
    for k in put_headers:
      http_conn.putheader(k, put_headers[k])
    http_conn.endheaders()

    # Turn off debug on http connection so upload content isn't included
    # in debug stream.
    http_conn.set_debuglevel(0)
    while buf:
      # Some code is duplicated here, but separating the PY2 and PY3 paths makes
      # this easier to remove PY2 blocks when we move to PY3 only.
      if six.PY2:
        http_conn.send(buf)
        total_bytes_uploaded += len(buf)
      else:
        if isinstance(buf, bytes):
          http_conn.send(buf)
          total_bytes_uploaded += len(buf)
        else:
          # Probably a unicode/str object, try encoding.
          buf_bytes = buf.encode(UTF8)
          http_conn.send(buf_bytes)
          total_bytes_uploaded += len(buf_bytes)

      if cb:
        i += 1
        if i == cb_count or cb_count == -1:
          cb(total_bytes_uploaded, file_length)
          i = 0

      buf = fp.read(self.BUFFER_SIZE)

    # Restore http connection debug level.
    http_conn.set_debuglevel(conn.debug)

    if cb:
      cb(total_bytes_uploaded, file_length)
    if total_bytes_uploaded != file_length:
      # Abort (and delete the tracker file) so if the user retries
      # they'll start a new resumable upload rather than potentially
      # attempting to pick back up later where we left off.
      raise ResumableUploadException(
          'File changed during upload: EOF at %d bytes of %d byte file.' %
          (total_bytes_uploaded, file_length),
          ResumableTransferDisposition.ABORT)

    resp = http_conn.getresponse()
    if resp.status == 200:
      # Success.
      return (resp.getheader('etag'), resp.getheader('x-goog-generation'),
              resp.getheader('x-goog-metageneration'))
    # Retry timeout (408) and status 429, 500 and 503 errors after a delay.
    elif resp.status in [408, 429, 500, 503]:
      disposition = ResumableTransferDisposition.WAIT_BEFORE_RETRY
    else:
      # Catch all for any other error codes.
      disposition = ResumableTransferDisposition.ABORT
    raise ResumableUploadException(
        'Got response code %d while attempting '
        'upload (%s)' % (resp.status, resp.reason), disposition)

  def _AttemptResumableUpload(self, key, fp, file_length, headers, cb, num_cb):
    """Attempts a resumable upload.

    Args:
      key: Boto key representing object to upload.
      fp: File pointer containing upload bytes.
      file_length: Total length of the upload.
      headers: Headers to be used in upload requests.
      cb: Progress callback function that takes (progress, total_size).
      num_cb: Granularity of the callback (maximum number of times the
              callback will be called during the file transfer). If negative,
              perform callback with each buffer read.

    Returns:
      (etag, generation, metageneration) from service upon success.

    Raises:
      ResumableUploadException if any problems occur.
    """
    (service_start, service_end) = self.SERVICE_HAS_NOTHING
    conn = key.bucket.connection
    if self.upload_url:
      # Try to resume existing resumable upload.
      try:
        (service_start,
         service_end) = (self._QueryServicePos(conn, file_length))
        self.service_has_bytes = service_start
        if conn.debug >= 1:
          self.logger.debug('Resuming transfer.')
      except ResumableUploadException as e:
        if conn.debug >= 1:
          self.logger.debug('Unable to resume transfer (%s).', e.message)
        self._StartNewResumableUpload(key, headers)
    else:
      self._StartNewResumableUpload(key, headers)

    # upload_start_point allows the code that instantiated the
    # ResumableUploadHandler to find out the point from which it started
    # uploading (e.g., so it can correctly compute throughput).
    if self.upload_start_point is None:
      self.upload_start_point = service_end

    total_bytes_uploaded = service_end + 1

    # Start reading from the file based upon the number of bytes that the
    # server has so far.
    if total_bytes_uploaded < file_length:
      fp.seek(total_bytes_uploaded)

    conn = key.bucket.connection

    # Get a new HTTP connection (vs conn.get_http_connection(), which reuses
    # pool connections) because httplib requires a new HTTP connection per
    # transaction. (Without this, calling http_conn.getresponse() would get
    # "ResponseNotReady".)
    http_conn = conn.new_http_connection(self.upload_url_host, conn.port,
                                         conn.is_secure)
    http_conn.set_debuglevel(conn.debug)

    # Make sure to close http_conn at end so if a local file read
    # failure occurs partway through service will terminate current upload
    # and can report that progress on next attempt.
    try:
      return self._UploadFileBytes(conn, http_conn, fp, file_length,
                                   total_bytes_uploaded, cb, num_cb, headers)
    except (ResumableUploadException, socket.error):
      resp = self._QueryServiceState(conn, file_length)
      if resp.status == 400:
        raise ResumableUploadException(
            'Got 400 response from service state query after failed resumable '
            'upload attempt. This can happen for various reasons, including '
            'specifying an invalid request (e.g., an invalid canned ACL) or '
            'if the file size changed between upload attempts',
            ResumableTransferDisposition.ABORT)
      else:
        raise
    finally:
      http_conn.close()

  def HandleResumableUploadException(self, e, debug):
    if e.disposition == ResumableTransferDisposition.ABORT_CUR_PROCESS:
      if debug >= 1:
        self.logger.debug(
            'Caught non-retryable ResumableUploadException (%s); '
            'aborting but retaining tracker file', e.message)
      raise
    elif e.disposition == ResumableTransferDisposition.ABORT:
      if debug >= 1:
        self.logger.debug(
            'Caught non-retryable ResumableUploadException (%s); '
            'aborting and removing tracker file', e.message)
      raise
    elif e.disposition == ResumableTransferDisposition.START_OVER:
      raise
    else:
      if debug >= 1:
        self.logger.debug('Caught ResumableUploadException (%s) - will retry',
                          e.message)

  def TrackProgressLessIterations(self,
                                  service_had_bytes_before_attempt,
                                  debug=0):
    """Tracks the number of iterations without progress.

    Performs randomized exponential backoff.

    Args:
      service_had_bytes_before_attempt: Number of bytes the service had prior
                                       to this upload attempt.
      debug: debug level 0..3
    """
    # At this point we had a re-tryable failure; see if made progress.
    if self.service_has_bytes > service_had_bytes_before_attempt:
      self.progress_less_iterations = 0  # If progress, reset counter.
    else:
      self.progress_less_iterations += 1

    if self.progress_less_iterations > self.num_retries:
      # Don't retry any longer in the current process.
      raise ResumableUploadException(
          'Too many resumable upload attempts failed without '
          'progress. You might try this upload again later',
          ResumableTransferDisposition.ABORT_CUR_PROCESS)

    # Use binary exponential backoff to desynchronize client requests.
    sleep_time_secs = min(random.random() * (2**self.progress_less_iterations),
                          GetMaxRetryDelay())
    if debug >= 1:
      self.logger.debug(
          'Got retryable failure (%d progress-less in a row).\n'
          'Sleeping %3.1f seconds before re-trying',
          self.progress_less_iterations, sleep_time_secs)
    time.sleep(sleep_time_secs)

  def SendFile(self,
               key,
               fp,
               size,
               headers,
               canned_acl=None,
               cb=None,
               num_cb=XML_PROGRESS_CALLBACKS):
    """Upload a file to a key into a bucket on GS, resumable upload protocol.

    Args:
      key: `boto.s3.key.Key` or subclass representing the upload destination.
      fp: File pointer to upload
      size: Size of the file to upload.
      headers: The headers to pass along with the PUT request
      canned_acl: Optional canned ACL to apply to object.
      cb: Callback function that will be called to report progress on
          the upload.  The callback should accept two integer parameters, the
          first representing the number of bytes that have been successfully
          transmitted to GS, and the second representing the total number of
          bytes that need to be transmitted.
      num_cb: (optional) If a callback is specified with the cb parameter, this
              parameter determines the granularity of the callback by defining
              the maximum number of times the callback will be called during the
              file transfer. Providing a negative integer will cause your
              callback to be called with each buffer read.

    Raises:
      ResumableUploadException if a problem occurs during the transfer.
    """

    if not headers:
      headers = {}
    # If Content-Type header is present and set to None, remove it.
    # This is gsutil's way of asking boto to refrain from auto-generating
    # that header.
    content_type = 'Content-Type'
    if content_type in headers and headers[content_type] is None:
      del headers[content_type]

    if canned_acl:
      headers[key.provider.acl_header] = canned_acl

    headers['User-Agent'] = UserAgent

    file_length = size
    debug = key.bucket.connection.debug

    # Use num-retries from constructor if one was provided; else check
    # for a value specified in the boto config file; else default to 5.
    if self.num_retries is None:
      self.num_retries = GetNumRetries()
    self.progress_less_iterations = 0

    while True:  # Retry as long as we're making progress.
      service_had_bytes_before_attempt = self.service_has_bytes
      try:
        # Save generation and metageneration in class state so caller
        # can find these values, for use in preconditions of future
        # operations on the uploaded object.
        _, self.generation, self.metageneration = self._AttemptResumableUpload(
            key, fp, file_length, headers, cb, num_cb)

        key.generation = self.generation
        if debug >= 1:
          self.logger.debug('Resumable upload complete.')
        return
      except self.RETRYABLE_EXCEPTIONS as e:
        if debug >= 1:
          self.logger.debug('Caught exception (%s)', e.__repr__())
        if isinstance(e, IOError) and e.errno == errno.EPIPE:
          # Broken pipe error causes httplib to immediately
          # close the socket (http://bugs.python.org/issue5542),
          # so we need to close the connection before we resume
          # the upload (which will cause a new connection to be
          # opened the next time an HTTP request is sent).
          key.bucket.connection.connection.close()
      except ResumableUploadException as e:
        self.HandleResumableUploadException(e, debug)

      self.TrackProgressLessIterations(service_had_bytes_before_attempt,
                                       debug=debug)
