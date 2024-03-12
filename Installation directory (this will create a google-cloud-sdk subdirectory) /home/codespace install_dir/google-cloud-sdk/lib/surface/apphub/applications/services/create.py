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
"""Create Command for Application Service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.api_lib.apphub.applications import services as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
         To create the Service `my-service` with discovered service
        `my-discovered-service` in the Application `my-app` in location
        `us-east1`, run:

          $ {command} my-service --application=my-app --location=us-east1 --discovered-service=my-discovered-service
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class CreateGA(base.CreateCommand):
  """Create an Apphub application service."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddCreateApplicationServiceFlags(
        parser, release_track=base.ReleaseTrack.GA
    )

  def Run(self, args):
    """Run the create command."""
    client = apis.ServicesClient(release_track=base.ReleaseTrack.GA)
    service_ref = api_lib_utils.GetApplicationServiceRef(args)
    dis_service_ref = api_lib_utils.GetDiscoveredServiceRef(args)
    parent_ref = service_ref.Parent()
    attributes = api_lib_utils.PopulateAttributes(
        args, release_track=base.ReleaseTrack.GA
    )

    return client.Create(
        service_id=service_ref.Name(),
        parent=parent_ref.RelativeName(),
        async_flag=args.async_,
        discovered_service=dis_service_ref.RelativeName(),
        display_name=args.display_name,
        description=args.description,
        attributes=attributes,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class CreateAlpha(base.CreateCommand):
  """Create an Apphub application service."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddCreateApplicationServiceFlags(
        parser, release_track=base.ReleaseTrack.ALPHA
    )

  def Run(self, args):
    """Run the create command."""
    client = apis.ServicesClient(release_track=base.ReleaseTrack.ALPHA)
    service_ref = api_lib_utils.GetApplicationServiceRef(args)
    dis_service_ref = api_lib_utils.GetDiscoveredServiceRef(args)
    parent_ref = service_ref.Parent()
    attributes = api_lib_utils.PopulateAttributes(
        args, release_track=base.ReleaseTrack.ALPHA
    )

    return client.Create(
        service_id=service_ref.Name(),
        parent=parent_ref.RelativeName(),
        async_flag=args.async_,
        discovered_service=dis_service_ref.RelativeName(),
        display_name=args.display_name,
        description=args.description,
        attributes=attributes,
    )
