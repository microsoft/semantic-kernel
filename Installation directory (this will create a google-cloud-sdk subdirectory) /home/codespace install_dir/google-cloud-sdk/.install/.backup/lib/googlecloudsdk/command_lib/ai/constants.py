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
"""Constants used for AI Platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

BETA_VERSION = 'BETA'
GA_VERSION = 'GA'
AI_PLATFORM_API_VERSION = {
    GA_VERSION: 'v1',
    BETA_VERSION: 'v1beta1'
}
AI_PLATFORM_MESSAGE_PREFIX = {
    GA_VERSION: 'GoogleCloudAiplatformV1',
    BETA_VERSION: 'GoogleCloudAiplatformV1beta1'
}
AI_PLATFORM_API_NAME = 'aiplatform'
AI_PLATFORM_RELEASE_TRACK_TO_VERSION = {
    base.ReleaseTrack.GA: GA_VERSION,
    base.ReleaseTrack.BETA: BETA_VERSION
}

# The default available regions for most Vertex AI products. See
# https://cloud.google.com/vertex-ai/docs/general/locations#feature-availability
# for more details.
SUPPORTED_REGION = ('us-central1', 'europe-west4', 'asia-east1')

# Available regions specifically for training, including custom-jobs and
# hp-tuning-jobs.
SUPPORTED_TRAINING_REGIONS = (
    'asia-east1',
    'asia-east2',
    'asia-northeast1',
    'asia-northeast2',
    'asia-northeast3',
    'asia-south1',
    'asia-southeast1',
    'asia-southeast2',
    'australia-southeast1',
    'australia-southeast2',
    'europe-central2',
    'europe-north1',
    'europe-southwest1',
    'europe-west1',
    'europe-west2',
    'europe-west3',
    'europe-west4',
    'europe-west6',
    'europe-west8',
    'europe-west9',
    'me-west1',
    'northamerica-northeast1',
    'northamerica-northeast2',
    'southamerica-east1',
    'southamerica-west1',
    'us-central1',
    'us-east1',
    'us-east4',
    'us-south1',
    'us-west1',
    'us-west2',
    'us-west3',
    'us-west4',
)

# Available regions specifically for online prediction, including endpoints and
# models
SUPPORTED_OP_REGIONS = (
    'asia-east1',
    'asia-east2',
    'asia-northeast1',
    'asia-northeast2',
    'asia-northeast3',
    'asia-south1',
    'asia-southeast1',
    'asia-southeast2',
    'australia-southeast1',
    'australia-southeast2',
    'europe-central2',
    'europe-north1',
    'europe-southwest1',
    'europe-west1',
    'europe-west2',
    'europe-west3',
    'europe-west4',
    'europe-west6',
    'europe-west8',
    'europe-west9',
    'me-west1',
    'northamerica-northeast1',
    'northamerica-northeast2',
    'southamerica-east1',
    'southamerica-west1',
    'us-central1',
    'us-east1',
    'us-east4',
    'us-south1',
    'us-west1',
    'us-west2',
    'us-west3',
    'us-west4',
)

# Available regions specifically for deployment resource pools
SUPPORTED_DEPLOYMENT_RESOURCE_POOL_REGIONS = (
    'us-central1',
    'us-east1',
    'us-east4',
    'us-west1',
    'europe-west1',
    'asia-northeast1',
    'asia-southeast1',
)

# Available regions specifically for model monitoring jobs
SUPPORTED_MODEL_MONITORING_JOBS_REGIONS = (
    'asia-east1',
    'asia-east2',
    'asia-northeast1',
    'asia-northeast3',
    'asia-south1',
    'asia-southeast1',
    'asia-southeast2',
    'australia-southeast1',
    'europe-central2',
    'europe-west1',
    'europe-west2',
    'europe-west3',
    'europe-west4',
    'europe-west6',
    'europe-west9',
    'northamerica-northeast1',
    'northamerica-northeast2',
    'southamerica-east1',
    'us-central1',
    'us-east1',
    'us-east4',
    'us-west1',
    'us-west2',
    'us-west3',
    'us-west4',
)

OPERATION_CREATION_DISPLAY_MESSAGE = """\
The {verb} operation [{name}] was submitted successfully.

You may view the status of your operation with the command

  $ gcloud ai operations describe {id} {sub_commands}\
"""

DEFAULT_OPERATION_COLLECTION = 'aiplatform.projects.locations.operations'

DEPLOYMENT_RESOURCE_POOLS_COLLECTION = 'aiplatform.projects.locations.deploymentResourcePools'

ENDPOINTS_COLLECTION = 'aiplatform.projects.locations.endpoints'

INDEX_ENDPOINTS_COLLECTION = 'aiplatform.projects.locations.indexEndpoints'
INDEXES_COLLECTION = 'aiplatform.projects.locations.indexes'

TENSORBOARDS_COLLECTION = 'aiplatform.projects.locations.tensorboards'

TENSORBOARD_EXPERIMENTS_COLLECTION = 'aiplatform.projects.locations.tensorboards.experiments'

TENSORBOARD_RUNS_COLLECTION = 'aiplatform.projects.locations.tensorboards.experiments.runs'

TENSORBOARD_TIME_SERIES_COLLECTION = 'aiplatform.projects.locations.tensorboards.experiments.runs.timeSeries'

MODEL_MONITORING_JOBS_COLLECTION = 'aiplatform.projects.locations.modelDeploymentMonitoringJobs'

OP_AUTOSCALING_METRIC_NAME_MAPPER = {
    'cpu-usage':
        'aiplatform.googleapis.com/prediction/online/cpu/utilization',
    'gpu-duty-cycle':
        'aiplatform.googleapis.com/prediction/online/accelerator/duty_cycle',
}

MODEL_MONITORING_JOB_CREATION_DISPLAY_MESSAGE = """\
Model monitoring Job [{id}] submitted successfully.

Your job is still active. You may view the status of your job with the command

  $ {cmd_prefix} ai model-monitoring-jobs describe {id}

Job State: {state}\
"""

MODEL_MONITORING_JOB_PAUSE_DISPLAY_MESSAGE = """\
Request to pause model deployment monitoring job [{id}] has been sent

You may view the status of your job with the command

  $ {cmd_prefix} ai model-monitoring-jobs describe {id}
"""

MODEL_MONITORING_JOB_RESUME_DISPLAY_MESSAGE = """\
Request to resume model deployment monitoring job [{id}] has been sent

You may view the status of your job with the command

  $ {cmd_prefix} ai model-monitoring-jobs describe {id}
"""
