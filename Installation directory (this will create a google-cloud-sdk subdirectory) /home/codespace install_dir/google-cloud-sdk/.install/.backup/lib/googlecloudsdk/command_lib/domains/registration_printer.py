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
"""Cloud Domains Registration-specific printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.core.resource import custom_printer_base as cp
from googlecloudsdk.core.resource import yaml_printer as yp

REGISTRATION_PRINTER_FORMAT = 'registration'


class RegistrationPrinter(cp.CustomPrinterBase):
  """Prints the Cloud Domains registration in YAML format with custom fields order."""

  _KNOWN_FIELDS_BY_IMPORTANCE = [
      'name', 'createTime', 'domainName', 'state', 'issues', 'expireTime',
      'labels', 'managementSettings', 'dnsSettings', 'contactSettings',
      'pendingContactSettings', 'supportedPrivacy'
  ]

  _KNOWN_REPEATED_FIELDS = ['issues', 'supportedPrivacy']

  def _ClearField(self, registration, field):
    if field in self._KNOWN_REPEATED_FIELDS:
      setattr(registration, field, [])
    else:
      setattr(registration, field, None)

  def _TransformKnownFields(self, printer, registration):
    for field in self._KNOWN_FIELDS_BY_IMPORTANCE:
      record = getattr(registration, field, None)
      if record:
        printer.AddRecord({field: record}, delimit=False)

  def _TransformRemainingFields(self, printer, registration):
    for field in self._KNOWN_FIELDS_BY_IMPORTANCE:
      if getattr(registration, field, None):
        self._ClearField(registration, field)

    # printer.AddRecord prints {} for empty resources in scenario tests.
    # That's why we only call it when there is something to print.
    finished = True
    if registration.all_unrecognized_fields():
      finished = False
    for f in registration.all_fields():
      if getattr(registration, f.name):
        finished = False
    if not finished:
      printer.AddRecord(registration, delimit=False)

  def Transform(self, registration):
    """Transform a registration into a YAML output."""
    yaml = yp.YamlPrinter()
    self._TransformKnownFields(yaml, registration)
    self._TransformRemainingFields(yaml, registration)
