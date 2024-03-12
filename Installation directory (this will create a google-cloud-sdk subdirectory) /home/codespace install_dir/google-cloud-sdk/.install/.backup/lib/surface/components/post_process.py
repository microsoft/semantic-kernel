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

"""The command to perform any necessary post installation steps."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core.updater import local_state


@base.Hidden
class PostProcess(base.SilentCommand):
  """Performs any necessary post installation steps."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--force-recompile',
        action='store_true',
        required=False,
        hidden=True,
        default='False',
        help='THIS ARGUMENT NEEDS HELP TEXT.')
    parser.add_argument(
        '--compile-python',
        required=False,
        hidden=True,
        default='True',
        action='store_true',
        help='THIS ARGUMENT NEEDS HELP TEXT.')

  def Run(self, args):
    # Re-compile python files.
    if args.compile_python:
      state = local_state.InstallationState.ForCurrent()
      state.CompilePythonFiles(force=args.force_recompile)
