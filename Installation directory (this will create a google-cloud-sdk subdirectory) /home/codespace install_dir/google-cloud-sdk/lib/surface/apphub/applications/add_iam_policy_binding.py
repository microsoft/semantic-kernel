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
"""Add IAM policy binding to an application."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.apphub import utils as api_lib_utils
from googlecloudsdk.api_lib.apphub.applications import client as apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apphub import flags
from googlecloudsdk.command_lib.iam import iam_util


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """\
        To add an IAM policy binding for the role of `roles/apphub.viewer`
        for the user `test-user@gmail.com` to Application `my-app` in location
        `us-east1`, run:

          $ {command} my-app --location=us-east1 --role=roles/apphub.viewer --member=user:test-user@gmail.com
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.GA)
class AddIamPolicyBindingGA(base.Command):
  """Add IAM policy binding to an Apphub application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddAddIamPolicyBindingFlags(parser)
    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    client = apis.ApplicationsClient(release_track=base.ReleaseTrack.GA)
    app_ref = api_lib_utils.GetApplicationRef(args)
    return client.AddIamPolicyBinding(
        app_id=app_ref.RelativeName(), member=args.member, role=args.role
    )


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AddIamPolicyBindingAlpha(base.Command):
  """Add IAM policy binding to an Apphub application."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddAddIamPolicyBindingFlags(parser)
    iam_util.AddArgsForAddIamPolicyBinding(parser)

  def Run(self, args):
    client = apis.ApplicationsClient(release_track=base.ReleaseTrack.ALPHA)
    app_ref = api_lib_utils.GetApplicationRef(args)
    return client.AddIamPolicyBinding(
        app_id=app_ref.RelativeName(), member=args.member, role=args.role
    )
