# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.  #
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

"""Command to list all credentials for a registry."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import registries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.core.resource import resource_projector


class List(base.ListCommand):
  """List credentials for a registry."""

  detailed_help = {
      'EXAMPLES':
          """\
          To list the credentials of a registry, run:

            $ {command} --region=us-central1 --registry=my-registry
          """,
  }

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat(
        'table(index, publicKeyCertificate.format,'
        'publicKeyCertificate.x509Details.issuer,'
        'publicKeyCertificate.x509Details.subject,'
        'publicKeyCertificate.x509Details.startTime,'
        'publicKeyCertificate.x509Details.expiryTime,'
        'publicKeyCertificate.x509Details.signatureAlgorithm,'
        'publicKeyCertificate.x509Details.publicKeyType)')

    base.URI_FLAG.RemoveFromParser(parser)
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    resource_args.AddRegistryResourceArg(parser,
                                         'for which to list credentials',
                                         positional=False)

  def Run(self, args):
    """Run the list command."""
    client = registries.RegistriesClient()

    registry_ref = args.CONCEPTS.registry.Parse()

    registry = client.Get(registry_ref)
    for idx, credential in enumerate(registry.credentials):
      serializable = resource_projector.MakeSerializable(credential)
      serializable['index'] = idx
      yield serializable
