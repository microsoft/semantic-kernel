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
"""Command to create a new project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.api_lib.services import enable_api

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.projects import flags as project_flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.resource_manager import flags

from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io

ID_DESCRIPTION = ('Project IDs are immutable and can be set only during '
                  'project creation. They must start with a lowercase letter '
                  'and can have lowercase ASCII letters, digits or hyphens. '
                  'Project IDs must be between 6 and 30 characters.')


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new project.

  Creates a new project with the given project ID. By default, projects are not
  created under a parent resource. To do so, use either the --organization or
  --folder flag.

  ## EXAMPLES

  The following command creates a project with ID `example-foo-bar-1`, name
  `Happy project` and label `type=happy`:

    $ {command} example-foo-bar-1 --name="Happy project" --labels=type=happy

  By default, projects are not created under a parent resource. The following
  command creates a project with ID `example-2` with parent `folders/12345`:

    $ {command} example-2 --folder=12345

  The following command creates a project with ID `example-3` with parent
  `organizations/2048`:

    $ {command} example-3 --organization=2048

  ## SEE ALSO

  {see_also}
  """

  detailed_help = {'see_also': project_flags.CREATE_DELETE_IN_CONSOLE_SEE_ALSO}

  @staticmethod
  def Args(parser):
    """Default argument specification."""

    labels_util.AddCreateLabelsFlags(parser)
    if properties.IsDefaultUniverse():
      type_ = arg_parsers.RegexpValidator(
          r'[a-z][a-z0-9-]{5,29}', ID_DESCRIPTION
      )
    else:
      type_ = arg_parsers.RegexpValidator(
          r'^(?!.*-$)(((?:[a-z][\.a-z0-9-]{5,29})\:?)?(?:[a-z][a-z0-9-]{5,29})$)',
          ID_DESCRIPTION,
      )
    parser.add_argument(
        'id',
        metavar='PROJECT_ID',
        type=type_,
        nargs='?',
        help='ID for the project you want to create.\n\n{0}'.format(
            ID_DESCRIPTION))
    parser.add_argument(
        '--name',
        help='Name for the project you want to create. '
        'If not specified, will use project id as name.')
    parser.add_argument(
        '--enable-cloud-apis',
        action='store_true',
        default=True,
        help='Enable cloudapis.googleapis.com during creation.')
    parser.add_argument(
        '--set-as-default',
        action='store_true',
        default=False,
        help='Set newly created project as [core.project] property.')
    flags.TagsFlag().AddToParser(parser)
    flags.OrganizationIdFlag('to use as a parent').AddToParser(parser)
    flags.FolderIdFlag('to use as a parent').AddToParser(parser)

  def Run(self, args):
    """Default Run method implementation."""

    flags.CheckParentFlags(args, parent_required=False)
    project_id = args.id
    if not project_id and args.name:
      candidate = command_lib_util.IdFromName(args.name)
      if candidate and console_io.PromptContinue(
          'No project id provided.',
          'Use [{}] as project id'.format(candidate),
          throw_if_unattended=True):
        project_id = candidate
    if not project_id:
      raise exceptions.RequiredArgumentException(
          'PROJECT_ID', 'an id or a name must be provided for the new project')
    project_ref = command_lib_util.ParseProject(project_id)
    labels = labels_util.ParseCreateArgs(
        args, projects_util.GetMessages().Project.LabelsValue)
    tags = flags.GetTagsFromFlags(
        args, projects_util.GetMessages().Project.TagsValue)
    try:
      create_op = projects_api.Create(
          project_ref,
          display_name=args.name,
          parent=projects_api.ParentNameToResourceId(
              flags.GetParentFromFlags(args)),
          labels=labels,
          tags=tags)
    except apitools_exceptions.HttpConflictError:
      msg = ('Project creation failed. The project ID you specified is '
             'already in use by another project. Please try an alternative '
             'ID.')
      core_exceptions.reraise(exceptions.HttpException(msg))
    log.CreatedResource(project_ref, is_async=True)
    create_op = operations.WaitForOperation(create_op)

    # Enable cloudapis.googleapis.com
    if args.enable_cloud_apis:
      log.debug('Enabling cloudapis.googleapis.com')
      enable_api.EnableService(project_ref.Name(), 'cloudapis.googleapis.com')

    if args.set_as_default:
      project_property = properties.FromString('core/project')
      properties.PersistProperty(project_property, project_id)
      log.status.Print('Updated property [core/project] to [{0}].'
                       .format(project_id))

    return operations.ExtractOperationResponse(create_op,
                                               apis.GetMessagesModule(
                                                   'cloudresourcemanager',
                                                   'v1').Project)
