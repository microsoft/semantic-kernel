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
"""Delete a CA pool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  r"""Delete a CA pool.

    Note that all certificate authorities must be removed from the CA Pool
    before the CA pool can be deleted.

    ## EXAMPLES

    To delete a CA pool:

      $ {command} my-pool --location=us-west1

    To delete a CA pool while skipping the confirmation input:

      $ {command} my-pool --location=us-west1 --quiet
  """

  @staticmethod
  def Args(parser):
    resource_args.AddCaPoolPositionalResourceArg(parser, 'to delete')
    flags.AddIgnoreDependentResourcesFlag(parser)

  def Run(self, args):
    client = privateca_base.GetClientInstance('v1')
    messages = privateca_base.GetMessagesModule('v1')

    ca_pool_ref = args.CONCEPTS.ca_pool.Parse()

    if args.ignore_dependent_resources:
      prompt_message = (
          'You are about to delete the CA Pool [{}] without '
          'checking if it is being used by another cloud '
          'resource. If you proceed, there may be unintended and '
          'unrecoverable effects on any dependent resource(s) since the '
          'CA Pool would not be able to issue certificates.'
      ).format(ca_pool_ref.RelativeName())
    else:
      prompt_message = ('You are about to delete the CA pool [{}]').format(
          ca_pool_ref.RelativeName())

    if not console_io.PromptContinue(
        message=prompt_message,
        default=True):
      log.status.Print('Aborted by user.')
      return

    operation = client.projects_locations_caPools.Delete(
        messages.PrivatecaProjectsLocationsCaPoolsDeleteRequest(
            name=ca_pool_ref.RelativeName(),
            ignoreDependentResources=args.ignore_dependent_resources,
            requestId=request_utils.GenerateRequestId()))

    operations.Await(
        operation, 'Deleting the CA pool', api_version='v1')

    log.status.Print('Deleted the CA pool [{}].'.format(
        ca_pool_ref.RelativeName()))
