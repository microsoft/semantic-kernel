# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command for setting instance template of managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags
from googlecloudsdk.command_lib.compute.instance_groups.managed import flags as managed_flags


@base.ReleaseTracks(base.ReleaseTrack.GA)
class SetInstanceTemplateGA(base.Command):
  r"""Command for setting instance template of managed instance group."""

  @classmethod
  def Args(cls, parser):
    managed_flags.INSTANCE_TEMPLATE_ARG.AddArgument(parser)
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    resource_arg = instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
    default_scope = compute_scope.ScopeEnum.ZONE
    scope_lister = flags.GetDefaultScopeLister(client)
    igm_ref = resource_arg.ResolveAsResource(
        args,
        holder.resources,
        default_scope=default_scope,
        scope_lister=scope_lister)

    template_ref = managed_flags.INSTANCE_TEMPLATE_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=flags.compute_scope.ScopeEnum.GLOBAL,
    )

    return self._MakePatchRequest(client, igm_ref, template_ref)

  def _MakePatchRequest(self, client, igm_ref, template_ref):
    messages = client.messages

    igm_resource = messages.InstanceGroupManager(
        instanceTemplate=template_ref.SelfLink(),
        versions=[
            messages.InstanceGroupManagerVersion(
                instanceTemplate=template_ref.SelfLink())
        ])

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = client.apitools_client.instanceGroupManagers
      request_type = messages.ComputeInstanceGroupManagersPatchRequest
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = client.apitools_client.regionInstanceGroupManagers
      request_type = messages.ComputeRegionInstanceGroupManagersPatchRequest
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    request = request_type(**igm_ref.AsDict())
    request.instanceGroupManagerResource = igm_resource

    return client.MakeRequests([(service, 'Patch', request)])


SetInstanceTemplateGA.detailed_help = {
    'brief': 'Set the instance template for a managed instance group.',
    'DESCRIPTION': """
      *{command}* sets the instance template for an existing managed instance
    group.

    The new template applies to all new instances added to the managed instance
    group.

    To apply the new template to existing instances in the group, use one of the
    following methods:

    - Update instances using the `update-instances` command.
    - Recreate instances using the `recreate-instances` command.
    - Use the `rolling-action start-update` command.
    - Use the API to set the group's `updatePolicy.type` to `PROACTIVE`.

    """,
    'EXAMPLES': """
    Running:

          {command} \\
          example-managed-instance-group --template=example-global-instance-template

    Sets the instance template for the 'example-managed-instance-group' group
    to a global resource 'example-global-instance-template'.

    To use a regional instance template, specify the full or partial URL of the template.

    Running:

          {command} \\
          example-managed-instance-group \\
          --template=projects/example-project/regions/us-central1/instanceTemplates/example-regional-instance-template

    Sets the instance template for the 'example-managed-instance-group' group
    to a regional resource 'example-regional-instance-template'.
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class SetInstanceTemplate(SetInstanceTemplateGA):
  r"""Command for setting instance template of managed instance group."""

  @classmethod
  def Args(cls, parser):
    super(SetInstanceTemplate, cls).Args(parser)

  def Run(self, args):
    patch_request = super(SetInstanceTemplate, self).Run(args)

    return patch_request


SetInstanceTemplate.detailed_help = SetInstanceTemplateGA.detailed_help
