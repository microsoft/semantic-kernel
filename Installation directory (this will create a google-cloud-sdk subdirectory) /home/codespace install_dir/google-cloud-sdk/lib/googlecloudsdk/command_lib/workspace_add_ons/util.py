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
"""Deployment utilities for `gcloud gsuiteaddons` commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.core.util import files


def ParseJsonFileToDeployment(deployment_file):
  f = files.ReadFileContents(deployment_file)
  return json.loads(f)


def LoadJsonString(deployment):
  return json.loads(deployment)


def SetAuthorizationNamePath(unused_ref, unused_args, request):
  """Sets the request path in name attribute for authorization request.

  Appends /authorization at the end of the request path for the singleton
  authorization request.

  Args:
    unused_ref: reference to the project object.
    unused_args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """
  del unused_ref, unused_args  # Unused.
  request.name = request.name + '/authorization'
  return request


def SetInstallStatusNamePath(deployment_ref, unused_args, request):
  """Sets the request path in the name attribute for install status request.

  Replaces the '/' within the deployment name by '%2F' and appends
  /installStatus at the end of the request path for the install
  status request.

  Args:
    deployment_ref: reference to the deployment object
    unused_args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """
  del unused_args  # Unused.
  request.name = '{}/deployments/{}/installStatus'.format(
      deployment_ref.Parent().RelativeName(),
      deployment_ref.deploymentsId.replace('/', '%2F'))
  return request


def HandleEscapingInNamePath(deployment_ref, unused_args, request):
  """Sets the request path in the name attribute for various add on commands.

  Replaces the '/' within the deployment name by '%2F' in the install,
  uninstall,
  delete, replace, describe commands.

  Args:
    deployment_ref: reference to the deployment object
    unused_args: command line arguments.
    request: API request to be issued

  Returns:
    modified request
  """
  del unused_args  # Unused.
  request.name = '{}/deployments/{}'.format(
      deployment_ref.Parent().RelativeName(),
      deployment_ref.deploymentsId.replace('/', '%2F'))
  return request
