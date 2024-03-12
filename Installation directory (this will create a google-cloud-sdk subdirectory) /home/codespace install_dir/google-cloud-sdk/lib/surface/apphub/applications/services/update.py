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
"""Command to update a Application Service in the Project/Location."""

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
        To update the Service `my-service` with a new environment
        `prod` in the Application `my-app` in location `us-east1`,
        run:

          $ {command} my-service --environment-type=TEST --application=my-app --location=us-east1
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update an Apphub application service."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddUpdateApplicationServiceFlags(
        parser, release_track=base.ReleaseTrack.GA
    )

  def Run(self, args):
    """Run the create command."""
    client = apis.ServicesClient(release_track=base.ReleaseTrack.GA)
    service_ref = api_lib_utils.GetApplicationServiceRef(args)
    attributes = api_lib_utils.PopulateAttributes(
        args, release_track=base.ReleaseTrack.GA
    )
    return client.Update(
        service_id=service_ref.RelativeName(),
        async_flag=args.async_,
        attributes=attributes,
        args=args,
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update an Apphub application service."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddUpdateApplicationServiceFlags(
        parser, release_track=base.ReleaseTrack.ALPHA
    )

  def Run(self, args):
    """Run the create command."""
    client = apis.ServicesClient(release_track=base.ReleaseTrack.ALPHA)
    service_ref = api_lib_utils.GetApplicationServiceRef(args)
    attributes = api_lib_utils.PopulateAttributes(
        args, release_track=base.ReleaseTrack.ALPHA
    )
    return client.Update(
        service_id=service_ref.RelativeName(),
        async_flag=args.async_,
        attributes=attributes,
        args=args,
    )
