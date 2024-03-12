# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command to describe service account identity bindings."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.iam import util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.iam import iam_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a service account identity binding."""

  @staticmethod
  def Args(parser):
    parser.add_argument(
        'binding_id',
        metavar='BINDING-ID',
        help='The ID of the identity binding.')
    parser.add_argument(
        '--service-account',
        required=True,
        type=iam_util.GetIamAccountFormatValidator(),
        help='The service account with the identity binding.')

  def Run(self, args):
    client, messages = util.GetClientAndMessages()
    req = messages.IamProjectsServiceAccountsIdentityBindingsDeleteRequest(
        name=iam_util.EmailAndIdentityBindingToResourceName(
            args.service_account, args.binding_id))

    console_io.PromptContinue(
        message='You are about to delete identity binding [{0}] on service '
        'account [{1}].'.format(args.binding_id, args.service_account),
        cancel_on_no=True)

    client.projects_serviceAccounts_identityBindings.Delete(req)

    log.status.Print(
        'Deleted identity binding [{0}] on service account [{1}]'.format(
            args.binding_id, args.service_account))
