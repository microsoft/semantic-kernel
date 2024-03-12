# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""'notebooks environments create' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.notebooks import util
from googlecloudsdk.core import log
from googlecloudsdk.core import resources


def CreateEnvironment(args, messages):
  """Creates the Environment message for the create request.

  Args:
    args: Argparse object from Command.Run
    messages: Module containing messages definition for the specified API.

  Returns:
    Instance of the Environment message.
  """

  def CreateContainerImageFromArgs(args):
    container_image = messages.ContainerImage(
        repository=args.container_repository, tag=args.container_tag)
    return container_image

  def CreateVmImageFromArgs(args):
    vm_image = messages.VmImage(
        project=args.vm_image_project)
    if args.IsSpecified('vm_image_family'):
      vm_image.imageFamily = args.vm_image_family
    else:
      vm_image.imageName = args.vm_image_name
    return vm_image

  if args.IsSpecified('vm_image_project'):
    vm_image = CreateVmImageFromArgs(args)
  else:
    container_image = CreateContainerImageFromArgs(args)

  environment = messages.Environment(
      name=args.environment,
      description=args.description,
      displayName=args.display_name,
      postStartupScript=args.post_startup_script)
  if args.IsSpecified('vm_image_project'):
    environment.vmImage = vm_image
  else:
    environment.containerImage = container_image
  return environment


def CreateEnvironmentCreateRequest(args, messages):
  parent = util.GetParentForEnvironment(args)
  environment = CreateEnvironment(args, messages)
  return messages.NotebooksProjectsLocationsEnvironmentsCreateRequest(
      parent=parent, environment=environment, environmentId=args.environment)


def CreateEnvironmentListRequest(args, messages):
  parent = util.GetParentFromArgs(args)
  return messages.NotebooksProjectsLocationsEnvironmentsListRequest(
      parent=parent)


def CreateEnvironmentDeleteRequest(args, messages):
  environment = GetEnvironmentResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsEnvironmentsDeleteRequest(
      name=environment)


def CreateEnvironmentDescribeRequest(args, messages):
  environment = GetEnvironmentResource(args).RelativeName()
  return messages.NotebooksProjectsLocationsEnvironmentsGetRequest(
      name=environment)


def GetEnvironmentResource(args):
  return args.CONCEPTS.environment.Parse()


def GetEnvironmentURI(resource):
  environment = resources.REGISTRY.ParseRelativeName(
      resource.name, collection='notebooks.projects.locations.environments')
  return environment.SelfLink()


def HandleLRO(operation,
              args,
              environment_service,
              release_track,
              is_delete=False):
  """Handles Long Running Operations for both cases of async."""
  logging_method = log.DeletedResource if is_delete else log.CreatedResource
  if args.async_:
    logging_method(
        util.GetOperationResource(operation.name, release_track),
        kind='notebooks environment {0}'.format(args.environment),
        is_async=True)
    return operation
  else:
    response = util.WaitForOperation(
        operation,
        'Waiting for Environment [{}] to be {} with [{}]'.format(
            args.environment, 'deleted' if is_delete else 'created',
            operation.name),
        service=environment_service,
        release_track=release_track,
        is_delete=is_delete)
    logging_method(
        util.GetOperationResource(operation.name, release_track),
        kind='notebooks environment {0}'.format(args.environment),
        is_async=False)
    return response
