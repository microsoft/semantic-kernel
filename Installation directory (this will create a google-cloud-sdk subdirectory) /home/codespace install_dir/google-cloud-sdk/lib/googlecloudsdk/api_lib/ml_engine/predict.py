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
"""Utilities for dealing with ML predict API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core.credentials import requests

from six.moves import http_client as httplib


class InstancesEncodeError(core_exceptions.Error):
  """Indicates that error occurs while decoding the instances in http body."""
  pass


class HttpRequestFailError(core_exceptions.Error):
  """Indicates that the http request fails in some way."""
  pass


def _GetPrediction(url, body, headers):
  """Make http request to get prediction results."""
  response = requests.GetSession().request(
      'POST', url, data=body, headers=headers)
  return response.status_code, response.text


def Predict(model_or_version_ref, instances, signature_name=None):
  """Performs online prediction on the input data file.

  Args:
      model_or_version_ref: a Resource representing either a model or a version.
      instances: a list of JSON or UTF-8 encoded instances to perform
          prediction on.
      signature_name: name of input/output signature in the TF meta graph.

  Returns:
      A json object that contains predictions.

  Raises:
      HttpRequestFailError: if error happens with http request, or parsing
          the http response.
  """
  url = model_or_version_ref.SelfLink() + ':predict'
  # Construct the body for the predict request.
  headers = {'Content-Type': 'application/json'}
  content = {'instances': instances}
  if signature_name:
    content['signature_name'] = signature_name
  try:
    body = json.dumps(content, sort_keys=True)
  except (UnicodeDecodeError, TypeError):
    # Python 2: UnicodeDecode Error, Python 3: TypeError
    raise InstancesEncodeError('Instances cannot be JSON encoded, probably '
                               'because the input is not utf-8 encoded.')

  # Workaround since gcloud cannot handle HttpBody properly, see b/31403673
  response_status, response_body = _GetPrediction(url, body, headers)
  if int(response_status) != httplib.OK:
    raise HttpRequestFailError('HTTP request failed. Response: ' +
                               response_body)
  try:
    return json.loads(response_body)
  except ValueError:
    raise HttpRequestFailError('No JSON object could be decoded from the '
                               'HTTP response body: ' + response_body)


def Explain(model_or_version_ref, instances):
  """Performs online explanation on the input data file.

  Args:
      model_or_version_ref: a Resource representing either a model or a version.
      instances: a list of JSON or UTF-8 encoded instances to perform
          prediction on.

  Returns:
      A json object that contains explanations.

  Raises:
      HttpRequestFailError: if error happens with http request, or parsing
          the http response.
  """
  url = model_or_version_ref.SelfLink() + ':explain'
  # Construct the body for the explain request.
  headers = {'Content-Type': 'application/json'}
  content = {'instances': instances}
  try:
    body = json.dumps(content, sort_keys=True)
  except (UnicodeDecodeError, TypeError):
    # Python 2: UnicodeDecode Error, Python 3: TypeError
    raise InstancesEncodeError('Instances cannot be JSON encoded, probably '
                               'because the input is not utf-8 encoded.')

  # Workaround since gcloud cannot handle HttpBody properly, see b/31403673
  response_status, response_body = _GetPrediction(url, body, headers)
  if int(response_status) != httplib.OK:
    raise HttpRequestFailError('HTTP request failed. Response: ' +
                               response_body)
  try:
    return json.loads(response_body)
  except ValueError:
    raise HttpRequestFailError('No JSON object could be decoded from the '
                               'HTTP response body: ' + response_body)
