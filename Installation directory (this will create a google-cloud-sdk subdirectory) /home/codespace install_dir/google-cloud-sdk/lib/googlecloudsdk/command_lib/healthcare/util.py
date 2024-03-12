# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""General utilties for Cloud Healthcare commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis


# Returns a function that inserts an empty FHIR config object (of the given API
# version) when the flag is set to true.
def InsertEmptyFhirConfig(api_version):
  def VersionedInsertEmptyFhirConfig(flag):
    if not flag:
      return None
    messages = apis.GetMessagesModule('healthcare', api_version)
    return messages.FhirConfig()
  return VersionedInsertEmptyFhirConfig


# Returns a function that inserts an AnnotationConfig in DeidentifyConfig with
# 'store_quote' field set to True.
def InsertAnnotationConfig(api_version):
  def VersionedInsertAnnotationConfig(annotation_store):
    if not annotation_store:
      return None
    messages = apis.GetMessagesModule('healthcare', api_version)
    return messages.AnnotationConfig(
        annotationStoreName=annotation_store, storeQuote=True)
  return VersionedInsertAnnotationConfig


def InsertDicomStreamConfig(api_version):
  """Returns a function that inserts a DicomStreamingConfig of a Dicom Store.

  Args:
    api_version: the version of the API that is currently being used.

  Returns:
    A DicomStreamConfig object with provided BigQueryDestinations.
  """
  def VersionedInsertDicomStreamConfig(arg):
    if not arg:
      return None
    bq_destinations = arg.split(',')
    messages = apis.GetMessagesModule('healthcare', api_version)
    stream_configs = []
    if api_version == 'v1alpha2':
      for dest in bq_destinations:
        stream_configs.append(messages.GoogleCloudHealthcareV1alpha2DicomStreamConfig(
            bigqueryDestination=
            messages.GoogleCloudHealthcareV1alpha2DicomBigQueryDestination(
                tableUri=dest)))
    elif api_version == 'v1beta1':
      for dest in bq_destinations:
        stream_configs.append(messages.GoogleCloudHealthcareV1beta1DicomStreamConfig(
            bigqueryDestination=
            messages.GoogleCloudHealthcareV1beta1DicomBigQueryDestination(
                tableUri=dest)))
    else:
      for dest in bq_destinations:
        stream_configs.append(messages.GoogleCloudHealthcareV1DicomStreamConfig(
            bigqueryDestination=
            messages.GoogleCloudHealthcareV1DicomBigQueryDestination(
                tableUri=dest)))
    return stream_configs
  return VersionedInsertDicomStreamConfig
