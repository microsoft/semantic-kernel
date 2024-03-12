# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""recommender API utlities."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.recommender import service as recommender_service
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import base
from googlecloudsdk.core import yaml

RECOMMENDER_API_ALPHA_VERSION = 'v1alpha2'
RECOMMENDER_API_BETA_VERSION = 'v1beta1'
RECOMMENDER_API_GA_VERSION = 'v1'


def ToCamelCase(s):
  """Converts CamelCase to camelCase."""
  return s[0].lower() + s[1:]


def ReadConfig(config_file, message_type):
  """Parses json config file.

  Args:
    config_file: file path of the config file.
    message_type: The protorpc Message type.

  Returns:
    A message of type "message_type".
  """
  config = None
  # Yaml is a superset of json, so parse json file as yaml.
  data = yaml.load_path(config_file)
  if data:
    config = messages_util.DictToMessageWithErrorCheck(data, message_type)
  return config


def GetConfigServiceFromArgs(api_version, is_insight_api):
  """Returns the config api service from the user-specified arguments.

  Args:
    api_version: API version string.
    is_insight_api: boolean value sepcify whether this is a insight api,
      otherwise will return a recommendation service api.
  """
  if is_insight_api:
    return recommender_service.ProjectsInsightTypeConfigsService(api_version)
  return recommender_service.ProjectsRecommenderConfigsService(api_version)


def GetDescribeConfigRequestFromArgs(parent_resource, is_insight_api,
                                     api_version):
  """Returns the describe request from the user-specified arguments.

  Args:
    parent_resource: resource url string, the flags are already defined in
      argparse namespace.
    is_insight_api: boolean value specifying whether this is a insight api,
      otherwise treat as a recommender service api and return related describe
      request message.
    api_version: API version string.
  """

  messages = recommender_service.RecommenderMessages(api_version)
  if is_insight_api:
    request = messages.RecommenderProjectsLocationsInsightTypesGetConfigRequest(
        name=parent_resource)
  else:
    request = messages.RecommenderProjectsLocationsRecommendersGetConfigRequest(
        name=parent_resource)
  return request


def GetApiVersion(release_track):
  """Get API version string.

  Converts API version string from release track value.

  Args:
    release_track: release_track value, can be ALPHA, BETA, GA

  Returns:
    API version string.
  """
  switcher = {
      base.ReleaseTrack.ALPHA: RECOMMENDER_API_ALPHA_VERSION,
      base.ReleaseTrack.BETA: RECOMMENDER_API_BETA_VERSION,
      base.ReleaseTrack.GA: RECOMMENDER_API_GA_VERSION,
  }
  return switcher.get(release_track, RECOMMENDER_API_ALPHA_VERSION)
