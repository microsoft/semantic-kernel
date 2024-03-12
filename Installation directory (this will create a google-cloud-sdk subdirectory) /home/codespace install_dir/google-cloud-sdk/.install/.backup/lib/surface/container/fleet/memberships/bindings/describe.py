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
"""Command to show fleet information."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.api_lib.container.fleet import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources


class Describe(base.DescribeCommand):
  """Show Membership-Binding info.

  This command can fail for the following reasons:
  * The Membership specified does not exist.
  * The Membership Binding specified does not exist in the project.
  * The caller does not have permission to access the Membership Binding.
  * The caller did not specify the location (--location) if referring to
  location other than global.

  ## EXAMPLES

  To print metadata for the membership Binding `BINDING_NAME` in a global
  membership `MEMBERSHIP_NAME`, run:

    $ {command} BINDING_NAME --membership=MEMBERSHIP_NAME

  To print metadata for the Binding `BINDING_NAME` associated with regional
  membership `MEMBERSHIP_NAME`, provide the location LOCATION_NAME for the
  Membership where the Binding belongs along with membership name.

  $ {command} BINDING_NAME --membership=MEMBERSHIP_NAME --location=LOCATION_NAME
  """

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipBindingResourceArg(
        parser,
        api_version=util.VERSION_MAP[cls.ReleaseTrack()],
        binding_help=('Name of the Membership Binding to be described.'
                      'Must comply with RFC 1123 (up to 63 characters, '
                      'alphanumeric and \'-\')'))

  def Run(self, args):
    fleetclient = client.FleetClient(release_track=self.ReleaseTrack())
    return fleetclient.GetMembershipBinding(
        resources.MembershipBindingResourceName(args))
