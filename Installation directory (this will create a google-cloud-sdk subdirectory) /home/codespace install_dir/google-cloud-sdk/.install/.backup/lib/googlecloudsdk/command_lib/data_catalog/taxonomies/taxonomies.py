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
"""Utilities for Data Catalog taxonomy commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import taxonomies


def Export(args, version_label):
  """Export the taxonomies from a project/location based on a list of taxonomyIds."""
  client = taxonomies.TaxonomiesClient(version_label)
  return client.Export(
      args.project_val,
      args.location,
      args.taxonomies
  )


def Import(args, version_label):
  """Export the taxonomies from a project/location based on a list of taxonomyIds."""
  client = taxonomies.TaxonomiesClient(version_label)
  return client.Import(
      args.project_val,
      args.location,
      args.taxonomies
  )

