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

"""Command to describe named configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.configurations import properties_file


class Describe(base.DescribeCommand):
  """Describes a named configuration by listing its properties."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          See `gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To describe an existing configuration named `my-config`, run:

            $ {command} my-config

          This is similar to:

            $ gcloud config configurations activate my-config

            $ gcloud config list
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'configuration_name',
        completer=completers.NamedConfigCompleter,
        help='Name of the configuration to describe')
    parser.add_argument(
        '--all', action='store_true',
        help='Include unset properties in output.')

  def Run(self, args):
    all_configs = named_configs.ConfigurationStore.AllConfigs(
        include_none_config=True)
    config = all_configs.get(args.configuration_name, None)
    if not config:
      raise named_configs.NamedConfigError(
          'The configuration [{0}] does not exist.'
          .format(args.configuration_name))

    return {
        'name': config.name,
        'is_active': config.is_active,
        'properties': properties.VALUES.AllValues(
            list_unset=args.all,
            properties_file=properties_file.PropertiesFile([config.file_path]),
            only_file_contents=True),
    }
