# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute target-instances commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      zone.basename(),
      instance.basename(),
      natPolicy
    )"""


class TargetInstancesCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(TargetInstancesCompleter, self).__init__(
        collection='compute.targetInstances',
        list_command='compute target-instances list --uri',
        **kwargs)


def TargetInstanceArgument(required=True, plural=False):
  return compute_flags.ResourceArgument(
      resource_name='target instance',
      completer=TargetInstancesCompleter,
      plural=plural,
      required=required,
      zonal_collection='compute.targetInstances',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)


NETWORK_ARG = compute_flags.ResourceArgument(
    name='--network',
    required=False,
    resource_name='network',
    global_collection='compute.networks',
    short_help='Network that this target instance applies to.',
    detailed_help="""\
        Network that this target instance applies to. This is only necessary if
        the corresponding instance has multiple network interfaces.
        If not specified, the default network interface will be used.
        """)


def AddNetwork(parser):
  NETWORK_ARG.AddArgument(parser)
