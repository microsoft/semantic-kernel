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
"""Fetch default Config Connector identity."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io

from googlecloudsdk.api_lib.container import util as container_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.composer import util as composer_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def _BaseRun(args):
  """Base operations for `get-config-connector-identity` run command."""
  container_util.CheckKubectlInstalled()

  cluster_id = 'krmapihost-' + args.name
  location = args.location
  project_id = args.project or properties.VALUES.core.project.GetOrFail()

  GetConfigConnectorIdentityForCluster(location, cluster_id, project_id)


def GetConfigConnectorIdentityForCluster(location, cluster_id, project_id):
  """Get Config Connector identity for the given cluster."""
  with composer_util.TemporaryKubeconfig(location, cluster_id):
    output = io.StringIO()
    composer_util.RunKubectlCommand([
        'get', 'ConfigConnectorContext', '-o',
        'jsonpath="{.items[0].spec.googleServiceAccount}"'
    ],
                                    out_func=output.write,
                                    err_func=log.err.write,
                                    namespace='config-control')
    identity = output.getvalue().replace('"', '')
    log.status.Print(
        'Default Config Connector identity: [{identity}].\n'
        '\n'
        'For example, to give Config Connector permission to manage Google Cloud resources in the same project:\n'
        'gcloud projects add-iam-policy-binding {project_id} \\\n'
        '    --member \"serviceAccount:{identity}\" \\\n'
        '    --role \"roles/owner\" \\\n'
        '    --project {project_id}\n'.format(
            identity=identity, project_id=project_id))


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class GetConfigConnectorIdentity(base.Command):
  """Fetch default Config Connector identity.

  {command} prints the default Config Connector Google Service Account in
  a specific Anthos Config Controller.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To print the default Config Connector identity used by your
          Config Controller 'main' in the location 'us-central1', run:

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
    """
    _BaseRun(args)
