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
"""Command to generate install manifest for Attached cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import locations as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import flags as attached_flags
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log

_EXAMPLES = """
To generate install manifest for cluster named ``my-cluster'' managed in location ``us-west1'', run:

$ {command} my-cluster --location=us-west1 --platform-version=PLATFORM_VERSION

To store the manifest in a file named ``manifest.yaml'', run:

$ {command} my-cluster --location=us-west1 --platform-version=PLATFORM_VERSION --output-file=manifest.yaml
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.Command):
  """Generate Install Manifest for an Attached cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddAttachedClusterResourceArg(
        parser, 'to generate install manifest'
    )

    attached_flags.AddPlatformVersion(parser)
    attached_flags.AddProxyConfig(parser)
    flags.AddOutputFile(parser, 'to store manifest')

  def Run(self, args):
    """Runs the generate-install-manifest command."""
    location = resource_args.ParseAttachedClusterResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      cluster_ref = resource_args.ParseAttachedClusterResourceArg(args)
      client = api_util.LocationsClient()
      resp = client.GenerateInstallManifest(cluster_ref, args=args)
      if args.output_file:
        log.WriteToFileOrStdout(
            args.output_file,
            resp.manifest,
            overwrite=True,
            binary=False,
            private=True,
        )
        return None

      return resp
