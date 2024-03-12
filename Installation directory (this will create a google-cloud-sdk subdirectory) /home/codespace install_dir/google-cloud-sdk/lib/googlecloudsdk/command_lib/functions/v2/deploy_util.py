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
"""Utility functions for Functions specific to deploying Gen2 functions."""


from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.command_lib.projects import util as projects_util


def ensure_pubsub_sa_has_token_creator_role():
  """Ensures the project's Pub/Sub service account has permission to create tokens.

  If the permission is missing, prompts the user to grant it. If the console
  cannot prompt, prints a warning instead.
  """
  pubsub_sa = 'service-{}@gcp-sa-pubsub.iam.gserviceaccount.com'.format(
      projects_util.GetProjectNumber(api_util.GetProject())
  )

  api_util.PromptToBindRoleIfMissing(
      pubsub_sa,
      'roles/iam.serviceAccountTokenCreator',
      alt_roles=['roles/pubsub.serviceAgent'],
      reason=(
          'Pub/Sub needs this role to create identity tokens. '
          'For more details, please see '
          'https://cloud.google.com/pubsub/docs/push#authentication'
      ),
  )


def ensure_data_access_logs_are_enabled(trigger_event_filters):
  # type: (list[cloudfunctions_v2_messages.EventFilter]) -> None
  """Ensures appropriate Data Access Audit Logs are enabled for the given event filters.

  If they're not, the user will be prompted to enable them or warned if the
  console cannot prompt.

  Args:
    trigger_event_filters: the CAL trigger's event filters.
  """
  service_filter = [
      f for f in trigger_event_filters if f.attribute == 'serviceName'
  ]
  if service_filter:
    api_util.PromptToEnableDataAccessAuditLogs(service_filter[0].value)
