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
"""Shared messages for anthos surface."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

MISSING_BINARY = ('Could not locate anthos executable [{binary}]'
                  ' on the system PATH. '
                  'Please ensure gcloud anthos component is properly '
                  'installed. '
                  'See https://cloud.google.com/sdk/docs/components for '
                  'more details.')

MISSING_AUTH_BINARY = ('Could not locate anthos auth executable [{binary}]'
                       ' on the system PATH. '
                       'Please ensure gcloud anthos-auth component is properly '
                       'installed. '
                       'See https://cloud.google.com/sdk/docs/components for '
                       'more details.')

LOGIN_CONFIG_MESSAGE = 'Configuring Anthos authentication '
LOGIN_CONFIG_SUCCESS_MESSAGE = LOGIN_CONFIG_MESSAGE + 'success.'
LOGIN_CONFIG_FAILED_MESSAGE = LOGIN_CONFIG_MESSAGE + 'failed\n {}'
