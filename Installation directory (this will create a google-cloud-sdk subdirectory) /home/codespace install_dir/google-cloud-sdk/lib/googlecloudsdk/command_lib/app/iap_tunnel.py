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
"""Tunnel TCP traffic over Cloud IAP WebSocket connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import iap_tunnel
from googlecloudsdk.core import log


def AddSshTunnelArgs(parser):
  parser.add_argument(
      '--tunnel-through-iap',
      action='store_true',
      help="""\
      Tunnel the ssh connection through Identity-Aware Proxy for TCP forwarding.

      To learn more, see the
      [IAP for TCP forwarding documentation](https://cloud.google.com/iap/docs/tcp-forwarding-overview).
      """)


def CreateSshTunnelArgs(args, api_client, track, project, version, instance):
  """Construct an SshTunnelArgs from command line args and values.

  Args:
    args: The parsed commandline arguments. May or may not have had
      AddSshTunnelArgs called.
    api_client: An appengine_api_client.AppEngineApiClient.
    track: ReleaseTrack, The currently running release track.
    project: str, the project id (string with dashes).
    version: The target version reference object.
    instance: The target instance reference object.

  Returns:
    SshTunnelArgs or None if IAP Tunnel is disabled.
  """
  # If tunneling through IAP is not available, then abort.
  if not hasattr(args, 'tunnel_through_iap'):
    return None

  # If instance has an external ip, then abort.
  instance_ip_mode_enum = api_client.messages.Network.InstanceIpModeValueValuesEnum
  if version.network.instanceIpMode is not instance_ip_mode_enum.INTERNAL:
    return None

  if args.IsSpecified('tunnel_through_iap'):
    # If IAP tunneling is explicitly disabled, then abort.
    if not args.tunnel_through_iap:
      log.status.Print('IAP tunnel is disabled; ssh/scp operations that require'
                       ' IAP tunneling will fail.')
      return None
  else:
    # Default to using IAP tunneling for instances without an external ip.
    log.status.Print('External IP address was not found; defaulting to using '
                     'IAP tunneling.')

  res = iap_tunnel.SshTunnelArgs()

  res.track = track.prefix
  res.project = project
  res.zone = instance.vmZoneName
  res.instance = instance.id

  return res
