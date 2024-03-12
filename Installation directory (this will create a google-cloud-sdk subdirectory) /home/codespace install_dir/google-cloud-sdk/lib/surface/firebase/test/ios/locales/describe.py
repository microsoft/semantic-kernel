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
"""The 'gcloud firebase test ios locales describe' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.api_lib.firebase.test import util
from googlecloudsdk.calliope import base


class Describe(base.DescribeCommand):
  """Describe an iOS locale."""

  detailed_help = {
      'DESCRIPTION': 'Describe an iOS locale.',
      'EXAMPLES': """
To describe an iOS locale, run:

  {command} es_419

To describe an iOS locale in JSON format, run:

  {command} es_419 --format=json
"""
  }

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
    """Run the 'gcloud firebase test ios locales describe' command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation (i.e. group and command arguments combined).

    Returns:
      The testing_v1_messages.Locale object to describe.
    """
    catalog = util.GetIosCatalog(self.context)
    for locale in catalog.runtimeConfiguration.locales:
      if locale.id == args.locale:
        return locale
    raise exceptions.LocaleNotFoundError(args.locale)
