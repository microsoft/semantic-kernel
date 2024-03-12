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

"""Refine server response for display."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.dataproc import util


class DisplayHelper(util.Bunch):
  """Refine server response for display."""

  def __init__(self, job):
    super(DisplayHelper, self).__init__(encoding.MessageToDict(job))
    self._job = job

  @property
  def jobType(self):
    return self.getTruncatedFieldNameBySuffix('Job')

  @property
  def batchType(self):
    return self.getTruncatedFieldNameBySuffix('Batch')

  @property
  def sessionType(self):
    return self.getTruncatedFieldNameBySuffix('Session')

  def getTruncatedFieldNameBySuffix(self, suffix):
    """Get a field name by suffix and truncate it.

    The one_of fields in server response have their type name as field key.
    One can retrieve the name of those fields by iterating through all the
    fields.

    Args:
      suffix: the suffix to match.

    Returns:
      The first matched truncated field name.

    Raises:
      AttributeError: Error occur when there is no match for the suffix.

    Usage Example:
      In server response:
      {
        ...
        "sparkJob":{
          ...
        }
        ...
      }
      type = helper.getTruncatedFieldNameBySuffix('Job')
    """
    for field in [field.name for field in self._job.all_fields()]:
      if field.endswith(suffix):
        token, _, _ = field.rpartition(suffix)
        if self._job.get_assigned_value(field):
          return token
    raise AttributeError('Response has no field with {} as suffix.'
                         .format(suffix))
