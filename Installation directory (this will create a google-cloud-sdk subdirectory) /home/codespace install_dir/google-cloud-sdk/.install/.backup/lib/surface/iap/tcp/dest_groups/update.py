# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Create IAP TCP Destination Group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Update(base.Command):
  """Update the IAP TCP Destination Group resource."""
  detailed_help = {
      "EXAMPLES":
          """\
          To update a DestGroup with name ``GROUP_NAME'', in region ``REGION''
          with ip ranges ``CIDR1'', ``CIDR2'' in the current project run:

          $ {command} DEST_GROUP_NAME --region=REGION --ip-range-list=CIDR1,CIDR2

          To update a DestGroup with name ``GROUP_NAME'', in region ``REGION''
          with fqdns ``FQDN1'', ``FQDN2'' in the current project run:

          $ {command} DEST_GROUP_NAME --region=REGION --fqdn-list=FQDN1,FQDN2

          To update a DestGroup with name ``GROUP_NAME'', in region ``REGION''
          with fqdns ``FQDN1'', ``FQDN2'' and ip ranges ``CIDR1'', ``CIDR2'' in
          the project  ``PROJECT_ID'' run:

          $ {command} DEST_GROUP_NAME --region=REGION --fqdn-list=FQDN1,FQDN2
          --ip-range-list=CIDR1,CIDR2 --project=PROJECT_ID

          To clear the fqdn list in a DestGroup with name ``GROUP_NAME'', in
          region ``REGION'' in the current project run:

          $ {command} DEST_GROUP_NAME --region=REGION --fqdn-list=""

          To clear the ip range list in a DestGroup with name ``GROUP_NAME'', in
          region ``REGION'' in the current project run:

          $ {command} DEST_GROUP_NAME --region=REGION --ip-range-list=""
          """,
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddDestGroupArgs(parser)
    iap_util.AddDestGroupUpdateIpAndFqdnArgs(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter
    Raises:
      ValueError: If both ip-range-list and fqdn-list are not provided
    """
    iap_setting_ref = iap_util.ParseIapDestGroupResource(
        self.ReleaseTrack(), args)

    update_mask = ""
    if args.IsSpecified("ip_range_list") and args.IsSpecified("fqdn_list"):
      update_mask = "*"
    elif args.IsSpecified("ip_range_list"):
      update_mask = "cidrs"
    elif args.IsSpecified("fqdn_list"):
      update_mask = "fqdns"
    else:
      raise ValueError(
          "The flags --fqdn-list or --ip-range-list must be provided.")
    return iap_setting_ref.Update(args.ip_range_list, args.fqdn_list,
                                  update_mask)
