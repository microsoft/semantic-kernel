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

"""gcloud dns managed-zone delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete an empty Cloud DNS managed-zone.

  This command deletes an empty Cloud DNS managed-zone. An empty managed-zone
  has only SOA and NS record-sets.

  ## EXAMPLES

  To delete an empty managed-zone, run:

    $ {command} my-zone

  To delete an empty zonal managed-zone in us-east1-c, run:

    $ {command} my-zone --location=us-east1-c
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    flags.GetDnsZoneArg(
        'The name of the empty managed-zone to be deleted.').AddToParser(parser)
    flags.GetLocationArg().AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    dns = util.GetApiClient(api_version)
    registry = util.GetRegistry(api_version)

    zone_ref = registry.Parse(
        args.dns_zone,
        util.GetParamsForRegistry(api_version, args),
        collection='dns.managedZones')
    request = dns.MESSAGES_MODULE.DnsManagedZonesDeleteRequest(
        managedZone=zone_ref.managedZone, project=zone_ref.project)

    if api_version == 'v2':
      # For a request with location, use v2 api.
      request.location = args.location

    result = dns.managedZones.Delete(request)
    log.DeletedResource(zone_ref)
    return result
