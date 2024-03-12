# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""A command that generates and/or updates single resource config commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.meta import generate_config_command
from googlecloudsdk.command_lib.util.resource_map.declarative import resource_name_translator


class GenerateCommand(base.Command):
  """Generate declarative config commands with surface specs and tests."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--output-root',
        metavar='DIRECTORY',
        required=True,
        help=('Root of the directory within which to generate config '
              'config export commands.'))
    parser.add_argument(
        '--enable-overwrites',
        action='store_true',
        help=('When enabled, allows overwriting of existing commands, surface '
              'specs, and test files.'))
    parser.add_argument(
        '--collections',
        metavar='COLLECTION',
        type=arg_parsers.ArgList(),
        help=('List of apitools collections to generate commands for.'))
    parser.add_argument(
        '--release-tracks',
        metavar='TRACK',
        type=arg_parsers.ArgList(),
        help='List of release tracks to generate commands for. E.g. `ALPHA,BETA,GA`'
    )

  def Run(self, args):
    translator = resource_name_translator.ResourceNameTranslator()
    release_tracks = getattr(args, 'release_tracks') or ['ALPHA']
    specified_collections = getattr(args, 'collections')

    for collection in translator:
      render_files = False
      resource_data = collection.resource_data
      if ('enable_single_resource_autogen' in resource_data and
          resource_data.enable_single_resource_autogen):
        if specified_collections:
          if collection.collection_name in specified_collections:
            render_files = True
        else:
          render_files = True
      if render_files:
        generate_config_command.WriteConfigYaml(collection.collection_name,
                                                args.output_root,
                                                resource_data,
                                                release_tracks,
                                                args.enable_overwrites)
