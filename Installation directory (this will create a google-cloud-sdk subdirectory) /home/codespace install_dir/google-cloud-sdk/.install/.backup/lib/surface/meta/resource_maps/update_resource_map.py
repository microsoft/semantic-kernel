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
"""Command used for updating resource maps."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

from googlecloudsdk.command_lib.util.resource_map import resource_map_update_util
from googlecloudsdk.command_lib.util.resource_map.declarative import declarative_map_update_util


class UpdateResourceMap(base.Command):
  """Command used for updating resource maps."""

  @staticmethod
  def Args(parser):
    group = parser.add_group(mutex=True)
    group.add_argument(
        '--all', action='store_true', help='Update all resource maps.')
    individual_maps_group = group.add_group()
    individual_maps_group.add_argument(
        '--declarative',
        action='store_true',
        help='Update the declarative resource map.')
    individual_maps_group.add_argument(
        '--base', action='store_true', help='Update the base resource map.')

  def Run(self, args):
    if args.base or args.all:
      resource_map_update_util.update()
    if args.declarative or args.all:
      declarative_map_update_util.update()
