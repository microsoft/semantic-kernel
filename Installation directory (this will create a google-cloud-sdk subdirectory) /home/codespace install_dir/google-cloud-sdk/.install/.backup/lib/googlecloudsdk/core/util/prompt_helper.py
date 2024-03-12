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
"""This module helps with prompting."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import abc

import os
import time
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files as file_utils

import six


class PromptRecordBase(six.with_metaclass(abc.ABCMeta, object)):
  """Base class to cache prompting results.

  Attributes:
    _cache_file_path: cache file path.
    dirty: bool, True if record in the cache file should be updated. Otherwise,
      False.
    last_prompt_time: Last time user was prompted.
  """

  def __init__(self, cache_file_path=None):
    self._cache_file_path = cache_file_path
    self._dirty = False

  def CacheFileExists(self):
    return os.path.isfile(self._cache_file_path)

  def SavePromptRecordToFile(self):
    """Serializes data to the cache file."""
    if not self._dirty:
      return
    with file_utils.FileWriter(self._cache_file_path) as f:
      yaml.dump(self._ToDictionary(), stream=f)
    self._dirty = False

  @abc.abstractmethod
  def _ToDictionary(self):
    pass

  @abc.abstractmethod
  def ReadPromptRecordFromFile(self):
    pass

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    self.SavePromptRecordToFile()

  @property
  def dirty(self):
    return self._dirty

  @property
  def last_prompt_time(self):
    return self._last_prompt_time

  @last_prompt_time.setter
  def last_prompt_time(self, value):
    self._last_prompt_time = value
    self._dirty = True


class OptInPromptRecord(PromptRecordBase):
  """Opt-in data usage record."""

  def __init__(self):
    super(OptInPromptRecord, self).__init__(
        cache_file_path=config.Paths().opt_in_prompting_cache_path)
    self._last_prompt_time = self.ReadPromptRecordFromFile()

  def _ToDictionary(self):
    res = {}
    if self._last_prompt_time:
      res['last_prompt_time'] = self._last_prompt_time
    return res

  def ReadPromptRecordFromFile(self):
    if not self.CacheFileExists():
      return None

    try:
      with file_utils.FileReader(self._cache_file_path) as f:
        data = yaml.load(f)
      return data.get('last_prompt_time', None)
    except Exception:  # pylint:disable=broad-except
      log.debug('Failed to parse opt-in prompt cache. '
                'Using empty cache instead.')
      return None


class BasePrompter(six.with_metaclass(abc.ABCMeta, object)):

  @abc.abstractmethod
  def Prompt(self):
    pass

  @abc.abstractmethod
  def ShouldPrompt(self):
    pass


class OptInPrompter(BasePrompter):
  """Prompter to opt-in in data usage."""

  PROMPT_INTERVAL = 86400 * 30 * 2  # 60 days
  MESSAGE = (
      "To help improve the quality of this product, we collect anonymized "
      "usage data and anonymized stacktraces when crashes are encountered; "
      "additional information is available at "
      "<https://cloud.google.com/sdk/usage-statistics>. This data is handled "
      "in accordance with our privacy policy "
      "<https://cloud.google.com/terms/cloud-privacy-notice>. You may choose "
      "to opt in this collection now (by choosing 'Y' at the below "
      "prompt), or at any time in the future by running the following "
      "command:\n\n"
      "    gcloud config set disable_usage_reporting false\n")

  def __init__(self):
    self.record = OptInPromptRecord()

  def Prompt(self):
    """Asks users to opt-in data usage report."""
    if not properties.IsDefaultUniverse():
      return

    if not self.record.CacheFileExists():
      with self.record as pr:
        pr.last_prompt_time = 0

    if self.ShouldPrompt():
      answer = console_io.PromptContinue(
          message=self.MESSAGE,
          prompt_string='Do you want to opt-in',
          default=False,
          throw_if_unattended=False,
          cancel_on_no=False)
      if answer:
        properties.PersistProperty(
            properties.VALUES.core.disable_usage_reporting, 'False')
      with self.record as pr:
        pr.last_prompt_time = time.time()

  def ShouldPrompt(self):
    """Checks whether to prompt or not."""
    if not (log.out.isatty() and log.err.isatty()):
      return False
    last_prompt_time = self.record.last_prompt_time
    now = time.time()
    if last_prompt_time and \
        (now - last_prompt_time) < self.PROMPT_INTERVAL:
      return False
    return True
