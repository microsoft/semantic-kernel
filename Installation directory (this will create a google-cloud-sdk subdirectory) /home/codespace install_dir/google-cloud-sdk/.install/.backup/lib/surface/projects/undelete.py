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

"""Command to undelete a project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core import log


class Undelete(base.CreateCommand):
  """Undelete a project.

  Undeletes the project with the given project ID.

  This command can fail for the following reasons:
  * There is no project with the given ID.
  * The active account does not have Owner or Editor permissions for the
    given project.

  ## EXAMPLES

  The following command undeletes the project with the ID `example-foo-bar-1`:

    $ {command} example-foo-bar-1

  ## SEE ALSO

  {see_also}
  """

  detailed_help = {'see_also': flags.CREATE_DELETE_IN_CONSOLE_SEE_ALSO}

  @staticmethod
  def Args(parser):
    flags.GetProjectIDNumberFlag('undelete').AddToParser(parser)

  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    result = projects_api.Undelete(project_ref)
    log.RestoredResource(project_ref, kind='project')
    return result
