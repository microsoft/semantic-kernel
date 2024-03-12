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

"""Command for describing interconnect locations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.interconnects.locations import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects.locations import flags


class Describe(base.DescribeCommand):
  """Describe a Compute Engine interconnect location.

    Displays all data associated with Compute Engine
    interconnect location in a project.

    Example of usage:

      $ {command} my-location
  """

  INTERCONNECT_LOCATION_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INTERCONNECT_LOCATION_ARG = flags.InterconnectLocationArgument()
    cls.INTERCONNECT_LOCATION_ARG.AddArgument(parser, operation_type='describe')

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.INTERCONNECT_LOCATION_ARG.ResolveAsResource(
        args, holder.resources)

    interconnect_location = client.InterconnectLocation(
        ref, compute_client=holder.client)

    return interconnect_location.Describe()
