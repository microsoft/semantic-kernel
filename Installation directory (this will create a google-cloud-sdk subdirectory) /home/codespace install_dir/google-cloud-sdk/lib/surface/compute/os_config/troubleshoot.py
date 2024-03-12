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
"""Command for troubleshooting problems with the VM Manager."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.instances import flags
from googlecloudsdk.command_lib.compute.os_config import troubleshooter


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Troubleshoot(base.Command):
  """Troubleshoot VM Manager issues."""

  def _ResolveInstance(self, holder, compute_client, args):
    """Resolves the arguments into an instance.

    Args:
      holder: the api holder
      compute_client: the compute client
      args: The command line arguments.

    Returns:
      An instance reference to a VM.
    """
    resources = holder.resources
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=flags.GetInstanceZoneScopeLister(compute_client))
    return instance_ref

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client

    instance_ref = self._ResolveInstance(holder, compute_client, args)
    troubleshooter.Troubleshoot(compute_client,
                                instance_ref,
                                self.ReleaseTrack())
    return

Troubleshoot.detailed_help = {
    'brief':
        'Troubleshoot issues with the setup of VM Manager on a specified VM '
        'instance',
    'DESCRIPTION':
        """
    *{command}* troubleshoots issues with the setup of VM Manager on a specified
    VM instance

    The troubleshoot command investigates the following settings or configurations for your VM Manager setup:\n
    - Checks if the OS Config API is enabled in the project.
    - Checks if the required metadata is set up correctly in the VM instance.
    - Checks if the latest version of the OS Config agent is running on the VM instance.
    - Checks if a service account is attached to the VM instance.
    - Checks if the VM Manager service agent is enabled.
    - Checks if the VM instance has a public IP or Private Google Access.
    """,
    'EXAMPLES': """
    To troubleshoot an instance named `my-instance` in zone `us-west1-a`, run

        $ {command} my-instance --zone=us-west1-a
    """
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class TroubleshootAlpha(base.Command):
  """(ALPHA) Troubleshoot VM Manager issues."""

  def _ResolveInstance(self, holder, compute_client, args):
    """Resolves the arguments into an instance.

    Args:
      holder: the api holder
      compute_client: the compute client
      args: The command line arguments.

    Returns:
      An instance reference to a VM.
    """
    resources = holder.resources
    instance_ref = flags.INSTANCE_ARG.ResolveAsResource(
        args,
        resources,
        scope_lister=flags.GetInstanceZoneScopeLister(compute_client))
    return instance_ref

  @staticmethod
  def Args(parser):
    flags.INSTANCE_ARG.AddArgument(parser)
    parser.add_argument('--enable-log-analysis',
                        required=False,
                        action='store_true',
                        help=(
                            'Enable the checking of audit logs created by Cloud'
                            ' Logging. The troubleshooter checks the VM\'s '
                            'Cloud Logging logs and serial log output for '
                            'errors, provides you with the analysis data, and '
                            'allows you to download the logs.'
                        ))

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    compute_client = holder.client

    instance_ref = self._ResolveInstance(holder, compute_client, args)
    troubleshooter.Troubleshoot(compute_client,
                                instance_ref,
                                self.ReleaseTrack(),
                                analyze_logs=args.enable_log_analysis)
    return

TroubleshootAlpha.detailed_help = {
    'brief':
        'Troubleshoot issues with the setup of VM Manager on a specified VM '
        'instance',
    'DESCRIPTION':
        """
    *{command}* troubleshoots issues with the setup of VM Manager on a specified
    VM instance

    The troubleshoot command investigates the following settings or configurations for your VM Manager setup:\n
    - Checks if the OS Config API is enabled in the project.\n
    - Checks if the required metadata is set up correctly in the VM instance.\n
    - Checks if the latest version of the OS Config agent is running on the VM instance.\n
    - Checks if a service account is attached to the VM instance.\n
    - Checks if the VM Manager service agent is enabled.\n
    - Checks if the VM instance has a public IP or Private Google Access.
    """,
    'EXAMPLES': """
    To troubleshoot an instance named `my-instance` in zone `us-west1-a`, run

        $ {command} my-instance --zone=us-west1-a

    To troubleshoot the same instance in the same zone with log analysis, run

        $ {command} my-instance --zone=us-west1-a --enable-log-analysis
    """
}
