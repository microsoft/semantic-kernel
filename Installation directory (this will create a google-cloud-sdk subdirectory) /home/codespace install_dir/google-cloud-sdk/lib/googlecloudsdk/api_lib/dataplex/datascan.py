# -*- coding: utf-8 -*- #
# Copyright 2022 Google Inc. All Rights Reserved.
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
"""Client for interaction with Datascan API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.command_lib.iam import iam_util


def GenerateData(args):
  """Generate Data From Arguments."""
  module = dataplex_api.GetMessageModule()

  if args.IsSpecified('data_source_entity'):
    data = module.GoogleCloudDataplexV1DataSource(
        entity=args.data_source_entity
    )
  else:
    data = module.GoogleCloudDataplexV1DataSource(
        resource=args.data_source_resource
    )
  return data


def GenerateDataQualitySpec(args):
  """Generate DataQualitySpec From Arguments."""
  module = dataplex_api.GetMessageModule()

  if args.IsSpecified('data_quality_spec_file'):
    dataqualityspec = dataplex_api.ReadObject(args.data_quality_spec_file)
    if dataqualityspec is not None:
      dataqualityspec = messages_util.DictToMessageWithErrorCheck(
          dataplex_api.SnakeToCamelDict(dataqualityspec),
          module.GoogleCloudDataplexV1DataQualitySpec,
      )
  else:
    dataqualityspec = module.GoogleCloudDataplexV1DataQualitySpec()
  return dataqualityspec


def GenerateDataProfileSpec(args):
  """Generate DataProfileSpec From Arguments."""
  module = dataplex_api.GetMessageModule()

  if args.IsSpecified('data_profile_spec_file'):
    dataprofilespec = dataplex_api.ReadObject(args.data_profile_spec_file)
    if dataprofilespec is not None:
      dataprofilespec = messages_util.DictToMessageWithErrorCheck(
          dataplex_api.SnakeToCamelDict(dataprofilespec),
          module.GoogleCloudDataplexV1DataProfileSpec,
      )
  else:
    exclude_fields, include_fields, sampling_percent, row_filter = [None] * 4
    if hasattr(args, 'exclude_field_names') and args.IsSpecified(
        'exclude_field_names'
    ):
      exclude_fields = (
          module.GoogleCloudDataplexV1DataProfileSpecSelectedFields(
              fieldNames=list(
                  val.strip() for val in args.exclude_field_names.split(',')
              )
          )
      )
    if hasattr(args, 'include_field_names') and args.IsSpecified(
        'include_field_names'
    ):
      include_fields = (
          module.GoogleCloudDataplexV1DataProfileSpecSelectedFields(
              fieldNames=list(
                  val.strip() for val in args.include_field_names.split(',')
              )
          )
      )
    if hasattr(args, 'sampling_percent') and args.IsSpecified(
        'sampling_percent'
    ):
      sampling_percent = float(args.sampling_percent)
    if hasattr(args, 'row_filter') and args.IsSpecified('row_filter'):
      row_filter = args.row_filter
    dataprofilespec = module.GoogleCloudDataplexV1DataProfileSpec(
        excludeFields=exclude_fields,
        includeFields=include_fields,
        samplingPercent=sampling_percent,
        rowFilter=row_filter,
    )
    if hasattr(args, 'export_results_table') and args.IsSpecified(
        'export_results_table'
    ):
      dataprofilespec.postScanActions = module.GoogleCloudDataplexV1DataProfileSpecPostScanActions(
          bigqueryExport=module.GoogleCloudDataplexV1DataProfileSpecPostScanActionsBigQueryExport(
              resultsTable=args.export_results_table
          )
      )
  return dataprofilespec


def GenerateSchedule(args):
  """Generate DataQualitySpec From Arguments."""
  module = dataplex_api.GetMessageModule()
  schedule = module.GoogleCloudDataplexV1TriggerSchedule(cron=args.schedule)
  return schedule


def GenerateTrigger(args):
  """Generate DataQualitySpec From Arguments."""
  module = dataplex_api.GetMessageModule()
  trigger = module.GoogleCloudDataplexV1Trigger()
  if args.IsSpecified('schedule'):
    trigger.schedule = GenerateSchedule(args)
  else:
    trigger.onDemand = module.GoogleCloudDataplexV1TriggerOnDemand()
  return trigger


def GenerateExecutionSpecForCreateRequest(args):
  """Generate ExecutionSpec From Arguments."""
  module = dataplex_api.GetMessageModule()
  executionspec = module.GoogleCloudDataplexV1DataScanExecutionSpec(
      field=args.field if hasattr(args, 'field') else args.incremental_field,
      trigger=GenerateTrigger(args),
  )
  return executionspec


def GenerateExecutionSpecForUpdateRequest(args):
  """Generate ExecutionSpec From Arguments."""
  module = dataplex_api.GetMessageModule()
  executionspec = module.GoogleCloudDataplexV1DataScanExecutionSpec(
      trigger=GenerateTrigger(args),
  )
  return executionspec


def GenerateUpdateMask(args):
  """Create Update Mask for Datascan."""
  update_mask = []
  args_to_mask = {
      'description': 'description',
      'display_name': 'displayName',
      'labels': 'labels',
      'on_demand': 'executionSpec.trigger.onDemand',
      'schedule': 'executionSpec.trigger.schedule',
  }
  args_to_mask_attr = {
      'data_profile_spec_file': 'dataProfileSpec',
      'data_quality_spec_file': 'dataQualitySpec',
      'row_filter': 'dataProfileSpec.rowFilter',
      'sampling_percent': 'dataProfileSpec.samplingPercent',
      'include_field_names': 'dataProfileSpec.includeFields',
      'exclude_field_names': 'dataProfileSpec.excludeFields',
  }

  for arg, val in args_to_mask.items():
    if args.IsSpecified(arg):
      update_mask.append(val)

  for arg, val in args_to_mask_attr.items():
    if hasattr(args, arg) and args.IsSpecified(arg):
      update_mask.append(val)
  return update_mask


def GenerateDatascanForCreateRequest(args):
  """Create Datascan for Message Create Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1DataScan(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(
          module.GoogleCloudDataplexV1DataScan, args
      ),
      data=GenerateData(args),
      executionSpec=GenerateExecutionSpecForCreateRequest(args),
  )
  if args.scan_type == 'PROFILE':
    if hasattr(args, 'data_quality_spec_file') and args.IsSpecified(
        'data_quality_spec_file'
    ):
      raise ValueError(
          'Data quality spec file specified for data profile scan.'
      )
    else:
      request.dataProfileSpec = GenerateDataProfileSpec(args)
  elif args.scan_type == 'QUALITY':
    if hasattr(args, 'data_profile_spec_file') and args.IsSpecified(
        'data_profile_spec_file'
    ):
      raise ValueError(
          'Data profile spec file specified for data quality scan.'
      )
    elif args.IsSpecified('data_quality_spec_file'):
      request.dataQualitySpec = GenerateDataQualitySpec(args)
    else:
      raise ValueError(
          'If scan-type="QUALITY" , data-quality-spec-file is a required'
          ' argument.'
      )
  return request


def GenerateDatascanForUpdateRequest(args):
  """Create Datascan for Message Update Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1DataScan(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(
          module.GoogleCloudDataplexV1DataScan, args
      ),
      executionSpec=GenerateExecutionSpecForUpdateRequest(args),
  )
  if args.scan_type == 'PROFILE':
    if hasattr(args, 'data_quality_spec_file') and args.IsSpecified(
        'data_quality_spec_file'
    ):
      raise ValueError(
          'Data quality spec file specified for data profile scan.'
      )
    request.dataProfileSpec = GenerateDataProfileSpec(args)
  elif args.scan_type == 'QUALITY':
    if hasattr(args, 'data_profile_spec_file') and args.IsSpecified(
        'data_profile_spec_file'
    ):
      raise ValueError(
          'Data profile spec file specified for data quality scan.'
      )
    elif args.IsSpecified('data_quality_spec_file'):
      request.dataQualitySpec = GenerateDataQualitySpec(args)
    else:
      request.dataQualitySpec = module.GoogleCloudDataplexV1DataQualitySpec()
  return request


def SetIamPolicy(datascan_ref, policy):
  """Set IAM Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule().DataplexProjectsLocationsDataScansSetIamPolicyRequest(
      resource=datascan_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule().GoogleIamV1SetIamPolicyRequest(
          policy=policy
      ),
  )
  return dataplex_api.GetClientInstance().projects_locations_dataScans.SetIamPolicy(
      set_iam_policy_req
  )


def SetIamPolicyFromFile(datascan_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file, dataplex_api.GetMessageModule().GoogleIamV1Policy
  )
  return SetIamPolicy(datascan_ref, policy)


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation, dataplex_api.GetClientInstance().projects_locations_dataScans
  )
