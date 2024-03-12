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
"""Create command to create a new resource of threat prevention profile."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.network_security.security_profiles.threat_prevention import sp_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.network_security import sp_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION': """

          Create a new Security Profile with the given name.

        """,
    'EXAMPLES': """
          To create a Security Profile with the name `my-security-profile` and an optional description as `New Security Profile`, run:

              $ {command} my-security-profile --description="New Security Profile"

        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class CreateProfile(base.CreateCommand):
  """Create a new Threat Prevention Profile."""

  @classmethod
  def Args(cls, parser):
    sp_flags.AddSecurityProfileResource(parser, cls.ReleaseTrack())
    sp_flags.AddProfileDescription(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    client = sp_api.Client(self.ReleaseTrack())
    security_profile = args.CONCEPTS.security_profile.Parse()
    description = args.description
    labels = labels_util.ParseCreateArgs(
        args, client.messages.SecurityProfile.LabelsValue
    )
    is_async = args.async_

    if not args.IsSpecified('description'):
      args.description = 'Security Profile of type Threat Prevention'

    if args.location != 'global':
      raise core_exceptions.Error(
          'Only `global` location is supported, but got: %s' % args.location
      )

    response = client.CreateSecurityProfile(
        name=security_profile.RelativeName(),
        sp_id=security_profile.Name(),
        parent=security_profile.Parent().RelativeName(),
        description=description,
        labels=labels,
    )

    # Return the in-progress operation if async is requested.
    if is_async:
      operation_id = response.name
      log.status.Print(
          'Check for operation completion status using operation ID:',
          operation_id,
      )
      return response

    # Default operation poller if async is not specified.
    return client.WaitForOperation(
        operation_ref=client.GetOperationsRef(response),
        message='Waiting for security-profile [{}] to be created'.format(
            security_profile.RelativeName()
        ),
        has_result=True,
    )


CreateProfile.detailed_help = DETAILED_HELP
