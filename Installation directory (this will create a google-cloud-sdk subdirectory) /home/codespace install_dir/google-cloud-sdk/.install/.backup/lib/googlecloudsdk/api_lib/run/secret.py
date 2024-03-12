# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Wraps a k8s Secret message, making fields more convenient."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import k8s_object


class Secret(k8s_object.KubernetesObject):
  """A kubernetes Secret resource."""

  API_CATEGORY = None  # Core resources do not have an api category
  KIND = 'Secret'

  @property
  def string_data(self):
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._m.stringData.additionalProperties,
        self._messages.Secret.StringDataValue.AdditionalProperty,
        key_field='key',
        value_field='value',
    )

  @property
  def data(self):
    return k8s_object.KeyValueListAsDictionaryWrapper(
        self._m.data.additionalProperties,
        self._messages.Secret.DataValue.AdditionalProperty,
        key_field='key',
        value_field='value',
    )
