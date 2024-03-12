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
"""Command for listing Stacks resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.run.integrations import graph
from googlecloudsdk.command_lib.run.integrations import run_apps_operations
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ExportGraph(base.ListCommand):
  """Export a graph for Stacks resources."""

  def Run(self, args):
    """Export a graph for Stacks resources.

    Args:
      args: ArgumentParser, used to reference the inputs provided by the user.

    Returns:
      dict with a single key that maps to a list of resources.
      This will be used by the integration_list_printer to format all
      the entries in the list.

      The reason this is not a list is because the printer will only recieve
      one entry at a time and cannot easily format all entries into a table.
    """
    release_track = self.ReleaseTrack()

    with run_apps_operations.Connect(args, release_track) as client:
      return client.GetBindingData()

  def Display(self, args, bindings):
    """This method is called to print the result of the Run() method.

    Args:
      args: all the arguments that were provided to this command invocation.
      bindings: The binding data returned from Run().
    """
    del args
    if bindings:
      for line in graph.GenerateBindingGraph(bindings, 'ResourcesGraph'):
        log.out.write(line)
        log.out.write('\n')
