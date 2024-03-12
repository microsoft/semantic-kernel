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
"""Client for interaction with Environment API CRUD DATAPLEX."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataplex import util as dataplex_api
from googlecloudsdk.command_lib.iam import iam_util


def SetIamPolicy(environment_ref, policy):
  """Set Iam Policy request."""
  set_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesEnvironmentsSetIamPolicyRequest(
      resource=environment_ref.RelativeName(),
      googleIamV1SetIamPolicyRequest=dataplex_api.GetMessageModule()
      .GoogleIamV1SetIamPolicyRequest(policy=policy))
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_environments.SetIamPolicy(set_iam_policy_req)


def GetIamPolicy(environment_ref):
  """Get Iam Policy request."""
  get_iam_policy_req = dataplex_api.GetMessageModule(
  ).DataplexProjectsLocationsLakesEnvironmentsGetIamPolicyRequest(
      resource=environment_ref.RelativeName())
  return dataplex_api.GetClientInstance(
  ).projects_locations_lakes_environments.GetIamPolicy(get_iam_policy_req)


def AddIamPolicyBinding(environment_ref, member, role):
  """Add IAM policy binding request."""
  policy = GetIamPolicy(environment_ref)
  iam_util.AddBindingToIamPolicy(
      dataplex_api.GetMessageModule().GoogleIamV1Binding, policy, member, role)
  return SetIamPolicy(environment_ref, policy)


def RemoveIamPolicyBinding(environment_ref, member, role):
  """Remove IAM policy binding request."""
  policy = GetIamPolicy(environment_ref)
  iam_util.RemoveBindingFromIamPolicy(policy, member, role)
  return SetIamPolicy(environment_ref, policy)


def SetIamPolicyFromFile(environment_ref, policy_file):
  """Set IAM policy binding request from file."""
  policy = iam_util.ParsePolicyFile(
      policy_file,
      dataplex_api.GetMessageModule().GoogleIamV1Policy)
  return SetIamPolicy(environment_ref, policy)


def GenerateInfrastructureSpec(args):
  """Generate InfrastructureSpec From Arguments."""
  module = dataplex_api.GetMessageModule()
  compute_resource = module.GoogleCloudDataplexV1EnvironmentInfrastructureSpecComputeResources(
      diskSizeGb=args.compute_disk_size_gb,
      nodeCount=args.compute_node_count,
      maxNodeCount=args.compute_max_node_count)
  os_image_runtime = module.GoogleCloudDataplexV1EnvironmentInfrastructureSpecOsImageRuntime(
      imageVersion=args.os_image_version,
      javaLibraries=args.os_image_java_libraries,
      pythonPackages=args.os_image_python_packages,
      properties=args.os_image_properties)
  infrastructure_spec = module.GoogleCloudDataplexV1EnvironmentInfrastructureSpec(
      compute=compute_resource, osImage=os_image_runtime)
  return infrastructure_spec


def GenerateSessionSpec(args):
  """Generate SessionSpec From Arguments."""
  module = dataplex_api.GetMessageModule()
  session_spec = module.GoogleCloudDataplexV1EnvironmentSessionSpec(
      enableFastStartup=args.session_enable_fast_startup,
      maxIdleDuration=args.session_max_idle_duration)
  return session_spec


def GenerateEnvironmentForCreateRequest(args):
  """Create Environment for Message Create Requests."""
  module = dataplex_api.GetMessageModule()
  request = module.GoogleCloudDataplexV1Environment(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Environment,
                                       args),
      infrastructureSpec=GenerateInfrastructureSpec(args),
      sessionSpec=GenerateSessionSpec(args))
  return request


def GenerateEnvironmentForUpdateRequest(args):
  """Create Environment for Message Update Requests."""
  module = dataplex_api.GetMessageModule()
  return module.GoogleCloudDataplexV1Environment(
      description=args.description,
      displayName=args.display_name,
      labels=dataplex_api.CreateLabels(module.GoogleCloudDataplexV1Environment,
                                       args),
      infrastructureSpec=GenerateInfrastructureSpec(args),
      sessionSpec=GenerateSessionSpec(args))


def GenerateUpdateMask(args):
  """Create Update Mask for Environments."""
  update_mask = []
  if args.IsSpecified('description'):
    update_mask.append('description')
  if args.IsSpecified('display_name'):
    update_mask.append('displayName')
  if args.IsSpecified('labels'):
    update_mask.append('labels')
  if args.IsSpecified('compute_disk_size_gb'):
    update_mask.append('infrastructureSpec.compute.diskSizeGb')
  if args.IsSpecified('compute_node_count'):
    update_mask.append('infrastructureSpec.compute.nodeCount')
  if args.IsSpecified('compute_max_node_count'):
    update_mask.append('infrastructureSpec.compute.maxNodeCount')
  if args.IsSpecified('os_image_version'):
    update_mask.append('infrastructureSpec.osImage.imageVersion')
  if args.IsSpecified('os_image_java_libraries'):
    update_mask.append('infrastructureSpec.osImage.javaLibraries')
  if args.IsSpecified('os_image_python_packages'):
    update_mask.append('infrastructureSpec.osImage.pythonPackages')
  if args.IsSpecified('os_image_properties'):
    update_mask.append('infrastructureSpec.osImage.properties')
  if args.IsSpecified('session_max_idle_duration'):
    update_mask.append('sessionSpec.maxIdleDuration')
  if args.IsSpecified('session_enable_fast_startup'):
    update_mask.append('sessionSpec.enableFastStartup')
  return update_mask


def WaitForOperation(operation):
  """Waits for the given google.longrunning.Operation to complete."""
  return dataplex_api.WaitForOperation(
      operation,
      dataplex_api.GetClientInstance().projects_locations_lakes_environments)
