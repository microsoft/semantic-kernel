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
"""Command for creating Compute Engine commitments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.commitments import flags

_MISSING_COMMITMENTS_QUOTA_REGEX = r'Quota .COMMITMENTS. exceeded.+'


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update Compute Engine commitments."""
  detailed_help = {
      'EXAMPLES':
          """
        To enable auto renewal on a commitment called ``commitment-1'' in the ``us-central1''
        region, run:

          $ {command} commitment-1 --auto-renew --region=us-central1

        To disable auto renewal on a commitment called ``commitment-1''
        in the ``us-central1'' region, run:

          $ {command} commitment-1 --no-auto-renew --region=us-central1

        To upgrade the term of a commitment called ``commitment-1''
        from  12-month to 36-month, in the ``us-central1'' region, run:

          $ {command} commitment-1 --plan=36-month --region=us-central1
      """
  }

  @classmethod
  def Args(cls, parser):
    flags.MakeCommitmentArg(plural=False).AddArgument(
        parser, operation_type='update')
    flags.AddUpdateFlags(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources
    commitment_ref = self._CreateReference(client, resources, args)

    messages = holder.client.messages
    service = holder.client.apitools_client.regionCommitments

    commitment_resource = messages.Commitment(name=commitment_ref.Name())

    commitment_resource.autoRenew = flags.TranslateAutoRenewArgForUpdate(args)
    commitment_resource.plan = self._TranslatePlanArgForUpdate(
        messages=messages, plan=args.plan
    )
    commitment_update_request = self._GetUpdateRequest(
        messages, commitment_ref, commitment_resource
    )

    batch_url = holder.client.batch_url
    http = holder.client.apitools_client.http
    errors = []
    result = list(
        request_helper.MakeRequests(
            requests=[(service, 'Update', commitment_update_request)],
            http=http,
            batch_url=batch_url,
            errors=errors))
    for i, error in enumerate(errors):
      if re.match(_MISSING_COMMITMENTS_QUOTA_REGEX, error[1]):
        errors[i] = (error[0], error[1] +
                     (' You can request commitments quota on '
                      'https://cloud.google.com/compute/docs/instances/'
                      'signing-up-committed-use-discounts#quota'))
    if errors:
      utils.RaiseToolException(errors)
    return result

  def _CreateReference(self, client, resources, args):
    return flags.MakeCommitmentArg(False).ResolveAsResource(
        args,
        resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

  def _GetUpdateRequest(self, messages, commitment_ref, commitment_resource):
    return messages.ComputeRegionCommitmentsUpdateRequest(
        commitment=commitment_ref.Name(),
        commitmentResource=commitment_resource,
        paths=self._GetPaths(commitment_resource),
        project=commitment_ref.project,
        region=commitment_ref.region)

  def _GetPaths(self, commitment_resource):
    paths = []
    if commitment_resource.autoRenew is not None:
      paths.append('autoRenew')
    if commitment_resource.plan is not None:
      paths.append('plan')
    return paths

  def _TranslatePlanArgForUpdate(self, messages=None, plan=None):
    if plan is None:
      return None
    else:
      return flags.TranslatePlanArg(messages, plan)
