# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to get the public certificate of an Azure Client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64

from apitools.base.py import encoding
from googlecloudsdk.api_lib.container.gkemulticloud import azure as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.core import log


_EXAMPLES = """
To get the public certificate of an Azure client named ``my-client'' in
location ``us-west1'', run:

$ {command} my-client --location=us-west1

To store the certificate in a file named ``client.crt'', run:

$ {command} my-client --location=us-west1 --output-file=client.crt
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class GetPublicCert(base.DescribeCommand):
  """Get the public certificate of an Azure client."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClientResourceArg(
        parser, 'to get the public certificate'
    )
    flags.AddOutputFile(parser, 'to store PEM')

  def Run(self, args):
    """Runs the get-public-cert command."""
    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureClientResourceArg(args).locationsId,
        self.ReleaseTrack(),
    ):
      client_ref = resource_args.ParseAzureClientResourceArg(args)
      api_client = api_util.ClientsClient()
      client = api_client.Get(client_ref)
      cert = self._GetCert(client)
      log.WriteToFileOrStdout(
          args.output_file if args.output_file else '-',
          cert,
          overwrite=True,
          binary=False,
          private=True,
      )

  def _GetCert(self, client):
    if client.pemCertificate:
      return client.pemCertificate
    # Support older versions with certificate instead of pemCertificate.
    # This is needed because "certificate" was removed from the proto so
    # the apigen tool doesn't generate it in the AzureClient class.
    client_dict = encoding.MessageToPyValue(client)
    if 'certificate' in client_dict:
      return base64.b64decode(client_dict['certificate'].encode('utf-8'))
