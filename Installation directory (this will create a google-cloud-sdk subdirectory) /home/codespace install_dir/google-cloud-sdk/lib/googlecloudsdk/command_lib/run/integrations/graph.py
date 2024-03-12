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
"""stuff."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import List

from googlecloudsdk.api_lib.run.integrations import types_utils
from googlecloudsdk.command_lib.run.integrations.typekits import base
from googlecloudsdk.generated_clients.apis.runapps.v1alpha1 import runapps_v1alpha1_messages as runapps


_EDGE_FORMAT = '  "{edge_source}":n -> "{edge_dest}":n;'
_LABEL_FORMAT = '{type} | <n> {name}'


def GenerateBindingGraph(bindings: List[base.BindingData], name: str):
  """Produce graph of the given bindings.

  Args:
    bindings: the list of bindings.
    name: name of the graph

  Yields:
    the binding graph in DOT format.
  """
  yield 'strict digraph {graph_name} {{'.format(graph_name=name)
  yield '  node [style="filled" shape=Mrecord penwidth=2]'
  yield '  rankdir=LR'
  yield '\n'

  in_counter = {}
  out_counter = {}
  ids = {}
  # Edges
  for binding in bindings:
    source_id = binding.from_id
    dest_id = binding.to_id
    ids[_NodeName(source_id)] = source_id
    ids[_NodeName(dest_id)] = dest_id
    _CountType(out_counter, source_id)
    _CountType(in_counter, dest_id)
    yield _GraphvizEdge(source_id, dest_id)
  yield '\n'
  # Node styles
  for name in ids:
    res_id = ids[name]
    in_count = in_counter.get(res_id.type, 0)
    out_count = out_counter.get(res_id.type, 0)
    yield _GraphvizNode(res_id, in_count, out_count)

  # End the graph.
  yield '}'


def _CountType(counter, res_id):
  counter[res_id.type] = counter.get(res_id.type, 0) + 1


def _GraphvizEdge(from_id, to_id):
  return _EDGE_FORMAT.format(
      edge_source=_NodeName(from_id),
      edge_dest=_NodeName(to_id),
  )


def _GraphvizNode(
    res_id: runapps.ResourceID, in_count: int, out_count: int
) -> str:
  """Style for the node.

  Args:
    res_id: resource ID of the node
    in_count: number of bindings going into this node
    out_count: number of bindings coming out of this node

  Returns:
    node style code in DOT
  """
  ingress = in_count == 0 and out_count > 0
  backing = out_count == 0 and in_count > 0
  # All colors are from go/gcolors
  if ingress:
    color = '#e37400'  # Google Yellow 900
    fillcolor = '#fdd663'  # Google Yellow 300
  elif backing:
    color = '#0d652d'  # Google Green 900
    fillcolor = '#81c995'  # Google Green 300
  else:
    color = '#174ea6'  # Google Blue 900
    fillcolor = '#8ab4f8'  # Google Blue 300
  return (
      '  "{}" [label="{}" color="{}" fillcolor="{}"]'.format(
          _NodeName(res_id), _NodeLabel(res_id), color, fillcolor
      )
  )


def _NodeName(res_id: runapps.ResourceID) -> str:
  return '{}/{}'.format(res_id.type, res_id.name)


def _NodeLabel(res_id: runapps.ResourceID) -> str:
  type_metadata = types_utils.GetTypeMetadataByResourceType(res_id.type)
  type_name = res_id.type.capitalize()
  if type_metadata and type_metadata.label:
    type_name = type_metadata.label
  return _LABEL_FORMAT.format(type=type_name, name=res_id.name)
