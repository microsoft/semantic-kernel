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

"""Implements raw HID device communication on Windows."""

import ctypes
from ctypes import wintypes

import platform

from pyu2f import errors
from pyu2f.hid import base


# Load relevant DLLs
hid = ctypes.windll.Hid
setupapi = ctypes.windll.SetupAPI
kernel32 = ctypes.windll.Kernel32


# Various structs that are used in the Windows APIs we call
class GUID(ctypes.Structure):
  _fields_ = [("Data1", ctypes.c_ulong),
              ("Data2", ctypes.c_ushort),
              ("Data3", ctypes.c_ushort),
              ("Data4", ctypes.c_ubyte * 8)]

# On Windows, SetupAPI.h packs structures differently in 64bit and
# 32bit mode.  In 64bit mode, thestructures are packed on 8 byte
# boundaries, while in 32bit mode, they are packed on 1 byte boundaries.
# This is important to get right for some API calls that fill out these
# structures.
if platform.architecture()[0] == "64bit":
  SETUPAPI_PACK = 8
elif platform.architecture()[0] == "32bit":
  SETUPAPI_PACK = 1
else:
  raise errors.HidError("Unknown architecture: %s" % platform.architecture()[0])


class DeviceInterfaceData(ctypes.Structure):
  _fields_ = [("cbSize", wintypes.DWORD),
              ("InterfaceClassGuid", GUID),
              ("Flags", wintypes.DWORD),
              ("Reserved", ctypes.POINTER(ctypes.c_ulong))]
  _pack_ = SETUPAPI_PACK


class DeviceInterfaceDetailData(ctypes.Structure):
  _fields_ = [("cbSize", wintypes.DWORD),
              ("DevicePath", ctypes.c_byte * 1)]
  _pack_ = SETUPAPI_PACK


class HidAttributes(ctypes.Structure):
  _fields_ = [("Size", ctypes.c_ulong),
              ("VendorID", ctypes.c_ushort),
              ("ProductID", ctypes.c_ushort),
              ("VersionNumber", ctypes.c_ushort)]


class HidCapabilities(ctypes.Structure):
  _fields_ = [("Usage", ctypes.c_ushort),
              ("UsagePage", ctypes.c_ushort),
              ("InputReportByteLength", ctypes.c_ushort),
              ("OutputReportByteLength", ctypes.c_ushort),
              ("FeatureReportByteLength", ctypes.c_ushort),
              ("Reserved", ctypes.c_ushort * 17),
              ("NotUsed", ctypes.c_ushort * 10)]

# Various void* aliases for readability.
HDEVINFO = ctypes.c_void_p
HANDLE = ctypes.c_void_p
PHIDP_PREPARSED_DATA = ctypes.c_void_p  # pylint: disable=invalid-name

# This is a HANDLE.
INVALID_HANDLE_VALUE = 0xffffffff

# Status codes
NTSTATUS = ctypes.c_long
HIDP_STATUS_SUCCESS = 0x00110000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
OPEN_EXISTING = 0x03
ERROR_ACCESS_DENIED = 0x05

# CreateFile Flags
GENERIC_WRITE = 0x40000000
GENERIC_READ = 0x80000000

# Function signatures
hid.HidD_GetHidGuid.restype = None
hid.HidD_GetHidGuid.argtypes = [ctypes.POINTER(GUID)]
hid.HidD_GetAttributes.restype = wintypes.BOOLEAN
hid.HidD_GetAttributes.argtypes = [HANDLE, ctypes.POINTER(HidAttributes)]
hid.HidD_GetPreparsedData.restype = wintypes.BOOLEAN
hid.HidD_GetPreparsedData.argtypes = [HANDLE,
                                      ctypes.POINTER(PHIDP_PREPARSED_DATA)]
hid.HidD_FreePreparsedData.restype = wintypes.BOOLEAN
hid.HidD_FreePreparsedData.argtypes = [PHIDP_PREPARSED_DATA]
hid.HidD_GetProductString.restype = wintypes.BOOLEAN
hid.HidD_GetProductString.argtypes = [HANDLE, ctypes.c_void_p, ctypes.c_ulong]
hid.HidP_GetCaps.restype = NTSTATUS
hid.HidP_GetCaps.argtypes = [PHIDP_PREPARSED_DATA,
                             ctypes.POINTER(HidCapabilities)]

setupapi.SetupDiGetClassDevsA.argtypes = [ctypes.POINTER(GUID), ctypes.c_char_p,
                                          wintypes.HWND, wintypes.DWORD]
setupapi.SetupDiGetClassDevsA.restype = HDEVINFO
setupapi.SetupDiEnumDeviceInterfaces.restype = wintypes.BOOL
setupapi.SetupDiEnumDeviceInterfaces.argtypes = [
    HDEVINFO, ctypes.c_void_p, ctypes.POINTER(GUID), wintypes.DWORD,
    ctypes.POINTER(DeviceInterfaceData)]
setupapi.SetupDiGetDeviceInterfaceDetailA.restype = wintypes.BOOL
setupapi.SetupDiGetDeviceInterfaceDetailA.argtypes = [
    HDEVINFO, ctypes.POINTER(DeviceInterfaceData),
    ctypes.POINTER(DeviceInterfaceDetailData), wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]

kernel32.CreateFileA.restype = HANDLE
kernel32.CreateFileA.argtypes = [
    ctypes.c_char_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
    wintypes.DWORD, wintypes.DWORD, HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.CloseHandle.argtypes = [HANDLE]
kernel32.ReadFile.restype = wintypes.BOOL
kernel32.ReadFile.argtypes = [
    HANDLE, ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
kernel32.WriteFile.restype = wintypes.BOOL
kernel32.WriteFile.argtypes = [
    HANDLE, ctypes.c_void_p, wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]


def FillDeviceAttributes(device, descriptor):
  """Fill out the attributes of the device.

  Fills the devices HidAttributes and product string
  into the descriptor.

  Args:
    device: A handle to the open device
    descriptor: The DeviceDescriptor to populate with the
      attributes.

  Returns:
    None

  Raises:
    WindowsError when unable to obtain attributes or product
      string.
  """
  attributes = HidAttributes()
  result = hid.HidD_GetAttributes(device, ctypes.byref(attributes))
  if not result:
    raise ctypes.WinError()

  buf = ctypes.create_string_buffer(1024)
  result = hid.HidD_GetProductString(device, buf, 1024)

  if not result:
    raise ctypes.WinError()

  descriptor.vendor_id = attributes.VendorID
  descriptor.product_id = attributes.ProductID
  descriptor.product_string = ctypes.wstring_at(buf)


def FillDeviceCapabilities(device, descriptor):
  """Fill out device capabilities.

  Fills the HidCapabilitites of the device into descriptor.

  Args:
    device: A handle to the open device
    descriptor: DeviceDescriptor to populate with the
      capabilities

  Returns:
    none

  Raises:
    WindowsError when unable to obtain capabilitites.
  """
  preparsed_data = PHIDP_PREPARSED_DATA(0)
  ret = hid.HidD_GetPreparsedData(device, ctypes.byref(preparsed_data))
  if not ret:
    raise ctypes.WinError()

  try:
    caps = HidCapabilities()
    ret = hid.HidP_GetCaps(preparsed_data, ctypes.byref(caps))

    if ret != HIDP_STATUS_SUCCESS:
      raise ctypes.WinError()

    descriptor.usage = caps.Usage
    descriptor.usage_page = caps.UsagePage
    descriptor.internal_max_in_report_len = caps.InputReportByteLength
    descriptor.internal_max_out_report_len = caps.OutputReportByteLength

  finally:
    hid.HidD_FreePreparsedData(preparsed_data)


# The python os.open() implementation uses the windows libc
# open() function, which writes CreateFile but does so in a way
# that doesn't let us open the device with the right set of permissions.
# Therefore, we have to directly use the Windows API calls.
# We could use PyWin32, which provides simple wrappers.  However, to avoid
# requiring a PyWin32 dependency for clients, we simply also implement it
# using ctypes.
def OpenDevice(path, enum=False):
  """Open the device and return a handle to it."""
  desired_access = GENERIC_WRITE | GENERIC_READ
  share_mode = FILE_SHARE_READ | FILE_SHARE_WRITE
  if enum:
    desired_access = 0

  h = kernel32.CreateFileA(path,
                           desired_access,
                           share_mode,
                           None, OPEN_EXISTING, 0, None)
  if h == INVALID_HANDLE_VALUE:
    raise ctypes.WinError()
  return h


class WindowsHidDevice(base.HidDevice):
  """Implementation of raw HID interface on Windows."""

  @staticmethod
  def Enumerate():
    """See base class."""
    hid_guid = GUID()
    hid.HidD_GetHidGuid(ctypes.byref(hid_guid))

    devices = setupapi.SetupDiGetClassDevsA(
        ctypes.byref(hid_guid), None, None, 0x12)
    index = 0
    interface_info = DeviceInterfaceData()
    interface_info.cbSize = ctypes.sizeof(DeviceInterfaceData)  # pylint: disable=invalid-name

    out = []
    while True:
      result = setupapi.SetupDiEnumDeviceInterfaces(
          devices, 0, ctypes.byref(hid_guid), index,
          ctypes.byref(interface_info))
      index += 1
      if not result:
        break

      detail_len = wintypes.DWORD()
      result = setupapi.SetupDiGetDeviceInterfaceDetailA(
          devices, ctypes.byref(interface_info), None, 0,
          ctypes.byref(detail_len), None)

      detail_len = detail_len.value
      if detail_len == 0:
        # skip this device, some kind of error
        continue

      buf = ctypes.create_string_buffer(detail_len)
      interface_detail = DeviceInterfaceDetailData.from_buffer(buf)
      interface_detail.cbSize = ctypes.sizeof(DeviceInterfaceDetailData)

      result = setupapi.SetupDiGetDeviceInterfaceDetailA(
          devices, ctypes.byref(interface_info),
          ctypes.byref(interface_detail), detail_len, None, None)

      if not result:
        raise ctypes.WinError()

      descriptor = base.DeviceDescriptor()
      # This is a bit of a hack to work around a limitation of ctypes and
      # "header" structures that are common in windows.  DevicePath is a
      # ctypes array of length 1, but it is backed with a buffer that is much
      # longer and contains a null terminated string.  So, we read the null
      # terminated string off DevicePath here.  Per the comment above, the
      # alignment of this struct varies depending on architecture, but
      # in all cases the path string starts 1 DWORD into the structure.
      #
      # The path length is:
      #   length of detail buffer - header length (1 DWORD)
      path_len = detail_len - ctypes.sizeof(wintypes.DWORD)
      descriptor.path = ctypes.string_at(
          ctypes.addressof(interface_detail.DevicePath), path_len)

      device = None
      try:
        device = OpenDevice(descriptor.path, True)
      except WindowsError as e:  # pylint: disable=undefined-variable
        if e.winerror == ERROR_ACCESS_DENIED:  # Access Denied, e.g. a keyboard
          continue
        else:
          raise e

      try:
        FillDeviceAttributes(device, descriptor)
        FillDeviceCapabilities(device, descriptor)
        out.append(descriptor.ToPublicDict())
      except WindowsError as e:
        continue # skip this device
      finally:
        kernel32.CloseHandle(device)

    return out

  def __init__(self, path):
    """See base class."""
    base.HidDevice.__init__(self, path)
    self.dev = OpenDevice(path)
    self.desc = base.DeviceDescriptor()
    FillDeviceCapabilities(self.dev, self.desc)

  def GetInReportDataLength(self):
    """See base class."""
    return self.desc.internal_max_in_report_len - 1

  def GetOutReportDataLength(self):
    """See base class."""
    return self.desc.internal_max_out_report_len - 1

  def Write(self, packet):
    """See base class."""
    if len(packet) != self.GetOutReportDataLength():
      raise errors.HidError("Packet length must match report data length.")

    packet_data = [0] + packet  # Prepend the zero-byte (report ID)
    out = bytes(bytearray(packet_data))
    num_written = wintypes.DWORD()
    ret = (
        kernel32.WriteFile(
            self.dev, out, len(out),
            ctypes.byref(num_written), None))
    if num_written.value != len(out):
      raise errors.HidError(
          "Failed to write complete packet.  " + "Expected %d, but got %d" %
          (len(out), num_written.value))
    if not ret:
      raise ctypes.WinError()

  def Read(self):
    """See base class."""
    buf = ctypes.create_string_buffer(self.desc.internal_max_in_report_len)
    num_read = wintypes.DWORD()
    ret = kernel32.ReadFile(
        self.dev, buf, len(buf), ctypes.byref(num_read), None)

    if num_read.value != self.desc.internal_max_in_report_len:
      raise errors.HidError("Failed to read full length report from device.")

    if not ret:
      raise ctypes.WinError()

    # Convert the string buffer to a list of numbers.  Throw away the first
    # byte, which is the report id (which we don't care about).
    return list(bytearray(buf[1:]))

  def __del__(self):
    """Closes the file handle when object is GC-ed."""
    if hasattr(self, 'dev'):
      kernel32.CloseHandle(self.dev)
