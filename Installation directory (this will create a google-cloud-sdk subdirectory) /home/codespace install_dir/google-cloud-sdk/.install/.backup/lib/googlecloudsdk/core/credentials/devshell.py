# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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


"""Credentials for use with the developer shell."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.util import encoding

DEVSHELL_ENV = 'CLOUD_SHELL'
DEVSHELL_CLIENT_PORT = 'DEVSHELL_CLIENT_PORT'


def IsDevshellEnvironment():
  return bool(encoding.GetEncodedValue(os.environ, DEVSHELL_ENV, False)) \
         or HasDevshellAuth()


def HasDevshellAuth():
  port = int(encoding.GetEncodedValue(os.environ, DEVSHELL_CLIENT_PORT, 0))
  return port != 0
