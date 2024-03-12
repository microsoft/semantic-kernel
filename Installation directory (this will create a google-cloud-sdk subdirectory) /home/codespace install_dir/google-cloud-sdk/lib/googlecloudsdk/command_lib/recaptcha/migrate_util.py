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

"""Utilities for reCAPTCHA Migrate Key Command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.core import log


def LogMigrateSuccess(response, unused_ref):
  """Expected to contain displayName field, return "key" otherwise."""
  key_name = response.displayName or "reCAPTCHA key to Enterprise"
  success_msg = "Migration of {} succeeded.".format(key_name)
  msg_len = len(success_msg)
  log.status.Print("-" * msg_len)
  log.status.Print(success_msg)
  log.status.Print("-" * msg_len)

