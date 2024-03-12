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
"""Utilities for `gcloud network-connectivity`."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse


# Table format for spokes list
LIST_FORMAT = """
    table(
      name.basename(),
      name.segment(3):label=LOCATION,
      hub.basename(),
      format(
        "{0}{1}{2}{3}",
        linkedVpnTunnels.yesno(yes="VPN tunnel", no=""),
        linkedInterconnectAttachments.yesno(yes="VLAN attachment", no=""),
        linkedRouterApplianceInstances.yesno(yes="Router appliance", no=""),
        linkedVpcNetwork.yesno(yes="VPC network", no="")
      ):label=TYPE,
      firstof(linkedVpnTunnels.uris, linkedInterconnectAttachments.uris, linkedRouterApplianceInstances.instances, linkedVpcNetwork).len():label="RESOURCE COUNT",
      format(
        "{0}{1}",
        linkedVpcNetwork.yesno(yes="N/A", no=""),
        firstof(linkedVpnTunnels.siteToSiteDataTransfer, linkedInterconnectAttachments.siteToSiteDataTransfer, linkedRouterApplianceInstances.siteToSiteDataTransfer).yesno(yes="On", no="")
      ).yesno(no="Off"):label="DATA TRANSFER",
      description
    )
"""

LIST_SPOKES_FORMAT = """
    table(
      name.basename(),
      name.segment(1):label=PROJECT,
      name.segment(3):label=LOCATION,
      spokeType:label=TYPE,
      state,
      reasons.code.list():label="STATE REASON",
      format(
        "{0}{1}",
        linkedVpcNetwork.yesno(yes="N/A", no=""),
        firstof(linkedVpnTunnels.siteToSiteDataTransfer, linkedInterconnectAttachments.siteToSiteDataTransfer, linkedRouterApplianceInstances.siteToSiteDataTransfer).yesno(yes="On", no="")
      ).yesno(no="Off").if(view=detailed):label="DATA TRANSFER",
      description.if(view=detailed)
    )
"""


def AppendLocationsGlobalToParent(unused_ref, unused_args, request):
  """Add locations/global to parent path."""

  request.parent += "/locations/global"
  return request


def SetGlobalLocation():
  """Set default location to global."""
  return "global"


def ClearOverlaps(unused_ref, args, patch_request):
  """Handles clear_overlaps flag."""

  if args.IsSpecified("clear_overlaps"):
    update_mask = patch_request.updateMask
    if not update_mask:
      patch_request.updateMask = "overlaps"
    else:
      patch_request.updateMask = update_mask + "," + "overlaps"
  return patch_request


class StoreGlobalAction(argparse._StoreConstAction):
  # pylint: disable=protected-access
  # pylint: disable=redefined-builtin
  """Return "global" if the --global argument is used."""

  def __init__(self,
               option_strings,
               dest,
               default="",
               required=False,
               help=None):
    super(StoreGlobalAction, self).__init__(
        option_strings=option_strings,
        dest=dest,
        const="global",
        default=default,
        required=required,
        help=help)
