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

"""`gcloud iot registries credentials delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudiot import registries
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iot import flags
from googlecloudsdk.command_lib.iot import resource_args
from googlecloudsdk.command_lib.iot import util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a credential from a registry."""

  detailed_help = {
      'EXAMPLES':
          """\
          To delete the first credential from a registry, run:

            $ {command} --region=us-central1 --registry=my-registry 0
          """,
  }

  @staticmethod
  def Args(parser):
    resource_args.AddRegistryResourceArg(parser,
                                         'from which to delete credentials',
                                         positional=False)
    flags.GetIndexFlag('credential', 'to delete').AddToParser(parser)

  def Run(self, args):
    client = registries.RegistriesClient()

    registry_ref = args.CONCEPTS.registry.Parse()

    credentials = client.Get(registry_ref).credentials
    try:
      credential = credentials.pop(args.index)
    except IndexError:
      raise util.BadCredentialIndexError(registry_ref.Name(), credentials,
                                         args.index, resource='registry')
    console_io.PromptContinue(
        message='This will delete the following credential: {}'.format(
            credential),
        cancel_on_no=True)
    response = client.Patch(registry_ref, credentials=credentials)
    log.DeletedResource(
        registry_ref.Name(),
        'credential at index [{}] for registry'.format(args.index))
    return response
