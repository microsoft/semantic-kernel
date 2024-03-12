# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Flags and helpers for the container builds command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.util import completers


class BuildsCompleter(completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(BuildsCompleter, self).__init__(
        collection='cloudbuild.projects.builds',
        list_command='container builds list --uri',
        **kwargs)


def AddBuildArg(parser, intro=None):
  """Adds a 'build' arg to the given parser.

  Args:
    parser: The argparse parser to add the arg to.
    intro: Introductory sentence.
  """
  if intro:
    help_text = intro + ' '
  else:
    help_text = ''
  help_text += ('The ID of the build is printed at the end of the build '
                'submission process, or in the ID column when listing builds.')
  parser.add_argument(
      'build',
      completer=BuildsCompleter,
      help=help_text)
