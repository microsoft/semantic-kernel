# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Command to list Cloud Storage objects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import expansion

from six.moves import queue


@base.Hidden
@base.Deprecate(is_removed=False, warning='This command is deprecated. '
                'Use `gcloud alpha storage ls` instead.')
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List the objects in Cloud Storage buckets."""

  detailed_help = {
      'DESCRIPTION': """\
      *{command}* lets you list the objects in your Cloud Storage buckets.
      Forward slashes in object names are logically treated as directories for
      the purposes of listing contents. See below for example of how to use
      wildcards to get the listing behavior you want.
      """,
      'EXAMPLES': """\
      To list the contents of a bucket:

          $ {command} gs://my-bucket

      This will list the direct contents of the bucket. To recursively list the
      contents of all directories in the bucket:

          $ {command} gs://my-bucket --recursive

      You can use wildcards to match multiple paths (including multiple
      buckets). Bucket wildcards are expanded only to the buckets contained in
      your current project:

          $ {command} gs://my-b*/log*.txt

      The following wildcards are valid and match only within the current
      directory:

          *: Matches zero or more characters
          ?: Matches zero or one characters
          []: Matches a character range (ex. [a-z] or [0-9])

      You can use double-star wildcards to match zero or more directory levels
      in a path:

          $ {command} gs://my-bucket/**/log*.txt

      You can also use double-star to match all files after a root in a path:

          $ {command} gs://my-bucket/**

      Double-star expansion can not be combined with other expressions in a
      given path segment and will operate as a single star in that context. For
      example:

          gs://my-bucket/dir**/log.txt      is treated as:

          gs://my-bucket/dir*/log.txt       and instead should be written as:

          gs://my-bucket/dir*/**/log.txt    to get the recursive behavior.
      """,
  }

  OBJECT_FORMAT_STRING = """\
      table(
          path:label=PATH,
          data.size.size(zero=""):label=SIZE,
          data.timeCreated.date():label=CREATED,
          data.updated.date():label=UPDATED
      )"""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'path',
        nargs='*',
        help='The path of objects and directories to list. The path must begin '
             'with gs:// and may or may not contain wildcard characters.')
    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively list the contents of any directories that match the '
             'path expression.')
    parser.add_argument(
        '--flatten-results',
        action='store_true',
        help='Show all matching objects in one list as opposed to grouping by '
             'directory.')
    parser.display_info.AddFormat("""\
        table[no-heading](
            format('{0}:', dir),
            objects:format='%s'
        )""" % List.OBJECT_FORMAT_STRING)

  def Run(self, args):
    paths = args.path or ['gs://']
    expander = expansion.GCSPathExpander()
    objects, dirs = expander.ExpandPaths(paths)

    if args.IsSpecified('flatten_results'):
      # Respect the user's choice if given explicitly.
      flatten = args.flatten_results
    else:
      # Get a default for this mode if not specifically provided.
      # Simplest case where we are listing only files or a single directory,
      # don't nest output in tables by directory.
      flatten = bool(not args.recursive and
                     not (objects and dirs) and
                     len(dirs) < 2)

    # First collect all the directly matching objects.
    results = []
    if objects:
      results.append(
          {'dir': '',
           'objects': expander.GetSortedObjectDetails(objects)})

    # For each matching directory, get the objects directly under it.
    dirs_to_process = queue.Queue()
    for d in sorted(dirs):
      dirs_to_process.put(d)
    while not dirs_to_process.empty():
      d = dirs_to_process.get()
      children = [d + o for o in sorted(expander.ListDir(d))]
      details = expander.GetSortedObjectDetails(children)
      results.append({'dir': d, 'objects': details})

      if args.recursive:
        # Recurse on any directories that are found under the current parent.
        for c in children:
          if expander.IsDir(c):
            dirs_to_process.put(c + '/')

    if not flatten:
      return results
    # Flatten results.
    args.GetDisplayInfo().AddFormat(List.OBJECT_FORMAT_STRING)
    return itertools.chain.from_iterable([x['objects'] for x in results])
