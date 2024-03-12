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

"""Shared flags definitions for muteconfigs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

MUTE_CONFIG_FLAG = base.Argument(
    "mute_config",
    help="ID of the mute config or the full resource name of the mute config."
    )

DESCRIPTION_FLAG = base.Argument(
    "--description",
    required=False,
    help="The text that will be used to describe a mute configuration."
    )

DISPLAY_NAME_FLAG = base.Argument(
    "--display-name",
    required=False,
    help="""The text that will be used to represent a mute configuration display name."""
    )

FILTER_FLAG = base.Argument(
    "--filter",
    required=False,
    help="""The filter string which will applied to findings muted by a mute configuration."""
    )


def AddParentGroup(parser, required=False):
  """Adds a parent group to the parser."""
  parent_group = parser.add_group(mutex=True, required=required)
  parent_group.add_argument(
      "--organization",
      help="""Organization where the mute config resides. Formatted as ``organizations/123'' or just ``123''.""",
  )

  parent_group.add_argument(
      "--folder",
      help="""Folder where the mute config resides. Formatted as ``folders/456'' or just ``456''.""",
  )
  parent_group.add_argument(
      "--project",
      help="""Project (id or number) where the mute config resides. Formatted as ``projects/789'' or just ``789''.""",
  )
  return parser

