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

"""A command that validates YAML data against a JSON Schema."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import yaml
from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.console import console_io


class ValidateYAML(base.Command):
  """Validate a YAML file against a JSON Schema.

  {command} validates YAML / JSON files against
  [JSON Schemas](https://json-schema.org/).
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'schema_file',
        help='The path to a file containing the JSON Schema.')
    parser.add_argument(
        'yaml_file',
        help=('The path to a file containing YAML / JSON data. Use `-` for '
              'the standard input.'))

  def Run(self, args):
    contents = console_io.ReadFromFileOrStdin(args.yaml_file, binary=False)
    parsed_yaml = yaml.load(contents)
    yaml_validator.Validator(args.schema_file).Validate(parsed_yaml)
