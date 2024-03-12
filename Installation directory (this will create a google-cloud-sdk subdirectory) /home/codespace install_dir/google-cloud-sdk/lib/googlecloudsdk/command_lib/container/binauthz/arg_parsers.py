# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""arg_parser validators for Binary Authoritzation's CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.command_lib.container.binauthz import parsing
from googlecloudsdk.core import log

# List of valid regions, used by the "export-system-policy --region" command.
# TODO(b/137271989): This hard-coded list is not ideal because it has to be
# updated whenever a region is added. It could be avoided by serving a list of
# locations from the back end.
BINAUTHZ_ENFORCER_REGIONS = [
    'global',
    'africa-south1',
    'asia-east1',
    'asia-east2',
    'asia-northeast1',
    'asia-northeast2',
    'asia-northeast3',
    'asia-south1',
    'asia-south2',
    'asia-southeast1',
    'asia-southeast2',
    'australia-southeast1',
    'australia-southeast2',
    'europe-central2',
    'europe-north1',
    'europe-southwest1',
    'europe-west1',
    'europe-west10',
    'europe-west12',
    'europe-west2',
    'europe-west3',
    'europe-west4',
    'europe-west5',
    'europe-west6',
    'europe-west8',
    'europe-west9',
    'me-central1',
    'me-central2',
    'me-west1',
    'northamerica-northeast1',
    'northamerica-northeast2',
    'southamerica-east1',
    'southamerica-west1',
    'us-central1',
    'us-central2',
    'us-east1',
    'us-east4',
    'us-east5',
    'us-east7',
    'us-south1',
    'us-west1',
    'us-west2',
    'us-west3',
    'us-west4',
    'us-west8',
]


def PolicyFileName(fname):
  if parsing.GetResourceFileType(fname) == parsing.ResourceFileType.UNKNOWN:
    raise arg_parsers.ArgumentTypeError(
        'Policy file must be a .yaml or .json file.')
  return fname


def ResourceFileName(fname):
  if parsing.GetResourceFileType(fname) == parsing.ResourceFileType.UNKNOWN:
    raise arg_parsers.ArgumentTypeError(
        'Resource file must be a .yaml or .json file.'
    )
  return fname
