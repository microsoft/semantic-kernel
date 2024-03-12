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

"""WebSocket connection class for tunneling with Cloud IAP."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections
import logging
import threading
import time

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_helper as helper
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils as utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import retry
import six
from six.moves import queue

MAX_WEBSOCKET_SEND_WAIT_TIME_SEC = 2
MAX_WEBSOCKET_OPEN_WAIT_TIME_SEC = 60
MAX_RECONNECT_SLEEP_TIME_MS = 20 * 1000  # 20 seconds
MAX_RECONNECT_WAIT_TIME_MS = 15 * 60 * 1000  # 15 minutes
MAX_UNSENT_QUEUE_LENGTH = 5
ALL_DATA_SENT_WAIT_TIME_SEC = 10
RECONNECT_INITIAL_SLEEP_MS = 1500


class SendAckNotification(exceptions.Error):
  pass


class ConnectionCreationError(exceptions.Error):
  pass


class ConnectionReconnectTimeout(exceptions.Error):
  pass


class StoppingError(exceptions.Error):
  pass


class SubprotocolEarlyAckError(exceptions.Error):
  pass


class SubprotocolEarlyDataError(exceptions.Error):
  pass


class SubprotocolExtraConnectSuccessSid(exceptions.Error):
  pass


class SubprotocolExtraReconnectSuccessAck(exceptions.Error):
  pass


class SubprotocolInvalidAckError(exceptions.Error):
  pass


class SubprotocolOutOfOrderAckError(exceptions.Error):
  pass


class IapTunnelWebSocket(object):
  """Cloud IAP WebSocket class for tunnelling connections.

  It takes in local data (via Send()) which it sends over the websocket. It
  takes data from the websocket and gives it to data_handler_callback.
  """

  def __init__(self, tunnel_target, get_access_token_callback,
               data_handler_callback, close_handler_callback,
               user_agent, ignore_certs=False):
    self._tunnel_target = tunnel_target
    self._get_access_token_callback = get_access_token_callback
    self._data_handler_callback = data_handler_callback
    self._close_handler_callback = close_handler_callback
    self._ignore_certs = ignore_certs
    self._user_agent = user_agent

    self._websocket_helper = None
    self._connect_msg_received = False
    self._connection_sid = None
    self._stopping = False
    self._close_message_sent = False
    self._send_and_reconnect_thread = None
    # Indicates if the local input gave an EOF.
    self._input_eof = False
    # Indicates that after getting a local input EOF, we have send all previous
    # local data over the websocket.
    self._sent_all = threading.Event()
    # Used to prevent multiple Ack requests from filling the _unsent_data queue.
    self._cant_send_ack = threading.Event()

    self._total_bytes_confirmed = 0
    self._total_bytes_received = 0
    self._total_bytes_received_and_acked = 0
    self._unsent_data = queue.Queue(maxsize=MAX_UNSENT_QUEUE_LENGTH)
    self._unconfirmed_data = collections.deque()
    # This queue is used to store data that was sent but didn't get acked by
    # the server. We will use it to resend the data.
    self._data_to_resend = queue.Queue()

  def __del__(self):
    if self._websocket_helper:
      self._websocket_helper.Close()

  def Close(self):
    """Close down local connection and WebSocket connection."""
    self._stopping = True
    # We unblock the send thread by putting a connectionAborted error in the
    # queue.
    self._unsent_data.put(StoppingError)
    try:
      self._close_handler_callback()
    except:  # pylint: disable=bare-except
      pass
    if self._websocket_helper:
      if not self._close_message_sent:
        self._websocket_helper.SendClose()
        self._close_message_sent = True
      self._websocket_helper.Close()

  def InitiateConnection(self):
    """Initiate the WebSocket connection."""
    utils.CheckPythonVersion(self._ignore_certs)
    utils.ValidateParameters(self._tunnel_target)

    self._StartNewWebSocket()
    self._WaitForOpenOrRaiseError()
    self._send_and_reconnect_thread = threading.Thread(
        target=self._SendDataAndReconnectWebSocket)
    self._send_and_reconnect_thread.daemon = True
    self._send_and_reconnect_thread.start()

  def Send(self, bytes_to_send):
    """Send bytes over WebSocket connection.

    Args:
      bytes_to_send: The bytes to send. Must not be empty.

    Raises:
      ConnectionReconnectTimeout: If something is preventing data from being
        sent.
    """
    while bytes_to_send:
      first_to_send = bytes_to_send[:utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE]
      bytes_to_send = bytes_to_send[utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE:]
      if first_to_send:
        self._EnqueueBytesWithWaitForReconnect(first_to_send)

  def LocalEOF(self):
    """Indicate that the local input gave an EOF.

    This should always be called after finishing sending data, as to stop the
    sending thread.
    """

    self._unsent_data.put(EOFError)

  def WaitForAllSent(self):
    """Wait until all local data has been sent on the websocket.

    Blocks until either all data from Send() has been sent, or it times out
    waiting. Once true, always returns true. Even if this returns true, a
    reconnect could occur causing previously sent data to be resent. Must only
    be called after an EOF has been given to Send().

    Returns:
      True on success, False on timeout.
    """
    # If we didn't have any wait time, python2 would ignore ctrl-c when in
    # --listen-on-stdin mode. With a wait time, it pays attention to ctrl-c.
    # When doing ssh, the inner gcloud will continue behind the scenes until
    # either all data is sent or this times out. We don't want a weird hidden
    # gcloud staying around like that for a long time (even in the case of a
    # write block), so the wait time isn't very long.
    return self._sent_all.wait(ALL_DATA_SENT_WAIT_TIME_SEC)

  def _AttemptReconnect(self, reconnect_func):
    """Attempt to reconnect with a new WebSocket."""

    r = retry.Retryer(max_wait_ms=MAX_RECONNECT_WAIT_TIME_MS,
                      exponential_sleep_multiplier=1.1,
                      wait_ceiling_ms=MAX_RECONNECT_SLEEP_TIME_MS)
    try:
      r.RetryOnException(func=reconnect_func,
                         sleep_ms=RECONNECT_INITIAL_SLEEP_MS)
    except retry.RetryException:
      log.warning('Unable to reconnect within [%d] ms',
                  MAX_RECONNECT_WAIT_TIME_MS, exc_info=True)
      self._StopConnectionAsync()

  def _EnqueueBytesWithWaitForReconnect(self, bytes_to_send):
    """Add bytes to the queue; block waiting for reconnect if queue is full.

    Args:
      bytes_to_send: The local bytes to send over the websocket. At most
        utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE.

    Raises:
      ConnectionReconnectTimeout: If something is preventing data from being
        sent.
      ConnectionCreationError: If the connection was closed and no more
        reconnect retries will be performed.
    """

    end_time = time.time() + MAX_RECONNECT_WAIT_TIME_MS / 1000.0
    while time.time() < end_time and not self._stopping:
      try:
        # Blocks for a few seconds, to avoid empty loops. The only reason the
        # timeout is short, is so we notice when the socket was closed. A longer
        # timeout may make us miss that.
        self._unsent_data.put(bytes_to_send, timeout=
                              MAX_WEBSOCKET_SEND_WAIT_TIME_SEC)

        # Needed since the gcloud logging methods will log to file regardless
        # of the verbosity level set by the user.
        if log.GetVerbosity() == logging.DEBUG:
          log.debug('ENQUEUED data_len [%d] bytes_to_send[:20] [%r]',
                    len(bytes_to_send), bytes_to_send[:20])
        return
      except queue.Full:
        # Throws Full if timeout was reached
        pass
    # If we got here it means we either closed the socket, or couldn't reconnect
    if self._stopping:
      raise ConnectionCreationError('Unexpected error while reconnecting.'
                                    ' Check logs for more details.')
    raise ConnectionReconnectTimeout()

  def _HasConnected(self):
    """Returns true if we received a connect message."""
    return self._connect_msg_received

  def _IsClosed(self):
    return ((self._websocket_helper and self._websocket_helper.IsClosed()) or
            (self._send_and_reconnect_thread and
             not self._send_and_reconnect_thread.is_alive()))

  def _StartNewWebSocket(self):
    """Start a new WebSocket and thread to listen for incoming data."""
    headers = ['User-Agent: ' + self._user_agent]
    request_reason = properties.VALUES.core.request_reason.Get()
    if request_reason:
      headers += ['X-Goog-Request-Reason: ' + request_reason]

    if self._get_access_token_callback:
      headers += ['Authorization: Bearer ' + self._get_access_token_callback()]

    log.debug('Using new websocket library')

    if self._connection_sid:
      url = utils.CreateWebSocketReconnectUrl(
          self._tunnel_target,
          self._connection_sid,
          self._total_bytes_received,
          should_use_new_websocket=True)
      log.info('Reconnecting with URL [%r]', url)
    else:
      url = utils.CreateWebSocketConnectUrl(
          self._tunnel_target, should_use_new_websocket=True)
      log.info('Connecting with URL [%r]', url)

    self._connect_msg_received = False

    self._websocket_helper = helper.IapTunnelWebSocketHelper(
        url,
        headers,
        self._ignore_certs,
        self._tunnel_target.proxy_info,
        self._OnData,
        self._OnClose,
        should_use_new_websocket=True)
    self._websocket_helper.StartReceivingThread()

  def _SendAck(self):
    """Send an ACK back to server."""
    if self._total_bytes_received > self._total_bytes_received_and_acked:
      bytes_received = self._total_bytes_received
      try:
        ack_data = utils.CreateSubprotocolAckFrame(bytes_received)
        self._websocket_helper.Send(ack_data)
        self._total_bytes_received_and_acked = bytes_received
      except helper.WebSocketConnectionClosed:
        # We throw here so the caller can reconnect
        raise
      except EnvironmentError as e:
        log.info('Unable to send WebSocket ack [%s]', six.text_type(e))
      except:  # pylint: disable=bare-except
        if not self._IsClosed():
          log.info('Error while attempting to ack [%d] bytes', bytes_received,
                   exc_info=True)
        else:
          raise
      finally:
        self._cant_send_ack.clear()

  def _MaybeSendAck(self):
    """Decide if an ACK should be sent back to the server."""
    if self._cant_send_ack.is_set():
      return
    # Using these extra variables because the line is too long otherwise
    total_bytes = self._total_bytes_received
    bytes_recv_and_ackd = self._total_bytes_received_and_acked
    window_size = utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE
    # Following this doc: go/delayed-ack-message the recommended is to wait
    # at least 2x the window size before we send ack messages,
    # to avoid wasting cpu cycles on both ends
    if total_bytes - bytes_recv_and_ackd > 2 * window_size:
      self._cant_send_ack.set()
      # Place into queue instead of calling _SendAck() to ensure only the
      # sending thread will send the data.
      self._unsent_data.put(SendAckNotification)

  def _SendDataAndReconnectWebSocket(self):
    """Main function for send_and_reconnect_thread."""
    def SendData():
      if not self._stopping:
        self._SendQueuedData()
        self._SendAck()

    def Reconnect():
      if not self._stopping:
        self._StartNewWebSocket()
        self._WaitForOpenOrRaiseError()

    try:
      while not self._stopping:
        try:
          SendData()
        except Exception as e:  # pylint: disable=broad-except
          log.debug('Error while sending data, trying to reconnect [%s]',
                    six.text_type(e))
          self._AttemptReconnect(Reconnect)
    finally:
      self.Close()

  def _SendQueuedData(self):
    """Send data that is sitting in the unsent data queue."""
    try:
      while not self._stopping:
        self._MaybeSendAck()
        # This is a blocking call in case the queue is empty. The timeout is
        # there so we can unblock and send acks if no message arrive after a few
        # seconds
        try:
          if not self._data_to_resend.empty():
            data = self._data_to_resend.get()
          else:
            # TODO(b/279928850): Possibly remove timeout.
            data = self._unsent_data.get(timeout=
                                         MAX_WEBSOCKET_SEND_WAIT_TIME_SEC)
        except queue.Empty:
          # Throws empty if timeout reached
          if self._IsClosed():
            raise helper.WebSocketConnectionClosed
          break

        # When EOF is reached, EOF error will be put in the queue.
        # When close is called. ConnectionAborted error is put in the queue.
        if data is EOFError or data is StoppingError:
          # Now we tell the thread to quit as there's no more data to send.
          self._stopping = True
          if data is EOFError:
            self._input_eof = True
          break

        if data is SendAckNotification:
          self._SendAck()
          continue

        # We need to append to _unconfirmed_data before calling Send(), because
        # otherwise we could receive the ack for the sent data before we do the
        # append, which we would interpret as an invalid ack. This does mean
        # there's a small window of time where we'll accept acks of data that
        # hasn't truly been sent if a badly behaving server sends such acks, but
        # that's not really a problem, because we'll behave identically to as if
        # the ack was received after the data was sent (so no data or control
        # flow corruption), and we don't have a goal of giving an error every
        # time the server misbehaves.
        # It's also important in case we take the data out of the unset data
        # queue but we can't send it up because the connection was closed. By
        # adding it to unconfirmed, we will resend it later.
        self._unconfirmed_data.append(data)

        send_data = utils.CreateSubprotocolDataFrame(data)
        self._websocket_helper.Send(send_data)
    finally:
      if (self._input_eof and self._data_to_resend.empty() and
          self._unsent_data.empty()):
        self._sent_all.set()

  def _StopConnectionAsync(self):
    self._stopping = True

  def _WaitForOpenOrRaiseError(self):
    """Wait for WebSocket open confirmation or any error condition."""
    for _ in range(MAX_WEBSOCKET_OPEN_WAIT_TIME_SEC * 100):
      if self._IsClosed():
        break
      if self._HasConnected():
        return
      time.sleep(0.01)

    if (self._websocket_helper and self._websocket_helper.IsClosed() and
        self._websocket_helper.ErrorMsg()):
      extra_msg = ''
      # Error messages like 'Handshake status 400' or 'Handshake status 404'
      # may often indicate missing permissions.
      if self._websocket_helper.ErrorMsg().startswith('Handshake status 40'):
        extra_msg = ' (May be due to missing permissions)'
      # Error messages starting with '4003' indicate that either nothing is
      # listening on the port, or there is an issue with the firewall.
      elif self._websocket_helper.ErrorMsg().startswith('4003'):
        extra_msg = ' (Failed to connect to port %d)' % self._tunnel_target.port
      error_msg = ('Error while connecting [%s].%s' %
                   (self._websocket_helper.ErrorMsg(), extra_msg))
      raise ConnectionCreationError(error_msg)

    raise ConnectionCreationError('Unexpected error while connecting. Check '
                                  'logs for more details.')

  def _OnClose(self):
    self._StopConnectionAsync()

  def _OnData(self, binary_data):
    """Receive a single message from the server."""
    tag, bytes_left = utils.ExtractSubprotocolTag(binary_data)
    # In order of decreasing usage during connection:
    if tag == utils.SUBPROTOCOL_TAG_DATA:
      self._HandleSubprotocolData(bytes_left)
    elif tag == utils.SUBPROTOCOL_TAG_ACK:
      self._HandleSubprotocolAck(bytes_left)
    elif tag == utils.SUBPROTOCOL_TAG_CONNECT_SUCCESS_SID:
      self._HandleSubprotocolConnectSuccessSid(bytes_left)
    elif tag == utils.SUBPROTOCOL_TAG_RECONNECT_SUCCESS_ACK:
      self._HandleSubprotocolReconnectSuccessAck(bytes_left)
    else:
      log.debug('Unsupported subprotocol tag [%r], discarding the message', tag)

  def _HandleSubprotocolAck(self, binary_data):
    """Handle Subprotocol ACK Frame."""
    if not self._HasConnected():
      self._StopConnectionAsync()
      raise SubprotocolEarlyAckError('Received ACK before connected.')

    bytes_confirmed, bytes_left = utils.ExtractSubprotocolAck(binary_data)
    self._ConfirmData(bytes_confirmed)
    if bytes_left:
      log.debug('Discarding [%d] extra bytes after processing ACK',
                len(bytes_left))

  def _HandleSubprotocolConnectSuccessSid(self, binary_data):
    """Handle Subprotocol CONNECT_SUCCESS_SID Frame."""
    if self._HasConnected():
      self._StopConnectionAsync()
      raise SubprotocolExtraConnectSuccessSid(
          'Received CONNECT_SUCCESS_SID after already connected.')

    data, bytes_left = utils.ExtractSubprotocolConnectSuccessSid(binary_data)
    self._connection_sid = data
    self._connect_msg_received = True
    if bytes_left:
      log.debug(
          'Discarding [%d] extra bytes after processing CONNECT_SUCCESS_SID',
          len(bytes_left))

  def _AddUnconfirmedDataBackToTheQueue(self):
    # This data will be sent first
    for data in self._unconfirmed_data:
      self._data_to_resend.put(data)
    self._unconfirmed_data = collections.deque()

  def _HandleSubprotocolReconnectSuccessAck(self, binary_data):
    """Handle Subprotocol RECONNECT_SUCCESS_ACK Frame."""
    if self._HasConnected():
      self._StopConnectionAsync()
      raise SubprotocolExtraReconnectSuccessAck(
          'Received RECONNECT_SUCCESS_ACK after already connected.')

    bytes_confirmed, bytes_left = (
        utils.ExtractSubprotocolReconnectSuccessAck(binary_data))
    bytes_being_confirmed = bytes_confirmed - self._total_bytes_confirmed
    self._ConfirmData(bytes_confirmed)
    log.info(
        'Reconnecting: confirming [%d] bytes and resending [%d] messages.',
        bytes_being_confirmed, len(self._unconfirmed_data))
    self._AddUnconfirmedDataBackToTheQueue()
    self._connect_msg_received = True
    if bytes_left:
      log.debug(
          'Discarding [%d] extra bytes after processing RECONNECT_SUCCESS_ACK',
          len(bytes_left))

  def _HandleSubprotocolData(self, binary_data):
    """Handle Subprotocol DATA Frame."""
    if not self._HasConnected():
      self._StopConnectionAsync()
      raise SubprotocolEarlyDataError('Received DATA before connected.')

    data, bytes_left = utils.ExtractSubprotocolData(binary_data)
    self._total_bytes_received += len(data)
    self._MaybeSendAck()
    try:
      self._data_handler_callback(data)
    except:  # pylint: disable=bare-except
      self._StopConnectionAsync()
      raise
    if bytes_left:
      log.debug('Discarding [%d] extra bytes after processing DATA',
                len(bytes_left))

  def _ConfirmData(self, bytes_confirmed):
    """Discard data that has been confirmed via ACKs received from server."""
    if bytes_confirmed < self._total_bytes_confirmed:
      self._StopConnectionAsync()
      raise SubprotocolOutOfOrderAckError(
          'Received out-of-order Ack for [%d] bytes.' % bytes_confirmed)

    bytes_to_confirm = bytes_confirmed - self._total_bytes_confirmed
    while bytes_to_confirm and self._unconfirmed_data:
      data_chunk = self._unconfirmed_data.popleft()
      if len(data_chunk) > bytes_to_confirm:
        self._unconfirmed_data.appendleft(data_chunk[bytes_to_confirm:])
        self._total_bytes_confirmed += bytes_to_confirm
      else:
        self._total_bytes_confirmed += len(data_chunk)
      bytes_to_confirm = bytes_confirmed - self._total_bytes_confirmed

    if bytes_to_confirm:
      self._StopConnectionAsync()
      raise SubprotocolInvalidAckError(
          'Bytes confirmed [%r] were larger than bytes sent [%r].' %
          (bytes_confirmed, self._total_bytes_confirmed))
