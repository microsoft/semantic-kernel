# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""This file provides util to decorate output of functions command."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools
from apitools.base.py import encoding


def decorate_v1_function_with_v2_api_info(v1_func, v2_func):
  # type: (v1_messages.CloudFunction, v2_messages.Function) -> dict[str, Any]
  """Decorate gen1 function in v1 API format with additional info from its v2 API format.

  Currently only the `environment` and `upgradeInfo` fields are copied over.

  Args:
    v1_func: A gen1 function retrieved from v1 API.
    v2_func: The same gen1 function but as returned by the v2 API.

  Returns:
    The given Gen1 function encoded as a dict in the v1 format but with the
      `upgradeInfo` and `environment` properties from the v2 format added.
  """
  v1_dict = encoding.MessageToDict(v1_func)
  if v2_func and v2_func.environment:
    v1_dict["environment"] = str(v2_func.environment)
  if v2_func and v2_func.upgradeInfo:
    v1_dict["upgradeInfo"] = encoding.MessageToDict(v2_func.upgradeInfo)
  return v1_dict


def decorate_v1_generator_with_v2_api_info(v1_generator, v2_generator):
  """Decorate gen1 functions in v1 API format with additional info from its v2 API format.

  Currently only the `environment` and `upgradeInfo` fields are copied over.

  Args:
    v1_generator: Generator, generating gen1 function retrieved from v1 API.
    v2_generator: Generator, generating gen1 function retrieved from v2 API.

  Yields:
    Gen1 function encoded as a dict with upgrade info decorated.
  """
  gen1_generator = sorted(
      itertools.chain(v1_generator, v2_generator), key=lambda f: f.name
  )
  for _, func_gen in itertools.groupby(gen1_generator, key=lambda f: f.name):
    func_list = list(func_gen)
    if len(func_list) < 2:
      # If this is v2 function, upgrade info should have been included.
      # No decoration needed. Yield directly.
      # If this is v1 function, no corresponding v2 function is found,
      # so there is no upgrade info we have use to decorate. Yield directly.
      yield func_list[0]
    else:
      v1_func, v2_func = func_list
      yield decorate_v1_function_with_v2_api_info(v1_func, v2_func)
