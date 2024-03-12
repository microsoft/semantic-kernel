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
"""recommender API recommendations service."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis

RECOMMENDER_API_NAME = 'recommender'


def RecommenderClient(api_version):
  return apis.GetClientInstance(RECOMMENDER_API_NAME, api_version)


def RecommenderMessages(api_version):
  """Returns the messages module for the Resource Settings service."""
  return apis.GetMessagesModule(RECOMMENDER_API_NAME, api_version)


def BillingAccountsRecommenderRecommendationsService(api_version):
  """Returns the service class for the Billing Account recommendations."""
  client = RecommenderClient(api_version)
  return client.billingAccounts_locations_recommenders_recommendations


def ProjectsRecommenderRecommendationsService(api_version):
  """Returns the service class for the Project recommendations."""
  client = RecommenderClient(api_version)
  return client.projects_locations_recommenders_recommendations


def ProjectsRecommenderConfigsService(api_version):
  """Returns the service class for the Project recommender configs."""
  client = RecommenderClient(api_version)
  return client.projects_locations_recommenders


def ProjectsInsightTypeConfigsService(api_version):
  """Returns the service class for the Project insight type configs."""
  client = RecommenderClient(api_version)
  return client.projects_locations_insightTypes


def FoldersRecommenderRecommendationsService(api_version):
  """Returns the service class for the Folders recommendations."""
  client = RecommenderClient(api_version)
  return client.folders_locations_recommenders_recommendations


def OrganizationsRecommenderRecommendationsService(api_version):
  """Returns the service class for the Organization recommendations."""
  client = RecommenderClient(api_version)
  return client.organizations_locations_recommenders_recommendations


def BillingAccountsInsightTypeInsightsService(api_version):
  """Returns the service class for the Billing Account insights."""
  client = RecommenderClient(api_version)
  return client.billingAccounts_locations_insightTypes_insights


def ProjectsInsightTypeInsightsService(api_version):
  """Returns the service class for the Project insights."""
  client = RecommenderClient(api_version)
  return client.projects_locations_insightTypes_insights


def FoldersInsightTypeInsightsService(api_version):
  """Returns the service class for the Folders insights."""
  client = RecommenderClient(api_version)
  return client.folders_locations_insightTypes_insights


def OrganizationsInsightTypeInsightsService(api_version):
  """Returns the service class for the Organization insights."""
  client = RecommenderClient(api_version)
  return client.organizations_locations_insightTypes_insights
