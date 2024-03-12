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
"""Wrapper for JSON-based Component Status."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import six


class ComponentStatus(object):
  """Class that wraps a KubeRun Component Status JSON object."""

  def __init__(self,
               name,
               deployment_state,
               commit_id,
               deployment_time,
               url,
               log_url,
               services=None,
               deployment_message='',
               deployment_reason=''):
    self.name = name
    self.deployment_state = deployment_state
    self.commit_id = commit_id
    self.deployment_time = deployment_time
    self.url = url
    self.log_url = log_url
    self.services = [] if services is None else services
    self.deployment_message = deployment_message
    self.deployment_reason = deployment_reason

  @classmethod
  def FromJSON(cls, name, json_object):
    return cls(
        name=name,
        deployment_state=json_object['deploymentState'],
        deployment_message=json_object['deploymentMessage'],
        commit_id=json_object['commitId'],
        deployment_time=json_object['deploymentTimestamp'],
        url=json_object['url'],
        log_url=json_object['logUrl'],
        services=[
            r['name']
            for r in json_object['resources']
            if r['type'] == 'Service'
        ],
        deployment_reason=json_object['deploymentReason']
        if 'deploymentReason' in json_object else '')

  def __repr__(self):
    # TODO(b/171419038): Create a common base class for these data wrappers
    items = sorted(self.__dict__.items())
    attrs_as_kv_strings = ['{}={!r}'.format(k, v) for (k, v) in items]
    return six.text_type('ComponentStatus({})').format(
        ', '.join(attrs_as_kv_strings))

  def __eq__(self, other):
    if isinstance(other, self.__class__):
      return self.__dict__ == other.__dict__
    return False
