# Copyright 2017 Google Inc. All Rights Reserved.
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
"""This module contains utilities for monitoring client side calls."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import abc
import six



class Context(six.with_metaclass(abc.ABCMeta, object)):
  """Interface for implementations of client monitoring context manager.

  All client operations are executed inside this context.
  """

  @abc.abstractmethod
  def __init__(self, operation):
    pass

  @abc.abstractmethod
  def __enter__(self):
    return self

  @abc.abstractmethod
  def __exit__(self, exc_type,
               exc_value,
               traceback):

    pass


class Nop(Context):
  """Default implementation of Context that does nothing."""

  # pylint: disable=useless-super-delegation
  def __init__(self, operation):
    super(Nop, self).__init__(operation)

  def __enter__(self):
    return self

  def __exit__(self, exc_type,
               exc_value,
               traceback):
    pass
