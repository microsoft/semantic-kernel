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
"""Command to authorize accounts for transfer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import os

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.credentials import creds
from googlecloudsdk.core.credentials import store as creds_store
from googlecloudsdk.core.util import files

EXPECTED_USER_ROLES = frozenset([
    'roles/owner',
    'roles/storagetransfer.admin',
    'roles/storagetransfer.transferAgent',
    'roles/storage.objectAdmin',
    'roles/pubsub.editor',
])
EXPECTED_P4SA_ROLES = frozenset([
    'roles/storage.admin',
    'roles/storagetransfer.serviceAgent',
])


def _get_iam_prefixed_email(email_string, is_service_account):
  """Returns an email format useful for interacting with IAM APIs."""
  iam_prefix = 'serviceAccount' if is_service_account else 'user'
  return '{}:{}'.format(iam_prefix, email_string)


def _get_existing_transfer_roles_for_account(project_iam_policy,
                                             prefixed_account_email, roles_set):
  """Returns roles in IAM policy from roles_set assigned to account email."""
  roles = set()
  # iam_policy.bindings structure:
  # list[<Binding
  #       members=['serviceAccount:member@thing.iam.gserviceaccount.com', ...],
  #       role='roles/somerole'>...]
  for binding in project_iam_policy.bindings:
    if (any([m == prefixed_account_email for m in binding.members]) and
        binding.role in roles_set):
      roles.add(binding.role)
  return roles


class Authorize(base.Command):
  """Authorize an account for all Transfer Service features."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Authorize a Google account for all Transfer Service features.

      This command provides admin and owner rights for simplicity. If that's
      too much authority for your use case, see custom setups here:
      https://cloud.google.com/storage-transfer/docs/on-prem-set-up
      """,
      'EXAMPLES':
          """\
      To see what Transfer Service IAM roles the account logged into gcloud may
      be missing, run:

        $ {command}

      To add the missing IAM roles, run:

        $ {command} --add-missing

      To check a custom service account for missing roles, run:

        $ {command} --creds-file=path/to/service-account-key.json
      """
  }

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--creds-file',
        help='The path to the creds file for an account to authorize.'
        ' The file should be in JSON format and contain a "type" and'
        ' "client_email", which are automatically generated for most'
        ' creds files downloaded from Google (e.g. service account tokens).'
        ' If this flag is not present, the command authorizes the user'
        ' currently logged into gcloud.')
    parser.add_argument(
        '--add-missing',
        action='store_true',
        help='Add IAM roles necessary to use all Transfer Service'
        ' features to the specified account. By default, this command just'
        ' prints missing roles.')

  def Run(self, args):
    client = apis.GetClientInstance('storagetransfer', 'v1')
    messages = apis.GetMessagesModule('storagetransfer', 'v1')

    if args.creds_file:
      expanded_file_path = os.path.abspath(os.path.expanduser(args.creds_file))
      with files.FileReader(expanded_file_path) as file_reader:
        try:
          parsed_creds_file = json.load(file_reader)
          account_email = parsed_creds_file['client_email']
          is_service_account = parsed_creds_file['type'] == 'service_account'
        except (ValueError, KeyError) as e:
          log.error(e)
          raise ValueError('Invalid creds file format.'
                           ' Run command with "--help" flag for more details.')
        prefixed_account_email = _get_iam_prefixed_email(
            account_email, is_service_account)
    else:
      account_email = properties.VALUES.core.account.Get()
      is_service_account = creds.IsServiceAccountCredentials(creds_store.Load())
      prefixed_account_email = _get_iam_prefixed_email(account_email,
                                                       is_service_account)

    project_id = properties.VALUES.core.project.Get()
    parsed_project_id = projects_util.ParseProject(project_id)
    project_iam_policy = projects_api.GetIamPolicy(parsed_project_id)

    existing_user_roles = _get_existing_transfer_roles_for_account(
        project_iam_policy, prefixed_account_email, EXPECTED_USER_ROLES)
    log.status.Print('User {} has roles:\n{}'.format(account_email,
                                                     list(existing_user_roles)))
    missing_user_roles = EXPECTED_USER_ROLES - existing_user_roles
    log.status.Print('Missing roles:\n{}'.format(list(missing_user_roles)))

    all_missing_role_tuples = [
        (prefixed_account_email, role) for role in missing_user_roles
    ]

    log.status.Print('***')

    transfer_p4sa_email = client.googleServiceAccounts.Get(
        messages.StoragetransferGoogleServiceAccountsGetRequest(
            projectId=project_id)).accountEmail
    prefixed_transfer_p4sa_email = _get_iam_prefixed_email(
        transfer_p4sa_email, is_service_account=True)

    existing_p4sa_roles = _get_existing_transfer_roles_for_account(
        project_iam_policy, prefixed_transfer_p4sa_email, EXPECTED_P4SA_ROLES)
    log.status.Print('Google-managed transfer account {} has roles:\n{}'.format(
        transfer_p4sa_email, list(existing_p4sa_roles)))
    missing_p4sa_roles = EXPECTED_P4SA_ROLES - existing_p4sa_roles
    log.status.Print('Missing roles:\n{}'.format(list(missing_p4sa_roles)))

    all_missing_role_tuples += [
        (prefixed_transfer_p4sa_email, role) for role in missing_p4sa_roles
    ]

    if args.add_missing or all_missing_role_tuples:
      log.status.Print('***')
      if args.add_missing:
        if all_missing_role_tuples:
          log.status.Print('Adding roles:\n{}'.format(all_missing_role_tuples))
          projects_api.AddIamPolicyBindings(parsed_project_id,
                                            all_missing_role_tuples)
          log.status.Print('***')
          # Source:
          # https://cloud.google.com/iam/docs/granting-changing-revoking-access
          log.status.Print(
              'Done. Permissions typically take seconds to propagate, but,'
              ' in some cases, it can take up to seven minutes.')
        else:
          log.status.Print('No missing roles to add.')
      else:
        log.status.Print('Rerun with --add-missing to add missing roles.')
