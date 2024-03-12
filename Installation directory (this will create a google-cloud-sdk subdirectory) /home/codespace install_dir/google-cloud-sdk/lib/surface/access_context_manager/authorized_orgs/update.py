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
"""`gcloud access-context-manager authorized-orgs update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.accesscontextmanager import authorized_orgs as authorized_orgs_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.accesscontextmanager import authorized_orgs
from googlecloudsdk.command_lib.accesscontextmanager import policies
from googlecloudsdk.command_lib.util.args import repeated


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateAuthorizedOrgsDescsBase(base.UpdateCommand):
  """Update an existing authorized organizations description."""
  _API_VERSION = 'v1'

  @staticmethod
  def Args(parser):
    UpdateAuthorizedOrgsDescsBase.ArgsVersioned(parser)

  @staticmethod
  def ArgsVersioned(parser):
    authorized_orgs.AddResourceArg(parser, 'to update')
    authorized_orgs.AddAuthorizedOrgsDescUpdateArgs(parser)

  def Run(self, args):
    client = authorized_orgs_api.Client(version=self._API_VERSION)
    authorized_orgs_desc_ref = args.CONCEPTS.authorized_orgs_desc.Parse()
    result = repeated.CachedResult.FromFunc(client.Get,
                                            authorized_orgs_desc_ref)
    policies.ValidateAccessPolicyArg(authorized_orgs_desc_ref, args)

    return self.Patch(
        client=client,
        authorized_orgs_desc_ref=authorized_orgs_desc_ref,
        orgs=authorized_orgs.ParseOrgs(args, result),
    )

  def Patch(self, client, authorized_orgs_desc_ref, orgs):
    return client.Patch(authorized_orgs_desc_ref, orgs=orgs)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAuthorizedOrgsDescsAlpha(UpdateAuthorizedOrgsDescsBase):
  """Update an existing authorized orgsd desc."""
  _INCLUDE_UNRESTRICTED = False
  _API_VERSION = 'v1alpha'

  @staticmethod
  def Args(parser):
    UpdateAuthorizedOrgsDescsBase.ArgsVersioned(parser)


detailed_help = {
    'brief':
        'Update the organizations for an existing authorized organizations '
        'description.',
    'DESCRIPTION':
        ('This command updates an authorized organizations description.'),
    'EXAMPLES': (
        'To update the organizations for an authorized organizations '
        'description:\n\n  $ {command} my-authorized-orgs '
        '--add-orgs="organizations/123,organizations/456" ')
}

UpdateAuthorizedOrgsDescsBase.detailed_help = detailed_help
UpdateAuthorizedOrgsDescsAlpha.detailed_help = detailed_help
