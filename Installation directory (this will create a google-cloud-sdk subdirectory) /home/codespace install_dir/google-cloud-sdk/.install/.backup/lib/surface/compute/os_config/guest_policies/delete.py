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
"""Implements command to delete a specified guest policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute.os_config import utils as osconfig_api_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.os_config import utils as osconfig_command_utils
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Delete(base.DeleteCommand):
  """Delete the specified guest policy.

  ## EXAMPLES

    To delete the guest policy named `policy1` in the current project, run:

          $ {command} policy1

  """

  @staticmethod
  def Args(parser):
    """See base class."""
    parser.add_argument(
        'POLICY_ID', type=str, help='Name of the guest policy to delete.')

  def Run(self, args):
    """See base class."""
    release_track = self.ReleaseTrack()
    client = osconfig_api_utils.GetClientInstance(release_track)
    messages = osconfig_api_utils.GetClientMessages(release_track)

    project = properties.VALUES.core.project.GetOrFail()
    guest_policy_name = osconfig_command_utils.GetGuestPolicyUriPath(
        'projects', project, args.POLICY_ID)
    request = messages.OsconfigProjectsGuestPoliciesDeleteRequest(
        name=guest_policy_name)
    service = client.projects_guestPolicies

    response = service.Delete(request)
    log.DeletedResource(guest_policy_name)
    return response
