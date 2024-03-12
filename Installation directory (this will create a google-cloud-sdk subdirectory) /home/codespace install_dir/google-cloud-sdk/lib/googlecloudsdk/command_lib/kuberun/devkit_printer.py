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
"""DevKit-specific printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.core.resource import custom_printer_base as cp


DEVKIT_PRINTER_FORMAT = 'devkit'


class DevKitPrinter(cp.CustomPrinterBase):
  """Prints the kuberun DevKit custom human-readable format.
  """

  def _ComponentTable(self, record):
    rows = [(x.name, str(x.event_input), x.description) for x in
            record.components]
    return cp.Table([('NAME', 'TAKES CE-INPUT', 'DESCRIPTION')] + rows)

  def Transform(self, record):
    """Transform a service into the output structure of marker classes."""
    return cp.Labeled([
        ('Name', record.name),
        ('Version', record.version),
        ('Description', record.description),
        ('Supported Components', self._ComponentTable(record)),
    ])
