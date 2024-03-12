# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Export Binary Authorization system policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.api_lib.container.binauthz import system_policy
from googlecloudsdk.api_lib.container.binauthz import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.binauthz import arg_parsers


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ExportSystemPolicy(base.Command):
  """Export the Binary Authorization system policy.

  For reliability reasons, the system policy is updated one region at a time.
  Because of this precaution, the system policy can differ between regions
  during an update. Use --location to view the system policy of a specific
  region.

  If --location is not specified, an arbitrary region is used. (Specifically, a
  region in the last group of regions to receive updates. Since most changes are
  additions, this will show the minimal set of system images that are allowed
  in all regions.)

  ## EXAMPLES

  To view the system policy:

      $ {command}

  To view the system policy in the region us-central1:

      $ {command} --location=us-central1
  """

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        '--location',
        # Although the name is "location" for consistency with other gcloud
        # commands, only regions are allowed (not other locations, like zones).
        choices=arg_parsers.BINAUTHZ_ENFORCER_REGIONS,
        required=False,
        default='global',
        help='The region for which to get the system policy (or "global").')

  def Run(self, args):
    api_version = apis.GetApiVersion(self.ReleaseTrack())
    return system_policy.Client(api_version).Get(
        util.GetSystemPolicyRef(args.location))
