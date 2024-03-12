# -*- coding: utf-8 -*-
# Copyright 2011 Google Inc. All Rights Reserved.
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
"""No-op authorization plugin allowing boto anonymous access.

This allows users to use gsutil for accessing publicly readable buckets and
objects without first signing up for an account.
"""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

from boto.auth_handler import AuthHandler


class NoOpAuth(AuthHandler):
  """No-op authorization plugin class."""

  capability = ['hmac-v4-s3', 's3']

  def __init__(self, path, config, provider):
    pass

  def add_auth(self, http_request):
    pass
