# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Command for spanner SSD caches update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.spanner import ssd_caches
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.util.args import labels_util


class Update(base.Command):
  """Update a Cloud Spanner SSD cache."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
        To update the size of a Cloud Spanner SSD cache to 2048 GiB, run:

          $ {command} my-cache-id --config=my-config-id --size-gib=2048

        To update display name of a Cloud Spanner SSD cache, run:

          $ {command} my-cache-id --config=my-config-id --display-name=new-display-name

        To modify the SSD Cache by adding label 'k0', with value 'value1' and label 'k1' with value 'value2' and removing labels with key 'k3', run:

         $ {command} my-cache-id --config=my-config-id --update-labels=k0=value1,k1=value2 --remove-labels=k3

        To clear all labels of a Cloud Spanner SSD cache, run:

          $ {command} my-cache-id --config=my-config-id --clear-labels

        To remove existing labels of a Cloud Spanner SSD cache, run:

          $ {command} my-cache-id --config=my-config-id --remove-labels=k0,k1
        """),
  }

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.SsdCache(positional=True, required=True, hidden=False).AddToParser(
        parser
    )
    flags.Config().AddToParser(parser)

    update_group = parser.add_group(
        required=True,
        help='SSD Cache attributes to be updated. At least one is required.',
    )

    update_group.add_argument(
        '--size-gib', type=int, help='The size of this SSD Cache in GiB.'
    )

    update_group.add_argument(
        '--display-name',
        help='The name of this SSD Cache as it appears in UIs.',
    )

    labels_util.AddUpdateLabelsFlags(update_group)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      SSD Cache update response.
    """
    return ssd_caches.Patch(args)
