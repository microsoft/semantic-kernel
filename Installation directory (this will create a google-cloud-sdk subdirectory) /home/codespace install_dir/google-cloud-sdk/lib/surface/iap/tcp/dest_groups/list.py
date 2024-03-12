# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Create IAP TCP Destination Group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iap import util as iap_util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class List(base.ListCommand):
  """Lists the IAP TCP Destination Group resource."""
  detailed_help = {
      'EXAMPLES':
          """\

          To list all Destination Groups in the current project run:

          $ {command}

          To list all Destination Groups in region ``REGION'' in the current
          project run:

          $ {command} --region=REGION

          To limit the results returned by the server to be at most ``PAGE_SIZE'',
          run:

          $ {command} --page-size=PAGE_SIZE

          To list at most `5` Destination Groups sorted alphabetically by project
          ID, run:

          $ {command} --sort-by=projectId --limit=5

          To list all Destination Groups in the project ``PROJECT'' run:

          $ {command} --project=PROJECT

          To list all Destination Groups that have cidr ``CIDR'' run:

          $ {command} --filter="cidrs=CIDR"

          To list all Destination Groups that have FQDN ``FQDN'' run:

          $ {command} --filter="fqdns=FQDN"

          To list all Destination Groups that have name ``NAME'' run:

          $ {command} --filter="name=NAME"
          """,
  }

  @staticmethod
  def Args(parser):
    """Registers flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    iap_util.AddDestGroupListRegionArgs(parser)
    # Remove unsupported default List flags.
    base.URI_FLAG.RemoveFromParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command.

    Args:
      args: An argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      The specified function with its description and configured filter
    """
    iap_setting_ref = iap_util.ParseIapDestGroupResourceWithNoGroupId(
        self.ReleaseTrack(), args)
    results_to_yield = iap_setting_ref.List(args.page_size, args.limit)
    # The List method will return a generator to yield the next values. If we
    # return it directly, it will work with gcloud but the Displayer class in
    # calliope won't be able to apply any filters to it.
    # So we will make it a litst first before returning.
    return list(results_to_yield)
