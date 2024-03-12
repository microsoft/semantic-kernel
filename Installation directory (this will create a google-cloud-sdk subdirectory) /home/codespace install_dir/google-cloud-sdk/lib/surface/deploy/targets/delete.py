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
"""Deletes a Gcloud Deploy delivery target resource."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.clouddeploy import client_util
from googlecloudsdk.api_lib.util import exceptions as gcloud_exception
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.deploy import exceptions as deploy_exceptions
from googlecloudsdk.command_lib.deploy import resource_args
from googlecloudsdk.command_lib.deploy import target_util

_DETAILED_HELP = {
    'DESCRIPTION':
        '{description}',
    'EXAMPLES':
        textwrap.dedent("""\
        To delete a target called 'test-target' in region 'us-central1', run:

          $ {command} test-target --region=us-central1
        """)
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Deletes a Cloud Deploy target."""
  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    resource_args.AddTargetResourceArg(parser, positional=True)

  @gcloud_exception.CatchHTTPErrorRaiseHTTPException(
      deploy_exceptions.HTTP_ERROR_FORMAT
  )
  def Run(self, args):
    """Entry point of the export command.

    Args:
      args: argparse.Namespace, An object that contains the values for the
        arguments specified in the .Args() method.
    """
    target_ref = args.CONCEPTS.target.Parse()
    op = target_util.DeleteTarget(target_ref.RelativeName())
    client_util.OperationsClient().CheckOperationStatus(
        {target_ref.RelativeName(): op}, 'Deleted Cloud Deploy target: {}.')
