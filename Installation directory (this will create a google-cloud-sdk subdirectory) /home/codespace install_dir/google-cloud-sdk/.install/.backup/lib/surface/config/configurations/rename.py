# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""Command to rename named configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.config import completers
from googlecloudsdk.core import log
from googlecloudsdk.core.configurations import named_configs


class Rename(base.SilentCommand):
  """Renames a named configuration."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}

          See `gcloud topic configurations` for an overview of named
          configurations.
          """,
      'EXAMPLES': """\
          To rename an existing configuration named `my-config`, run:

            $ {command} my-config --new-name=new-config
          """,
  }

  @staticmethod
  def Args(parser):
    """Adds args for this command."""
    parser.add_argument(
        'configuration_name',
        completer=completers.NamedConfigCompleter,
        help='Name of the configuration to rename')
    parser.add_argument(
        '--new-name',
        required=True,
        help='Specifies the new name of the configuration.')

  def Run(self, args):

    named_configs.ConfigurationStore.RenameConfig(args.configuration_name,
                                                  args.new_name)

    log.status.Print('Renamed [{0}] to be [{1}].'.format(
        args.configuration_name, args.new_name))

    return args.new_name
