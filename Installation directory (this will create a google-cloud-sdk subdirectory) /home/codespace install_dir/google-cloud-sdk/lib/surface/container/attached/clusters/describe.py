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
"""Command to describe an Attached cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkemulticloud import attached as api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.attached import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util

_EXAMPLES = """
To describe a cluster named ``my-cluster'' managed in location ``us-west1'',
run:

$ {command} my-cluster --location=us-west1
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an Attached cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser):
    """Registers flags for this command."""
    resource_args.AddAttachedClusterResourceArg(parser, 'to describe')

  def Run(self, args):
    """Runs the describe command."""
    location = resource_args.ParseAttachedClusterResourceArg(args).locationsId
    with endpoint_util.GkemulticloudEndpointOverride(location):
      cluster_ref = resource_args.ParseAttachedClusterResourceArg(args)
      cluster_client = api_util.ClustersClient()
      return cluster_client.Get(cluster_ref)
