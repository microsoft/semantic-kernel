#!/usr/bin/env python
# Copyright 2016 Google Inc. All Rights Reserved.
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

"""Implement base classes for hid package.

This module provides the base classes implemented by the
platform-specific modules.  It includes a base class for
all implementations built on interacting with file-like objects.
"""


class HidDevice(object):
  """Base class for all HID devices in this package."""

  @staticmethod
  def Enumerate():
    """Enumerates all the hid devices.

    This function enumerates all the hid device and provides metadata
    for helping the client select one.

    Returns:
      A list of dictionaries of metadata.  Each implementation is required
      to provide at least: vendor_id, product_id, product_string, usage,
      usage_page, and path.
    """
    pass

  def __init__(self, path):
    """Initialize the device at path."""
    pass

  def GetInReportDataLength(self):
    """Returns the max input report data length in bytes.

    Returns the max input report data length in bytes.  This excludes the
    report id.
    """
    pass

  def GetOutReportDataLength(self):
    """Returns the max output report data length in bytes.

    Returns the max output report data length in bytes.  This excludes the
    report id.
    """
    pass

  def Write(self, packet):
    """Writes packet to device.

    Writes the packet to the device.

    Args:
      packet: An array of integers to write to the device.  Excludes the report
      ID. Must be equal to GetOutReportLength().
    """
    pass

  def Read(self):
    """Reads packet from device.

    Reads the packet from the device.

    Returns:
      An array of integers read from the device.  Excludes the report ID.
      The length is equal to GetInReportDataLength().
    """
    pass


class DeviceDescriptor(object):
  """Descriptor for basic attributes of the device."""

  usage_page = None
  usage = None
  vendor_id = None
  product_id = None
  product_string = None
  path = None

  internal_max_in_report_len = 0
  internal_max_out_report_len = 0

  def ToPublicDict(self):
    out = {}
    for k, v in list(self.__dict__.items()):
      if not k.startswith('internal_'):
        out[k] = v
    return out
