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
"""Command for spanner instance configs update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import instance_config_operations
from googlecloudsdk.api_lib.spanner import instance_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.util.args import labels_util


class Update(base.UpdateCommand):
  """Update a Cloud Spanner instance configuration."""
  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To update display name of a custom Cloud Spanner instance configuration 'custom-instance-config', run:

          $ {command} custom-instance-config --display-name=nam3-RO-us-central1

        To modify the instance config 'custom-instance-config' by adding label 'k0', with value 'value1' and label 'k1' with value 'value2' and removing labels with key 'k3', run:

         $ {command} custom-instance-config --update-labels=k0=value1,k1=value2 --remove-labels=k3

        To clear all labels of a custom Cloud Spanner instance configuration 'custom-instance-config', run:

          $ {command} custom-instance-config --clear-labels

        To remove an existing label of a custom Cloud Spanner instance configuration 'custom-instance-config', run:

          $ {command} custom-instance-config --remove-labels=KEY1,KEY2
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
        'config',
        metavar='INSTANCE_CONFIG',
        completer=flags.InstanceConfigCompleter,
        help='Cloud Spanner instance config. The \'custom-\' prefix is required '
        'to avoid name conflicts with Google-managed configurations.')

    parser.add_argument(
        '--display-name',
        help='The name of this instance configuration as it appears in UIs.')

    parser.add_argument(
        '--etag', help='Used for optimistic concurrency control.')

    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddUpdateLabelsFlags(parser)

    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Use this flag to validate that the request will succeed before executing it.'
    )

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Instance config update response.
    """
    op = instance_configs.Patch(args)

    # Return immediately when --validate-only is specified. The backend
    # implementation returns a fake operation id (0) in case of --validate-only
    # flag. Waiting for the operation to complete will result in a NOT_FOUND
    # error. As a result, misleading message for users.
    if args.async_ or args.validate_only:
      return op
    return instance_config_operations.Await(op, 'Updating instance-config')
