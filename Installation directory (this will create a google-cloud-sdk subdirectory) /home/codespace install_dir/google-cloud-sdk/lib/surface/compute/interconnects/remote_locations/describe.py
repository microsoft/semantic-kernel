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
"""Command for describing interconnect remote locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.remote_locations import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects.remote_locations import flags


class Describe(base.DescribeCommand):
  """Describe a Google Compute Engine interconnect remote location."""

  detailed_help = {
      'DESCRIPTION': """\
              Displays all data associated with Google Compute Engine interconnect remote location in a project.
        """,
      'EXAMPLES': """\
        Example of usage:

          $ {command} my-remote-location
        """,
  }

  INTERCONNECT_REMOTE_LOCATION_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INTERCONNECT_REMOTE_LOCATION_ARG = flags.InterconnectRemoteLocationArgument(
    )
    cls.INTERCONNECT_REMOTE_LOCATION_ARG.AddArgument(
        parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.INTERCONNECT_REMOTE_LOCATION_ARG.ResolveAsResource(
        args, holder.resources)

    interconnect_remote_location = client.InterconnectRemoteLocation(
        ref, compute_client=holder.client)

    return interconnect_remote_location.Describe()
