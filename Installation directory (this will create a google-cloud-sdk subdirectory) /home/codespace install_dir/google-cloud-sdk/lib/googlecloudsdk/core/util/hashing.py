# -*- coding: utf-8 -*- #

# Copyright 2021 Google LLC. All Rights Reserved.
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
"""A module for generic hashing utilities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import hashlib


def get_md5(byte_string=b''):
  """Returns md5 object, avoiding incorrect FIPS error on Red Hat systems.

  Examples: get_md5(b'abc')
            get_md5(bytes('abc', encoding='utf-8'))

  Args:
    byte_string (bytes): String in bytes form to hash. Don't include for empty
      hash object, since md5(b'').digest() == md5().digest().

  Returns:
    md5 hash object.
  """
  try:
    return hashlib.md5(byte_string)
  except ValueError:
    # On Red Hat-based platforms, may catch a FIPS error.
    # "usedforsecurity" flag only available on Red Hat systems or Python 3.9+.
    # pylint:disable=unexpected-keyword-arg
    return hashlib.md5(byte_string, usedforsecurity=False)
    # pylint:enable=unexpected-keyword-arg
