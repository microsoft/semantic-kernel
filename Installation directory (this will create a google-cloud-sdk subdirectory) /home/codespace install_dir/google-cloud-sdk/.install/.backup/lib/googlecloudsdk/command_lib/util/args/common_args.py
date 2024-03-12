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
"""utilities to define common arguments."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.resource_manager import completers as resource_manager_completers
from googlecloudsdk.core import properties


def ProjectArgument(help_text_to_prepend=None, help_text_to_overwrite=None):
  """Creates project argument.

  Args:
    help_text_to_prepend: str, help text to prepend to the generic --project
      help text.
    help_text_to_overwrite: str, help text to overwrite the generic --project
      help text.

  Returns:
    calliope.base.Argument, The argument for project.
  """
  if help_text_to_overwrite:
    help_text = help_text_to_overwrite
  else:
    help_text = """\
The Google Cloud project ID to use for this invocation. If
omitted, then the current project is assumed; the current project can
be listed using `gcloud config list --format='text(core.project)'`
and can be set using `gcloud config set project PROJECTID`.

`--project` and its fallback `{core_project}` property play two roles
in the invocation. It specifies the project of the resource to
operate on. It also specifies the project for API enablement check,
quota, and billing. To specify a different project for quota and
billing, use `--billing-project` or `{billing_project}` property.
    """.format(
        core_project=properties.VALUES.core.project,
        billing_project=properties.VALUES.billing.quota_project)
    if help_text_to_prepend:
      help_text = '\n\n'.join((help_text_to_prepend, help_text))

  return base.Argument(
      '--project',
      metavar='PROJECT_ID',
      dest='project',
      category=base.COMMONLY_USED_FLAGS,
      suggestion_aliases=['--application'],
      completer=resource_manager_completers.ProjectCompleter,
      action=actions.StoreProperty(properties.VALUES.core.project),
      help=help_text)
