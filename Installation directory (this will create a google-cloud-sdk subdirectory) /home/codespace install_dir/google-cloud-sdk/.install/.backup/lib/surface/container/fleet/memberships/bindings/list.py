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
"""Command to show bindings in a membership."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.container.fleet import util
from googlecloudsdk.core import properties


class List(base.ListCommand):
  """List Bindings in a Membership.

  This command can fail for the following reasons:
  * The Membership specified does not exist.
  * The user does not have access to the Membership specified.
  * The caller did not specify the location (--location) if referring to
  location other than global.

  ## EXAMPLES

  The following command lists Bindings in global Membership `MEMBERSHIP_NAME`:

    $ {command} --membership=MEMBERSHIP_NAME

  To list all the bindings associated with regional membership
  `MEMBERSHIP_NAME`, provide the location LOCATION_NAME for the Membership where
  the Binding belongs along with membership name.

  $ {command} --membership=MEMBERSHIP_NAME --location=LOCATION_NAME

  """

  @staticmethod
  def Args(parser):
    # Table formatting
    parser.display_info.AddFormat(util.B_LIST_FORMAT)
    parser.add_argument(
        '--membership',
        type=str,
        required=True,
        help='Name of the Membership to list Bindings from.')
    parser.add_argument(
        '--location',
        type=str,
        default='global',
        help='Name of the Membership location to list Bindings from.')

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    project = args.project
    if project is None:
      project = properties.VALUES.core.project.Get()
    if args.IsKnownAndSpecified('membership'):
      return fleetclient.ListMembershipBindings(project, args.membership,
                                                args.location)
    raise calliope_exceptions.RequiredArgumentException(
        'membership', 'Membership parent is required.')
