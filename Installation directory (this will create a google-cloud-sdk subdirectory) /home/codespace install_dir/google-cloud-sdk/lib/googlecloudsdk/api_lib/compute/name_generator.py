# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""A module for generating resource names."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import random
import string
import six
from six.moves import range  # pylint: disable=redefined-builtin

_LENGTH = 12
_BEGIN_ALPHABET = string.ascii_lowercase
_ALPHABET = _BEGIN_ALPHABET + string.digits


def GenerateRandomName():
  """Generates a random string.

  Returns:
    The returned string will be 12 characters long and will begin with
    a lowercase letter followed by 11 characters drawn from the set
    [a-z0-9].
  """
  buf = io.StringIO()
  buf.write(six.text_type(random.choice(_BEGIN_ALPHABET)))
  for _ in range(_LENGTH - 1):
    buf.write(six.text_type(random.choice(_ALPHABET)))
  return buf.getvalue()
