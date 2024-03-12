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
"""Troubleshoot VM boot and kernel issue for ssh connection."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.compute import ssh_troubleshooter
from googlecloudsdk.command_lib.compute import ssh_troubleshooter_utils
from googlecloudsdk.core import log

_API_COMPUTE_CLIENT_NAME = 'compute'
_API_CLIENT_VERSION_V1 = 'v1'

VM_BOOT_PATTERNS = [
    'Security Violation',

    # GRUB not being able to find image.
    'Failed to load image',

    # OS emergency mode (emergency.target in systemd).
    'You are now being dropped into an emergency shell',
    'You are in (rescue|emergency) mode',
    r'Started \x1b?\[?.*Emergency Shell',
    r'Reached target \x1b?\[?.*Emergency Mode',

    # GRUB emergency shell.
    'Minimal BASH-like line editing is supported',
]

VM_BOOT_MESSAGE = (
    'The VM may not be running. The serial console logs show the VM has been '
    'unable to complete the boot process. Check your serial console logs to '
    'see if the VM has been dropped into an "emergency shell" or has reached '
    '"Emergency Mode". If that is the case, try restarting the VM to see if '
    'the problem is reproducible.\n')

KERNEL_PANIC_PATTERNS = [
    'Kernel panic - not syncing: Attempted to kill init!',
    'Kernel panic - not syncing: Fatal exception',
    'Kernel panic - not syncing: No working init found.',
    'Kernel panic - not syncing: VFS: Unable to mount root fs on unknown-block',
]

KERNEL_PANIC_MESSAGE = (
    'The VM is experiencing a kernel panic. This problem is specific to your '
    'VM and its workload, so you may need to investigate based on a "kernel '
    'panic" error in your serial console logs.\n')


class VMBootTroubleshooter(ssh_troubleshooter.SshTroubleshooter):
  """Check VM boot and kernel panic issues.

  Attributes:
    project: The project object.
    zone: str, the zone name.
    instance: The instance object.
  """

  def __init__(self, project, zone, instance):
    self.project = project
    self.zone = zone
    self.instance = instance
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
    log.status.Print('---- Checking VM boot status ----')
    sc_log = ssh_troubleshooter_utils.GetSerialConsoleLog(
        self.compute_client, self.compute_message, self.instance.name,
        self.project.name, self.zone)
    if ssh_troubleshooter_utils.SearchPatternErrorInLog(VM_BOOT_PATTERNS,
                                                        sc_log):
      self.issues['boot_issue'] = VM_BOOT_MESSAGE
    if ssh_troubleshooter_utils.SearchPatternErrorInLog(KERNEL_PANIC_PATTERNS,
                                                        sc_log):
      self.issues['kernel_panic'] = KERNEL_PANIC_MESSAGE
    log.status.Print('VM boot: {0} issue(s) found.\n'.format(len(self.issues)))
    # Prompt appropriate messages to user.
    for message in self.issues.values():
      log.status.Print(message)
