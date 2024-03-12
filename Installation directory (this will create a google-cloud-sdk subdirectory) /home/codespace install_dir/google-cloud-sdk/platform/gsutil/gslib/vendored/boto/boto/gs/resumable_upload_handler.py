# Copyright 2010 Google Inc.
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
import errno
import os
import random
import re
import socket
import time
from hashlib import md5

import six.moves.http_client as httplib
from six.moves import urllib as urlparse

from boto import config, UserAgent
from boto.connection import AWSAuthConnection
from boto.exception import InvalidUriError
from boto.exception import ResumableTransferDisposition
from boto.exception import ResumableUploadException
from boto.s3.keyfile import KeyFile

"""
Handler for Google Cloud Storage resumable uploads. See
http://code.google.com/apis/storage/docs/developer-guide.html#resumable
for details.

Resumable uploads will retry failed uploads, resuming at the byte
count completed by the last upload attempt. If too many retries happen with
no progress (per configurable num_retries param), the upload will be
aborted in the current process.

The caller can optionally specify a tracker_file_name param in the
ResumableUploadHandler constructor. If you do this, that file will
save the state needed to allow retrying later, in a separate process
(e.g., in a later run of gsutil).
"""


class ResumableUploadHandler(object):

    BUFFER_SIZE = 8192
    RETRYABLE_EXCEPTIONS = (httplib.HTTPException, IOError, socket.error,
                            socket.gaierror)

    # (start, end) response indicating server has nothing (upload protocol uses
    # inclusive numbering).
    SERVER_HAS_NOTHING = (0, -1)

    def __init__(self, tracker_file_name=None, num_retries=None):
        """
        Constructor. Instantiate once for each uploaded file.

        :type tracker_file_name: string
        :param tracker_file_name: optional file name to save tracker URI.
            If supplied and the current process fails the upload, it can be
            retried in a new process. If called with an existing file containing
            a valid tracker URI, we'll resume the upload from this URI; else
            we'll start a new resumable upload (and write the URI to this
            tracker file).

        :type num_retries: int
        :param num_retries: the number of times we'll re-try a resumable upload
            making no progress. (Count resets every time we get progress, so
            upload can span many more than this number of retries.)
        """
        self.tracker_file_name = tracker_file_name
        self.num_retries = num_retries
        self.server_has_bytes = 0  # Byte count at last server check.
        self.tracker_uri = None
        if tracker_file_name:
            self._load_tracker_uri_from_file()
        # Save upload_start_point in instance state so caller can find how
        # much was transferred by this ResumableUploadHandler (across retries).
        self.upload_start_point = None

    def _load_tracker_uri_from_file(self):
        f = None
        try:
            f = open(self.tracker_file_name, 'r')
            uri = f.readline().strip()
            self._set_tracker_uri(uri)
        except IOError as e:
            # Ignore non-existent file (happens first time an upload
            # is attempted on a file), but warn user for other errors.
            if e.errno != errno.ENOENT:
                # Will restart because self.tracker_uri is None.
                print('Couldn\'t read URI tracker file (%s): %s. Restarting '
                      'upload from scratch.' %
                      (self.tracker_file_name, e.strerror))
        except InvalidUriError as e:
            # Warn user, but proceed (will restart because
            # self.tracker_uri is None).
            print('Invalid tracker URI (%s) found in URI tracker file '
                  '(%s). Restarting upload from scratch.' %
                  (uri, self.tracker_file_name))
        finally:
            if f:
                f.close()

    def _save_tracker_uri_to_file(self):
        """
        Saves URI to tracker file if one was passed to constructor.
        """
        if not self.tracker_file_name:
            return
        f = None
        try:
            with os.fdopen(os.open(self.tracker_file_name,
                                   os.O_WRONLY | os.O_CREAT, 0o600), 'w') as f:
              f.write(self.tracker_uri)
        except IOError as e:
            raise ResumableUploadException(
                'Couldn\'t write URI tracker file (%s): %s.\nThis can happen'
                'if you\'re using an incorrectly configured upload tool\n'
                '(e.g., gsutil configured to save tracker files to an '
                'unwritable directory)' %
                (self.tracker_file_name, e.strerror),
                ResumableTransferDisposition.ABORT)

    def _set_tracker_uri(self, uri):
        """
        Called when we start a new resumable upload or get a new tracker
        URI for the upload. Saves URI and resets upload state.

        Raises InvalidUriError if URI is syntactically invalid.
        """
        parse_result = urlparse.urlparse(uri)
        if (parse_result.scheme.lower() not in ['http', 'https'] or
            not parse_result.netloc):
            raise InvalidUriError('Invalid tracker URI (%s)' % uri)
        self.tracker_uri = uri
        self.tracker_uri_host = parse_result.netloc
        self.tracker_uri_path = '%s?%s' % (
            parse_result.path, parse_result.query)
        self.server_has_bytes = 0

    def get_tracker_uri(self):
        """
        Returns upload tracker URI, or None if the upload has not yet started.
        """
        return self.tracker_uri

    def get_upload_id(self):
        """
        Returns the upload ID for the resumable upload, or None if the upload
        has not yet started.
        """
        # We extract the upload_id from the tracker uri. We could retrieve the
        # upload_id from the headers in the response but this only works for
        # the case where we get the tracker uri from the service. In the case
        # where we get the tracker from the tracking file we need to do this
        # logic anyway.
        delim = '?upload_id='
        if self.tracker_uri and delim in self.tracker_uri:
          return self.tracker_uri[self.tracker_uri.index(delim) + len(delim):]
        else:
          return None

    def _remove_tracker_file(self):
        if (self.tracker_file_name and
            os.path.exists(self.tracker_file_name)):
                os.unlink(self.tracker_file_name)

    def _build_content_range_header(self, range_spec='*', length_spec='*'):
        return 'bytes %s/%s' % (range_spec, length_spec)

    def _query_server_state(self, conn, file_length):
        """
        Queries server to find out state of given upload.

        Note that this method really just makes special case use of the
        fact that the upload server always returns the current start/end
        state whenever a PUT doesn't complete.

        Returns HTTP response from sending request.

        Raises ResumableUploadException if problem querying server.
        """
        # Send an empty PUT so that server replies with this resumable
        # transfer's state.
        put_headers = {}
        put_headers['Content-Range'] = (
            self._build_content_range_header('*', file_length))
        put_headers['Content-Length'] = '0'
        return AWSAuthConnection.make_request(conn, 'PUT',
                                              path=self.tracker_uri_path,
                                              auth_path=self.tracker_uri_path,
                                              headers=put_headers,
                                              host=self.tracker_uri_host)

    def _query_server_pos(self, conn, file_length):
        """
        Queries server to find out what bytes it currently has.

        Returns (server_start, server_end), where the values are inclusive.
        For example, (0, 2) would mean that the server has bytes 0, 1, *and* 2.

        Raises ResumableUploadException if problem querying server.
        """
        resp = self._query_server_state(conn, file_length)
        if resp.status == 200:
            # To handle the boundary condition where the server has the complete
            # file, we return (server_start, file_length-1). That way the
            # calling code can always simply read up through server_end. (If we
            # didn't handle this boundary condition here, the caller would have
            # to check whether server_end == file_length and read one fewer byte
            # in that case.)
            return (0, file_length - 1)  # Completed upload.
        if resp.status != 308:
            # This means the server didn't have any state for the given
            # upload ID, which can happen (for example) if the caller saved
            # the tracker URI to a file and then tried to restart the transfer
            # after that upload ID has gone stale. In that case we need to
            # start a new transfer (and the caller will then save the new
            # tracker URI to the tracker file).
            raise ResumableUploadException(
                'Got non-308 response (%s) from server state query' %
                resp.status, ResumableTransferDisposition.START_OVER)
        got_valid_response = False
        range_spec = resp.getheader('range')
        if range_spec:
            # Parse 'bytes=<from>-<to>' range_spec.
            m = re.search('bytes=(\d+)-(\d+)', range_spec)
            if m:
                server_start = long(m.group(1))
                server_end = long(m.group(2))
                got_valid_response = True
        else:
            # No Range header, which means the server does not yet have
            # any bytes. Note that the Range header uses inclusive 'from'
            # and 'to' values. Since Range 0-0 would mean that the server
            # has byte 0, omitting the Range header is used to indicate that
            # the server doesn't have any bytes.
            return self.SERVER_HAS_NOTHING
        if not got_valid_response:
            raise ResumableUploadException(
                'Couldn\'t parse upload server state query response (%s)' %
                str(resp.getheaders()), ResumableTransferDisposition.START_OVER)
        if conn.debug >= 1:
            print('Server has: Range: %d - %d.' % (server_start, server_end))
        return (server_start, server_end)

    def _start_new_resumable_upload(self, key, headers=None):
        """
        Starts a new resumable upload.

        Raises ResumableUploadException if any errors occur.
        """
        conn = key.bucket.connection
        if conn.debug >= 1:
            print('Starting new resumable upload.')
        self.server_has_bytes = 0

        # Start a new resumable upload by sending a POST request with an
        # empty body and the "X-Goog-Resumable: start" header. Include any
        # caller-provided headers (e.g., Content-Type) EXCEPT Content-Length
        # (and raise an exception if they tried to pass one, since it's
        # a semantic error to specify it at this point, and if we were to
        # include one now it would cause the server to expect that many
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

        resp = conn.make_request(
            'POST', key.bucket.name, key.name, post_headers)
        # Get tracker URI from response 'Location' header.
        body = resp.read()

        # Check for various status conditions.
        if resp.status in [500, 503]:
            # Retry status 500 and 503 errors after a delay.
            raise ResumableUploadException(
                'Got status %d from attempt to start resumable upload. '
                'Will wait/retry' % resp.status,
                ResumableTransferDisposition.WAIT_BEFORE_RETRY)
        elif resp.status != 200 and resp.status != 201:
            raise ResumableUploadException(
                'Got status %d from attempt to start resumable upload. '
                'Aborting' % resp.status,
                ResumableTransferDisposition.ABORT)

        # Else we got 200 or 201 response code, indicating the resumable
        # upload was created.
        tracker_uri = resp.getheader('Location')
        if not tracker_uri:
            raise ResumableUploadException(
                'No resumable tracker URI found in resumable initiation '
                'POST response (%s)' % body,
                ResumableTransferDisposition.WAIT_BEFORE_RETRY)
        self._set_tracker_uri(tracker_uri)
        self._save_tracker_uri_to_file()

    def _upload_file_bytes(self, conn, http_conn, fp, file_length,
                           total_bytes_uploaded, cb, num_cb, headers):
        """
        Makes one attempt to upload file bytes, using an existing resumable
        upload connection.

        Returns (etag, generation, metageneration) from server upon success.

        Raises ResumableUploadException if any problems occur.
        """
        buf = fp.read(self.BUFFER_SIZE)
        if cb:
            # The cb_count represents the number of full buffers to send between
            # cb executions.
            if num_cb > 2:
                cb_count = file_length / self.BUFFER_SIZE / (num_cb-2)
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
        if not headers:
          put_headers = {}
        else:
          put_headers = headers.copy()
        if file_length:
            if total_bytes_uploaded == file_length:
                range_header = self._build_content_range_header(
                    '*', file_length)
            else:
                range_header = self._build_content_range_header(
                    '%d-%d' % (total_bytes_uploaded, file_length - 1),
                    file_length)
            put_headers['Content-Range'] = range_header
        # Set Content-Length to the total bytes we'll send with this PUT.
        put_headers['Content-Length'] = str(file_length - total_bytes_uploaded)
        http_request = AWSAuthConnection.build_base_http_request(
            conn, 'PUT', path=self.tracker_uri_path, auth_path=None,
            headers=put_headers, host=self.tracker_uri_host)
        http_conn.putrequest('PUT', http_request.path)
        for k in put_headers:
            http_conn.putheader(k, put_headers[k])
        http_conn.endheaders()

        # Turn off debug on http connection so upload content isn't included
        # in debug stream.
        http_conn.set_debuglevel(0)
        while buf:
            http_conn.send(buf)
            for alg in self.digesters:
                self.digesters[alg].update(buf)
            total_bytes_uploaded += len(buf)
            if cb:
                i += 1
                if i == cb_count or cb_count == -1:
                    cb(total_bytes_uploaded, file_length)
                    i = 0
            buf = fp.read(self.BUFFER_SIZE)
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
        # Restore http connection debug level.
        http_conn.set_debuglevel(conn.debug)

        if resp.status == 200:
            # Success.
            return (resp.getheader('etag'),
                    resp.getheader('x-goog-generation'),
                    resp.getheader('x-goog-metageneration'))
        # Retry timeout (408) and status 500 and 503 errors after a delay.
        elif resp.status in [408, 500, 503]:
            disposition = ResumableTransferDisposition.WAIT_BEFORE_RETRY
        else:
            # Catch all for any other error codes.
            disposition = ResumableTransferDisposition.ABORT
        raise ResumableUploadException('Got response code %d while attempting '
                                       'upload (%s)' %
                                       (resp.status, resp.reason), disposition)

    def _attempt_resumable_upload(self, key, fp, file_length, headers, cb,
                                  num_cb):
        """
        Attempts a resumable upload.

        Returns (etag, generation, metageneration) from server upon success.

        Raises ResumableUploadException if any problems occur.
        """
        (server_start, server_end) = self.SERVER_HAS_NOTHING
        conn = key.bucket.connection
        if self.tracker_uri:
            # Try to resume existing resumable upload.
            try:
                (server_start, server_end) = (
                    self._query_server_pos(conn, file_length))
                self.server_has_bytes = server_start

                if server_end:
                  # If the server already has some of the content, we need to
                  # update the digesters with the bytes that have already been
                  # uploaded to ensure we get a complete hash in the end.
                  print('Catching up hash digest(s) for resumed upload')
                  fp.seek(0)
                  # Read local file's bytes through position server has. For
                  # example, if server has (0, 3) we want to read 3-0+1=4 bytes.
                  bytes_to_go = server_end + 1
                  while bytes_to_go:
                      chunk = fp.read(min(key.BufferSize, bytes_to_go))
                      if not chunk:
                          raise ResumableUploadException(
                              'Hit end of file during resumable upload hash '
                              'catchup. This should not happen under\n'
                              'normal circumstances, as it indicates the '
                              'server has more bytes of this transfer\nthan'
                              ' the current file size. Restarting upload.',
                              ResumableTransferDisposition.START_OVER)
                      for alg in self.digesters:
                          self.digesters[alg].update(chunk)
                      bytes_to_go -= len(chunk)

                if conn.debug >= 1:
                    print('Resuming transfer.')
            except ResumableUploadException as e:
                if conn.debug >= 1:
                    print('Unable to resume transfer (%s).' % e.message)
                self._start_new_resumable_upload(key, headers)
        else:
            self._start_new_resumable_upload(key, headers)

        # upload_start_point allows the code that instantiated the
        # ResumableUploadHandler to find out the point from which it started
        # uploading (e.g., so it can correctly compute throughput).
        if self.upload_start_point is None:
            self.upload_start_point = server_end

        total_bytes_uploaded = server_end + 1
        # Corner case: Don't attempt to seek if we've already uploaded the
        # entire file, because if the file is a stream (e.g., the KeyFile
        # wrapper around input key when copying between providers), attempting
        # to seek to the end of file would result in an InvalidRange error.
        if file_length < total_bytes_uploaded:
          fp.seek(total_bytes_uploaded)
        conn = key.bucket.connection

        # Get a new HTTP connection (vs conn.get_http_connection(), which reuses
        # pool connections) because httplib requires a new HTTP connection per
        # transaction. (Without this, calling http_conn.getresponse() would get
        # "ResponseNotReady".)
        http_conn = conn.new_http_connection(self.tracker_uri_host, conn.port,
                                             conn.is_secure)
        http_conn.set_debuglevel(conn.debug)

        # Make sure to close http_conn at end so if a local file read
        # failure occurs partway through server will terminate current upload
        # and can report that progress on next attempt.
        try:
            return self._upload_file_bytes(conn, http_conn, fp, file_length,
                                           total_bytes_uploaded, cb, num_cb,
                                           headers)
        except (ResumableUploadException, socket.error):
            resp = self._query_server_state(conn, file_length)
            if resp.status == 400:
                raise ResumableUploadException('Got 400 response from server '
                    'state query after failed resumable upload attempt. This '
                    'can happen for various reasons, including specifying an '
                    'invalid request (e.g., an invalid canned ACL) or if the '
                    'file size changed between upload attempts',
                    ResumableTransferDisposition.ABORT)
            else:
                raise
        finally:
            http_conn.close()

    def _check_final_md5(self, key, etag):
        """
        Checks that etag from server agrees with md5 computed before upload.
        This is important, since the upload could have spanned a number of
        hours and multiple processes (e.g., gsutil runs), and the user could
        change some of the file and not realize they have inconsistent data.
        """
        if key.bucket.connection.debug >= 1:
            print('Checking md5 against etag.')
        if key.md5 != etag.strip('"\''):
            # Call key.open_read() before attempting to delete the
            # (incorrect-content) key, so we perform that request on a
            # different HTTP connection. This is neededb because httplib
            # will return a "Response not ready" error if you try to perform
            # a second transaction on the connection.
            key.open_read()
            key.close()
            key.delete()
            raise ResumableUploadException(
                'File changed during upload: md5 signature doesn\'t match etag '
                '(incorrect uploaded object deleted)',
                ResumableTransferDisposition.ABORT)

    def handle_resumable_upload_exception(self, e, debug):
        if (e.disposition == ResumableTransferDisposition.ABORT_CUR_PROCESS):
            if debug >= 1:
                print('Caught non-retryable ResumableUploadException (%s); '
                      'aborting but retaining tracker file' % e.message)
            raise
        elif (e.disposition == ResumableTransferDisposition.ABORT):
            if debug >= 1:
                print('Caught non-retryable ResumableUploadException (%s); '
                      'aborting and removing tracker file' % e.message)
            self._remove_tracker_file()
            raise
        else:
            if debug >= 1:
                print('Caught ResumableUploadException (%s) - will retry' %
                      e.message)

    def track_progress_less_iterations(self, server_had_bytes_before_attempt,
                                       roll_back_md5=True, debug=0):
        # At this point we had a re-tryable failure; see if made progress.
        if self.server_has_bytes > server_had_bytes_before_attempt:
            self.progress_less_iterations = 0   # If progress, reset counter.
        else:
            self.progress_less_iterations += 1
            if roll_back_md5:
                # Rollback any potential hash updates, as we did not
                # make any progress in this iteration.
                self.digesters = self.digesters_before_attempt

        if self.progress_less_iterations > self.num_retries:
            # Don't retry any longer in the current process.
            raise ResumableUploadException(
                    'Too many resumable upload attempts failed without '
                    'progress. You might try this upload again later',
                    ResumableTransferDisposition.ABORT_CUR_PROCESS)

        # Use binary exponential backoff to desynchronize client requests.
        sleep_time_secs = random.random() * (2**self.progress_less_iterations)
        if debug >= 1:
            print('Got retryable failure (%d progress-less in a row).\n'
                   'Sleeping %3.1f seconds before re-trying' %
                   (self.progress_less_iterations, sleep_time_secs))
        time.sleep(sleep_time_secs)

    def send_file(self, key, fp, headers, cb=None, num_cb=10, hash_algs=None):
        """
        Upload a file to a key into a bucket on GS, using GS resumable upload
        protocol.

        :type key: :class:`boto.s3.key.Key` or subclass
        :param key: The Key object to which data is to be uploaded

        :type fp: file-like object
        :param fp: The file pointer to upload

        :type headers: dict
        :param headers: The headers to pass along with the PUT request

        :type cb: function
        :param cb: a callback function that will be called to report progress on
            the upload.  The callback should accept two integer parameters, the
            first representing the number of bytes that have been successfully
            transmitted to GS, and the second representing the total number of
            bytes that need to be transmitted.

        :type num_cb: int
        :param num_cb: (optional) If a callback is specified with the cb
            parameter, this parameter determines the granularity of the callback
            by defining the maximum number of times the callback will be called
            during the file transfer. Providing a negative integer will cause
            your callback to be called with each buffer read.

        :type hash_algs: dictionary
        :param hash_algs: (optional) Dictionary mapping hash algorithm
            descriptions to corresponding state-ful hashing objects that
            implement update(), digest(), and copy() (e.g. hashlib.md5()).
            Defaults to {'md5': md5()}.

        Raises ResumableUploadException if a problem occurs during the transfer.
        """

        if not headers:
            headers = {}
        # If Content-Type header is present and set to None, remove it.
        # This is gsutil's way of asking boto to refrain from auto-generating
        # that header.
        CT = 'Content-Type'
        if CT in headers and headers[CT] is None:
            del headers[CT]

        headers['User-Agent'] = UserAgent

        # Determine file size different ways for case where fp is actually a
        # wrapper around a Key vs an actual file.
        if isinstance(fp, KeyFile):
            file_length = fp.getkey().size
        else:
            fp.seek(0, os.SEEK_END)
            file_length = fp.tell()
            fp.seek(0)
        debug = key.bucket.connection.debug

        # Compute the MD5 checksum on the fly.
        if hash_algs is None:
            hash_algs = {'md5': md5}
        self.digesters = dict(
            (alg, hash_algs[alg]()) for alg in hash_algs or {})

        # Use num-retries from constructor if one was provided; else check
        # for a value specified in the boto config file; else default to 5.
        if self.num_retries is None:
            self.num_retries = config.getint('Boto', 'num_retries', 6)
        self.progress_less_iterations = 0

        while True:  # Retry as long as we're making progress.
            server_had_bytes_before_attempt = self.server_has_bytes
            self.digesters_before_attempt = dict(
                (alg, self.digesters[alg].copy())
                for alg in self.digesters)
            try:
                # Save generation and metageneration in class state so caller
                # can find these values, for use in preconditions of future
                # operations on the uploaded object.
                (etag, self.generation, self.metageneration) = (
                    self._attempt_resumable_upload(key, fp, file_length,
                                                   headers, cb, num_cb))

                # Get the final digests for the uploaded content.
                for alg in self.digesters:
                    key.local_hashes[alg] = self.digesters[alg].digest()

                # Upload succceded, so remove the tracker file (if have one).
                self._remove_tracker_file()
                self._check_final_md5(key, etag)
                key.generation = self.generation
                if debug >= 1:
                    print('Resumable upload complete.')
                return
            except self.RETRYABLE_EXCEPTIONS as e:
                if debug >= 1:
                    print('Caught exception (%s)' % e.__repr__())
                if isinstance(e, IOError) and e.errno == errno.EPIPE:
                    # Broken pipe error causes httplib to immediately
                    # close the socket (http://bugs.python.org/issue5542),
                    # so we need to close the connection before we resume
                    # the upload (which will cause a new connection to be
                    # opened the next time an HTTP request is sent).
                    key.bucket.connection.connection.close()
            except ResumableUploadException as e:
                self.handle_resumable_upload_exception(e, debug)

            self.track_progress_less_iterations(server_had_bytes_before_attempt,
                                                True, debug)
