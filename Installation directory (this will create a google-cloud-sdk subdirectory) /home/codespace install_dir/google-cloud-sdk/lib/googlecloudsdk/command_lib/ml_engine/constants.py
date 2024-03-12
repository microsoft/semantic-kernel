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


SUPPORTED_REGIONS = [
    'asia-east1',
    'asia-northeast1',
    'asia-southeast1',
    'australia-southeast1',
    'europe-west1',
    'europe-west2',
    'europe-west3',
    'europe-west4',
    'northamerica-northeast1',
    'us-central1',
    'us-east1',
    'us-east4',
    'us-west1',
]

SUPPORTED_REGIONS_WITH_GLOBAL = ['global'] + SUPPORTED_REGIONS
