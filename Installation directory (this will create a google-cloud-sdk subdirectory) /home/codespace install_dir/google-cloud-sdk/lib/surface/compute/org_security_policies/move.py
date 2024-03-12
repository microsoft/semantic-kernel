# -*- coding: utf-8 -*- #
# Copyright 2019 Google Inc. All Rights Reserved.
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
"""Command for moving organization security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.org_security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.org_security_policies import flags
from googlecloudsdk.command_lib.compute.org_security_policies \
    import org_security_policies_utils
from googlecloudsdk.core import log
import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Move(base.UpdateCommand):
  """Move a Compute Engine organization security policy.

  *{command}* is used to move is used to move organization security policies to
  new parent nodes.
  """

  ORG_SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.ORG_SECURITY_POLICY_ARG = flags.OrgSecurityPolicyArgument(
        required=True, operation='move')
    cls.ORG_SECURITY_POLICY_ARG.AddArgument(parser, operation_type='move')
    flags.AddArgsMove(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.ORG_SECURITY_POLICY_ARG.ResolveAsResource(
        args, holder.resources, with_project=False)
    org_security_policy = client.OrgSecurityPolicy(
        ref=ref,
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())

    parent_id = None
    if args.IsSpecified('organization'):
      parent_id = 'organizations/' + args.organization
    if args.IsSpecified('folder'):
      parent_id = 'folders/' + args.folder
    if parent_id is None:
      log.error('Must specify parent id with --organization=ORGANIZATION or'
                '--folder=FOLDER')
      sys.exit()
    sp_id = org_security_policies_utils.GetSecurityPolicyId(
        org_security_policy, ref.Name(), organization=args.organization)
    return org_security_policy.Move(
        only_generate_request=False, sp_id=sp_id, parent_id=parent_id)


Move.detailed_help = {
    'EXAMPLES':
        """\
    To move an organization security policy under folder with ID ``123456789" to
    folder ``987654321", run:

      $ {command} move 123456789 --folder=987654321
    """,
}
