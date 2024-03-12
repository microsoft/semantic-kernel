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
"""bigtable app profiles create command."""

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
class CreateAppProfile(base.CreateCommand):
  """Create a new Bigtable app profile."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
          To create an app profile with a multi-cluster routing policy, run:

            $ {command} my-app-profile-id --instance=my-instance-id --route-any

          To create an app profile with a single-cluster routing policy which
          routes all requests to `my-cluster-id`, run:

            $ {command} my-single-cluster-app-profile --instance=my-instance-id --route-to=my-cluster-id

          To create an app profile with a friendly description, run:

            $ {command} my-app-profile-id --instance=my-instance-id --route-any --description="Routes requests for my use case"

          To create an app profile with a request priority of PRIORITY_MEDIUM,
          run:

            $ {command} my-app-profile-id --instance=my-instance-id --route-any --priority=PRIORITY_MEDIUM

          """),
  }

  @staticmethod
  def Args(parser):
    arguments.AddAppProfileResourceArg(parser, 'to create')
    (
        arguments.ArgAdder(parser)
        .AddDescription('app profile', required=False)
        .AddAppProfileRouting()
        .AddIsolation()
        .AddForce('create')
    )

  def _CreateAppProfile(self, app_profile_ref, args):
    """Creates an AppProfile with the given arguments.

    Args:
      app_profile_ref: A resource reference of the new app profile.
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ConflictingArgumentsException,
      OneOfArgumentsRequiredException:
        See app_profiles.Create(...)

    Returns:
      Created app profile resource object.
    """
    return app_profiles.Create(
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
        See _CreateAppProfile(...)

    Returns:
      Created resource.
    """
    app_profile_ref = args.CONCEPTS.app_profile.Parse()
    try:
      result = self._CreateAppProfile(app_profile_ref, args)
    except HttpError as e:
      util.FormatErrorMessages(e)
    else:
      log.CreatedResource(app_profile_ref.Name(), kind='app profile')
      return result


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class CreateAppProfileBeta(CreateAppProfile):
  """Create a new Bigtable app profile."""

  @staticmethod
  def Args(parser):
    arguments.AddAppProfileResourceArg(parser, 'to create')
    (
        arguments.ArgAdder(parser)
        .AddDescription('app profile', required=False)
        .AddAppProfileRouting()
        .AddIsolation(allow_data_boost=True)
        .AddForce('create')
    )

  def _CreateAppProfile(self, app_profile_ref, args):
    """Creates an AppProfile with the given arguments.

    Args:
      app_profile_ref: A resource reference of the new app profile.
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ConflictingArgumentsException,
      OneOfArgumentsRequiredException:
        See app_profiles.Create(...)

    Returns:
      Created app profile resource object.
    """
    return app_profiles.Create(
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
class CreateAppProfileAlpha(CreateAppProfileBeta):
  """Create a new Bigtable app profile."""

  @staticmethod
  def Args(parser):
    arguments.AddAppProfileResourceArg(parser, 'to create')
    (
        arguments.ArgAdder(parser)
        .AddDescription('app profile', required=False)
        .AddAppProfileRouting(
            allow_failover_radius=True,
            allow_row_affinity=True,
        )
        .AddIsolation(allow_data_boost=True)
        .AddForce('create')
    )

  def _CreateAppProfile(self, app_profile_ref, args):
    """Creates an AppProfile with the given arguments.

    Args:
      app_profile_ref: A resource reference of the new app profile.
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      ConflictingArgumentsException,
      OneOfArgumentsRequiredException:
        See app_profiles.Create(...)

    Returns:
      Created app profile resource object.
    """
    return app_profiles.Create(
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
