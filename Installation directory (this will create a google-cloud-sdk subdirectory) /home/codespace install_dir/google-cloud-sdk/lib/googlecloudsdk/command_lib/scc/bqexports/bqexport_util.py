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

"""Shared util methods common to BQExports commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.command_lib.scc import errors
from googlecloudsdk.command_lib.scc import util


def ValidateAndGetBigQueryExportV1Name(args):
  """Returns relative resource name for a v1 B2igQuery export.

  Validates on regexes for args containing full names or short names with
  resources. Localization is supported by the
  ValidateAndGetBigQueryExportV2Name method.

  Args:
    args: an argparse object that should contain .BIG_QUERY_EXPORT, optionally 1
      of .organization, .folder, .project

  Examples:

  args with BIG_QUERY_EXPORT="organizations/123/bigQueryExports/config1"
  returns the BIG_QUERY_EXPORT

  args with BIG_QUERY_EXPORT="config1" and projects="projects/123" returns
  projects/123/bigQueryExports/config1
  """
  bq_export_name = args.BIG_QUERY_EXPORT

  long_name_format = re.compile(
      "(organizations|projects|folders)/.*/bigQueryExports/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
  ).match(bq_export_name)
  short_name_format = re.compile("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$").match(
      bq_export_name
  )

  if not long_name_format and not short_name_format:
    if "/" in bq_export_name:
      raise errors.InvalidSCCInputError(
          "BigQuery export must match the full resource name, or "
          "`--organization=`, `--folder=` or `--project=` must be provided."
      )
    else:
      raise errors.InvalidSCCInputError(
          "BigQuery export id does not match the pattern "
          "'^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$'."
      )

  if long_name_format:
    return bq_export_name

  if short_name_format:
    parent = util.GetParentFromNamedArguments(args)
    if parent is None:
      raise errors.InvalidSCCInputError(
          "BigQuery export must match the full resource name, or "
          "`--organization=`, `--folder=` or `--project=` must be provided."
      )
    else:
      return (
          util.GetParentFromNamedArguments(args)
          + "/bigQueryExports/"
          + bq_export_name
      )


def ValidateAndGetBigQueryExportV2Name(args):
  """Returns relative resource name for a v2 Big Query export.

  Validates on regexes for args containing full names with locations or short
  names with resources.

  Args:
    args: an argparse object that should contain .BIG_QUERY_EXPORT, optionally 1
      of .organization, .folder, .project; and optionally .location

  Examples:

  args with BIG_QUERY_EXPORT="organizations/123/bigQueryExports/config1"
  and location="locations/us" returns
  organizations/123/locations/us/bigQueryExports/config1

  args with
  BIG_QUERY_EXPORT="folders/123/locations/us/bigQueryExports/config1"
  and returns folders/123/locations/us/bigQueryExports/config1

  args with BIG_QUERY_EXPORT="config1", projects="projects/123", and
  locations="us" returns projects/123/bigQueryExports/config1
  """

  id_pattern = re.compile("^[a-z]([a-z0-9-]{0,61}[a-z0-9])?$")
  nonregionalized_resource_pattern = re.compile(
      "(organizations|projects|folders)/.+/bigQueryExports/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
  )

  regionalized_resource_pattern = re.compile(
      "(organizations|projects|folders)/.+/locations/.+/bigQueryExports/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
  )
  bq_export_id = args.BIG_QUERY_EXPORT
  location = util.ValidateAndGetLocation(args, "v2")

  # id-only pattern (short name): compose the full name
  if id_pattern.match(bq_export_id):
    parent = util.GetParentFromNamedArguments(args)
    if parent is None:
      raise errors.InvalidSCCInputError(
          "BigQuery export must match the full resource name, or "
          "`--organization=`, `--folder=` or `--project=` must be provided."
      )
    return f"{parent}/locations/{location}/bigQueryExports/{bq_export_id}"

  # v2=style regionalized patterns
  if regionalized_resource_pattern.match(bq_export_id):
    return bq_export_id

  # v1-style nonregionalized patterns are acceptable
  if nonregionalized_resource_pattern.match(bq_export_id):
    # Handle config id as full resource name
    [parent_segment, id_segment] = bq_export_id.split("/bigQueryExports/")
    return f"{parent_segment}/locations/{location}/bigQueryExports/{id_segment}"

  raise errors.InvalidSCCInputError(
      "BigQuery export must match"
      " (organizations|projects|folders)/.+/bigQueryExports/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
      " (organizations|projects|folders)/.+/locations/.+/bigQueryExports/[a-z]([a-z0-9-]{0,61}[a-z0-9])?$"
      " or [a-zA-Z0-9-_]{1,128}$."
  )

