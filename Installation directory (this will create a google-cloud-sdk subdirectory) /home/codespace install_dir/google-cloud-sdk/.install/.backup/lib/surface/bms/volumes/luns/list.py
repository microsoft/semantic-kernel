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
"""'Bare Metal Solution logical unit numbers (LUNs) list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import log
import six

DETAILED_HELP = {
    'DESCRIPTION':
        """
          List Bare Metal Solution logical unit numbers (LUNs) for a volume.
        """,
    'EXAMPLES':
        """
          To list all LUNs on volume ``my-volume'' in region ``us-central1'',
          run:

            $ {command} --region=us-central1 --volume=my-volume
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(six.with_metaclass(abc.ABCMeta, base.CacheCommand)):
  """List Bare Metal Solution LUNs in a project."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Remove unsupported default List flags.
    flags.FILTER_FLAG_NO_SORTBY_DOC.AddToParser(parser)
    flags.LIMIT_FLAG_NO_SORTBY_DOC.AddToParser(parser)
    flags.AddVolumeArgToParser(parser)

    # The default format picks out the components of the relative name: given
    # projects/myproject/locations/us-central1/volumes/my-volume/snapshots/my-snapshot
    # it takes -1 (my-snapshot), -3 (my-volume), -5 (us-central1), and
    # -7 (myproject)
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,id:label=ID,'
        'name.segment(-5):label=REGION,'
        'name.segment(-3):label=VOLUME,sizeGb,state)')

  def Run(self, args):
    volume = args.CONCEPTS.volume.Parse()
    client = BmsClient()
    return client.ListLUNsForVolume(volume,
                                    limit=args.limit)

  def Epilog(self, resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      resources_were_displayed: True if resources were displayed.
    """
    if not resources_were_displayed:
      log.status.Print('Listed 0 items.')

List.detailed_help = DETAILED_HELP
