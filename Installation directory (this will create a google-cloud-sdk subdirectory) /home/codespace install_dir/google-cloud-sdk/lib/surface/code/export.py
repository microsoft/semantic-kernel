# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Command for creating files for a local development environment."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.code import flags
from googlecloudsdk.command_lib.code import local
from googlecloudsdk.command_lib.code import local_files
from googlecloudsdk.command_lib.code.cloud import cloud
from googlecloudsdk.command_lib.code.cloud import cloud_files
from googlecloudsdk.core.util import files
import six


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Export(base.Command):
  """Writes skaffold and kubernetes files for local development.

  Writes skaffold and kubernetes yaml that builds a docker image
  and runs it locally. In order to build and run the image, run

  > skaffold dev

  This command should be used if there is a need to make
  customizations to the development environment. Otherwise,
  the gcloud local dev command should be used instead.
  """

  @classmethod
  def Args(cls, parser):
    common = flags.CommonFlags()
    common.AddAlphaAndBetaFlags(cls.ReleaseTrack())

    common.AddServiceName()
    common.AddImage()
    common.AddMemory()
    common.AddCpu()
    common.EnvVarsGroup().AddEnvVars()
    common.EnvVarsGroup().AddEnvVarsFile()

    common.BuildersGroup().AddBuilder()

    common.ConfigureParser(parser)

    skaffold_output_group = parser.add_mutually_exclusive_group(required=False)
    skaffold_output_group.add_argument(
        '--skaffold-file',
        default='skaffold.yaml',
        required=False,
        help='Location of the generated skaffold.yaml file.')

    skaffold_output_group.add_argument(
        '--no-skaffold-file',
        default=False,
        action='store_true',
        required=False,
        help='Do not produce a skaffold.yaml file.')

    parser.add_argument(
        '--kubernetes-file',
        default='pods_and_services.yaml',
        help='File containing yaml specifications for kubernetes resources.')

  def Run(self, args):
    if args.IsKnownAndSpecified('cloud') and args.cloud:
      settings = cloud.AssembleSettings(args)
      file_generator = cloud_files.CloudRuntimeFiles(settings)
    else:
      settings = local.AssembleSettings(args, self.ReleaseTrack())
      file_generator = local_files.LocalRuntimeFiles(settings)

    with files.FileWriter(args.kubernetes_file) as output:
      output.write(six.u(file_generator.KubernetesConfig()))

    if not args.no_skaffold_file:
      with files.FileWriter(args.skaffold_file) as output:
        output.write(six.u(file_generator.SkaffoldConfig(args.kubernetes_file)))
