# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Troubleshoot VPC setting for ssh connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_troubleshooter
from googlecloudsdk.core import log

_API_COMPUTE_CLIENT_NAME = 'compute'
_API_CLIENT_VERSION_V1 = 'v1'

IAP_MESSAGE = (
    'There is an issue with your IAP configuration\n'
    '\n'
    'Check the following items:\n'
    ' - The IAP firewall rule is valid.\n'
    ' - IAP tunneling is enabled.\n'
    ' - You are connecting using an IAP token.\n'
    ' - You have the IAM role of Project Owner, IAP-Secured Tunnel User, or '
    'iap.tunnelInstances.accessViaIAP (preferred)\n'
    ' - Your organization hasn\'t blocked access to external IP addresses. '
    'IAP changes the source traffic to 35.235.240.0/20 and the tunnel to '
    'https://tunnel.cloudproxy.app.\n'
    ' - If your organization blocks access to public IP addresses, try '
    'connecting through a bastion server.\n'
    '\n'
    'Help for IAP port forwarding: '
    'https://cloud.google.com/iap/docs/using-tcp-forwarding\n'
    'https://cloud.google.com/iap/docs/faq#what_domain_does_for_tcp_use'
    '\n'
    'Help for bastion server: '
    'https://cloud.google.com/compute/docs/instances/connecting-advanced#bastion_host\n')   # pylint: disable=line-too-long


DEFAULT_SSH_PORT_MESSAGE = (
    'No ingress firewall rule allowing SSH found.\n'
    '\n'
    'If the project uses the default ingress firewall rule for SSH, connections'
    ' to all VMs are allowed on TCP port 22.\n'
    'If the VPC network that the VM\'s network interface is in has a custom '
    'firewall rule, make sure that custom rule allows ingress traffic on the '
    'VM\'s SSH TCP port (usually, this is TCP port 22).\n'
    'Help for default firewall rule: '
    'https://cloud.google.com/vpc/docs/vpc#default-network\n'
    'Help for custom firewall rule: '
    'https://cloud.google.com/network-connectivity/docs/vpn/how-to/configuring-firewall-rules?hl=it\n'  # pylint: disable=line-too-long
    '\n'
    "If you need to investigate further, enable the VM's serial console. "
    "Then connect through the VM serial port, find the SSH server's listen "
    "port, and make sure the port number in the VM's firewall rules matches"
    " the SSH server's listen port.\n"
    'Help for serial console: https://cloud.google.com/compute/docs/instances/interacting-with-serial-console\n'  # pylint: disable=line-too-long
    'Help for serial port: https://cloud.google.com/compute/docs/instances/interacting-with-serial-console\n'  # pylint: disable=line-too-long
    'Help for firewall rules: https://cloud.google.com/vpc/docs/using-firewalls\n')  # pylint: disable=line-too-long


class VPCTroubleshooter(ssh_troubleshooter.SshTroubleshooter):
  """Check VPC setting."""

  project = None
  zone = None
  instance = None
  iap_tunnel_args = None

  def __init__(self, project, zone, instance, iap_tunnel_args):
    self.project = project
    self.zone = zone
    self.instance = instance
    self.iap_tunnel_args = iap_tunnel_args
    self.compute_client = apis.GetClientInstance(_API_COMPUTE_CLIENT_NAME,
                                                 _API_CLIENT_VERSION_V1)
    self.compute_message = apis.GetMessagesModule(_API_COMPUTE_CLIENT_NAME,
                                                  _API_CLIENT_VERSION_V1)
    self.issues = {}

  def check_prerequisite(self):
    return

  def cleanup_resources(self):
    return

  def troubleshoot(self):
    log.status.Print('---- Checking VPC settings ----')
    self._CheckDefaultSSHPort()
    if self.iap_tunnel_args:
      self._CheckIAPTunneling()
    log.status.Print('VPC settings: {0} issue(s) found.\n'.format(
        len(self.issues)))
    for message in self.issues.values():
      log.status.Print(message)
    return

  def _CheckIAPTunneling(self):
    firewall_list = self._ListInstanceEffectiveFirewall()
    for firewall in firewall_list:
      if self._HasValidateIAPTunnelingRule(firewall):
        return
    self.issues['iap'] = IAP_MESSAGE

  def _CheckDefaultSSHPort(self):
    firewall_list = self._ListInstanceEffectiveFirewall()
    for firewall in firewall_list:
      if self._HasSSHProtocalAndPort(firewall):
        return
    self.issues['default_ssh_port'] = DEFAULT_SSH_PORT_MESSAGE

  def _ListInstanceEffectiveFirewall(self):
    req = self.compute_message.ComputeInstancesGetEffectiveFirewallsRequest(
        instance=self.instance.name,
        networkInterface='nic0',
        project=self.project.name,
        zone=self.zone)
    return self.compute_client.instances.GetEffectiveFirewalls(req).firewalls

  def _HasValidateIAPTunnelingRule(self, firewall):
    if firewall.direction != self.compute_message.Firewall.DirectionValueValuesEnum.INGRESS:
      return False
    if all(range != '35.235.240.0/20' for range in firewall.sourceRanges):
      return False
    if not self._HasSSHProtocalAndPort(firewall):
      return False
    return True

  def _HasSSHProtocalAndPort(self, firewall):
    for allow_rule in firewall.allowed:
      if allow_rule.IPProtocol == 'tcp' and any(
          port == '22' for port in allow_rule.ports):
        return True
    return False
