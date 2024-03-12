# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Implementation of CloudApi for GCS using boto3."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.storage.s3_xml import client as s3_xml_client
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.core import properties


# pylint:disable=abstract-method
class XmlClient(s3_xml_client.S3XmlClient):
  """GCS XML client."""

  scheme = storage_url.ProviderPrefix.GCS

  def __init__(self):
    storage = properties.VALUES.storage

    self.access_key_id = storage.gs_xml_access_key_id.Get()
    self.access_key_secret = storage.gs_xml_secret_access_key.Get()
    self.endpoint_url = storage.gs_xml_endpoint_url.Get()

    self.client = self.create_client()
