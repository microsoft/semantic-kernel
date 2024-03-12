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
"""Service-specific printer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import service
from googlecloudsdk.command_lib.kuberun import k8s_object_printer
from googlecloudsdk.command_lib.kuberun import revision_printer
from googlecloudsdk.command_lib.kuberun import traffic_printer
from googlecloudsdk.core.console import console_attr
from googlecloudsdk.core.resource import custom_printer_base as cp

SERVICE_PRINTER_FORMAT = 'service'


class ServicePrinter(cp.CustomPrinterBase):
  """Prints the run Service in a custom human-readable format.

  Format specific to Cloud Run services. Only available on Cloud Run commands
  that print services.
  """

  def _GetRevisionHeader(self, record):
    return console_attr.GetConsoleAttr().Emphasize('Revision {}'.format(
        record.status.latestCreatedRevisionName))

  def _RevisionPrinters(self, record):
    """Adds printers for the revision."""
    return cp.Lines([
        self._GetRevisionHeader(record),
        k8s_object_printer.FormatLabels(record.template.labels),
        revision_printer.RevisionPrinter().TransformSpec(record.template),
    ])

  def Transform(self, service_dict):
    """Transform a service into the output structure of marker classes.

    Args:
      service_dict: dictionary object representing a service unmarshalled from
        json

    Returns:
      marker class of the formatted service object.
    """
    record = service.Service(service_dict)
    fmt = cp.Lines([
        k8s_object_printer.FormatHeader(record),
        k8s_object_printer.FormatLabels(record.labels), ' ',
        traffic_printer.TransformRouteFields(record), ' ',
        cp.Labeled([(k8s_object_printer.FormatLastUpdated(record),
                     self._RevisionPrinters(record))]),
        k8s_object_printer.FormatReadyMessage(record)
    ])
    return fmt
