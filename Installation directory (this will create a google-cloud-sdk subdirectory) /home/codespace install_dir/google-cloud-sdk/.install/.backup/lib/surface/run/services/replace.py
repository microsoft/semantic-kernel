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
"""Command for updating env vars and other configuration info."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from googlecloudsdk.api_lib.run import global_methods
from googlecloudsdk.api_lib.run import service
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import messages as messages_util
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util as projects_util
from googlecloudsdk.command_lib.run import config_changes
from googlecloudsdk.command_lib.run import connection_context
from googlecloudsdk.command_lib.run import exceptions
from googlecloudsdk.command_lib.run import flags
from googlecloudsdk.command_lib.run import messages_util as run_messages_util
from googlecloudsdk.command_lib.run import platforms
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import resource_args
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Replace(base.Command):
  """Create or replace a service from a YAML service specification."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Creates or replaces a service from a YAML service specification.
          """,
      'EXAMPLES':
          """\
          To replace the specification for a service defined in myservice.yaml

              $ {command} myservice.yaml

         """,
  }

  @classmethod
  def CommonArgs(cls, parser):
    # Flags specific to connecting to a cluster
    cluster_group = flags.GetClusterArgGroup(parser)
    namespace_presentation = presentation_specs.ResourcePresentationSpec(
        '--namespace',
        resource_args.GetNamespaceResourceSpec(),
        'Namespace to replace service.',
        required=True,
        prefixes=False)
    concept_parsers.ConceptParser([namespace_presentation
                                  ]).AddToParser(cluster_group)

    # Flags not specific to any platform
    flags.AddAsyncFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    flags.AddDryRunFlag(parser)
    parser.add_argument(
        'FILE',
        action='store',
        type=arg_parsers.YAMLFileContents(),
        help='The absolute path to the YAML file with a Knative '
        'service definition for the service to update or deploy.')

    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  @classmethod
  def Args(cls, parser):
    cls.CommonArgs(parser)

  def _ConnectionContext(self, args, region_label):
    return connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack(), region_label=region_label
    )

  def Run(self, args):
    """Create or Update service from YAML."""
    run_messages = apis.GetMessagesModule(global_methods.SERVERLESS_API_NAME,
                                          global_methods.SERVERLESS_API_VERSION)
    service_dict = dict(args.FILE)
    # Clear the status to make migration from k8s deployments easier.
    # Since a Deployment status will have several fields that Cloud Run doesn't
    # support, trying to convert it to a message as-is will fail even though
    # status is ignored by the server.
    if 'status' in service_dict:
      del service_dict['status']

    # For cases where YAML contains the project number as metadata.namespace,
    # preemptively convert them to a string to avoid validation failures.
    namespace = service_dict.get('metadata', {}).get('namespace', None)
    if namespace is not None and not isinstance(namespace, str):
      service_dict['metadata']['namespace'] = str(namespace)

    new_service = None  # this avoids a lot of errors.
    try:
      raw_service = messages_util.DictToMessageWithErrorCheck(
          service_dict, run_messages.Service)
      new_service = service.Service(raw_service, run_messages)
    except messages_util.ScalarTypeMismatchError as e:
      exceptions.MaybeRaiseCustomFieldMismatch(
          e,
          help_text='Please make sure that the YAML file matches the Knative '
          'service definition spec in https://kubernetes.io/docs/'
          'reference/kubernetes-api/services-resources/service-v1/'
          '#Service.')

    # If managed, namespace must match project (or will default to project if
    # not specified).
    # If not managed, namespace simply must not conflict if specified in
    # multiple places (or will default to "default" if not specified).
    namespace = args.CONCEPTS.namespace.Parse().Name()  # From flag or default
    if new_service.metadata.namespace is not None:
      if (args.IsSpecified('namespace') and
          namespace != new_service.metadata.namespace):
        raise exceptions.ConfigurationError(
            'Namespace specified in file does not match passed flag.')
      namespace = new_service.metadata.namespace
      if platforms.GetPlatform() == platforms.PLATFORM_MANAGED:
        project = properties.VALUES.core.project.Get()
        project_number = projects_util.GetProjectNumber(project)
        if namespace != project and namespace != str(project_number):
          raise exceptions.ConfigurationError(
              'Namespace must be project ID [{}] or quoted number [{}] for '
              'Cloud Run (fully managed).'.format(project, project_number))
    new_service.metadata.namespace = namespace

    changes = [
        config_changes.ReplaceServiceChange(new_service),
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack())
    ]
    service_ref = resources.REGISTRY.Parse(
        new_service.metadata.name,
        params={'namespacesId': new_service.metadata.namespace},
        collection='run.namespaces.services')

    region_label = new_service.region if new_service.is_managed else None

    conn_context = self._ConnectionContext(args, region_label)
    dry_run = args.dry_run if hasattr(args, 'dry_run') else False

    action = (
        'Validating new configuration for'
        if dry_run
        else 'Applying new configuration to'
    )

    with serverless_operations.Connect(conn_context) as client:
      service_obj = client.GetService(service_ref)

      pretty_print.Info(
          run_messages_util.GetStartDeployMessage(
              conn_context, service_ref, operation=action
          )
      )

      deployment_stages = stages.ServiceStages()
      header = ('Deploying...' if service_obj else 'Deploying new service...')
      if dry_run:
        header = 'Validating...'
      with progress_tracker.StagedProgressTracker(
          header,
          deployment_stages,
          failure_message='Deployment failed',
          suppress_output=args.async_ or dry_run,
      ) as tracker:
        service_obj = client.ReleaseService(
            service_ref,
            changes,
            self.ReleaseTrack(),
            tracker,
            asyn=args.async_,
            allow_unauthenticated=None,
            for_replace=True,
            dry_run=dry_run,
        )
      if args.async_:
        pretty_print.Success(
            'New configuration for [{{bold}}{serv}{{reset}}] is being applied '
            'asynchronously.'.format(serv=service_obj.name))
      elif dry_run:
        pretty_print.Success(
            'New configuration has been validated for service '
            '[{{bold}}{serv}{{reset}}].'.format(serv=service_obj.name)
        )
      else:
        pretty_print.Success('New configuration has been applied to service '
                             '[{{bold}}{serv}{{reset}}].\n'
                             'URL: {{bold}}{url}{{reset}}'.format(
                                 serv=service_obj.name, url=service_obj.domain))
      return service_obj


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class AlphaReplace(Replace):

  @classmethod
  def Args(cls, parser):
    Replace.CommonArgs(parser)


AlphaReplace.__doc__ = Replace.__doc__
