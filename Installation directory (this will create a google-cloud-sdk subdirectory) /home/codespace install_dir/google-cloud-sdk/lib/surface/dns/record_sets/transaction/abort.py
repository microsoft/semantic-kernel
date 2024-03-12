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

"""gcloud dns record-sets transaction abort command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.dns import transaction_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import flags
from googlecloudsdk.core import log


class Abort(base.Command):
  """Abort transaction.

  This command aborts the transaction and deletes the transaction file.

  ## EXAMPLES

  To abort the transaction, run:

    $ {command} --zone=MANAGED_ZONE
  """

  @staticmethod
  def Args(parser):
    flags.GetZoneArg().AddToParser(parser)

  def Run(self, args):
    if not os.path.isfile(args.transaction_file):
      raise transaction_util.TransactionFileNotFound(
          'Transaction not found at [{0}]'.format(args.transaction_file))

    os.remove(args.transaction_file)

    log.status.Print('Aborted transaction [{0}].'.format(args.transaction_file))
