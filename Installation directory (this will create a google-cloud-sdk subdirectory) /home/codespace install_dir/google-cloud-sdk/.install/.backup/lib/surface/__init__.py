# -*- coding: utf-8 -*- #
# Copyright 2013 Google LLC. All Rights Reserved.
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

"""The super-group for the Cloud CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import common_args
from googlecloudsdk.core import properties


class Gcloud(base.Group):
  """Manage Google Cloud resources and developer workflow.

  The `gcloud` CLI manages authentication, local configuration, developer
  workflow, and interactions with the Google Cloud APIs.

  For a quick introduction to the `gcloud` CLI, a list of commonly
  used commands, and a look at how these commands are structured, run
  `gcloud cheat-sheet` or see the
  [`gcloud` CLI cheat sheet](https://cloud.google.com/sdk/docs/cheatsheet).
  """

  @staticmethod
  def Args(parser):
    parser.add_argument(
        '--account',
        metavar='ACCOUNT',
        category=base.COMMONLY_USED_FLAGS,
        help='Google Cloud user account to use for invocation.',
        action=actions.StoreProperty(properties.VALUES.core.account))

    # Ideally this would be on the alpha group (since it's alpha) but there are
    # a bunch of problems with doing that. Global flags are treated differently
    # than other flags and flags on the Alpha group are not treated as global.
    # The result is that the flag shows up on every man page as if it was part
    # of the individual command (which is undesirable and breaks every surface
    # spec).
    parser.add_argument(
        '--impersonate-service-account',
        metavar='SERVICE_ACCOUNT_EMAILS',
        help="""\
        For this `gcloud` invocation, all API requests will be
        made as the given service account or target service account in an
        impersonation delegation chain instead of the currently selected
        account. You can specify either a single service account as the
        impersonator, or a comma-separated list of service accounts to
        create an impersonation delegation chain. The impersonation is done
        without needing to create, download, and activate a key for the
        service account or accounts.

        In order to make API requests as a service account, your
        currently selected account must have an IAM role that includes
        the `iam.serviceAccounts.getAccessToken` permission for the
        service account or accounts.

        The `roles/iam.serviceAccountTokenCreator` role has
        the `iam.serviceAccounts.getAccessToken permission`. You can
        also create a custom role.

        You can specify a list of service accounts, separated with
        commas. This creates an impersonation delegation chain in which
        each service account delegates its permissions to the next
        service account in the chain. Each service account in the list
        must have the `roles/iam.serviceAccountTokenCreator` role on the
        next service account in the list. For example, when
        `--impersonate-service-account=`
        ``SERVICE_ACCOUNT_1'',``SERVICE_ACCOUNT_2'',
        the active account must have the
        `roles/iam.serviceAccountTokenCreator` role on
        ``SERVICE_ACCOUNT_1'', which must have the
        `roles/iam.serviceAccountTokenCreator` role on
        ``SERVICE_ACCOUNT_2''.
        ``SERVICE_ACCOUNT_1'' is the impersonated service
        account and ``SERVICE_ACCOUNT_2'' is the delegate.
        """,
        action=actions.StoreProperty(
            properties.VALUES.auth.impersonate_service_account))
    parser.add_argument(
        '--access-token-file',
        metavar='ACCESS_TOKEN_FILE',
        help="""\
        A file path to read the access token. Use this flag to
        authenticate `gcloud` with an access token. The credentials of
        the active account (if exists) will be ignored. The file should
        only contain an access token with no other information.
        """,
        action=actions.StoreProperty(properties.VALUES.auth.access_token_file))
    common_args.ProjectArgument().AddToParser(parser)
    parser.add_argument(
        '--billing-project',
        metavar='BILLING_PROJECT',
        category=base.COMMONLY_USED_FLAGS,
        help="""\
             The Google Cloud project that will be charged quota for
             operations performed in `gcloud`. If you need to operate on one
             project, but need quota against a different project, you can use
             this flag to specify the billing project. If both
             `billing/quota_project` and `--billing-project` are specified,
             `--billing-project` takes precedence.
             Run `$ gcloud config set --help` to see more information about
             `billing/quota_project`.
             """,
        action=actions.StoreProperty(
            properties.VALUES.billing.quota_project))
    # Must have a None default so properties are not always overridden when the
    # arg is not provided.
    parser.add_argument(
        '--quiet',
        '-q',
        default=None,
        category=base.COMMONLY_USED_FLAGS,
        action=actions.StoreConstProperty(
            properties.VALUES.core.disable_prompts, True),
        help="""\
        Disable all interactive prompts when running `gcloud` commands. If input
        is required, defaults will be used, or an error will be raised.

        Overrides the default core/disable_prompts property value for this
        command invocation. This is equivalent to setting the environment
        variable `CLOUDSDK_CORE_DISABLE_PROMPTS` to 1.
        """)

    trace_group = parser.add_mutually_exclusive_group()
    trace_group.add_argument(
        '--trace-token',
        default=None,
        action=actions.StoreProperty(properties.VALUES.core.trace_token),
        help='Token used to route traces of service requests for investigation'
        ' of issues.')
    trace_group.add_argument(
        '--trace-email',
        metavar='USERNAME',
        default=None,
        action=actions.StoreProperty(properties.VALUES.core.trace_email),
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')
    trace_group.add_argument(
        '--trace-log',
        default=None,
        action=actions.StoreBooleanProperty(properties.VALUES.core.trace_log),
        hidden=True,
        help='THIS ARGUMENT NEEDS HELP TEXT.')
