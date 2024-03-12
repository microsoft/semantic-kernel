# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""`gcloud iot registries credentials create` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import registries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core import log


class Create(base.CreateCommand):
  """Add a new credential to a registry.

  A registry may have at most 10 credentials.
  """

  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To add a credential located in '/path/to/cert.pem' to a registry, run:

            $ {command} --region=us-central1 --registry=my-registry --path=/path/to/cert.pem
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddRegistryResourceArg(parser,
                                         'for which to create credentials',
                                         positional=False)
    flags.AddDeviceRegistryCredentialFlagsToParser(parser)

  def Run(self, args):
    client = registries.RegistriesClient()

    registry_ref = args.CONCEPTS.registry.Parse()
    new_credential = util.ParseRegistryCredential(args.path,
                                                  messages=client.messages)

    credentials = client.Get(registry_ref).credentials
    credentials.append(new_credential)
    response = client.Patch(registry_ref, credentials=credentials)
    log.CreatedResource(registry_ref.Name(), 'credentials for registry')
    return response
