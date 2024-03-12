# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Command to describe an Anthos cluster on AWS."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import aws as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.aws import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import constants
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import versions
from googlecloudsdk.core import log


_EXAMPLES = """
To describe a cluster named ``my-cluster'' managed in location ``us-west1'',
run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an Anthos cluster on AWS."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddAwsClusterResourceArg(parser, 'to describe')

  def Run(self, args):
    """Runs the describe command."""
    self._upgrade_hint = None
    cluster_ref = resource_args.ParseAwsClusterResourceArg(args)
    with endpoint_util.GkemulticloudEndpointOverride(cluster_ref.locationsId):
      cluster_client = api_util.ClustersClient()
      cluster_info = cluster_client.Get(cluster_ref)
      self._upgrade_hint = versions.upgrade_hint_cluster(
          cluster_ref, cluster_info, constants.AWS
      )
      return cluster_info

  def Epilog(self, results_were_displayed):
    if self._upgrade_hint:
      log.status.Print(self._upgrade_hint)
