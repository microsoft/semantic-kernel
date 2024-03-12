# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Delete public delegated prefixes command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import public_delegated_prefixes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.public_delegated_prefixes import flags
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  r"""Deletes a Compute Engine public delegated prefix.

  ## EXAMPLES

  To delete a public delegated prefix:

    $ {command} my-public-delegated-prefix --global
  """

  @staticmethod
  def Args(parser):
    flags.MakePublicDelegatedPrefixesArg().AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    pdp_client = public_delegated_prefixes.PublicDelegatedPrefixesClient(
        holder.client, holder.client.messages, holder.resources)

    pdp_ref = flags.MakePublicDelegatedPrefixesArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(holder.client))
    console_io.PromptContinue(
        'You are about to delete public delegated prefix: [{}]'.format(
            pdp_ref.Name()),
        throw_if_unattended=True,
        cancel_on_no=True)

    result = pdp_client.Delete(pdp_ref)
    log.DeletedResource(pdp_ref.Name(), 'public delegated prefix')
    return result
