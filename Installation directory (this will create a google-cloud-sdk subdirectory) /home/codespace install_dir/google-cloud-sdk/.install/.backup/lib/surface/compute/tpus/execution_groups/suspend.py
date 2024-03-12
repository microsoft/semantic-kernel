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
"""Command for suspending the TPU node and GCE VM combination."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.exceptions import HttpNotFoundError
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.tpus import flags as tpus_flags
from googlecloudsdk.command_lib.compute.tpus.execution_groups import util as tpu_utils
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Suspend(base.Command):
  r"""Deletes Google Compute TPU and suspends the VM.

  ## EXAMPLES

  To delete the TPU and suspend the VM, run:

    $ {command} test-execution-group --zone=test-zone --project=test-project

  """

  @classmethod
  def Args(cls, parser):
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='suspend')
    tpus_flags.AddTpuNameArg(parser)

  def Run(self, args):
    tpu_utils.DefaultArgs.ValidateZone(args)

    responses = []
    instance = tpu_utils.Instance(self.ReleaseTrack())
    instance_operation_ref = None
    try:
      instance_operation_ref = instance.Stop(args.execution_group_name,
                                             args.zone)
    except HttpNotFoundError:
      log.status.Print(
          'Instance:{} not found, possibly already deleted.'.format(
              args.execution_group_name))

    tpu_operation_ref = None
    tpu = tpu_utils.TPUNode(self.ReleaseTrack())
    try:
      tpu_operation_ref = tpu.Delete(args.execution_group_name, args.zone)
    except HttpNotFoundError:
      log.status.Print(
          'TPU Node:{} not found, possibly already deleted.'.format(
              args.execution_group_name))

    if instance_operation_ref:
      try:
        instance_delete_response = instance.WaitForOperationNoResources(
            instance_operation_ref, 'Suspending GCE VM')
        responses.append(instance_delete_response)
      except HttpNotFoundError:
        log.status.Print(
            'Instance:{} not found, possibly already deleted.'.format(
                args.execution_group_name))

    if tpu_operation_ref:
      try:
        responses.append(
            tpu.WaitForOperationNoResources(
                tpu_operation_ref, 'Deleting TPU node'))
      except HttpNotFoundError:
        log.status.Print(
            'TPU Node:{} not found, possibly already deleted.'.format(
                args.execution_group_name))

    return responses
