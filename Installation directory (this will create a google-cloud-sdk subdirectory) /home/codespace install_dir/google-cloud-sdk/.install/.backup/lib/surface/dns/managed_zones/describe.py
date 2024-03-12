# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""gcloud dns managed-zone describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import managed_zones
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.dns import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """View the details of a Cloud DNS managed-zone.

  This command displays the details of the specified managed-zone.

  ## EXAMPLES

  To display the details of your managed-zone, run:

    $ {command} my-zone

  To display the details of a zonal managed-zone in Zonal Cloud DNS service in
  us-east1-c, run:

    $ {command} my-zone --location=us-east1-c
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    flags.GetZoneResourceArg(
        'The name of the managed-zone to be described.').AddToParser(parser)
    flags.GetLocationArg().AddToParser(parser)

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    location = args.location if api_version == 'v2' else None
    zones_client = managed_zones.Client.FromApiVersion(api_version, location)
    registry = util.GetRegistry(api_version)

    zone_ref = registry.Parse(
        args.zone,
        util.GetParamsForRegistry(api_version, args),
        collection='dns.managedZones')
    # This is a special case in that the . and .. mess up the URI in the HTTP
    # request.  All other bad arguments are handled server side.
    if zone_ref.managedZone == '.' or zone_ref.managedZone == '..':
      raise exceptions.BadArgumentException('describe', zone_ref.managedZone)
    return zones_client.Get(zone_ref)
