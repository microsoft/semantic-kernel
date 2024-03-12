# -*- coding: utf-8 -*-
# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Additional help about CRC32C and installing crcmod."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from gslib.help_provider import HelpProvider

_DETAILED_HELP_TEXT = ("""
<B>OVERVIEW</B>
  Google Cloud Storage provides a cyclic redundancy check (CRC) header that
  allows clients to verify the integrity of object contents. For non-composite
  objects Google Cloud Storage also provides an MD5 header to allow clients to
  verify object integrity, but for composite objects only the CRC is available.
  gsutil automatically performs integrity checks on all uploads and downloads.
  Additionally, you can use the ``gsutil hash`` command to calculate a CRC for
  any local file.

  The CRC variant used by Google Cloud Storage is called CRC32C (Castagnoli),
  which is not available in the standard Python distribution. The implementation
  of CRC32C used by gsutil is provided by a third-party Python module called
  `crcmod <https://pypi.python.org/pypi/crcmod>`_.

  The crcmod module contains a pure-Python implementation of CRC32C, but using
  it results in slow checksum computation and subsequently very poor
  performance. A Python C extension is also provided by crcmod, which requires
  compiling into a binary module for use. gsutil ships with a precompiled
  crcmod C extension for macOS; for other platforms, see the installation
  instructions below.

  At the end of each copy operation, the ``gsutil cp``, ``gsutil mv``, and
  ``gsutil rsync`` commands validate that the checksum of the source
  file/object matches the checksum of the destination file/object. If the
  checksums do not match, gsutil will delete the invalid copy and print a
  warning message. This very rarely happens, but if it does, you should
  retry the operation.


<B>CONFIGURATION</B>
  To determine if the compiled version of crcmod is available in your Python
  environment, you can inspect the output of the ``gsutil version`` command for
  the "compiled crcmod" entry:

    $ gsutil version -l
    ...
    compiled crcmod: True
    ...

  If your crcmod library is compiled to a native binary, this value will be
  True. If using the pure-Python version, the value will be False.

  To control gsutil's behavior in response to crcmod's status, you can set the
  ``check_hashes`` variable in your `boto configuration file
  <https://cloud.google.com/storage/docs/boto-gsutil>`_. For details on this
  variable, see the surrounding comments in your boto configuration file. If
  ``check_hashes`` is not present in your configuration file, regenerate the
  file by running ``gsutil config`` with the appropriate ``-e`` or ``-a`` flag.


<B>INSTALLATION</B>
  These installation instructions assume that:

  -  You have ``pip`` installed. Consult the `pip installation instructions
     <https://pip.pypa.io/en/stable/installing/>`_ for details on how
     to install ``pip``.
  -  Your installation of ``pip`` can be found in your ``PATH`` environment
     variable. If it cannot, you may need to replace ``pip3`` in the commands
     below with the full path to the executable.
  -  You are installing the crcmod package for use with your system installation
     of Python, and thus use the ``sudo`` command. If installing crcmod for a
     different Python environment (e.g. in a virtualenv), you should omit
     ``sudo`` from the commands below.
  -  You are using a Python 3 version with gsutil. You can determine which
     Python version gsutil is using by running ``gsutil version -l`` and looking
     for the ``python version: 2.x.x`` or ``python version: 3.x.x`` line.

  CentOS, RHEL, and Fedora
  ------------------------

  To compile and install crcmod:

    yum install gcc python3-devel python3-setuptools redhat-rpm-config
    sudo pip3 uninstall crcmod
    sudo pip3 install --no-cache-dir -U crcmod

  Debian and Ubuntu
  -----------------

  To compile and install crcmod:

    sudo apt-get install gcc python3-dev python3-setuptools
    sudo pip3 uninstall crcmod
    sudo pip3 install --no-cache-dir -U crcmod

  Enterprise SUSE
  -----------------

  To compile and install crcmod when using Enterprise SUSE for SAP 12:

    sudo zypper install gcc python-devel
    sudo pip uninstall crcmod
    sudo pip install --no-cache-dir -U crcmod
    
  To compile and install crcmod when using Enterprise SUSE for SAP 15:

    sudo zypper install gcc python3-devel
    sudo pip uninstall crcmod
    sudo pip install --no-cache-dir -U crcmod

  macOS
  -----

  gsutil distributes a pre-compiled version of crcmod for macOS, so you shouldn't
  need to compile and install it yourself. If for some reason the pre-compiled
  version is not being detected, please let the Google Cloud Storage team know
  (see ``gsutil help support``).

  To compile manually on macOS, you will first need to install
  `Xcode <https://developer.apple.com/xcode/>`_ and then run:

    pip3 install -U crcmod

  Windows
  -------

  An installer is available for the compiled version of crcmod from the Python
  Package Index (PyPi) at the following URL:

  https://pypi.python.org/pypi/crcmod/1.7

  NOTE: If you have installed crcmod and gsutil hasn't detected it, it may have
  been installed to the wrong directory. It should be located at
  <python_dir>\\files\\Lib\\site-packages\\crcmod\\

  In some cases the installer will incorrectly install to
  <python_dir>\\Lib\\site-packages\\crcmod\\

  Manually copying the crcmod directory to the correct location should resolve
  the issue.
""")


class CommandOptions(HelpProvider):
  """Additional help about CRC32C and installing crcmod."""

  # Help specification. See help_provider.py for documentation.
  help_spec = HelpProvider.HelpSpec(
      help_name='crc32c',
      help_name_aliases=['crc32', 'crc', 'crcmod'],
      help_type='additional_help',
      help_one_line_summary='CRC32C and Installing crcmod',
      help_text=_DETAILED_HELP_TEXT,
      subcommand_help_text={},
  )
