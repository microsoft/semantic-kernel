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

from apitools.base.py.exceptions import HttpConflictError
from apitools.base.py.exceptions import HttpNotFoundError

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.tpus import flags as tpus_flags
from googlecloudsdk.command_lib.compute.tpus.execution_groups import util as tpu_utils
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Resume(base.Command):
  r"""Creates Google Compute TPU and resumes the VM.

  ## EXAMPLES

  To resume a suspended TPU VM combination, run:

    $ {command} test-execution-group --zone=test-zone --project=test-project \
    --accelerator-type=v2-8 --tf-version=2.4.1

  """

  @classmethod
  def Args(cls, parser):
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='resume')
    tpus_flags.AddTpuNameArg(parser)
    tpus_flags.GetAcceleratorTypeFlag().AddToParser(parser)
    tpus_flags.AddTfVersionFlagForResume(parser)
    tpus_flags.AddPreemptibleFlag(parser)
    tpus_flags.AddVmOnlyFlag(parser)
    tpus_flags.AddNetworkArgsForResume(parser)

  def Run(self, args):
    tpu_utils.DefaultArgs.ValidateZone(args)

    responses = []
    tpu = tpu_utils.TPUNode(self.ReleaseTrack())
    tpu_operation_ref = None
    instance_operation_ref = None
    if not args.vm_only:
      try:
        tpu_operation_ref = tpu.Create(args.execution_group_name,
                                       args.accelerator_type, args.tf_version,
                                       args.zone, args.preemptible,
                                       args.network)
      except HttpConflictError:
        log.status.Print('TPU Node with name:{} already exists, '
                         'try a different name'.format(
                             args.execution_group_name))
        return responses

    instance = tpu_utils.Instance(self.ReleaseTrack())
    try:
      instance_operation_ref = instance.Start(
          args.execution_group_name, args.zone)
    except HttpNotFoundError:
      log.status.Print('Instance:{} not found, possibly deleted.'.format(
          args.execution_group_name))
      return responses

    if instance_operation_ref:
      instance_start_response = instance.WaitForOperation(
          instance_operation_ref, 'Starting GCE VM')
      responses.append(instance_start_response)

    if tpu_operation_ref:
      responses.append(
          tpu.WaitForOperation(tpu_operation_ref, 'Creating TPU node:{}'.format(
              args.execution_group_name)))

    return responses


