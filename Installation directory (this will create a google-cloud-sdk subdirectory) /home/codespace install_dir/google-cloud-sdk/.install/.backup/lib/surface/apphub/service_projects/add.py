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
"""Command to add a Service Project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import service_projects as apis
from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To add the service project `my-service-project` to the host project
        `my-host-project`, run:

          $ {command} my-service-project --project=my-host-project
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Add an Apphub service project."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddServiceProjectFlags(parser)

  def Run(self, args):
    """Run the add command."""
    client = apis.ServiceProjectsClient(release_track=base.ReleaseTrack.GA)
    service_project_ref = api_lib_utils.GetServiceProjectRef(args)
    parent_ref = service_project_ref.Parent()
    return client.Add(
        service_project=service_project_ref.Name(),
        async_flag=args.async_,
        parent=parent_ref.RelativeName(),
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Add an Apphub service project."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddServiceProjectFlags(parser)

  def Run(self, args):
    """Run the add command."""
    client = apis.ServiceProjectsClient(release_track=base.ReleaseTrack.ALPHA)
    service_project_ref = api_lib_utils.GetServiceProjectRef(args)
    parent_ref = service_project_ref.Parent()
    return client.Add(
        service_project=service_project_ref.Name(),
        async_flag=args.async_,
        parent=parent_ref.RelativeName(),
    )
