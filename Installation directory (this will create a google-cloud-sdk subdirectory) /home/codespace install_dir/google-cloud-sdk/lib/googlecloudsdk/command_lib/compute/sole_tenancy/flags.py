# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Flags for the `compute sole-tenancy` related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers


def AddNodeAffinityFlagToParser(parser, is_update=False):
  """Adds a node affinity flag used for scheduling instances."""
  sole_tenancy_group = parser.add_group('Sole Tenancy.', mutex=True)
  sole_tenancy_group.add_argument(
      '--node-affinity-file',
      type=arg_parsers.FileContents(),
      help="""\
          The JSON/YAML file containing the configuration of desired nodes onto
          which this instance could be scheduled. These rules filter the nodes
          according to their node affinity labels. A node's affinity labels come
          from the node template of the group the node is in.

          The file should contain a list of a JSON/YAML objects. For an example,
          see https://cloud.google.com/compute/docs/nodes/provisioning-sole-tenant-vms#configure_node_affinity_labels.
          The following list describes the fields:

          *key*::: Corresponds to the node affinity label keys of
          the Node resource.
          *operator*::: Specifies the node selection type. Must be one of:
            `IN`: Requires Compute Engine to seek for matched nodes.
            `NOT_IN`: Requires Compute Engine to avoid certain nodes.
          *values*::: Optional. A list of values which correspond to the node
          affinity label values of the Node resource.
          """)
  sole_tenancy_group.add_argument(
      '--node-group',
      help='The name of the node group to schedule this instance on.')
  sole_tenancy_group.add_argument(
      '--node', help='The name of the node to schedule this instance on.')
  if is_update:
    sole_tenancy_group.add_argument(
        '--clear-node-affinities',
        action='store_true',
        help="""\
          Removes the node affinities field from the instance. If specified,
          the instance node settings will be cleared. The instance will not be
          scheduled onto a sole-tenant node.
          """)
