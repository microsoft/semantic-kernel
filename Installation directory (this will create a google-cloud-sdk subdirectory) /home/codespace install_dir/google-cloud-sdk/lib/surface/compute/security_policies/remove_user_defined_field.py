# -*- coding: utf-8 -*- #
# Copyright 2023 Google Inc. All Rights Reserved.
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
"""Command for removing user defined fields from security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute.security_policies import flags


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class RemoveUserDefinedFieldAlpha(base.UpdateCommand):
  """Remove a user defined field from a Compute Engine security policy.

  *{command}* is used to remove user defined fields from security policies.

  ## EXAMPLES

  To remove a user defined field run this:

    $ {command} SECURITY_POLICY --user-defined-field-name=my-field
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyRegionalArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='update')
    parser.add_argument(
        '--user-defined-field-name',
        required=True,
        help='The name of the user defined field to remove.',
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.SECURITY_POLICY_ARG.ResolveAsResource(args, holder.resources)
    security_policy = client.SecurityPolicy(
        ref=ref, compute_client=holder.client
    )
    existing_security_policy = security_policy.Describe()[0]

    existing_user_defined_fields = existing_security_policy.userDefinedFields
    new_user_defined_fields = []
    for user_defined_field in existing_user_defined_fields:
      if user_defined_field.name != args.user_defined_field_name:
        new_user_defined_fields.append(user_defined_field)

    if len(existing_user_defined_fields) == len(new_user_defined_fields):
      raise exceptions.InvalidArgumentException(
          '--user-defined-field-name',
          'user defined field does not exist in this policy.',
      )

    updated_security_policy = holder.client.messages.SecurityPolicy(
        userDefinedFields=new_user_defined_fields,
        fingerprint=existing_security_policy.fingerprint,
    )

    field_mask = 'user_defined_fields' if not new_user_defined_fields else None

    return security_policy.Patch(
        security_policy=updated_security_policy, field_mask=field_mask
    )
