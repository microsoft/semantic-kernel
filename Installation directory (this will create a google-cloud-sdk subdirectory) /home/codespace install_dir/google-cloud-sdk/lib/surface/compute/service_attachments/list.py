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
"""Command for listing service attachments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.service_attachments import flags


def _Args(parser):
  parser.display_info.AddFormat(flags.DEFAULT_LIST_FORMAT)
  lister.AddRegionsArg(parser)
  parser.display_info.AddCacheUpdater(flags.ServiceAttachmentsCompleter)


def _Run(args, holder):
  """Issues requests necessary to list service attachments."""
  client = holder.client

  request_data = lister.ParseRegionalFlags(args, holder.resources)
  list_implementation = lister.RegionalLister(
      client, client.apitools_client.serviceAttachments)

  return lister.Invoke(request_data, list_implementation)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """List service attachments."""

  detailed_help = base_classes.GetRegionalListerHelp('service attachments')

  @classmethod
  def Args(cls, parser):
    _Args(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder)
