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
"""Utilities for Anthos on VMware errors."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class MissingClusterField(exceptions.Error):
  """Class for errors by missing cluster fields."""

  def __init__(self, cluster_id, field, extra_message=None):
    message = 'Cluster {} is missing {}.'.format(cluster_id, field)
    if extra_message:
      message += ' ' + extra_message
    super(MissingClusterField, self).__init__(message)


class UnsupportedClusterVersion(exceptions.Error):
  """Class for errors by unsupported cluster versions."""
