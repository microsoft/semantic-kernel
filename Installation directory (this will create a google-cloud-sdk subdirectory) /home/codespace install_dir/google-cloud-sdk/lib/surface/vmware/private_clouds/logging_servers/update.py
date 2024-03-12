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
"""'vmware logging-server update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.loggingservers import LoggingServersClient
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': """
        Update a Logging Server. Only source_type, hostname, protocol, port can be updated.
      """,
    'EXAMPLES': """
        To update a logging-server called `my-logging-server` in private cloud `my-private-cloud` and zone `us-west2-a` to change `ESXI` source_type, `192.168.20.15` hostname
        `UDP` protocol and `514` port, run:

          $ {command} my-logging-server --location=us-west2-a --project=my-project --private-cloud=my-private-cloud --source-type=ESXI --hostname=192.168.20.15 --protocol=UDP --port=514

          Or:

          $ {command} my-logging-server --private-cloud=my-private-cloud --source-type=ESXI --hostname=192.168.20.15 --protocol=UDP --port=514

         In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
  """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Cloud VMware Engine logging-server."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLoggingServerArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.display_info.AddFormat('yaml')
    parser.add_argument(
        '--hostname',
        help="""\
            Fully-qualified domain name (FQDN) or IP Address of the logging server.
            """,
    )
    parser.add_argument(
        '--source-type',
        choices=['VCSA', 'ESXI'],
        help="""\
            The type of component that produces logs that will be forwarded
            to this logging server.
            """,
    )
    parser.add_argument(
        '--protocol',
        choices=['UDP', 'TCP', 'TLS', 'RELP', 'SSL'],
        help="""\
            Defines possible protocols used to send logs to
            a logging server.
            """,
    )
    parser.add_argument(
        '--port',
        type=arg_parsers.BoundedInt(0, 65535),
        help="""\
            Port number at which the logging server receives logs.
            """,
    )

  def Run(self, args):
    logging_server = args.CONCEPTS.logging_server.Parse()
    client = LoggingServersClient()
    operation = client.Update(
        logging_server,
        args.hostname,
        args.source_type,
        args.protocol,
        args.port,
    )
    is_async = args.async_

    if is_async:
      log.UpdatedResource(operation.name, kind='logging-server', is_async=True)
      return

    resource = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for logging-server [{}] to be updated'.format(
            logging_server.RelativeName()
        ),
    )
    log.UpdatedResource(logging_server.RelativeName(), kind='logging-server')
    return resource
