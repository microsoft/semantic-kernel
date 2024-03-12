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
"""Command for bigtable clusters delete."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.bigtable import clusters
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bigtable import arguments
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class DeleteCluster(base.DeleteCommand):
  """Delete a bigtable cluster."""

  detailed_help = {
      'EXAMPLES':
          textwrap.dedent("""\
          To delete a cluster, run:

            $ {command} my-cluster-id --instance=my-instance-id

          """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    arguments.AddClusterResourceArg(parser, 'to delete')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    cluster_ref = args.CONCEPTS.cluster.Parse()
    console_io.PromptContinue(
        'You are about to delete cluster: [{0}]'.format(cluster_ref.Name()),
        throw_if_unattended=True,
        cancel_on_no=True)
    response = clusters.Delete(cluster_ref)
    log.DeletedResource(cluster_ref.Name(), 'cluster')
    return response
