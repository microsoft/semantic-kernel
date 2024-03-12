# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command to get IAM policy for an organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import organizations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.organizations import flags
from googlecloudsdk.command_lib.organizations import org_utils


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class GetIamPolicy(base.ListCommand):
  """Get IAM policy for an organization.

  Gets the IAM policy for an organization, given an organization ID.

  If a domain is supplied instead of an organization ID, this command will
  attempt to look up the organization ID associated with that domain.
  """

  detailed_help = {
      'EXAMPLES': """\
          The following command prints the IAM policy for an organization with
          the ID `123456789`:

            $ {command} 123456789

          The following command prints the IAM policy for the organzation
          associated with the domain ``example.com'':

            $ {command} example.com
          """
  }

  @staticmethod
  def Args(parser):
    flags.IdArg('whose policy you want to get.').AddToParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    org_id = org_utils.GetOrganizationId(args.id)
    if org_id:
      return organizations.Client().GetIamPolicy(org_id)
    else:
      raise org_utils.UnknownOrganizationError(args.id)
