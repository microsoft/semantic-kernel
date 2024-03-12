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
"""Command to describe an Anthos on VMware admin cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import vmware_admin_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.vmware import flags

_EXAMPLES = """
To describe an admin cluster named ``my-cluster'' managed in location ``us-west1'',
run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class Describe(base.DescribeCommand):
  """Describe an Anthos on VMware admin cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    flags.AddAdminClusterResourceArg(parser, 'to describe')

  def Run(self, args):
    """Runs the describe command."""
    cluster_ref = args.CONCEPTS.admin_cluster.Parse()
    client = apis.AdminClustersClient()
    return client.Describe(cluster_ref)
