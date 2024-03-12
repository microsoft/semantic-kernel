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
"""Export Cloud Build trigger to file command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.builds import flags as build_flags
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


class Import(base.Command):
  """Import a build trigger."""

  detailed_help = {
      'DESCRIPTION':
          """\
        To import a trigger from a file:
        $ cat > trigger.yaml <<EOF
        name: my-trigger
        github:
          owner: GoogleCloudPlatform
          name: cloud-builders
          push:
            branch: .*
        EOF
          """,
      'EXAMPLES': ("""
        To import a build trigger from a file called trigger.yaml, run:

          $ {command} --source=trigger.yaml
      """),
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """

    build_flags.AddRegionFlag(parser)
    parser.add_argument(
        '--source',
        metavar='PATH',
        required=True,
        help="""\
File path where trigger should be imported from.
        """)

  def _UpdateTrigger(self, client, messages, project_id, location_id, trigger):
    trigger_id = trigger.id
    if not trigger_id:
      trigger_id = trigger.name
    name = resources.REGISTRY.Parse(
        trigger.id,
        params={
            'projectsId': project_id,
            'locationsId': location_id,
            'triggersId': trigger_id,
        },
        collection='cloudbuild.projects.locations.triggers').RelativeName()
    trigger.resourceName = name

    return client.projects_locations_triggers.Patch(
        messages.CloudbuildProjectsLocationsTriggersPatchRequest(
            resourceName=name, triggerId=trigger_id, buildTrigger=trigger))

  def _CreateTrigger(self, client, messages, project, location, trigger):
    parent = resources.REGISTRY.Create(
        collection='cloudbuild.projects.locations',
        projectsId=project,
        locationsId=location).RelativeName()

    return client.projects_locations_triggers.Create(
        messages.CloudbuildProjectsLocationsTriggersCreateRequest(
            parent=parent, buildTrigger=trigger))

  def _CreateOrUpdateTrigger(self, client, messages, project, location,
                             trigger):
    if trigger.id:
      # Trigger already has an ID - only try update.
      return self._UpdateTrigger(client, messages, project, location, trigger)
    elif trigger.name:
      # No ID specified, but trigger with given name could still exist.
      # Try to update an existing trigger; if it doesn't exist, then
      # create it.
      try:
        return self._UpdateTrigger(client, messages, project, location, trigger)
      except apitools_exceptions.HttpNotFoundError:
        return self._CreateTrigger(client, messages, project, location, trigger)
    else:
      # No identifying information specified. Create a trigger with the given
      # specification.
      return self._CreateTrigger(client, messages, project, location, trigger)

  def Run(self, args):
    """Imports a build trigger.

    Args:
      args: an argparse namespace. All the arguments that were provided to this
        command invocation.

    Returns:
      Some value that we want to have printed later.
    """
    client = cloudbuild_util.GetClientInstance()
    messages = cloudbuild_util.GetMessagesModule()

    project = properties.VALUES.core.project.Get(required=True)
    regionprop = properties.VALUES.builds.region.Get()
    location = args.region or regionprop or cloudbuild_util.DEFAULT_REGION
    triggers = cloudbuild_util.LoadMessagesFromPath(
        args.source,
        messages.BuildTrigger,
        'BuildTrigger',
        skip_camel_case=['substitutions'])

    return [
        self._CreateOrUpdateTrigger(client, messages, project, location,
                                    trigger) for trigger in triggers
    ]
