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
"""Cloud Workstations workstations API utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import socket
import ssl
import sys
import threading
import time

from apitools.base.py.exceptions import Error
from apitools.base.py.exceptions import HttpError

from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.api_lib.workstations.util import GetClientInstance
from googlecloudsdk.api_lib.workstations.util import GetMessagesModule
from googlecloudsdk.api_lib.workstations.util import VERSION_MAP
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.ssh import containers
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import execution_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources

from requests import certs
import six
import websocket
import websocket._exceptions as websocket_exceptions


class Workstations:
  """The Workstations set of Cloud Workstations API functions."""

  def __init__(self, release_track=base.ReleaseTrack.BETA):
    self.api_version = VERSION_MAP.get(release_track)
    self.client = GetClientInstance(release_track)
    self.messages = GetMessagesModule(release_track)
    self._service = self.client.projects_locations_workstationClusters_workstationConfigs_workstations
    self.threading_event = threading.Event()
    self.tcp_tunnel_open = False

  def ListUsableWorkstations(self, args):
    list_usable_req = self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsWorkstationsListUsableRequest(
        parent=args.CONCEPTS.config.Parse().RelativeName()
    )
    return self._service.ListUsable(list_usable_req).workstations

  def Start(self, args):
    """Start a workstation."""
    workstation_name = args.CONCEPTS.workstation.Parse().RelativeName()
    workstation_id = arg_utils.GetFromNamespace(
        args, 'workstation', use_defaults=True)
    start_req = self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsWorkstationsStartRequest(
        name=workstation_name)
    op_ref = self._service.Start(start_req)

    log.status.Print(
        'Starting workstation: [{}]'.format(workstation_id))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='workstations.projects.locations.operations',
        api_version=self.api_version)
    poller = waiter.CloudOperationPoller(
        self._service, self.client.projects_locations_operations)

    waiter.WaitFor(poller, op_resource,
                   'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.status.Print('Started workstation [{}].'.format(workstation_id))

  def Stop(self, args):
    """Stop a workstation."""
    workstation_name = args.CONCEPTS.workstation.Parse().RelativeName()
    workstation_id = arg_utils.GetFromNamespace(
        args, 'workstation', use_defaults=True)
    stop_req = self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsWorkstationsStopRequest(
        name=workstation_name)
    op_ref = self._service.Stop(stop_req)

    log.status.Print(
        'Stopping workstation: [{}]'.format(workstation_id))

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='workstations.projects.locations.operations',
        api_version=self.api_version)
    poller = waiter.CloudOperationPoller(
        self._service, self.client.projects_locations_operations)

    waiter.WaitFor(poller, op_resource,
                   'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.status.Print('Stopped workstation [{}].'.format(workstation_id))

  def StartTcpTunnel(self, args, threaded=False):
    """Start a TCP tunnel to a workstation."""
    config_name = args.CONCEPTS.workstation.Parse().Parent().RelativeName()
    try:
      config = self.client.projects_locations_workstationClusters_workstationConfigs.Get(
          self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsGetRequest(
              name=config_name
          )
      )
      if (
          hasattr(config, 'disableTcpConnections')
          and config.disableTcpConnections
      ):
        log.error(
            'TCP tunneling is disabled for workstations under this'
            ' configuration.'
        )
        sys.exit(1)
    except HttpError:
      # The user may not have permission to get the config. In that
      # case just proceed, and if tcp tunneling is disabled the error
      # message just won't be as nice.
      pass

    workstation_name = args.CONCEPTS.workstation.Parse().RelativeName()

    # Look up the workstation host and determine port
    try:
      workstation = self.client.projects_locations_workstationClusters_workstationConfigs_workstations.Get(
          self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsWorkstationsGetRequest(
              name=workstation_name
          )
      )
    except HttpError as e:
      # Specified workstation does not exist
      if threaded:
        self.threading_event.set()
      log.error(e)
      sys.exit(1)

    self.host = workstation.host
    self.port = args.workstation_port
    if (
        workstation.state
        != self.messages.Workstation.StateValueValuesEnum.STATE_RUNNING
    ):
      if threaded:
        self.threading_event.set()
      log.error('Workstation is not running.')
      sys.exit(1)

    # Generate an access token and refresh it periodically
    self._FetchAccessToken(workstation_name, threaded)
    self._RefreshAccessToken(workstation_name, threaded)

    # Bind on the local TCP port
    (host, port) = self._GetLocalHostPort(args)
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.socket.bind((host, port))
    self.socket.listen(1)
    if port == 0:
      log.status.Print(
          'Picking local unused port [{0}].'.format(
              self.socket.getsockname()[1]
          )
      )

    # Accept new client connections
    log.status.Print(
        'Listening on port [{0}].'.format(self.socket.getsockname()[1])
    )

    if threaded:
      # Notifies threads that the TCP tunnel was started
      self.tcp_tunnel_open = True
      self.threading_event.set()
      while self.tcp_tunnel_open:
        conn, addr = self.socket.accept()
        self._AcceptConnection(conn, addr)
    else:
      try:
        with execution_utils.RaisesKeyboardInterrupt():
          while True:
            conn, addr = self.socket.accept()
            self._AcceptConnection(conn, addr)
      except KeyboardInterrupt:
        log.info('Keyboard interrupt received.')

    log.status.Print('Server shutdown complete.')

  def Ssh(self, args):
    """SSH's to a workstation."""
    self.env = ssh.Environment.Current()
    self.env.RequireSSH()

    keys = ssh.Keys.FromFilename()
    keys.EnsureKeysExist(overwrite=False)

    (host, port) = self._GetLocalHostPort(args)

    remote = ssh.Remote(host=host, user=args.user)

    port = (
        args.local_host_port.port
        if int(args.local_host_port.port) != 0
        else six.text_type(self.socket.getsockname()[1])
    )

    options = {
        'UserKnownHostsFile': '/dev/null',
        'StrictHostKeyChecking': 'no',
        'ServerAliveInterval': '0',
    }

    remainder = []
    if args.ssh_args:
      remainder.extend(args.ssh_args)

    tty = not args.command
    command_list = args.command.split(' ') if args.command else None
    remote_command = containers.GetRemoteCommand(None, command_list)

    cmd = ssh.SSHCommand(
        remote=remote,
        port=port,
        options=options,
        tty=tty,
        remainder=remainder,
        remote_command=remote_command,
    )

    return cmd.Run(self.env)

  def _FetchAccessToken(self, workstation, threaded=False):
    try:
      self.access_token = self.client.projects_locations_workstationClusters_workstationConfigs_workstations.GenerateAccessToken(
          self.messages.WorkstationsProjectsLocationsWorkstationClustersWorkstationConfigsWorkstationsGenerateAccessTokenRequest(
              workstation=workstation
          )
      ).accessToken
    except Error as e:
      if threaded:
        self.threading_event.set()
      log.error('Error fetching access token: {0}'.format(e))
      sys.exit(1)

  def _RefreshAccessToken(self, workstation, threaded=False):
    def Refresh():
      while True:
        time.sleep(2700)  # 45 minutes
        self._FetchAccessToken(workstation, threaded)

    t = threading.Thread(target=Refresh)
    t.daemon = True
    t.start()

  def _GetLocalHostPort(self, args):
    host = args.local_host_port.host or 'localhost'
    port = args.local_host_port.port or '0'
    return host, int(port)

  def _AcceptConnection(self, client, _):
    """Opens a WebSocket connection."""
    custom_ca_certs = properties.VALUES.core.custom_ca_certs_file.Get()
    if custom_ca_certs:
      ca_certs = custom_ca_certs
    else:
      ca_certs = certs.where()

    server = websocket.WebSocketApp(
        'wss://%s/_workstation/tcp/%d' % (self.host, self.port),
        header={'Authorization': 'Bearer %s' % self.access_token},
        on_open=lambda ws: self._ForwardClientToServer(client, ws),
        on_data=lambda ws, data, op, finished: client.send(data),
        on_error=lambda ws, e: self._OnWebsocketError(client, e),
    )

    def Run():
      server.run_forever(
          sslopt={
              'cert_reqs': ssl.CERT_REQUIRED,
              'ca_certs': ca_certs,
          }
      )

    t = threading.Thread(target=Run)
    t.daemon = True
    t.start()

  def _ForwardClientToServer(self, client, server):
    def Forward():
      while True:
        data = client.recv(4096)
        if not data:
          break
        server.send(data)

    t = threading.Thread(target=Forward)
    t.daemon = True
    t.start()

  def _OnWebsocketError(self, client, error):
    """Handles WebSocket errors."""
    if (
        isinstance(error, websocket_exceptions.WebSocketBadStatusException)
        and error.status_code == 503
    ):
      log.error(
          'The workstation does not have a server running on port {0}.'.format(
              self.port
          )
      )
      client.close()
    elif isinstance(
        error, websocket_exceptions.WebSocketConnectionClosedException
    ):
      pass
    else:
      log.error('Error connecting to workstation: {0}'.format(error))
