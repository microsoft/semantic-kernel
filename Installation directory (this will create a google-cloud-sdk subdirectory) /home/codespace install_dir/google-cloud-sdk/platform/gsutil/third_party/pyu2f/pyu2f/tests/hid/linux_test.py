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

"""Tests for pyu2f.hid.linux."""

import base64
import os
import sys

import mock

from pyu2f.hid import linux

# Since the builtins name changed between Python 2 and Python 3, we have to
# make sure to mock the corret one.
if sys.version_info[0] > 2:
  import builtins as py_builtins
else:
  import __builtin__ as py_builtins

try:
  from pyfakefs import fake_filesystem  # pylint: disable=g-import-not-at-top
except ImportError:
  from fakefs import fake_filesystem  # pylint: disable=g-import-not-at-top

if sys.version_info[:2] < (2, 7):
  import unittest2 as unittest  # pylint: disable=g-import-not-at-top
else:
  import unittest  # pylint: disable=g-import-not-at-top


# These are base64 encoded report descriptors of a Yubico token
# and a Logitech keyboard.
YUBICO_RD = 'BtDxCQGhAQkgFQAm/wB1CJVAgQIJIRUAJv8AdQiVQJECwA=='
KEYBOARD_RD = (
    'BQEJAqEBCQGhAAUJGQEpBRUAJQGVBXUBgQKVAXUDgQEFAQkwCTEJOBWBJX91CJUDgQbAwA==')


def AddDevice(fs, dev_name, product_name,
              vendor_id, product_id, report_descriptor_b64):
  uevent = fs.CreateFile('/sys/class/hidraw/%s/device/uevent' % dev_name)
  rd = fs.CreateFile('/sys/class/hidraw/%s/device/report_descriptor' % dev_name)
  report_descriptor = base64.b64decode(report_descriptor_b64)
  rd.SetContents(report_descriptor)

  buf = 'HID_NAME=%s\n' % product_name.encode('utf8')
  buf += 'HID_ID=0001:%08X:%08X\n' % (vendor_id, product_id)
  uevent.SetContents(buf)


class FakeDeviceOsModule(object):
  O_RDWR = os.O_RDWR
  path = os.path

  data_written = None
  data_to_return = None

  def open(self, unused_path, unused_opts):  # pylint: disable=invalid-name
    return 0

  def write(self, unused_dev, data):  # pylint: disable=invalid-name
    self.data_written = data

  def read(self, unused_dev, unused_length):  # pylint: disable=invalid-name
    return self.data_to_return


class LinuxTest(unittest.TestCase):
  def setUp(self):
    self.fs = fake_filesystem.FakeFilesystem()
    self.fs.CreateDirectory('/sys/class/hidraw')

  def tearDown(self):
    self.fs.RemoveObject('/sys/class/hidraw')

  def testCallEnumerate(self):
    AddDevice(self.fs, 'hidraw1', 'Logitech USB Keyboard',
              0x046d, 0xc31c, KEYBOARD_RD)
    AddDevice(self.fs, 'hidraw2', 'Yubico U2F', 0x1050, 0x0407, YUBICO_RD)
    with mock.patch.object(linux, 'os', fake_filesystem.FakeOsModule(self.fs)):
      fake_open = fake_filesystem.FakeFileOpen(self.fs)
      with mock.patch.object(py_builtins, 'open', fake_open):
        devs = list(linux.LinuxHidDevice.Enumerate())
        devs = sorted(devs, key=lambda k: (k['vendor_id']))

        self.assertEquals(len(devs), 2)
        self.assertEquals(devs[0]['vendor_id'], 0x046d)
        self.assertEquals(devs[0]['product_id'], 0x0c31c)
        self.assertEquals(devs[1]['vendor_id'], 0x1050)
        self.assertEquals(devs[1]['product_id'], 0x0407)
        self.assertEquals(devs[1]['usage_page'], 0xf1d0)
        self.assertEquals(devs[1]['usage'], 1)

  def testCallOpen(self):
    AddDevice(self.fs, 'hidraw1', 'Yubico U2F', 0x1050, 0x0407, YUBICO_RD)
    fake_open = fake_filesystem.FakeFileOpen(self.fs)
    # The open() builtin is used to read from the fake sysfs
    with mock.patch.object(py_builtins, 'open', fake_open):
      # The os.open function is used to interact with the low
      # level device.  We don't want to use fakefs for that.
      fake_dev_os = FakeDeviceOsModule()
      with mock.patch.object(linux, 'os', fake_dev_os):
        dev = linux.LinuxHidDevice('/dev/hidraw1')
        self.assertEquals(dev.GetInReportDataLength(), 64)
        self.assertEquals(dev.GetOutReportDataLength(), 64)

        dev.Write(list(range(0, 64)))
        # The HidDevice implementation prepends a zero-byte representing the
        # report ID
        self.assertEquals(list(fake_dev_os.data_written),
                          [0] + list(range(0, 64)))

        fake_dev_os.data_to_return = b'x' * 64
        self.assertEquals(dev.Read(), [120] * 64)  # chr(120) = 'x'


if __name__ == '__main__':
  unittest.main()
