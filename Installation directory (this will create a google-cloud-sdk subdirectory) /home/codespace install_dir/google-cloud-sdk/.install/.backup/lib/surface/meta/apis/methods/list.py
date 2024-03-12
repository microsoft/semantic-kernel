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

import itertools

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta.apis import flags
from googlecloudsdk.command_lib.util.apis import registry


class List(base.ListCommand):
  """List the methods of a resource collection for an API."""

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    collection_flag = base.Argument(
        '--collection',
        completer=flags.CollectionCompleter,
        help='The name of the collection for which to list methods.\n'
             'If left blank, returns methods from all collections.')
    collection_flag.AddToParser(parser)
    flags.API_VERSION_FLAG.AddToParser(parser)
    api_flag = base.Argument(
        '--api',
        completer=flags.APICompleter,
        help=('The name of the API to get the methods for. If `--api-version` '
              'is also supplied, then returns methods from specified version, '
              'otherwise returns methods from all versions of this API.'))
    api_flag.AddToParser(parser)
    parser.display_info.AddFormat("""
      table(
        name:sort=1,
        detailed_path:optional,
        http_method,
        request_type,
        response_type
      )
    """)

  def Run(self, args):
    if not args.collection:
      if args.api:
        collections = [registry.GetAPICollections(args.api, args.api_version)]
      else:
        collections = [
            registry.GetAPICollections(api.name, api.version)
            for api in registry.GetAllAPIs()
        ]
      collections = list(itertools.chain.from_iterable(collections))
      methods = [registry.GetMethods(collection.full_name,
                                     api_version=collection.api_version)
                 for collection in collections]
      methods = list(itertools.chain.from_iterable(methods))
      return methods

    return registry.GetMethods(args.collection, api_version=args.api_version)
