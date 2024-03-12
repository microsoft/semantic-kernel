# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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


"""Container resource transforms and symbols dict.

A resource transform function converts a JSON-serializable resource to a string
value. This module contains built-in transform functions that may be used in
resource projection and filter expressions.

NOTICE: Each TransformFoo() method is the implementation of a foo() transform
function. Even though the implementation here is in Python the usage in resource
projection and filter expressions is language agnostic. This affects the
Pythonicness of the Transform*() methods:
  (1) The docstrings are used to generate external user documentation.
  (2) The method prototypes are included in the documentation. In particular the
      prototype formal parameter names are stylized for the documentation.
  (3) The 'r', 'kwargs', and 'projection' args are not included in the external
      documentation. Docstring descriptions, other than the Args: line for the
      arg itself, should not mention these args. Assume the reader knows the
      specific item the transform is being applied to. When in doubt refer to
      the output of $ gcloud topic projections.
  (4) The types of some args, like r, are not fixed until runtime. Other args
      may have either a base type value or string representation of that type.
      It is up to the transform implementation to silently do the string=>type
      conversions. That's why you may see e.g. int(arg) in some of the methods.
  (5) Unless it is documented to do so, a transform function must not raise any
      exceptions related to the resource r. The `undefined' arg is used to
      handle all unusual conditions, including ones that would raise exceptions.
      Exceptions for arguments explicitly under the caller's control are OK.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core.util import times


def ParseExpireTime(s):
  """Return timedelta TTL for a cluster.

  Args:
    s: expireTime string timestamp in RFC3339 format.
  Returns:
    datetime.timedelta of time remaining before cluster expiration.
  Raises:
    TypeError, ValueError if time could not be parsed.
  """
  if not s:
    return None
  expire_dt = times.ParseDateTime(s)
  if not expire_dt:
    return None
  return expire_dt - times.Now(expire_dt.tzinfo)


def TransformMasterVersion(r, undefined=''):
  """Returns the formatted master version.

  Args:
    r: JSON-serializable object.
    undefined: Returns this value if the resource cannot be formatted.
  Returns:
    The formatted master version.
  """
  version = r.get('currentMasterVersion', None)
  if version is None:
    return undefined
  if r.get('enableKubernetesAlpha', False):
    version = '{0} ALPHA'.format(version)
  try:
    time_left = ParseExpireTime(r.get('expireTime', None))
    if time_left is not None:
      if time_left.days > constants.EXPIRE_WARNING_DAYS:
        version += ' ({0} days left)'.format(time_left.days)
      else:
        version += ' (! {0} days left !)'.format(time_left.days)
    return version
  except times.Error:
    return undefined
  return version


_TRANSFORMS = {
    'master_version': TransformMasterVersion,
}


def GetTransforms():
  """Returns the compute specific resource transform symbol table."""
  return _TRANSFORMS
