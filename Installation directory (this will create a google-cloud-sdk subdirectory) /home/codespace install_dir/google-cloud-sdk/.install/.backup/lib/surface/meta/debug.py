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
"""The `gcloud meta debug` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import debug


class Debug(base.Command):
  """Run an interactive debug console with the Cloud SDK libraries loaded.

  This command runs an interactive console with the Cloud SDK libraries loaded.

  It's useful for:

  * Manually testing out an API.
  * Exploring available Cloud SDK core libraries.
  * Debugging specific problems.

  It comes with many utilities pre-loaded in the environment:

  * All API clients loaded with one command (`LoadApis()`). Then, for instance,
    `appengine` refers to the App Engine API client.
  * Many common Cloud SDK imports pre-imported (e.g. core.util.files,
    console_io, properties).

  Use `dir()` to explore them all.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--mode', choices=sorted(debug.CONSOLES.keys()), default='python',
        help='The debug console mode to run in.')

  def Run(self, args):
    debug.CONSOLES[args.mode]()
