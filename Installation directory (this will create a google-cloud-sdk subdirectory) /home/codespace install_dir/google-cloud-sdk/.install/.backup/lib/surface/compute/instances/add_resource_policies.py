# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command for adding resource policies to instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags as instance_flags
from googlecloudsdk.command_lib.compute.resource_policies import flags
from googlecloudsdk.command_lib.compute.resource_policies import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class InstancesAddResourcePolicies(base.UpdateCommand):
  """Add resource policies to Compute Engine VM instances.

    *{command}* adds resource policies to Compute Engine
    virtual instances. These policies define time windows in which
    live migrations take place.

    ## EXAMPLES

    To add resource policy ``pol1'' to instance ``inst1'', run this:

      $ {command} inst1 --resource-policies=pol1

    For information on how to create resource policies, see:

      $ gcloud compute resource-policies create --help

  """

  @staticmethod
  def Args(parser):
    instance_flags.INSTANCE_ARG.AddArgument(
        parser, operation_type='add resource policies to')
    flags.AddResourcePoliciesArgs(parser, 'added to', 'instance', required=True)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    messages = client.messages

    instance_ref = instance_flags.INSTANCE_ARG.ResolveAsResource(
        args,
        holder.resources,
        scope_lister=instance_flags.GetInstanceZoneScopeLister(client))

    resource_policies = []
    for policy in args.resource_policies:
      resource_policy_ref = util.ParseResourcePolicyWithZone(
          holder.resources,
          policy,
          project=instance_ref.project,
          zone=instance_ref.zone)
      resource_policies.append(resource_policy_ref.SelfLink())

    add_request = messages.ComputeInstancesAddResourcePoliciesRequest(
        instance=instance_ref.Name(),
        project=instance_ref.project,
        zone=instance_ref.zone,
        instancesAddResourcePoliciesRequest=
        messages.InstancesAddResourcePoliciesRequest(
            resourcePolicies=resource_policies))

    return client.MakeRequests([(client.apitools_client.instances,
                                 'AddResourcePolicies', add_request)])
