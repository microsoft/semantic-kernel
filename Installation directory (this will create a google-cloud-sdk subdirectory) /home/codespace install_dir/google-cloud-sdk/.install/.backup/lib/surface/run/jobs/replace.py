# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
from googlecloudsdk.api_lib.run import job
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
from googlecloudsdk.command_lib.run import pretty_print
from googlecloudsdk.command_lib.run import serverless_operations
from googlecloudsdk.command_lib.run import stages
from googlecloudsdk.core import config
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
from googlecloudsdk.core.console import progress_tracker


class Replace(base.Command):
  """Create or replace a job from a YAML job specification."""

  detailed_help = {
      'DESCRIPTION':
          """\
          Creates or replaces a job from a YAML job specification.
          """,
      'EXAMPLES':
          """\
          To replace the specification for a job defined in myjob.yaml

              $ {command} myjob.yaml

         """,
  }

  @staticmethod
  def Args(parser):
    flags.AddAsyncFlag(parser)
    flags.AddClientNameAndVersionFlags(parser)
    parser.add_argument(
        'FILE',
        action='store',
        type=arg_parsers.YAMLFileContents(),
        help='The absolute path to the YAML file with a Cloud Run '
        'job definition for the job to update or create.')
    # No output by default, can be overridden by --format
    parser.display_info.AddFormat('none')

  def Run(self, args):
    """Create or Update job from YAML."""
    run_messages = apis.GetMessagesModule(global_methods.SERVERLESS_API_NAME,
                                          global_methods.SERVERLESS_API_VERSION)
    job_dict = dict(args.FILE)
    # Clear the status field since it is ignored by Cloud Run APIs and can cause
    # issues trying to convert to a message.
    if 'status' in job_dict:
      del job_dict['status']
    if ('spec' not in job_dict or 'template' not in job_dict['spec']):
      raise exceptions.ConfigurationError(
          'spec.template is required but missing. '
          'Please check the content in your yaml file.')
    # If spec.template.metadata is not set, add an empty one so that client
    # annotations can be added.
    if 'metadata' not in job_dict['spec']['template']:
      job_dict['spec']['template']['metadata'] = {}

    # For cases where YAML contains the project number as metadata.namespace,
    # preemptively convert them to a string to avoid validation failures.
    namespace = job_dict.get('metadata', {}).get('namespace', None)
    if namespace is not None and not isinstance(namespace, str):
      job_dict['metadata']['namespace'] = str(namespace)

    try:
      raw_job = messages_util.DictToMessageWithErrorCheck(
          job_dict, run_messages.Job)
      new_job = job.Job(raw_job, run_messages)
    except messages_util.ScalarTypeMismatchError as e:
      exceptions.MaybeRaiseCustomFieldMismatch(
          e,
          help_text='Please make sure that the YAML file matches the Cloud Run '
          'job definition spec in https://cloud.google.com/run/docs/reference'
          '/rest/v1/namespaces.jobs#Job')

    # Namespace must match project (or will default to project if
    # not specified).
    namespace = properties.VALUES.core.project.Get()
    if new_job.metadata.namespace is not None:
      project = namespace
      project_number = projects_util.GetProjectNumber(namespace)
      namespace = new_job.metadata.namespace
      if namespace != project and namespace != str(project_number):
        raise exceptions.ConfigurationError(
            'Namespace must be project ID [{}] or quoted number [{}] for '
            'Cloud Run (fully managed).'.format(project, project_number))
    new_job.metadata.namespace = namespace

    is_either_specified = (
        args.IsSpecified('client_name') or args.IsSpecified('client_version'))
    changes = [
        config_changes.ReplaceJobChange(new_job),
        config_changes.SetLaunchStageAnnotationChange(self.ReleaseTrack()),
        config_changes.SetClientNameAndVersionAnnotationChange(
            args.client_name if is_either_specified else 'gcloud',
            args.client_version
            if is_either_specified else config.CLOUD_SDK_VERSION,
            set_on_template=True)
    ]

    job_ref = resources.REGISTRY.Parse(
        new_job.metadata.name,
        params={'namespacesId': new_job.metadata.namespace},
        collection='run.namespaces.jobs')

    region_label = new_job.region if new_job.is_managed else None
    conn_context = connection_context.GetConnectionContext(
        args, flags.Product.RUN, self.ReleaseTrack(), region_label=region_label)

    with serverless_operations.Connect(conn_context) as client:
      job_obj = client.GetJob(job_ref)

      is_create = not job_obj
      operation = ('Creating' if is_create else 'Updating')
      pretty_print.Info(
          run_messages_util.GetStartDeployMessage(conn_context, job_ref,
                                                  operation, 'job'))

      header = operation + ' job...'
      with progress_tracker.StagedProgressTracker(
          header,
          stages.JobStages(),
          failure_message=('Job failed to deploy'),
          suppress_output=args.async_) as tracker:
        if job_obj:
          job_obj = client.UpdateJob(
              job_ref, changes, tracker, asyn=args.async_)
        else:
          job_obj = client.CreateJob(
              job_ref, changes, tracker, asyn=args.async_)

      operation = ('created' if is_create else 'updated')
      if args.async_:
        pretty_print.Success(
            'Job [{{bold}}{job}{{reset}}] is being {operation} '
            'asynchronously.'.format(job=job_obj.name, operation=operation))
      else:
        pretty_print.Success('Job [{{bold}}{job}{{reset}}] has been '
                             'successfully {operation}.'.format(
                                 job=job_obj.name, operation=operation))
      log.status.Print(
          run_messages_util.GetRunJobMessage(self.ReleaseTrack(), job_obj.name))
      return job_obj
