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

"""Implements interface for talking to hid devices.

This module implenets an interface for talking to low level hid devices
using various methods on different platforms.
"""
import sys


def Enumerate():
  return InternalPlatformSwitch('Enumerate')


def Open(path):
  return InternalPlatformSwitch('__init__', path)


def InternalPlatformSwitch(funcname, *args, **kwargs):
  """Determine, on a platform-specific basis, which module to use."""
  # pylint: disable=g-import-not-at-top
  clz = None
  if sys.platform.startswith('linux'):
    from pyu2f.hid import linux
    clz = linux.LinuxHidDevice
  elif sys.platform.startswith('win32'):
    from pyu2f.hid import windows
    clz = windows.WindowsHidDevice
  elif sys.platform.startswith('darwin'):
    from pyu2f.hid import macos
    clz = macos.MacOsHidDevice

  if not clz:
    raise Exception('Unsupported platform: ' + sys.platform)

  if funcname == '__init__':
    return clz(*args, **kwargs)
  return getattr(clz, funcname)(*args, **kwargs)
