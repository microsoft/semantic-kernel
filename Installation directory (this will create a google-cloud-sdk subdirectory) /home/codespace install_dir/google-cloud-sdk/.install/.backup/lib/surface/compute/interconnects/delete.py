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

"""Command for deleting interconnects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.interconnects import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.interconnects import flags


class Delete(base.DeleteCommand):
  """Delete Compute Engine interconnects.

  *{command}* deletes Compute Engine interconnects. Interconnects
   can only be deleted when no other resources (e.g.,
   InterconnectAttachments) refer to them.
  """

  INTERCONNECT_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.INTERCONNECT_ARG = flags.InterconnectArgument(plural=True)
    cls.INTERCONNECT_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.InterconnectsCompleter)

  def Collection(self):
    return 'compute.interconnects'

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    refs = self.INTERCONNECT_ARG.ResolveAsResource(args, holder.resources)
    utils.PromptForDeletion(refs)

    requests = []
    for ref in refs:
      interconnect = client.Interconnect(ref, compute_client=holder.client)
      requests.extend(interconnect.Delete(only_generate_request=True))

    return holder.client.MakeRequests(requests)
