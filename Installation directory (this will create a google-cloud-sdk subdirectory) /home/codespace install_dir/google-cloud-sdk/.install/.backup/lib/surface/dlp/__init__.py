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

"""The gcloud dlp command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DLP(base.Group):
  """Manage sensitive data with Cloud Data Loss Prevention.

  The DLP API lets you understand and manage sensitive data. It provides
  fast, scalable classification and optional redaction for sensitive data
  elements like credit card numbers, names, Social Security numbers, passport
  numbers, U.S. and selected international driver's license numbers, and phone
  numbers. The API classifies this data using more than 50 predefined detectors
  to identify patterns, formats, and checksums, and even understands contextual
  clues. The API supports text and images; just send data to the API or
  specify data stored on your Google Cloud Storage, BigQuery,
  or Cloud Datastore instances.
  """
  category = base.SECURITY_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190532822):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
