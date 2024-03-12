# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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

"""Get IAM Policy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class GetIamPolicy(base.ListCommand):
  """Get IAM policy for an IAP IAM resource.

  *{command}* displays the IAM policy associated with an IAP IAM
  resource. If formatted as JSON, the output can be edited and used as a policy
  file for set-iam-policy. The output includes an "etag" field
  identifying the version emitted and allowing detection of
  concurrent policy updates; see
  $ {parent_command} set-iam-policy for additional details.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To get the IAM policy for the web accesses to the IAP protected
          resources within the active project,
          run:

            $ {command}

          To get the IAM policy for the web accesses to the IAP protected
          resources within a project, run:

            $ {command} --project=PROJECT_ID

          To get the IAM policy for the web accesses to the IAP protected
          resources within an App Engine application, run:

            $ {command} --resource-type=app-engine

          To get the IAM policy for the web accesses to the IAP protected
          resources within an App Engine service, run:

            $ {command} --resource-type=app-engine --service=SERVICE_ID

          To get the IAM policy for the web accesses to the IAP protected
          resources within an App Engine service version, run:

            $ {command} --resource-type=app-engine --service=SERVICE_ID
                --version=VERSION

          To get the IAM policy for the web accesses to the IAP protected
          resources within all backend services, run:

            $ {command} --resource-type=backend-services

          To get the IAM policy for the web accesses to the IAP protected
          resources within a backend service, run:

            $ {command} --resource-type=backend-services --service=SERVICE_ID
  """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddIapIamResourceArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    iap_iam_ref = iap_util.ParseIapIamResource(self.ReleaseTrack(), args)
    return iap_iam_ref.GetIamPolicy()


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetIamPolicyALPHA(GetIamPolicy):
  """Get IAM policy for an IAP IAM resource.

  *{command}* displays the IAM policy associated with an IAP IAM
  resource. If formatted as JSON, the output can be edited and used as a policy
  file for set-iam-policy. The output includes an "etag" field
  identifying the version emitted and allowing detection of
  concurrent policy updates; see
  $ {parent_command} set-iam-policy for additional details.
  """

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddIapIamResourceArgs(parser, use_region_arg=True)
    base.URI_FLAG.RemoveFromParser(parser)
