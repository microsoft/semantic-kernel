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
"""Protocol adapter class to allow requests to GET file:// URLs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
import os

from googlecloudsdk.core.util import files
import requests


class LocalFileAdapter(requests.adapters.BaseAdapter):
  """Protocol Adapter to allow Requests to GET file:// URLs."""

  @staticmethod
  def _chkpath(method, path):
    """Return an HTTP status for the given filesystem path."""
    if method.lower() not in ("get", "head"):
      return requests.codes.not_allowed, "Method Not Allowed"
    elif os.path.isdir(path):
      return requests.codes.bad_request, "Path Not A File"
    elif not os.path.isfile(path):
      return requests.codes.not_found, "File Not Found"
    elif not os.access(path, os.R_OK):
      return requests.codes.forbidden, "Access Denied"
    else:
      return requests.codes.ok, "OK"

  def send(self, req, **kwargs):  # pylint: disable=unused-argument
    """Return the file specified by the given request.

    Args:
      req: PreparedRequest
      **kwargs: kwargs can include values for headers, timeout, stream, etc.

    Returns:
      requests.Response object
    """
    path = files.NormalizePathFromURL(req.path_url)
    response = requests.Response()

    response.status_code, response.reason = self._chkpath(req.method, path)
    if response.status_code == 200 and req.method.lower() != "head":
      try:
        response.raw = io.BytesIO(files.ReadBinaryFileContents(path))
      except (OSError, IOError) as err:
        response.status_code = 500
        response.reason = str(err)

    response.url = req.url
    response.request = req
    response.connection = self
    return response
