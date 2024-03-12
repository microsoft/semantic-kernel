# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""SSH/SCP utilities for Cloud TPU Queued Resource commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
import six


def ParseNodeFlag(node_flag, node_specs):
  """Parses the --node flag into a list of node_specs."""
  num_nodes = len(node_specs)
  if six.text_type(node_flag).upper() == 'ALL':
    indexes = list(range(num_nodes))
  else:
    indexes = set()
    ranges = node_flag.split(',')
    for r in ranges:
      if not r:
        continue
      if '-' in r:
        bounds = r.split('-')
        if len(bounds) != 2 or not bounds[0] or not bounds[1]:
          raise exceptions.InvalidArgumentException(
              '--node',
              'Range "{}" does not match expected format'
              ' "lowerBound-upperBound", where lowerBound < upperBound.'.format(
                  r
              ),
          )
        start, end = int(bounds[0]), int(bounds[1])
        if start >= end:
          raise exceptions.InvalidArgumentException(
              '--node',
              'Range "{}" does not match expected format'
              ' "lowerBound-upperBound", where lowerBound < upperBound.'.format(
                  r
              ),
          )
        indexes.update(range(start, end + 1))
      else:
        try:
          indexes.add(int(r))
        except ValueError:
          raise exceptions.InvalidArgumentException(
              '--node',
              'unable to parse node ID {}. Please only use numbers.'.format(r),
          )

  if not indexes:
    raise exceptions.InvalidArgumentException(
        '--node',
        'Unable to parse node ranges from {}.'.format(node_flag),
    )

  mx = max(indexes)
  if mx >= num_nodes:
    raise exceptions.InvalidArgumentException(
        '--node',
        'node index {} is larger than the valid node indices on this TPU Queued'
        ' Resource. Please only use indexes in the range [0, {}], inclusive.'
        .format(mx, num_nodes - 1),
    )

  # Get the filtered node specs.
  filtered_node_specs = []
  for node in indexes:
    filtered_node_specs.append(node_specs[node])
  return filtered_node_specs


def WaitForNodeBatchCompletion(ssh_threads, nodes):
  """Waits for the completion of batch, but does not block for failures.

  Args:
    ssh_threads: List of ssh threads.
    nodes: List of SSH prepped nodes.
  """
  for ssh_thread in ssh_threads:
    ssh_thread.join()

  for node in nodes:
    if node:
      log.status.Print('Finished preparing node {}.'.format(node.tpu_name))
