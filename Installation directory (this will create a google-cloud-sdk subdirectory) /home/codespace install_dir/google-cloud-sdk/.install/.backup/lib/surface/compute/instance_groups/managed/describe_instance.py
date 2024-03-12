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
"""Command for creating instance with per instance config."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import request_helper
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute import scope as compute_scope
from googlecloudsdk.command_lib.compute.instance_groups import flags as instance_groups_flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class DescribeInstance(base.DescribeCommand):
  """Describe an instance in a managed instance group."""

  @staticmethod
  def Args(parser):
    instance_groups_flags.GetInstanceGroupManagerArg(
        region_flag=True).AddArgument(
            parser, operation_type='describe an instance in')
    parser.add_argument(
        '--instance',
        required=True,
        help='Name of the managed instance to describe.')

  def Run(self, args):
    """Retrieves response with instance in the instance group."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client
    resources = holder.resources

    group_ref = (
        instance_groups_flags.MULTISCOPE_INSTANCE_GROUP_MANAGER_ARG
        .ResolveAsResource(
            args,
            holder.resources,
            default_scope=compute_scope.ScopeEnum.ZONE,
            scope_lister=compute_flags.GetDefaultScopeLister(client)))

    if hasattr(group_ref, 'zone'):
      service = client.apitools_client.instanceGroupManagers
      request = (
          client.messages
          .ComputeInstanceGroupManagersListManagedInstancesRequest(
              instanceGroupManager=group_ref.Name(),
              zone=group_ref.zone,
              project=group_ref.project))
    elif hasattr(group_ref, 'region'):
      service = client.apitools_client.regionInstanceGroupManagers
      request = (
          client.messages
          .ComputeRegionInstanceGroupManagersListManagedInstancesRequest(
              instanceGroupManager=group_ref.Name(),
              region=group_ref.region,
              project=group_ref.project))

    errors = []
    results = list(
        request_helper.MakeRequests(
            requests=[(service, 'ListManagedInstances', request)],
            http=client.apitools_client.http,
            batch_url=client.batch_url,
            errors=errors))

    if errors:
      utils.RaiseToolException(errors)
    instance_with_name = next(
        (instance for instance in results
         if resources.ParseURL(instance.instance).Name() == args.instance),
        None)
    if not instance_with_name:
      raise ValueError('Unknown instance with name `{0}\''.format(args.name))
    # Add name to instance and return it
    instance_with_name = encoding.MessageToDict(instance_with_name)
    instance_with_name['name'] = (
        resources.ParseURL(instance_with_name['instance']).Name())
    return instance_with_name


DescribeInstance.detailed_help = {
    'brief':
        'Describe an instance in a managed instance group.',
    'DESCRIPTION':
        """\
          *{command}* describes an instance in a managed instance group, listing
          all its attributes in YAML format.
        """,
    'EXAMPLES':
        """\
        To describe an instance `instance-1` in `my-group`
        (in region europe-west4), run:

            $ {command} \\
                  my-group --instance=instance-1 \\
                  --region=europe-west4
        """
}
