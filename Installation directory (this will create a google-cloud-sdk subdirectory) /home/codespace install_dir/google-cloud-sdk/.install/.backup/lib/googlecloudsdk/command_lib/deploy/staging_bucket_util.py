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
"""Support library to handle the staging bucket."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import six


def GetDefaultStagingBucket(pipeline_uuid):
  """Returns the default source staging bucket."""
  if not pipeline_uuid:
    raise ValueError(
        'Expected a value for pipeline uid but the string is either empty or "None"'
    )
  uid_str = six.text_type(pipeline_uuid)
  bucket_name = uid_str + '_clouddeploy'
  if len(bucket_name) > 63:
    raise ValueError(
        'The length of the bucket id: {} must not exceed 63 characters'.format(
            bucket_name))
  return bucket_name
