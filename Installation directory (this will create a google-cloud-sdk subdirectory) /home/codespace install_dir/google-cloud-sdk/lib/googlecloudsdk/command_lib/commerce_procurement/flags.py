# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Provides common arguments for the Commerce Procurement command surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddOrderAllocationEntryArgs(parser):
  """Register an arg group for Order Allocation entry flags.

  Args:
    parser: A group where all allocation entry arguments are registered.

  Returns:
    No return value.
  """
  resource_value_group = parser.add_mutually_exclusive_group(required=True)
  resource_value_group.add_argument(
      '--int64-resource-value', type=int, help='Resource value in int64 type.')
  resource_value_group.add_argument(
      '--double-resource-value',
      type=float,
      help='Resource value in double type.')
  resource_value_group.add_argument(
      '--string-resource-value', help='Resource value in string type.')

  parser.add_argument(
      '--targets',
      required=True,
      action='append',
      help='Targets of the order allocation. Only projects are allowed now.')
