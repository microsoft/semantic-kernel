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
"""API Library for gcloud cloudscheduler."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.scheduler import jobs
from googlecloudsdk.api_lib.scheduler import locations
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base


API_NAME = 'cloudscheduler'
ALPHA_API_VERSION = 'v1alpha1'
BETA_API_VERSION = 'v1beta1'
GA_API_VERSION = 'v1'


class UnsupportedReleaseTrackError(Exception):
  """Raised when requesting an api for an unsupported release track."""


def ApiVersionFromReleaseTrack(release_track):
  if release_track == base.ReleaseTrack.ALPHA:
    return ALPHA_API_VERSION
  if release_track == base.ReleaseTrack.BETA:
    return BETA_API_VERSION
  if release_track == base.ReleaseTrack.GA:
    return GA_API_VERSION
  else:
    raise UnsupportedReleaseTrackError(release_track)


def GetApiAdapter(release_track, legacy_cron=False):
  if release_track == base.ReleaseTrack.ALPHA:
    return AlphaApiAdapter(legacy_cron=legacy_cron)
  elif release_track == base.ReleaseTrack.BETA:
    return BetaApiAdapter(legacy_cron=legacy_cron)
  elif release_track == base.ReleaseTrack.GA:
    return GaApiAdapter(legacy_cron=legacy_cron)
  else:
    raise UnsupportedReleaseTrackError(release_track)


class BaseApiAdapter(object):

  def __init__(self, api_version):
    self.client = apis.GetClientInstance(API_NAME, api_version)
    self.messages = self.client.MESSAGES_MODULE
    self.locations = locations.Locations(self.client.MESSAGES_MODULE,
                                         self.client.projects_locations)


class AlphaApiAdapter(BaseApiAdapter):

  def __init__(self, legacy_cron=False):
    super(AlphaApiAdapter, self).__init__(ALPHA_API_VERSION)
    self.jobs = jobs.BaseJobs(self.client.MESSAGES_MODULE,
                              self.client.projects_locations_jobs,
                              legacy_cron=legacy_cron)


class BetaApiAdapter(BaseApiAdapter):

  def __init__(self, legacy_cron=False):
    super(BetaApiAdapter, self).__init__(BETA_API_VERSION)
    self.jobs = jobs.BaseJobs(self.client.MESSAGES_MODULE,
                              self.client.projects_locations_jobs,
                              legacy_cron=legacy_cron)


class GaApiAdapter(BaseApiAdapter):

  def __init__(self, legacy_cron=False):
    super(GaApiAdapter, self).__init__(GA_API_VERSION)
    self.jobs = jobs.BaseJobs(self.client.MESSAGES_MODULE,
                              self.client.projects_locations_jobs,
                              legacy_cron=legacy_cron)
