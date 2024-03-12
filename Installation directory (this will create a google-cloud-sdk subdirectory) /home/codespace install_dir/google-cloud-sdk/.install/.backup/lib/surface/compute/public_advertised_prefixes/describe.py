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
"""Command for describing public advertised prefixes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.public_advertised_prefixes import flags


class Describe(base.DescribeCommand):
  """Describes a Compute Engine public advertised prefix.

  ## EXAMPLES

  To describe a public advertised prefix:

    $ {command} my-pap
  """

  @staticmethod
  def Args(parser):
    flags.MakePublicAdvertisedPrefixesArg().AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    pap_ref = flags.MakePublicAdvertisedPrefixesArg().ResolveAsResource(
        args,
        holder.resources,
        scope_lister=compute_flags.GetDefaultScopeLister(client))

    request = client.messages.ComputePublicAdvertisedPrefixesGetRequest(
        publicAdvertisedPrefix=pap_ref.Name(), project=pap_ref.project)

    return client.MakeRequests([
        (client.apitools_client.publicAdvertisedPrefixes, 'Get', request)
    ])[0]
