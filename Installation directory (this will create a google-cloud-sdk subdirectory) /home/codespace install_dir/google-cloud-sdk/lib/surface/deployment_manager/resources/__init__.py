# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Deployment Manager resources sub-group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.deployment_manager import exceptions
from googlecloudsdk.calliope import base


class Resources(base.Group):
  """Commands for Deployment Manager resources.

  Commands to list and examine resources within a deployment.
  """

  detailed_help = {
      'EXAMPLES': """\
          To view all details about a resource, run:

            $ {command} describe my-resource --deployment my-deployment

          To see the list of all resources in a deployment, run:

            $ {command} list --deployment my-deployment
          """,
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument('--deployment', help='Deployment name')

  def Filter(self, unused_tool_context, args):
    if not args.deployment:
      raise exceptions.ArgumentError('argument --deployment is required')
