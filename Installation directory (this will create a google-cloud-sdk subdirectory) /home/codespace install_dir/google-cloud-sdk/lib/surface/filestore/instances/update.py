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
"""Update a Filestore instance."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.filestore import filestore_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.filestore.instances import flags as instances_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log

import six


def _CommonArgs(parser, api_version=filestore_client.V1_API_VERSION):
  instances_flags.AddInstanceUpdateArgs(parser, api_version)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Update(base.CreateCommand):
  """Update a Filestore instance."""

  _API_VERSION = filestore_client.V1_API_VERSION

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, Update._API_VERSION)

  def Run(self, args):
    """Run command line arguments.

    Args:
      args: cmd line arguments.

    Raises:
       InvalidArgumentException: for invalid jason formatted --file-args.
       KeyError: for key errors in Jason values.
    Returns:
       client: client instance.
    """

    instance_ref = args.CONCEPTS.instance.Parse()
    client = filestore_client.FilestoreClient(self._API_VERSION)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_instance = client.GetInstance(instance_ref)

    try:
      if args.file_share:
        client.MakeNFSExportOptionsMsg(
            messages=client.messages,
            nfs_export_options=args.file_share.get('nfs-export-options', []),
        )
    except KeyError as err:
      raise exceptions.InvalidArgumentException(
          '--file-share', six.text_type(err)
      )
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.Instance.LabelsValue, orig_instance.labels
      ).GetOrNone()
    else:
      labels = None
    try:
      instance = client.ParseUpdatedInstanceConfig(
          orig_instance,
          description=args.description,
          labels=labels,
          file_share=args.file_share,
          clear_nfs_export_options=args.clear_nfs_export_options)
    except filestore_client.Error as e:
      raise exceptions.InvalidArgumentException('--file-share',
                                                six.text_type(e))

    updated_fields = []
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (args.IsSpecified('update_labels') or
        args.IsSpecified('remove_labels') or args.IsSpecified('clear_labels')):
      updated_fields.append('labels')
    if args.IsSpecified('file_share'):
      updated_fields.append('fileShares')
    update_mask = ','.join(updated_fields)

    result = client.UpdateInstance(instance_ref, instance, update_mask,
                                   args.async_)
    if args.async_:
      log.status.Print(
          'To check the status of the operation, run `gcloud {} filestore '
          'operations describe {}`'.format(self._API_VERSION, result.name))
    return result


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(Update):
  """Update a Filestore instance."""

  _API_VERSION = filestore_client.ALPHA_API_VERSION

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, UpdateAlpha._API_VERSION)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(Update):
  """Update a Filestore instance."""

  _API_VERSION = filestore_client.BETA_API_VERSION

  @staticmethod
  def Args(parser):
    _CommonArgs(parser, UpdateBeta._API_VERSION)

  def Run(self, args):
    """Runs a command line string arguments.

    Args:
      args: cmd line string arguments.

    Returns:
       client: A FilestoreClient instance.

    Raises:
       InvalidArgumentException: for invalid JSON formatted --file-args.
       KeyError: for key errors in JSON values.
    """

    instance_ref = args.CONCEPTS.instance.Parse()
    client = filestore_client.FilestoreClient(self._API_VERSION)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    orig_instance = client.GetInstance(instance_ref)

    try:
      if args.file_share:
        client.MakeNFSExportOptionsMsgBeta(
            messages=client.messages,
            nfs_export_options=args.file_share.get('nfs-export-options', []),
        )
    except KeyError as e:
      raise exceptions.InvalidArgumentException(
          '--file-share', six.text_type(e)
      )
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.Instance.LabelsValue, orig_instance.labels
      ).GetOrNone()
    else:
      labels = None

    try:
      instance = client.ParseUpdatedInstanceConfig(
          orig_instance,
          description=args.description,
          labels=labels,
          file_share=args.file_share,
          managed_ad=args.managed_ad,
          disconnect_managed_ad=args.disconnect_managed_ad,
          clear_nfs_export_options=args.clear_nfs_export_options)
    except filestore_client.Error as e:
      raise exceptions.InvalidArgumentException('--file-share',
                                                six.text_type(e))

    updated_fields = []
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (args.IsSpecified('update_labels') or
        args.IsSpecified('remove_labels') or args.IsSpecified('clear_labels')):
      updated_fields.append('labels')
    if args.IsSpecified('file_share'):
      updated_fields.append('fileShares')
    if args.IsSpecified('managed_ad') or args.IsSpecified(
        'disconnect_managed_ad'
    ):
      updated_fields.append('directoryServices')
    update_mask = ','.join(updated_fields)

    result = client.UpdateInstance(instance_ref, instance, update_mask,
                                   args.async_)
    if args.async_:
      log.status.Print(
          'To check the status of the operation, run `gcloud {} filestore '
          'operations describe {}`'.format(self._API_VERSION, result.name))
    return result


Update.detailed_help = {
    'DESCRIPTION':
        'Update a Filestore instance.',
    'EXAMPLES':
        """\
The following command updates the Filestore instance NAME to change the
description to "A new description."

  $ {command} NAME --description="A new description."

The following command updates a Filestore instance named NAME to add the label
"key1=value1" and remove any metadata with the label "key2".

  $ {command} NAME --update-labels=key1=value1 --remove-labels=key2

  $ {command} NAME --zone=ZONE --flags-file=FILE_PATH

Example json configuration file:
  {
  "--file-share":
  {
    "capacity": "102400",
    "name": "my_vol",
    "nfs-export-options": [
      {
        "access-mode": "READ_WRITE",
        "ip-ranges": [
          "10.0.0.0/29",
          "10.2.0.0/29"
        ],
        "squash-mode": "ROOT_SQUASH",
        "anon_uid": 1003,
        "anon_gid": 1003
      },
    ],
  }
  }


The following command updates a Filestore instance named NAME to change the
capacity to CAPACITY.

  $ {command} NAME --project=PROJECT_ID --zone=ZONE\
    --file-share=name=VOLUME_NAME,capacity=CAPACITY
"""}
