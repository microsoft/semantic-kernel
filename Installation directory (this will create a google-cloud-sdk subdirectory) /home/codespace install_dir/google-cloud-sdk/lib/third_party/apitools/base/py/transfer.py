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

"""Upload and download support for apitools."""
from __future__ import print_function

import email.generator as email_generator
import email.mime.multipart as mime_multipart
import email.mime.nonmultipart as mime_nonmultipart
import io
import json
import mimetypes
import os
import threading

import six
from six.moves import http_client

from apitools.base.py import buffered_stream
from apitools.base.py import compression
from apitools.base.py import exceptions
from apitools.base.py import http_wrapper
from apitools.base.py import stream_slice
from apitools.base.py import util

__all__ = [
    'Download',
    'Upload',
    'RESUMABLE_UPLOAD',
    'SIMPLE_UPLOAD',
    'DownloadProgressPrinter',
    'DownloadCompletePrinter',
    'UploadProgressPrinter',
    'UploadCompletePrinter',
]

_RESUMABLE_UPLOAD_THRESHOLD = 5 << 20
SIMPLE_UPLOAD = 'simple'
RESUMABLE_UPLOAD = 'resumable'


def DownloadProgressPrinter(response, unused_download):
    """Print download progress based on response."""
    if 'content-range' in response.info:
        print('Received %s' % response.info['content-range'])
    else:
        print('Received %d bytes' % response.length)


def DownloadCompletePrinter(unused_response, unused_download):
    """Print information about a completed download."""
    print('Download complete')


def UploadProgressPrinter(response, unused_upload):
    """Print upload progress based on response."""
    print('Sent %s' % response.info['range'])


def UploadCompletePrinter(unused_response, unused_upload):
    """Print information about a completed upload."""
    print('Upload complete')


class _Transfer(object):

    """Generic bits common to Uploads and Downloads."""

    def __init__(self, stream, close_stream=False, chunksize=None,
                 auto_transfer=True, http=None, num_retries=5):
        self.__bytes_http = None
        self.__close_stream = close_stream
        self.__http = http
        self.__stream = stream
        self.__url = None

        self.__num_retries = 5
        # Let the @property do validation
        self.num_retries = num_retries

        self.retry_func = (
            http_wrapper.HandleExceptionsAndRebuildHttpConnections)
        self.auto_transfer = auto_transfer
        self.chunksize = chunksize or 1048576

    def __repr__(self):
        return str(self)

    @property
    def close_stream(self):
        return self.__close_stream

    @property
    def http(self):
        return self.__http

    @property
    def bytes_http(self):
        return self.__bytes_http or self.http

    @bytes_http.setter
    def bytes_http(self, value):
        self.__bytes_http = value

    @property
    def num_retries(self):
        return self.__num_retries

    @num_retries.setter
    def num_retries(self, value):
        util.Typecheck(value, six.integer_types)
        if value < 0:
            raise exceptions.InvalidDataError(
                'Cannot have negative value for num_retries')
        self.__num_retries = value

    @property
    def stream(self):
        return self.__stream

    @property
    def url(self):
        return self.__url

    def _Initialize(self, http, url):
        """Initialize this download by setting self.http and self.url.

        We want the user to be able to override self.http by having set
        the value in the constructor; in that case, we ignore the provided
        http.

        Args:
          http: An httplib2.Http instance or None.
          url: The url for this transfer.

        Returns:
          None. Initializes self.
        """
        self.EnsureUninitialized()
        if self.http is None:
            self.__http = http or http_wrapper.GetHttp()
        self.__url = url

    @property
    def initialized(self):
        return self.url is not None and self.http is not None

    @property
    def _type_name(self):
        return type(self).__name__

    def EnsureInitialized(self):
        if not self.initialized:
            raise exceptions.TransferInvalidError(
                'Cannot use uninitialized %s' % self._type_name)

    def EnsureUninitialized(self):
        if self.initialized:
            raise exceptions.TransferInvalidError(
                'Cannot re-initialize %s' % self._type_name)

    def __del__(self):
        if self.__close_stream:
            self.__stream.close()

    def _ExecuteCallback(self, callback, response):
        # TODO(user): Push these into a queue.
        if callback is not None:
            threading.Thread(target=callback, args=(response, self)).start()


class Download(_Transfer):

    """Data for a single download.

    Public attributes:
      chunksize: default chunksize to use for transfers.
    """
    _ACCEPTABLE_STATUSES = set((
        http_client.OK,
        http_client.NO_CONTENT,
        http_client.PARTIAL_CONTENT,
        http_client.REQUESTED_RANGE_NOT_SATISFIABLE,
    ))
    _REQUIRED_SERIALIZATION_KEYS = set((
        'auto_transfer', 'progress', 'total_size', 'url'))

    def __init__(self, stream, progress_callback=None, finish_callback=None,
                 **kwds):
        total_size = kwds.pop('total_size', None)
        super(Download, self).__init__(stream, **kwds)
        self.__initial_response = None
        self.__progress = 0
        self.__total_size = total_size
        self.__encoding = None

        self.progress_callback = progress_callback
        self.finish_callback = finish_callback

    @property
    def progress(self):
        return self.__progress

    @property
    def encoding(self):
        return self.__encoding

    @classmethod
    def FromFile(cls, filename, overwrite=False, auto_transfer=True, **kwds):
        """Create a new download object from a filename."""
        path = os.path.expanduser(filename)
        if os.path.exists(path) and not overwrite:
            raise exceptions.InvalidUserInputError(
                'File %s exists and overwrite not specified' % path)
        return cls(open(path, 'wb'), close_stream=True,
                   auto_transfer=auto_transfer, **kwds)

    @classmethod
    def FromStream(cls, stream, auto_transfer=True, total_size=None, **kwds):
        """Create a new Download object from a stream."""
        return cls(stream, auto_transfer=auto_transfer, total_size=total_size,
                   **kwds)

    @classmethod
    def FromData(cls, stream, json_data, http=None, auto_transfer=None,
                 client=None, **kwds):
        """Create a new Download object from a stream and serialized data."""
        info = json.loads(json_data)
        missing_keys = cls._REQUIRED_SERIALIZATION_KEYS - set(info.keys())
        if missing_keys:
            raise exceptions.InvalidDataError(
                'Invalid serialization data, missing keys: %s' % (
                    ', '.join(missing_keys)))
        download = cls.FromStream(stream, **kwds)
        if auto_transfer is not None:
            download.auto_transfer = auto_transfer
        else:
            download.auto_transfer = info['auto_transfer']
        if client is not None:
            url = client.FinalizeTransferUrl(info['url'])
        else:
            url = info['url']

        setattr(download, '_Download__progress', info['progress'])
        setattr(download, '_Download__total_size', info['total_size'])
        download._Initialize(  # pylint: disable=protected-access
            http, url)
        return download

    @property
    def serialization_data(self):
        self.EnsureInitialized()
        return {
            'auto_transfer': self.auto_transfer,
            'progress': self.progress,
            'total_size': self.total_size,
            'url': self.url,
        }

    @property
    def total_size(self):
        return self.__total_size

    def __str__(self):
        if not self.initialized:
            return 'Download (uninitialized)'
        return 'Download with %d/%s bytes transferred from url %s' % (
            self.progress, self.total_size, self.url)

    def ConfigureRequest(self, http_request, url_builder):
        url_builder.query_params['alt'] = 'media'
        # TODO(user): We need to send range requests because by
        # default httplib2 stores entire reponses in memory. Override
        # httplib2's download method (as gsutil does) so that this is not
        # necessary.
        http_request.headers['Range'] = 'bytes=0-%d' % (self.chunksize - 1,)

    def __SetTotal(self, info):
        """Sets the total size based off info if possible otherwise 0."""
        if 'content-range' in info:
            _, _, total = info['content-range'].rpartition('/')
            if total != '*':
                self.__total_size = int(total)
        # Note "total_size is None" means we don't know it; if no size
        # info was returned on our initial range request, that means we
        # have a 0-byte file. (That last statement has been verified
        # empirically, but is not clearly documented anywhere.)
        if self.total_size is None:
            self.__total_size = 0

    def InitializeDownload(self, http_request, http=None, client=None):
        """Initialize this download by making a request.

        Args:
          http_request: The HttpRequest to use to initialize this download.
          http: The httplib2.Http instance for this request.
          client: If provided, let this client process the final URL before
              sending any additional requests. If client is provided and
              http is not, client.http will be used instead.
        """
        self.EnsureUninitialized()
        if http is None and client is None:
            raise exceptions.UserError('Must provide client or http.')
        http = http or client.http
        if client is not None:
            http_request.url = client.FinalizeTransferUrl(http_request.url)
        url = http_request.url
        if self.auto_transfer:
            end_byte = self.__ComputeEndByte(0)
            self.__SetRangeHeader(http_request, 0, end_byte)
            response = http_wrapper.MakeRequest(
                self.bytes_http or http, http_request)
            if response.status_code not in self._ACCEPTABLE_STATUSES:
                raise exceptions.HttpError.FromResponse(response)
            self.__initial_response = response
            self.__SetTotal(response.info)
            url = response.info.get('content-location', response.request_url)
        if client is not None:
            url = client.FinalizeTransferUrl(url)
        self._Initialize(http, url)
        # Unless the user has requested otherwise, we want to just
        # go ahead and pump the bytes now.
        if self.auto_transfer:
            self.StreamInChunks()

    def __NormalizeStartEnd(self, start, end=None):
        """Normalizes start and end values based on total size."""
        if end is not None:
            if start < 0:
                raise exceptions.TransferInvalidError(
                    'Cannot have end index with negative start index ' +
                    '[start=%d, end=%d]' % (start, end))
            elif start >= self.total_size:
                raise exceptions.TransferInvalidError(
                    'Cannot have start index greater than total size ' +
                    '[start=%d, total_size=%d]' % (start, self.total_size))
            end = min(end, self.total_size - 1)
            if end < start:
                raise exceptions.TransferInvalidError(
                    'Range requested with end[%s] < start[%s]' % (end, start))
            return start, end
        else:
            if start < 0:
                start = max(0, start + self.total_size)
            return start, self.total_size - 1

    def __SetRangeHeader(self, request, start, end=None):
        if start < 0:
            request.headers['range'] = 'bytes=%d' % start
        elif end is None or end < start:
            request.headers['range'] = 'bytes=%d-' % start
        else:
            request.headers['range'] = 'bytes=%d-%d' % (start, end)

    def __ComputeEndByte(self, start, end=None, use_chunks=True):
        """Compute the last byte to fetch for this request.

        This is all based on the HTTP spec for Range and
        Content-Range.

        Note that this is potentially confusing in several ways:
          * the value for the last byte is 0-based, eg "fetch 10 bytes
            from the beginning" would return 9 here.
          * if we have no information about size, and don't want to
            use the chunksize, we'll return None.
        See the tests for more examples.

        Args:
          start: byte to start at.
          end: (int or None, default: None) Suggested last byte.
          use_chunks: (bool, default: True) If False, ignore self.chunksize.

        Returns:
          Last byte to use in a Range header, or None.

        """
        end_byte = end

        if start < 0 and not self.total_size:
            return end_byte

        if use_chunks:
            alternate = start + self.chunksize - 1
            if end_byte is not None:
                end_byte = min(end_byte, alternate)
            else:
                end_byte = alternate

        if self.total_size:
            alternate = self.total_size - 1
            if end_byte is not None:
                end_byte = min(end_byte, alternate)
            else:
                end_byte = alternate

        return end_byte

    def __GetChunk(self, start, end, additional_headers=None):
        """Retrieve a chunk, and return the full response."""
        self.EnsureInitialized()
        request = http_wrapper.Request(url=self.url)
        self.__SetRangeHeader(request, start, end=end)
        if additional_headers is not None:
            request.headers.update(additional_headers)
        return http_wrapper.MakeRequest(
            self.bytes_http, request, retry_func=self.retry_func,
            retries=self.num_retries)

    def __ProcessResponse(self, response):
        """Process response (by updating self and writing to self.stream)."""
        if response.status_code not in self._ACCEPTABLE_STATUSES:
            # We distinguish errors that mean we made a mistake in setting
            # up the transfer versus something we should attempt again.
            if response.status_code in (http_client.FORBIDDEN,
                                        http_client.NOT_FOUND):
                raise exceptions.HttpError.FromResponse(response)
            else:
                raise exceptions.TransferRetryError(response.content)
        if response.status_code in (http_client.OK,
                                    http_client.PARTIAL_CONTENT):
            try:
                self.stream.write(six.ensure_binary(response.content))
            except TypeError:
                self.stream.write(six.ensure_text(response.content))
            self.__progress += response.length
            if response.info and 'content-encoding' in response.info:
                # TODO(user): Handle the case where this changes over a
                # download.
                self.__encoding = response.info['content-encoding']
        elif response.status_code == http_client.NO_CONTENT:
            # It's important to write something to the stream for the case
            # of a 0-byte download to a file, as otherwise python won't
            # create the file.
            self.stream.write('')
        return response

    def GetRange(self, start, end=None, additional_headers=None,
                 use_chunks=True):
        """Retrieve a given byte range from this download, inclusive.

        Range must be of one of these three forms:
        * 0 <= start, end = None: Fetch from start to the end of the file.
        * 0 <= start <= end: Fetch the bytes from start to end.
        * start < 0, end = None: Fetch the last -start bytes of the file.

        (These variations correspond to those described in the HTTP 1.1
        protocol for range headers in RFC 2616, sec. 14.35.1.)

        Args:
          start: (int) Where to start fetching bytes. (See above.)
          end: (int, optional) Where to stop fetching bytes. (See above.)
          additional_headers: (bool, optional) Any additional headers to
              pass with the request.
          use_chunks: (bool, default: True) If False, ignore self.chunksize
              and fetch this range in a single request.

        Returns:
          None. Streams bytes into self.stream.
        """
        self.EnsureInitialized()
        progress_end_normalized = False
        if self.total_size is not None:
            progress, end_byte = self.__NormalizeStartEnd(start, end)
            progress_end_normalized = True
        else:
            progress = start
            end_byte = end
        while (not progress_end_normalized or end_byte is None or
               progress <= end_byte):
            end_byte = self.__ComputeEndByte(progress, end=end_byte,
                                             use_chunks=use_chunks)
            response = self.__GetChunk(progress, end_byte,
                                       additional_headers=additional_headers)
            if not progress_end_normalized:
                self.__SetTotal(response.info)
                progress, end_byte = self.__NormalizeStartEnd(start, end)
                progress_end_normalized = True
            response = self.__ProcessResponse(response)
            progress += response.length
            if response.length == 0:
                if response.status_code == http_client.OK:
                    # There can legitimately be no Content-Length header sent
                    # in some cases (e.g., when there's a Transfer-Encoding
                    # header) and if this was a 200 response (as opposed to
                    # 206 Partial Content) we know we're done now without
                    # looping further on received length.
                    return
                raise exceptions.TransferRetryError(
                    'Zero bytes unexpectedly returned in download response')

    def StreamInChunks(self, callback=None, finish_callback=None,
                       additional_headers=None):
        """Stream the entire download in chunks."""
        self.StreamMedia(callback=callback, finish_callback=finish_callback,
                         additional_headers=additional_headers,
                         use_chunks=True)

    def StreamMedia(self, callback=None, finish_callback=None,
                    additional_headers=None, use_chunks=True):
        """Stream the entire download.

        Args:
          callback: (default: None) Callback to call as each chunk is
              completed.
          finish_callback: (default: None) Callback to call when the
              download is complete.
          additional_headers: (default: None) Additional headers to
              include in fetching bytes.
          use_chunks: (bool, default: True) If False, ignore self.chunksize
              and stream this download in a single request.

        Returns:
            None. Streams bytes into self.stream.
        """
        callback = callback or self.progress_callback
        finish_callback = finish_callback or self.finish_callback

        self.EnsureInitialized()
        while True:
            if self.__initial_response is not None:
                response = self.__initial_response
                self.__initial_response = None
            else:
                end_byte = self.__ComputeEndByte(self.progress,
                                                 use_chunks=use_chunks)
                response = self.__GetChunk(
                    self.progress, end_byte,
                    additional_headers=additional_headers)
            if self.total_size is None:
                self.__SetTotal(response.info)
            response = self.__ProcessResponse(response)
            self._ExecuteCallback(callback, response)
            if (response.status_code == http_client.OK or
                    self.progress >= self.total_size):
                break
        self._ExecuteCallback(finish_callback, response)


if six.PY3:
    class MultipartBytesGenerator(email_generator.BytesGenerator):
        """Generates a bytes Message object tree for multipart messages

        This is a BytesGenerator that has been modified to not attempt line
        termination character modification in the bytes payload. Known to
        work with the compat32 policy only. It may work on others, but not
        tested. The outfp object must accept bytes in its write method.
        """
        def _handle_text(self, msg):
            # If the string has surrogates the original source was bytes, so
            # just write it back out.
            if msg._payload is None:
                return
            self.write(msg._payload)

        def _encode(self, s):
            return s.encode('ascii', 'surrogateescape')

        # Default body handler
        _writeBody = _handle_text


class Upload(_Transfer):

    """Data for a single Upload.

    Fields:
      stream: The stream to upload.
      mime_type: MIME type of the upload.
      total_size: (optional) Total upload size for the stream.
      close_stream: (default: False) Whether or not we should close the
          stream when finished with the upload.
      auto_transfer: (default: True) If True, stream all bytes as soon as
          the upload is created.
    """
    _REQUIRED_SERIALIZATION_KEYS = set((
        'auto_transfer', 'mime_type', 'total_size', 'url'))

    def __init__(self, stream, mime_type, total_size=None, http=None,
                 close_stream=False, chunksize=None, auto_transfer=True,
                 progress_callback=None, finish_callback=None,
                 gzip_encoded=False, **kwds):
        super(Upload, self).__init__(
            stream, close_stream=close_stream, chunksize=chunksize,
            auto_transfer=auto_transfer, http=http, **kwds)
        self.__complete = False
        self.__final_response = None
        self.__mime_type = mime_type
        self.__progress = 0
        self.__server_chunk_granularity = None
        self.__strategy = None
        self.__total_size = None
        self.__gzip_encoded = gzip_encoded

        self.progress_callback = progress_callback
        self.finish_callback = finish_callback
        self.total_size = total_size

    @property
    def progress(self):
        return self.__progress

    @classmethod
    def FromFile(cls, filename, mime_type=None, auto_transfer=True,
                 gzip_encoded=False, **kwds):
        """Create a new Upload object from a filename."""
        path = os.path.expanduser(filename)
        if not os.path.exists(path):
            raise exceptions.NotFoundError('Could not find file %s' % path)
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(path)
            if mime_type is None:
                raise exceptions.InvalidUserInputError(
                    'Could not guess mime type for %s' % path)
        size = os.stat(path).st_size
        return cls(open(path, 'rb'), mime_type, total_size=size,
                   close_stream=True, auto_transfer=auto_transfer,
                   gzip_encoded=gzip_encoded, **kwds)

    @classmethod
    def FromStream(cls, stream, mime_type, total_size=None, auto_transfer=True,
                   gzip_encoded=False, **kwds):
        """Create a new Upload object from a stream."""
        if mime_type is None:
            raise exceptions.InvalidUserInputError(
                'No mime_type specified for stream')
        return cls(stream, mime_type, total_size=total_size,
                   close_stream=False, auto_transfer=auto_transfer,
                   gzip_encoded=gzip_encoded, **kwds)

    @classmethod
    def FromData(cls, stream, json_data, http, auto_transfer=None,
                 gzip_encoded=False, client=None, **kwds):
        """Create a new Upload of stream from serialized json_data and http."""
        info = json.loads(json_data)
        missing_keys = cls._REQUIRED_SERIALIZATION_KEYS - set(info.keys())
        if missing_keys:
            raise exceptions.InvalidDataError(
                'Invalid serialization data, missing keys: %s' % (
                    ', '.join(missing_keys)))
        if 'total_size' in kwds:
            raise exceptions.InvalidUserInputError(
                'Cannot override total_size on serialized Upload')
        upload = cls.FromStream(stream, info['mime_type'],
                                total_size=info.get('total_size'),
                                gzip_encoded=gzip_encoded, **kwds)
        if isinstance(stream, io.IOBase) and not stream.seekable():
            raise exceptions.InvalidUserInputError(
                'Cannot restart resumable upload on non-seekable stream')
        if auto_transfer is not None:
            upload.auto_transfer = auto_transfer
        else:
            upload.auto_transfer = info['auto_transfer']
        if client is not None:
          url = client.FinalizeTransferUrl(info['url'])
        else:
          url = info['url']

        upload.strategy = RESUMABLE_UPLOAD
        upload._Initialize(  # pylint: disable=protected-access
            http, url)
        upload.RefreshResumableUploadState()
        upload.EnsureInitialized()
        if upload.auto_transfer:
            upload.StreamInChunks()
        return upload

    @property
    def serialization_data(self):
        self.EnsureInitialized()
        if self.strategy != RESUMABLE_UPLOAD:
            raise exceptions.InvalidDataError(
                'Serialization only supported for resumable uploads')
        return {
            'auto_transfer': self.auto_transfer,
            'mime_type': self.mime_type,
            'total_size': self.total_size,
            'url': self.url,
        }

    @property
    def complete(self):
        return self.__complete

    @property
    def mime_type(self):
        return self.__mime_type

    def __str__(self):
        if not self.initialized:
            return 'Upload (uninitialized)'
        return 'Upload with %d/%s bytes transferred for url %s' % (
            self.progress, self.total_size or '???', self.url)

    @property
    def strategy(self):
        return self.__strategy

    @strategy.setter
    def strategy(self, value):
        if value not in (SIMPLE_UPLOAD, RESUMABLE_UPLOAD):
            raise exceptions.UserError((
                'Invalid value "%s" for upload strategy, must be one of '
                '"simple" or "resumable".') % value)
        self.__strategy = value

    @property
    def total_size(self):
        return self.__total_size

    @total_size.setter
    def total_size(self, value):
        self.EnsureUninitialized()
        self.__total_size = value

    def __SetDefaultUploadStrategy(self, upload_config, http_request):
        """Determine and set the default upload strategy for this upload.

        We generally prefer simple or multipart, unless we're forced to
        use resumable. This happens when any of (1) the upload is too
        large, (2) the simple endpoint doesn't support multipart requests
        and we have metadata, or (3) there is no simple upload endpoint.

        Args:
          upload_config: Configuration for the upload endpoint.
          http_request: The associated http request.

        Returns:
          None.
        """
        if upload_config.resumable_path is None:
            self.strategy = SIMPLE_UPLOAD
        if self.strategy is not None:
            return
        strategy = SIMPLE_UPLOAD
        if (self.total_size is not None and
                self.total_size > _RESUMABLE_UPLOAD_THRESHOLD):
            strategy = RESUMABLE_UPLOAD
        if http_request.body and not upload_config.simple_multipart:
            strategy = RESUMABLE_UPLOAD
        if not upload_config.simple_path:
            strategy = RESUMABLE_UPLOAD
        self.strategy = strategy

    def ConfigureRequest(self, upload_config, http_request, url_builder):
        """Configure the request and url for this upload."""
        # Validate total_size vs. max_size
        if (self.total_size and upload_config.max_size and
                self.total_size > upload_config.max_size):
            raise exceptions.InvalidUserInputError(
                'Upload too big: %s larger than max size %s' % (
                    self.total_size, upload_config.max_size))
        # Validate mime type
        if not util.AcceptableMimeType(upload_config.accept, self.mime_type):
            raise exceptions.InvalidUserInputError(
                'MIME type %s does not match any accepted MIME ranges %s' % (
                    self.mime_type, upload_config.accept))

        self.__SetDefaultUploadStrategy(upload_config, http_request)
        if self.strategy == SIMPLE_UPLOAD:
            url_builder.relative_path = upload_config.simple_path
            if http_request.body:
                url_builder.query_params['uploadType'] = 'multipart'
                self.__ConfigureMultipartRequest(http_request)
            else:
                url_builder.query_params['uploadType'] = 'media'
                self.__ConfigureMediaRequest(http_request)
            # Once the entire body is written, compress the body if configured
            # to. Both multipart and media request uploads will read the
            # entire stream into memory, which means full compression is also
            # safe to perform. Because the strategy is set to SIMPLE_UPLOAD,
            # StreamInChunks throws an exception, meaning double compression
            # cannot happen.
            if self.__gzip_encoded:
                http_request.headers['Content-Encoding'] = 'gzip'
                # Turn the body into a stream so that we can compress it, then
                # read the compressed bytes.  In the event of a retry (e.g. if
                # our access token has expired), we need to be able to re-read
                # the body, which we can't do with a stream. So, we consume the
                # bytes from the stream now and store them in a re-readable
                # bytes container.
                http_request.body = (
                    compression.CompressStream(
                        six.BytesIO(http_request.body))[0].read())
        else:
            url_builder.relative_path = upload_config.resumable_path
            url_builder.query_params['uploadType'] = 'resumable'
            self.__ConfigureResumableRequest(http_request)

    def __ConfigureMediaRequest(self, http_request):
        """Configure http_request as a simple request for this upload."""
        http_request.headers['content-type'] = self.mime_type
        http_request.body = self.stream.read()
        http_request.loggable_body = '<media body>'

    def __ConfigureMultipartRequest(self, http_request):
        """Configure http_request as a multipart request for this upload."""
        # This is a multipart/related upload.
        msg_root = mime_multipart.MIMEMultipart('related')
        # msg_root should not write out its own headers
        setattr(msg_root, '_write_headers', lambda self: None)

        # attach the body as one part
        msg = mime_nonmultipart.MIMENonMultipart(
            *http_request.headers['content-type'].split('/'))
        msg.set_payload(http_request.body)
        msg_root.attach(msg)

        # attach the media as the second part
        msg = mime_nonmultipart.MIMENonMultipart(*self.mime_type.split('/'))
        msg['Content-Transfer-Encoding'] = 'binary'
        msg.set_payload(self.stream.read())
        msg_root.attach(msg)

        # NOTE: We encode the body, but can't use
        #       `email.message.Message.as_string` because it prepends
        #       `> ` to `From ` lines.
        fp = six.BytesIO()
        if six.PY3:
            generator_class = MultipartBytesGenerator
        else:
            generator_class = email_generator.Generator
        g = generator_class(fp, mangle_from_=False)
        g.flatten(msg_root, unixfrom=False)
        http_request.body = fp.getvalue()

        multipart_boundary = msg_root.get_boundary()
        http_request.headers['content-type'] = (
            'multipart/related; boundary=%r' % multipart_boundary)
        if isinstance(multipart_boundary, six.text_type):
            multipart_boundary = multipart_boundary.encode('ascii')

        body_components = http_request.body.split(multipart_boundary)
        headers, _, _ = body_components[-2].partition(b'\n\n')
        body_components[-2] = b'\n\n'.join([headers, b'<media body>\n\n--'])
        http_request.loggable_body = multipart_boundary.join(body_components)

    def __ConfigureResumableRequest(self, http_request):
        http_request.headers['X-Upload-Content-Type'] = self.mime_type
        if self.total_size is not None:
            http_request.headers[
                'X-Upload-Content-Length'] = str(self.total_size)

    def RefreshResumableUploadState(self):
        """Talk to the server and refresh the state of this resumable upload.

        Returns:
          Response if the upload is complete.
        """
        if self.strategy != RESUMABLE_UPLOAD:
            return
        self.EnsureInitialized()
        refresh_request = http_wrapper.Request(
            url=self.url, http_method='PUT',
            headers={'Content-Range': 'bytes */*'})
        refresh_response = http_wrapper.MakeRequest(
            self.http, refresh_request, redirections=0,
            retries=self.num_retries)
        range_header = self._GetRangeHeaderFromResponse(refresh_response)
        if refresh_response.status_code in (http_client.OK,
                                            http_client.CREATED):
            self.__complete = True
            self.__progress = self.total_size
            self.stream.seek(self.progress)
            # If we're finished, the refresh response will contain the metadata
            # originally requested. Cache it so it can be returned in
            # StreamInChunks.
            self.__final_response = refresh_response
        elif refresh_response.status_code == http_wrapper.RESUME_INCOMPLETE:
            if range_header is None:
                self.__progress = 0
            else:
                self.__progress = self.__GetLastByte(range_header) + 1
            self.stream.seek(self.progress)
        else:
            raise exceptions.HttpError.FromResponse(refresh_response)

    def _GetRangeHeaderFromResponse(self, response):
        return response.info.get('Range', response.info.get('range'))

    def InitializeUpload(self, http_request, http=None, client=None):
        """Initialize this upload from the given http_request."""
        if self.strategy is None:
            raise exceptions.UserError(
                'No upload strategy set; did you call ConfigureRequest?')
        if http is None and client is None:
            raise exceptions.UserError('Must provide client or http.')
        if self.strategy != RESUMABLE_UPLOAD:
            return
        http = http or client.http
        if client is not None:
            http_request.url = client.FinalizeTransferUrl(http_request.url)
        self.EnsureUninitialized()
        http_response = http_wrapper.MakeRequest(http, http_request,
                                                 retries=self.num_retries)
        if http_response.status_code != http_client.OK:
            raise exceptions.HttpError.FromResponse(http_response)

        self.__server_chunk_granularity = http_response.info.get(
            'X-Goog-Upload-Chunk-Granularity')
        url = http_response.info['location']
        if client is not None:
            url = client.FinalizeTransferUrl(url)
        self._Initialize(http, url)

        # Unless the user has requested otherwise, we want to just
        # go ahead and pump the bytes now.
        if self.auto_transfer:
            return self.StreamInChunks()
        return http_response

    def __GetLastByte(self, range_header):
        _, _, end = range_header.partition('-')
        # TODO(user): Validate start == 0?
        return int(end)

    def __ValidateChunksize(self, chunksize=None):
        if self.__server_chunk_granularity is None:
            return
        chunksize = chunksize or self.chunksize
        if chunksize % self.__server_chunk_granularity:
            raise exceptions.ConfigurationValueError(
                'Server requires chunksize to be a multiple of %d' %
                self.__server_chunk_granularity)

    def __IsRetryable(self, response):
        return (response.status_code >= 500 or
                response.status_code == http_wrapper.TOO_MANY_REQUESTS or
                response.retry_after)

    def __StreamMedia(self, callback=None, finish_callback=None,
                      additional_headers=None, use_chunks=True):
        """Helper function for StreamMedia / StreamInChunks."""
        if self.strategy != RESUMABLE_UPLOAD:
            raise exceptions.InvalidUserInputError(
                'Cannot stream non-resumable upload')
        callback = callback or self.progress_callback
        finish_callback = finish_callback or self.finish_callback
        # final_response is set if we resumed an already-completed upload.
        response = self.__final_response

        def CallSendChunk(start):
            return self.__SendChunk(
                start, additional_headers=additional_headers)

        def CallSendMediaBody(start):
            return self.__SendMediaBody(
                start, additional_headers=additional_headers)

        send_func = CallSendChunk if use_chunks else CallSendMediaBody
        if not use_chunks and self.__gzip_encoded:
            raise exceptions.InvalidUserInputError(
                'Cannot gzip encode non-chunked upload')
        if use_chunks:
            self.__ValidateChunksize(self.chunksize)
        self.EnsureInitialized()
        while not self.complete:
            response = send_func(self.stream.tell())
            if response.status_code in (http_client.OK, http_client.CREATED):
                self.__complete = True
                break
            if response.status_code not in (
                    http_client.OK, http_client.CREATED,
                    http_wrapper.RESUME_INCOMPLETE):
                # Only raise an exception if the error is something we can't
                # recover from.
                if (self.strategy != RESUMABLE_UPLOAD or
                        not self.__IsRetryable(response)):
                    raise exceptions.HttpError.FromResponse(response)
                # We want to reset our state to wherever the server left us
                # before this failed request, and then raise.
                self.RefreshResumableUploadState()

                self._ExecuteCallback(callback, response)
                continue

            self.__progress = self.__GetLastByte(
                self._GetRangeHeaderFromResponse(response))
            if self.progress + 1 != self.stream.tell():
                # TODO(user): Add a better way to recover here.
                raise exceptions.CommunicationError(
                    'Failed to transfer all bytes in chunk, upload paused at '
                    'byte %d' % self.progress)
            self._ExecuteCallback(callback, response)
        if self.__complete and hasattr(self.stream, 'seek'):
            current_pos = self.stream.tell()
            self.stream.seek(0, os.SEEK_END)
            end_pos = self.stream.tell()
            self.stream.seek(current_pos)
            if current_pos != end_pos:
                raise exceptions.TransferInvalidError(
                    'Upload complete with %s additional bytes left in stream' %
                    (int(end_pos) - int(current_pos)))
        self._ExecuteCallback(finish_callback, response)
        return response

    def StreamMedia(self, callback=None, finish_callback=None,
                    additional_headers=None):
        """Send this resumable upload in a single request.

        Args:
          callback: Progress callback function with inputs
              (http_wrapper.Response, transfer.Upload)
          finish_callback: Final callback function with inputs
              (http_wrapper.Response, transfer.Upload)
          additional_headers: Dict of headers to include with the upload
              http_wrapper.Request.

        Returns:
          http_wrapper.Response of final response.
        """
        return self.__StreamMedia(
            callback=callback, finish_callback=finish_callback,
            additional_headers=additional_headers, use_chunks=False)

    def StreamInChunks(self, callback=None, finish_callback=None,
                       additional_headers=None):
        """Send this (resumable) upload in chunks."""
        return self.__StreamMedia(
            callback=callback, finish_callback=finish_callback,
            additional_headers=additional_headers)

    def __SendMediaRequest(self, request, end):
        """Request helper function for SendMediaBody & SendChunk."""
        def CheckResponse(response):
            if response is None:
                # Caller shouldn't call us if the response is None,
                # but handle anyway.
                raise exceptions.RequestError(
                    'Request to url %s did not return a response.' %
                    response.request_url)
        response = http_wrapper.MakeRequest(
            self.bytes_http, request, retry_func=self.retry_func,
            retries=self.num_retries, check_response_func=CheckResponse)
        if response.status_code == http_wrapper.RESUME_INCOMPLETE:
            last_byte = self.__GetLastByte(
                self._GetRangeHeaderFromResponse(response))
            if last_byte + 1 != end:
                self.stream.seek(last_byte + 1)
        return response

    def __SendMediaBody(self, start, additional_headers=None):
        """Send the entire media stream in a single request."""
        self.EnsureInitialized()
        if self.total_size is None:
            raise exceptions.TransferInvalidError(
                'Total size must be known for SendMediaBody')
        body_stream = stream_slice.StreamSlice(
            self.stream, self.total_size - start)

        request = http_wrapper.Request(url=self.url, http_method='PUT',
                                       body=body_stream)
        request.headers['Content-Type'] = self.mime_type
        if start == self.total_size:
            # End of an upload with 0 bytes left to send; just finalize.
            range_string = 'bytes */%s' % self.total_size
        else:
            range_string = 'bytes %s-%s/%s' % (start, self.total_size - 1,
                                               self.total_size)

        request.headers['Content-Range'] = range_string
        if additional_headers:
            request.headers.update(additional_headers)

        return self.__SendMediaRequest(request, self.total_size)

    def __SendChunk(self, start, additional_headers=None):
        """Send the specified chunk."""
        self.EnsureInitialized()
        no_log_body = self.total_size is None
        request = http_wrapper.Request(url=self.url, http_method='PUT')
        if self.__gzip_encoded:
            request.headers['Content-Encoding'] = 'gzip'
            body_stream, read_length, exhausted = compression.CompressStream(
                self.stream, self.chunksize)
            end = start + read_length
            # If the stream length was previously unknown and the input stream
            # is exhausted, then we're at the end of the stream.
            if self.total_size is None and exhausted:
                self.__total_size = end
        elif self.total_size is None:
            # For the streaming resumable case, we need to detect when
            # we're at the end of the stream.
            body_stream = buffered_stream.BufferedStream(
                self.stream, start, self.chunksize)
            end = body_stream.stream_end_position
            if body_stream.stream_exhausted:
                self.__total_size = end
            # TODO: Here, change body_stream from a stream to a string object,
            # which means reading a chunk into memory.  This works around
            # https://code.google.com/p/httplib2/issues/detail?id=176 which can
            # cause httplib2 to skip bytes on 401's for file objects.
            # Rework this solution to be more general.
            body_stream = body_stream.read(self.chunksize)
        else:
            end = min(start + self.chunksize, self.total_size)
            body_stream = stream_slice.StreamSlice(self.stream, end - start)
        # TODO(user): Think about clearer errors on "no data in
        # stream".
        request.body = body_stream
        request.headers['Content-Type'] = self.mime_type
        if no_log_body:
            # Disable logging of streaming body.
            # TODO: Remove no_log_body and rework as part of a larger logs
            # refactor.
            request.loggable_body = '<media body>'
        if self.total_size is None:
            # Streaming resumable upload case, unknown total size.
            range_string = 'bytes %s-%s/*' % (start, end - 1)
        elif end == start:
            # End of an upload with 0 bytes left to send; just finalize.
            range_string = 'bytes */%s' % self.total_size
        else:
            # Normal resumable upload case with known sizes.
            range_string = 'bytes %s-%s/%s' % (start, end - 1, self.total_size)

        request.headers['Content-Range'] = range_string
        if additional_headers:
            request.headers.update(additional_headers)

        return self.__SendMediaRequest(request, end)
