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
"""Update Command for Application."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.api_lib.apphub.applications import client as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To update the Application `my-app` with a new environment
        `prod` in location `us-east1`, run:

          $ {command} my-app --location=us-east1 --environment-type=TEST
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class UpdateGA(base.UpdateCommand):
  """Update an Apphub application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.UpdateApplicationFlags(parser, release_track=base.ReleaseTrack.GA)

  def Run(self, args):
    """Run the create command."""
    client = apis.ApplicationsClient(release_track=base.ReleaseTrack.GA)
    app_ref = api_lib_utils.GetApplicationRef(args)
    return client.Update(args, app_ref, release_track=base.ReleaseTrack.GA)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update an Apphub application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.UpdateApplicationFlags(parser, release_track=base.ReleaseTrack.ALPHA)

  def Run(self, args):
    """Run the create command."""
    client = apis.ApplicationsClient(release_track=base.ReleaseTrack.ALPHA)
    app_ref = api_lib_utils.GetApplicationRef(args)
    return client.Update(args, app_ref, release_track=base.ReleaseTrack.ALPHA)
