# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Export current configuration of an Anthos cluster."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.anthos import flags
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Export(base.BinaryBackedCommand):
  """Export current configuration of an Anthos cluster."""

  detailed_help = {
      'EXAMPLES': """
      To export configuration from cluster 'my-cluster' to the local directory
      `my-dir` using project 'my-project':

          $ {command} my-cluster --project=my-project --output-directory=my-dir
      """,
  }

  @staticmethod
  def Args(parser):
    flags.GetClusterFlag(positional=True,
                         help_override='The cluster name from '
                                       'which to export the '
                                       'configurations.').AddToParser(parser)
    flags.GetLocationFlag().AddToParser(parser)
    flags.GetOutputDirFlag().AddToParser(parser)
    common_args.ProjectArgument(
        help_text_to_overwrite='Project ID.').AddToParser(parser)

  def Run(self, args):
    command_executor = anthoscli_backend.AnthosCliWrapper()
    export_project = args.project or properties.VALUES.core.project.Get()
    cluster = args.CLUSTER or  properties.VALUES.compute.zone.Get()
    location = args.location
    output_dir = args.OUTPUT_DIRECTORY
    auth_cred = anthoscli_backend.GetAuthToken(
        account=properties.VALUES.core.account.Get(), operation='export')

    log.status.Print('Starting export of cluster [{}] using '
                     'project [{}]'.format(cluster, export_project))
    response = command_executor(command='export',
                                cluster=cluster,
                                project=export_project,
                                location=location,
                                output_dir=output_dir,
                                show_exec_error=args.show_exec_error,
                                env=anthoscli_backend.GetEnvArgsForCommand(
                                    extra_vars={'GCLOUD_AUTH_PLUGIN': 'true'}),
                                stdin=auth_cred)
    return self._DefaultOperationResponseHandler(response)
