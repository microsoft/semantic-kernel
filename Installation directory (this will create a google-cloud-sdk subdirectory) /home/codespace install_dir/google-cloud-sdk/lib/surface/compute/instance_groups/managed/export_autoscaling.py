# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Command for configuring autoscaling of a managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import managed_instance_groups_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.core.util import files


_IGNORED_FIELDS = ['creationTimestamp', 'id', 'kind', 'name', 'region',
                   'selfLink', 'status', 'statusDetails', 'target', 'zone']


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class ExportAutoscaling(base.Command):
  """Export autoscaling parameters of a managed instance group to JSON."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)
    parser.add_argument(
        '--autoscaling-file',
        metavar='PATH',
        required=True,
        help=('Path of the file to which autoscaling configuration will be '
              'written.'))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    igm_ref = instance_groups_flags.CreateGroupReference(
        client, holder.resources, args)

    autoscaler = managed_instance_groups_utils.AutoscalerForMigByRef(
        client, holder.resources, igm_ref)
    if autoscaler:
      autoscaler_dict = encoding.MessageToDict(autoscaler)
      for f in _IGNORED_FIELDS:
        if f in autoscaler_dict:
          del autoscaler_dict[f]
    else:
      autoscaler_dict = None

    files.WriteFileContents(args.autoscaling_file, json.dumps(autoscaler_dict))


ExportAutoscaling.detailed_help = {
    'brief': 'Export autoscaling parameters of a managed instance group',
    'DESCRIPTION': """
        *{command}* exports the autoscaling parameters of the specified managed
instance group.

Autoscalers can use one or more autoscaling signals. Information on using
multiple autoscaling signals can be found here: [](https://cloud.google.com/compute/docs/autoscaler/multiple-signals)
        """,
}
