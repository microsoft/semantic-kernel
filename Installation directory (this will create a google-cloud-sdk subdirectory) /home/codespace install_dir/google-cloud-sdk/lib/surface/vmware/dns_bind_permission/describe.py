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
"""'vmware dns-bind-permission describe' command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware import dnsbindpermission
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

DETAILED_HELP = {
    'DESCRIPTION': """
          Gets all the users and service accounts having bind permission on the intranet VPC associated with the consumer project granted by the Grant API.
        """,
    'EXAMPLES': """
          To get all the users and service accounts having bind permission on the intranet VPC associated with the consumer project `my-project`, run:

            $ {command} --project=my-project

          Or:

            $ {command}

         In the second example, the project is taken from gcloud properties core/project.

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Get all users and service accounts having bind permission."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddProjectArgToParser(parser)

  def Run(self, args):
    return dnsbindpermission.DNSBindPermissionClient().Get(
        args.CONCEPTS.project.Parse()
    )
