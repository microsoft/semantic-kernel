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

"""Command to update a new project."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudresourcemanager import projects_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class UpdateAlpha(base.UpdateCommand):
  """Update the name and/or labels of a project.

  Update the name and/or labels of the given project.

  This command can fail for the following reasons:
  * There is no project with the given ID.
  * The active account does not have Owner or Editor permissions for the
    given project.

  ## EXAMPLES

  The following command updates a project with the ID
  `example-foo-bar-1` to have the name "Foo Bar & Grill" and removes the
  label `dive`:

    $ {command} example-foo-bar-1 --name="Foo Bar & Grill" --remove-labels=dive

  The following command updates a project with the ID `example-foo-bar-1` to
  have labels `foo` and `bar` with values of `abc` and `def`, respectively:

    $ {command} example-foo-bar-1 --update-labels="foo=abc,bar=def"
  """

  @staticmethod
  def Args(parser):
    flags.GetProjectIDNumberFlag('update').AddToParser(parser)
    update_flags = parser.add_group(required=True)
    update_flags.add_argument('--name', help='New name for the project.')

    labels_group = update_flags.add_group('Labels Flags')
    labels_util.AddUpdateLabelsFlags(labels_group)
    parser.display_info.AddFormat(command_lib_util.LIST_FORMAT)

  def Run(self, args):
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    project_ref = command_lib_util.ParseProject(args.id)
    result = projects_api.Update(project_ref, name=args.name,
                                 labels_diff=labels_diff)
    log.UpdatedResource(project_ref)
    return result


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update the name of a project.

  Update the name of the given project.

  This command can fail for the following reasons:
  * There is no project with the given ID.
  * The active account does not have Owner or Editor permissions for the
    given project.

  ## EXAMPLES

  The following command updates a project with the ID
  `example-foo-bar-1` to have the name "Foo Bar & Grill":

    $ {command} example-foo-bar-1 --name="Foo Bar & Grill"
  """

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    flags.GetProjectFlag('update').AddToParser(parser)
    parser.add_argument('--name', required=True,
                        help='New name for the project.')

  def Run(self, args):
    project_ref = command_lib_util.ParseProject(args.id)
    result = projects_api.Update(project_ref, name=args.name,
                                 labels_diff=labels_util.Diff())
    log.UpdatedResource(project_ref)
    return result
