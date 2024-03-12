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
"""Bare Metal Solution instance update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a Bare Metal Solution instance.

          This call returns immediately, but the update operation may take
          several minutes to complete. To check if the operation is complete,
          use the `describe` command for the instance.
        """,
    'EXAMPLES':
        """
          To update an instance called ``my-instance'' in region ``us-central1'' with
          a new label ``key1=value1'', run:

          $ {command} my-instance  --region=us-central1 --update-labels=key1=value1

          To clear all labels, run:

          $ {command} my-instance --region=us-central1 --clear-labels
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Bare Metal Solution instance."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddInstanceArgToParser(parser, positional=True)
    labels_util.AddUpdateLabelsFlags(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddInstanceOsImageToParser(parser, hidden=False)
    flags.AddInstanceEnableHyperthreadingToParser(parser, hidden=False)

  def GetRequestFields(self, args, client, instance):
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_resource = client.GetInstance(instance)
    labels_update = labels_diff.Apply(client.messages.Instance.LabelsValue,
                                      orig_resource.labels).GetOrNone()
    os_image = getattr(args, 'os_image', None)
    enable_hyperthreading = getattr(args, 'enable_hyperthreading', None)
    return {
        'instance_resource': instance,
        'labels': labels_update,
        'os_image': os_image,
        'enable_hyperthreading': enable_hyperthreading,
        'ssh_keys': [],
        'kms_key_version': None,
        'clear_ssh_keys': False,
    }

  def Run(self, args):
    client = BmsClient()
    instance = args.CONCEPTS.instance.Parse()
    op_ref = client.UpdateInstance(
        **self.GetRequestFields(args, client, instance))
    if op_ref.done:
      log.UpdatedResource(instance.Name(), kind='instance')
      return op_ref
    if args.async_:
      log.status.Print(
          f'Update request issued for: [{instance.Name()}]\n'
          f'Check operation [{op_ref.name}] for status.')
      return op_ref

    op_resource = resources.REGISTRY.ParseRelativeName(
        op_ref.name,
        collection='baremetalsolution.projects.locations.operations',
        api_version='v2')
    poller = waiter.CloudOperationPollerNoResources(
        client.operation_service)
    res = waiter.WaitFor(
        poller, op_resource,
        'Waiting for operation [{}] to complete'.format(op_ref.name))
    log.UpdatedResource(instance.Name(), kind='instance')
    return res


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a Bare Metal Solution instance."""

  @staticmethod
  def Args(parser):
    flags.AddProvisioningSshKeyArgToParser(parser, required=False, plural=True)
    flags.AddKMSCryptoKeyVersionToParser(parser, hidden=False)
    # Flags which are only available in ALPHA should be added to parser here.
    Update.Args(parser)

  def GetRequestFields(self, args, client, instance):
    return {
        **super().GetRequestFields(args, client, instance),
        'kms_key_version': args.kms_crypto_key_version,
        'ssh_keys': args.CONCEPTS.ssh_keys.Parse(),
        'clear_ssh_keys': getattr(args, 'clear_ssh_keys', False),
    }

Update.detailed_help = DETAILED_HELP
