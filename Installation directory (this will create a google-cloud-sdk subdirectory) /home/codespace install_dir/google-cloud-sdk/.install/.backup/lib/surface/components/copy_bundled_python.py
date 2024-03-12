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

"""`gcloud components copy-bundled-python` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.components import util
from googlecloudsdk.core.updater import update_manager


@base.Hidden
class CopyBundledPython(base.Command):
  """Make a temporary copy of bundled Python installation.

  Also print its location.

  If the Python installation used to execute this command is *not* bundled, do
  not make a copy. Instead, print the location of the current Python
  installation.
  """

  @staticmethod
  def Args(parser):
    parser.display_info.AddFormat('value(python_location)')

  def Run(self, args):
    manager = util.GetUpdateManager(args)
    if manager.IsPythonBundled():
      python_location = update_manager.CopyPython()
    else:
      python_location = sys.executable
    # There's no straightforward way to print a string that was returned from
    # Run() using the formatting, so we wrap it in a dict.
    return {'python_location': python_location}
