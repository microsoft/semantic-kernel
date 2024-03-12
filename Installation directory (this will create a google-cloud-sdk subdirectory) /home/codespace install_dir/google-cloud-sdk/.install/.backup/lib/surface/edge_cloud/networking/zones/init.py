# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command to initialize a Distributed Cloud Edge Network zone."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.edge_cloud.networking.zones import zones
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.edge_cloud.networking import resource_args
from googlecloudsdk.core import log

DESCRIPTION = ('Initialize a specified Distributed Cloud Edge Network zone.')
EXAMPLES = """\
    To initialize a Distributed Cloud Edge Network zone called
    'us-central1-edge-den1', run:

        $ {command} us-central1-edge-den1 --location=us-central1

   """


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class InitialzeZone(base.Command):
  """Initialize a specified Distributed Cloud Edge Network zone.

  *{command}* is used to initialize a Distributed Cloud Edge Network
  zone.
  """

  detailed_help = {'DESCRIPTION': DESCRIPTION, 'EXAMPLES': EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddZoneResourceArg(parser, 'to initialize', True)

  def Run(self, args):
    zones_client = zones.ZonesClient(self.ReleaseTrack())
    zone_ref = args.CONCEPTS.zone.Parse()
    log.status.Print('Starting to initialize the zone...')
    zones_client.InitializeZone(zone_ref)
    log.status.Print('Initialized zone [{0}].'.format(zone_ref.RelativeName()))
