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

"""The 'gcloud firebase test android' sub-group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Android(base.Group):
  """Command group for Android application testing."""

  detailed_help = {
      'DESCRIPTION': """\
          Explore physical and virtual Android models, Android OS versions, and
          Android locales which are available as test targets. Also run tests
          against your Android app on these devices, monitor your test progress,
          and view detailed test results in the Firebase console.
          """,

      'EXAMPLES': """\
          To see a list of available Android devices, their form factors, and
          supported Android OS versions, run:

            $ {command} models list

          To view more detailed information about a specific Android model, run:

            $ {command} models describe MODEL_ID

          To view details about available Android OS versions, such as their
          code names and release dates, run:

            $ {command} versions list

          To view information about a specific Android OS version, run:

            $ {command} versions describe VERSION_ID

          To view the list of available Android locales which can be used for
          testing internationalized applications, run:

            $ {command} locales list

          To view information about a specific locale, run:

            $ {command} locales describe LOCALE

          To view all options available for running Android tests, run:

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
