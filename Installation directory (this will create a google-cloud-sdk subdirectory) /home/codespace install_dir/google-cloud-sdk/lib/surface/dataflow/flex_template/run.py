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
"""Implementation of gcloud dataflow flex_template run command.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Run(base.Command):
  """Runs a job from the specified path."""

  detailed_help = {
      'DESCRIPTION':
          'Runs a job from the specified flex template gcs path.',
      'EXAMPLES':
          """\
          To run a job from the flex template, run:

            $ {command} my-job --template-file-gcs-location=gs://flex-template-path --region=europe-west1 --parameters=input="gs://input",output="gs://output-path" --max-workers=5
          """,
  }

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    parser.add_argument(
        'job_name',
        metavar='JOB_NAME',
        help='Unique name to assign to the job.')

    parser.add_argument(
        '--template-file-gcs-location',
        help=('Google Cloud Storage location of the flex template to run. '
              "(Must be a URL beginning with 'gs://'.)"),
        type=arg_parsers.RegexpValidator(r'^gs://.*',
                                         'Must begin with \'gs://\''),
        required=True)

    parser.add_argument(
        '--region',
        metavar='REGION_ID',
        help=('Region ID of the job\'s regional endpoint. ' +
              dataflow_util.DEFAULT_REGION_MESSAGE))

    parser.add_argument(
        '--staging-location',
        help=('Default Google Cloud Storage location to stage local files.'
              "(Must be a URL beginning with 'gs://'.)"),
        type=arg_parsers.RegexpValidator(r'^gs://.*',
                                         'Must begin with \'gs://\''))

    parser.add_argument(
        '--temp-location',
        help=('Default Google Cloud Storage location to stage temporary files. '
              'If not set, defaults to the value for --staging-location.'
              "(Must be a URL beginning with 'gs://'.)"),
        type=arg_parsers.RegexpValidator(r'^gs://.*',
                                         'Must begin with \'gs://\''))

    parser.add_argument(
        '--service-account-email',
        type=arg_parsers.RegexpValidator(r'.*@.*\..*',
                                         'must provide a valid email address'),
        help='Service account to run the workers as.')

    parser.add_argument(
        '--max-workers', type=int, help='Maximum number of workers to run.')

    parser.add_argument(
        '--disable-public-ips',
        action=actions.StoreBooleanProperty(
            properties.VALUES.dataflow.disable_public_ips),
        help='Cloud Dataflow workers must not use public IP addresses.')

    parser.add_argument(
        '--num-workers', type=int, help='Initial number of workers to use.')

    parser.add_argument(
        '--worker-machine-type',
        help='Type of machine to use for workers. Defaults to '
        'server-specified.')

    parser.add_argument(
        '--subnetwork',
        help='Compute Engine subnetwork for launching instances '
        'to run your pipeline.')

    parser.add_argument(
        '--network',
        help='Compute Engine network for launching instances to '
        'run your pipeline.')

    parser.add_argument(
        '--dataflow-kms-key',
        help='Cloud KMS key to protect the job resources.')

    region_group = parser.add_mutually_exclusive_group()
    region_group.add_argument(
        '--worker-region',
        help='Region to run the workers in.')

    region_group.add_argument(
        '--worker-zone',
        help='Zone to run the workers in.')

    parser.add_argument(
        '--enable-streaming-engine',
        action=actions.StoreBooleanProperty(
            properties.VALUES.dataflow.enable_streaming_engine),
        help='Enabling Streaming Engine for the streaming job.')

    parser.add_argument(
        '--additional-experiments',
        metavar='ADDITIONAL_EXPERIMENTS',
        type=arg_parsers.ArgList(),
        action=arg_parsers.UpdateAction,
        help=
        ('Additional experiments to pass to the job.'))

    parser.add_argument(
        '--additional-user-labels',
        metavar='ADDITIONAL_USER_LABELS',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help=
        ('Additional user labels to pass to the job.'))

    parser.add_argument(
        '--parameters',
        metavar='PARAMETERS',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help=
        ('Parameters to pass to the job.'))
    streaming_update_args = parser.add_argument_group()
    streaming_update_args.add_argument(
        '--transform-name-mappings',
        metavar='TRANSFORM_NAME_MAPPINGS',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help=
        ('Transform name mappings for the streaming update job.'))

    streaming_update_args.add_argument(
        '--update',
        help=('Set this to true for streaming update jobs.'),
        action=arg_parsers.StoreTrueFalseAction,
        required=True)

    parser.add_argument(
        '--flexrs-goal',
        help=('FlexRS goal for the flex template job.'),
        choices=['COST_OPTIMIZED', 'SPEED_OPTIMIZED'])

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      A Job message.
    """
    arguments = apis.TemplateArguments(
        project_id=properties.VALUES.core.project.Get(required=True),
        region_id=dataflow_util.GetRegion(args),
        job_name=args.job_name,
        gcs_location=args.template_file_gcs_location,
        max_workers=args.max_workers,
        num_workers=args.num_workers,
        network=args.network,
        subnetwork=args.subnetwork,
        worker_machine_type=args.worker_machine_type,
        kms_key_name=args.dataflow_kms_key,
        staging_location=args.staging_location,
        temp_location=args.temp_location,
        disable_public_ips=
        properties.VALUES.dataflow.disable_public_ips.GetBool(),
        service_account_email=args.service_account_email,
        worker_region=args.worker_region,
        worker_zone=args.worker_zone,
        enable_streaming_engine=
        properties.VALUES.dataflow.enable_streaming_engine.GetBool(),
        additional_experiments=args.additional_experiments,
        additional_user_labels=args.additional_user_labels,
        streaming_update=args.update,
        transform_name_mappings=args.transform_name_mappings,
        flexrs_goal=args.flexrs_goal,
        parameters=args.parameters)
    return apis.Templates.CreateJobFromFlexTemplate(arguments)

