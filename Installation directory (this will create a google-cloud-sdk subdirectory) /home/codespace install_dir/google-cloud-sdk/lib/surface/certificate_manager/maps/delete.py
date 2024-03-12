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
"""`gcloud certificate-manager maps delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.certificate_manager import certificate_maps
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.certificate_manager import flags
from googlecloudsdk.command_lib.certificate_manager import resource_args
from googlecloudsdk.command_lib.certificate_manager import util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a certificate map.

  Delete a certificate map resource.

  ## EXAMPLES

  To delete the certificate map with name simple-map, run:

    $ {command} simple-map
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateMapResourceArg(parser, 'to delete')
    flags.AddAsyncFlagToParser(parser)

  def Run(self, args):
    client = certificate_maps.CertificateMapClient()
    map_ref = args.CONCEPTS.map.Parse()

    console_io.PromptContinue(
        'You are about to delete certificate map \'{}\''.format(
            map_ref.certificateMapsId),
        throw_if_unattended=True,
        cancel_on_no=True)

    response = client.Delete(map_ref)

    response = util.WaitForOperation(response, is_async=args.async_)
    log.DeletedResource(map_ref.Name(), 'map', is_async=args.async_)
    return response
