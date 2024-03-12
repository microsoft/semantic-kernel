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
"""recommender API locations list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import locations
from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'EXAMPLES': """
          Lists locations.

            $ {command}
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
@base.Hidden
class List(base.ListCommand):
  r"""List locations operations.

  This command lists all available locations.
  """

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command.
    """
    parser.add_argument('--organization',
                        metavar='ORGANIZATION', help='Organization ID')
    parser.add_argument('--folder', metavar='FOLDER', help='Folder ID')
    parser.add_argument('--billing-account',
                        metavar='BILLING_ACCOUNT', help='Billing Account ID')
    parser.add_argument('--project', metavar='PROJECT', help='Project ID')
    parser.display_info.AddFormat("""
        table(
          name.basename(): label=LOCATIONS
        )
    """)

  def Run(self, args):
    """Run 'gcloud recommender recommenders list'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The list of recommender types for this project.
    """
    client = locations.CreateClient(self.ReleaseTrack())
    return client.List(
        args.page_size,
        project=args.project,
        organization=args.organization,
        folder=args.folder,
        billing_account=args.billing_account,
    )
