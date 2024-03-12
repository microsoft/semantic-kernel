# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""The `gcloud compute shared-vpc get-host-project` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import xpn_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.xpn import flags


class GetHostProject(base.Command):
  """Get the shared VPC host project that the given project is associated with.
  """

  detailed_help = {
      'EXAMPLES':
          """
          If `service-project1` and `service-project2` are associated service
          projects of the shared VPC host project `host-project`,

            $ {command} service-project1

          will show the `host-project` project.
      """
  }

  @staticmethod
  def Args(parser):
    flags.GetProjectIdArgument('get the host project for').AddToParser(parser)

  def Run(self, args):
    xpn_client = xpn_api.GetXpnClient(self.ReleaseTrack())
    return xpn_client.GetHostProject(args.project)
