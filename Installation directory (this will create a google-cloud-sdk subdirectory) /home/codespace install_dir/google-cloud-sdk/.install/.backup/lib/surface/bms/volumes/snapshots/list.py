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
"""'Bare Metal Solution snapshots list command."""

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
          List snapshots for a Bare Metal Solution boot volume.
        """,
    'EXAMPLES':
        """
          To list snapshots on boot volume ``my-boot-volume'' in region
          ``us-central1'', run:

            $ {command} --region=us-central1 --volume=my-boot-volume
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class List(six.with_metaclass(abc.ABCMeta, base.CacheCommand)):
  """List snapshots for a Bare Metal Solution boot volume."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    # Remove unsupported default List flags.
    flags.FILTER_FLAG_NO_SORTBY_DOC.AddToParser(parser)
    flags.LIMIT_FLAG_NO_SORTBY_DOC.AddToParser(parser)

    flags.AddVolumeArgToParser(
        parser,
        group_help_text='The Bare Metal Solution volume to list snapshots of.')

    # The default format picks out the components of the relative name: given
    # projects/myproject/locations/us-central1/volumes/my-volume/snapshots/my-snapshot
    # it takes -1 (my-snapshot), -3 (my-volume), -5 (us-central1), and
    # -7 (myproject)
    parser.display_info.AddFormat(
        'table(name.segment(-1):label=NAME,id:label=ID,'
        'name.segment(-5):label=REGION,'
        'name.segment(-3):label=VOLUME,description,createTime,type)')

  def Run(self, args):
    volume = args.CONCEPTS.volume.Parse()
    client = BmsClient()
    return client.ListSnapshotsForVolume(volume,
                                         limit=args.limit)

  def Epilog(self, resources_were_displayed):
    """Called after resources are displayed if the default format was used.

    Args:
      resources_were_displayed: True if resources were displayed.
    """
    if not resources_were_displayed:
      log.status.Print('Listed 0 items.')

List.detailed_help = DETAILED_HELP
