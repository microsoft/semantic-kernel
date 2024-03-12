# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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
"""Command for modifying backend services."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import io
from apitools.base.protorpclite import messages
from apitools.base.py import encoding

from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.api_lib.compute import property_selector
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from googlecloudsdk.command_lib.compute import exceptions
from googlecloudsdk.command_lib.compute import flags as compute_flags
from googlecloudsdk.command_lib.compute.backend_services import backend_services_utils
from googlecloudsdk.command_lib.compute.backend_services import flags
from googlecloudsdk.core import resources
from googlecloudsdk.core import yaml
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import edit
import six


class InvalidResourceError(calliope_exceptions.ToolException):
  # Normally we'd want to subclass core.exceptions.Error, but base_classes.Edit
  # abuses ToolException to classify errors when displaying messages to users,
  # and we should continue to fit in that framework for now.
  pass


class Edit(base.Command):
  """Modify a backend service.

    *{command}* modifies a backend service of a Google Cloud load balancer or
    Traffic Director. The backend service resource is fetched from the server
    and presented in a text editor that displays the configurable fields.

    The specific editor is defined by the ``EDITOR'' environment variable.

    The name of each backend corresponds to the name of an instance group,
    zonal NEG, serverless NEG, or internet NEG.

    To add, remove, or swap backends, use the `gcloud compute backend-services
    remove-backend` and `gcloud compute backend-services add-backend` commands.
  """

  DEFAULT_FORMAT = 'yaml'
  _BACKEND_SERVICE_ARG = flags.GLOBAL_REGIONAL_BACKEND_SERVICE_ARG

  @classmethod
  def Args(cls, parser):
    cls._BACKEND_SERVICE_ARG.AddArgument(parser)

  def _ProcessEditedResource(self, holder, backend_service_ref, file_contents,
                             original_object, original_record,
                             modifiable_record, args):
    """Returns an updated resource that was edited by the user."""

    # It's very important that we replace the characters of comment
    # lines with spaces instead of removing the comment lines
    # entirely. JSON and YAML deserialization give error messages
    # containing line, column, and the character offset of where the
    # error occurred. If the deserialization fails; we want to make
    # sure those numbers map back to what the user actually had in
    # front of him or her otherwise the errors will not be very
    # useful.
    non_comment_lines = '\n'.join(
        ' ' * len(line) if line.startswith('#') else line
        for line in file_contents.splitlines())

    modified_record = base_classes.DeserializeValue(
        non_comment_lines, args.format or Edit.DEFAULT_FORMAT)

    # Normalizes all of the fields that refer to other
    # resource. (i.e., translates short names to URIs)
    reference_normalizer = property_selector.PropertySelector(
        transformations=self.GetReferenceNormalizers(holder.resources))
    modified_record = reference_normalizer.Apply(modified_record)

    if modifiable_record == modified_record:
      new_object = None

    else:
      modified_record['name'] = original_record['name']
      fingerprint = original_record.get('fingerprint')
      if fingerprint:
        modified_record['fingerprint'] = fingerprint

      new_object = encoding.DictToMessage(modified_record,
                                          holder.client.messages.BackendService)

    # If existing object is equal to the proposed object or if
    # there is no new object, then there is no work to be done, so we
    # return the original object.
    if not new_object or original_object == new_object:
      return [original_object]

    return holder.client.MakeRequests(
        [self.GetSetRequest(holder.client, backend_service_ref, new_object)])

  def Run(self, args):
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())
    client = holder.client

    backend_service_ref = self._BACKEND_SERVICE_ARG.ResolveAsResource(
        args,
        holder.resources,
        default_scope=backend_services_utils.GetDefaultScope(),
        scope_lister=compute_flags.GetDefaultScopeLister(client))
    get_request = self.GetGetRequest(client, backend_service_ref)

    objects = client.MakeRequests([get_request])

    original_object = objects[0]
    original_record = encoding.MessageToDict(original_object)

    # Selects only the fields that can be modified.
    field_selector = property_selector.PropertySelector(properties=[
        'backends',
        'customRequestHeaders',
        'customResponseHeaders',
        'description',
        'enableCDN',
        'healthChecks',
        'iap.enabled',
        'iap.oauth2ClientId',
        'iap.oauth2ClientSecret',
        'port',
        'portName',
        'protocol',
        'timeoutSec',
    ])
    modifiable_record = field_selector.Apply(original_record)

    file_contents = self.BuildFileContents(args, client, original_record,
                                           modifiable_record)
    resource_list = self.EditResource(args, backend_service_ref, file_contents,
                                      holder, modifiable_record,
                                      original_object, original_record)

    for resource in resource_list:
      yield resource

  def BuildFileContents(self, args, client, original_record, modifiable_record):
    buf = io.StringIO()
    for line in base_classes.HELP.splitlines():
      buf.write('#')
      if line:
        buf.write(' ')
      buf.write(line)
      buf.write('\n')
    buf.write('\n')
    buf.write(base_classes.SerializeDict(modifiable_record,
                                         args.format or Edit.DEFAULT_FORMAT))
    buf.write('\n')
    example = base_classes.SerializeDict(
        encoding.MessageToDict(self.GetExampleResource(client)),
        args.format or Edit.DEFAULT_FORMAT)
    base_classes.WriteResourceInCommentBlock(example, 'Example resource:', buf)
    buf.write('#\n')
    original = base_classes.SerializeDict(original_record,
                                          args.format or Edit.DEFAULT_FORMAT)
    base_classes.WriteResourceInCommentBlock(original, 'Original resource:',
                                             buf)
    return buf.getvalue()

  def EditResource(self, args, backend_service_ref, file_contents, holder,
                   modifiable_record, original_object, original_record):
    while True:
      try:
        file_contents = edit.OnlineEdit(file_contents)
      except edit.NoSaveException:
        raise exceptions.AbortedError('Edit aborted by user.')
      try:
        resource_list = self._ProcessEditedResource(holder, backend_service_ref,
                                                    file_contents,
                                                    original_object,
                                                    original_record,
                                                    modifiable_record, args)
        break
      except (ValueError, yaml.YAMLParseError,
              messages.ValidationError,
              calliope_exceptions.ToolException) as e:
        message = getattr(e, 'message', six.text_type(e))

        if isinstance(e, calliope_exceptions.ToolException):
          problem_type = 'applying'
        else:
          problem_type = 'parsing'

        message = ('There was a problem {0} your changes: {1}'
                   .format(problem_type, message))
        if not console_io.PromptContinue(
            message=message,
            prompt_string='Would you like to edit the resource again?'):
          raise exceptions.AbortedError('Edit aborted by user.')
    return resource_list

  def GetExampleResource(self, client):
    uri_prefix = ('https://compute.googleapis.com/compute/v1/projects/'
                  'my-project/')
    instance_groups_uri_prefix = (
        'https://compute.googleapis.com/compute/v1/projects/'
        'my-project/zones/')

    return client.messages.BackendService(
        backends=[
            client.messages.Backend(
                balancingMode=(
                    client.messages.Backend.BalancingModeValueValuesEnum.RATE),
                group=(instance_groups_uri_prefix +
                       'us-central1-a/instanceGroups/group-1'),
                maxRate=100),
            client.messages.Backend(
                balancingMode=(
                    client.messages.Backend.BalancingModeValueValuesEnum.RATE),
                group=(instance_groups_uri_prefix +
                       'europe-west1-a/instanceGroups/group-2'),
                maxRate=150),
        ],
        customRequestHeaders=['X-Forwarded-Port:443'],
        customResponseHeaders=['X-Client-Geo-Location:US,Mountain View'],
        description='My backend service',
        healthChecks=[
            uri_prefix + 'global/httpHealthChecks/my-health-check-1',
            uri_prefix + 'global/httpHealthChecks/my-health-check-2'
        ],
        name='backend-service',
        port=80,
        portName='http',
        protocol=client.messages.BackendService.ProtocolValueValuesEnum.HTTP,
        selfLink=uri_prefix + 'global/backendServices/backend-service',
        timeoutSec=30,
    )

  def GetReferenceNormalizers(self, resource_registry):

    def MakeReferenceNormalizer(field_name, allowed_collections):
      """Returns a function to normalize resource references."""
      def NormalizeReference(reference):
        """Returns normalized URI for field_name."""
        try:
          value_ref = resource_registry.Parse(reference)
        except resources.UnknownCollectionException:
          raise InvalidResourceError(
              '[{field_name}] must be referenced using URIs.'.format(
                  field_name=field_name))

        if value_ref.Collection() not in allowed_collections:
          raise InvalidResourceError(
              'Invalid [{field_name}] reference: [{value}].'. format(
                  field_name=field_name, value=reference))
        return value_ref.SelfLink()
      return NormalizeReference

    # Ensure group is a uri or full collection path representing an instance
    # group. Full uris/paths are required because if the user gives us less, we
    # don't want to be in the business of guessing health checks.
    return [
        ('healthChecks[]',
         MakeReferenceNormalizer(
             'healthChecks',
             ('compute.httpHealthChecks', 'compute.httpsHealthChecks',
              'compute.healthChecks', 'compute.regionHealthChecks'))),
        ('backends[].group',
         MakeReferenceNormalizer(
             'group',
             ('compute.instanceGroups', 'compute.regionInstanceGroups'))),
    ]

  def GetGetRequest(self, client, backend_service_ref):
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return (client.apitools_client.regionBackendServices, 'Get',
              client.messages.ComputeRegionBackendServicesGetRequest(
                  **backend_service_ref.AsDict()))
    return (client.apitools_client.backendServices, 'Get',
            client.messages.ComputeBackendServicesGetRequest(
                **backend_service_ref.AsDict()))

  def GetSetRequest(self, client, backend_service_ref, replacement):
    if backend_service_ref.Collection() == 'compute.regionBackendServices':
      return (client.apitools_client.regionBackendServices, 'Update',
              client.messages.ComputeRegionBackendServicesUpdateRequest(
                  backendServiceResource=replacement,
                  **backend_service_ref.AsDict()))
    return (client.apitools_client.backendServices, 'Update',
            client.messages.ComputeBackendServicesUpdateRequest(
                backendServiceResource=replacement,
                **backend_service_ref.AsDict()))
