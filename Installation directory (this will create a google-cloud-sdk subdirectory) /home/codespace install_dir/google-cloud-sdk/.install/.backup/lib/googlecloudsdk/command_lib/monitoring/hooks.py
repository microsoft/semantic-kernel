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

"""Hooks for YAML commands for Stackdrive Monitoring Surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def AddOrderByToListRequest(unused_ref, args, list_request):
  del unused_ref

  if args.sort_by:
    # Stackdriver API uses '-' instead of '~'.
    sort_by = [field.replace('~', '-') for field in args.sort_by]
    list_request.orderBy = ','.join(sort_by)
  return list_request


def _AddTypeToFilter(filter_expr, channel_type):
  type_filter = 'type="{}"'.format(channel_type)
  if not filter_expr:
    return type_filter
  return '{0} AND ({1})'.format(type_filter, filter_expr)


def ModifyListNotificationChannelsRequest(project_ref, args, list_request):
  """Modifies the list request by adding a filter defined by the type flag."""
  del project_ref
  filter_expr = args.filter
  if args.type:
    filter_expr = _AddTypeToFilter(filter_expr, args.type)

  list_request.filter = filter_expr
  return list_request
