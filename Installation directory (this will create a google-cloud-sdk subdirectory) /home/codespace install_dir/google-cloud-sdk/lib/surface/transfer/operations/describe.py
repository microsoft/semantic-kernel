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
"""Command to get details on a transfer operation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import operations_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core.resource import resource_printer


class Describe(base.Command):
  """Get configuration and latest transfer operation details."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Get details about a specific transfer operation.
      """,
      'EXAMPLES':
          """\
      To describe an operation, run:

        $ {command} OPERATION-NAME
      """,
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'name', help='The name of the operation you want to describe.')

  def Display(self, args, resources):
    del args  # Unsued.
    resource_printer.Print(resources, 'json')

  def Run(self, args):
    return operations_util.api_get(args.name)
