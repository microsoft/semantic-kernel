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
"""Command to delete SSL policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.api_lib.compute.operations import poller
from googlecloudsdk.api_lib.compute.ssl_policies import ssl_policies_utils
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.ssl_policies import flags


class DeleteBatchPoller(poller.BatchPoller):

  def __init__(self, compute_adapter, resource_service, target_refs=None):
    super(DeleteBatchPoller, self).__init__(compute_adapter, resource_service,
                                            target_refs)

  def GetResult(self, operation_batch):
    # For delete operations, once the operation status is DONE, there is
    # nothing further to fetch.
    return


class Delete(base.DeleteCommand):
  """Delete Compute Engine SSL policies.

  *{command}* is used to delete one or more Compute Engine SSL policies.
  SSL policies can only be deleted when no other resources (e.g.,
  Target HTTPS proxies, Target SSL proxies) refer to them.

  An SSL policy specifies the server-side support for SSL features. An SSL
  policy can be attached to a TargetHttpsProxy or a TargetSslProxy. This affects
  connections between clients and the load balancer. SSL
  policies do not affect the connection between the load balancers and the
  backends. SSL policies are used by Application Load Balancers and proxy
  Network Load Balancers.
  """

  SSL_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddCacheUpdater(flags.SslPoliciesCompleter)
    cls.SSL_POLICY_ARG = flags.GetSslPolicyMultiScopeArgument(plural=True)
    cls.SSL_POLICY_ARG.AddArgument(parser, operation_type='delete')

  def Run(self, args):
    """Issues the request to delete a SSL policy."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    helper = ssl_policies_utils.SslPolicyHelper(holder)
    client = holder.client.apitools_client
    refs = self.SSL_POLICY_ARG.ResolveAsResource(
        args, holder.resources, default_scope=compute_scope.ScopeEnum.GLOBAL)
    utils.PromptForDeletion(refs)

    operation_refs = [helper.Delete(ref) for ref in refs]
    wait_message = 'Deleting SSL {}'.format(
        ('policies' if (len(operation_refs) > 1) else 'policy'))
    operation_poller = DeleteBatchPoller(holder.client, client.sslPolicies)
    return waiter.WaitFor(operation_poller,
                          poller.OperationBatch(operation_refs), wait_message)
