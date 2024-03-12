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
"""Flags and helpers for the compute interconnects remote-locations commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


class InterconnectRemoteLocationsCompleter(
    compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(InterconnectRemoteLocationsCompleter, self).__init__(
        collection='compute.interconnectRemoteLocations',
        list_command='alpha compute interconnects remote-locations list --uri',
        **kwargs)


def InterconnectRemoteLocationArgument(required=True):
  return compute_flags.ResourceArgument(
      resource_name='Cloud Interconnect remote location',
      completer=InterconnectRemoteLocationsCompleter,
      plural=False,
      required=required,
      global_collection='compute.interconnectRemoteLocations')


def InterconnectRemoteLocationArgumentForOtherResource(short_help,
                                                       required=False,
                                                       detailed_help=None):
  return compute_flags.ResourceArgument(
      name='--remote-location',
      resource_name='interconnectRemoteLocation',
      completer=InterconnectRemoteLocationsCompleter,
      plural=False,
      required=required,
      global_collection='compute.interconnectRemoteLocations',
      short_help=short_help,
      detailed_help=detailed_help)
