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
"""This module holds exceptions raised by Bare Metal Solution commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import exceptions


class NoConfigurationChangeError(exceptions.Error):
  """No configuration changes were requested."""


class MissingPropertyError(exceptions.Error):
  """Indicates a missing property in an ArgDict flag."""

  def __init__(self, flag_name, property_name):
    message = 'Flag [--{}] is missing the required property [{}]'.format(
        flag_name, property_name)
    super(MissingPropertyError, self).__init__(message)
