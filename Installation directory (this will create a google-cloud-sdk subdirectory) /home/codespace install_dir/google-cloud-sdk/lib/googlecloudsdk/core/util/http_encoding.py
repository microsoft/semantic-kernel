# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Retry logic for HTTP exceptions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def Encode(s):
  """Return bytes objects encoded for HTTP headers / payload."""
  if s is None:
    return s
  return s.encode('utf-8')


def Decode(s):
  """Return text objects decoded from HTTP headers / payload."""
  if s is None:
    return s
  return s.decode('utf-8')
