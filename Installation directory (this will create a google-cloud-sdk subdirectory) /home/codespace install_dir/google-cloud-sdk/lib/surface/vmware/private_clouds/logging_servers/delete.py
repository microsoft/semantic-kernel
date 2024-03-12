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
"""'vmware logging-server delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.loggingservers import LoggingServersClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': """
        Delete logging-server from a VMware Engine private cloud.
      """,
    'EXAMPLES': """
        To delete an logging-server called `my-logging-server` in private cloud
        `my-private-cloud` and location `us-east2-b`, run:

          $ {command} my-logging-server --private-cloud=my-private-cloud --location=us-east2-b --project=my-project

        Or:

          $ {command} my-logging-server --private-cloud=my-private-cloud

        In the second example, the project and region are taken from gcloud properties core/project and vmware/region.
  """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete logging-server from a VMware Engine private cloud."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddLoggingServerArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)

  def Run(self, args):
    logging_server = args.CONCEPTS.logging_server.Parse()
    client = LoggingServersClient()
    is_async = args.async_
    operation = client.Delete(logging_server)
    if is_async:
      log.DeletedResource(operation.name, kind='logging-server', is_async=True)
      return operation

    client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message='waiting for logging-server [{}] to be deleted'.format(
            logging_server.RelativeName()
        ),
        has_result=False,
    )

    log.DeletedResource(
        logging_server.RelativeName(), kind='logging-server', is_async=False
    )
