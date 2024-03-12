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
"""This file provides the implementation of the `functions remove-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v1 import util
from googlecloudsdk.command_lib.iam import iam_util


def Run(args):
  """Remove a binding from the IAM policy for a Google Cloud Function."""
  client = util.GetApiClientInstance()
  messages = client.MESSAGES_MODULE
  function_ref = args.CONCEPTS.name.Parse()
  policy = client.projects_locations_functions.GetIamPolicy(
      messages.CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
          resource=function_ref.RelativeName()))
  iam_util.RemoveBindingFromIamPolicy(policy, args.member, args.role)
  return client.projects_locations_functions.SetIamPolicy(
      messages.CloudfunctionsProjectsLocationsFunctionsSetIamPolicyRequest(
          resource=function_ref.RelativeName(),
          setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy)))
