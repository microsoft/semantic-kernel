# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""CRM API common error handling."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from functools import wraps
from apitools.base.py import exceptions
from googlecloudsdk.api_lib.util import exceptions as api_exceptions


def EmitErrorDetails(func):
  """Decorates a function for better errors."""

  @wraps(func)
  def Wrapper(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except exceptions.HttpError as error:
      raise api_exceptions.HttpException(error, '{message}{details?\n{?}}')

  return Wrapper


def YieldErrorDetails(func):
  """Decorates a function which produces a generator for better errors."""

  @wraps(func)
  def Wrapper(*args, **kwargs):
    try:
      for i in func(*args, **kwargs):
        yield i
    except exceptions.HttpError as error:
      raise api_exceptions.HttpException(error, '{message}{details?\n{?}}')

  return Wrapper
