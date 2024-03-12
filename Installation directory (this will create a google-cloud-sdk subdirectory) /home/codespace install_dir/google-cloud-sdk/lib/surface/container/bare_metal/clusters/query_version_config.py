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
"""Command to query Anthos on bare metal version configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.gkeonprem import bare_metal_clusters as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_arguments
from googlecloudsdk.command_lib.container.bare_metal import cluster_flags as flags

_EXAMPLES = """
To query all available versions in location `us-west1`, run:

$ {command} --location=us-west1

To query versions for creating a cluster with an admin cluster membership named
`my-admin-cluster-membership` managed in project `my-admin-cluster-project` and
location `us-west`, run:

$ {command} --location=us-west1 --admin-cluster-membership=my-admin-cluster-membership --admin-cluster-membership-project=my-admin-cluster-project

To query versions for upgrading a user cluster named `my-user-cluster` in
location `us-west1`, run:

$ {command} --location=us-west1 --cluster=my-user-cluster
"""


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class QueryVersionConfig(base.Command):
  """Query versions for creating or upgrading an Anthos on bare metal user cluster."""

  detailed_help = {'EXAMPLES': _EXAMPLES}

  @staticmethod
  def Args(parser: parser_arguments.ArgumentInterceptor):
    """Registers flags for this command."""
    flags.AddLocationResourceArg(parser, verb='to query versions')
    flags.AddConfigType(parser)

  def Run(self, args):
    """Runs the query-version-config command."""
    client = apis.ClustersClient()
    return client.QueryVersionConfig(args)
