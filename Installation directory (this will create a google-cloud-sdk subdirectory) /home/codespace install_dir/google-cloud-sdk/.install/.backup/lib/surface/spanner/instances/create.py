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
"""Command for spanner instances create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import instance_configs
from googlecloudsdk.api_lib.spanner import instance_operations
from googlecloudsdk.api_lib.spanner import instances
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import resource_args


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Create(base.CreateCommand):
  """Create a Cloud Spanner instance."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To create a Cloud Spanner instance, run:

          $ {command} my-instance-id --config=regional-us-east1 --description=my-instance-display-name --nodes=3
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
    flags.Instance().AddToParser(parser)
    flags.Config().AddToParser(parser)
    flags.Description().AddToParser(parser)
    resource_args.AddExpireBehaviorArg(parser)
    resource_args.AddInstanceTypeArg(parser)
    flags.AddCapacityArgsForInstance(
        require_all_autoscaling_args=True,
        hide_autoscaling_args=True,
        parser=parser,
    )
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(flags.InstanceCompleter)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    instance_type = resource_args.GetInstanceType(args)
    expire_behavior = resource_args.GetExpireBehavior(args)

    op = instances.Create(
        instance=args.instance,
        config=args.config,
        description=args.description,
        nodes=args.nodes,
        processing_units=args.processing_units,
        autoscaling_min_nodes=args.autoscaling_min_nodes,
        autoscaling_max_nodes=args.autoscaling_max_nodes,
        autoscaling_min_processing_units=args.autoscaling_min_processing_units,
        autoscaling_max_processing_units=args.autoscaling_max_processing_units,
        autoscaling_high_priority_cpu_target=args.autoscaling_high_priority_cpu_target,
        autoscaling_storage_target=args.autoscaling_storage_target,
        instance_type=instance_type,
        expire_behavior=expire_behavior,
    )
    if args.async_:
      return op
    instance_operations.Await(op, 'Creating instance')


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class BetaCreate(base.CreateCommand):
  """Create a Cloud Spanner instance."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To create a Cloud Spanner instance, run:

          $ {command} my-instance-id --config=regional-us-east1 --description=my-instance-display-name --nodes=3
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
    flags.Instance().AddToParser(parser)
    flags.Config().AddToParser(parser)
    flags.Description().AddToParser(parser)
    resource_args.AddExpireBehaviorArg(parser)
    resource_args.AddInstanceTypeArg(parser)
    flags.AddCapacityArgsForInstance(
        require_all_autoscaling_args=True,
        hide_autoscaling_args=False,
        parser=parser,
    )
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(flags.InstanceCompleter)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    instance_type = resource_args.GetInstanceType(args)
    expire_behavior = resource_args.GetExpireBehavior(args)

    op = instances.Create(
        instance=args.instance,
        config=args.config,
        description=args.description,
        nodes=args.nodes,
        processing_units=args.processing_units,
        autoscaling_min_nodes=args.autoscaling_min_nodes,
        autoscaling_max_nodes=args.autoscaling_max_nodes,
        autoscaling_min_processing_units=args.autoscaling_min_processing_units,
        autoscaling_max_processing_units=args.autoscaling_max_processing_units,
        autoscaling_high_priority_cpu_target=args.autoscaling_high_priority_cpu_target,
        autoscaling_storage_target=args.autoscaling_storage_target,
        instance_type=instance_type,
        expire_behavior=expire_behavior,
    )
    if args.async_:
      return op
    instance_operations.Await(op, 'Creating instance')


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaCreate(Create):
  """Create a Cloud Spanner instance with ALPHA features."""
  __doc__ = Create.__doc__

  @staticmethod
  def Args(parser):
    """See base class."""
    flags.Instance().AddToParser(parser)
    flags.Config().AddToParser(parser)
    flags.Description().AddToParser(parser)
    flags.SsdCache().AddToParser(parser)
    resource_args.AddExpireBehaviorArg(parser)
    resource_args.AddInstanceTypeArg(parser)
    resource_args.AddDefaultStorageTypeArg(parser)
    flags.AddCapacityArgsForInstance(
        require_all_autoscaling_args=True,
        hide_autoscaling_args=False,
        parser=parser,
    )
    base.ASYNC_FLAG.AddToParser(parser)
    parser.display_info.AddCacheUpdater(flags.InstanceCompleter)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    instance_type = resource_args.GetInstanceType(args)
    expire_behavior = resource_args.GetExpireBehavior(args)
    default_storage_type = resource_args.GetDefaultStorageTypeArg(args)
    if default_storage_type is None:
      default_storage_type = self.FetchValueFromAllowedStorageTypes(args.config)

    if default_storage_type is None:
      return ('Operation unsuccessful. Default storage type value could not be '
              'determined.')

    op = instances.Create(
        args.instance,
        args.config,
        args.description,
        args.nodes,
        args.processing_units,
        args.autoscaling_min_nodes,
        args.autoscaling_max_nodes,
        args.autoscaling_min_processing_units,
        args.autoscaling_max_processing_units,
        args.autoscaling_high_priority_cpu_target,
        args.autoscaling_storage_target,
        instance_type,
        expire_behavior,
        default_storage_type,
        args.ssd_cache,
    )
    if args.async_:
      return op
    instance_operations.Await(op, 'Creating instance')

  # Return the first value in the config's allowed-storage-types;
  # Else, return SSD.
  def FetchValueFromAllowedStorageTypes(self, instance_config_id):
    instance_config = instance_configs.Get(instance_config_id)
    allowed_storage_types = instance_config.allowedStorageTypes
    msgs = apis.GetMessagesModule('spanner', 'v1')
    if not allowed_storage_types:
      return msgs.Instance.DefaultStorageTypeValueValuesEnum.SSD
    first_allowed_storage_type = allowed_storage_types[0]
    if first_allowed_storage_type == msgs.InstanceConfig.AllowedStorageTypesValueListEntryValuesEnum.SSD:
      return msgs.Instance.DefaultStorageTypeValueValuesEnum.SSD
    elif first_allowed_storage_type == msgs.InstanceConfig.AllowedStorageTypesValueListEntryValuesEnum.HDD:
      return msgs.Instance.DefaultStorageTypeValueValuesEnum.HDD
    else:
      return None
