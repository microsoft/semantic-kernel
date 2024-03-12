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
"""Gcloud auth token for the kuberun go binary.

The gcloud auth token obtained for the account in use and returned as a simple
JSON like:
{ 'AuthToken': '<TOKEN>' }
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core import exceptions
from googlecloudsdk.core.credentials import store as c_store


class KubeRunAuthException(exceptions.Error):
  """Base Exception for auth issues raised by gcloud kuberun surface."""


def GetAuthToken(account=None):
  """Generate a JSON object containing the current gcloud auth token."""
  try:
    access_token = c_store.GetFreshAccessToken(account)
    output = {
        'AuthToken': access_token,
    }
  except Exception as e:  # pylint: disable=broad-except
    raise KubeRunAuthException(
        'Error retrieving auth credentials for {account}: {error}. '.format(
            account=account, error=e))
  return json.dumps(output, sort_keys=True)
