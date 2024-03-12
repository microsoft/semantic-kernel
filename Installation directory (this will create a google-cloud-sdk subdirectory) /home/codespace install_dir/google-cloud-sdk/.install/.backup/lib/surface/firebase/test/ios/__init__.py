# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""The 'gcloud firebase test ios' sub-group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import log


class Ios(base.Group):
  """Command group for iOS application testing."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Explore physical iOS devices and iOS versions which are available as
          test targets. Also run tests against your iOS app on these devices,
          monitor your test progress, and view detailed test results in the
          Firebase console.
      """,
      'EXAMPLES':
          """\
          To see a list of available iOS devices and supported iOS versions,
          run:

            $ {command} models list

          To view information about a specific iOS model, run:

            $ {command} models describe MODEL_ID

          To view details about all iOS versions, run:

            $ {command} versions list

          To view information about a specific iOS version, run:

            $ {command} versions describe VERSION_ID

          To view all options available for iOS tests, run:

            $ {command} run --help
      """
  }

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags common to this sub-group.

    Args:
      parser: An argparse parser used to add arguments that immediately follow
          this group in the CLI. Positional arguments are allowed.
    """

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: {str:object}, The current context, which is a set of key-value
          pairs that can be used for common initialization among commands.
      args: argparse.Namespace: The same Namespace given to the corresponding
          .Run() invocation.

    Returns:
      The refined command context.
    """
    return context
