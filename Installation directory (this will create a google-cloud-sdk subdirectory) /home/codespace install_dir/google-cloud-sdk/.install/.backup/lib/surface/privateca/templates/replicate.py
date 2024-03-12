# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Replicate a certificate template to multiple regions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import exceptions as api_exceptions
from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.api_lib.privateca import locations
from googlecloudsdk.api_lib.privateca import request_utils
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.privateca import operations
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.core import log
import six


class ReplicationError(Exception):
  """Represents an error that occurred while replicating a resource to a given location."""

  def __init__(self, location, message):
    self._message = 'Failed to replicate to location [{}]: {}'.format(
        location, message)
    super(ReplicationError, self).__init__(self._message)

  def __str__(self):
    return self._message


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Replicate(base.SilentCommand):
  """Replicate a certificate template to multiple locations."""

  detailed_help = {
      'DESCRIPTION':
          'Replicate a certificate template to multiple locations.',
      'EXAMPLES':
          """\
      To replicate a certificate templates to all supported locations, run:

        $ {command} my-template --location=us-west1 --all-locations

      To replicate a certificate template to 'us-west2' and 'us-east1', run:

        $ {command} my-template --location=us-west1 --target-locations=us-west2,us-east1

      To overwrite existing templates with the same resource ID in the target
      locations, use the --overwrite flag:

        $ {command} my-template --location=us-west1 --target-locations=us-west2,us-east1 --overwrite

      To continue replicating templates in other locations in the event of a
      failure in one or more locations, use the --continue-on-error flag:

        $ {command} my-template --location=us-west1 --all-locations --continue-on-error""",
  }

  @staticmethod
  def Args(parser):
    resource_args.AddCertificateTemplatePositionalResourceArg(
        parser, 'to replicate')

    target_locations_group = base.ArgumentGroup(
        mutex=True,
        required=True,
        help='Specify where the certificate template should be replicated.'
    ).AddToParser(parser)

    base.Argument(
        '--all-locations',
        action='store_const',
        const=True,
        help='Replicate this template to all supported locations.').AddToParser(
            target_locations_group)
    base.Argument(
        '--target-locations',
        help='Replicate this template to the given locations.',
        type=arg_parsers.ArgList(
            element_type=lambda x: six.text_type(x).strip()),
        metavar='LOCATION').AddToParser(target_locations_group)

    base.Argument(
        '--overwrite',
        help=('Overwrite any existing templates with the same name, '
              'if they exist.'),
        action='store_const',
        const=True,
        default=False).AddToParser(parser)
    base.Argument(
        '--continue-on-error',
        help=('Continue replicating the template to other locations '
              'even if an error is encountered. If this is set, an '
              'error in one location will be logged but will not '
              'prevent replication to other locations.'),
        action='store_const',
        const=True,
        default=False).AddToParser(parser)

  def _CreateOrUpdateTemplate(self, project, location, template_id, template,
                              overwrite):
    """Returns an LRO for a Create or Update operation for the given template.

    Args:
      project: str, the project ID or number for the new template.
      location: str, the location for the new template.
      template_id: str, the resource ID for the new template.
      template: object, the body of the new template.
      overwrite: bool, whether to overwrite existing templates with the same ID.

    Raises:
      ReplicationError, if the template could not be replicated to this
      location.
    """
    parent = 'projects/{}/locations/{}'.format(project, location)
    resource_name = '{}/certificateTemplates/{}'.format(parent, template_id)
    try:
      return self.client.projects_locations_certificateTemplates.Create(
          self.messages
          .PrivatecaProjectsLocationsCertificateTemplatesCreateRequest(
              parent=parent,
              certificateTemplateId=template_id,
              certificateTemplate=template,
              requestId=request_utils.GenerateRequestId()))
    except api_exceptions.HttpConflictError as e:
      if not overwrite:
        raise ReplicationError(
            location,
            'Certificate template [{}] already exists and the --overwrite flag '
            'was not set.'.format(resource_name))

      return self.client.projects_locations_certificateTemplates.Patch(
          self.messages
          .PrivatecaProjectsLocationsCertificateTemplatesPatchRequest(
              name=resource_name,
              certificateTemplate=template,
              # Always copy all fields. Mask value of '*' doesn't seem to be
              # currently supported by CCFE.
              updateMask='predefined_values,identity_constraints,passthrough_extensions,description,labels',
              requestId=request_utils.GenerateRequestId()))
    except api_exceptions.HttpError as e:
      raise ReplicationError(location, six.text_type(e))

  def Run(self, args):
    """Runs the command."""
    self.client = privateca_base.GetClientInstance(api_version='v1')
    self.messages = privateca_base.GetMessagesModule(api_version='v1')

    template_ref = args.CONCEPTS.certificate_template.Parse()
    template = self.client.projects_locations_certificateTemplates.Get(
        self.messages.PrivatecaProjectsLocationsCertificateTemplatesGetRequest(
            name=template_ref.RelativeName()))

    # Name is output-only and will be different for each location.
    template.name = ''

    success_count = 0
    target_locations = args.target_locations
    if args.all_locations:
      target_locations = [
          location for location in locations.GetSupportedLocations('v1')
          if location != template_ref.locationsId
      ]
    for location in target_locations:
      location = location.strip()
      if location == template_ref.locationsId:
        log.warning(
            'Skipping location [{}] since it is the source location.'.format(
                location))
        continue

      try:
        operation = self._CreateOrUpdateTemplate(template_ref.projectsId,
                                                 location, template_ref.Name(),
                                                 template, args.overwrite)
        operations.Await(
            operation,
            'Replicating template to [{}]'.format(location),
            api_version='v1')
        success_count += 1
      except ReplicationError as e:
        if args.continue_on_error:
          log.warning(six.text_type(e))
          continue
        raise e

    log.status.Print(
        'Replicated template [{}] to {} out of {} locations.'.format(
            template_ref.RelativeName(), success_count, len(target_locations)))
