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
"""Command for listing instance configs of a managed instance group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import instance_groups_utils
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List per-instance configs of a managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.AddArgument(
        parser, operation_type='list instance configs for')

    parser.display_info.AddFormat('yaml')
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    igm_ref = (instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG.
               ResolveAsResource)(
                   args,
                   resources,
                   scope_lister=compute_flags.GetDefaultScopeLister(client),
               )

    if igm_ref.Collection() == 'compute.instanceGroupManagers':
      service = client.apitools_client.instanceGroupManagers
      request = (client.messages.
                 ComputeInstanceGroupManagersListPerInstanceConfigsRequest)(
                     instanceGroupManager=igm_ref.Name(),
                     project=igm_ref.project,
                     zone=igm_ref.zone,
                 )
    elif igm_ref.Collection() == 'compute.regionInstanceGroupManagers':
      service = client.apitools_client.regionInstanceGroupManagers
      request = (
          client.messages.
          ComputeRegionInstanceGroupManagersListPerInstanceConfigsRequest)(
              instanceGroupManager=igm_ref.Name(),
              project=igm_ref.project,
              region=igm_ref.region,
          )
    else:
      raise ValueError('Unknown reference type {0}'.format(
          igm_ref.Collection()))

    errors = []
    results = list(
        request_helper.MakeRequests(
            requests=[(service, 'ListPerInstanceConfigs', request)],
            http=client.apitools_client.http,
            batch_url=client.batch_url,
            errors=errors))

    if errors:
      utils.RaiseToolException(errors)

    return instance_groups_utils.UnwrapResponse(results, 'items')


List.detailed_help = {
    'brief':
        'List per-instance configs of a managed instance group.',
    'DESCRIPTION':
        """\
        *{command}* lists per-instance configs for each instance with preserved
        resources (like disks). The list is presented by default in the form of
        a tree (YAML) due to a potential for having multiple resources defined
        in a single per-instance config.
        """,
    'EXAMPLES':
        """\
        To list all the per-instance configs for the managed instance group
        ``my-group'', run:

          $ {command} my-group --region=europe-west4
        """
}
