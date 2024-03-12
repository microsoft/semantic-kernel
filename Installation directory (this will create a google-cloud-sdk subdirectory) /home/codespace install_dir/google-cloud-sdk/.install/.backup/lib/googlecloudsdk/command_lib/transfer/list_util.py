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
"""Utils for transfer list commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.core import log

# Backend default.
_TRANSFER_LIST_PAGE_SIZE = 256


def add_common_list_flags(parser):
  """Inheriting from ListCommand adds flags transfer needs to modify."""
  parser.add_argument(
      '--limit',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      help='Return the first items from the API up to this limit.')
  parser.add_argument(
      '--page-size',
      type=arg_parsers.BoundedInt(1, sys.maxsize, unlimited=True),
      default=_TRANSFER_LIST_PAGE_SIZE,
      help='Retrieve batches of this many items from the API.')


def print_transfer_resources_iterator(resource_iterator,
                                      command_display_function, command_args):
  """Gcloud's built-in display logic has issues with enormous lists.

  Args:
    resource_iterator (iterable): Likely an instance of Apitools
      list_pager.YieldFromList but can also be a List.
    command_display_function (func): The self.Display function built into
      classes inheriting from base.Command.
    command_args (argparse.Namespace): The args object passed to self.Display
      and self.Run of commands inheriting from base.Command.
  """

  # Output may look something like:
  # NAME         STATUS
  # resource1    ENABLED
  # resource2    DISABLED
  # ...
  #
  # NAME         STATUS
  # resource257  DISABLED

  resource_list = []
  for resource in resource_iterator:
    resource_list.append(resource)
    if len(resource_list) >= _TRANSFER_LIST_PAGE_SIZE:
      log.status.Print()
      command_display_function(command_args, resource_list)
      resource_list = []

  if resource_list:
    log.status.Print()
    command_display_function(command_args, resource_list)

  # Prevents command base class from trying to handle custom format after.
  command_args.format = None
