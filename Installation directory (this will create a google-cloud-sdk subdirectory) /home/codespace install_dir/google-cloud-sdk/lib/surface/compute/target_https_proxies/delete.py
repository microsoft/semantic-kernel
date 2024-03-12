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
"""Command for deleting target HTTPS proxies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.target_https_proxies import flags
from googlecloudsdk.command_lib.compute.target_https_proxies import target_https_proxies_utils


def _DetailedHelp():
  return {
      'brief':
          'Delete target HTTPS proxies.',
      'DESCRIPTION':
          """\
      *{command}* deletes one or more target HTTPS proxies.
      """,
      'EXAMPLES':
          """\
      Delete a global target HTTPS proxy by running:

        $ {command} PROXY_NAME

      Delete a regional target HTTPS proxy by running:

        $ {command} PROXY_NAME --region=REGION_NAME
      """,
  }


def _Run(args, holder, target_https_proxy_arg):
  """Issues requests necessary to delete Target HTTPS Proxies."""
  client = holder.client

  target_https_proxy_refs = target_https_proxy_arg.ResolveAsResource(
      args,
      holder.resources,
      default_scope=compute_scope.ScopeEnum.GLOBAL,
      scope_lister=compute_flags.GetDefaultScopeLister(client))

  utils.PromptForDeletion(target_https_proxy_refs)

  requests = []
  for target_https_proxy_ref in target_https_proxy_refs:
    if target_https_proxies_utils.IsRegionalTargetHttpsProxiesRef(
        target_https_proxy_ref):
      requests.append(
          (client.apitools_client.regionTargetHttpsProxies, 'Delete',
           client.messages.ComputeRegionTargetHttpsProxiesDeleteRequest(
               **target_https_proxy_ref.AsDict())))
    else:
      requests.append((client.apitools_client.targetHttpsProxies, 'Delete',
                       client.messages.ComputeTargetHttpsProxiesDeleteRequest(
                           **target_https_proxy_ref.AsDict())))

  return client.MakeRequests(requests)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete target HTTPS proxies."""

  TARGET_HTTPS_PROXY_ARG = None
  detailed_help = _DetailedHelp()

  @classmethod
  def Args(cls, parser):
    cls.TARGET_HTTPS_PROXY_ARG = flags.TargetHttpsProxyArgument(plural=True)
    cls.TARGET_HTTPS_PROXY_ARG.AddArgument(parser, operation_type='delete')
    parser.display_info.AddCacheUpdater(flags.TargetHttpsProxiesCompleter)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    return _Run(args, holder, self.TARGET_HTTPS_PROXY_ARG)
