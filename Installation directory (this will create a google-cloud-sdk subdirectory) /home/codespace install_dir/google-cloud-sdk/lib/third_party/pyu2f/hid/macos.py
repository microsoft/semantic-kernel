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

"""Implements HID device interface on MacOS using IOKit and HIDManager."""
from six.moves import queue
from six.moves import range
import ctypes
import ctypes.util
import logging
import sys
import threading

from pyu2f import errors
from pyu2f.hid import base

logger = logging.getLogger('pyu2f.macos')

# Constants
DEVICE_PATH_BUFFER_SIZE = 512
DEVICE_STRING_PROPERTY_BUFFER_SIZE = 512

HID_DEVICE_PROPERTY_VENDOR_ID = 'VendorId'
HID_DEVICE_PROPERTY_PRODUCT_ID = 'ProductID'
HID_DEVICE_PROPERTY_PRODUCT = 'Product'
HID_DEVICE_PROPERTY_PRIMARY_USAGE = 'PrimaryUsage'
HID_DEVICE_PROPERTY_PRIMARY_USAGE_PAGE = 'PrimaryUsagePage'
HID_DEVICE_PROPERTY_MAX_INPUT_REPORT_SIZE = 'MaxInputReportSize'
HID_DEVICE_PROPERTY_MAX_OUTPUT_REPORT_SIZE = 'MaxOutputReportSize'
HID_DEVICE_PROPERTY_REPORT_ID = 'ReportID'


# Declare C types
class _CFType(ctypes.Structure):
  pass


class _CFString(_CFType):
  pass


class _CFSet(_CFType):
  pass


class _IOHIDManager(_CFType):
  pass


class _IOHIDDevice(_CFType):
  pass


class _CFRunLoop(_CFType):
  pass


class _CFAllocator(_CFType):
  pass


# Linter isn't consistent about valid class names. Disabling some of the errors
CF_SET_REF = ctypes.POINTER(_CFSet)
CF_STRING_REF = ctypes.POINTER(_CFString)
CF_TYPE_REF = ctypes.POINTER(_CFType)
CF_RUN_LOOP_REF = ctypes.POINTER(_CFRunLoop)
CF_RUN_LOOP_RUN_RESULT = ctypes.c_int32
CF_ALLOCATOR_REF = ctypes.POINTER(_CFAllocator)
CF_TYPE_ID = ctypes.c_ulong  # pylint: disable=invalid-name
CF_INDEX = ctypes.c_long  # pylint: disable=invalid-name
CF_TIME_INTERVAL = ctypes.c_double  # pylint: disable=invalid-name
IO_RETURN = ctypes.c_uint
IO_HID_REPORT_TYPE = ctypes.c_uint
IO_OBJECT_T = ctypes.c_uint
MACH_PORT_T = ctypes.c_uint
IO_STRING_T = ctypes.c_char_p  # pylint: disable=invalid-name
IO_SERVICE_T = IO_OBJECT_T
IO_REGISTRY_ENTRY_T = IO_OBJECT_T

IO_HID_MANAGER_REF = ctypes.POINTER(_IOHIDManager)
IO_HID_DEVICE_REF = ctypes.POINTER(_IOHIDDevice)

IO_HID_REPORT_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.py_object, IO_RETURN,
                                          ctypes.c_void_p, IO_HID_REPORT_TYPE,
                                          ctypes.c_uint32,
                                          ctypes.POINTER(ctypes.c_uint8),
                                          CF_INDEX)

# Define C constants
K_CF_NUMBER_SINT32_TYPE = 3
K_CF_STRING_ENCODING_UTF8 = 0x08000100
K_CF_ALLOCATOR_DEFAULT = None

K_IO_SERVICE_PLANE = b'IOService'
K_IO_MASTER_PORT_DEFAULT = 0
K_IO_HID_REPORT_TYPE_OUTPUT = 1
K_IO_RETURN_SUCCESS = 0

K_CF_RUN_LOOP_RUN_STOPPED = 2
K_CF_RUN_LOOP_RUN_TIMED_OUT = 3
K_CF_RUN_LOOP_RUN_HANDLED_SOURCE = 4

# Load relevant libraries
iokit = ctypes.cdll.LoadLibrary(ctypes.util.find_library('IOKit'))
cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation'))

# Only use iokit and cf if we're on macos, this way we can still run tests
# on other platforms if we properly mock
if sys.platform.startswith('darwin'):
  # Exported constants
  K_CF_RUNLOOP_DEFAULT_MODE = CF_STRING_REF.in_dll(cf, 'kCFRunLoopDefaultMode')

  # Declare C function prototypes
  cf.CFSetGetValues.restype = None
  cf.CFSetGetValues.argtypes = [CF_SET_REF, ctypes.POINTER(ctypes.c_void_p)]
  cf.CFStringCreateWithCString.restype = CF_STRING_REF
  cf.CFStringCreateWithCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p,
                                           ctypes.c_uint32]
  cf.CFStringGetCString.restype = ctypes.c_int
  cf.CFStringGetCString.argtypes = [CF_STRING_REF, ctypes.c_char_p, CF_INDEX,
                                    ctypes.c_uint32]
  cf.CFStringGetLength.restype = CF_INDEX
  cf.CFStringGetLength.argtypes = [CF_STRING_REF]
  cf.CFGetTypeID.restype = CF_TYPE_ID
  cf.CFGetTypeID.argtypes = [CF_TYPE_REF]
  cf.CFNumberGetTypeID.restype = CF_TYPE_ID
  cf.CFNumberGetValue.restype = ctypes.c_int
  cf.CFRelease.restype = None
  cf.CFRelease.argtypes = [CF_TYPE_REF]
  cf.CFRunLoopGetCurrent.restype = CF_RUN_LOOP_REF
  cf.CFRunLoopGetCurrent.argTypes = []
  cf.CFRunLoopRunInMode.restype = CF_RUN_LOOP_RUN_RESULT
  cf.CFRunLoopRunInMode.argtypes = [CF_STRING_REF, CF_TIME_INTERVAL,
                                    ctypes.c_bool]

  iokit.IOObjectRelease.argtypes = [IO_OBJECT_T]
  iokit.IOHIDManagerCreate.restype = IO_HID_MANAGER_REF
  iokit.IOHIDManagerCopyDevices.restype = CF_SET_REF
  iokit.IOHIDManagerCopyDevices.argtypes = [IO_HID_MANAGER_REF]
  iokit.IOHIDManagerSetDeviceMatching.restype = None
  iokit.IOHIDManagerSetDeviceMatching.argtypes = [IO_HID_MANAGER_REF,
                                                  CF_TYPE_REF]
  iokit.IOHIDDeviceGetProperty.restype = CF_TYPE_REF
  iokit.IOHIDDeviceGetProperty.argtypes = [IO_HID_DEVICE_REF, CF_STRING_REF]
  iokit.IOHIDDeviceRegisterInputReportCallback.restype = None
  iokit.IOHIDDeviceRegisterInputReportCallback.argtypes = [
      IO_HID_DEVICE_REF, ctypes.POINTER(ctypes.c_uint8), CF_INDEX,
      IO_HID_REPORT_CALLBACK, ctypes.py_object]
  iokit.IORegistryEntryFromPath.restype = IO_REGISTRY_ENTRY_T
  iokit.IORegistryEntryFromPath.argtypes = [MACH_PORT_T, IO_STRING_T]
  iokit.IOHIDDeviceCreate.restype = IO_HID_DEVICE_REF
  iokit.IOHIDDeviceCreate.argtypes = [CF_ALLOCATOR_REF, IO_SERVICE_T]
  iokit.IOHIDDeviceScheduleWithRunLoop.restype = None
  iokit.IOHIDDeviceScheduleWithRunLoop.argtypes = [IO_HID_DEVICE_REF,
                                                   CF_RUN_LOOP_REF,
                                                   CF_STRING_REF]
  iokit.IOHIDDeviceUnscheduleFromRunLoop.restype = None
  iokit.IOHIDDeviceUnscheduleFromRunLoop.argtypes = [IO_HID_DEVICE_REF,
                                                     CF_RUN_LOOP_REF,
                                                     CF_STRING_REF]
  iokit.IOHIDDeviceSetReport.restype = IO_RETURN
  iokit.IOHIDDeviceSetReport.argtypes = [IO_HID_DEVICE_REF, IO_HID_REPORT_TYPE,
                                         CF_INDEX,
                                         ctypes.POINTER(ctypes.c_uint8),
                                         CF_INDEX]
else:
  logger.warning('Not running on MacOS')


def CFStr(s):
  """Builds a CFString from a python string.

  Args:
    s: source string

  Returns:
    CFStringRef representation of the source string

  Resulting CFString must be CFReleased when no longer needed.
  """
  return cf.CFStringCreateWithCString(None, s.encode(), 0)


def GetDeviceIntProperty(dev_ref, key):
  """Reads int property from the HID device."""
  cf_key = CFStr(key)
  type_ref = iokit.IOHIDDeviceGetProperty(dev_ref, cf_key)
  cf.CFRelease(cf_key)
  if not type_ref:
    return None

  if cf.CFGetTypeID(type_ref) != cf.CFNumberGetTypeID():
    raise errors.OsHidError('Expected number type, got {}'.format(
        cf.CFGetTypeID(type_ref)))

  out = ctypes.c_int32()
  ret = cf.CFNumberGetValue(type_ref, K_CF_NUMBER_SINT32_TYPE,
                            ctypes.byref(out))
  if not ret:
    return None

  return out.value


def GetDeviceStringProperty(dev_ref, key):
  """Reads string property from the HID device."""
  cf_key = CFStr(key)
  type_ref = iokit.IOHIDDeviceGetProperty(dev_ref, cf_key)
  cf.CFRelease(cf_key)
  if not type_ref:
    return None

  if cf.CFGetTypeID(type_ref) != cf.CFStringGetTypeID():
    raise errors.OsHidError('Expected string type, got {}'.format(
        cf.CFGetTypeID(type_ref)))

  type_ref = ctypes.cast(type_ref, CF_STRING_REF)
  out = ctypes.create_string_buffer(DEVICE_STRING_PROPERTY_BUFFER_SIZE)
  ret = cf.CFStringGetCString(type_ref, out, DEVICE_STRING_PROPERTY_BUFFER_SIZE,
                              K_CF_STRING_ENCODING_UTF8)
  if not ret:
    return None

  return out.value.decode('utf8')


def GetDevicePath(device_handle):
  """Obtains the unique path for the device.

  Args:
    device_handle: reference to the device

  Returns:
    A unique path for the device, obtained from the IO Registry

  """
  # Obtain device path from IO Registry
  io_service_obj = iokit.IOHIDDeviceGetService(device_handle)
  str_buffer = ctypes.create_string_buffer(DEVICE_PATH_BUFFER_SIZE)
  iokit.IORegistryEntryGetPath(io_service_obj, K_IO_SERVICE_PLANE, str_buffer)

  return str_buffer.value


def HidReadCallback(read_queue, result, sender, report_type, report_id, report,
                    report_length):
  """Handles incoming IN report from HID device."""
  del result, sender, report_type, report_id  # Unused by the callback function

  incoming_bytes = [report[i] for i in range(report_length)]
  read_queue.put(incoming_bytes)

# C wrapper around ReadCallback()
# Declared in this scope so it doesn't get GC-ed
REGISTERED_READ_CALLBACK = IO_HID_REPORT_CALLBACK(HidReadCallback)


def DeviceReadThread(hid_device):
  """Binds a device to the thread's run loop, then starts the run loop.

  Args:
    hid_device: The MacOsHidDevice object

  The HID manager requires a run loop to handle Report reads. This thread
  function serves that purpose.
  """

  # Schedule device events with run loop
  hid_device.run_loop_ref = cf.CFRunLoopGetCurrent()
  if not hid_device.run_loop_ref:
    logger.error('Failed to get current run loop')
    return

  iokit.IOHIDDeviceScheduleWithRunLoop(hid_device.device_handle,
                                       hid_device.run_loop_ref,
                                       K_CF_RUNLOOP_DEFAULT_MODE)

  # Run the run loop
  run_loop_run_result = K_CF_RUN_LOOP_RUN_TIMED_OUT
  while (run_loop_run_result == K_CF_RUN_LOOP_RUN_TIMED_OUT or
         run_loop_run_result == K_CF_RUN_LOOP_RUN_HANDLED_SOURCE):
    run_loop_run_result = cf.CFRunLoopRunInMode(
        K_CF_RUNLOOP_DEFAULT_MODE,
        1000,  # Timeout in seconds
        False)  # Return after source handled

  # log any unexpected run loop exit
  if run_loop_run_result != K_CF_RUN_LOOP_RUN_STOPPED:
    logger.error('Unexpected run loop exit code: %d', run_loop_run_result)

  # Unschedule from run loop
  iokit.IOHIDDeviceUnscheduleFromRunLoop(hid_device.device_handle,
                                         hid_device.run_loop_ref,
                                         K_CF_RUNLOOP_DEFAULT_MODE)


class MacOsHidDevice(base.HidDevice):
  """Implementation of HID device for MacOS.

  Uses IOKit HID Manager to interact with the device.
  """

  @staticmethod
  def Enumerate():
    """See base class."""
    # Init a HID manager
    hid_mgr = iokit.IOHIDManagerCreate(None, None)
    if not hid_mgr:
      raise errors.OsHidError('Unable to obtain HID manager reference')
    iokit.IOHIDManagerSetDeviceMatching(hid_mgr, None)

    # Get devices from HID manager
    device_set_ref = iokit.IOHIDManagerCopyDevices(hid_mgr)
    if not device_set_ref:
      raise errors.OsHidError('Failed to obtain devices from HID manager')

    num = iokit.CFSetGetCount(device_set_ref)
    devices = (IO_HID_DEVICE_REF * num)()
    iokit.CFSetGetValues(device_set_ref, devices)

    # Retrieve and build descriptor dictionaries for each device
    descriptors = []
    for dev in devices:
      d = base.DeviceDescriptor()
      d.vendor_id = GetDeviceIntProperty(dev, HID_DEVICE_PROPERTY_VENDOR_ID)
      d.product_id = GetDeviceIntProperty(dev, HID_DEVICE_PROPERTY_PRODUCT_ID)
      d.product_string = GetDeviceStringProperty(dev,
                                                 HID_DEVICE_PROPERTY_PRODUCT)
      d.usage = GetDeviceIntProperty(dev, HID_DEVICE_PROPERTY_PRIMARY_USAGE)
      d.usage_page = GetDeviceIntProperty(
          dev, HID_DEVICE_PROPERTY_PRIMARY_USAGE_PAGE)
      d.report_id = GetDeviceIntProperty(dev, HID_DEVICE_PROPERTY_REPORT_ID)
      d.path = GetDevicePath(dev)
      descriptors.append(d.ToPublicDict())

    # Clean up CF objects
    cf.CFRelease(device_set_ref)
    cf.CFRelease(hid_mgr)

    return descriptors

  def __init__(self, path):
    # Resolve the path to device handle
    device_entry = iokit.IORegistryEntryFromPath(K_IO_MASTER_PORT_DEFAULT, path)
    if not device_entry:
      raise errors.OsHidError('Device path does not match any HID device on '
                              'the system')

    self.device_handle = iokit.IOHIDDeviceCreate(K_CF_ALLOCATOR_DEFAULT,
                                                 device_entry)
    if not self.device_handle:
      raise errors.OsHidError('Failed to obtain device handle from registry '
                              'entry')
    iokit.IOObjectRelease(device_entry)

    self.device_path = path

    # Open device
    result = iokit.IOHIDDeviceOpen(self.device_handle, 0)
    if result != K_IO_RETURN_SUCCESS:
      raise errors.OsHidError('Failed to open device for communication: {}'
                              .format(result))

    # Create read queue
    self.read_queue = queue.Queue()

    # Create and start read thread
    self.run_loop_ref = None
    self.read_thread = threading.Thread(target=DeviceReadThread,
                                        args=(self,))
    self.read_thread.daemon = True
    self.read_thread.start()

    # Read max report sizes for in/out
    self.internal_max_in_report_len = GetDeviceIntProperty(
        self.device_handle,
        HID_DEVICE_PROPERTY_MAX_INPUT_REPORT_SIZE)
    if not self.internal_max_in_report_len:
      raise errors.OsHidError('Unable to obtain max in report size')

    self.internal_max_out_report_len = GetDeviceIntProperty(
        self.device_handle,
        HID_DEVICE_PROPERTY_MAX_OUTPUT_REPORT_SIZE)
    if not self.internal_max_out_report_len:
      raise errors.OsHidError('Unable to obtain max out report size')

    # Register read callback
    self.in_report_buffer = (ctypes.c_uint8 * self.internal_max_in_report_len)()
    iokit.IOHIDDeviceRegisterInputReportCallback(
        self.device_handle,
        self.in_report_buffer,
        self.internal_max_in_report_len,
        REGISTERED_READ_CALLBACK,
        ctypes.py_object(self.read_queue))

  def GetInReportDataLength(self):
    """See base class."""
    return self.internal_max_in_report_len

  def GetOutReportDataLength(self):
    """See base class."""
    return self.internal_max_out_report_len

  def Write(self, packet):
    """See base class."""
    report_id = 0
    out_report_buffer = (ctypes.c_uint8 * self.internal_max_out_report_len)()
    out_report_buffer[:] = packet[:]

    result = iokit.IOHIDDeviceSetReport(self.device_handle,
                                        K_IO_HID_REPORT_TYPE_OUTPUT,
                                        report_id,
                                        out_report_buffer,
                                        self.internal_max_out_report_len)

    # Non-zero status indicates failure
    if result != K_IO_RETURN_SUCCESS:
      raise errors.OsHidError('Failed to write report to device')

  def Read(self):
    """See base class."""

    result = None
    while result is None:
        try:
            result = self.read_queue.get(timeout=60)
        except queue.Empty:
            continue

    return result

  def __del__(self):
    # Unregister the callback
    if hasattr(self, 'in_report_buffer'):
        iokit.IOHIDDeviceRegisterInputReportCallback(
            self.device_handle,
            self.in_report_buffer,
            self.internal_max_in_report_len,
            None,
            None)

    # Stop the run loop
    if hasattr(self, 'run_loop_ref'):
        cf.CFRunLoopStop(self.run_loop_ref)

    # Wait for the read thread to exit
    if hasattr(self, 'read_thread'):
        self.read_thread.join()
