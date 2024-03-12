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
"""Simplify fully-qualified paths for compute."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


def Name(uri):
  """Get just the name of the object the uri refers to."""

  # Since the path is assumed valid, we can just take the last piece.
  return uri.split('/')[-1]


def ScopedSuffix(uri):
  """Get just the scoped part of the object the uri refers to."""

  # The path is assumed valid.
  if '/zones/' in uri:
    # This is zonally scoped. Return the part after zone/.
    return uri.split('/zones/')[-1]
  elif '/regions/' in uri:
    # This is regionally scoped. Return the part after regions/.
    return uri.split('/regions/')[-1]
  else:
    # This is globally scoped. Return the name.
    return Name(uri)


def ProjectSuffix(uri):
  """Get the entire relative path of the object the uri refers to."""

  # Get the part after projects. The argument is assumed valid.
  return uri.split('/projects/')[-1]
