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

"""Runtime-config resource transforms and symbols dict.

NOTICE: Each TransformFoo() method is the implementation of a foo() transform
function. Even though the implementation here is in Python the usage in resource
projection and filter expressions is language agnostic. This affects the
Pythonicness of the Transform*() methods:
  (1) The docstrings are used to generate external user documentation.
  (2) The method prototypes are included in the documentation. In particular the
      prototype formal parameter names are stylized for the documentation.
  (3) The types of some args, like r, are not fixed until runtime. Other args
      may have either a base type value or string representation of that type.
      It is up to the transform implementation to silently do the string=>type
      conversions. That's why you may see e.g. int(arg) in some of the methods.
  (4) Unless it is documented to do so, a transform function must not raise any
      exceptions. The `undefined' arg is used to handle all unusual conditions,
      including ones that would raise exceptions.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

# The DEADLINE_EXCEEDED error code.
DEADLINE_EXCEEDED = 4


def TransformWaiterStatus(r, undefined=''):
  """Returns a short description of the status of a waiter or waiter operation.

  Status will be one of WAITING, SUCCESS, FAILURE, or TIMEOUT.

  Args:
    r: a JSON-serializable object
    undefined: Returns this value if the resource status cannot be determined.

  Returns:
    One of WAITING, SUCCESS, FAILURE, or TIMEOUT

  Example:
    `--format="table(name, status())"`:::
    Displays the status in table column two.
  """
  if not isinstance(r, dict):
    return undefined

  if not r.get('done'):
    return 'WAITING'

  error = r.get('error')
  if not error:
    return 'SUCCESS'

  if error.get('code') == DEADLINE_EXCEEDED:
    return 'TIMEOUT'
  else:
    return 'FAILURE'


_TRANSFORMS = {
    'waiter_status': TransformWaiterStatus,
}


def GetTransforms():
  """Returns the runtimeconfig-specific resource transform symbol table."""
  return _TRANSFORMS
