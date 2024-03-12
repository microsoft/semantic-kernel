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
"""Util for dynamically setting the best performing app configuration."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import multiprocessing

from googlecloudsdk.core import log
from googlecloudsdk.core import properties

COMPONENT_SIZE = '5Mi'

DEFAULT_TO_PARALLELISM = True

MULTI_FILE_LOW_CPU_PROCESS_COUNT = 2
MULTI_FILE_HIGH_CPU_PROCESS_COUNT = 16
MULTI_FILE_LOW_CPU_THREAD_COUNT = 10
MULTI_FILE_HIGH_CPU_THREAD_COUNT = 4
MULTI_FILE_LOW_CPU_SLICED_OBJECT_DOWNLOAD_THRESHOLD = '50Mi'
MULTI_FILE_HIGH_CPU_SLICED_OBJECT_DOWNLOAD_THRESHOLD = '10Mi'
MULTI_FILE_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS = 10

SINGLE_FILE_LOW_CPU_PROCESS_COUNT = 4
SINGLE_FILE_HIGH_CPU_PROCESS_COUNT = 8
SINGLE_FILE_THREAD_COUNT = 2
SINGLE_FILE_SLICED_OBJECT_DOWNLOAD_THRESHOLD = '50Mi'
SINGLE_FILE_LOW_CPU_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS = 8
SINGLE_FILE_HIGH_CPU_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS = 16


def _set_if_not_user_set(property_name, value):
  """Sets property to opitmized value if user did not set custom one."""
  storage_property = getattr(properties.VALUES.storage, property_name)
  if storage_property.Get() is None:
    storage_property.Set(value)


def detect_and_set_best_config(is_estimated_multi_file_workload):
  """Determines best app config based on system and workload."""
  if is_estimated_multi_file_workload:
    _set_if_not_user_set('sliced_object_download_component_size',
                         COMPONENT_SIZE)
    _set_if_not_user_set('sliced_object_download_max_components',
                         MULTI_FILE_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS)
    if multiprocessing.cpu_count() < 4:
      log.info('Using low CPU count, multi-file workload config.')
      _set_if_not_user_set('process_count', MULTI_FILE_LOW_CPU_PROCESS_COUNT)
      _set_if_not_user_set('thread_count', MULTI_FILE_LOW_CPU_THREAD_COUNT)
      _set_if_not_user_set('sliced_object_download_threshold',
                           MULTI_FILE_LOW_CPU_SLICED_OBJECT_DOWNLOAD_THRESHOLD)
    else:
      log.info('Using high CPU count, multi-file workload config.')
      _set_if_not_user_set('process_count', MULTI_FILE_HIGH_CPU_PROCESS_COUNT)
      _set_if_not_user_set('thread_count', MULTI_FILE_HIGH_CPU_THREAD_COUNT)
      _set_if_not_user_set(
          'sliced_object_download_threshold',
          MULTI_FILE_HIGH_CPU_SLICED_OBJECT_DOWNLOAD_THRESHOLD)
  else:
    _set_if_not_user_set('sliced_object_download_threshold',
                         SINGLE_FILE_SLICED_OBJECT_DOWNLOAD_THRESHOLD)
    _set_if_not_user_set('sliced_object_download_component_size',
                         COMPONENT_SIZE)
    if multiprocessing.cpu_count() < 8:
      log.info('Using low CPU count, single-file workload config.')
      _set_if_not_user_set('process_count', SINGLE_FILE_LOW_CPU_PROCESS_COUNT)
      _set_if_not_user_set('thread_count', SINGLE_FILE_THREAD_COUNT)
      _set_if_not_user_set(
          'sliced_object_download_max_components',
          SINGLE_FILE_LOW_CPU_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS)
    else:
      log.info('Using high CPU count, single-file workload config.')
      _set_if_not_user_set('process_count', SINGLE_FILE_HIGH_CPU_PROCESS_COUNT)
      _set_if_not_user_set('thread_count', SINGLE_FILE_THREAD_COUNT)
      _set_if_not_user_set(
          'sliced_object_download_max_components',
          SINGLE_FILE_HIGH_CPU_SLICED_OBJECT_DOWNLOAD_MAX_COMPONENTS)
