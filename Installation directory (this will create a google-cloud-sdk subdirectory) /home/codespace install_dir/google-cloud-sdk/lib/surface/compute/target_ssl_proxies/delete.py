# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for deleting target SSL proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.target_ssl_proxies import flags


class Delete(base.DeleteCommand):
  """Delete target SSL proxy."""

  TARGET_SSL_PROXY_ARG = None

  @staticmethod
  def Args(parser):
    Delete.TARGET_SSL_PROXY_ARG = flags.TargetSslProxyArgument(plural=True)
    Delete.TARGET_SSL_PROXY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.TargetSslProxiesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    refs = self.TARGET_SSL_PROXY_ARG.ResolveAsResource(args, holder.resources)
    utils.PromptForDeletion(refs)

    client = holder.client.apitools_client
    messages = holder.client.messages

    requests = []
    for ref in refs:
      requests.append(
          (client.targetSslProxies,
           'Delete',
           messages.ComputeTargetSslProxiesDeleteRequest(
               project=ref.project, targetSslProxy=ref.Name())))

    errors = []
    resources = holder.client.MakeRequests(requests, errors)

    if errors:
      utils.RaiseToolException(errors)
    return resources


Delete.detailed_help = {
    'brief': 'Delete target SSL proxies',
    'DESCRIPTION': """\
        *{command}* deletes one or more target SSL proxies.
        """,
}
