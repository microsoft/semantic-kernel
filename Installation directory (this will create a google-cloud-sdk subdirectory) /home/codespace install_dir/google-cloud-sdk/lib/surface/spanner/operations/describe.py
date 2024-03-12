# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Command for spanner operations describe."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import backup_operations
from googlecloudsdk.api_lib.spanner import database_operations
from googlecloudsdk.api_lib.spanner import instance_config_operations
from googlecloudsdk.api_lib.spanner import instance_operations
from googlecloudsdk.api_lib.spanner import ssd_cache_operations
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.spanner import flags


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Describe(base.DescribeCommand):
  """Describe a Cloud Spanner operation."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To describe a Cloud Spanner instance operation, run:

          $ {command} _auto_12345 --instance=my-instance-id

        To describe a Cloud Spanner database operation, run:

          $ {command}  _auto_12345 --instance=my-instance-id
              --database=my-database-id

        To describe a Cloud Spanner backup operation, run:

          $ {command}  _auto_12345 --instance=my-instance-id
              --backup=my-backup-id
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    mutex_group = parser.add_group(mutex=True, required=True)
    mutex_group.add_argument(
        '--instance-config',
        completer=flags.InstanceConfigCompleter,
        help='The ID of the instance configuration the operation is executing on.'
    )
    mutex_group.add_argument(
        '--instance',
        completer=flags.InstanceCompleter,
        help='The ID of the instance the operation is executing on.')

    flags.AddCommonDescribeArgs(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    if args.instance_config:
      return instance_config_operations.Get(args.instance_config,
                                            args.operation)

    # Checks that user only specified either database or backup flag.
    if (args.IsSpecified('database') and args.IsSpecified('backup')):
      raise c_exceptions.InvalidArgumentException(
          '--database or --backup',
          'Must specify either --database or --backup.')

    if args.backup:
      return backup_operations.Get(args.instance, args.backup, args.operation)

    if args.database:
      return database_operations.Get(args.instance, args.database,
                                     args.operation)

    return instance_operations.Get(args.instance, args.operation)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaDescribe(Describe):
  """Describe a Cloud Spanner operation with ALPHA features."""

  __doc__ = Describe.__doc__

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Please add arguments in alphabetical order except for no- or a clear-
    pair for that argument which can follow the argument itself.
    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    super(AlphaDescribe, AlphaDescribe).Args(parser)

    flags.SsdCache(
        positional=False,
        required=False,
        hidden=True,
        text='The ID of the SSD Cache the operation is executing on.',
    ).AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    if args.ssd_cache:
      if args.instance:
        raise c_exceptions.InvalidArgumentException(
            '--instance or --ssd-cache',
            'The `--instance` flag cannot be used with `--ssd-cache`.',
        )
      return ssd_cache_operations.Get(
          args.operation, args.ssd_cache, args.instance_config
      )

    return super().Run(args)
