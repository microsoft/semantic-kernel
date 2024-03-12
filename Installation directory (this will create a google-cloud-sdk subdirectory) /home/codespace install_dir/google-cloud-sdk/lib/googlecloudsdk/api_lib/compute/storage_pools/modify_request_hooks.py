# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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
"""Modify request hooks, specifically for storage-pool related ones."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def add_name_to_payload(resource_ref, _, request_msg):
  """Modify the request message, carrying resource name into it.

  Args:
    resource_ref: the resource reference.
    request_msg: the request message constructed by the framework
  Returns:
    the modified request message.
  """
  request_msg.storagePool.name = resource_ref.storagePool
  return request_msg
