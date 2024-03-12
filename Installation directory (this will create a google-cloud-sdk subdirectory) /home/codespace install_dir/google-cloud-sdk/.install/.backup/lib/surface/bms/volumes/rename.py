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
"""Bare Metal Solution volume rename command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import log


DETAILED_HELP = {
    'DESCRIPTION':
        """
          Rename a Bare Metal Solution volume.
        """,
    'EXAMPLES':
        """
          To rename a volume ``my-volume'' to ``my-new-volume-name'' in region ``us-central1'', run:

          $ {command} my-volume --new-name=my-new-volume-name --region=us-central1 --project=bms-example-project
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Rename(base.UpdateCommand):
  """Rename a Bare Metal Solution volume."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddVolumeArgToParser(parser, positional=True)
    flags.AddNewNameArgToParser(parser, 'volume')

  def Run(self, args):
    client = BmsClient()
    old_name = args.CONCEPTS.volume.Parse()
    new_name = args.new_name
    res = client.RenameVolume(old_name, new_name)
    log.status.Print(
        'Renamed {} to {} successfully'.format(old_name.Name(), new_name))
    return res


Rename.detailed_help = DETAILED_HELP
