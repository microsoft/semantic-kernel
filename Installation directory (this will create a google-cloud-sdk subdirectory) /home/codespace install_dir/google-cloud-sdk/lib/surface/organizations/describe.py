# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command to show metadata for a specified organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.organizations import flags
from googlecloudsdk.command_lib.organizations import org_utils


class Describe(base.DescribeCommand):
  """Show metadata for an organization.

  Shows metadata for an organization, given a valid organization ID. If an
  organization domain is supplied instead, this command will attempt to find
  the organization by domain name.

  This command can fail for the following reasons:
      * The organization specified does not exist.
      * The active account does not have permission to access the given
        organization.
      * The domain name supplied does not correspond to a unique organization
        ID.
  """
  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          The following command prints metadata for an organization with the
          ID `3589215982`:

            $ {command} 3589215982

          The following command prints metadata for an organization associated
          with the domain ``example.com'':

            $ {command} example.com
    """),
  }

  @staticmethod
  def Args(parser):
    flags.IdArg('you want to describe.').AddToParser(parser)

  def Run(self, args):
    org = org_utils.GetOrganization(args.id)
    if org is not None:
      return org
    else:
      raise org_utils.UnknownOrganizationError(args.id)
