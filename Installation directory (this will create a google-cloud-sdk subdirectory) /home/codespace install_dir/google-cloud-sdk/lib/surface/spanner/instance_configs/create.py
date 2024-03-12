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
"""Command for spanner instance configs create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap
from googlecloudsdk.api_lib.spanner import instance_config_operations
from googlecloudsdk.api_lib.spanner import instance_configs
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as c_exceptions
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.util.args import labels_util


class Create(base.CreateCommand):
  """Create a Cloud Spanner instance configuration."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
        To create a custom Cloud Spanner instance configuration based on an existing Google-managed configuration (nam3) by adding a 'READ_ONLY' type replica in location 'us-east4', run:

          $ {command} custom-instance-config
            --clone-config=nam3
            --add-replicas=location=us-east4,type=READ_ONLY

        To create a custom Cloud Spanner instance configuration based on another custom configuration (custom-instance-config) by adding a 'READ_ONLY' type replica in location 'us-east1' and removing a 'READ_ONLY' type replica in location 'us-east4', run:

          $ {command} custom-instance-config1
            --clone-config=custom-instance-config
            --add-replicas=location=us-east1,type=READ_ONLY
            --skip-replicas=location=us-east4,type=READ_ONLY
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
        help='Cloud Spanner instance configuration. The \'custom-\' prefix is required '
        'to avoid name conflicts with Google-managed configurations.')

    parser.add_argument(
        '--display-name',
        help='The name of this instance configuration as it appears in UIs. '
        'Must specify this option if creating an instance-config with '
        '--replicas.')

    parser.add_argument(
        '--etag', help='Used for optimistic concurrency control.')

    base.ASYNC_FLAG.AddToParser(parser)
    labels_util.AddCreateLabelsFlags(parser)

    parser.add_argument(
        '--validate-only',
        action='store_true',
        default=False,
        help='Use this flag to validate that the request will succeed before executing it.'
    )

    replica_help_text = """\
        The geographic placement of nodes in this instance configuration and
        their replication types.

        *location*::: The location of the serving resources, e.g. "us-central1".

        *type*::: The type of replica.

        Items in the list are separated by ":". The allowed values and formats
        are as follows.

        *READ_ONLY*::::

        Read-only replicas only support reads (not writes). Read-only
        replicas:

          * Maintain a full copy of your data.

          * Serve reads.

          * Do not participate in voting to commit writes.

          * Are not eligible to become a leader.

        *READ_WRITE*::::

        Read-write replicas support both reads and writes. These
        replicas:

          * Maintain a full copy of your data.

          * Serve reads.

          * Can vote whether to commit a write.

          * Participate in leadership election.

          * Are eligible to become a leader.

        *WITNESS*::::

        Witness replicas don't support reads but do participate in
        voting to commit writes. Witness replicas:

          * Do not maintain a full copy of data.

          * Do not serve reads.

          * Vote whether to commit writes.

          * Participate in leader election but are not eligible to become
            leader.

        """
    clone_or_manual = parser.add_mutually_exclusive_group(required=True)
    manual_flags = clone_or_manual.add_argument_group(
        'Command-line flags to setup a custom instance configuration replicas:')
    flags.ReplicaFlag(manual_flags, name='--replicas', text=replica_help_text)
    manual_flags.add_argument(
        '--base-config',
        required=True,
        help='The name of the Google-managed instance configuration, based on which your custom configuration is created.'
    )

    clone_flags = clone_or_manual.add_argument_group(
        'Command-line flags to setup a custom instance configuration using clone options:'
    )
    clone_flags.add_argument(
        '--clone-config',
        required=True,
        metavar='INSTANCE_CONFIG',
        completer=flags.InstanceConfigCompleter,
        help='The ID of the instance config, based on which this '
        'configuration is created. The clone is an independent copy of this '
        'config. Available configurations can be found by running '
        '"gcloud spanner instance-configs list"')
    flags.ReplicaFlag(
        clone_flags,
        name='--add-replicas',
        text='Add new replicas while cloning from the source config.',
        required=False)
    flags.ReplicaFlag(
        clone_flags,
        name='--skip-replicas',
        text='Skip replicas from the source config while cloning. Each replica '
        'in the list must exist in the source config replicas list.',
        required=False)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Instance config create response.
    """
    if args.clone_config:
      # If the config exists, it's cloned, otherwise, we display the
      # error from instanceConfigs.Get.
      config = instance_configs.Get(args.clone_config)
      op = instance_configs.CreateUsingExistingConfig(args, config)
    else:
      if not args.IsSpecified('display_name'):
        raise c_exceptions.InvalidArgumentException(
            '--display-name', 'Must specify --display-name.')

      op = instance_configs.CreateUsingReplicas(args.config, args.display_name,
                                                args.base_config, args.replicas,
                                                args.validate_only, args.labels,
                                                args.etag)
    # Return immediately when --validate-only is specified. The backend
    # implementation returns a fake operation id (0) in case of --validate-only
    # flag. Waiting for the operation to complete will result in a NOT_FOUND
    # error. As a result, misleading message for users.
    if args.async_ or args.validate_only:
      return op
    return instance_config_operations.Await(op, 'Creating instance-config')
