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
"""'vmware logging-server list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.loggingservers import LoggingServersClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

_DETAILED_HELP = {
    'DESCRIPTION': """
        List logging-server in a VMware Engine private cloud.
        """,
    'EXAMPLES': """
        To list logger-server in the `my-private-cloud` private cloud run:

          $ {command} --location=us-west2-a --project=my-project --private-cloud=my-private-cloud

          Or:

          $ {command} --private-cloud=my-private-cloud

        In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
  """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List logging-server in a Google Cloud VMware Engine private cloud."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser)
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,'
        'name.segment(-5):label=LOCATION,'
        'name.segment(-3):label=PRIVATE_CLOUD,'
        'sourceType,hostname,port,protocol,'
        'createTime)'
    )

  def Run(self, args):
    private_cloud = args.CONCEPTS.private_cloud.Parse()
    client = LoggingServersClient()
    return client.List(private_cloud)
