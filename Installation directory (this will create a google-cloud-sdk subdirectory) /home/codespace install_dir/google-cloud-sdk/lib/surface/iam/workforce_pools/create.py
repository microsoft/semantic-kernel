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
"""Command to create a new workforce pool under a parent organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as gcloud_exceptions
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.command_lib.iam import identity_pool_waiter
from googlecloudsdk.command_lib.iam.workforce_pools import flags
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


class Create(base.CreateCommand):
  r"""Create a new workforce pool under an organization.

  Creates a workforce pool under an organization given a valid organization ID.

  ## EXAMPLES

  The following command creates a workforce pool with ID `my-workforce-pool`
  in the organization ``12345'':

    $ {command} my-workforce-pool --organization=12345

  The following command creates a workforce pool with ID `my-workforce-pool`
  with explicit values for all required and optional parameters:

    $ {command} my-workforce-pool --organization=12345 --location=global
    --display-name="My Workforce Pool" --description="My workforce pool
    description." --session-duration="7200s" --disabled
  """

  @staticmethod
  def Args(parser):
    workforce_pool_data = yaml_data.ResourceYAMLData.FromPath(
        'iam.workforce_pool'
    )
    concept_parsers.ConceptParser.ForResource(
        'workforce_pool',
        concepts.ResourceSpec.FromYaml(
            workforce_pool_data.GetData(), is_positional=True
        ),
        'The workforce pool to create.',
        required=True,
    ).AddToParser(parser)
    flags.AddParentFlags(parser, 'create')
    parser.add_argument(
        '--display-name',
        help=(
            'A display name for the workforce pool. Cannot exceed 32 '
            + 'characters in length.'
        ),
    )
    parser.add_argument(
        '--description',
        help=(
            'A description for the workforce pool. Cannot exceed 256 '
            + 'characters in length.'
        ),
    )
    parser.add_argument(
        '--disabled',
        action='store_true',
        help='Whether or not the workforce pool is disabled.',
    )
    parser.add_argument(
        '--session-duration',
        help=(
            'How long the Google Cloud access tokens, console sign-in '
            + 'sessions, and gcloud sign-in sessions from this workforce '
            + 'pool are valid. Must be greater than 15 minutes (900s) and '
            + 'less than 12 hours (43200s). If not configured, minted '
            + 'credentials will have a default duration of one hour (3600s).'
        ),
    )
    parser.add_argument(
        '--allowed-services',
        action='append',
        type=arg_parsers.ArgDict(
            spec={'domain': str}, required_keys=['domain']
        ),
        help=(
            'Services allowed for web sign-in with the workforce pool. The flag'
            ' accepts multiple values with the key as `domain` and value as the'
            ' domain of the service allowed for web sign-in. If not set, by'
            ' default all the services are allowed.'
        ),
    )
    parser.add_argument(
        '--disable-programmatic-signin',
        action='store_true',
        help='Disable programmatic sign-in for workforce pool users.',
    )
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    if not args.organization:
      raise gcloud_exceptions.RequiredArgumentException(
          '--organization',
          'Should specify the organization for workforce pools.',
      )
    parent_name = iam_util.GetParentName(
        args.organization, None, 'workforce pool'
    )
    workforce_pool_ref = args.CONCEPTS.workforce_pool.Parse()
    new_workforce_pool = messages.WorkforcePool(
        parent=parent_name,
        displayName=args.display_name,
        description=args.description,
        disabled=args.disabled,
        sessionDuration=args.session_duration,
        accessRestrictions=self.CreateAccessRestrictions(args, messages),
    )
    lro_ref = client.locations_workforcePools.Create(
        messages.IamLocationsWorkforcePoolsCreateRequest(
            location=flags.ParseLocation(args),
            workforcePoolId=workforce_pool_ref.workforcePoolsId,
            workforcePool=new_workforce_pool,
        )
    )

    log.status.Print(
        'Create request issued for: [{}]'.format(
            workforce_pool_ref.workforcePoolsId
        )
    )

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(lro_ref.name))
      return lro_ref

    lro_resource = resources.REGISTRY.ParseRelativeName(
        lro_ref.name, collection='iam.locations.workforcePools.operations'
    )
    poller = identity_pool_waiter.IdentityPoolOperationPoller(
        client.locations_workforcePools,
        client.locations_workforcePools_operations,
    )

    # Wait for a maximum of 5 minutes, as the IAM replication has a lag of up to
    # 80 seconds. GetOperation has a dependency on IAMInternal.CheckPolicy, and
    # requires the caller to have `workforcePools.get` permission on the created
    # resource to return as `done`. See b/203589135.
    result = waiter.WaitFor(
        poller,
        lro_resource,
        'Waiting for operations [{}] to complete'.format(lro_ref.name),
        max_wait_ms=300000,
    )
    log.status.Print(
        'Created workforce pool [{}].'.format(
            workforce_pool_ref.workforcePoolsId
        )
    )

    return result

  def CreateAccessRestrictions(self, args, messages):
    if args.IsSpecified('allowed_services') or args.IsSpecified(
        'disable_programmatic_signin'
    ):
      access_restrictions = messages.AccessRestrictions()
      if args.IsSpecified('allowed_services'):
        access_restrictions.allowedServices = args.allowed_services
      if args.IsSpecified('disable_programmatic_signin'):
        access_restrictions.disableProgrammaticSignin = (
            args.disable_programmatic_signin
        )
      return access_restrictions
    return None
