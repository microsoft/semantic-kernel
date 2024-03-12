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
"""'vmware logging-servers describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.loggingservers import LoggingServersClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags

_DETAILED_HELP = {
    'DESCRIPTION': """
        Display data associated with a VMware Engine logging-server, such as its host name, port, protocol, and source type.
      """,
    'EXAMPLES': """
        To describe a logging-server called `my-logging-server` in private cloud `my-private-cloud` and zone `us-west2-a`, run:

          $ {command} my-logging-server --location=us-west2-a --project=my-project --private-cloud=my-private-cloud

          Or:

          $ {command} my-logging-server --private-cloud=my-private-cloud

         In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
  """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe a Google Cloud VMware Engine logging-server."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLoggingServerArgToParser(parser)

  def Run(self, args):
    logging_server = args.CONCEPTS.logging_server.Parse()
    client = LoggingServersClient()
    return client.Get(logging_server)
