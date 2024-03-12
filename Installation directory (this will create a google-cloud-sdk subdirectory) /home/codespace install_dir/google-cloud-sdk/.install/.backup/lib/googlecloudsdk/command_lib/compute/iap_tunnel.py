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

"""Tunnel TCP traffic over Cloud IAP WebSocket connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import ctypes
import errno
import functools
import gc
import io
import os
import select
import socket
import sys
import threading

from googlecloudsdk.api_lib.compute import iap_tunnel_websocket
from googlecloudsdk.api_lib.compute import iap_tunnel_websocket_utils as utils
from googlecloudsdk.api_lib.compute import sg_tunnel
from googlecloudsdk.api_lib.compute import sg_tunnel_utils as sg_utils
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import http_proxy
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import transport
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import store
from googlecloudsdk.core.util import files
from googlecloudsdk.core.util import platforms
import portpicker
import six
from six.moves import queue


if not platforms.OperatingSystem.IsWindows():
  import fcntl  # pylint: disable=g-import-not-at-top
else:
  from ctypes import wintypes  # pylint: disable=g-import-not-at-top

READ_FROM_STDIN_TIMEOUT_SECS = 3


class LocalPortUnavailableError(exceptions.Error):
  pass


class UnableToOpenPortError(exceptions.Error):
  pass


def _AddBaseArgs(parser):
  parser.add_argument(
      '--iap-tunnel-url-override',
      hidden=True,
      help=('Allows for overriding the connection endpoint for integration '
            'testing.'))
  parser.add_argument(
      '--iap-tunnel-insecure-disable-websocket-cert-check',
      default=False,
      action='store_true',
      hidden=True,
      help='Disables checking certificates on the WebSocket connection.')


def AddSshTunnelArgs(parser, tunnel_through_iap_scope):
  _AddBaseArgs(parser)
  tunnel_through_iap_scope.add_argument(
      '--tunnel-through-iap',
      action='store_true',
      help="""\
      Tunnel the ssh connection through Cloud Identity-Aware Proxy for TCP
      forwarding.

      To learn more, see the
      [IAP for TCP forwarding documentation](https://cloud.google.com/iap/docs/tcp-forwarding-overview).
      """)


def AddHostBasedTunnelArgs(parser, support_security_gateway=False):
  """Add the arguments for supporting host-based connections."""

  group = parser.add_argument_group()
  group.add_argument(
      '--region',
      default=None,
      required=True,
      help=('Configures the region to use when connecting via IP address or '
            'FQDN.'))

  if support_security_gateway:
    group_mutex = group.add_argument_group(mutex=True)
    AddSecurityGatewayTunnelArgs(group_mutex.add_argument_group(hidden=True))
    group = group_mutex.add_argument_group()
  AddOnPremTunnelArgs(group)


def AddOnPremTunnelArgs(parser):
  """Add the arguments for supporting IP/FQDN-based tunnels."""
  parser.add_argument(
      '--network',
      default=None,
      required=True,
      help=(
          'Configures the VPC network to use when connecting via IP address or '
          'FQDN.'))
  # TODO(b/196572980): Make dest-group required in beta/GA.
  parser.add_argument(
      '--dest-group',
      default=None,
      required=False,
      help=('Configures the destination group to use when connecting via IP '
            'address or FQDN.'))


def AddSecurityGatewayTunnelArgs(parser):
  """Add arguments for the Security Gateway path."""
  parser.add_argument(
      '--security-gateway',
      default=None,
      required=True,
      help='Configure the security gateway resource for connecting.')


def AddProxyServerHelperArgs(parser):
  _AddBaseArgs(parser)


def CreateSshTunnelArgs(args, track, instance_ref, external_interface):
  """Construct an SshTunnelArgs from command line args and values.

  Args:
    args: The parsed commandline arguments. May or may not have had
      AddSshTunnelArgs called.
    track: ReleaseTrack, The currently running release track.
    instance_ref: The target instance reference object.
    external_interface: The external interface of target resource object, if
      available, otherwise None.
  Returns:
    SshTunnelArgs or None if IAP Tunnel is disabled.
  """
  # If tunneling through IAP is not available, then abort.
  if not hasattr(args, 'tunnel_through_iap'):
    return None

  # If set to connect directly to private IP address, then abort.
  if getattr(args, 'internal_ip', False):
    return None

  if args.IsSpecified('tunnel_through_iap'):
    # If IAP tunneling is explicitly disabled, then abort.
    if not args.tunnel_through_iap:
      return None
  else:
    # If no external interface is available, then default to using IAP
    # tunneling and continue with code below.  Otherwise, abort.
    if external_interface:
      return None
    log.status.Print('External IP address was not found; defaulting to using '
                     'IAP tunneling.')

  res = SshTunnelArgs()

  res.track = track.prefix
  res.project = instance_ref.project
  res.zone = instance_ref.zone
  res.instance = instance_ref.instance

  _AddPassThroughArgs(args, res)

  return res


def CreateOnPremSshTunnelArgs(args, track, host):
  """Construct an SshTunnelArgs from command line args and values for on-prem.

  Args:
    args: The parsed commandline arguments. May or may not have had
      AddSshTunnelArgs called.
    track: ReleaseTrack, The currently running release track.
    host: The target IP address or FQDN.
  Returns:
    SshTunnelArgs.
  """
  res = SshTunnelArgs()

  res.track = track.prefix
  res.project = properties.VALUES.core.project.GetOrFail()
  res.region = args.region
  res.network = args.network
  res.instance = host

  _AddPassThroughArgs(args, res)

  return res


def _AddPassThroughArgs(args, ssh_tunnel_args):
  """Adds any passthrough args to the SshTunnelArgs.

  Args:
    args: The parsed commandline arguments. May or may not have had
      AddSshTunnelArgs called.
    ssh_tunnel_args: SshTunnelArgs, The SSH tunnel args to update.
  """
  if args.IsSpecified('iap_tunnel_url_override'):
    ssh_tunnel_args.pass_through_args.append(
        '--iap-tunnel-url-override=' + args.iap_tunnel_url_override)
  if args.iap_tunnel_insecure_disable_websocket_cert_check:
    ssh_tunnel_args.pass_through_args.append(
        '--iap-tunnel-insecure-disable-websocket-cert-check')
  if args.IsKnownAndSpecified('dest_group'):
    ssh_tunnel_args.pass_through_args.append('--dest-group=' + args.dest_group)


class SshTunnelArgs(object):
  """A class to hold some options for IAP Tunnel SSH/SCP.

  Attributes:
    track: str/None, the prefix of the track for the inner gcloud.
    project: str, the project id (string with dashes).
    zone: str, the zone name.
    instance: str, the instance name (or IP or FQDN for on-prem).
    region: str, the region name (on-prem only).
    network: str, the network name (on-prem only).
    pass_through_args: [str], additional args to be passed to the inner gcloud.
  """

  def __init__(self):
    self.track = None
    self.project = ''
    self.zone = ''
    self.instance = ''
    self.region = ''
    self.network = ''
    self.pass_through_args = []

  def _Members(self):
    return (
        self.track,
        self.project,
        self.zone,
        self.instance,
        self.region,
        self.network,
        self.pass_through_args,
    )

  def __eq__(self, other):
    # pylint: disable=protected-access
    return self._Members() == other._Members()

  def __ne__(self, other):
    return not self == other

  def __repr__(self):
    return 'SshTunnelArgs<%r>' % (self._Members(),)


def DetermineLocalPort(port_arg=0):
  if not port_arg:
    port_arg = portpicker.pick_unused_port()
  if not portpicker.is_port_free(port_arg):
    raise LocalPortUnavailableError('Local port [%d] is not available.' %
                                    port_arg)
  return port_arg


def _CloseLocalConnectionCallback(local_conn):
  """Callback function to close the local connection, if any."""
  # For test WebSocket connections, there is not a local socket connection.
  if local_conn:
    try:
      # Calling shutdown() first is needed to promptly notify the process on
      # the other side of the connection that it is closing. This allows that
      # other process, whether over TCP or stdin, to promptly terminate rather
      # that waiting for the next time that the process tries to send data.
      local_conn.shutdown(socket.SHUT_RDWR)
    except EnvironmentError:
      pass
    try:
      local_conn.close()
    except EnvironmentError:
      pass


def _GetAccessTokenCallback(credentials):
  """Callback function to refresh credentials and return access token."""
  if not credentials:
    return None
  log.debug('credentials type for _GetAccessTokenCallback is [%s].',
            six.text_type(credentials))
  store.RefreshIfAlmostExpire(credentials)

  if creds.IsGoogleAuthCredentials(credentials):
    return credentials.token
  else:
    return credentials.access_token


def _SendLocalDataCallback(local_conn, data):
  # For test WebSocket connections, there is not a local socket connection.
  if local_conn:
    local_conn.send(data)


def _OpenLocalTcpSockets(local_host, local_port):
  """Attempt to open a local socket(s) listening on specified host and port."""
  open_sockets = []
  for res in socket.getaddrinfo(
      local_host, local_port, socket.AF_UNSPEC, socket.SOCK_STREAM, 0,
      socket.AI_PASSIVE):
    af, socktype, proto, unused_canonname, sock_addr = res
    try:
      s = socket.socket(af, socktype, proto)
    except socket.error:
      continue
    try:
      if not platforms.OperatingSystem.IsWindows():
        # This allows us to restart quickly on the same port. See b/213858080.
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind(sock_addr)
      # Keep it large enough so it can handle burst of tunnel requests.
      s.listen(128)
      open_sockets.append(s)
    except EnvironmentError:
      try:
        s.close()
      except socket.error:
        pass

  if open_sockets:
    return open_sockets

  raise UnableToOpenPortError('Unable to open socket on port [%d].' %
                              local_port)


class _StdinSocket(object):
  """A wrapper around stdin/out that allows it to be treated like a socket.

  Does not implement all socket functions. And of the ones implemented, not all
  arguments/flags are supported. Once created, stdin should never be accessed by
  anything else.
  """

  class _StdinSocketMessage(object):
    """A class to wrap messages coming to the stdin socket for windows systems."""

    def __init__(self, messageType, data):
      self._type = messageType
      self._data = data

    def GetData(self):
      return self._data

    def GetType(self):
      return self._type

  class _EOFError(Exception):
    pass

  class _StdinClosedMessageType():
    pass

  class _ExceptionMessageType():
    pass

  class _DataMessageType():
    pass

  def __init__(self):

    self._stdin_closed = False
    # Maximum number of bytes the thread should read.
    self._bufsize = utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE
    if platforms.OperatingSystem.IsWindows():
      # We will use this thread-safe queue to communicate with the input
      # reading thread.
      self._message_queue = queue.Queue()
      self._reading_thread = threading.Thread(
          target=self._ReadFromStdinAndEnqueueMessageWindows)
      self._reading_thread.daemon = True
      self._reading_thread.start()
    else:
      self._old_flags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
      # Set up non-blocking mode to avoid getting stuck on read.
      fcntl.fcntl(sys.stdin, fcntl.F_SETFL, self._old_flags | os.O_NONBLOCK)

  def __del__(self):
    # We need to restore the flags, even when gcloud exits, nonblocking stdin
    # causes weird problems in that terminal, such as cat stops working.
    # This will happen if gcloud is running with stdin mode directly, then
    # killed between the set nonblocking and the restore. The user could fix
    # that by running bash and exiting it, or just closing the terminal.
    # If gcloud is running as an ssh ProxyCommand this problem doesn't happen.
    if not platforms.OperatingSystem.IsWindows():
      fcntl.fcntl(sys.stdin, fcntl.F_SETFL, self._old_flags)

  def send(self, data):  # pylint: disable=invalid-name
    files.WriteStreamBytes(sys.stdout, data)
    if not six.PY2:
      # WriteStreamBytes flushes python2 but not python3. Perhaps it should
      # be modified to also flush python3.
      sys.stdout.buffer.flush()
    return len(data)

  def recv(self, bufsize):  # pylint: disable=invalid-name
    """Receives data from stdin.

    Blocks until at least 1 byte is available.
    On Unix (but not Windows) this is unblocked by close() and shutdown(RD).
    On all platforms a signal handler triggering an exception will unblock this.
    This cannot be called by multiple threads at the same time.
    This function performs cleanups before returning, so killing gcloud while
    this is running should be avoided. Specifically RaisesKeyboardInterrupt
    should be in effect so that ctrl-c causes a clean exit with an exception
    instead of triggering gcloud's default os.kill().

    Args:
      bufsize: The maximum number of bytes to receive. Must be positive.
    Returns:
      The bytes received. EOF is indicated by b''.
    Raises:
      IOError: On low level errors.
    """

    if platforms.OperatingSystem.IsWindows():
      return self._RecvWindows(bufsize)
    else:
      return self._RecvUnix(bufsize)

  def close(self):  # pylint: disable=invalid-name
    # Closing stdin doesn't help, because it doesn't unblock read() calls.
    # Also it causes problems, such as segfaulting in python2 and blocking in
    # python3.
    self.shutdown(socket.SHUT_RD)

  def shutdown(self, how):  # pylint: disable=invalid-name
    # Shutting down read only (SHUT_RD)
    if how in (socket.SHUT_RDWR, socket.SHUT_RD):
      self._stdin_closed = True

      # For windows we will unblock the thread early
      if platforms.OperatingSystem.IsWindows():
        # We queue the message so that the recv loop can abort
        msg = self._StdinSocketMessage(self._StdinClosedMessageType, b'')
        self._message_queue.put(msg)

  def _ReadFromStdinAndEnqueueMessageWindows(self):
    """Reads data from stdin on Windows.

      This method will loop until stdin is closed. Should be executed in a
      separate thread to avoid blocking the main thread.
    """

    try:
      while not self._stdin_closed:
        # STD_INPUT_HANDLE is -10
        h = ctypes.windll.kernel32.GetStdHandle(-10)
        buf = ctypes.create_string_buffer(self._bufsize)
        number_of_bytes_read = wintypes.DWORD()
        ok = ctypes.windll.kernel32.ReadFile(
            h, buf, self._bufsize, ctypes.byref(number_of_bytes_read), None)
        if not ok:
          raise socket.error(errno.EIO, 'stdin ReadFile failed')
        msg = buf.raw[:number_of_bytes_read.value]
        self._message_queue.put(self._StdinSocketMessage(self._DataMessageType,
                                                         msg))
    except Exception:  # pylint: disable=broad-except
      self._message_queue.put(
          self._StdinSocketMessage(self._ExceptionMessageType,
                                   sys.exc_info()))

  def _RecvWindows(self, bufsize):
    """Reads data from stdin on Windows.

    Args:
      bufsize: The maximum number of bytes to receive. Must be positive.
    Returns:
      The bytes received. EOF is indicated by b''.
    Raises:
      socket.error: On low level errors.
    """

    if bufsize != utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE:
      log.info('bufsize [%s] is not max_data_frame_size', bufsize)

    # We are using 1 second timeout here, which mean it can take up to 1
    # second for gcloud to realize it should exit. Lower timeout means more
    # cpu usage
    while not self._stdin_closed:
      try:
        msg = self._message_queue.get(timeout=1)
      except queue.Empty:
        # Timeout reached
        continue

      msg_type = msg.GetType()
      msg_data = msg.GetData()

      if msg_type is self._ExceptionMessageType:
        six.reraise(msg_data[0], msg_data[1], msg_data[2])

      if msg_type is self._StdinClosedMessageType:
        self._stdin_closed = True

      return msg_data
    # If stdin was closed we return an empty byte, so we can have a similar
    # behavior as the unix version
    return b''

  def _RecvUnix(self, bufsize):
    """Reads data from stdin on Unix.

    Args:
      bufsize: The maximum number of bytes to receive. Must be positive.
    Returns:
      The bytes received. EOF is indicated by b''. Once EOF has been indicated,
      will always indicate EOF.
    Raises:
      IOError: On low level errors.
    """

    # We don't except bufsize to be anything other than the max size of our
    # protocol. We will log it only for now to get telemetry if this
    # ever happens.
    if bufsize != utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE:
      log.info('bufsize [%s] is not max_data_frame_size', bufsize)

    if self._stdin_closed:
      return b''

    try:
      while not self._stdin_closed:
        # We have a timeout here because of b/197960494
        stdin_ready = select.select([sys.stdin], (), (),
                                    READ_FROM_STDIN_TIMEOUT_SECS)
        if not stdin_ready[0]:
          continue
        return self._ReadUnixNonBlocking(self._bufsize)
    except _StdinSocket._EOFError:
      self._stdin_closed = True
    return b''

  def _ReadUnixNonBlocking(self, bufsize):
    """Reads from stdin on Unix in a nonblocking manner.

    Args:
      bufsize: The maximum number of bytes to receive. Must be positive.
    Returns:
      The bytes read. b'' means no data is available.
    Raises:
      _StdinSocket._EOFError: to indicate EOF.
      IOError: On low level errors.
    """
    # In python 3, we need to read stdin in a binary way, not a text way to
    # read bytes instead of str. In python 2, binary mode vs text mode only
    # matters on Windows.
    try:
      if six.PY2:
        b = sys.stdin.read(bufsize)
      else:
        b = sys.stdin.buffer.read(bufsize)
    except IOError as e:
      if e.errno == errno.EAGAIN or isinstance(e, io.BlockingIOError):
        # In python2, no nonblocking data available is indicated by raising
        # IOError with EAGAIN.
        # The online python3 documentation says BlockingIOError is raised when
        # no nonblocking data available. We handle that case in case it is ever
        # correct. BlockingIOError is a subclass of OSError which is identical
        # to IOError.
        return b''
      raise
    if b == b'':  # pylint: disable=g-explicit-bool-comparison
      # In python 2 and 3, EOF is indicated by returning b''.
      raise _StdinSocket._EOFError

    if b is None:
      # Regardless of what the online python3 documentation says, it actually
      # returns None to indicate no nonblocking data available.
      b = b''
    return b


class SecurityGatewayTunnelHelper(object):
  """Helper class for starting a Security Gateaway tunnel."""

  def __init__(self, args, project, region, security_gateway, host, port):
    # Re-use the same args as IAP to prevent adding more flags than necessary.
    self._tunnel_url_override = args.iap_tunnel_url_override
    self._ignore_certs = args.iap_tunnel_insecure_disable_websocket_cert_check

    self._project = project
    self._region = region
    self._security_gateway = security_gateway
    self._host = host
    self._port = port

    self._shutdown = False

  def _InitiateConnection(self, local_conn,
                          get_access_token_callback, user_agent):
    del user_agent  # Unused.
    sg_tunnel_target = self._GetTargetInfo()
    new_sg_tunnel = sg_tunnel.SecurityGatewayTunnel(
        sg_tunnel_target,
        get_access_token_callback,
        functools.partial(_SendLocalDataCallback, local_conn),
        functools.partial(_CloseLocalConnectionCallback, local_conn),
        self._ignore_certs)
    new_sg_tunnel.InitiateConnection()
    return new_sg_tunnel

  def _GetTargetInfo(self):
    proxy_info = http_proxy.GetHttpProxyInfo()
    if callable(proxy_info):
      proxy_info = proxy_info(method='https')
    return sg_utils.SecurityGatewayTargetInfo(
        project=self._project,
        region=self._region,
        security_gateway=self._security_gateway,
        host=self._host,
        port=self._port,
        url_override=self._tunnel_url_override,
        proxy_info=proxy_info,
    )

  def RunReceiveLocalData(self, local_conn, socket_address, user_agent):
    """Receive data from provided local connection and send over HTTP CONNECT.

    Args:
      local_conn: A socket or _StdinSocket representing the local connection.
      socket_address: A verbose loggable string describing where conn is
        connected to.
      user_agent: The user_agent of this connection
    """
    sg_conn = None
    try:
      sg_conn = self._InitiateConnection(
          local_conn,
          functools.partial(_GetAccessTokenCallback,
                            store.LoadIfEnabled(use_google_auth=True)),
          user_agent)
      while not (self._shutdown or sg_conn.ShouldStop()):
        data = local_conn.recv(utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE)
        if not data:
          log.warning('Local connection [%s] has closed.', socket_address)
          break
        sg_conn.Send(data)
    except socket.error as e:
      log.error('Error while transmitting local connection [%s]: %s ',
                socket_address, e)
    finally:
      log.info('Terminating connection from local connection: [%s]',
               socket_address)
      if local_conn:
        local_conn.shutdown(socket.SHUT_RD)
        local_conn.close()
      if sg_conn:
        sg_conn.Close()
        log.debug('Connection [%s] closed.', socket_address)

  def Close(self):
    # This is expected to be called from a separate thread than the one running
    # RunReceiveLocalData.
    self._shutdown = True


class IAPWebsocketTunnelHelper(object):
  """Helper class for starting an IAP WebSocket tunnel."""

  def __init__(self, args, project,
               zone=None, instance=None, interface=None, port=None,
               region=None, network=None, host=None, dest_group=None):
    self._project = project
    self._iap_tunnel_url_override = args.iap_tunnel_url_override
    self._ignore_certs = args.iap_tunnel_insecure_disable_websocket_cert_check

    self._zone = zone
    self._instance = instance
    self._interface = interface
    self._port = port
    self._region = region
    self._network = network
    self._host = host
    self._dest_group = dest_group

    self._shutdown = False

  def Close(self):
    self._shutdown = True

  def _InitiateConnection(self, local_conn, get_access_token_callback,
                          user_agent):
    tunnel_target = self._GetTunnelTargetInfo()
    new_websocket = iap_tunnel_websocket.IapTunnelWebSocket(
        tunnel_target, get_access_token_callback,
        functools.partial(_SendLocalDataCallback, local_conn),
        functools.partial(_CloseLocalConnectionCallback, local_conn),
        user_agent, ignore_certs=self._ignore_certs)
    new_websocket.InitiateConnection()
    return new_websocket

  def _GetTunnelTargetInfo(self):
    proxy_info = http_proxy.GetHttpProxyInfo()
    if callable(proxy_info):
      proxy_info = proxy_info(method='https')
    return utils.IapTunnelTargetInfo(project=self._project,
                                     zone=self._zone,
                                     instance=self._instance,
                                     interface=self._interface,
                                     port=self._port,
                                     url_override=self._iap_tunnel_url_override,
                                     proxy_info=proxy_info,
                                     region=self._region,
                                     network=self._network,
                                     host=self._host,
                                     dest_group=self._dest_group)

  def RunReceiveLocalData(self, conn, socket_address, user_agent):
    """Receive data from provided local connection and send over WebSocket.

    Args:
      conn: A socket or _StdinSocket representing the local connection.
      socket_address: A verbose loggable string describing where conn is
        connected to.
      user_agent: The user_agent of this connection
    """
    websocket_conn = None
    try:
      websocket_conn = self._InitiateConnection(
          conn,
          functools.partial(_GetAccessTokenCallback,
                            store.LoadIfEnabled(use_google_auth=True)),
          user_agent)
      while not self._shutdown:
        data = conn.recv(utils.SUBPROTOCOL_MAX_DATA_FRAME_SIZE)
        if not data:
          # When we recv an EOF, we notify the websocket_conn of it, then we
          # wait for all data to send before returning.
          websocket_conn.LocalEOF()
          if not websocket_conn.WaitForAllSent():
            log.warning('Failed to send all data from [%s].', socket_address)
          break
        websocket_conn.Send(data)
    finally:
      if self._shutdown:
        log.info('Terminating connection to [%s].', socket_address)
      else:
        log.info('Client closed connection from [%s].', socket_address)
      try:
        conn.close()
      except EnvironmentError:
        pass
      try:
        if websocket_conn:
          websocket_conn.Close()
      except (EnvironmentError, exceptions.Error):
        pass


class IapTunnelProxyServerHelper():
  """Proxy server helper listens on a port for new local connections."""

  def __init__(self, local_host, local_port,
               should_test_connection, tunneler):
    self._tunneler = tunneler
    self._local_host = local_host
    self._local_port = local_port
    self._should_test_connection = should_test_connection
    self._server_sockets = []
    self._connections = []

  def __del__(self):
    self._CloseServerSockets()

  def Run(self):
    """Start accepting connections."""
    if self._should_test_connection:
      try:
        self._TestConnection()
      except iap_tunnel_websocket.ConnectionCreationError as e:
        raise iap_tunnel_websocket.ConnectionCreationError(
            'While checking if a connection can be made: %s' % six.text_type(e))
    self._server_sockets = _OpenLocalTcpSockets(self._local_host,
                                                self._local_port)
    log.out.Print('Listening on port [%d].' % self._local_port)

    try:
      with execution_utils.RaisesKeyboardInterrupt():
        while True:
          self._connections.append(self._AcceptNewConnection())
          # To fix b/189195317, we will need to erase the reference of dead
          # tasks.
          self._CleanDeadClientConnections()
    except KeyboardInterrupt:
      log.info('Keyboard interrupt received.')
    finally:
      self._CloseServerSockets()

    self._tunneler.Close()
    self._CloseClientConnections()
    log.status.Print('Server shutdown complete.')

  def _TestConnection(self):
    log.status.Print('Testing if tunnel connection works.')
    user_agent = transport.MakeUserAgentString()
    # pylint: disable=protected-access
    conn = self._tunneler._InitiateConnection(
        None,
        functools.partial(_GetAccessTokenCallback,
                          store.LoadIfEnabled(use_google_auth=True)),
        user_agent)
    # pylint: enable=protected-access
    conn.Close()

  def _AcceptNewConnection(self):
    """Accept a new socket connection and start a new WebSocket tunnel."""
    # Python socket accept() on Windows does not get interrupted by ctrl-c
    # To work around that, use select() with a timeout before the accept()
    # which allows for the ctrl-c to be noticed and abort the process as
    # expected.
    ready_sockets = [()]
    while not ready_sockets[0]:
      # 0.2 second timeout
      ready_sockets = select.select(self._server_sockets, (), (), 0.2)

    ready_read_sockets = ready_sockets[0]
    conn, socket_address = ready_read_sockets[0].accept()
    new_thread = threading.Thread(target=self._HandleNewConnection,
                                  args=(conn, socket_address))
    new_thread.daemon = True
    new_thread.start()
    return new_thread, conn

  def _CloseServerSockets(self):
    log.debug('Stopping server.')
    try:
      for server_socket in self._server_sockets:
        server_socket.close()
    except EnvironmentError:
      pass

  def _CloseClientConnections(self):
    """Close client connections that seem to still be open."""
    if self._connections:
      close_count = 0
      for client_thread, conn in self._connections:
        if client_thread.is_alive():
          close_count += 1
          try:
            conn.close()
          except EnvironmentError:
            pass
      if close_count:
        log.status.Print('Closed [%d] local connection(s).' % close_count)

  def _CleanDeadClientConnections(self):
    """Erase reference to dead connections so they can be garbage collected."""
    conn_still_alive = []
    if self._connections:
      dead_connections = 0
      for client_thread, conn in self._connections:
        if not client_thread.is_alive():
          dead_connections += 1
          try:
            conn.close()
          except EnvironmentError:
            pass
          del conn
          del client_thread
        else:
          conn_still_alive.append([client_thread, conn])
      if dead_connections:
        log.debug('Cleaned [%d] dead connection(s).' % dead_connections)
        self._connections = conn_still_alive
      # We run GC mostly for windows platforms, where it seems GC is not
      # collecting memory quick enough. For linux platforms, this is needed only
      # to immediately clean the memory we freed above.
      gc.collect(2)
      log.debug('connections alive: [%d]' % len(self._connections))

  def _HandleNewConnection(self, conn, socket_address):
    try:
      user_agent = transport.MakeUserAgentString()
      self._tunneler.RunReceiveLocalData(conn, repr(socket_address),
                                         user_agent)
    except EnvironmentError as e:
      log.info('Socket error [%s] while receiving from client.',
               six.text_type(e))
    except:  # pylint: disable=bare-except
      log.exception('Error while receiving from client.')


class IapTunnelStdinHelper():
  """Facilitates a connection that gets local data from stdin."""

  def __init__(self, tunneler):
    self._tunneler = tunneler

  def Run(self):
    """Executes the tunneling of data."""
    try:
      with execution_utils.RaisesKeyboardInterrupt():

        # Fetching user agent before we start the read loop, because the agent
        # fetch will call sys.stdin.isatty, which is blocking if there is a read
        # waiting for data in the stdin. This only affects MacOs + python 2.7.
        user_agent = transport.MakeUserAgentString()

        self._tunneler.RunReceiveLocalData(_StdinSocket(), 'stdin', user_agent)
    except KeyboardInterrupt:
      log.info('Keyboard interrupt received.')
