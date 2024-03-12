# -*- coding: utf-8 -*-
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Developer Shell auth bridge.

This enables Boto API auth in Developer Shell environment.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from boto.auth_handler import AuthHandler
from boto.auth_handler import NotReadyToAuthenticate
import oauth2client.contrib.devshell as devshell


class DevshellAuth(AuthHandler):
  """Developer Shell authorization plugin class."""

  capability = ['s3']

  def __init__(self, path, config, provider):
    # Provider here is a boto.provider.Provider object (as opposed to the
    # provider attribute of CloudApi objects, which is a string).
    if provider.name != 'google':
      # Devshell credentials are valid for Google only and can't be used for s3.
      raise NotReadyToAuthenticate()
    try:
      self.creds = devshell.DevshellCredentials()
    except:
      raise NotReadyToAuthenticate()

  def add_auth(self, http_request):
    http_request.headers['Authorization'] = ('Bearer %s' %
                                             self.creds.access_token)
