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

"""Command to set IAM policy for a resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import organizations
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.organizations import flags
from googlecloudsdk.command_lib.organizations import org_utils


class SetIamPolicy(base.Command):
  """Set IAM policy for an organization.

  Given an organization ID and a file encoded in JSON or YAML that contains the
  IAM policy, this command will set the IAM policy for that organization.
  """

  detailed_help = {
      'EXAMPLES': (
          '\n'.join([
              'The following command reads an IAM policy defined in a JSON',
              'file `policy.json` and sets it for an organization with the ID',
              '`123456789`:',
              '',
              '  $ {command} 123456789 policy.json',
              '',
              'The following command reads an IAM policy defined in a JSON',
              'file `policy.json` and sets it for the organization associated',
              'with the domain `example.com`:',
              '',
              '  $ {command} example.com policy.json',
          ]))
      }

  @staticmethod
  def Args(parser):
    flags.IdArg('whose IAM policy you want to set.').AddToParser(parser)
    parser.add_argument(
        'policy_file', help='JSON or YAML file containing the IAM policy.')

  def Run(self, args):
    org_id = org_utils.GetOrganizationId(args.id)
    if org_id:
      return organizations.Client().SetIamPolicy(org_id, args.policy_file)
    else:
      raise org_utils.UnknownOrganizationError(args.id)
