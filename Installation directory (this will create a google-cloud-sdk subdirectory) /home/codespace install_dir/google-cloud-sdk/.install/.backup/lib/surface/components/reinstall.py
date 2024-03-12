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

"""The command to install/update gcloud components."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.components import util


class Reinstall(base.SilentCommand):
  """Reinstall the Google Cloud CLI with the same components you have now.

  If your Google Cloud CLI installation becomes corrupt, this command attempts
  to fix it by downloading the latest version of the Google Cloud CLI and
  reinstalling it. This will replace your existing installation with a fresh
  one.  The command is the equivalent of deleting your current installation,
  downloading a fresh copy of the gcloud CLI, and installing in the same
  location.

  ## EXAMPLES
  To reinstall all components you have installed, run:

    $ {command}
  """

  @staticmethod
  def Args(parser):
    pass

  def Run(self, args):
    """Runs the list command."""
    update_manager = util.GetUpdateManager(args)
    update_manager.Reinstall()
