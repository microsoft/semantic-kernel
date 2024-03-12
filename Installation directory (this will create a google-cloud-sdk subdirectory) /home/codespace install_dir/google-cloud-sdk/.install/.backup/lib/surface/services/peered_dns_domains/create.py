# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""services peered-dns-domains create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.services import peering
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_OP_BASE_CMD = 'gcloud services vpc-peerings operations '
_OP_WAIT_CMD = _OP_BASE_CMD + 'wait {0}'


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA,
    base.ReleaseTrack.BETA,
    base.ReleaseTrack.GA,
)
class Create(base.SilentCommand):
  """Create a peered DNS domain for a private service connection."""

  detailed_help = {
      'DESCRIPTION':
          """\
          This command creates a peered DNS domain for a private service
          connection which sends requests for records in a given namespace
          originating in the service producer VPC network to the consumer
          VPC network to be resolved.
          """,
      'EXAMPLES':
          """\
          To create a peered DNS domain called `example-com` which forwards DNS
          requests for the domain suffix `example.com.` for a private service
          connection between service `peering-service` and the consumer network
          `my-network` in the current project, run:

            $ {command} example-com --network=my-network \\
                --service=peering-service --dns-suffix=example.com.

          To run the same command asynchronously (non-blocking), run:

            $ {command} example-com --network=my-network \\
                --service=peering-service --dns-suffix=example.com. \\
                --async
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        'name', help='The name of the peered DNS domain to create.')
    parser.add_argument(
        '--network',
        metavar='NETWORK',
        required=True,
        help='The network in the consumer project peered with the service.')
    parser.add_argument(
        '--service',
        metavar='SERVICE',
        default='servicenetworking.googleapis.com',
        help='The name of the service to create a peered DNS domain for.')
    parser.add_argument(
        '--dns-suffix',
        metavar='DNS_SUFFIX',
        required=True,
        help='The DNS domain name suffix of the peered DNS domain.')
    base.ASYNC_FLAG.AddToParser(parser)

  def Run(self, args):
    """Run 'services peered-dns-domains create'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.
    """
    project = properties.VALUES.core.project.Get(required=True)
    project_number = _GetProjectNumber(project)
    op = peering.CreatePeeredDnsDomain(
        project_number,
        args.service,
        args.network,
        args.name,
        args.dns_suffix,
    )
    if args.async_:
      cmd = _OP_WAIT_CMD.format(op.name)
      log.status.Print('Asynchronous operation is in progress... '
                       'Use the following command to wait for its '
                       'completion:\n {0}'.format(cmd))
      return
    op = services_util.WaitOperation(op.name, peering.GetOperation)
    services_util.PrintOperation(op)


def _GetProjectNumber(project_id):
  return projects_api.Get(projects_util.ParseProject(project_id)).projectNumber
