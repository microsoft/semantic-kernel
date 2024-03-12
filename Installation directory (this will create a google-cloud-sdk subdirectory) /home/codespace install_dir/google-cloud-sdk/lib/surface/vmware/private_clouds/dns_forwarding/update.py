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
"""'vmware dns-forwarding update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

_DETAILED_HELP = {
    'DESCRIPTION': """
        Update DNS forwarding.
      """,
    'EXAMPLES': """
        To update a DNS forwarding config in private cloud `my-private-cloud` and zone `us-west2-a` to forward DNS requests
        for domain `activedirectory.my.corp` to name servers `192.168.20.15` and `192.168.20.16`
        and for domain `proxy.my.corp` to nameservers `192.168.30.15` and `192.168.30.16`, run:

          $ {command} --location=us-west2-a --project=my-project --private-cloud=my-private-cloud  --rule=domain=activedirectory.my.corp,name-servers=192.168.20.15;192.168.20.16 --rule=domain=proxy.my.corp,name-servers=192.168.30.15;192.168.30.16

          Or:

          $ {command} --private-cloud=my-private-cloud --rule=domain=activedirectory.my.corp,name-servers=192.168.20.15;192.168.20.16 --rule=domain=proxy.my.corp,name-servers=192.168.30.15;192.168.30.16

         In the second example, the project and location are taken from gcloud properties core/project and compute/zone.
  """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Google Cloud VMware Engine dns-forwarding."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=False)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, True)
    parser.add_argument(
        '--rule',
        type=arg_parsers.ArgDict(
            required_keys=['domain', 'name-servers'],
            spec={
                'domain': str,
                'name-servers': arg_parsers.ArgList(custom_delim_char=';')
            }
        ),
        action='append',
        required=False,
        default=[],
        metavar='domain=DOMAIN,name-servers="NAME_SERVER1;NAME_SERVER2[;NAME_SERVER3]"',
        help="""\
            Domain name and the name servers used to resolve DNS requests for this domain.
            """,
    )

  def Run(self, args):
    privatecloud = args.CONCEPTS.private_cloud.Parse()
    client = PrivateCloudsClient()
    is_async = args.async_
    operation = client.UpdateDnsForwarding(privatecloud, args.rule)
    if is_async:
      log.UpdatedResource(operation.name, kind='dns forwarding', is_async=True)
      return operation

    _ = client.WaitForOperation(
        operation_ref=client.GetOperationRef(operation),
        message=(
            'waiting for DNS forwarding of private cloud [{}] to be updated'
            .format(privatecloud.RelativeName())
        ),
    )
    resource = client.GetDnsForwarding(privatecloud)
    log.UpdatedResource(resource, kind='dns forwarding')

    return resource
