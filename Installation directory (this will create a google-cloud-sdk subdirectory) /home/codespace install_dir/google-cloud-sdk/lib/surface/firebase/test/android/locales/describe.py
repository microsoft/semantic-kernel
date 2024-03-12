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

"""The 'gcloud firebase test android locales describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.calliope import base


DETAILED_HELP = {
    'EXAMPLES': """
    To see the attributes of the Android locale 'my-locale', run:

      $ {command} my-locale
    """,
}


class Describe(base.DescribeCommand):
  """Describe an Android locale."""

  @staticmethod
  def Args(parser):
    """Method called by Calliope to register flags for this command.

    Args:
      parser: An argparse parser used to add arguments that follow this
          command in the CLI. Positional arguments are allowed.
    """
    # Positional arg
    parser.add_argument(
        'locale',
        help='The locale to describe, found using $ {parent_command} list.')

  def Run(self, args):
    """Run the 'gcloud firebase test android locales describe' command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      The testing_v1_messages.Locale object to describe.
    """
    catalog = util.GetAndroidCatalog(self.context)
    for locale in catalog.runtimeConfiguration.locales:
      if locale.id == args.locale:
        return locale
    raise exceptions.LocaleNotFoundError(args.locale)


Describe.detailed_help = DETAILED_HELP
