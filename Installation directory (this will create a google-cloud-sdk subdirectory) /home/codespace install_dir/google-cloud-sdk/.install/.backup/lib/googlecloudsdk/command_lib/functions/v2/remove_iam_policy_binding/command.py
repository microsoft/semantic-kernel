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

from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.command_lib.functions import run_util
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def Run(args, release_track):
  """Removes a binding from the IAM policy for a Google Cloud Function."""
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)

  function_ref = args.CONCEPTS.name.Parse()
  function_relative_name = function_ref.RelativeName()

  policy = client.projects_locations_functions.GetIamPolicy(
      messages.CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
          resource=function_relative_name
      )
  )

  iam_util.RemoveBindingFromIamPolicy(policy, args.member, args.role)

  policy = client.projects_locations_functions.SetIamPolicy(
      messages.CloudfunctionsProjectsLocationsFunctionsSetIamPolicyRequest(
          resource=function_relative_name,
          setIamPolicyRequest=messages.SetIamPolicyRequest(policy=policy),
      )
  )

  if args.role in [
      'roles/cloudfunctions.admin',
      'roles/cloudfunctions.developer',
      'roles/cloudfunctions.invoker',
  ]:
    log.warning(
        'The binding between member {member} and role {role} has been'
        ' successfully removed. However, to make sure the member {member}'
        " doesn't have the permission to invoke the 2nd gen function, you need"
        ' to remove the invoker binding in the underlying Cloud Run service.'
        ' This can be done by running the following command:\n '
        ' gcloud functions remove-invoker-policy-binding {function_ref}'
        ' --member={member} \n'.format(
            member=args.member, role=args.role, function_ref=function_ref.Name()
        )
    )
    if console_io.CanPrompt() and console_io.PromptContinue(
        prompt_string=(
            'Would you like to run this command and additionally deny [{}]'
            ' permission to invoke function [{}]'
        ).format(args.member, function_ref.Name()),
    ):
      function = client.projects_locations_functions.Get(
          messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
              name=function_ref.RelativeName()
          )
      )
      run_util.AddOrRemoveInvokerBinding(
          function, args.member, add_binding=False
      )
      log.status.Print(
          'The role [roles/run.invoker] was successfully removed for member '
          '{member} in the underlying Cloud Run service. You can view '
          'its IAM policy by running:\n'
          'gcloud run services get-iam-policy {service}\n'.format(
              service=function.serviceConfig.service, member=args.member
          )
      )

  return policy
