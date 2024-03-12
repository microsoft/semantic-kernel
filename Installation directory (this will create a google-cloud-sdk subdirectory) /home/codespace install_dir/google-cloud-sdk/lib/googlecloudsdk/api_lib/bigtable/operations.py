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
"""Bigtable operations API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties


def ModifyDescribeRequest(unused_operation_ref, args, req):
  """Check input and construct describe request if needed."""
  operation_name = args.operation
  # operation_string = operation_name
  project_id = properties.VALUES.core.project.Get()  # default project id

  if operation_name.startswith('operations/projects'):
    return req
  # Assuming that if the operation name is not complete, it's only missing
  # the operations/projects/{} prefix.
  operation_name_with_prefix = ('operations/projects/' +
                                project_id + '/' + operation_name)
  req.name = operation_name_with_prefix
  return req
