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

"""Tests for pyu2f.hid.macos."""

import ctypes
import sys
import mock

from pyu2f import errors
from pyu2f.hid import macos


if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


def init_mock_iokit(mock_iokit):
  # Device open should always return 0 (success)
  mock_iokit.IOHIDDeviceOpen = mock.Mock(return_value=0)
  mock_iokit.IOHIDDeviceSetReport = mock.Mock(return_value=0)
  mock_iokit.IOHIDDeviceCreate = mock.Mock(return_value='handle')


def init_mock_cf(mock_cf):
  mock_cf.CFGetTypeID = mock.Mock(return_value=123)
  mock_cf.CFNumberGetTypeID = mock.Mock(return_value=123)
  mock_cf.CFStringGetTypeID = mock.Mock(return_value=123)


def init_mock_get_int_property(mock_get_int_property):
  mock_get_int_property.return_value = 64


class MacOsTest(unittest.TestCase):

  @mock.patch.object(macos.threading, 'Thread')
  @mock.patch.multiple(macos, iokit=mock.DEFAULT, cf=mock.DEFAULT,
                       GetDeviceIntProperty=mock.DEFAULT)
  def testInitHidDevice(self, thread, iokit, cf, GetDeviceIntProperty):  # pylint: disable=invalid-name
    init_mock_iokit(iokit)
    init_mock_cf(cf)
    init_mock_get_int_property(GetDeviceIntProperty)

    device = macos.MacOsHidDevice('fakepath')

    self.assertEquals(64, device.GetInReportDataLength())
    self.assertEquals(64, device.GetOutReportDataLength())

  @mock.patch.object(macos.threading, 'Thread')
  @mock.patch.multiple(macos, iokit=mock.DEFAULT, cf=mock.DEFAULT,
                       GetDeviceIntProperty=mock.DEFAULT)
  def testCallWriteSuccess(self, thread, iokit, cf, GetDeviceIntProperty):  # pylint: disable=invalid-name
    init_mock_iokit(iokit)
    init_mock_cf(cf)
    init_mock_get_int_property(GetDeviceIntProperty)

    device = macos.MacOsHidDevice('fakepath')

    # Write 64 bytes to device
    data = bytearray(range(64))

    # Write to device
    device.Write(data)

    # Validate that write calls into IOKit
    set_report_call_args = iokit.IOHIDDeviceSetReport.call_args
    self.assertIsNotNone(set_report_call_args)

    set_report_call_pos_args = iokit.IOHIDDeviceSetReport.call_args[0]
    self.assertEquals(len(set_report_call_pos_args), 5)
    self.assertEquals(set_report_call_pos_args[0], 'handle')
    self.assertEquals(set_report_call_pos_args[1], 1)
    self.assertEquals(set_report_call_pos_args[2], 0)
    self.assertEquals(set_report_call_pos_args[4], 64)

    report_buffer = set_report_call_pos_args[3]
    self.assertEqual(len(report_buffer), 64)
    self.assertEqual(bytearray(report_buffer), data, 'Data sent to '
                     'IOHIDDeviceSetReport should match data sent to the '
                     'device')

  @mock.patch.object(macos.threading, 'Thread')
  @mock.patch.multiple(macos, iokit=mock.DEFAULT, cf=mock.DEFAULT,
                       GetDeviceIntProperty=mock.DEFAULT)
  def testCallWriteFailure(self, thread, iokit, cf, GetDeviceIntProperty):  # pylint: disable=invalid-name
    init_mock_iokit(iokit)
    init_mock_cf(cf)
    init_mock_get_int_property(GetDeviceIntProperty)

    # Make set report call return failure (non-zero)
    iokit.IOHIDDeviceSetReport.return_value = -1

    device = macos.MacOsHidDevice('fakepath')

    # Write 64 bytes to device
    data = bytearray(range(64))

    # Write should throw an OsHidError exception
    with self.assertRaises(errors.OsHidError):
      device.Write(data)

  @mock.patch.object(macos.threading, 'Thread')
  @mock.patch.multiple(macos, iokit=mock.DEFAULT, cf=mock.DEFAULT,
                       GetDeviceIntProperty=mock.DEFAULT)
  def testCallReadSuccess(self, thread, iokit, cf, GetDeviceIntProperty):  # pylint: disable=invalid-name
    init_mock_iokit(iokit)
    init_mock_cf(cf)
    init_mock_get_int_property(GetDeviceIntProperty)

    device = macos.MacOsHidDevice('fakepath')

    # Call callback for IN report
    report = (ctypes.c_uint8 * 64)()
    report[:] = range(64)[:]
    q = device.read_queue
    macos.HidReadCallback(q, None, None, None, 0, report, 64)

    # Device read should return the callback data
    read_result = device.Read()
    self.assertEquals(read_result, list(range(64)), 'Read data should match '
                      'data passed into the callback')


if __name__ == '__main__':
  unittest.main()
