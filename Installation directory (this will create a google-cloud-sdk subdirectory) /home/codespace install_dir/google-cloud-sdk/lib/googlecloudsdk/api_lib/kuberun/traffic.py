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
"""Wrapper for JSON-based TrafficTarget."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.kuberun import structuredout

# Designated key value for latest.
# Revisions' names may not be uppercase, so this is distinct.
LATEST_REVISION_KEY = 'LATEST'


def GetKey(target):
  """Returns the key for a TrafficTarget.

  Args:
    target: TrafficTarget, the TrafficTarget to check

  Returns:
    LATEST_REVISION_KEY if target is for the latest revison or
    target.revisionName if not.
  """
  return LATEST_REVISION_KEY if target.latestRevision else target.revisionName


class TrafficTarget(structuredout.MapObject):
  """Wraps the traffic target of Knative service revision."""

  def __str__(self):
    return '%s' % self._props

  def __repr__(self):
    return str(self)

  @property
  def latestRevision(self):
    return self._props.get('latestRevision')

  @property
  def revisionName(self):
    return self._props.get('revisionName')

  @property
  def percent(self):
    return self._props['percent']

  @property
  def tag(self):
    return self._props.get('tag')

  @property
  def url(self):
    return self._props.get('url')
