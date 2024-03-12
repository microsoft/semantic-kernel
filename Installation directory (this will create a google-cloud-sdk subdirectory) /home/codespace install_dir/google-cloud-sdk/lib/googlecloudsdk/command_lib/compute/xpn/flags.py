# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags for commands dealing with cross-project networking (XPN)."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


def GetProjectIdArgument(verb):
  """Return the PROJECT_ID argument for XPN commands."""
  arg = base.Argument(
      'project', metavar='PROJECT_ID',
      help='ID for the project to {verb}'.format(verb=verb))
  return arg


def GetHostProjectFlag(verb):
  """Return the --host-project flag for XPN commands."""
  arg = base.Argument('--host-project', required=True,
                      help='The XPN host to {verb}'.format(verb=verb))
  return arg
