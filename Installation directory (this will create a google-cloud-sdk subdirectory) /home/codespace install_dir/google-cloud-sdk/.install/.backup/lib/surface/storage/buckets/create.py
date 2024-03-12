# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Implementation of create command for making buckets."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import errors
from googlecloudsdk.command_lib.storage import errors_util
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage import user_request_args_factory
from googlecloudsdk.command_lib.storage.resources import resource_reference
from googlecloudsdk.command_lib.storage.tasks.buckets import create_bucket_task


class Create(base.Command):
  """Create buckets for storing objects."""

  detailed_help = {
      'DESCRIPTION':
          """
      Create new buckets.
      """,
      'EXAMPLES':
          """

      The following command creates 2 Cloud Storage buckets, one named
      ``my-bucket'' and a second bucket named ``my-other-bucket'':

        $ {command} gs://my-bucket gs://my-other-bucket

      The following command creates a bucket with the ``nearline'' default
      [storage class](https://cloud.google.com/storage/docs/storage-classes) in
      the ``asia'' [location](https://cloud.google.com/storage/docs/locations):

        $ {command} gs://my-bucket --default-storage-class=nearline --location=asia
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'url', type=str, nargs='+', help='The URLs of the buckets to create.')
    parser.add_argument(
        '--location',
        '-l',
        type=str,
        help=('[Location](https://cloud.google.com/storage/docs/locations)'
              ' for the bucket. If not specified, the location used by Cloud'
              ' Storage is ``us\'\'. A bucket\'s location cannot be changed'
              ' after creation.'))
    parser.add_argument(
        '--public-access-prevention',
        '--pap',
        action=arg_parsers.StoreTrueFalseAction,
        help='Sets public access prevention to "enforced".'
        ' For details on how exactly public access is blocked, see:'
        ' http://cloud.google.com/storage/docs/public-access-prevention')
    parser.add_argument(
        '--uniform-bucket-level-access',
        '-b',
        action=arg_parsers.StoreTrueFalseAction,
        help='Turns on uniform bucket-level access setting. Default is False.')
    parser.add_argument(
        '--default-storage-class',
        '-c',
        '-s',
        type=str,
        help=('Default [storage class]'
              '(https://cloud.google.com/storage/docs/storage-classes) for'
              ' the bucket. If not specified, the default storage class'
              ' used by Cloud Storage is "Standard".'))
    parser.add_argument(
        '--default-encryption-key',
        '-k',
        type=str,
        help=(
            'Set the default KMS key using the full path to the key, which '
            'has the following form: '
            '``projects/[project-id]/locations/[location]/keyRings/[key-ring]/cryptoKeys/[my-key]\'\'.'
        ))
    parser.add_argument(
        '--retention-period',
        help='Minimum [retention period](https://cloud.google.com'
        '/storage/docs/bucket-lock#retention-periods)'
        ' for objects stored in the bucket, for example'
        ' ``--retention-period=1Y1M1D5S\'\'. Objects added to the bucket'
        ' cannot be deleted until they\'ve been stored for the specified'
        ' length of time. Default is no retention period. Only available'
        ' for Cloud Storage using the JSON API.')
    parser.add_argument(
        '--placement',
        metavar='REGION',
        type=arg_parsers.ArgList(min_length=2,
                                 max_length=2,
                                 custom_delim_char=','),
        help=('A comma-separated list of exactly 2 regions that form the custom'
              ' dual-region. Only regions within the same continent are or will'
              ' ever be valid. Invalid location pairs (such as mixed-continent,'
              ' or with unsupported regions) will return an error.'))
    parser.add_argument(
        '--soft-delete-duration',
        type=arg_parsers.Duration(),
        help=(
            'Duration to retain soft-deleted objects. For example, "2w1d" is'
            ' two weeks and one day. The presence of this flag creates a'
            ' bucket with a soft delete policy enabled, meaning deleted'
            ' objects can be restored if requested within the inputted'
            ' duration. See `gcloud topic datetimes` for more information on'
            ' the duration format.'
        ),
    )
    flags.add_additional_headers_flag(parser)
    flags.add_autoclass_flags(parser)
    flags.add_enable_per_object_retention_flag(parser)
    flags.add_recovery_point_objective_flag(parser)

    if cls.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      parser.add_argument(
          '--enable-hierarchical-namespace',
          action='store_true',
          help='Enable heirarchical namepsace for the bucket',
      )

  def Run(self, args):
    for url_string in args.url:
      url = storage_url.storage_url_from_string(url_string)
      errors_util.raise_error_if_not_bucket(args.command_path, url)
      resource = resource_reference.UnknownResource(url)
      user_request_args = (
          user_request_args_factory.get_user_request_args_from_command_args(
              args, metadata_type=user_request_args_factory.MetadataType.BUCKET)
          )
      if (
          user_request_args.resource_args.autoclass_terminal_storage_class
          is not None
          and not user_request_args.resource_args.enable_autoclass
      ):
        raise errors.Error(
            '--autoclass_terminal_storage_class is only allowed if'
            ' --enable-autoclass is set.'
        )
      create_bucket_task.CreateBucketTask(
          resource,
          user_request_args=user_request_args).execute()
