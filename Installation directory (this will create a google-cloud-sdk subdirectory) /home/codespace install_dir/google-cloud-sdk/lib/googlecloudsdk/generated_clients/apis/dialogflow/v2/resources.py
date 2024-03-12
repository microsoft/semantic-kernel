# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Resource definitions for Cloud Platform Apis generated from apitools."""

import enum


BASE_URL = 'https://dialogflow.googleapis.com/v2/'
DOCS_URL = 'https://cloud.google.com/dialogflow/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_AGENT = (
      'projects.agent',
      'projects/{projectsId}/agent',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_AGENT_ENTITYTYPES = (
      'projects.agent.entityTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/entityTypes/{entityTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_ENVIRONMENTS = (
      'projects.agent.environments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/environments/{environmentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_ENVIRONMENTS_USERS = (
      'projects.agent.environments.users',
      'projects/{projectsId}/agent/environments/{environmentsId}/users/'
      '{usersId}',
      {},
      ['projectsId', 'environmentsId', 'usersId'],
      True
  )
  PROJECTS_AGENT_ENVIRONMENTS_USERS_SESSIONS = (
      'projects.agent.environments.users.sessions',
      'projects/{projectsId}/agent/environments/{environmentsId}/users/'
      '{usersId}/sessions/{sessionsId}',
      {},
      ['projectsId', 'environmentsId', 'usersId', 'sessionsId'],
      True
  )
  PROJECTS_AGENT_ENVIRONMENTS_USERS_SESSIONS_CONTEXTS = (
      'projects.agent.environments.users.sessions.contexts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/environments/{environmentsId}/'
              'users/{usersId}/sessions/{sessionsId}/contexts/{contextsId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_ENVIRONMENTS_USERS_SESSIONS_ENTITYTYPES = (
      'projects.agent.environments.users.sessions.entityTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/environments/{environmentsId}/'
              'users/{usersId}/sessions/{sessionsId}/entityTypes/'
              '{entityTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_INTENTS = (
      'projects.agent.intents',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/intents/{intentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_KNOWLEDGEBASES = (
      'projects.agent.knowledgeBases',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/knowledgeBases/{knowledgeBasesId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_KNOWLEDGEBASES_DOCUMENTS = (
      'projects.agent.knowledgeBases.documents',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/knowledgeBases/{knowledgeBasesId}/'
              'documents/{documentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_SESSIONS = (
      'projects.agent.sessions',
      'projects/{projectsId}/agent/sessions/{sessionsId}',
      {},
      ['projectsId', 'sessionsId'],
      True
  )
  PROJECTS_AGENT_SESSIONS_CONTEXTS = (
      'projects.agent.sessions.contexts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/sessions/{sessionsId}/contexts/'
              '{contextsId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_SESSIONS_ENTITYTYPES = (
      'projects.agent.sessions.entityTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/sessions/{sessionsId}/entityTypes/'
              '{entityTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_AGENT_VERSIONS = (
      'projects.agent.versions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/agent/versions/{versionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONVERSATIONDATASETS = (
      'projects.conversationDatasets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/conversationDatasets/'
              '{conversationDatasetsId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONVERSATIONMODELS = (
      'projects.conversationModels',
      '{+name}',
      {
          '':
              'projects/{projectsId}/conversationModels/'
              '{conversationModelsId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONVERSATIONMODELS_EVALUATIONS = (
      'projects.conversationModels.evaluations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/conversationModels/'
              '{conversationModelsId}/evaluations/{evaluationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONVERSATIONPROFILES = (
      'projects.conversationProfiles',
      '{+name}',
      {
          '':
              'projects/{projectsId}/conversationProfiles/'
              '{conversationProfilesId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONVERSATIONS = (
      'projects.conversations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/conversations/{conversationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_CONVERSATIONS_PARTICIPANTS = (
      'projects.conversations.participants',
      '{+name}',
      {
          '':
              'projects/{projectsId}/conversations/{conversationsId}/'
              'participants/{participantsId}',
      },
      ['name'],
      True
  )
  PROJECTS_KNOWLEDGEBASES = (
      'projects.knowledgeBases',
      '{+name}',
      {
          '':
              'projects/{projectsId}/knowledgeBases/{knowledgeBasesId}',
      },
      ['name'],
      True
  )
  PROJECTS_KNOWLEDGEBASES_DOCUMENTS = (
      'projects.knowledgeBases.documents',
      '{+name}',
      {
          '':
              'projects/{projectsId}/knowledgeBases/{knowledgeBasesId}/'
              'documents/{documentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_ENTITYTYPES = (
      'projects.locations.agent.entityTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/'
              'entityTypes/{entityTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_ENVIRONMENTS = (
      'projects.locations.agent.environments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/'
              'environments/{environmentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_ENVIRONMENTS_USERS = (
      'projects.locations.agent.environments.users',
      'projects/{projectsId}/locations/{locationsId}/agent/environments/'
      '{environmentsId}/users/{usersId}',
      {},
      ['projectsId', 'locationsId', 'environmentsId', 'usersId'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_ENVIRONMENTS_USERS_SESSIONS = (
      'projects.locations.agent.environments.users.sessions',
      'projects/{projectsId}/locations/{locationsId}/agent/environments/'
      '{environmentsId}/users/{usersId}/sessions/{sessionsId}',
      {},
      ['projectsId', 'locationsId', 'environmentsId', 'usersId', 'sessionsId'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_ENVIRONMENTS_USERS_SESSIONS_CONTEXTS = (
      'projects.locations.agent.environments.users.sessions.contexts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/'
              'environments/{environmentsId}/users/{usersId}/sessions/'
              '{sessionsId}/contexts/{contextsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_ENVIRONMENTS_USERS_SESSIONS_ENTITYTYPES = (
      'projects.locations.agent.environments.users.sessions.entityTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/'
              'environments/{environmentsId}/users/{usersId}/sessions/'
              '{sessionsId}/entityTypes/{entityTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_INTENTS = (
      'projects.locations.agent.intents',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/intents/'
              '{intentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_SESSIONS = (
      'projects.locations.agent.sessions',
      'projects/{projectsId}/locations/{locationsId}/agent/sessions/'
      '{sessionsId}',
      {},
      ['projectsId', 'locationsId', 'sessionsId'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_SESSIONS_CONTEXTS = (
      'projects.locations.agent.sessions.contexts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/sessions/'
              '{sessionsId}/contexts/{contextsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_SESSIONS_ENTITYTYPES = (
      'projects.locations.agent.sessions.entityTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/sessions/'
              '{sessionsId}/entityTypes/{entityTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_AGENT_VERSIONS = (
      'projects.locations.agent.versions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/agent/versions/'
              '{versionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONVERSATIONDATASETS = (
      'projects.locations.conversationDatasets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'conversationDatasets/{conversationDatasetsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONVERSATIONMODELS = (
      'projects.locations.conversationModels',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'conversationModels/{conversationModelsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONVERSATIONMODELS_EVALUATIONS = (
      'projects.locations.conversationModels.evaluations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'conversationModels/{conversationModelsId}/evaluations/'
              '{evaluationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONVERSATIONPROFILES = (
      'projects.locations.conversationProfiles',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'conversationProfiles/{conversationProfilesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONVERSATIONS = (
      'projects.locations.conversations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/conversations/'
              '{conversationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CONVERSATIONS_PARTICIPANTS = (
      'projects.locations.conversations.participants',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/conversations/'
              '{conversationsId}/participants/{participantsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_KNOWLEDGEBASES = (
      'projects.locations.knowledgeBases',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/knowledgeBases/'
              '{knowledgeBasesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_KNOWLEDGEBASES_DOCUMENTS = (
      'projects.locations.knowledgeBases.documents',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/knowledgeBases/'
              '{knowledgeBasesId}/documents/{documentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_OPERATIONS = (
      'projects.locations.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/operations/'
              '{operationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_OPERATIONS = (
      'projects.operations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/operations/{operationsId}',
      },
      ['name'],
      True
  )

  def __init__(self, collection_name, path, flat_paths, params,
               enable_uri_parsing):
    self.collection_name = collection_name
    self.path = path
    self.flat_paths = flat_paths
    self.params = params
    self.enable_uri_parsing = enable_uri_parsing
