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
"""Hooks for declarative commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def SetDefaultPageSizeRequestHook(default_page_size):
  """Create a modify_request_hook that applies default_page_size to args.

  Args:
    default_page_size: The page size to use when not specified by the user.

  Returns:
    A modify_request_hook that updates `args.page_size` when not set by user.
  """
  def Hook(unused_ref, args, request):
    if not args.page_size:
      args.page_size = int(default_page_size)
    return request
  return Hook
