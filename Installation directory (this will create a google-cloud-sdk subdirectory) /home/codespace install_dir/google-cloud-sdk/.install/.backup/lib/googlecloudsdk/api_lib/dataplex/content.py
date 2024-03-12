# -*- coding: utf-8 -*- #
# Copyright 2021 Google Inc. All Rights Reserved.
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
"""Client for interaction with CONTENT API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(content_ref, policy):
  """Sets Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesContentSetIamPolicyRequest(
      resource=content_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_content.SetIamPolicy(set_iam_policy_req)


def GetIamPolicy(content_ref):
  """Gets Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesContentGetIamPolicyRequest(
      resource=content_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_content.GetIamPolicy(get_iam_policy_req)


def AddIamPolicyBinding(content_ref, member, role):
  """Adds iam policy binding request."""
  policy = GetIamPolicy(content_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return SetIamPolicy(content_ref, policy)


def RemoveIamPolicyBinding(lake_ref, member, role):
  """Removes iam policy binding request."""
  policy = GetIamPolicy(lake_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(lake_ref, policy)


def SetIamPolicyFromFile(content_ref, policy_file):
  """Sets iam policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return SetIamPolicy(content_ref, policy)


def GenerateContentForCreateRequest(args):
  """Creates Content for Message Create Requests."""
  module = dataplex_api.GetMessageModule()
  content = module.GoogleCloudDataplexV1Content(
      dataText=args.data_text,
      description=args.description,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Content,
                                       args),
      path=args.path)
  if args.kernel_type:
    content.notebook = GenerateNotebook(args)
  if args.query_engine:
    content.sqlScript = GenerateSqlScript(args)
  return content


def GenerateContentForUpdateRequest(args):
  """Creates Content for Message Update Requests."""
  module = dataplex_api.GetMessageModule()
  content = module.GoogleCloudDataplexV1Content(
      dataText=args.data_text,
      description=args.description,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Content,
                                       args),
      path=args.path)
  if args.kernel_type:
    content.notebook = GenerateNotebook(args)
  if args.query_engine:
    content.sqlScript = GenerateSqlScript(args)
  return content


def GenerateNotebook(args):
  """Creates Notebook field for Content Message Create/Update Requests."""
  module = dataplex_api.GetMessageModule()
  kernel_type_field = module.GoogleCloudDataplexV1ContentNotebook
  notebook = module.GoogleCloudDataplexV1ContentNotebook()
  if args.kernel_type:
    notebook.kernelType = kernel_type_field.KernelTypeValueValuesEnum(
        args.kernel_type)
  return notebook


def GenerateSqlScript(args):
  """Creates SQL Script field for Content Message Create/Update Requests."""
  module = dataplex_api.GetMessageModule()
  query_engine_field = module.GoogleCloudDataplexV1ContentSqlScript
  sql_script = module.GoogleCloudDataplexV1ContentSqlScript()
  if args.query_engine:
    sql_script.engine = query_engine_field.EngineValueValuesEnum(
        args.query_engine)
  return sql_script


def GenerateUpdateMask(args):
  """Creates Update Mask for Content."""
  args_api_field_map = {
      'description': 'description',
      'labels': 'labels',
      'path': 'path',
      'query_engine': 'sqlScript.engine',
      'kernel_type': 'notebook.kernelType',
      'data_text': 'data_text'
  }
  update_mask = []

  for k, v in args_api_field_map.items():
    if args.IsSpecified(k):
      update_mask.append(v)
  return update_mask


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_lakes_content)
