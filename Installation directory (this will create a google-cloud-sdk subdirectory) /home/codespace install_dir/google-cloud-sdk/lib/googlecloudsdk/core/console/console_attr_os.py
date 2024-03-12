# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""OS specific console_attr helper functions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import sys

from googlecloudsdk.core.util import encoding
from googlecloudsdk.core.util import platforms


def GetTermSize():
  """Gets the terminal x and y dimensions in characters.

  _GetTermSize*() helper functions taken from:
    http://stackoverflow.com/questions/263890/

  Returns:
    (columns, lines): A tuple containing the terminal x and y dimensions.
  """
  xy = None
  # Believe the first helper that doesn't bail.
  for get_terminal_size in (_GetTermSizePosix,
                            _GetTermSizeWindows,
                            _GetTermSizeEnvironment,
                            _GetTermSizeTput):
    try:
      xy = get_terminal_size()
      if xy:
        break
    except:  # pylint: disable=bare-except
      pass
  return xy or (80, 24)


def _GetTermSizePosix():
  """Returns the Posix terminal x and y dimensions."""
  # pylint: disable=g-import-not-at-top
  import fcntl
  # pylint: disable=g-import-not-at-top
  import struct
  # pylint: disable=g-import-not-at-top
  import termios

  def _GetXY(fd):
    """Returns the terminal (x,y) size for fd.

    Args:
      fd: The terminal file descriptor.

    Returns:
      The terminal (x,y) size for fd or None on error.
    """
    try:
      # This magic incantation converts a struct from ioctl(2) containing two
      # binary shorts to a (rows, columns) int tuple.
      rc = struct.unpack(b'hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, 'junk'))
      return (rc[1], rc[0]) if rc else None
    except:  # pylint: disable=bare-except
      return None

  xy = _GetXY(0) or _GetXY(1) or _GetXY(2)
  if not xy:
    fd = None
    try:
      fd = os.open(os.ctermid(), os.O_RDONLY)
      xy = _GetXY(fd)
    except:  # pylint: disable=bare-except
      xy = None
    finally:
      if fd is not None:
        os.close(fd)
  return xy


def _GetTermSizeWindows():
  """Returns the Windows terminal x and y dimensions."""
  # pylint:disable=g-import-not-at-top
  import struct
  # pylint: disable=g-import-not-at-top
  from ctypes import create_string_buffer
  # pylint:disable=g-import-not-at-top
  from ctypes import windll

  # stdin handle is -10
  # stdout handle is -11
  # stderr handle is -12

  h = windll.kernel32.GetStdHandle(-12)
  csbi = create_string_buffer(22)
  if not windll.kernel32.GetConsoleScreenBufferInfo(h, csbi):
    return None
  (unused_bufx, unused_bufy, unused_curx, unused_cury, unused_wattr,
   left, top, right, bottom,
   unused_maxx, unused_maxy) = struct.unpack(b'hhhhHhhhhhh', csbi.raw)
  x = right - left + 1
  y = bottom - top + 1
  return (x, y)


def _GetTermSizeEnvironment():
  """Returns the terminal x and y dimensions from the environment."""
  return (int(os.environ['COLUMNS']), int(os.environ['LINES']))


def _GetTermSizeTput():
  """Returns the terminal x and y dimemsions from tput(1)."""
  import subprocess  # pylint: disable=g-import-not-at-top
  output = encoding.Decode(subprocess.check_output(['tput', 'cols'],
                                                   stderr=subprocess.STDOUT))
  cols = int(output)
  output = encoding.Decode(subprocess.check_output(['tput', 'lines'],
                                                   stderr=subprocess.STDOUT))
  rows = int(output)
  return (cols, rows)


_ANSI_CSI = '\x1b'  # ANSI control sequence indicator (ESC)
_CONTROL_D = '\x04'  # unix EOF (^D)
_CONTROL_Z = '\x1a'  # Windows EOF (^Z)
_WINDOWS_CSI_1 = '\x00'  # Windows control sequence indicator #1
_WINDOWS_CSI_2 = '\xe0'  # Windows control sequence indicator #2


def GetRawKeyFunction():
  """Returns a function that reads one keypress from stdin with no echo.

  Returns:
    A function that reads one keypress from stdin with no echo or a function
    that always returns None if stdin does not support it.
  """
  # Believe the first helper that doesn't bail.
  for get_raw_key_function in (_GetRawKeyFunctionPosix,
                               _GetRawKeyFunctionWindows):
    try:
      return get_raw_key_function()
    except:  # pylint: disable=bare-except
      pass
  return lambda: None


def _GetRawKeyFunctionPosix():
  """_GetRawKeyFunction helper using Posix APIs."""
  # pylint: disable=g-import-not-at-top
  import tty
  # pylint: disable=g-import-not-at-top
  import termios

  def _GetRawKeyPosix():
    """Reads and returns one keypress from stdin, no echo, using Posix APIs.

    Returns:
      The key name, None for EOF, <*> for function keys, otherwise a
      character.
    """
    ansi_to_key = {
        'A': '<UP-ARROW>',
        'B': '<DOWN-ARROW>',
        'D': '<LEFT-ARROW>',
        'C': '<RIGHT-ARROW>',
        '5': '<PAGE-UP>',
        '6': '<PAGE-DOWN>',
        'H': '<HOME>',
        'F': '<END>',
        'M': '<DOWN-ARROW>',
        'S': '<PAGE-UP>',
        'T': '<PAGE-DOWN>',
    }

    # Flush pending output. sys.stdin.read() would do this, but it's explicitly
    # bypassed in _GetKeyChar().
    sys.stdout.flush()

    fd = sys.stdin.fileno()

    def _GetKeyChar():
      return encoding.Decode(os.read(fd, 1))

    old_settings = termios.tcgetattr(fd)
    try:
      tty.setraw(fd)
      c = _GetKeyChar()
      if c == _ANSI_CSI:
        c = _GetKeyChar()
        while True:
          if c == _ANSI_CSI:
            return c
          if c.isalpha():
            break
          prev_c = c
          c = _GetKeyChar()
          if c == '~':
            c = prev_c
            break
        return ansi_to_key.get(c, '')
    except:  # pylint:disable=bare-except
      c = None
    finally:
      termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None if c in (_CONTROL_D, _CONTROL_Z) else c

  return _GetRawKeyPosix


def _GetRawKeyFunctionWindows():
  """_GetRawKeyFunction helper using Windows APIs."""
  # pylint: disable=g-import-not-at-top
  import msvcrt

  def _GetRawKeyWindows():
    """Reads and returns one keypress from stdin, no echo, using Windows APIs.

    Returns:
      The key name, None for EOF, <*> for function keys, otherwise a
      character.
    """
    windows_to_key = {
        'H': '<UP-ARROW>',
        'P': '<DOWN-ARROW>',
        'K': '<LEFT-ARROW>',
        'M': '<RIGHT-ARROW>',
        'I': '<PAGE-UP>',
        'Q': '<PAGE-DOWN>',
        'G': '<HOME>',
        'O': '<END>',
    }

    # Flush pending output. sys.stdin.read() would do this it's explicitly
    # bypassed in _GetKeyChar().
    sys.stdout.flush()

    def _GetKeyChar():
      return encoding.Decode(msvcrt.getch())

    c = _GetKeyChar()
    # Special function key is a two character sequence; return the second char.
    if c in (_WINDOWS_CSI_1, _WINDOWS_CSI_2):
      return windows_to_key.get(_GetKeyChar(), '')
    return None if c in (_CONTROL_D, _CONTROL_Z) else c

  return _GetRawKeyWindows


def ForceEnableAnsi():
  """Attempts to enable virtual terminal processing on Windows.

  Returns:
    bool: True if ANSI support is now active; False otherwise.
  """
  if platforms.OperatingSystem.Current() != platforms.OperatingSystem.WINDOWS:
    return False

  try:
    import ctypes  # pylint:disable=g-import-not-at-top

    enable_virtual_terminal_processing = 0x0004
    h = ctypes.windll.kernel32.GetStdHandle(-11)  # stdout handle is -11
    old_mode = ctypes.wintypes.DWORD()

    if ctypes.windll.kernel32.GetConsoleMode(h, ctypes.byref(old_mode)):
      if ctypes.windll.kernel32.SetConsoleMode(
          h, old_mode.value | enable_virtual_terminal_processing):
        return True
  except (OSError, AttributeError):
    pass  # If we cannot force ANSI, we should simply return False
  return False
