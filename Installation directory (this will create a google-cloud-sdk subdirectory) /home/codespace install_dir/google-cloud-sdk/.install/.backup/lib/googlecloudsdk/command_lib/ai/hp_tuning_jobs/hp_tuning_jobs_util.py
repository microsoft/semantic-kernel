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
"""Utilities for Vertex AI hyperparameter tuning jobs commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources

HPTUNING_JOB_COLLECTION = 'aiplatform.projects.locations.hyperparameterTuningJobs'


def ParseJobName(name):
  """Parses the id from a full hyperparameter tuning job name."""
  return resources.REGISTRY.Parse(
      name, collection=HPTUNING_JOB_COLLECTION).Name()


def OutputCommandVersion(release_track):
  if release_track == base.ReleaseTrack.GA:
    return ''
  elif release_track == base.ReleaseTrack.BETA:
    return ' beta'
  else:
    return ' alpha'
