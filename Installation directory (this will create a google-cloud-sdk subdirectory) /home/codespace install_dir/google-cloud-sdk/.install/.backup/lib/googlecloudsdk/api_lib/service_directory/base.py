# -*- coding: utf-8 -*- #
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""The base api lib for Service Directory CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base

_API_NAME = 'servicedirectory'
_VERSION_MAP = {
    base.ReleaseTrack.ALPHA: 'v1beta1',
    base.ReleaseTrack.BETA: 'v1beta1',
    base.ReleaseTrack.GA: 'v1'
}


class ServiceDirectoryApiLibBase(object):
  """The base class for all Service Directory clients."""

  def __init__(self, release_track=base.ReleaseTrack.GA):
    self.client = apis.GetClientInstance(_API_NAME,
                                         _VERSION_MAP.get(release_track))
    self.msgs = apis.GetMessagesModule(_API_NAME,
                                       _VERSION_MAP.get(release_track))
