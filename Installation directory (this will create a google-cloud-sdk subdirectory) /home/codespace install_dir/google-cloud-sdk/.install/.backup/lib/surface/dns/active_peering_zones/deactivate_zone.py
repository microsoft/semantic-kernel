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
"""gcloud dns active-peering-zones deactivate command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Deactivate(base.DeleteCommand):
  """Deactivates a Cloud DNS peering zone.

  This command deactivates a Cloud DNS peering zone, removing any peering config
  and setting a deactivate time. Reponses sent to the deactivated zone will
  return REFUSED.

  ## EXAMPLES

  To deactivate a peering zone, run:

    $ {command} peering_zone_id
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneIdArg().AddToParser(parser)
    parser.display_info.AddCacheUpdater(None)

  def Run(self, args):
    dns = util.GetApiClient('v1alpha2')
    messages = apis.GetMessagesModule('dns', 'v1alpha2')

    result = dns.activePeeringZones.Deactivate(
        messages.DnsActivePeeringZonesDeactivateRequest(
            peeringZoneId=int(args.zone_id),
            project=properties.VALUES.core.project.GetOrFail()))
    return result
