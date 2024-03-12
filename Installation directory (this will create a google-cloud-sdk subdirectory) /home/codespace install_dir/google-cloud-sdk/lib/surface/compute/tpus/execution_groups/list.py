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
"""Command for list TPU node and GCE VM combinations created."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.tpus.execution_groups import util as tpu_utils


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  r"""List TPU Node+VM groups created by execution group.

  ## EXAMPLES

  To list all active execution groups, run:

    $ {command} --zone=test-zone --project=test-project
  """

  @classmethod
  def Args(cls, parser):
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='list')
    parser.display_info.AddFormat('table(name, status)')

  def Run(self, args):
    tpu_utils.DefaultArgs.ValidateZone(args)

    responses = []
    instances = {}
    nodes = {}
    instance_helper = tpu_utils.Instance(self.ReleaseTrack())
    for instance in instance_helper.List(args.zone):
      instances[instance.name] = instance

    node_helper = tpu_utils.TPUNode(self.ReleaseTrack())
    for node in node_helper.List(args.zone):
      nodes[node_helper.NodeName(node)] = node

    for name, instance in instances.items():
      if name not in nodes.keys():
        responses.append(ListResult(name, 'Paused'))
      elif instance_helper.IsRunning(instance) and node_helper.IsRunning(
          nodes[name]):
        responses.append(ListResult(name, 'Running'))
      else:
        responses.append(ListResult(name, 'Unknown Status'))
    return sorted(responses)


class ListResult(object):

  def __init__(self, name, status):
    self.name = name
    self.status = status

  def __gt__(self, lr):
    return self.name + self.status > lr.name + lr.status
