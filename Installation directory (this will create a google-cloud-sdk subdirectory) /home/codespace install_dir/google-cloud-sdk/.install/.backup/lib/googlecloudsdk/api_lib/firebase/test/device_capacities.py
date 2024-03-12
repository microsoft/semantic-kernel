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

"""Common code for 'gcloud firebase test * list-device-capacities' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import collections

CapacityEntry = collections.namedtuple('CapacityEntry',
                                       ['model', 'name', 'version', 'capacity'])

DEVICE_CAPACITY_TABLE_FORMAT = """
        table[box](
          model:label=MODEL_ID,
          name:label=MODEL_NAME,
          version:label=OS_VERSION_ID,
          capacity.color(red=None,yellow=Low,green=High):label=DEVICE_CAPACITY
        )
    """


class DeviceCapacities(object):
  """Common code for 'gcloud firebase test * list-device-capacities' commands."""

  _capacity_messages_cache = None

  @property
  def capacity_messages(self):
    """A map of enum to user-friendly message."""

    if self._capacity_messages_cache is None:
      device_capacity_enum_android = self.context[
          'testing_messages'].PerAndroidVersionInfo.DeviceCapacityValueValuesEnum
      # Note: PerIosVersionInfo.DeviceCapacityValueValuesEnum is the same enum
      #  in the proto, but in gcloud client API it's an unique object
      device_capacity_enum_ios = self.context[
          'testing_messages'].PerIosVersionInfo.DeviceCapacityValueValuesEnum
      self._capacity_messages_cache = {
          device_capacity_enum_android.DEVICE_CAPACITY_UNSPECIFIED: 'None',
          device_capacity_enum_android.DEVICE_CAPACITY_HIGH: 'High',
          device_capacity_enum_android.DEVICE_CAPACITY_MEDIUM: 'Medium',
          device_capacity_enum_android.DEVICE_CAPACITY_LOW: 'Low',
          device_capacity_enum_android.DEVICE_CAPACITY_NONE: 'None',
          device_capacity_enum_ios.DEVICE_CAPACITY_UNSPECIFIED: 'None',
          device_capacity_enum_ios.DEVICE_CAPACITY_HIGH: 'High',
          device_capacity_enum_ios.DEVICE_CAPACITY_MEDIUM: 'Medium',
          device_capacity_enum_ios.DEVICE_CAPACITY_LOW: 'Low',
          device_capacity_enum_ios.DEVICE_CAPACITY_NONE: 'None',
      }

    return self._capacity_messages_cache

  def get_capacity_data(self, catalog):
    """Generate a list of devices/OS versions & corresponding capacity info.

    Args:
      catalog: Android or iOS catalog

    Returns:
      The list of device models, versions, and capacity info we want to have
      printed later. Obsolete (unsupported) devices, versions, and entries
      missing capacity info are filtered out.
    """

    capacity_data = []
    for model in catalog.models:
      for version_info in model.perVersionInfo:
        if version_info.versionId not in model.supportedVersionIds:
          continue
        capacity_data.append(
            CapacityEntry(
                model=model.id,
                name=model.name,
                version=version_info.versionId,
                capacity=self.capacity_messages[version_info.deviceCapacity]))

    return capacity_data
