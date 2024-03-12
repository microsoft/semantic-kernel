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

"""A module for diagnosing common problems caused by properties."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import config
from googlecloudsdk.core import properties
from googlecloudsdk.core.configurations import named_configs
from googlecloudsdk.core.diagnostics import check_base
from googlecloudsdk.core.diagnostics import diagnostic_base
import six


class PropertyDiagnostic(diagnostic_base.Diagnostic):
  """Diagnoses issues that may be caused by properties."""

  def __init__(self, ignore_hidden_property_allowlist):
    intro = ('Property diagnostic detects issues that may be caused by '
             'properties.')
    super(PropertyDiagnostic, self).__init__(
        intro=intro, title='Property diagnostic',
        checklist=[HiddenPropertiesChecker(ignore_hidden_property_allowlist)])


def _AllProperties():
  for section in properties.VALUES:
    for prop in section:
      yield prop


class HiddenPropertiesChecker(check_base.Checker):
  """Checks whether any hidden properties have been set."""

  _ALLOWLIST = (
      'metrics/environment',
  )

  def __init__(self, ignore_hidden_property_allowlist):
    self.ignore_hidden_property_allowlist = ignore_hidden_property_allowlist
    self.allowlist = set(
        (properties.VALUES.diagnostics.hidden_property_allowlist.Get() or '')
        .split(',')
    )
    self._properties_file = named_configs.ActivePropertiesFile.Load()

  @property
  def issue(self):
    return 'hidden properties'

  def Check(self, first_run=True):
    """Run hidden property check.

    Args:
      first_run: bool, True if first time this has been run this invocation.

    Returns:
      A tuple of (check_base.Result, fixer) where fixer is a function that can
        be used to fix a failed check, or None if the check passed or failed
        with no applicable fix.
    """
    failures = []
    for prop in _AllProperties():
      if prop.is_internal:
        continue
      if prop.is_hidden:
        fail = self._CheckHiddenProperty(prop)
        if fail:
          failures.append(fail)
    if failures:
      fail_message = self._ConstructMessageFromFailures(failures, first_run)
      result = check_base.Result(passed=False, message=fail_message,
                                 failures=failures)
      return result, None

    pass_message = 'Hidden Property Check {0}.'.format(
        'passed' if first_run else 'now passes')
    result = check_base.Result(passed=True, message=pass_message)
    return result, None

  def _CheckHiddenProperty(self, prop):
    if six.text_type(prop) in self._ALLOWLIST:
      return
    if (not self.ignore_hidden_property_allowlist and
        six.text_type(prop) in self.allowlist):
      return

    # pylint:disable=protected-access
    value = properties._GetPropertyWithoutCallback(prop, self._properties_file)
    if value is not None:
      msg = '[{0}]'.format(prop)
      return check_base.Failure(message=msg)

  def _ConstructMessageFromFailures(self, failures, first_run):
    message = 'Hidden Property Check {0}.\n'.format('failed' if first_run else
                                                    'still does not pass')
    if failures:
      message += 'The following hidden properties have been set:\n'
    for failure in failures:
      message += '    {0}\n'.format(failure.message)
    if first_run:
      message += ('Properties files\n'
                  '    User: {0}\n'
                  '    Installation: {1}\n'.format(
                      named_configs.ConfigurationStore.ActiveConfig().file_path,
                      config.Paths().installation_properties_path)
                 )
    return message
