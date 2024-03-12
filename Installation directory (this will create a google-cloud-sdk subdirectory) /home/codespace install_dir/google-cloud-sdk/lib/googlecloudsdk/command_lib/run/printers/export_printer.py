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
"""Printer for exporting k8s resources."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy

from googlecloudsdk.api_lib.run import k8s_object
from googlecloudsdk.core.resource import yaml_printer

_OMITTED_ANNOTATIONS = [
    k8s_object.SERVING_GROUP + '/creator',
    k8s_object.SERVING_GROUP + '/lastModifier',
    k8s_object.RUN_GROUP + '/client-name',
    k8s_object.RUN_GROUP + '/client-version',
    k8s_object.RUN_GROUP + '/creatorEmail',
    k8s_object.RUN_GROUP + '/lastModifierEmail',
    k8s_object.RUN_GROUP + '/operation-id'
]


EXPORT_PRINTER_FORMAT = 'export'


# To be replaced with the code that does gcloud export once that feature of
# Cloud SDK is ready.
# go/gcloud-export-import
class ExportPrinter(yaml_printer.YamlPrinter):
  """Printer for k8s_objects to export.

  Omits status information, and metadata that isn't consistent across
  deployments, like project or region.
  """

  def _AddRecord(self, record, delimit=True):
    record = self._FilterForExport(record)
    super(ExportPrinter, self)._AddRecord(record, delimit)

  def _FilterForExport(self, record):
    m = copy.deepcopy(record)

    meta = m.get('metadata')
    if meta:
      meta.pop('creationTimestamp', None)
      meta.pop('generation', None)
      meta.pop('resourceVersion', None)
      meta.pop('selfLink', None)
      meta.pop('uid', None)
      for k in _OMITTED_ANNOTATIONS:
        meta.get('annotations', {}).pop(k, None)

    m.pop('status', None)

    return m
