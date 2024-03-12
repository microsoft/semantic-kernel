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

"""Base SSHTroubleshooter class for each category of ssh troubleshooting check."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

import six


@six.add_metaclass(abc.ABCMeta)
class SshTroubleshooter(object):
  """A class whose instance is a ssh troubleshooter.

  Test authors should subclass Troubleshooter for each troubleshooter
  subcategory.
  """

  project = None
  zone = None
  instance = None

  def __init__(self):
    """Initialize with project and instance object, and zone.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def check_prerequisite(self):
    """Hook method for checking prerequisite for troubleshooting before troubleshoot action.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def cleanup_resources(self):
    """Hook method for cleaning troubleshooting resource after troubleshooting action.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def troubleshoot(self):
    """Hook method for troubleshooting action."""
    raise NotImplementedError

  def __call__(self):
    self.run()

  def run(self):
    self.check_prerequisite()
    self.troubleshoot()
    self.cleanup_resources()
