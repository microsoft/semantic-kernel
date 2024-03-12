# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud genomics operations describe.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.genomics import genomics_client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.genomics import flags


class Describe(base.DescribeCommand):
  """Returns details about an operation.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddName(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace, All the arguments that were provided to this
        command invocation.

    Returns:
      a Operation message
    """
    client, resource = genomics_client.CreateFromName(args.name)
    return client.GetOperation(resource)
