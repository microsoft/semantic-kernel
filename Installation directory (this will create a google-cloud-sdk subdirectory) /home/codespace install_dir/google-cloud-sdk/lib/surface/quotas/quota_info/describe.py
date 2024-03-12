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
"""QuotaInfo get command."""

from googlecloudsdk.api_lib.quotas import quota_info
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.quotas import flags


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Get QuotaInfo for a consumer.

  This command gets a specific quota info for a consumer. The supported
  consumers can be projects, folders, or organizations.

  ## EXAMPLES

  To get the details of quota `CpusPerProject` for service
  `example.googleapis.com` and consumer `projects/my-project`, run:

    $ {command} CpusPerProject --service=example.googleapis.com
    --project=my-project


  To get the details of quota `CpusPerProject` for service
  `example.googleapis.com` and consumer `folders/12345`, run:

    $ {command} CpusPerProject --service=example.googleapis.com --folder=12345
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    flags.QuotaId().AddToParser(parser)
    flags.AddConsumerFlags(parser, 'quota info to describe')
    flags.Service().AddToParser(parser)

  def Run(self, args):
    """Run command.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The requested QuotaInfo for the service and consumer.
    """
    return quota_info.GetQuotaInfo(args)
