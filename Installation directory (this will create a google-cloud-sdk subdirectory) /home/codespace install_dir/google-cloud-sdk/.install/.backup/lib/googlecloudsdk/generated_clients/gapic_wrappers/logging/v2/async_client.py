# -*- coding: utf-8 -*-
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
"""Logging gRPC client. This class is automatically generated."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import gapic_util
from googlecloudsdk.generated_clients.gapic_clients import logging_v2


class GapicWrapperClient(object):
  """Logging async client."""
  types = logging_v2.types

  def __init__(self, credentials, **kwargs):
    """
    Instantiates the GapicWrapperClient for logging_v2.

    Args:
      credentials: google.auth.credentials.Credentials, the credentials to use.
      **kwargs: Additional kwargs to pass to gapic.MakeClient.

    Returns:
        GapicWrapperClient
    """
    self.credentials = credentials
    self.config = gapic_util.MakeAsyncClient(
        logging_v2.services.config_service_v2.async_client.ConfigServiceV2AsyncClient,
        credentials, **kwargs)
    self.logging = gapic_util.MakeAsyncClient(
        logging_v2.services.logging_service_v2.async_client.LoggingServiceV2AsyncClient,
        credentials, **kwargs)
    self.metrics = gapic_util.MakeAsyncClient(
        logging_v2.services.metrics_service_v2.async_client.MetricsServiceV2AsyncClient,
        credentials, **kwargs)
