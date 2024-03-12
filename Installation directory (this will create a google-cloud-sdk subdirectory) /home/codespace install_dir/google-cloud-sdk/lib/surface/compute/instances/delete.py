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
"""Command for deleting instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import utils
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import exceptions as compute_exceptions
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.core.console import console_io
from six.moves import zip


_INSTANCE_DELETE_PROMPT = 'The following instances will be deleted.'
_INSTANCE_DELETE_PROMPT_DISK_ADDENDUM = """\
Any attached disks configured to be auto-deleted will be deleted unless they \
are attached to any other instances or the `--keep-disks` flag is given and \
specifies them for keeping. \
Deleting a disk is irreversible and any data on the disk will be lost."""

# During delete, graceful shutdown can take up to 60 minutes to complete, we
# are setting timeout to `70` minutes to give some space for delete operation
# to complete gracefully
_TIMEOUT_IN_SEC = 60 * 70

AUTO_DELETE_OVERRIDE_CHOICES = {
    'boot': 'The first partition is reserved for the root filesystem.',
    'data': 'A non-boot disk.',
    'all': 'All disk types.',
}

DETAILED_HELP = {
    'EXAMPLES': """
    To delete an instance called 'instance-1' in the zone 'us-central-2-a', run:

      $ {command} instance-1 --zone=us-central2-a

  """
}


class Delete(base.DeleteCommand):
  """Delete Compute Engine virtual machine instances.

  *{command}* deletes one or more Compute Engine virtual machine
  instances.
  """

  @classmethod
  def Args(cls, parser):
    auto_delete_override = parser.add_mutually_exclusive_group()

    auto_delete_override.add_argument(
        '--delete-disks',
        choices=AUTO_DELETE_OVERRIDE_CHOICES,
        metavar='DISK_TYPE',
        help="""\
        The types of disks to delete with instance deletion regardless
        of the disks' auto-delete configuration. When this flag is
        provided, the auto-delete bits on the attached disks are
        modified accordingly before the instance deletion requests are
        issued. For more information on disk auto-deletion, see
        [Set the auto-delete state of a zonal persistent disk](https://cloud.google.com/compute/docs/disks/modify-persistent-disk#updateautodelete)
        """)

    auto_delete_override.add_argument(
        '--keep-disks',
        choices=AUTO_DELETE_OVERRIDE_CHOICES,
        metavar='DISK_TYPE',
        help="""\
        The types of disks to not delete with instance deletion regardless
        of the disks' auto-delete configuration. When this flag is
        provided, the auto-delete bits on the attached disks are
        modified accordingly before the instance deletion requests are
        issued. For more information on disk auto-deletion, see
        [Set the auto-delete state of a zonal persistent disk](https://cloud.google.com/compute/docs/disks/modify-persistent-disk#updateautodelete)
        """)

    flags.INSTANCES_ARG.AddArgument(parser, operation_type='delete')

    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      parser.add_argument(
          '--no-graceful-shutdown',
          action='store_true',
          default=None,
          help='If specified, skips graceful shutdown.',
      )

    parser.display_info.AddCacheUpdater(completers.InstancesCompleter)

  def GetInstances(self, refs, client):
    """Fetches instance objects corresponding to the given references."""
    instance_get_requests = []
    for ref in refs:
      request_protobuf = client.messages.ComputeInstancesGetRequest(
          **ref.AsDict())
      instance_get_requests.append((client.apitools_client.instances, 'Get',
                                    request_protobuf))

    errors = []
    instances = client.MakeRequests(
        requests=instance_get_requests,
        errors_to_collect=errors)
    if errors:
      utils.RaiseToolException(
          errors,
          error_message='Failed to fetch some instances:')
    return instances

  def PromptIfDisksWithoutAutoDeleteWillBeDeleted(self, disks_to_warn_for):
    """Prompts if disks with False autoDelete will be deleted.

    Args:
      disks_to_warn_for: list of references to disk resources.
    """
    if not disks_to_warn_for:
      return

    prompt_list = []
    for ref in disks_to_warn_for:
      prompt_list.append('[{0}] in [{1}]'.format(ref.Name(), ref.zone))

    prompt_message = utils.ConstructList(
        'The following disks are not configured to be automatically deleted '
        'with instance deletion, but they will be deleted as a result of '
        'this operation if they are not attached to any other instances:',
        prompt_list)
    if not console_io.PromptContinue(message=prompt_message):
      raise compute_exceptions.AbortedError('Deletion aborted by user.')

  def AutoDeleteMustBeChanged(self, args, disk_resource):
    """Returns True if the autoDelete property of the disk must be changed."""
    if args.keep_disks == 'boot':
      return disk_resource.autoDelete and disk_resource.boot
    elif args.keep_disks == 'data':
      return disk_resource.autoDelete and not disk_resource.boot
    elif args.keep_disks == 'all':
      return disk_resource.autoDelete

    elif args.delete_disks == 'data':
      return not disk_resource.autoDelete and not disk_resource.boot
    elif args.delete_disks == 'all':
      return not disk_resource.autoDelete
    elif args.delete_disks == 'boot':
      return not disk_resource.autoDelete and disk_resource.boot

    return False

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    refs = flags.INSTANCES_ARG.ResolveAsResource(
        args, holder.resources,
        scope_lister=flags.GetInstanceZoneScopeLister(client))
    msg = _INSTANCE_DELETE_PROMPT
    if args.keep_disks != 'all':
      msg += ' ' + _INSTANCE_DELETE_PROMPT_DISK_ADDENDUM
    utils.PromptForDeletion(refs, scope_name='zone', prompt_title=msg)

    if args.delete_disks or args.keep_disks:
      instance_resources = self.GetInstances(refs, client)

      disks_to_warn_for = []
      set_auto_delete_requests = []

      for ref, resource in zip(refs, instance_resources):
        for disk in resource.disks:
          # Determines whether the current disk needs to have its
          # autoDelete parameter changed.
          if not self.AutoDeleteMustBeChanged(args, disk):
            continue

          # At this point, we know that the autoDelete property of the
          # disk must be changed. Since autoDelete is a boolean, we
          # just negate it!
          # Yay, computer science! :) :) :)
          new_auto_delete = not disk.autoDelete
          if new_auto_delete:
            disks_to_warn_for.append(holder.resources.Parse(
                disk.source, collection='compute.disks',
                params={'zone': ref.zone}))

          set_auto_delete_requests.append((
              client.apitools_client.instances,
              'SetDiskAutoDelete',
              client.messages.ComputeInstancesSetDiskAutoDeleteRequest(
                  autoDelete=new_auto_delete,
                  deviceName=disk.deviceName,
                  instance=ref.Name(),
                  project=ref.project,
                  zone=ref.zone)))

      if set_auto_delete_requests:
        self.PromptIfDisksWithoutAutoDeleteWillBeDeleted(disks_to_warn_for)
        errors = []
        client.MakeRequests(
            requests=set_auto_delete_requests,
            errors_to_collect=errors,
            timeout=_TIMEOUT_IN_SEC,
        )
        if errors:
          utils.RaiseToolException(
              errors,
              error_message=('Some requests to change disk auto-delete '
                             'behavior failed:'))

    delete_requests = []
    for ref in refs:
      if self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
        request_protobuf = client.messages.ComputeInstancesDeleteRequest(
            **ref.AsDict(), noGracefulShutdown=args.no_graceful_shutdown
        )
      else:
        request_protobuf = client.messages.ComputeInstancesDeleteRequest(
            **ref.AsDict()
        )
      delete_requests.append((client.apitools_client.instances, 'Delete',
                              request_protobuf))

    return client.MakeRequests(delete_requests, timeout=_TIMEOUT_IN_SEC)

Delete.detailed_help = DETAILED_HELP
