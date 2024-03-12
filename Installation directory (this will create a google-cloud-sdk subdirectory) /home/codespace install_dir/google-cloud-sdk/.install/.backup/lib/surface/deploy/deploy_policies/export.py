# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Exports a Cloud Deploy deploy policy resource."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.clouddeploy import deploy_policy
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import export_util
from googlecloudsdk.command_lib.deploy import manifest_util
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.export import util as core_export_util

_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': textwrap.dedent("""\

      To return the .yaml definition of the deploy policy `test-policy`, in region `us-central1`, run:

        $ {command} test-policy --region=us-central1

      """),
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Export(base.ExportCommand):
  """Returns the .yaml definition of the specified deploy policy.

  The exported yaml definition can be applied by `deploy apply` command.
  """

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddDeployPolicyResourceArg(parser, positional=True)
    core_export_util.AddExportFlags(parser)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    """Entry point of the export command.

    Args:
      args: argparser.Namespace, an object that contains the values for the
        arguments specified in the .Args() method.
    """
    deploy_policy_type_ref = args.CONCEPTS.deploy_policy.Parse()
    resource = deploy_policy.DeployPoliciesClient().Get(
        deploy_policy_type_ref.RelativeName()
    )

    manifest = manifest_util.ProtoToManifest(
        resource, deploy_policy_type_ref, manifest_util.DEPLOY_POLICY_KIND
    )

    export_util.Export(manifest, args)
