# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Client for interaction with Tasks API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(task_ref, policy):
  """Set IAM Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule().DataplexProjectsLocationsLakesTasksSetIamPolicyRequest(
      resource=task_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule().GoogleIamV1SetIamPolicyRequest(
          policy=policy
      ),
  )
  return dataplex_api.GetClientInstance().projects_locations_lakes_tasks.SetIamPolicy(
      set_iam_policy_req
  )


def GetIamPolicy(task_ref):
  """Get IAM Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule().DataplexProjectsLocationsLakesTasksGetIamPolicyRequest(
      resource=task_ref.RelativeName()
  )
  return dataplex_api.GetClientInstance().projects_locations_lakes_tasks.GetIamPolicy(
      get_iam_policy_req
  )


def AddIamPolicyBinding(task_ref, member, role):
  """Add IAM policy binding request."""
  policy = GetIamPolicy(task_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role
  )
  return SetIamPolicy(task_ref, policy)


def RemoveIamPolicyBinding(task_ref, member, role):
  """Remove IAM policy binding request."""
  policy = GetIamPolicy(task_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(task_ref, policy)


def SetIamPolicyFromFile(task_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file, dataplex_api.GetMessageModule().GoogleIamV1Policy
  )
  return SetIamPolicy(task_ref, policy)


def RunTask(task_ref, args):
  """Runs dataplex task with input updates to execution spec args and labels."""
  run_task_req = dataplex_api.GetMessageModule().DataplexProjectsLocationsLakesTasksRunRequest(
      name=task_ref.RelativeName(),
      googleCloudDataplexV1RunTaskRequest=dataplex_api.GetMessageModule().GoogleCloudDataplexV1RunTaskRequest(
          labels=dataplex_api.CreateLabels(
              dataplex_api.GetMessageModule().GoogleCloudDataplexV1RunTaskRequest,
              args,
          ),
          args=CreateArgs(
              dataplex_api.GetMessageModule().GoogleCloudDataplexV1RunTaskRequest,
              args,
          ),
      ),
  )
  run_task_response = (
      dataplex_api.GetClientInstance().projects_locations_lakes_tasks.Run(
          run_task_req
      )
  )
  return run_task_response


def CreateArgs(run_task_request, args):
  """Creates Args input compatible for creating a RunTaskRequest object."""
  if getattr(args, "ARGS", None):
    args_ref = dataplex_api.FetchExecutionSpecArgs(args.ARGS)
    if len(args_ref) > 0:
      return run_task_request.ArgsValue(
          additionalProperties=[
              run_task_request.ArgsValue.AdditionalProperty(
                  key=key, value=value
              )
              for key, value in sorted(args_ref.items())
          ]
      )
  return None
