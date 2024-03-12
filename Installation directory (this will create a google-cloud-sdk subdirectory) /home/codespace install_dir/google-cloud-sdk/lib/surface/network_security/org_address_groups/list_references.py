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
"""ListReference command for the AddressGroup under Organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

from googlecloudsdk.command_lib.network_security import flags
from googlecloudsdk.command_lib.network_security import util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class ListReferences(base.ListCommand):
  """Lists References of an Organization Address Group."""
  _release_track = base.ReleaseTrack.GA

  detailed_help = {
      'EXAMPLES':
          """\
        To list References of address group named my-address-group.

          $ {command} my-address-group
        """
  }

  @classmethod
  def Args(cls, parser):
    flags.AddOrganizationAddressGroupToParser(cls._release_track, parser)
    flags.AddListReferencesFormat(parser)

  def Run(self, args):
    return util.ListOrganizationAddressGroupReferences(self._release_track,
                                                       args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class ListReferencesBeta(ListReferences):
  """Lists References of an Organization Address Group."""
  _release_track = base.ReleaseTrack.BETA


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class ListReferencesAlpha(ListReferences):
  """Lists References of an Organization Address Group."""
  _release_track = base.ReleaseTrack.ALPHA
