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

"""The meta cache list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core import log
from googlecloudsdk.core.cache import exceptions as cache_exceptions


class List(base.ListCommand):
  """List the tables or table contents in a persistent cache."""

  @staticmethod
  def Args(parser):
    cache_util.AddCacheFlag(parser)
    parser.add_argument(
        'tables',
        nargs='*',
        help=('The table names or name patterns to list, where `?` matches any '
              'character and ```*``` matches any string of zero or more '
              'characters. If omitted then a table of all tables is '
              'displayed.'))

  def Run(self, args):
    with cache_util.GetCache(args.cache) as cache:
      log.info('cache name {}'.format(cache.name))

      if args.tables:
        names = [name for pattern in args.tables
                 for name in cache.Select(pattern)]
        if not names:
          raise cache_util.NoTablesMatched('No tables matched [{}].'.format(
              ','.join(args.tables)))
        if not args.IsSpecified('format'):
          args.format = 'json'
        results = []
        for name in names:
          try:
            table = cache.Table(name, create=False)
            results.append({
                'name': table.name,
                'data': table.Select(ignore_expiration=False)
            })
          except cache_exceptions.Error as e:
            log.warning(e)
        return results

      if not args.IsSpecified('format'):
        args.format = ('table[box](name, columns:label=COL, keys:label=KEY, '
                       'timeout, is_expired:label=EXPIRED)')
      names = cache.Select()
      return [cache.Table(name=name, create=False) for name in sorted(names)]
