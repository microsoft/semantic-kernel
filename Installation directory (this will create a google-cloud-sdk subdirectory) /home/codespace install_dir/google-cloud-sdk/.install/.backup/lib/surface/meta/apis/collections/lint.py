# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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


class Lint(base.ListCommand):
  """Show which collections have non-compliant list API methods."""

  @staticmethod
  def Args(parser):
    base.PAGE_SIZE_FLAG.RemoveFromParser(parser)
    base.URI_FLAG.RemoveFromParser(parser)
    parser.add_argument(
        '--api',
        completer=flags.APICompleter,
        help='The name of the API to get the collections for.')
    flags.API_VERSION_FLAG.AddToParser(parser)
    parser.display_info.AddFormat("""\
        table(
          collection:sort=6,
          has_list:sort=1,
          resource_arg:sort=2,
          flattened:sort=3,
          pageable:sort=4,
          page_size:sort=5)
    """)

  def Run(self, args):
    if args.api_version and not args.api:
      raise exceptions.RequiredArgumentException(
          '--api',
          'The --api-version flag can only be specified when using the --api '
          'flag.')

    collections = registry.GetAPICollections(api_name=args.api,
                                             api_version=args.api_version)
    results = []
    for c in collections:
      methods = registry.GetMethods(c.full_name, api_version=c.api_version)
      if not methods:
        # Synthetic collection
        continue

      list_methods = [m for m in methods if m.IsList()]
      if list_methods:
        method = list_methods[0]
        results.append({'collection': c.full_name,
                        'has_list': True,
                        'resource_arg': bool(method.request_collection),
                        'flattened': bool(method.ListItemField()),
                        'pageable': method.HasTokenizedRequest(),
                        'page_size': bool(method.BatchPageSizeField())})
      else:
        results.append({'collection': c.full_name, 'has_list': False})

    # Filter out anything that is fully within spec.
    results = [r for r in results if not (r['has_list'] and
                                          r['resource_arg'] and
                                          r['flattened'] and
                                          r['pageable'] and
                                          r['page_size'])]
    return results
