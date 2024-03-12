# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

"""A command that generates and/or updates help document directoriess."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
import googlecloudsdk.command_lib.meta.generate_command as generate_command


class GenerateCommand(base.Command):
  """Generate YAML file to implement given command.

  The command YAML file is generated in the --output-dir directory.
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'collection',
        metavar='COLLECTION',
        help=('The name of the collection to generate commands for.'))
    parser.add_argument(
        '--output-dir',
        metavar='DIRECTORY',
        help=('The directory where the generated command YAML files '
              'will be written. If not specified then yaml files will '
              'not be generated. If no output directory is specified, '
              'the new YAML file will be written to stdout.'))

  def Run(self, args):
    return generate_command.WriteAllYaml(args.collection, args.output_dir)
