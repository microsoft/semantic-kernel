# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Command to lookup a Discovered Workload."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import discovered_workloads as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To lookup a discovered workload with uri `my-workload-uri` in location `us-east1` run:

          $ {command} --location=us-east1 --uri=my-workload-uri
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class LookupGA(base.DescribeCommand):
  """Lookup an Apphub discovered workload with URI."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddLookupDiscoveredWorkloadFlags(parser)
    parser.display_info.AddUriFunc(
        lambda x: x
    )  # TODO(b/327027327): Delete this.

  def Run(self, args):
    """Run the lookup command."""
    client = apis.DiscoveredWorkloadsClient(
        release_track=base.ReleaseTrack.GA
    )
    location_ref = args.CONCEPTS.location.Parse()
    return client.Lookup(parent=location_ref.RelativeName(), uri=args.uri)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class LookupAlpha(base.DescribeCommand):
  """Lookup an Apphub discovered workload with URI."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddLookupDiscoveredWorkloadFlags(parser)
    parser.display_info.AddUriFunc(
        lambda x: x
    )  # TODO(b/327027327): Delete this.

  def Run(self, args):
    """Run the lookup command."""
    client = apis.DiscoveredWorkloadsClient(
        release_track=base.ReleaseTrack.ALPHA
    )
    location_ref = args.CONCEPTS.location.Parse()
    return client.Lookup(parent=location_ref.RelativeName(), uri=args.uri)
