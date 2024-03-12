# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Utilities for edge-cloud container location commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from apitools.base.py import encoding
from googlecloudsdk.core import log


def PrintWarning(response, _):
  """Print the warning in last response.

  Args:
    response: The last response of series api call
    _: Represents unused_args

  Returns:
    Nested response, normally should be the resource of a LRO.
  """
  json_obj = encoding.MessageToDict(response)
  if json_obj['metadata'].get('warnings'):
    for warning in json_obj['metadata']['warnings']:
      log.warning(warning)
  if 'response' in json_obj.keys():
    clusters = json_obj['response']
    clusters.pop('@type')
    return clusters
  else:
    return response
