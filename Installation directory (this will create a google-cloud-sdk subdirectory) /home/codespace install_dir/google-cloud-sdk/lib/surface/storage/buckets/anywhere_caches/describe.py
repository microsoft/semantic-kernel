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
"""Implementation of describe command to get the Anywhere Cache Instance."""

import collections

from googlecloudsdk.api_lib.storage import api_factory
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import flags
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.storage.resources import resource_util

# Determines the order in which the fields should be displayed for
# an AnywhereCacheResource.
AnywhereCacheDisplayTitlesAndDefaults = collections.namedtuple(
    'AnywhereCacheDisplayTitlesAndDefaults',
    (
        'admission_policy',
        'anywhere_cache_id',
        'bucket',
        'create_time',
        'id',
        'kind',
        'pending_update',
        'state',
        'ttl',
        'update_time',
        'zone',
    ),
)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Returns details of Anywhere Cache instance of a bucket."""

  detailed_help = {
      'DESCRIPTION': """

      Desribes a single Anywhere Cache instance if it exists.
      """,
      'EXAMPLES': """

      The following command describes the anywhere cache instance of bucket
      ``my-bucket'' having anywhere_cache_id ``my-cache-id'':

        $ {command} my-bucket/my-cache-id
      """,
  }

  @classmethod
  def Args(cls, parser):
    parser.add_argument(
        'id',
        type=str,
        help=(
            'Identifier for a Anywhere Cache instance. It is a combination of'
            ' bucket_name/anywhere_cache_id, For example :'
            ' test-bucket/my-cache-id.'
        ),
    )

    flags.add_raw_display_flag(parser)

  def Run(self, args):
    bucket_name, _, anywhere_cache_id = args.id.rpartition('/')

    result = api_factory.get_api(
        storage_url.ProviderPrefix.GCS
    ).get_anywhere_cache(bucket_name, anywhere_cache_id)

    return resource_util.get_display_dict_for_resource(
        result,
        AnywhereCacheDisplayTitlesAndDefaults,
        args.raw,
    )
