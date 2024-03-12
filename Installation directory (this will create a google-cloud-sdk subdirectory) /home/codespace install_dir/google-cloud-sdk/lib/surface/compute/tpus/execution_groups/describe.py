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
"""Command for describing the status of the TPU node and GCE VM combination."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.exceptions import HttpNotFoundError
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.tpus import flags as tpus_flags
from googlecloudsdk.command_lib.compute.tpus.execution_groups import util as tpu_utils


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  r"""Describe Google Compute TPU + VM combination.

  ## EXAMPLES

  To describe the TPU and VM combination, run:

    $ {command} test-execution-group --zone=test-zone --project=test-project

  """

  @classmethod
  def Args(cls, parser):
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='describe')
    tpus_flags.AddTpuNameArg(parser)
    parser.display_info.AddFormat('table(Field, Value)')

  def Run(self, args):
    tpu_utils.DefaultArgs.ValidateZone(args)

    responses = []
    instance_helper = tpu_utils.Instance(self.ReleaseTrack())
    try:
      instance = instance_helper.Get(args.execution_group_name, args.zone)
    except HttpNotFoundError:
      # As it stands, we provide vm-only option but no tpu-only option. So if
      # there is no VM, then we can safely short-circuit and claim the
      # execution group is not found.
      responses.append(
          GetResult('Execution Group Status:', 'Not Found'))
      return responses

    responses.append(
        GetResult(
            'Compute Engine Instance IP Address:',
            instance.networkInterfaces and instance.networkInterfaces[0] and
            instance.networkInterfaces[0].networkIP))
    responses.append(
        GetResult('Compute Engine Created:', instance.creationTimestamp))
    responses.append(
        GetResult('Compute Engine Machine Type:', instance.machineType))

    node_helper = tpu_utils.TPUNode(self.ReleaseTrack())
    node = None
    try:
      node = node_helper.Get(args.execution_group_name, args.zone)
    except HttpNotFoundError:
      responses.append(GetResult('TPU Node status:', 'Not Found'))

    if node:
      responses.append(GetResult('TPU Accelerator Type:', node.acceleratorType))
      responses.append(
          GetResult(
              'TPU IP Address:', node.networkEndpoints and
              node.networkEndpoints[0] and
              node.networkEndpoints[0].ipAddress))
      responses.append(GetResult('TPU TF Version:', node.tensorflowVersion))
      responses.append(GetResult('TPU Service Account:', node.serviceAccount))
      responses.append(GetResult('TPU Created:', node.createTime))
      responses.append(GetResult('TPU State:', node.state))
      responses.append(GetResult('TPU Health:', node.health))
      responses.append(
          GetResult('TPU Preemptible:', node.schedulingConfig and
                    node.schedulingConfig.preemptible))

    return responses


class GetResult(object):

  def __init__(self, status_field, status_value):
    self.field = status_field
    self.value = status_value

  def __gt__(self, lr):
    return self.field > lr.field
