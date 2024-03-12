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

"""The meta cache completers list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core.console import progress_tracker


class List(base.ListCommand):
  """List all Cloud SDK command argument completer objects.

  Cloud SDK command argument completers are objects that have a module path,
  collection name and API version.  The module path may be used as the
  _MODULE_PATH_ argument to the $ gcloud meta cache completers run command.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat("""\
       table[box](module_path,
                  type,
                  collection,
                  api_version,
                  attachments:format="table[box](
                     command:sort=1,
                     arguments.list())")
    """)

  def Run(self, args):
    if not args.IsSpecified('sort_by'):
      args.sort_by = ['module_path', 'collection', 'api_version']
    with progress_tracker.ProgressTracker(
        'Collecting attached completers from all command flags and arguments'):
      return cache_util.ListAttachedCompleters(self._cli_power_users_only)
