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
"""This file provides the implementation of the `functions add-iam-policy-binding` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.command_lib.functions import run_util
from googlecloudsdk.command_lib.functions.v2.add_invoker_policy_binding import command as add_invoker_policy_binding_command
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def Run(args, release_track):
  """Adds a binding to the IAM policy for a Google Cloud Function.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.
    release_track: The relevant value from the
      googlecloudsdk.calliope.base.ReleaseTrack enum.

  Returns:
    The updated IAM policy.
  """
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)

  function_ref = args.CONCEPTS.name.Parse()
  function_relative_name = function_ref.RelativeName()

  if args.role == 'roles/run.invoker':
    log.warning(
        'The role [roles/run.invoker] cannot be bound to a Cloud Function IAM'
        ' policy as it is a Cloud Run role. For 2nd gen functions, this role'
        ' must be granted on the underlying Cloud Run service. This'
        ' can be done by running the `gcloud functions'
        ' add-invoker-policy-binding` comand.\n'
    )

    if console_io.CanPrompt() and console_io.PromptContinue(
        prompt_string=(
            'Would you like to run this command instead and grant [{}]'
            ' permission to invoke function [{}]'.format(
                args.member, function_ref.Name()
            )
        )
    ):
      return add_invoker_policy_binding_command.Run(args, release_track)

  policy = client.projects_locations_functions.GetIamPolicy(
      messages.CloudfunctionsProjectsLocationsFunctionsGetIamPolicyRequest(
          resource=function_relative_name))

  iam_util.AddBindingToIamPolicy(
      messages.Binding, policy, args.member, args.role
  )

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
        'The role [{role}] was successfully bound to member [{member}] but this'
        ' does not grant the member permission to invoke 2nd gen function'
        ' [{name}]. Instead, the role [roles/run.invoker] must be granted on'
        ' the underlying Cloud Run service. This can be done by running the'
        ' `gcloud functions add-invoker-policy-binding` command.\n'.format(
            role=args.role, member=args.member, name=function_ref.Name()
        )
    )

    if console_io.CanPrompt() and console_io.PromptContinue(
        prompt_string=(
            'Would you like to run this command and additionally grant [{}]'
            ' permission to invoke function [{}]'
        ).format(args.member, function_ref.Name()),
    ):
      function = client.projects_locations_functions.Get(
          messages.CloudfunctionsProjectsLocationsFunctionsGetRequest(
              name=function_ref.RelativeName()
          )
      )
      run_util.AddOrRemoveInvokerBinding(
          function, args.member, add_binding=True
      )
      log.status.Print(
          'The role [roles/run.invoker] was successfully bound to the'
          ' underlying Cloud Run service. You can view its IAM policy by'
          ' running:\n'
          'gcloud run services get-iam-policy {}\n'.format(
              function.serviceConfig.service
          )
      )
      return policy

    log.status.Print(
        'Additional information on authenticating function calls can be found'
        ' at:\n'
        'https://cloud.google.com/functions/docs/securing/authenticating#authenticating_function_to_function_calls'
    )

  return policy
