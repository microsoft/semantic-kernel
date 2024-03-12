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

"""The meta cache delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.Command):
  """Delete a persistent cache or tables in the cache."""

  @staticmethod
  def Args(parser):
    cache_util.AddCacheFlag(parser)
    parser.add_argument(
        'tables',
        nargs='*',
        help=('The table names or name patterns to delete, where `?` matches '
              'any character and ```*``` matches any string of zero or more '
              'characters. If omitted then the entired cache is deleted.'))

  def Run(self, args):

    def _RequireConfirmation(name):
      """Prompt for cache deletion and return confirmation."""
      console_io.PromptContinue(
          message='The entire [{}] cache will be deleted.'.format(name),
          cancel_on_no=True,
          default=True)

    if not args.tables and not args.IsSpecified('cache'):
      _RequireConfirmation(args.cache)
      cache_util.Delete()
      return None

    with cache_util.GetCache(args.cache) as cache:
      log.info('cache name {}'.format(cache.name))
      if args.tables:
        names = [name for pattern in args.tables
                 for name in cache.Select(pattern)]
        if not names:
          raise cache_util.NoTablesMatched('No tables matched [{}].'.format(
              ','.join(args.tables)))
        console_io.PromptContinue(
            message='[{}] will be deleted.'.format(','.join(names)),
            default=True,
            cancel_on_no=True)
        for name in names:
          table = cache.Table(name)
          table.Delete()
        return None

      _RequireConfirmation(cache.name)
      cache.Delete()

    return None
