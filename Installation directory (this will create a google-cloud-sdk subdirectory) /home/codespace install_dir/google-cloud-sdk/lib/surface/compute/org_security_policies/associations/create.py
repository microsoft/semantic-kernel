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
"""Command for creating organization security policy associations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.org_security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.org_security_policies import flags
from googlecloudsdk.command_lib.compute.org_security_policies import org_security_policies_utils
from googlecloudsdk.core import log
import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Create(base.CreateCommand):
  """Create a new association between a security policy and an organization or folder resource.

  *{command}* is used to create organization security policy associations. An
  organization security policy is a set of rules that controls access to various
  resources.
  """

  @classmethod
  def Args(cls, parser):
    flags.AddArgsCreateAssociation(parser)
    parser.display_info.AddCacheUpdater(flags.OrgSecurityPoliciesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    org_security_policy = client.OrgSecurityPolicy(
        compute_client=holder.client,
        resources=holder.resources,
        version=six.text_type(self.ReleaseTrack()).lower())

    name = None
    attachment_id = None
    replace_existing_association = False

    if args.IsSpecified('name'):
      name = args.name

    attachment_id = None
    if args.IsSpecified('folder'):
      attachment_id = 'folders/' + args.folder
      if name is None:
        name = 'folder-' + args.folder

    if args.IsSpecified('organization') and attachment_id is None:
      attachment_id = 'organizations/' + args.organization
      if name is None:
        name = 'organization-' + args.organization

    if attachment_id is None:
      log.error(
          'Must specify attachment ID with --organization=ORGANIZATION or '
          '--folder=FOLDER')
      sys.exit()

    replace_existing_association = False
    if args.replace_association_on_target:
      replace_existing_association = True

    association = holder.client.messages.SecurityPolicyAssociation(
        attachmentId=attachment_id, name=name)

    security_policy_id = org_security_policies_utils.GetSecurityPolicyId(
        org_security_policy,
        args.security_policy,
        organization=args.organization)
    return org_security_policy.AddAssociation(
        association=association,
        security_policy_id=security_policy_id,
        replace_existing_association=replace_existing_association,
        only_generate_request=False)


Create.detailed_help = {
    'EXAMPLES':
        """\
    To associate an organization security policy under folder with ID
    ``123456789" to folder ``987654321", run:

      $ {command} create --security-policy=123456789 --folder=987654321
    """,
}
