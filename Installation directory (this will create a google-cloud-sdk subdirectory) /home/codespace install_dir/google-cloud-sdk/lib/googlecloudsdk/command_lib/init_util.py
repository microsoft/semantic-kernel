# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Contains utilities to support the `gcloud init` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.api_lib.cloudresourcemanager import projects_util
from googlecloudsdk.api_lib.resource_manager import operations
from googlecloudsdk.calliope import usage_text
from googlecloudsdk.command_lib.projects import util as  projects_command_util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import console_io
import six


_ENTER_PROJECT_ID_MESSAGE = """\
Enter a Project ID. Note that a Project ID CANNOT be changed later.
Project IDs must be 6-30 characters (lowercase ASCII, digits, or
hyphens) in length and start with a lowercase letter. \
"""
_CREATE_PROJECT_SENTINEL = object()

# At around 200 projects, being able to list them out becomes less useful.
_PROJECT_LIST_LIMIT = 200


def _GetProjectIds(limit=None):
  """Returns a list of project IDs the current user can list.

  Args:
    limit: int, the maximum number of project ids to return.

  Returns:
    list of str, project IDs, or None (if the command fails).
  """
  try:
    projects = projects_api.List(limit=limit)
    return sorted([project.projectId for project in projects])
  except Exception as err:  # pylint: disable=broad-except
    log.warning('Listing available projects failed: %s', six.text_type(err))
    return None


def _IsExistingProject(project_id):
  project_ref = projects_command_util.ParseProject(project_id)
  try:
    project = projects_api.Get(project_ref)
    return projects_util.IsActive(project)
  except Exception:  # pylint: disable=broad-except
    # Yeah, this isn't great, but there isn't a perfect exception super class
    # that covers both API related errors and network errors.
    return False


def _PromptForProjectId(project_ids, limit_exceeded):
  """Prompt the user for a project ID, based on the list of available IDs.

  Also allows an option to create a project.

  Args:
    project_ids: list of str or None, the project IDs to prompt for. If this
      value is None, the listing was unsuccessful and we prompt the user
      free-form (and do not validate the input). If it's empty, we offer to
      create a project for the user.
    limit_exceeded: bool, whether or not the project list limit was reached. If
      this limit is reached, then user will be prompted with a choice to
      manually enter a project id, create a new project, or list all projects.

  Returns:
    str, the project ID to use, or _CREATE_PROJECT_SENTINEL (if a project should
      be created), or None
  """
  if project_ids is None:
    return console_io.PromptResponse(
        'Enter project ID you would like to use:  ') or None
  elif not project_ids:
    if not console_io.PromptContinue(
        'This account has no projects.',
        prompt_string='Would you like to create one?'):
      return None
    return _CREATE_PROJECT_SENTINEL
  elif limit_exceeded:
    idx = console_io.PromptChoice(
        ['Enter a project ID', 'Create a new project', 'List projects'],
        message=('This account has a lot of projects! Listing them all can '
                 'take a while.'))
    if idx is None:
      return None
    elif idx == 0:
      return console_io.PromptWithValidator(
          _IsExistingProject,
          'Project ID does not exist or is not active.',
          'Enter project ID you would like to use:  ',
          allow_invalid=True)
    elif idx == 1:
      return _CREATE_PROJECT_SENTINEL
    else:
      project_ids = _GetProjectIds()

  idx = console_io.PromptChoice(
      project_ids + ['Enter a project ID', 'Create a new project'],
      message='Pick cloud project to use: ',
      allow_freeform=True,
      freeform_suggester=usage_text.TextChoiceSuggester())
  if idx is None:
    return None
  elif idx == len(project_ids):
    return console_io.PromptWithValidator(
        _IsExistingProject,
        'Project ID does not exist or is not active.',
        'Enter project ID you would like to use:  ',
        allow_invalid=True)
  elif idx == len(project_ids) + 1:
    return _CREATE_PROJECT_SENTINEL
  return project_ids[idx]


def _CreateProject(project_id, project_ids):
  """Create a project and check that it isn't in the known project IDs."""
  if project_ids and project_id in project_ids:
    raise ValueError('Attempting to create a project that already exists.')

  project_ref = resources.REGISTRY.Create(
      'cloudresourcemanager.projects', projectId=project_id)
  try:
    create_op = projects_api.Create(project_ref)
  except Exception as err:  # pylint: disable=broad-except
    log.warning('Project creation failed: {err}\n'
                'Please make sure to create the project [{project}] using\n'
                '    $ gcloud projects create {project}\n'
                'or change to another project using\n'
                '    $ gcloud config set project <PROJECT ID>'.format(
                    err=six.text_type(err), project=project_id))
    return None
  # wait for async Create operation to complete and check the status.
  try:
    create_op = operations.WaitForOperation(create_op)
  except operations.OperationFailedException as err:
    log.warning(
        'Project creation for project [{project}] failed:\n  {err}'.format(
            err=six.text_type(err), project=project_id))
    return None
  return project_id


def PickProject(preselected=None):
  """Allows user to select a project.

  Args:
    preselected: str, use this value if not None

  Returns:
    str, project_id or None if was not selected.
  """
  project_ids = _GetProjectIds(limit=_PROJECT_LIST_LIMIT + 1)
  limit_exceeded = False
  if project_ids is not None and len(project_ids) > _PROJECT_LIST_LIMIT:
    limit_exceeded = True

  selected = None
  if preselected:
    project_id = preselected
  else:
    project_id = _PromptForProjectId(project_ids, limit_exceeded)
    if project_id is not _CREATE_PROJECT_SENTINEL:
      selected = project_id

  if not limit_exceeded:
    if (project_ids is None or project_id in project_ids or
        project_id is None or selected):
      return project_id
  else:
    # If we fall into limit_exceeded logic and preselected was None, then
    # as long as project_id is not _CREATE_PROJECT_SENTINEL, then we know the
    # project_id is valid.
    if ((preselected and _IsExistingProject(preselected)) or
        project_id is not _CREATE_PROJECT_SENTINEL):
      return project_id

  if project_id is _CREATE_PROJECT_SENTINEL:
    project_id = console_io.PromptResponse(_ENTER_PROJECT_ID_MESSAGE)
    if not project_id:
      return None
  else:
    if project_ids:
      message = '[{0}] is not one of your projects [{1}]. '.format(
          project_id, ','.join(project_ids))
    else:
      message = 'This account has no projects.'
    if not console_io.PromptContinue(
        message=message, prompt_string='Would you like to create it?'):
      return None

  return _CreateProject(project_id, project_ids)
