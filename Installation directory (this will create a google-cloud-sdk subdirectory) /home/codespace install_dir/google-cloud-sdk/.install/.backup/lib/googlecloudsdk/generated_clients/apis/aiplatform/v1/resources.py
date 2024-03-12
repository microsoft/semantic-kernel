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


BASE_URL = 'https://aiplatform.googleapis.com/v1/'
DOCS_URL = 'https://cloud.google.com/vertex-ai/'


class Collections(enum.Enum):
  """Collections for all supported apis."""

  PROJECTS = (
      'projects',
      'projects/{projectsId}',
      {},
      ['projectsId'],
      True
  )
  PROJECTS_LOCATIONS = (
      'projects.locations',
      'projects/{projectsId}/locations/{locationsId}',
      {},
      ['projectsId', 'locationsId'],
      True
  )
  PROJECTS_LOCATIONS_BATCHPREDICTIONJOBS = (
      'projects.locations.batchPredictionJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'batchPredictionJobs/{batchPredictionJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_CUSTOMJOBS = (
      'projects.locations.customJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/customJobs/'
              '{customJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DATALABELINGJOBS = (
      'projects.locations.dataLabelingJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'dataLabelingJobs/{dataLabelingJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DATASETS = (
      'projects.locations.datasets',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/datasets/'
              '{datasetsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DATASETS_ANNOTATIONSPECS = (
      'projects.locations.datasets.annotationSpecs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/datasets/'
              '{datasetsId}/annotationSpecs/{annotationSpecsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DATASETS_DATASETVERSIONS = (
      'projects.locations.datasets.datasetVersions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/datasets/'
              '{datasetsId}/datasetVersions/{datasetVersionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_DEPLOYMENTRESOURCEPOOLS = (
      'projects.locations.deploymentResourcePools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'deploymentResourcePools/{deploymentResourcePoolsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ENDPOINTS = (
      'projects.locations.endpoints',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/endpoints/'
              '{endpointsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_ENDPOINTS_OPERATIONS = (
      'projects.locations.endpoints.operations',
      'projects/{projectsId}/locations/{locationsId}/endpoints/{endpointsId}/'
      'operations/{operationsId}',
      {},
      ['projectsId', 'locationsId', 'endpointsId', 'operationsId'],
      True
  )
  PROJECTS_LOCATIONS_FEATUREGROUPS = (
      'projects.locations.featureGroups',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/featureGroups/'
              '{featureGroupsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_FEATUREGROUPS_FEATURES = (
      'projects.locations.featureGroups.features',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/featureGroups/'
              '{featureGroupsId}/features/{featuresId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_FEATUREONLINESTORES = (
      'projects.locations.featureOnlineStores',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'featureOnlineStores/{featureOnlineStoresId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_FEATUREONLINESTORES_FEATUREVIEWS = (
      'projects.locations.featureOnlineStores.featureViews',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'featureOnlineStores/{featureOnlineStoresId}/featureViews/'
              '{featureViewsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_FEATURESTORES = (
      'projects.locations.featurestores',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/featurestores/'
              '{featurestoresId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_FEATURESTORES_ENTITYTYPES = (
      'projects.locations.featurestores.entityTypes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/featurestores/'
              '{featurestoresId}/entityTypes/{entityTypesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_FEATURESTORES_ENTITYTYPES_FEATURES = (
      'projects.locations.featurestores.entityTypes.features',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/featurestores/'
              '{featurestoresId}/entityTypes/{entityTypesId}/features/'
              '{featuresId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_HYPERPARAMETERTUNINGJOBS = (
      'projects.locations.hyperparameterTuningJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'hyperparameterTuningJobs/{hyperparameterTuningJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INDEXENDPOINTS = (
      'projects.locations.indexEndpoints',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/indexEndpoints/'
              '{indexEndpointsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INDEXENDPOINTS_OPERATIONS = (
      'projects.locations.indexEndpoints.operations',
      'projects/{projectsId}/locations/{locationsId}/indexEndpoints/'
      '{indexEndpointsId}/operations/{operationsId}',
      {},
      ['projectsId', 'locationsId', 'indexEndpointsId', 'operationsId'],
      True
  )
  PROJECTS_LOCATIONS_INDEXES = (
      'projects.locations.indexes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/indexes/'
              '{indexesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_INDEXES_OPERATIONS = (
      'projects.locations.indexes.operations',
      'projects/{projectsId}/locations/{locationsId}/indexes/{indexesId}/'
      'operations/{operationsId}',
      {},
      ['projectsId', 'locationsId', 'indexesId', 'operationsId'],
      True
  )
  PROJECTS_LOCATIONS_METADATASTORES = (
      'projects.locations.metadataStores',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/metadataStores/'
              '{metadataStoresId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_METADATASTORES_ARTIFACTS = (
      'projects.locations.metadataStores.artifacts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/metadataStores/'
              '{metadataStoresId}/artifacts/{artifactsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_METADATASTORES_CONTEXTS = (
      'projects.locations.metadataStores.contexts',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/metadataStores/'
              '{metadataStoresId}/contexts/{contextsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_METADATASTORES_EXECUTIONS = (
      'projects.locations.metadataStores.executions',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/metadataStores/'
              '{metadataStoresId}/executions/{executionsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_METADATASTORES_METADATASCHEMAS = (
      'projects.locations.metadataStores.metadataSchemas',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/metadataStores/'
              '{metadataStoresId}/metadataSchemas/{metadataSchemasId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_MODELDEPLOYMENTMONITORINGJOBS = (
      'projects.locations.modelDeploymentMonitoringJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'modelDeploymentMonitoringJobs/'
              '{modelDeploymentMonitoringJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_MODELS = (
      'projects.locations.models',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/models/'
              '{modelsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_MODELS_EVALUATIONS = (
      'projects.locations.models.evaluations',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/models/'
              '{modelsId}/evaluations/{evaluationsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_MODELS_EVALUATIONS_SLICES = (
      'projects.locations.models.evaluations.slices',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/models/'
              '{modelsId}/evaluations/{evaluationsId}/slices/{slicesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_MODELS_OPERATIONS = (
      'projects.locations.models.operations',
      'projects/{projectsId}/locations/{locationsId}/models/{modelsId}/'
      'operations/{operationsId}',
      {},
      ['projectsId', 'locationsId', 'modelsId', 'operationsId'],
      True
  )
  PROJECTS_LOCATIONS_NASJOBS = (
      'projects.locations.nasJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/nasJobs/'
              '{nasJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NASJOBS_NASTRIALDETAILS = (
      'projects.locations.nasJobs.nasTrialDetails',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/nasJobs/'
              '{nasJobsId}/nasTrialDetails/{nasTrialDetailsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NOTEBOOKRUNTIMETEMPLATES = (
      'projects.locations.notebookRuntimeTemplates',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'notebookRuntimeTemplates/{notebookRuntimeTemplatesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_NOTEBOOKRUNTIMES = (
      'projects.locations.notebookRuntimes',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'notebookRuntimes/{notebookRuntimesId}',
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
  PROJECTS_LOCATIONS_PIPELINEJOBS = (
      'projects.locations.pipelineJobs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/pipelineJobs/'
              '{pipelineJobsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SCHEDULES = (
      'projects.locations.schedules',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/schedules/'
              '{schedulesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_SPECIALISTPOOLS = (
      'projects.locations.specialistPools',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/specialistPools/'
              '{specialistPoolsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_STUDIES = (
      'projects.locations.studies',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/studies/'
              '{studiesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_STUDIES_TRIALS = (
      'projects.locations.studies.trials',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/studies/'
              '{studiesId}/trials/{trialsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TENSORBOARDS = (
      'projects.locations.tensorboards',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/tensorboards/'
              '{tensorboardsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TENSORBOARDS_EXPERIMENTS = (
      'projects.locations.tensorboards.experiments',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/tensorboards/'
              '{tensorboardsId}/experiments/{experimentsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TENSORBOARDS_EXPERIMENTS_RUNS = (
      'projects.locations.tensorboards.experiments.runs',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/tensorboards/'
              '{tensorboardsId}/experiments/{experimentsId}/runs/{runsId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TENSORBOARDS_EXPERIMENTS_RUNS_TIMESERIES = (
      'projects.locations.tensorboards.experiments.runs.timeSeries',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/tensorboards/'
              '{tensorboardsId}/experiments/{experimentsId}/runs/{runsId}/'
              'timeSeries/{timeSeriesId}',
      },
      ['name'],
      True
  )
  PROJECTS_LOCATIONS_TRAININGPIPELINES = (
      'projects.locations.trainingPipelines',
      '{+name}',
      {
          '':
              'projects/{projectsId}/locations/{locationsId}/'
              'trainingPipelines/{trainingPipelinesId}',
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
