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
"""Utilities used by gcloud functions call commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import parser_extensions
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests as core_requests
from googlecloudsdk.core.util import times


_CONTENT_TYPE = 'Content-Type'

# Required and Optional CloudEvent attributes
# https://github.com/cloudevents/spec/blob/v1.0.1/spec.md
_FIELDS = (
    'id', 'source', 'specversion', 'type', 'dataschema', 'subject', 'time'
)

# v2 HTTP triggered functions interpret an empty Content-Type header as leaving
# the request body empty, therefore default the content type as json.
_DEFAULT_HEADERS = {_CONTENT_TYPE: 'application/json'}


def _StructuredToBinaryData(request_data_json):
  """Convert CloudEvents structured format to binary format.

  Args:
    request_data_json: dict, the parsed request body data

  Returns:
    cloudevent_data: str, the CloudEvent expected data with attributes in header
    cloudevent_headers: dict, the CloudEvent headers
  """

  cloudevent_headers = {}
  cloudevent_data = None

  for key, value in list(request_data_json.items()):
    normalized_key = key.lower()
    if normalized_key == 'data':
      cloudevent_data = value
    elif normalized_key in _FIELDS:
      cloudevent_headers['ce-'+normalized_key] = value
    elif normalized_key == 'datacontenttype':
      cloudevent_headers[_CONTENT_TYPE] = value
    else:
      cloudevent_headers[normalized_key] = value

  if _CONTENT_TYPE not in cloudevent_headers:
    cloudevent_headers[_CONTENT_TYPE] = 'application/json'
  return json.dumps(cloudevent_data), cloudevent_headers


def MakePostRequest(url, args, extra_headers=None):
  # type:(str, parser_extensions.Namespace, dict[str, str]) -> str
  """Makes an HTTP Post Request to the specified url with data and headers from args.

  Args:
    url: The URL to send the post request to
    args: The arguments from the command line parser
    extra_headers: Extra headers to add to the HTTP post request

  Returns:
    str: The HTTP response content
  """

  request_data = None
  headers = _DEFAULT_HEADERS
  if args.data:
    request_data = args.data
    headers = _DEFAULT_HEADERS
  elif args.cloud_event:
    request_data, headers = _StructuredToBinaryData(
        json.loads(args.cloud_event))

  if extra_headers:
    headers = dict(headers.items() | extra_headers.items())

  requests_session = core_requests.GetSession()
  response = requests_session.post(
      url=url,
      data=request_data,
      headers=headers)
  response.raise_for_status()
  return response.content


def UpdateHttpTimeout(args, function, api_version, release_track):
  """Update core/http_timeout using args and function timeout.

  Args:
    args: The arguments from the command line parser
    function: function definition
    api_version: v1 or v2
    release_track: ALPHA, BETA, or GA
  """
  if release_track in [base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA]:
    timeout = 540 if api_version == 'v1' else 3600
    if args.timeout:
      timeout = int(args.timeout)
    elif api_version == 'v1' and function.timeout:
      timeout = int(
          times.ParseDuration(
              function.timeout, default_suffix='s'
          ).total_seconds
          + 30
      )
    elif (
        api_version == 'v2'
        and function.serviceConfig
        and function.serviceConfig.timeoutSeconds
    ):
      timeout = int(function.serviceConfig.timeoutSeconds) + 30
    properties.VALUES.core.http_timeout.Set(timeout)
