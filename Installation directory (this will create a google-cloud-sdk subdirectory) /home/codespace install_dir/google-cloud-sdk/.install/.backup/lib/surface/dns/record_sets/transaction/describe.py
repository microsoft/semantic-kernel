# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""gcloud dns record-sets transaction describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags


class Describe(base.DescribeCommand):
  """Describe the transaction.

  This command displays the contents of the transaction.

  ## EXAMPLES

  To look at the contents of the transaction, run:

    $ {command} --zone=MANAGED_ZONE
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)

  def Run(self, args):
    api_version = 'v1'
    # If in the future there are differences between API version, do NOT use
    # this patter of checking ReleaseTrack. Break this into multiple classes.
    if self.ReleaseTrack() == base.ReleaseTrack.BETA:
      api_version = 'v1beta2'
    elif self.ReleaseTrack() == base.ReleaseTrack.ALPHA:
      api_version = 'v1alpha2'

    with transaction_util.TransactionFile(args.transaction_file) as trans_file:
      return transaction_util.ChangeFromYamlFile(
          trans_file, api_version=api_version)
