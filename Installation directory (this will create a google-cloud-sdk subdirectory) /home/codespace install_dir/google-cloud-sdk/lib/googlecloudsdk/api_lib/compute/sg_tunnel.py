# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation for tunneling through Security Gateway."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import http.client
import logging
import select
import socket
import ssl
import threading

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils as iap_utils
from googlecloudsdk.api_lib.compute import sg_tunnel_utils as sg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log


MAX_BYTES_SOCKET_READ = 32768
RECV_TIMEOUT_SECONDS = 5
SEND_TIMEOUT_SECONDS = 5


class SGConnectionError(exceptions.Error):
  pass


class SecurityGatewayTunnel(object):
  """Creates the tunnel connection to the destination."""

  def __init__(
      self,
      target,
      access_token_callback,
      send_local_data_callback,
      close_local_connection_callback,
      ignore_certs=False,
  ):
    self._ignore_certs = ignore_certs

    self._get_access_token_callback = access_token_callback
    self._send_local_data_callback = send_local_data_callback
    self._close_local_connection_callback = close_local_connection_callback

    self._target = target

    self._sock = None
    self._sending_thread = None
    self._stopping = False

    # Used to unblock the sending thread immediately instead of waiting for a
    # timeout.
    self._spair, self._rpair = socket.socketpair()

  def __del__(self):
    self.Close()

  def InitiateConnection(self):
    """Starts a tunnel to the destination through Security Gateway."""

    sg_utils.ValidateParameters(self._target)
    ca_certs = iap_utils.CheckCACertsFile(self._ignore_certs)
    if self._ignore_certs:
      ssl_ctx = ssl._create_unverified_context(cafile=ca_certs)  # pylint: disable=protected-access
    else:
      ssl_ctx = ssl.create_default_context(cafile=ca_certs)

    proxy_host, proxy_port = sg_utils.GetProxyHostPort(
        self._target.url_override)

    conn = http.client.HTTPSConnection(
        proxy_host, proxy_port, context=ssl_ctx)
    dst_addr = '{}:{}'.format(self._target.host, self._target.port)
    headers = {}
    if callable(self._get_access_token_callback):
      headers['Proxy-Authorization'] = 'Bearer {}'.format(
          self._get_access_token_callback())
    headers['X-Resource-Key'] = sg_utils.GenerateSecurityGatewayResourcePath(
        self._target.project, self._target.region,
        self._target.security_gateway)
    log.debug('Sending headers: %s', headers)

    conn.request('CONNECT', dst_addr, headers=headers)
    resp = http.client.HTTPResponse(conn.sock, method='CONNECT', url=dst_addr)
    (_, code, reason) = resp._read_status()  # pylint: disable=protected-access
    if code != http.client.OK:
      log.error('Connection request status [%s] with reason: %s', code, reason)
      raise SGConnectionError(
          'Security Gateway failed to connect to destination url: ' + dst_addr)
    # This is the raw connection to the backend (no SSL wrapping).
    self._sock = conn.sock
    self._sock.setblocking(False)
    log.info('Connected to [%s]', dst_addr)

    self._sending_thread = threading.Thread(target=self._RunReceive)
    self._sending_thread.daemon = True
    self._sending_thread.start()

  def ShouldStop(self):
    """Signals to parent thread that this connection should be closed."""

    return self._stopping

  def Close(self):
    """Attempts to close both the local and tunnel connections."""
    if not self._stopping and self._sending_thread:
      # Attempt to close the sending thread first before continuing to prevent
      # any data races while closing the sockets.
      self._spair.send(b'0')
      self._sending_thread.join()

    self._close_local_connection_callback()

    if self._sock is None:
      return
    try:
      # It's recommended to explicitly call shutdown before calling close().
      # See https://docs.python.org/3/howto/sockets.html#disconnecting .
      self._sock.shutdown(socket.SHUT_RDWR)
      self._sock.close()
    except (socket.error, EnvironmentError) as e:
      log.debug('Failed to close connection to remote endpoint: [%s]', e)

  def Send(self, data):
    """Attempts to send all bytes in data to the remote endpoint."""
    data_len = len(data)
    if log.GetVerbosity() == logging.DEBUG:
      log.err.GetConsoleWriterStream().write(
          'DEBUG: SEND data_len [%d] data[:20] %r\n' % (data_len, data[:20]))
    sent_data = 0
    while sent_data < data_len:
      try:
        sent_data += self._sock.send(data)
      except (ssl.SSLWantWriteError, ssl.SSLWantReadError, BlockingIOError):
        select.select((), [self._sock], (), SEND_TIMEOUT_SECONDS)

  def _RunReceive(self):
    """Receives server data and sends to the local connection."""
    try:
      while not self._stopping:
        if not self._sock:
          break
        ready = [[self._sock]]
        if not self._sock.pending():
          ready = select.select([self._sock, self._rpair], (), (),
                                RECV_TIMEOUT_SECONDS)
        for s in ready[0]:
          if s is self._rpair:
            # Another thread is calling Close(), so this thread should stop.
            self._stopping = True
            break
          if s is self._sock:
            data, data_len = self._Read()
            if log.GetVerbosity() == logging.DEBUG:
              log.err.GetConsoleWriterStream().write(
                  'DEBUG: RECV data_len [%d] data[:20] %r\n' % (
                      len(data), data[:20]))
            if data_len == 0:
              log.debug('Remote endpoint [%s:%d] closed connection',
                        self._target.host, self._target.port)
              self._send_local_data_callback(b'')
              self._stopping = True
              break
            if data_len > 0:
              self._send_local_data_callback(data)
    finally:
      self._stopping = True

  def _Read(self):
    """Reads MAX_BYTES_SOCKET_READ bytes of data from the remote endpoint."""
    data = b''
    try:
      data = self._sock.recv(MAX_BYTES_SOCKET_READ)
    except (ssl.SSLWantWriteError, ssl.SSLWantReadError, BlockingIOError):
      return data, -1
    return data, len(data)
