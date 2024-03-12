# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""Utilities for determining the current platform and architecture."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import platform
import re
import subprocess
import sys

from googlecloudsdk.core.util import encoding


INVALID_WINDOWS_PATH_CHARACTERS = ('/', ':', '*', '?', '"', '<', '>', '|')


def MakePathWindowsCompatible(path):
  """Converts invalid Windows characters to Unicode 'unsupported' character."""
  if re.search(r'^[A-Za-z]:', path):
    # Windows drive letters are valid (e.g. "C:\\path\\...").
    new_path = [path[:2]]
    start_index = 2
  else:
    new_path = []
    start_index = 0
  performed_conversion = False
  for i in range(start_index, len(path)):
    if path[i] in INVALID_WINDOWS_PATH_CHARACTERS:
      performed_conversion = True
      new_path.append('${}'.format(
          INVALID_WINDOWS_PATH_CHARACTERS.index(path[i])))
    else:
      new_path.append(path[i])

  new_path_string = ''.join(new_path)
  if performed_conversion:
    sys.stderr.write('WARNING: The following characters are invalid in Windows'
                     ' file and directory names: {}\nRenaming {} to {}'.format(
                         ''.join(INVALID_WINDOWS_PATH_CHARACTERS), path,
                         new_path_string))
  return new_path_string


class Error(Exception):
  """Base class for exceptions in the platforms moudle."""
  pass


class InvalidEnumValue(Error):
  """Exception for when a string could not be parsed to a valid enum value."""

  def __init__(self, given, enum_type, options):
    """Constructs a new exception.

    Args:
      given: str, The given string that could not be parsed.
      enum_type: str, The human readable name of the enum you were trying to
        parse.
      options: list(str), The valid values for this enum.
    """
    super(InvalidEnumValue, self).__init__(
        'Could not parse [{0}] into a valid {1}.  Valid values are [{2}]'
        .format(given, enum_type, ', '.join(options)))


class OperatingSystem(object):
  """An enum representing the operating system you are running on."""

  class _OS(object):
    """A single operating system."""

    # pylint: disable=redefined-builtin
    def __init__(self, id, name, file_name):
      self.id = id
      self.name = name
      self.file_name = file_name

    def __str__(self):
      return self.id

    def __eq__(self, other):
      return (isinstance(other, type(self)) and
              self.id == other.id and
              self.name == other.name and
              self.file_name == other.file_name)

    def __hash__(self):
      return hash(self.id) + hash(self.name) + hash(self.file_name)

    def __ne__(self, other):
      return not self == other

    @classmethod
    def _CmpHelper(cls, x, y):
      """Just a helper equivalent to the cmp() function in Python 2."""
      return (x > y) - (x < y)

    def __lt__(self, other):
      return self._CmpHelper(
          (self.id, self.name, self.file_name),
          (other.id, other.name, other.file_name)) < 0

    def __gt__(self, other):
      return self._CmpHelper(
          (self.id, self.name, self.file_name),
          (other.id, other.name, other.file_name)) > 0

    def __le__(self, other):
      return not self.__gt__(other)

    def __ge__(self, other):
      return not self.__lt__(other)

    @property
    def version(self):
      """Returns the operating system version."""
      if self == OperatingSystem.WINDOWS:
        return platform.version()
      return platform.release()

    @property
    def clean_version(self):
      """Returns a cleaned version of the operating system version."""
      version = self.version
      if self == OperatingSystem.WINDOWS:
        capitalized = version.upper()
        if capitalized in ('XP', 'VISTA'):
          return version
        if capitalized.startswith('SERVER'):
          # Allow Server + 4 digits for year.
          return version[:11].replace(' ', '_')

      matches = re.match(r'(\d+)(\.\d+)?(\.\d+)?.*', version)
      if not matches:
        return None
      return ''.join(group for group in matches.groups() if group)

  WINDOWS = _OS('WINDOWS', 'Windows', 'windows')
  MACOSX = _OS('MACOSX', 'Mac OS X', 'darwin')
  LINUX = _OS('LINUX', 'Linux', 'linux')
  CYGWIN = _OS('CYGWIN', 'Cygwin', 'cygwin')
  MSYS = _OS('MSYS', 'Msys', 'msys')
  _ALL = [WINDOWS, MACOSX, LINUX, CYGWIN, MSYS]

  @staticmethod
  def AllValues():
    """Gets all possible enum values.

    Returns:
      list, All the enum values.
    """
    return list(OperatingSystem._ALL)

  @staticmethod
  def FromId(os_id, error_on_unknown=True):
    """Gets the enum corresponding to the given operating system id.

    Args:
      os_id: str, The operating system id to parse
      error_on_unknown: bool, True to raise an exception if the id is unknown,
        False to just return None.

    Raises:
      InvalidEnumValue: If the given value cannot be parsed.

    Returns:
      OperatingSystemTuple, One of the OperatingSystem constants or None if the
      input is None.
    """
    if not os_id:
      return None
    for operating_system in OperatingSystem._ALL:
      if operating_system.id == os_id:
        return operating_system
    if error_on_unknown:
      raise InvalidEnumValue(os_id, 'Operating System',
                             [value.id for value in OperatingSystem._ALL])
    return None

  @staticmethod
  def Current():
    """Determines the current operating system.

    Returns:
      OperatingSystemTuple, One of the OperatingSystem constants or None if it
      cannot be determined.
    """
    if os.name == 'nt':
      return OperatingSystem.WINDOWS
    elif 'linux' in sys.platform:
      return OperatingSystem.LINUX
    elif 'darwin' in sys.platform:
      return OperatingSystem.MACOSX
    elif 'cygwin' in sys.platform:
      return OperatingSystem.CYGWIN
    return None

  @staticmethod
  def IsWindows():
    """Returns True if the current operating system is Windows."""
    return OperatingSystem.Current() is OperatingSystem.WINDOWS


class Architecture(object):
  """An enum representing the system architecture you are running on."""

  class _ARCH(object):
    """A single architecture."""

    # pylint: disable=redefined-builtin
    def __init__(self, id, name, file_name):
      self.id = id
      self.name = name
      self.file_name = file_name

    def __str__(self):
      return self.id

    def __eq__(self, other):
      return (isinstance(other, type(self)) and
              self.id == other.id and
              self.name == other.name and
              self.file_name == other.file_name)

    def __hash__(self):
      return hash(self.id) + hash(self.name) + hash(self.file_name)

    def __ne__(self, other):
      return not self == other

    @classmethod
    def _CmpHelper(cls, x, y):
      """Just a helper equivalent to the cmp() function in Python 2."""
      return (x > y) - (x < y)

    def __lt__(self, other):
      return self._CmpHelper(
          (self.id, self.name, self.file_name),
          (other.id, other.name, other.file_name)) < 0

    def __gt__(self, other):
      return self._CmpHelper(
          (self.id, self.name, self.file_name),
          (other.id, other.name, other.file_name)) > 0

    def __le__(self, other):
      return not self.__gt__(other)

    def __ge__(self, other):
      return not self.__lt__(other)

  x86 = _ARCH('x86', 'x86', 'x86')
  x86_64 = _ARCH('x86_64', 'x86_64', 'x86_64')
  ppc = _ARCH('PPC', 'PPC', 'ppc')
  arm = _ARCH('arm', 'arm', 'arm')
  _ALL = [x86, x86_64, ppc, arm]

  # Possible values for `uname -m` and what arch they map to.
  # Examples of possible values: https://en.wikipedia.org/wiki/Uname
  _MACHINE_TO_ARCHITECTURE = {
      'amd64': x86_64, 'x86_64': x86_64, 'i686-64': x86_64,
      'i386': x86, 'i686': x86, 'x86': x86,
      'ia64': x86,  # Itanium is different x64 arch, treat it as the common x86.
      'powerpc': ppc, 'power macintosh': ppc, 'ppc64': ppc,
      'armv6': arm, 'armv6l': arm, 'arm64': arm, 'armv7': arm, 'armv7l': arm,
      'aarch64': arm}

  @staticmethod
  def AllValues():
    """Gets all possible enum values.

    Returns:
      list, All the enum values.
    """
    return list(Architecture._ALL)

  @staticmethod
  def FromId(architecture_id, error_on_unknown=True):
    """Gets the enum corresponding to the given architecture id.

    Args:
      architecture_id: str, The architecture id to parse
      error_on_unknown: bool, True to raise an exception if the id is unknown,
        False to just return None.

    Raises:
      InvalidEnumValue: If the given value cannot be parsed.

    Returns:
      ArchitectureTuple, One of the Architecture constants or None if the input
      is None.
    """
    if not architecture_id:
      return None
    for arch in Architecture._ALL:
      if arch.id == architecture_id:
        return arch
    if error_on_unknown:
      raise InvalidEnumValue(architecture_id, 'Architecture',
                             [value.id for value in Architecture._ALL])
    return None

  @staticmethod
  def Current():
    """Determines the current system architecture.

    Returns:
      ArchitectureTuple, One of the Architecture constants or None if it cannot
      be determined.
    """
    return Architecture._MACHINE_TO_ARCHITECTURE.get(platform.machine().lower())


class Platform(object):
  """Holds an operating system and architecture."""

  def __init__(self, operating_system, architecture):
    """Constructs a new platform.

    Args:
      operating_system: OperatingSystem, The OS
      architecture: Architecture, The machine architecture.
    """
    self.operating_system = operating_system
    self.architecture = architecture

  def __str__(self):
    return '{}-{}'.format(self.operating_system, self.architecture)

  @staticmethod
  def Current(os_override=None, arch_override=None):
    """Determines the current platform you are running on.

    Args:
      os_override: OperatingSystem, A value to use instead of the current.
      arch_override: Architecture, A value to use instead of the current.

    Returns:
      Platform, The platform tuple of operating system and architecture.  Either
      can be None if it could not be determined.
    """
    return Platform(
        os_override if os_override else OperatingSystem.Current(),
        arch_override if arch_override else Architecture.Current())

  def UserAgentFragment(self):
    """Generates the fragment of the User-Agent that represents the OS.

    Examples:
      (Linux 3.2.5-gg1236)
      (Windows NT 6.1.7601)
      (Macintosh; PPC Mac OS X 12.4.0)
      (Macintosh; Intel Mac OS X 12.4.0)

    Returns:
      str, The fragment of the User-Agent string.
    """
    # Below, there are examples of the value of platform.uname() per platform.
    # platform.release() is uname[2], platform.version() is uname[3].
    if self.operating_system == OperatingSystem.LINUX:
      # ('Linux', '<hostname goes here>', '3.2.5-gg1236',
      # '#1 SMP Tue May 21 02:35:06 PDT 2013', 'x86_64', 'x86_64')
      return '({name} {version})'.format(
          name=self.operating_system.name,
          version=self.operating_system.version)
    elif self.operating_system == OperatingSystem.WINDOWS:
      # ('Windows', '<hostname goes here>', '7', '6.1.7601', 'AMD64',
      # 'Intel64 Family 6 Model 45 Stepping 7, GenuineIntel')
      return '({name} NT {version})'.format(
          name=self.operating_system.name,
          version=self.operating_system.version)
    elif self.operating_system == OperatingSystem.MACOSX:
      # ('Darwin', '<hostname goes here>', '12.4.0',
      # 'Darwin Kernel Version 12.4.0: Wed May  1 17:57:12 PDT 2013;
      # root:xnu-2050.24.15~1/RELEASE_X86_64', 'x86_64', 'i386')
      format_string = '(Macintosh; {name} Mac OS X {version})'
      arch_string = (self.architecture.name
                     if self.architecture == Architecture.ppc else 'Intel')
      return format_string.format(
          name=arch_string,
          version=self.operating_system.version)
    else:
      return '()'

  def AsyncPopenArgs(self):
    """Returns the args for spawning an async process using Popen on this OS.

    Make sure the main process does not wait for the new process. On windows
    this means setting the 0x8 creation flag to detach the process.

    Killing a group leader kills the whole group. Setting creation flag 0x200 on
    Windows or running setsid on *nix makes sure the new process is in a new
    session with the new process the group leader. This means it can't be killed
    if the parent is killed.

    Finally, all file descriptors (FD) need to be closed so that waiting for the
    output of the main process does not inadvertently wait for the output of the
    new process, which means waiting for the termination of the new process.
    If the new process wants to write to a file, it can open new FDs.

    Returns:
      {str:}, The args for spawning an async process using Popen on this OS.
    """
    args = {}
    if self.operating_system == OperatingSystem.WINDOWS:
      args['close_fds'] = True  # This is enough to close _all_ FDs on windows.
      detached_process = 0x00000008
      create_new_process_group = 0x00000200
      # 0x008 | 0x200 == 0x208
      args['creationflags'] = detached_process | create_new_process_group
    else:
      # Killing a group leader kills the whole group.
      # Create a new session with the new process the group leader.
      if sys.version_info[0] == 3 and sys.version_info[1] > 8:
        args['start_new_session'] = True
      else:
        args['preexec_fn'] = os.setsid
      args['close_fds'] = True  # This closes all FDs _except_ 0, 1, 2 on *nix.
      args['stdin'] = subprocess.PIPE
      args['stdout'] = subprocess.PIPE
      args['stderr'] = subprocess.PIPE
    return args

  @staticmethod
  def IsActuallyM1ArmArchitecture():
    """Method that detects if platform is actually M1 Arm.

    This will return True even in the case where x86 Python is running under
    Rosetta 2. This will ONLY return true when running on a Macos M1 machine.
    Normal methods, for example "uname -a" will see x86_64 in the M1 case when
    Rosetta 2 is running, this method exists for when we want to know what the
    actual hardware is.

    Returns:
      True if M1 Arm detected, False otherwise.
    """
    cmd_args = ['sysctl', '-n', 'machdep.cpu.brand_string']
    try:
      proc = subprocess.Popen(
          cmd_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

      stdoutdata, _ = proc.communicate()
      if 'Apple M1' in encoding.Decode(stdoutdata):
        return True
    except:  # pylint: disable=bare-except
      pass
    return False


class PythonVersion(object):
  """Class to validate the Python version we are using.

  The Cloud CLI officially supports Python 3.8.

  However, many commands do work with Python 3.6, so we don't error out when
  users are using this (we consider it sometimes "compatible" but not
  "supported").
  """

  # See class docstring for descriptions of what these mean
  MIN_REQUIRED_PY3_VERSION = (3, 6)
  MIN_SUPPORTED_PY3_VERSION = (3, 8)
  MAX_SUPPORTED_PY3_VERSION = (3, 12)
  UPCOMING_SUNSET_PY3_VERSION = None
  UPCOMING_PY3_MIN_SUPPORTED_VERSION = None
  UPCOMING_PY3_DEPRECATION_DATE = None
  ENV_VAR_MESSAGE = """\

If you have a compatible Python interpreter installed, you can use it by setting
the CLOUDSDK_PYTHON environment variable to point to it.

"""

  def __init__(self, version=None):
    if version:
      self.version = version
    elif hasattr(sys, 'version_info'):
      self.version = sys.version_info[:2]
    else:
      self.version = None

  def InstallMacPythonMessage(self):
    if OperatingSystem.Current() != OperatingSystem.MACOSX:
      return ''
    return ('\nTo reinstall gcloud, run:\n'
            '    $ gcloud components reinstall\n\n'
            'This will also prompt to install a compatible version of Python.')

  def SupportedVersionMessage(self):
    return 'Please use Python version {0}.{1} and up.'.format(
        PythonVersion.MIN_SUPPORTED_PY3_VERSION[0],
        PythonVersion.MIN_SUPPORTED_PY3_VERSION[1])

  def UpcomingSupportedVersionMessage(self):
    return 'Please use Python version {0}.{1} and up.'.format(
        PythonVersion.UPCOMING_PY3_MIN_SUPPORTED_VERSION[0],
        PythonVersion.UPCOMING_PY3_MIN_SUPPORTED_VERSION[1],
    )

  def IsCompatible(self, raise_exception=False):
    """Ensure that the Python version we are using is compatible.

    This will print an error message if not compatible.

    Compatible versions are 3.6+.
    We don't guarantee support for 3.6 so we want to warn about it.

    Args:
      raise_exception: bool, True to raise an exception rather than printing
        the error and exiting.

    Raises:
      Error: If not compatible and raise_exception is True.

    Returns:
      bool, True if the version is valid, False otherwise.
    """
    error = None
    allow_py2 = (
        encoding.GetEncodedValue(
            os.environ, 'CLOUDSDK_ALLOW_PY2', 'False'
        ).lower()
        == 'true'
    )
    py2_error = False
    if not self.version:
      # We don't know the version, not a good sign.
      error = ('ERROR: Your current version of Python is not compatible with '
               'the Google Cloud CLI. {0}{1}\n'
               .format(self.SupportedVersionMessage(),
                       self.InstallMacPythonMessage()))
    elif self.version[0] < 3:
      # Python 2 Mode
      error = (
          'ERROR: Python 2 is not compatible with the Google '
          'Cloud CLI. {0}{1}\n'.format(self.SupportedVersionMessage(),
                                       self.InstallMacPythonMessage())
      )
      py2_error = True
    elif self.version < PythonVersion.MIN_REQUIRED_PY3_VERSION:
      # Python 3 Mode
      error = ('ERROR: Python {0}.{1} is not compatible with the Google '
               'Cloud CLI. {2}{3}\n'
               .format(self.version[0], self.version[1],
                       self.SupportedVersionMessage(),
                       self.InstallMacPythonMessage()))

    if error and allow_py2 and py2_error:
      sys.stderr.write(error)
      sys.stderr.write(PythonVersion.ENV_VAR_MESSAGE)
      return True
    elif error:
      if raise_exception:
        raise Error(error)
      sys.stderr.write(error)
      sys.stderr.write(PythonVersion.ENV_VAR_MESSAGE)
      return False

    # Warn that Python versions < MIN_SUPPORTED_PY3_VERSION are not supported.
    if self.version < self.MIN_SUPPORTED_PY3_VERSION:
      sys.stderr.write((
          'WARNING:  Python 3.{0}.x is no longer officially supported by the '
          'Google Cloud CLI\nand may not function correctly. {1}{2}').format(
              self.version[1],
              self.SupportedVersionMessage(), self.InstallMacPythonMessage()))
      sys.stderr.write('\n'+PythonVersion.ENV_VAR_MESSAGE)

    # Warn if python version is being deprecated soon.
    elif (PythonVersion.UPCOMING_PY3_MIN_SUPPORTED_VERSION and
          self.version <= PythonVersion.UPCOMING_PY3_MIN_SUPPORTED_VERSION):
      sys.stderr.write(
          """\
WARNING:  Python 3.{0}-3.{1} will be deprecated on {2}. {3}{4}""".format(
              PythonVersion.MIN_SUNSET_PY3_VERSION[1],
              PythonVersion.MAX_SUNSET_PY3_VERSION[1],
              PythonVersion.UPCOMING_PY3_DEPRECATION_DATE,
              self.UpcomingSupportedVersionMessage(),
              self.InstallMacPythonMessage()
          )
      )
      sys.stderr.write('\n'+PythonVersion.ENV_VAR_MESSAGE)

    return True
