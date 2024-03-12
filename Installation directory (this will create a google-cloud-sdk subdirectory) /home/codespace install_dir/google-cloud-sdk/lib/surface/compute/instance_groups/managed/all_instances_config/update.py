# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Command for deleting values overridden in all-instances config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as managed_instance_groups_flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update all-instances-config of a managed instance group."""

  @classmethod
  def Args(cls, parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=True).AddArgument(
            parser, operation_type='update the all instances configuration for')
    managed_instance_groups_flags.AddFlagsForUpdateAllInstancesConfig(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
               .ResolveAsResource)(
                   args,
                   resources,
                   scope_lister=compute_flags.GetDefaultScopeLister(client),
               )

    if igm_ref.Collection() not in [
        'compute.instanceGroupManagers', 'compute.regionInstanceGroupManagers'
    ]:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    patch_instance_group_manager = self._CreateInstanceGroupManagerPatch(
        args, client)
    return self._MakePatchRequest(client, igm_ref, patch_instance_group_manager)

  def _CreateInstanceGroupManagerPatch(self, args, client):
    """Creates IGM resource patch."""
    return client.messages.InstanceGroupManager(
        allInstancesConfig=client.messages
        .InstanceGroupManagerAllInstancesConfig(
            properties=client.messages.InstancePropertiesPatch(
                metadata=client.messages.InstancePropertiesPatch.MetadataValue(
                    additionalProperties=[
                        client.messages.InstancePropertiesPatch.MetadataValue
                        .AdditionalProperty(key=key, value=value)
                        for key, value in args.metadata.items()
                    ]),
                labels=client.messages.InstancePropertiesPatch.LabelsValue(
                    additionalProperties=[
                        client.messages.InstancePropertiesPatch.LabelsValue
                        .AdditionalProperty(key=key, value=value)
                        for key, value in args.labels.items()
                    ]))))

  def _MakePatchRequest(self, client, igm_ref, igm_updated_resource):
    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = client.apitools_client.instanceGroupManagers
      request = client.messages.ComputeInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_updated_resource,
          project=igm_ref.project,
          zone=igm_ref.zone)
    else:
      service = client.apitools_client.regionInstanceGroupManagers
      request = client.messages.ComputeRegionInstanceGroupManagersPatchRequest(
          instanceGroupManager=igm_ref.Name(),
          instanceGroupManagerResource=igm_updated_resource,
          project=igm_ref.project,
          region=igm_ref.region)
    return client.MakeRequests([(service, 'Patch', request)])


Update.detailed_help = {
    'brief':
        'Update the all-instances configuration of a managed instance group.',
    'DESCRIPTION':
        """\
        *{command}* updates the group's all-instances configuration and applies
        it only to new instances that are added to the group.

        To apply a revised all-instances configuration to existing instances
        in the group, use one of the following methods:

        - Update instances using the `update-instances` command.
        - Recreate instances using the `recreate-instances` command.
        - Use the `rolling-action start-update` command.
        - Use the API to set the group's `updatePolicy.type` to `PROACTIVE`.
        """,
    'EXAMPLES':
        """\
        To update an all-instances configuration in order to override the
        group's instance template for a label with the key `label-key`
        and metadata with the key `metadata-key` in group `my-group`, run:

          $ {command} my-group
            --metadata=metadata-key=metadata-override-value
            --labels=qlabel-key=label-override-value
        """
}
