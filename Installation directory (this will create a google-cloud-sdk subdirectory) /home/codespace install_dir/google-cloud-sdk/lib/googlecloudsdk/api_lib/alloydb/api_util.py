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
"""Common utility functions for getting the alloydb API client."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import log
from googlecloudsdk.core import resources

# API version constants
DEFAULT_RELEASE_TRACK = base.ReleaseTrack.ALPHA
VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1alpha',
    base.ReleaseTrack.BETA: 'v1beta',
    base.ReleaseTrack.GA: 'v1',
}
API_VERSION_DEFAULT = VERSION_MAP[DEFAULT_RELEASE_TRACK]


class AlloyDBClient(object):
  """Wrapper for alloydb API client and associated resources."""

  def __init__(self, release_track):
    api_version = VERSION_MAP[release_track]
    self.release_track = release_track
    self.alloydb_client = apis.GetClientInstance('alloydb', api_version)
    self.alloydb_messages = self.alloydb_client.MESSAGES_MODULE
    self.resource_parser = resources.Registry()
    self.resource_parser.RegisterApiByName('alloydb', api_version)


def GetMessagesModule(release_track):
  """Returns the message module for release track."""
  api_version = VERSION_MAP[release_track]
  return apis.GetMessagesModule('alloydb', api_version)


def YieldFromListHandlingUnreachable(*args, **kwargs):
  """Yields from paged List calls handling unreachable."""
  unreachable = set()

  def _GetFieldFn(message, attr):
    unreachable.update(message.unreachable)
    return getattr(message, attr)

  result = list_pager.YieldFromList(get_field_func=_GetFieldFn, *args, **kwargs)
  for item in result:
    yield item
  if unreachable:
    log.warning(
        'The following locations were unreachable: %s',
        ', '.join(sorted(unreachable)),
    )
