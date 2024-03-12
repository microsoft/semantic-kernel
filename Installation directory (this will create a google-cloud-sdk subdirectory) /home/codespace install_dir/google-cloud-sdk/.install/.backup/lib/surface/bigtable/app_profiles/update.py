# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""bigtable app profiles update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from apitools.base.py.exceptions import HttpError
from googlecloudsdk.api_lib.bigtable import app_profiles
from googlecloudsdk.api_lib.bigtable import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateAppProfile(base.CreateCommand):
  """Update a Bigtable app profile."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          To update an app profile to use a multi-cluster routing policy, run:

            $ {command} my-app-profile-id --instance=my-instance-id --route-any

          To update an app profile to use a single-cluster routing policy that
          routes all requests to `my-cluster-id` and allows transactional
          writes, run:

            $ {command} my-app-profile-id --instance=my-instance-id --route-to=my-cluster-id --transactional-writes

          To update the description for an app profile, run:

            $ {command} my-app-profile-id --instance=my-instance-id --description="New description"

          To update the request priority for an app profile to PRIORITY_LOW, run:

            $ {command} my-app-profile-id --instance=my-instance-id --priority=PRIORITY_LOW

          """),
  }

  @staticmethod
  def Args(parser):
    arguments.AddAppProfileResourceArg(parser, 'to update')
    (
        arguments.ArgAdder(parser)
        .AddDescription('app profile', required=False)
        .AddAppProfileRouting(required=False)
        .AddIsolation()
        .AddForce('update')
        .AddAsync()
    )

  def _UpdateAppProfile(self, app_profile_ref, args):
    """Updates an AppProfile with the given arguments.

    Args:
      app_profile_ref: A resource reference of the new app profile.
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ConflictingArgumentsException,
      OneOfArgumentsRequiredException:
        See app_profiles.Update(...)

    Returns:
      Long running operation.
    """
    return app_profiles.Update(
        app_profile_ref,
        cluster=args.route_to,
        description=args.description,
        multi_cluster=args.route_any,
        restrict_to=args.restrict_to,
        transactional_writes=args.transactional_writes,
        priority=args.priority,
        force=args.force,
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ConflictingArgumentsException,
      OneOfArgumentsRequiredException:
        See _UpdateAppProfile(...)

    Returns:
      Updated resource.
    """
    app_profile_ref = args.CONCEPTS.app_profile.Parse()
    try:
      result = self._UpdateAppProfile(app_profile_ref, args)
    except HttpError as e:
      util.FormatErrorMessages(e)
    else:
      operation_ref = util.GetOperationRef(result)

      if args.async_:
        log.UpdatedResource(
            operation_ref,
            kind='bigtable app profile {0}'.format(app_profile_ref.Name()),
            is_async=True,
        )
        return result

      return util.AwaitAppProfile(
          operation_ref,
          'Updating bigtable app profile {0}'.format(app_profile_ref.Name()),
      )


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateAppProfileBeta(UpdateAppProfile):
  """Update a Bigtable app profile."""

  @staticmethod
  def Args(parser):
    arguments.AddAppProfileResourceArg(parser, 'to update')
    (
        arguments.ArgAdder(parser)
        .AddDescription('app profile', required=False)
        .AddAppProfileRouting(required=False)
        .AddIsolation(allow_data_boost=True)
        .AddForce('update')
        .AddAsync()
    )

  def _UpdateAppProfile(self, app_profile_ref, args):
    """Updates an AppProfile with the given arguments.

    Args:
      app_profile_ref: A resource reference of the new app profile.
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ConflictingArgumentsException,
      OneOfArgumentsRequiredException:
        See app_profiles.Update(...)

    Returns:
      Long running operation.
    """
    return app_profiles.Update(
        app_profile_ref,
        cluster=args.route_to,
        description=args.description,
        multi_cluster=args.route_any,
        restrict_to=args.restrict_to,
        transactional_writes=args.transactional_writes,
        priority=args.priority,
        data_boost=args.data_boost,
        data_boost_compute_billing_owner=args.data_boost_compute_billing_owner,
        force=args.force,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAppProfileAlpha(UpdateAppProfileBeta):
  """Update a Bigtable app profile."""

  @staticmethod
  def Args(parser):
    arguments.AddAppProfileResourceArg(parser, 'to update')
    (
        arguments.ArgAdder(parser)
        .AddDescription('app profile', required=False)
        .AddAppProfileRouting(
            required=False,
            allow_failover_radius=True,
            allow_row_affinity=True,
        )
        .AddIsolation(allow_data_boost=True)
        .AddForce('update')
        .AddAsync()
    )

  def _UpdateAppProfile(self, app_profile_ref, args):
    """Updates an AppProfile with the given arguments.

    Args:
      app_profile_ref: A resource reference of the new app profile.
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ConflictingArgumentsException,
      OneOfArgumentsRequiredException:
        See app_profiles.Update(...)

    Returns:
      Long running operation.
    """
    return app_profiles.Update(
        app_profile_ref,
        cluster=args.route_to,
        description=args.description,
        multi_cluster=args.route_any,
        restrict_to=args.restrict_to,
        failover_radius=args.failover_radius,
        transactional_writes=args.transactional_writes,
        row_affinity=args.row_affinity,
        priority=args.priority,
        data_boost=args.data_boost,
        data_boost_compute_billing_owner=args.data_boost_compute_billing_owner,
        force=args.force,
    )
