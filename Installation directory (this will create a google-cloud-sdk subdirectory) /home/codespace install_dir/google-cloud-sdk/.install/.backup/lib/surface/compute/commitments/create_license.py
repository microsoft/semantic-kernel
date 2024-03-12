# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Command for creating Compute Engine license-based commitments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.commitments import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Create(base.Command):
  """Create Compute Engine license-based commitments."""
  detailed_help = {
      'EXAMPLES': '''
        To create a commitment called ``commitment-1'' in the ``us-central1''
        region with 36-month plan, sles-sap-12 license, 1-2 cores, run:

          $ {command} commitment-1 --plan=36-month --license=https://www.googleapis.com/compute/v1/projects/suse-sap-cloud/global/licenses/sles-sap-12 --region=us-central1 --amount=1 --cores-per-license=1-2
      '''
  }

  @classmethod
  def Args(cls, parser):
    flags.MakeCommitmentArg(False).AddArgument(parser, operation_type='create')
    flags.AddLicenceBasedFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    resources = holder.resources
    client = holder.client
    commitment_ref = flags.MakeCommitmentArg(False).ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))

    messages = holder.client.messages

    commitment = messages.Commitment(
        name=commitment_ref.Name(),
        plan=flags.TranslatePlanArg(messages, args.plan),
        category=messages.Commitment.CategoryValueValuesEnum.LICENSE,
        licenseResource=messages.LicenseResourceCommitment(
            amount=args.amount,
            coresPerLicense=args.cores_per_license,
            license=args.license
        ))
    request = (messages.ComputeRegionCommitmentsInsertRequest(
        commitment=commitment,
        project=commitment_ref.project,
        region=commitment_ref.region))
    return client.MakeRequests([(client.apitools_client.regionCommitments,
                                 'Insert', request)])


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(Create):
  """Create Compute Engine license-based commitments."""
