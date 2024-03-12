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
"""Command for adding user defined fields to security policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute.security_policies import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute.security_policies import flags
from googlecloudsdk.command_lib.compute.security_policies import security_policies_utils


@base.ReleaseTracks(
    base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA, base.ReleaseTrack.GA
)
class AddUserDefinedField(base.UpdateCommand):
  r"""Add a user defined field to a Compute Engine security policy.

  *{command}* is used to add user defined fields to security policies.

  ## EXAMPLES

  To add a user defined field run this:

    $ {command} SECURITY_POLICY \
       --user-defined-field-name=my-field \
       --base=ipv6 \
       --offset=10 \
       --size=3
  """

  SECURITY_POLICY_ARG = None

  @classmethod
  def Args(cls, parser):
    cls.SECURITY_POLICY_ARG = flags.SecurityPolicyRegionalArgument()
    cls.SECURITY_POLICY_ARG.AddArgument(parser, operation_type='update')
    parser.add_argument(
        '--user-defined-field-name',
        required=True,
        help='The name for the user defined field.'
    )
    parser.add_argument(
        '--base',
        choices=['ipv4', 'ipv6', 'tcp', 'udp'],
        required=True,
        help='The base relative to which offset is measured.',
    )
    parser.add_argument(
        '--offset',
        type=int,
        required=True,
        help=(
            'Offset of the first byte of the field (in network byte order)'
            ' relative to base.'
        ),
    )
    parser.add_argument(
        '--size',
        type=int,
        required=True,
        help='Size of the field in bytes. Valid values: 1-4.',
    )
    parser.add_argument(
        '--mask',
        help=(
            'If specified, apply this mask (bitwise AND) to the field to ignore'
            ' bits before matching. Encoded as a hexadecimal number (starting '
            'with "0x").'
        ),
    )

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    ref = self.SECURITY_POLICY_ARG.ResolveAsResource(args, holder.resources)
    security_policy = client.SecurityPolicy(
        ref=ref, compute_client=holder.client
    )
    existing_security_policy = security_policy.Describe()[0]

    user_defined_field = security_policies_utils.CreateUserDefinedField(
        holder.client, args
    )
    user_defined_fields = existing_security_policy.userDefinedFields
    user_defined_fields.append(user_defined_field)

    updated_security_policy = holder.client.messages.SecurityPolicy(
        userDefinedFields=user_defined_fields,
        fingerprint=existing_security_policy.fingerprint,
    )

    return security_policy.Patch(security_policy=updated_security_policy)
