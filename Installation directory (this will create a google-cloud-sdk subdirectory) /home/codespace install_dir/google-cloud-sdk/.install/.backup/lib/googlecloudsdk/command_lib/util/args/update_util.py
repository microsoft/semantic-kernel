# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Utilities for creating/parsing arguments for update commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.calliope import base


class UpdateResult(object):
  """Result type for applying updates.

  Attributes:
    needs_update: bool, whether the args require any changes to the existing
      resource.
    value: the value to put
  """

  def __init__(self, needs_update, value):
    self.needs_update = needs_update
    self.value = value

  @classmethod
  def MakeWithUpdate(cls, value):
    return cls(True, value)

  @classmethod
  def MakeNoUpdate(cls):
    return cls(False, None)


def AddClearableField(parser, arg_name, property_name, resource, full_help):
  """Add arguments corresponding to a field that can be cleared."""
  args = [
      base.Argument(
          '--{}'.format(arg_name),
          help='Set the {} for the {}.'.format(property_name, resource)),
      base.Argument(
          '--clear-{}'.format(arg_name),
          help='Clear the {} from the {}.'.format(property_name, resource),
          action='store_true')
  ]
  group = parser.add_mutually_exclusive_group(help=full_help)
  for arg in args:
    arg.AddToParser(group)


def ParseClearableField(args, arg_name):
  clear = getattr(args, 'clear_' + arg_name)
  set_ = getattr(args, arg_name, None)
  if clear:
    return UpdateResult.MakeWithUpdate(None)
  elif set_:
    return UpdateResult.MakeWithUpdate(set_)
  else:
    return UpdateResult.MakeNoUpdate()
