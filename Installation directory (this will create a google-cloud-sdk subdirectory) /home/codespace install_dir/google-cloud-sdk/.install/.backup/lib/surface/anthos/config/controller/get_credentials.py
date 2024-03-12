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
"""Fetch Config Controller credentials."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import api_adapter as container_api_adapter
from googlecloudsdk.api_lib.container import util as container_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log

NOT_RUNNING_MSG = """\
Config Controller {0} is not running. The kubernetes API may not be available."""


def _BaseRun(args):
  """Base operations for `get-credentials` run command."""
  container_util.CheckKubectlInstalled()

  cluster_id = 'krmapihost-' + args.name
  location_id = args.location
  project = None

  gke_api = container_api_adapter.NewAPIAdapter('v1')
  log.status.Print('Fetching cluster endpoint and auth data.')
  cluster_ref = gke_api.ParseCluster(cluster_id, location_id, project)
  cluster = gke_api.GetCluster(cluster_ref)

  if not gke_api.IsRunning(cluster):
    log.warning(NOT_RUNNING_MSG.format(cluster_ref.clusterId))

  return cluster, cluster_ref


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class GetCredentialsAlpha(base.Command):
  """Fetch credentials for a running Anthos Config Controller.

  {command} updates a `kubeconfig` file with appropriate credentials and
  endpoint information to point `kubectl` at a specific
  Anthos Config Controller.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To switch to working on your Config Controller 'main', run:

            $ {command} main --location=us-central1
      """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    parser.add_argument('name', help='Name of the Anthos Config Controller.')
    parser.add_argument(
        '--location',
        required=True,
        help='The location (region) of the Anthos Config Controller.')

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Raises:
      container_util.Error: if the cluster is unreachable or not running.
    """
    cluster, cluster_ref = _BaseRun(args)
    container_util.ClusterConfig.Persist(cluster, cluster_ref.projectId)
