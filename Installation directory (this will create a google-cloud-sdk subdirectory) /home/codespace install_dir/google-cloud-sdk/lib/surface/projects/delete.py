# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Command to delete a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.smart_guardrails import smart_guardrails
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.resource_manager import completers
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


class Delete(base.DeleteCommand):
  """Delete a project.

  Deletes the project with the given project ID.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The active account does not have IAM role `role/owner` or another IAM role
    with the `resourcemanager.projects.delete` permission for the given project.

  See [Access control for projects using
  IAM](https://cloud.google.com/resource-manager/docs/access-control-proj) for
  more information.

  ## EXAMPLES

  The following command deletes the project with the ID `example-foo-bar-1`:

    $ {command} example-foo-bar-1

  ## SEE ALSO

  {see_also}
  """

  detailed_help = {'see_also': flags.CREATE_DELETE_IN_CONSOLE_SEE_ALSO}

  @classmethod
  def Args(cls, parser):
    flags.GetProjectIDNumberFlag('delete').AddToParser(parser)

    if cls.ReleaseTrack() != base.ReleaseTrack.GA:
      flags.GetRecommendFlag('project deletion').AddToParser(parser)

    parser.display_info.AddCacheUpdater(completers.ProjectCompleter)

  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    if self.ReleaseTrack() != base.ReleaseTrack.GA and args.recommend:
      # Projects command group explicitly disables user project quota.
      # Call with user project quota enabled, so that
      # default project can be used as quota project.
      base.EnableUserProjectQuota()
      prompt_message = smart_guardrails.GetProjectDeletionRisk(
          base.ReleaseTrack.GA,
          project_ref.Name(),
      )
      base.DisableUserProjectQuota()
    else:
      prompt_message = 'Your project will be deleted.'
    if not console_io.PromptContinue(prompt_message):
      return None
    result = projects_api.Delete(project_ref)
    log.DeletedResource(project_ref)
    # Print this here rather than in Epilog because Epilog doesn't have access
    # to the deleted resource.
    # We can't be more specific than "limited period" because the API says
    # "at an unspecified time".
    log.status.Print(
        '\nYou can undo this operation for a limited period by running'
        ' the command below.\n    $ gcloud projects undelete {1}\n\n{0}'.format(
            flags.SHUT_DOWN_PROJECTS, args.id))
    return result
