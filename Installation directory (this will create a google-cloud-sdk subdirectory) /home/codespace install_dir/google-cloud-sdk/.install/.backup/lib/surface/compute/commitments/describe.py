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
"""Describing Compute Engine commitments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.commitments import flags


class Describe(base.DescribeCommand):
  """Describe a Compute Engine commitment."""
  detailed_help = {
      'EXAMPLES': '''
        To describe the commitment called ``commitment-1'' in the ``us-central1''
        region, run:

          $ {command} commitment-1 --region=us-central1
      '''
  }

  @staticmethod
  def Args(parser):
    flags.MakeCommitmentArg(False).AddArgument(
        parser, operation_type='describe')

  def Collection(self):
    return 'compute.commitments'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resources = holder.resources
    commitment_ref = flags.MakeCommitmentArg(False).ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    service = holder.client.apitools_client.regionCommitments
    messages = holder.client.messages
    request = messages.ComputeRegionCommitmentsGetRequest(
        commitment=commitment_ref.Name(),
        project=commitment_ref.project,
        region=commitment_ref.region,
    )
    return service.Get(request)
