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

"""A command that lists the resource collections for a given API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.meta.apis import flags
from googlecloudsdk.command_lib.util.apis import registry


class List(base.ListCommand):
  """List the resource collections for an API."""

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--api',
        completer=flags.APICompleter,
        help='The name of the API to get the collections for.')
    flags.API_VERSION_FLAG.AddToParser(parser)
    parser.display_info.AddFormat("""
      table(
        full_name:sort=1:label=COLLECTION_NAME,
        detailed_path
      )
    """)

  def Run(self, args):
    if args.api_version and not args.api:
      raise exceptions.RequiredArgumentException(
          '--api',
          'The --api-version flag can only be specified when using the --api '
          'flag.')

    return registry.GetAPICollections(api_name=args.api,
                                      api_version=args.api_version)
