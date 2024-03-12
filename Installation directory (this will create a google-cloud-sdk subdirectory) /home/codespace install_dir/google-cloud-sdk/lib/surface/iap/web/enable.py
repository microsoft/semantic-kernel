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

"""Enable Identity-Aware Proxy."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iap import util as iap_util


class Enable(base.Command):
  """Enable Cloud Identity-Aware Proxy (Cloud IAP) on an IAP resource.

  This command enables Cloud Identity-Aware Proxy on an IAP resource. OAuth 2.0
  credentials must be set, or must have been previously set, to enable IAP.
  """
  detailed_help = {
      'EXAMPLES':
          """\
          To enable IAP on an App Engine application, run:

            $ {command} --resource-type=app-engine
                --oauth2-client-id=CLIENT_ID --oauth2-client-secret=SECRET

          To enable IAP on a backend service, run:

            $ {command} --resource-type=backend-services
                --oauth2-client-id=CLIENT_ID --oauth2-client-secret=SECRET
                --service=SERVICE_ID
  """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
          to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddIapResourceArgs(parser)
    iap_util.AddOauthClientArgs(parser)
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter.
    """
    iap_ref = iap_util.ParseIapResource(self.ReleaseTrack(), args)
    return iap_ref.Enable(args.oauth2_client_id, args.oauth2_client_secret)
