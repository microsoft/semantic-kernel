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
"""Implements command to update a specified guest policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Update(base.Command):
  r"""Update the specified guest policy for a project.

  ## EXAMPLES

    To update the guest policy `policy1` in the project `project1`, run:

          $ {command} policy1 \
          --file=path_to_config_file --project=project1

  """

  @staticmethod
  def Args(parser):
    """See base class."""
    parser.add_argument(
        'POLICY_ID', type=str, help='Name of the guest policy to update.')
    parser.add_argument(
        '--file',
        required=True,
        help="""\
        The JSON or YAML file with the updated guest policy.

        If this file specifies an etag value, the update succeeds only if
        the policy that is already in place has a matching etag value. If no
        etag value is specified, the specifications in the updated policy file
        replaces the existing policy.

        For information about the guest policy format, see https://cloud.google.com/compute/docs/osconfig/rest/v1beta/projects.guestPolicies.
        """)

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    (guest_policy,
     _) = osconfig_command_utils.GetResourceAndUpdateFieldsFromFile(
         args.file, messages.GuestPolicy)

    project = properties.VALUES.core.project.GetOrFail()
    request = messages.OsconfigProjectsGuestPoliciesPatchRequest(
        guestPolicy=guest_policy,
        name=osconfig_command_utils.GetGuestPolicyUriPath(
            'projects', project, args.POLICY_ID),
        updateMask=None,
    )
    service = client.projects_guestPolicies

    return service.Patch(request)
