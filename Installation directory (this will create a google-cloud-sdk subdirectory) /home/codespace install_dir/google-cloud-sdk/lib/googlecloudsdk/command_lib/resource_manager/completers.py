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

"""Cloud resource manager completers."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.iam import completers as iam_completers
from googlecloudsdk.command_lib.util import completers


class ProjectCompleter(completers.ResourceParamCompleter):
  """The project completer."""

  def __init__(self, **kwargs):
    super(ProjectCompleter, self).__init__(
        collection='cloudresourcemanager.projects',
        list_command='projects list --uri',
        param='projectId',
        **kwargs)


class OrganizationCompleter(completers.ResourceParamCompleter):
  """The organization completer."""

  def __init__(self, **kwargs):
    super(OrganizationCompleter, self).__init__(
        collection='cloudresourcemanager.organizations',
        list_command='organizations list --uri',
        param='organizationsId',
        **kwargs)


class ProjectsIamRolesCompleter(iam_completers.IamRolesCompleter):
  """IAM Roles Completer."""

  def __init__(self, **kwargs):
    super(ProjectsIamRolesCompleter, self).__init__(
        resource_collection='cloudresourcemanager.projects',
        resource_dest='project_id',
        **kwargs
    )
