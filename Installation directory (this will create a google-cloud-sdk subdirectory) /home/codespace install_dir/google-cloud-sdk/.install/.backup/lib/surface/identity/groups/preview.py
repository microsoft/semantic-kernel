# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""The `groups preview` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.identity import admin_directory
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.apis import arg_utils


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Preview(base.Command):
  """Retrieve a list of users in a customer account using CEL query.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To retrieve a list of user in a customer and filter it with a query, run:

            $ {command} --query="user.locations.exists(loc, loc.desk_code == 'abc')" --customer=A1234abcd

          To retrieve a list of users with only fullName and primaryEMail fields, run:

            $ {command} --query="user.locations.exists(loc, loc.desk_code == 'abc')" --customer=A1234abcd --format="flattened(nextPageToken, users[].primaryEmail, users[].name.fullName)"

          """,
  }

  @staticmethod
  def Args(parser):
    scope_args = parser.add_mutually_exclusive_group(required=True)
   # TODO(b/142400670): Add support for my_customer option.
    scope_args.add_argument(
        '--customer',
        help=('The customer ID for the customer\'s G Suite account.'))
    parser.add_argument(
        '--query',
        help=('Query string using CEL and supported user attributes'))
    parser.add_argument(
        '--projection',
        choices=['basic', 'full', 'custom'],
        default='basic',
        help='Subsets of fields to fetch for this user.')
    parser.add_argument(
        '--custom-field-mask',
        metavar='custom-mask',
        type=arg_parsers.ArgList(),
        help=('A comma-separated list of schema names. All fields from these '
              'schemas are fetched. This should only be set when '
              '--projection=custom.'))
    parser.add_argument(
        '--view-type',
        choices=['admin-view', 'domain-public'],
        default='admin-view',
        help=('Whether to fetch the administrator-only or domain-wide public '
              'view of the user.'))
    # TODO(b/142472316): Consider using default gcloud list options.
    parser.add_argument(
        '--max-results',
        default=100,
        type=int,
        help=('Maximum number of results to return. Acceptable values are 1 to '
              '500, inclusive.'))
    parser.add_argument(
        '--page-token', help=('Token to specify next page in the list.'))

  def Run(self, args):
    messages = admin_directory.GetMessages()
    projection = ChoiceToEnum(
        args.projection,
        (messages.DirectoryUsersListRequest.ProjectionValueValuesEnum))
    view_type = ChoiceToEnum(
        args.view_type,
        (messages.DirectoryUsersListRequest.ViewTypeValueValuesEnum))

    return admin_directory.Preview(
        messages.DirectoryUsersListRequest(
            customer=args.customer,
            query=args.query,
            projection=projection,
            customFieldMask=args.custom_field_mask,
            viewType=view_type,
            maxResults=args.max_results,
            pageToken=args.page_token))


def ChoiceToEnumName(choice):
  """Converts an argument value to the string representation of the Enum."""
  return choice.replace('-', '_')


def ChoiceToEnum(choice, enum_type, item_type='choice', valid_choices=None):
  """Converts the typed choice into an apitools Enum value."""
  if choice is None:
    return None
  name = ChoiceToEnumName(choice)
  valid_choices = (
      valid_choices or
      [arg_utils.EnumNameToChoice(n) for n in enum_type.names()])
  try:
    return enum_type.lookup_by_name(name)
  except KeyError:
    raise arg_parsers.ArgumentTypeError(
        'Invalid {item}: {selection}. Valid choices are: [{values}].'.format(
            item=item_type,
            selection=arg_utils.EnumNameToChoice(name),
            values=', '.join(c for c in sorted(valid_choices))))
