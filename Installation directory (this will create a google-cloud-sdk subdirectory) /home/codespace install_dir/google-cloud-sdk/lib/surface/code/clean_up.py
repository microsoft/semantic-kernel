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
"""Command for cleaning up the kubernetes cluster."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.code import kubernetes


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class CleanUp(base.Command):
  """Delete the local development environment."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Delete the local development environment.

          Use this command to clean up a development environment. This command
          many also be used remove any artifacts of developments environments
          that did not successfully start up.
          """,
      'EXAMPLES':
          """\
          $ {command}

          To clean up a specific profile:

          $ {command} --minikube-profile=<profile name>
          """
  }

  @classmethod
  def Args(cls, parser):
    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument('--minikube-profile', help='Minikube profile.')

  def Run(self, args):
    kubernetes.DeleteMinikube(args.minikube_profile or
                              kubernetes.DEFAULT_CLUSTER_NAME)
