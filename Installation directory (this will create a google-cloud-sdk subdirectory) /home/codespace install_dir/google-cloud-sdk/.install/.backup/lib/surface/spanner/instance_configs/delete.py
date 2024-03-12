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
"""Command for spanner instance configs delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import instance_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a Cloud Spanner instance configuration."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To delete a custom Cloud Spanner instance configuration, run:

          $ {command} custom-instance-config
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Use this flag to validate that the request will succeed before executing it.'
    )

    parser.add_argument(
        '--etag',
        help='Used for optimistic concurrency control as a way to help prevent '
        'simultaneous deletes of an instance config from overwriting each '
        'other.')

    parser.add_argument(
        'config',
        metavar='INSTANCE_CONFIG',
        completer=flags.InstanceConfigCompleter,
        help='Cloud Spanner instance config.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Instance config delete response, which is empty.
    """
    console_io.PromptContinue(
        message='Delete instance config [{0}]. Are you sure?'.format(
            args.config),
        cancel_on_no=True)
    return instance_configs.Delete(args.config, args.etag, args.validate_only)
