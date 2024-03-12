# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""The command for describing the anthos support access RBACs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.container.fleet import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.fleet import resources

ROLE_BINDING_ID = 'gke-fleet-support-access'
RESOURCE_NAME_FORMAT = '{membership_name}/rbacrolebindings/{rbacrolebinding_id}'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe support access for the specified membership.

  ## EXAMPLES

    To describe support access for membership `my-membership` run:

      $ {command} my-membership

  """

  @classmethod
  def Args(cls, parser):
    resources.AddMembershipResourceArg(
        parser,
        membership_help=textwrap.dedent("""\
          The membership name that you want to describe support access for.
        """),
        location_help=textwrap.dedent("""\
          The location of the membership resource, e.g. `us-central1`.
          If not specified, defaults to `global`.
        """),
        membership_required=True,
        positional=True)

  def Run(self, args):
    membership_name = resources.ParseMembershipArg(args)
    name = RESOURCE_NAME_FORMAT.format(
        membership_name=membership_name, rbacrolebinding_id=ROLE_BINDING_ID)

    fleet_client = client.FleetClient(release_track=self.ReleaseTrack())
    return fleet_client.GetMembershipRbacRoleBinding(name)
