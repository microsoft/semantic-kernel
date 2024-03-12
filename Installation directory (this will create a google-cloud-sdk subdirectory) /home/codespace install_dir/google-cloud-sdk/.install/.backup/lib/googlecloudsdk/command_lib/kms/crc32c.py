# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Helpers for calculating CRC32C checksums."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import gcloud_crcmod as crcmod
import six


def Crc32c(data):
  """Calculates the CRC32C checksum of the provided data.

  Args:
    data: the bytes over which the checksum should be calculated.

  Returns:
    An int representing the CRC32C checksum of the provided bytes.
  """
  crc32c_fun = crcmod.predefined.mkPredefinedCrcFun('crc-32c')
  return crc32c_fun(six.ensure_binary(data))


def Crc32cMatches(data, data_crc32c):
  """Checks that the CRC32C checksum of the provided data matches the provided checksum.

  Args:
    data: bytes over which the checksum should be calculated.
    data_crc32c: int checksum against which data's checksum will be compared.

  Returns:
    True iff both checksums match.
  """
  return Crc32c(data) == data_crc32c
