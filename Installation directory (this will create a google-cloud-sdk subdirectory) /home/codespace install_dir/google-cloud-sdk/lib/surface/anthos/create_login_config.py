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
"""Authenticate clusters using the Anthos client.."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.anthos import anthoscli_backend
from googlecloudsdk.command_lib.anthos import flags
from googlecloudsdk.command_lib.anthos.common import kube_flags


class CreateLoginConfig(base.BinaryBackedCommand):
  """Generates a login configuration file.

   Generates the file containing configuration information developers
   will use to authenticate to an AWS Anthos cluster.
  """

  detailed_help = {
      'EXAMPLES': """
      To generate the default login config file (kubectl-anthos-config.yaml) using
      the kubeconfig file 'my-kube-config.yaml':

        $ {command} --kubeconfig 'my-kube-config.yaml'

      To generate a config named 'myconfg.yaml' the --kubeconfig file 'my-kube-config.yaml':

        $ {command} --kubeconfig 'my-kube-config.yaml' --output 'myconfg.yaml'
      """,
  }

  @staticmethod
  def Args(parser):
    kube_flags.GetKubeConfigFlag('Specifies the input kubeconfig '
                                 'file to access user cluster for '
                                 'login configuration data.',
                                 required=True).AddToParser(parser)
    flags.GetConfigOutputFileFlag().AddToParser(parser)
    flags.GetMergeFromFlag().AddToParser(parser)

  def Run(self, args):
    command_executor = anthoscli_backend.AnthosAuthWrapper()
    response = command_executor(
        command='create-login-config',
        kube_config=args.kubeconfig,
        output_file=args.output,
        merge_from=args.merge_from,
        show_exec_error=args.show_exec_error,
        env=anthoscli_backend.GetEnvArgsForCommand())
    return anthoscli_backend.LoginResponseHandler(response)
