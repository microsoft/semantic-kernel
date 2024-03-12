# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Command for updating groups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_api
from googlecloudsdk.api_lib.network_connectivity import networkconnectivity_util
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_connectivity import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.args import repeated
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


@base.ReleaseTracks(base.ReleaseTrack.GA)
@base.Hidden
class Update(base.Command):
  """Update a group.

  Update the details of a group.
  """

  @staticmethod
  def Args(parser):
    flags.AddGroupResourceArg(parser, 'to update')
    flags.AddDescriptionFlag(parser, 'New description of the group.')
    flags.AddAsyncFlag(parser)
    labels_util.AddUpdateLabelsFlags(parser)
    repeated.AddPrimitiveArgs(
        parser, 'group', 'auto-accept-projects', 'auto-accept projects',
        additional_help="""This controls the list of project ids or
        project numbers for which auto-accept is enabled for the group.""",
        include_set=False)

  def Run(self, args):
    client = networkconnectivity_api.GroupsClient(
        release_track=self.ReleaseTrack())

    group_ref = args.CONCEPTS.group.Parse()
    update_mask = []
    description = args.description
    if description is not None:
      update_mask.append('description')

    labels = None
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    original_group = client.Get(group_ref)
    if labels_diff.MayHaveUpdates():
      labels_update = labels_diff.Apply(client.messages.Group.LabelsValue,
                                        original_group.labels)
      if labels_update.needs_update:
        labels = labels_update.labels
        update_mask.append('labels')

    auto_accept_projects = repeated.ParsePrimitiveArgs(
        args, 'auto_accept_projects',
        lambda: original_group.autoAccept.autoAcceptProjects)
    auto_accept = None
    if auto_accept_projects is not None:
      auto_accept = client.messages.AutoAccept(
          autoAcceptProjects=auto_accept_projects)
      update_mask.append('auto_accept.auto_accept_projects')

    # Construct a group message with only the updated fields
    group = client.messages.Group(description=description, labels=labels,
                                  autoAccept=auto_accept)

    op_ref = client.UpdateGroup(group_ref, group, update_mask)

    log.status.Print('Update request issued for: [{}]'.format(group_ref.Name()))

    if op_ref.done:
      log.UpdatedResource(group_ref.Name(), kind='group')
      return op_ref

    if args.async_:
      log.status.Print('Check operation [{}] for status.'.format(op_ref.name))
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='networkconnectivity.projects.locations.operations',
        api_version=networkconnectivity_util.VERSION_MAP[self.ReleaseTrack()])
    poller = waiter.CloudOperationPoller(client.group_service,
                                         client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.UpdatedResource(group_ref.Name(), kind='group')
    return res

Update.detailed_help = {
    'EXAMPLES':
        """\
  To update the description of a group named ``my-group'', in the hub ``my-hub'', run:

    $ {command} my-group --hub=my-hub --description="new group description"

  To add the project ``my-project'' to the auto-accept list of a group named ``my-group'' in the hub ``my-hub'', run:

    $ {command} my-group --hub=my-hub --add-auto-accept-projects=my-project
  """,
    'API REFERENCE':
        """ \
  This command uses the networkconnectivity/v1 API. The full documentation
  for this API can be found at:
  https://cloud.google.com/network-connectivity/docs/reference/networkconnectivity/rest
  """,
}
