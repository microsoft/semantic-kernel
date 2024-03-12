# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Common loggers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import log


class Logger(object):
  """Base for all loggers."""

  def __init__(self, log_=None):
    self.log = log_ or log

  def Print(self, *msg):
    self.log.status.Print(*msg)


class Secrets(Logger):
  """Logger for secrets."""

  def _Print(self, action, secret_ref):
    self.Print('{action} secret [{secret}].'.format(
        action=action, secret=secret_ref.Name()))

  def Created(self, secret_ref):
    self._Print('Created', secret_ref)

  def Deleted(self, secret_ref):
    self._Print('Deleted', secret_ref)

  def Updated(self, secret_ref):
    self._Print('Updated', secret_ref)

  def UpdatedReplication(self, secret_ref):
    self._Print('Updated replication for', secret_ref)


class Versions(Logger):
  """Logger for versions."""

  def _Print(self, action, version_ref):
    self.Print('{action} version [{version}] of the secret [{secret}].'.format(
        action=action,
        version=version_ref.Name(),
        secret=version_ref.Parent().Name()))

  def Created(self, version_ref):
    self._Print('Created', version_ref)

  def Destroyed(self, version_ref):
    self._Print('Destroyed', version_ref)

  def Disabled(self, version_ref):
    self._Print('Disabled', version_ref)

  def Enabled(self, version_ref):
    self._Print('Enabled', version_ref)
