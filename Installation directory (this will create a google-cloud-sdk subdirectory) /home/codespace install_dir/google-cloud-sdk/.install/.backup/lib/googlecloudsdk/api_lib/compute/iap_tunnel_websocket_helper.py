# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""WebSocket helper class for tunneling with Cloud IAP."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging
import ssl
import sys
import threading
import traceback

from googlecloudsdk.api_lib.compute import iap_tunnel_lightweight_websocket as iap_websocket
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils as utils
from googlecloudsdk.core import context_aware
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core.util import encoding
import six
import websocket

TUNNEL_CLOUDPROXY_ORIGIN = 'bot:iap-tunneler'


class WebSocketConnectionClosed(exceptions.Error):
  pass


class WebSocketInvalidOpcodeError(exceptions.Error):
  pass


class WebSocketSendError(exceptions.Error):
  pass


class IapTunnelWebSocketHelper(object):
  """Helper class for common operations on websocket and related metadata."""

  def __init__(self, url, headers, ignore_certs, proxy_info, on_data, on_close,
               should_use_new_websocket):
    self._on_data = on_data
    self._on_close = on_close
    self._proxy_info = proxy_info
    self._receiving_thread = None

    ca_certs = utils.CheckCACertsFile(ignore_certs)
    self._sslopt = {'cert_reqs': ssl.CERT_REQUIRED,
                    'ca_certs': ca_certs}
    if ignore_certs:
      self._sslopt['cert_reqs'] = ssl.CERT_NONE
      self._sslopt['check_hostname'] = False

    caa_config = context_aware.Config()
    if caa_config:
      cert_path = caa_config.encrypted_client_cert_path
      log.debug('Using client certificate %s', cert_path)
      self._sslopt['certfile'] = cert_path
      self._sslopt['password'] = caa_config.encrypted_client_cert_password

    # Disable most of random logging in websocket library itself except in DEBUG
    if log.GetVerbosity() != logging.DEBUG:
      logging.getLogger('websocket').setLevel(logging.CRITICAL)

    self._is_closed = False
    self._error_msg = ''
    self._should_use_new_websocket = should_use_new_websocket
    if self._should_use_new_websocket:
      self._websocket = iap_websocket.IapLightWeightWebsocket(
          url,
          header=headers,
          on_close=self._OnClose,
          on_data=self._OnData,
          on_error=self._OnError,
          subprotocols=[utils.SUBPROTOCOL_NAME])
    else:
      self._websocket = websocket.WebSocketApp(
          url,
          header=headers,
          on_close=self._OnClose,
          on_data=self._OnData,
          on_error=self._OnError,
          subprotocols=[utils.SUBPROTOCOL_NAME])

  def __del__(self):
    self.Close()

  def Close(self, msg=''):
    """Close the WebSocket."""
    if not self._is_closed:
      try:
        self._websocket.close()
      except:  # pylint: disable=bare-except
        pass
      if not self._error_msg:
        self._error_msg = msg
      self._is_closed = True

  def IsClosed(self):
    """Check to see if WebSocket has closed."""
    return (self._is_closed or
            (self._receiving_thread and not self._receiving_thread.is_alive()))

  def ErrorMsg(self):
    return self._error_msg

  def Send(self, send_data):
    """Send data on WebSocket connection."""
    try:
      # Needed since the gcloud logging methods will log to file regardless
      # of the verbosity level set by the user.
      if log.GetVerbosity() == logging.DEBUG:
        log.debug('SEND data_len [%d] send_data[:20] %r', len(send_data),
                  send_data[:20])
      self._websocket.send(send_data, opcode=websocket.ABNF.OPCODE_BINARY)
    except EnvironmentError:
      self.Close()
      raise
    except websocket.WebSocketConnectionClosedException:
      self.Close()
      raise WebSocketConnectionClosed()
    except Exception as e:  # pylint: disable=broad-except
      log.debug('Error during WebSocket send of Data message.', exc_info=True)
      # Convert websocket library errors and any others into one based on
      # exceptions.Error
      tb = sys.exc_info()[2]
      self.Close()
      exceptions.reraise(
          WebSocketSendError(traceback.format_exception_only(type(e), e),
                             tb=tb))

  def SendClose(self):
    """Send WebSocket Close message if possible."""
    # Save self._websocket.sock, because some other thread could set it to None
    # while this function is executing.
    if self._should_use_new_websocket:
      sock = self._websocket
    else:
      sock = self._websocket.sock

    if sock:
      log.debug('CLOSE')
      try:
        sock.send_close()
      except (EnvironmentError,
              websocket.WebSocketConnectionClosedException) as e:
        log.info('Unable to send WebSocket Close message [%s].',
                 six.text_type(e))
        self.Close()
      except:  # pylint: disable=bare-except
        log.info('Error during WebSocket send of Close message.', exc_info=True)
        self.Close()

  def StartReceivingThread(self):
    if not self._is_closed:
      self._receiving_thread = threading.Thread(
          target=self._ReceiveFromWebSocket)
      self._receiving_thread.daemon = True
      self._receiving_thread.start()

  def _OnClose(self, close_code, close_reason):
    """Callback for WebSocket Close messages."""

    if close_code is None and close_reason is None:
      # This indicates a local close event and not an actual Close message, call
      # Close() but skip the rest of the processing.
      self.Close()
      return

    close_msg = '%r: %r' % (close_code, close_reason)
    log.info('Received WebSocket Close message [%s].', close_msg)
    self.Close(msg=close_msg)

    if close_code == 4004:
      # This is a resumable error indicating that reauthentication is required.
      # Call self.Close() so that the class that owns us knows we're no longer
      # active, and can create a brand new IapTunnelWebSocketHelper for a
      # reconnect attempt. But avoid calling self._on_close() because that
      # indicates that the entire session is dead and a reconnect shouldn't be
      # attempted.
      return

    try:
      self._on_close()
    except (EnvironmentError, exceptions.Error):
      log.info('Error while processing Close message', exc_info=True)
      raise

  def _OnData(self, binary_data, opcode, unused_finished=0):
    """Callback for WebSocket Data messages."""
    # Needed since the gcloud logging methods will log to file regardless
    # of the verbosity level set by the user.
    if log.GetVerbosity() == logging.DEBUG:
      log.debug('RECV opcode [%r] data_len [%d] binary_data[:20] [%r]', opcode,
                len(binary_data), binary_data[:20])
    try:
      # Even though we will only be processing BINARY messages, a bug in the
      # underlying websocket library will report the last opcode in a
      # multi-frame message instead of the first opcode - so CONT instead of
      # BINARY.
      if opcode not in (websocket.ABNF.OPCODE_CONT,
                        websocket.ABNF.OPCODE_BINARY):
        raise WebSocketInvalidOpcodeError('Unexpected WebSocket opcode [%r].' %
                                          opcode)
      self._on_data(binary_data)
    except EnvironmentError as e:
      log.info('Error [%s] while sending to client.', six.text_type(e))
      self.Close()
      raise
    except:  # pylint: disable=bare-except
      log.info('Error while processing Data message.', exc_info=True)
      self.Close()
      raise

  def _OnError(self, exception_obj):
    # Do not call Close() from here as it may generate callbacks in some error
    # conditions that can create a feedback loop with this function.
    if not self._is_closed:
      log.debug('Error during WebSocket processing.', exc_info=True)
      log.info('Error during WebSocket processing:\n' +
               ''.join(traceback.format_exception_only(type(exception_obj),
                                                       exception_obj)))
      self._error_msg = six.text_type(exception_obj)

  def _ReceiveFromWebSocket(self):
    """Receive data from WebSocket connection."""
    try:
      if self._proxy_info:
        http_proxy_auth = None
        if self._proxy_info.proxy_user or self._proxy_info.proxy_pass:
          # The websocket library ultimately expects the proxy username and
          # password to be strings, unlike httplib2's ProxyInfo which encodes
          # these as bytes. So we need to ensure they're decoded here before
          # calling run_forever.
          http_proxy_auth = (encoding.Decode(self._proxy_info.proxy_user),
                             encoding.Decode(self._proxy_info.proxy_pass))
        self._websocket.run_forever(
            origin=TUNNEL_CLOUDPROXY_ORIGIN, sslopt=self._sslopt,
            http_proxy_host=self._proxy_info.proxy_host,
            http_proxy_port=self._proxy_info.proxy_port,
            http_proxy_auth=http_proxy_auth)
      else:
        self._websocket.run_forever(origin=TUNNEL_CLOUDPROXY_ORIGIN,
                                    sslopt=self._sslopt)
    except:  # pylint: disable=bare-except
      try:
        log.info('Error while receiving from WebSocket.', exc_info=True)
      except:
        # This is a daemon thread, so it could be running while the interpreter
        # is exiting, so logging could fail. At that point the only thing to do
        # is ignore the exception. Ideally we would make this a non-daemon
        # thread.
        pass
    try:
      self.Close()
    except:  # pylint: disable=bare-except
      try:
        log.info('Error while closing in receiving thread.', exc_info=True)
      except:
        pass
