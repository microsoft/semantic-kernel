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

"""gcloud dns managed-zones list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.dns import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import properties


def _GetUriFunction(api_version):
  def _GetUri(resource):
    return util.GetRegistry(api_version).Create(
        'dns.managedZones',
        project=properties.VALUES.core.project.GetOrFail,
        managedZone=resource.name).SelfLink()
  return _GetUri


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """View the list of all your managed-zones.

  This command displays the list of your managed-zones.

  ## EXAMPLES

  To see the list of all managed-zones, run:

    $ {command}

  To see the list of first 10 managed-zones, run:

    $ {command} --limit=10

  To see the list of all managed-zones in a Zonal Cloud DNS service in
  us-east1-c, run:

    $ {command} --location=us-east1-c
  """

  @classmethod
  def _BetaOrAlpha(cls):
    return cls.ReleaseTrack() in (base.ReleaseTrack.BETA,
                                  base.ReleaseTrack.ALPHA)

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat('table(name, dnsName, description,'
                                  ' visibility)')
    parser.display_info.AddUriFunc(
        _GetUriFunction(util.GetApiFromTrack(cls.ReleaseTrack())))
    flags.GetLocationArg().AddToParser(parser)

  def Run(self, args):
    api_version = util.GetApiFromTrackAndArgs(self.ReleaseTrack(), args)
    dns_client = util.GetApiClient(api_version)

    project_id = properties.VALUES.core.project.GetOrFail()

    request = dns_client.MESSAGES_MODULE.DnsManagedZonesListRequest(
        project=project_id)
    # For a request with location, use v2 api.
    if api_version == 'v2':
      request.location = args.location

    return list_pager.YieldFromList(
        dns_client.managedZones, request, field='managedZones')
