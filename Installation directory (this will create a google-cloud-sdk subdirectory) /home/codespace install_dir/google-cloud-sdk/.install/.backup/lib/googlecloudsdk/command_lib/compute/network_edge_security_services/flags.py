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
"""Flags and helpers for the compute network edge security services commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


class NetworkEdgeSecurityServicesCompleter(
    compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(NetworkEdgeSecurityServicesCompleter, self).__init__(
        collection='compute.networkEdgeSecurityServices',
        list_command='compute network-edge-security-services list --uri',
        **kwargs)


def NetworkEdgeSecurityServiceArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='network edge security service',
      completer=NetworkEdgeSecurityServicesCompleter,
      plural=plural,
      custom_plural='network edge security services',
      required=required,
      regional_collection='compute.networkEdgeSecurityServices')
