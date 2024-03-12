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

"""Implements raw HID interface on Linux using SysFS and device files."""
from __future__ import division

import os
import struct

from pyu2f import errors
from pyu2f.hid import base

REPORT_DESCRIPTOR_KEY_MASK = 0xfc
LONG_ITEM_ENCODING = 0xfe
OUTPUT_ITEM = 0x90
INPUT_ITEM = 0x80
COLLECTION_ITEM = 0xa0
REPORT_COUNT = 0x94
REPORT_SIZE = 0x74
USAGE_PAGE = 0x04
USAGE = 0x08


def GetValueLength(rd, pos):
  """Get value length for a key in rd.

  For a key at position pos in the Report Descriptor rd, return the length
  of the associated value.  This supports both short and long format
  values.

  Args:
    rd: Report Descriptor
    pos: The position of the key in rd.

  Returns:
    (key_size, data_len) where key_size is the number of bytes occupied by
    the key and data_len is the length of the value associated by the key.
  """
  rd = bytearray(rd)
  key = rd[pos]
  if key == LONG_ITEM_ENCODING:
    # If the key is tagged as a long item (0xfe), then the format is
    # [key (1 byte)] [data len (1 byte)] [item tag (1 byte)] [data (n # bytes)].
    # Thus, the entire key record is 3 bytes long.
    if pos + 1 < len(rd):
      return (3, rd[pos + 1])
    else:
      raise errors.HidError('Malformed report descriptor')

  else:
    # If the key is tagged as a short item, then the item tag and data len are
    # packed into one byte.  The format is thus:
    # [tag (high 4 bits)] [type (2 bits)] [size code (2 bits)] [data (n bytes)].
    # The size code specifies 1,2, or 4 bytes (0x03 means 4 bytes).
    code = key & 0x03
    if code <= 0x02:
      return (1, code)
    elif code == 0x03:
      return (1, 4)

  raise errors.HidError('Cannot happen')


def ReadLsbBytes(rd, offset, value_size):
  """Reads value_size bytes from rd at offset, least signifcant byte first."""

  encoding = None
  if value_size == 1:
    encoding = '<B'
  elif value_size == 2:
    encoding = '<H'
  elif value_size == 4:
    encoding = '<L'
  else:
    raise errors.HidError('Invalid value size specified')

  ret, = struct.unpack(encoding, rd[offset:offset + value_size])
  return ret


class NoReportCountFound(Exception):
  pass


def ParseReportDescriptor(rd, desc):
  """Parse the binary report descriptor.

  Parse the binary report descriptor into a DeviceDescriptor object.

  Args:
    rd: The binary report descriptor
    desc: The DeviceDescriptor object to update with the results
        from parsing the descriptor.

  Returns:
    None
  """
  rd = bytearray(rd)

  pos = 0
  report_count = None
  report_size = None
  usage_page = None
  usage = None

  while pos < len(rd):
    key = rd[pos]

    # First step, determine the value encoding (either long or short).
    key_size, value_length = GetValueLength(rd, pos)

    if key & REPORT_DESCRIPTOR_KEY_MASK == INPUT_ITEM:
      if report_count and report_size:
        byte_length = (report_count * report_size) // 8
        desc.internal_max_in_report_len = max(
            desc.internal_max_in_report_len, byte_length)
        report_count = None
        report_size = None
    elif key & REPORT_DESCRIPTOR_KEY_MASK == OUTPUT_ITEM:
      if report_count and report_size:
        byte_length = (report_count * report_size) // 8
        desc.internal_max_out_report_len = max(
            desc.internal_max_out_report_len, byte_length)
        report_count = None
        report_size = None
    elif key & REPORT_DESCRIPTOR_KEY_MASK == COLLECTION_ITEM:
      if usage_page:
        desc.usage_page = usage_page
      if usage:
        desc.usage = usage
    elif key & REPORT_DESCRIPTOR_KEY_MASK == REPORT_COUNT:
      if len(rd) >= pos + 1 + value_length:
        report_count = ReadLsbBytes(rd, pos + 1, value_length)
    elif key & REPORT_DESCRIPTOR_KEY_MASK == REPORT_SIZE:
      if len(rd) >= pos + 1 + value_length:
        report_size = ReadLsbBytes(rd, pos + 1, value_length)
    elif key & REPORT_DESCRIPTOR_KEY_MASK == USAGE_PAGE:
      if len(rd) >= pos + 1 + value_length:
        usage_page = ReadLsbBytes(rd, pos + 1, value_length)
    elif key & REPORT_DESCRIPTOR_KEY_MASK == USAGE:
      if len(rd) >= pos + 1 + value_length:
        usage = ReadLsbBytes(rd, pos + 1, value_length)

    pos += value_length + key_size
  return desc


def ParseUevent(uevent, desc):
  lines = uevent.split(b'\n')
  for line in lines:
    line = line.strip()
    if not line:
      continue
    k, v = line.split(b'=')
    if k == b'HID_NAME':
      desc.product_string = v.decode('utf8')
    elif k == b'HID_ID':
      _, vid, pid = v.split(b':')
      desc.vendor_id = int(vid, 16)
      desc.product_id = int(pid, 16)


class LinuxHidDevice(base.HidDevice):
  """Implementation of HID device for linux.

  Implementation of HID device interface for linux that uses block
  devices to interact with the device and sysfs to enumerate/discover
  device metadata.
  """

  @staticmethod
  def Enumerate():
    hidraw_devices = []
    try:
      hidraw_devices = os.listdir('/sys/class/hidraw')
    except FileNotFoundError:
      raise errors.OsHidError('No hidraw device is available')

    for dev in hidraw_devices:
      rd_path = (
          os.path.join(
              '/sys/class/hidraw', dev,
              'device/report_descriptor'))
      uevent_path = os.path.join('/sys/class/hidraw', dev, 'device/uevent')
      rd_file = open(rd_path, 'rb')
      uevent_file = open(uevent_path, 'rb')
      desc = base.DeviceDescriptor()
      desc.path = os.path.join('/dev/', dev)
      ParseReportDescriptor(rd_file.read(), desc)
      ParseUevent(uevent_file.read(), desc)

      rd_file.close()
      uevent_file.close()
      yield desc.ToPublicDict()

  def __init__(self, path):
    base.HidDevice.__init__(self, path)
    self.dev = os.open(path, os.O_RDWR)
    self.desc = base.DeviceDescriptor()
    self.desc.path = path
    rd_file = open(os.path.join('/sys/class/hidraw',
                                os.path.basename(path),
                                'device/report_descriptor'), 'rb')
    ParseReportDescriptor(rd_file.read(), self.desc)
    rd_file.close()

  def GetInReportDataLength(self):
    """See base class."""
    return self.desc.internal_max_in_report_len

  def GetOutReportDataLength(self):
    """See base class."""
    return self.desc.internal_max_out_report_len

  def Write(self, packet):
    """See base class."""
    out = bytearray([0] + packet)  # Prepend the zero-byte (report ID)
    os.write(self.dev, out)

  def Read(self):
    """See base class."""
    raw_in = os.read(self.dev, self.GetInReportDataLength())
    decoded_in = list(bytearray(raw_in))
    return decoded_in
