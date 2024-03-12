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

"""Utils for interacting with PKIX tools."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container.binauthz import apis
from googlecloudsdk.command_lib.util.apis import arg_utils


def GetAlgorithmMapper(api_version=None):
  messages = apis.GetMessagesModule(api_version)
  algorithm_enum = messages.PkixPublicKey.SignatureAlgorithmValueValuesEnum
  return arg_utils.ChoiceEnumMapper(
      'algorithm_enum',
      algorithm_enum,
      include_filter=lambda name: 'UNSPECIFIED' not in name)
