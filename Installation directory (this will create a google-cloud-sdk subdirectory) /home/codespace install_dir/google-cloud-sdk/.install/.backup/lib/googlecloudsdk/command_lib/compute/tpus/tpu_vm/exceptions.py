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
"""Exceptions for Cloud TPU VM libraries."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class TPUInUnusableTerminalState(exceptions.Error):
  """Error when the TPU is in an unusable, terminal state."""

  def __init__(self, state):
    super(TPUInUnusableTerminalState, self).__init__(
        'This TPU has terminal state "{}", so it cannot be used anymore.'
        .format(state))


class TPUInUnusableState(exceptions.Error):
  """Error when the TPU is in an unusable state."""

  def __init__(self, state):
    super(TPUInUnusableState, self).__init__(
        'This TPU has state "{}", so it cannot be currently connected to.'
        .format(state))


class SSHKeyNotInAgent(exceptions.Error):
  """Error when the SSH key is not in the SSH agent."""

  def __init__(self, identity_file):
    super(SSHKeyNotInAgent, self).__init__(
        'SSH Key is not present in the SSH agent. Please run "ssh-add {}" to '
        'add it, and try again.'.format(identity_file))


class IapTunnelingUnavailable(exceptions.Error):
  """Error when IAP tunneling is unavailable (either temporarily or not)."""

  def __init__(self):
    super(IapTunnelingUnavailable, self).__init__(
        'Currently unable to connect to this TPU using IAP tunneling.')


class TPUInMaintenanceEvent(exceptions.Error):
  """Error when TPU has unhealthy maintenance for health."""

  def __init__(self):
    super(TPUInMaintenanceEvent, self).__init__(
        'This TPU is going through a maintenance event, and is currently unavailable. For more information, see https://cloud.google.com/tpu/docs/maintenance-events.'
    )
