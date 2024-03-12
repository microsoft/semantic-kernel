# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Lightweight websocket for IAP."""

# See https://datatracker.ietf.org/doc/html/rfc6455 for the protocol used.
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import errno
import select
import socket
import ssl
import struct
import threading

from googlecloudsdk.core.util import platforms
import six
import websocket._abnf as websocket_frame_utils
import websocket._exceptions as websocket_exceptions
import websocket._handshake as websocket_handshake
import websocket._http as websocket_http_utils
import websocket._utils as websocket_utils

WEBSOCKET_RETRY_TIMEOUT_SECS = 3
WEBSOCKET_MAX_ATTEMPTS = 3
CLOSE_STATUS_NORMAL = 1000
VALID_OPCODES = [
    websocket_frame_utils.ABNF.OPCODE_CLOSE,
    websocket_frame_utils.ABNF.OPCODE_BINARY
]


class SockOpt(object):
  """Class that represents the options for the underlying socket library."""

  def __init__(self, sslopt):
    if sslopt is None:
      sslopt = {}
    # Timeout and sockopt are required for the underlying library but we don't
    # use it.
    self.timeout = None
    self.sockopt = []
    self.sslopt = sslopt


class _FrameBuffer(object):
  """Class that represents one single frame sent or received by the websocket."""

  def __init__(self, recv_fn):
    self.recv = recv_fn

  def _recv_header(self):
    """Parse the header from the message."""
    header = self.recv(2)
    b1 = header[0]

    if six.PY2:
      b1 = ord(b1)

    fin = b1 >> 7 & 1
    rsv1 = b1 >> 6 & 1
    rsv2 = b1 >> 5 & 1
    rsv3 = b1 >> 4 & 1
    opcode = b1 & 0xf
    b2 = header[1]

    if six.PY2:
      b2 = ord(b2)

    has_mask = b2 >> 7 & 1
    length_bits = b2 & 0x7f

    return (fin, rsv1, rsv2, rsv3, opcode, has_mask, length_bits)

  def _recv_length(self, bits):
    """Parse the length from the message."""
    length_bits = bits & 0x7f
    if length_bits == 0x7e:
      v = self.recv(2)
      return struct.unpack("!H", v)[0]
    elif length_bits == 0x7f:
      v = self.recv(8)
      return struct.unpack("!Q", v)[0]
    else:
      return length_bits

  def recv_frame(self):
    """Receives the whole frame."""
    # Receives the header.
    (fin, rsv1, rsv2, rsv3, opcode, has_mask, length_bits) = self._recv_header()
    if has_mask == 1:
      raise Exception("Server should not mask the response")
    # Receives the frame length.
    length = self._recv_length(length_bits)
    # Receives the payload.
    payload = self.recv(length)

    return websocket_frame_utils.ABNF(fin, rsv1, rsv2, rsv3, opcode, has_mask,
                                      payload)


class IapLightWeightWebsocket(object):
  """Lightweight websocket created to send and receive data as fast as possible.

     This websocket implements rfc6455
  """

  def __init__(self,
               url,
               header,
               on_data,
               on_close,
               on_error,
               subprotocols,
               sock=None):
    self.url = url
    self.on_data = on_data
    self.on_close = on_close
    self.on_error = on_error
    # Sock is an already connected socket
    self.sock = sock
    # Used to store frame data during recv.
    self.frame_buffer = _FrameBuffer(self._recv_bytes)
    self.connected = False
    # Used to fix the mask key used. This is important for unit tests so we
    # don't use a random mask everytime.
    self.get_mask_key = None
    self.subprotocols = subprotocols
    self.header = header
    # Multiple threads may attempt to write simultaneously. This
    # is a bandaid attempt to fix a thread safety issue.
    # TODO(b/276477340): Find a better solution than to use locks as this code
    # does seem to decrease performance by ~3%.
    self.send_write_lock = threading.Lock()

  def recv(self):
    """Receives data from the server."""
    if not self.connected or not self.sock:
      raise websocket_exceptions.WebSocketConnectionClosedException(
          "Connection closed while receiving data.")
    # We will call recv_frame, which does the recv + parsing of the message
    return self.frame_buffer.recv_frame()

  def send(self, data, opcode):
    """Sends data to the server."""
    if opcode not in VALID_OPCODES:
      raise ValueError("Invalid opcode")
    # Create the frame, fin indicates the end, so we are sending only one frame.
    # Rsv1,rsv2 and rsv3 should be 0, they are extra flags but our server
    # doesn't interpret them. Mask is a fixed value that indicates if we want to
    # mask the data
    frame_data = websocket_frame_utils.ABNF(
        fin=1, rsv1=0, rsv2=0, rsv3=0, opcode=opcode, mask=1, data=data)

    if self.get_mask_key:
      frame_data.get_mask_key = self.get_mask_key
    frame_data = frame_data.format()
    # We will try to send up to WEBSOCKET_MAX_ATTEMPTS in case the
    # exception is not fatal.
    with self.send_write_lock:
      for attempt in range(1, WEBSOCKET_MAX_ATTEMPTS + 1):
        try:
          if not self.connected or not self.sock:
            raise websocket_exceptions.WebSocketConnectionClosedException(
                "Connection closed while sending data.")
          bytes_sent = self.sock.send(frame_data)
          # No bytes sent means the socket is closed.
          if not bytes_sent:
            raise websocket_exceptions.WebSocketConnectionClosedException(
                "Connection closed while sending data.")

          # If we failed to send all the data, throw error.
          if len(frame_data) != bytes_sent:
            raise Exception("Packet was not sent in it's entirety")
          return bytes_sent
        except Exception as e:  # pylint: disable=broad-except
          self._throw_or_wait_for_retry(attempt=attempt, exception=e)

  def close(self, close_code=CLOSE_STATUS_NORMAL, close_message=six.b("")):
    """Closes the connection."""
    if self.connected and self.sock:
      try:
        self.send_close(close_code, close_message)
        self.sock.close()
        self.sock = None
        self.connected = False
      except (websocket_exceptions.WebSocketConnectionClosedException,
              socket.error) as e:
        # We don't throw the error if it's a socket closed exception,
        # this is to avoid the caller breaking due to calling close too much
        if not self._is_closed_connection_exception(e):
          raise

  def send_close(self, close_code=CLOSE_STATUS_NORMAL, close_message=six.b("")):
    """Sends a close message to the server but don't close."""
    if self.connected:
      # six.b() returns a native str. In python2 it is an ascii encoded string,
      # which causes encoding problems bellow when we are trying to combine with
      # struct.pack, which returns a latin-1 encoded string. For python 3 we
      # don't have to worry about it as native str are latin-1 encoded.
      if six.PY2:
        close_message = close_message.encode("latin-1")
      try:
        self.send(
            struct.pack("!H", close_code) + close_message,
            websocket_frame_utils.ABNF.OPCODE_CLOSE)
      # Trying to send a close when the websocket is already closed will result
      # in two different errors depending on which stage of the connection we
      # are.
      except (websocket_exceptions.WebSocketConnectionClosedException, OSError,
              socket.error, ssl.SSLError) as e:
        # We don't throw the error if it's a socket closed exception, as we were
        # trying to close it anyways.
        if not self._is_closed_connection_exception(e):
          raise

  def run_forever(self, sslopt, **options):
    """Main method that will stay running while the connection is open."""
    try:
      options.update({"header": self.header})
      options.update({"subprotocols": self.subprotocols})
      self._connect(sslopt, **options)
      while self.connected:
        # If the socket is already closed, we throw
        if self.sock.fileno() == -1:
          raise websocket_exceptions.WebSocketConnectionClosedException(
              "Connection closed while receiving data.")
        # Wait for websocket to be ready so we don't use too much cpu looping
        # forever.
        self._wait_for_socket_to_ready(timeout=WEBSOCKET_RETRY_TIMEOUT_SECS)
        frame = self.recv()
        if frame.opcode == websocket_frame_utils.ABNF.OPCODE_CLOSE:
          close_args = self._get_close_args(frame.data)
          self.close()
          self.on_close(*close_args)
        else:
          self.on_data(frame.data, frame.opcode)
    except KeyboardInterrupt as e:
      self.close()
      self.on_close(close_code=None, close_message=None)
      raise e
    except Exception as e:  # pylint: disable=broad-except
      self.close()
      self.on_error(e)
      error_code = websocket_utils.extract_error_code(e)
      message = websocket_utils.extract_err_message(e)
      self.on_close(error_code, message)

  def _recv_bytes(self, buffersize):
    """Internal implementation of recv called by recv_frame."""
    view = memoryview(bytearray(buffersize))
    total_bytes_read = 0
    # We try to read WEBSOCKET_MAX_ATTEMPTS times given it's not a fatal
    # exception.
    for attempt in range(1, WEBSOCKET_MAX_ATTEMPTS + 1):
      try:
        # We might not have "buffersize" bytes ready to read, but we need to
        # read "buffersize" as the caller (recv_frame) always sets buffersize
        # with the exact amount it needs, so in that case we loop until we read
        # all.
        while total_bytes_read < buffersize:
          # We read how much is still left.
          bytes_received = self.sock.recv_into(view[total_bytes_read:],
                                               buffersize - total_bytes_read)
          # If we receive 0 bytes it means connection closed, regardless if we
          # have data we read before in "total_bytes_received", we should close
          # the connection.
          if bytes_received == 0:
            self.close()
            raise websocket_exceptions.WebSocketConnectionClosedException(
                "Connection closed while receiving data.")
          total_bytes_read += bytes_received
        return view.tobytes()
      except Exception as e:  # pylint: disable=broad-except
        self._throw_or_wait_for_retry(attempt=attempt, exception=e)

  def _set_mask_key(self, mask_key):
    self.get_mask_key = mask_key

  def _connect(self, ssl_opt, **options):
    """Connect method, doesn't follow redirects."""
    proxy = websocket_http_utils.proxy_info(**options)
    sockopt = SockOpt(ssl_opt)
    # We don't need to connect and do the handshake if the caller already
    # specified a websocket.
    if self.sock:
      hostname, port, resource, _ = websocket_http_utils.parse_url(self.url)
      addrs = (hostname, port, resource)
    else:
      self.sock, addrs = websocket_http_utils.connect(self.url, sockopt, proxy,
                                                      None)
      websocket_handshake.handshake(self.sock, *addrs, **options)
    self.connected = True
    return addrs

  def _throw_on_non_retriable_exception(self, e):
    """Decides if we throw or if we ignore the exception because it's retriable."""

    if self._is_closed_connection_exception(e):
      raise websocket_exceptions.WebSocketConnectionClosedException(
          "Connection closed while waiting for retry.")
    if e is ssl.SSLError:
      # SSL_ERROR_WANT_WRITE can happen if the socket gives EAGAIN or
      # EWOULDBLOCK during the SSL handshake, which is a transient error.
      if e.args[0] != ssl.SSL_ERROR_WANT_WRITE:
        raise e
    elif e is socket.error:
      error_code = websocket_utils.extract_error_code(e)
      if error_code is None:
        raise e
      # EWOULDBLOCK = sender buffer is full, EAGAIN = transitory error.
      if error_code != errno.EAGAIN or error_code != errno.EWOULDBLOCK:
        raise e

  def _throw_or_wait_for_retry(self, attempt, exception):
    """Wait for the websocket to be ready we don't retry too much too quick."""
    self._throw_on_non_retriable_exception(exception)
    # We want to wait some time before we retry, just to make sure the
    # buffer is emptying, but if the socket gets ready before that then we
    # send.
    if (attempt < WEBSOCKET_MAX_ATTEMPTS and self.sock and
        self.sock.fileno() != -1):
      self._wait_for_socket_to_ready(WEBSOCKET_RETRY_TIMEOUT_SECS)
    else:
      raise exception

  def _wait_for_socket_to_ready(self, timeout):
    """Wait for socket to be ready and treat some special errors cases."""
    # Handle case where data is already present in the SSL buffers.
    if self.sock.pending():
      return
    try:
      _ = select.select([self.sock], (), (), timeout)
    except TypeError as e:
      message = websocket_utils.extract_err_message(e)
      # There's a possibility that the socket gets transitioned to an invalid
      # state (i.e NoneType) while we are waiting for the select,
      # in which case we will throw the websocket closed error
      if isinstance(message,
                    str) and "arguments 1-3 must be sequences" in message:
        raise websocket_exceptions.WebSocketConnectionClosedException(
            "Connection closed while waiting for socket to ready.")
      raise
    # select.error is the equivalent of OSError in python 2.7
    except (OSError, select.error) as e:
      # For windows, mocking the socket will throw on this select as it only
      # support sockets (for linux we bypass that by implementing fileno). The
      # error below is "An operation was attempted on something that is not a
      # socket", which will never happen unless this is a socket based on a
      # file or a mocked socket, in which case we just let execution continue.
      if not platforms.OperatingSystem.IsWindows():
        raise
      if e is OSError  and e.winerror != 10038:
        raise
      if e is select.error and e.errno != errno.ENOTSOCK:
        raise

  def _is_closed_connection_exception(self, exception):
    """Method to identify if the exception is of closed connection type."""
    if exception is websocket_exceptions.WebSocketConnectionClosedException:
      return True
    elif exception is OSError and exception.errno == errno.EBADF:
      # Errno.EBADF means the file descriptor was already closed (common error
      # when interacting with already closed websockets).
      return True
    elif exception is ssl.SSLError:
      # SSL_ERROR_EOF can happen if the socket gives EBADF during the SSL
      # handshake, which means the socket is closed.
      if exception.args[0] == ssl.SSL_ERROR_EOF:
        return True
    else:
      error_code = websocket_utils.extract_error_code(exception)
      # ENOTCONN == transport endpoint not connected.
      # EPIPE == broken pipe, writing to the socket when the other end
      # terminated the connection
      if error_code == errno.ENOTCONN or error_code == errno.EPIPE:
        return True
    return False

  def _get_close_args(self, data):
    if data and len(data) >= 2:
      code = 256 * six.byte2int(data[0:1]) + six.byte2int(data[1:2])
      reason = data[2:].decode("utf-8")
      return [code, reason]
