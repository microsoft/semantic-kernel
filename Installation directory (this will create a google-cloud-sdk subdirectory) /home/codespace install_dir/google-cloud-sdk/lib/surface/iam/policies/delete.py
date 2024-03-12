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
"""Command to delete a policy on the given attachment point."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.iam import policies as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import policies_flags as flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a policy on the given attachment point with the given name."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          The following command deletes the IAM policy defined at the resource
          project ``123'' of kind ``denypolicies'' and id ``my-deny-policy'',
          with etag ``abc'':

            $ {command} my-deny-policy --attachment-point=cloudresourcemanager.googleapis.com/projects/123 --kind=denypolicies --etag=abc
          """),
  }

  @staticmethod
  def Args(parser):
    flags.GetAttachmentPointFlag().AddToParser(parser)
    flags.GetKindFlag().AddToParser(parser)
    flags.GetPolicyIDFlag().AddToParser(parser)
    flags.GetEtagFlag().AddToParser(parser)

  def Run(self, args):
    release_track = args.calliope_command.ReleaseTrack()
    client = apis.GetClientInstance(release_track)
    messages = apis.GetMessagesModule(release_track)
    attachment_point = args.attachment_point.replace('/', '%2F')
    kinds = {
        'denypolicies': 'denyPolicy',
        'principalaccessboundarypolicies': 'principalAccessBoundaryPolicy',
        'accessboundarypolicies': 'accessboundaryPolicy',
    }
    result = client.policies.Delete(
        messages.IamPoliciesDeleteRequest(
            name='policies/{}/{}/{}'.format(attachment_point, args.kind,
                                            args.policy_id),
            etag=args.etag))
    log.DeletedResource(result.name, kinds[args.kind], is_async=True)
    return result
