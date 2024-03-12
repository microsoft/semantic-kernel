# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the compute reservation commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.compute import completers as compute_completers
from googlecloudsdk.command_lib.compute import flags as compute_flags


class ZoneReservationsCompleter(compute_completers.ListCommandCompleter):

  def __init__(self, **kwargs):
    super(ZoneReservationsCompleter, self).__init__(
        collection='compute.reservations',
        list_command='alpha compute reservations list --uri',
        **kwargs)


def GetReservationResourceArg(positional=True):
  if positional:
    name = 'reservation'
  else:
    name = '--reservation'

  return compute_flags.ResourceArgument(
      name=name,
      resource_name='reservation',
      completer=ZoneReservationsCompleter,
      plural=False,
      required=True,
      zonal_collection='compute.reservations',
      zone_explanation=compute_flags.ZONE_PROPERTY_EXPLANATION)
