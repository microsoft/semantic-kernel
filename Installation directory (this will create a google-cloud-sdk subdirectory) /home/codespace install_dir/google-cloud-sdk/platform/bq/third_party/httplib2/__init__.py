# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Shim to enable run-time selection of httplib2 library version.

It is packaged into the public BQCLI using get_bq_public_libs.py.

Depending upon the system's Python version, the file imports all contents of
httplib2 under python2 or python3 directories.
"""

import sys

# pylint: disable=g-import-not-at-top, wildcard-import
if sys.version_info.major == 2 and sys.version_info.minor >= 7:
  import python2
  del python2.__all__
  from .python2 import *
elif sys.version_info.major >= 3:
  import httplib2.python3
  del python3.__all__  # pylint: disable=undefined-variable
  from .python3 import *
else:
  raise ImportError('Python < 2.7 is unsupported.')
# pylint: enable=g-import-not-at-top, wildcard-import
