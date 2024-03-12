# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""services operations describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import peering
from googlecloudsdk.api_lib.services import services_util
from googlecloudsdk.calliope import base

_NAME_HELP = """The name of operation to describe"""


class Describe(base.DescribeCommand):
  # pylint: disable=line-too-long
  """Describes an operation resource for a given operation name.

     This command will return information about an operation given the name
     of that operation.

     ## EXAMPLES
     To describe an operation resource named
     `operations/abc`, run:

       $ {command} --name=operations/abc
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    parser.add_argument(
        '--name', metavar='OPERATION_NAME', required=True, help=_NAME_HELP)

  def Run(self, args):
    """Run 'services operations describe'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      Nothing.
    """
    op = peering.GetOperation(args.name)
    services_util.PrintOperation(op)
