# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for describing Stacks types."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from frozendict import frozendict
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run.integrations import flags
from googlecloudsdk.command_lib.run.integrations import run_apps_operations
from googlecloudsdk.command_lib.run.integrations import types_describe_printer
from googlecloudsdk.core.resource import resource_printer


class Params:
  """Simple struct like class that only holds data."""

  def __init__(self, required, optional):
    self.required = required
    self.optional = optional


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describes a Stacks type."""

  detailed_help = {
      'DESCRIPTION': """\
          {description}
          """,
      'EXAMPLES': """\
          To describe a Stacks type

              $ {command} [TYPE]

         """,
  }

  @classmethod
  def Args(cls, parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    flags.AddPositionalTypeArg(parser)
    resource_printer.RegisterFormatter(
        types_describe_printer.PRINTER_FORMAT,
        types_describe_printer.TypesDescribePrinter,
        hidden=True)
    parser.display_info.AddFormat(
        types_describe_printer.PRINTER_FORMAT)

  def Run(self, args):
    """Describe a Stacks type."""
    release_track = self.ReleaseTrack()
    type_name = args.type
    with run_apps_operations.Connect(args, release_track) as client:
      type_def = client.GetIntegrationTypeDefinition(type_name, True)
      if not type_def:
        raise exceptions.ArgumentError(
            'Cannot find type [{}]'.format(type_name)
        )

      return {
          'description':
              type_def.description,
          'example_command':
              type_def.example_yaml,
          'parameters':
              self._GetParams(type_def),
      }

  def _GetParams(self, type_def):
    required_params = []
    optional_params = []
    # Per the PRD, required parameters should come first.
    for param in type_def.parameters:
      hidden = param.hidden
      required = param.required
      if hidden:
        continue
      if required:
        required_params.append(
            frozendict({
                'name': param.config_name,
                'description': param.description
            }))
      else:
        optional_params.append(
            frozendict({
                'name': param.config_name,
                'description': param.description
            }))

    # sorting the parameters based on name to guarantee the same ordering
    # for scenario tests.
    required_params = sorted(required_params, key=lambda x: x['name'])
    optional_params = sorted(optional_params, key=lambda x: x['name'])
    return Params(required=required_params, optional=optional_params)
