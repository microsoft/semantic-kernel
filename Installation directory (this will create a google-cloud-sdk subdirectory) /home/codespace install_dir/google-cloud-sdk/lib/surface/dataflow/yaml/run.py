# -*- coding: utf-8 -*- #
# Copyright 2024 Google LLC. All Rights Reserved.
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
"""Implementation of gcloud dataflow yaml run command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.core import properties
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files


YAML_TEMPLATE_GCS_LOCATION = (
    'gs://dataflow-templates-{}/latest/flex/Yaml_Template'
)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Run(base.Command):
  """Runs a job from the specified path."""

  detailed_help = {
      'DESCRIPTION': (
          'Runs a job from the specified yaml description or gcs path.'
      ),
      'EXAMPLES': """\
          To run a job from yaml, run:

            $ {command} my-job --yaml-pipeline-file=gs://yaml-path --region=europe-west1
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

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--yaml-pipeline-file',
        help=(
            'Path of a file defining the yaml pipeline to run. '
            "(Must be a local file or a URL beginning with 'gs://'.)"
        ),
    )

    group.add_argument(
        '--yaml-pipeline', help='Inline definition of the yaml pipeline to run.'
    )

    parser.add_argument(
        '--region',
        metavar='REGION_ID',
        help=('Region ID of the job\'s regional endpoint. ' +
              dataflow_util.DEFAULT_REGION_MESSAGE))

    parser.add_argument(
        '--pipeline-options',
        metavar='OPTIONS=VALUE;OPTION=VALUE',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        help='Pipeline options to pass to the job.',
    )

  def Run(self, args):
    """Runs the command.

    Args:
      args: The arguments that were provided to this command invocation.

    Returns:
      A Job message.
    """
    parameters = dict(args.pipeline_options or {})

    # These are required and mutually exclusive due to the grouping above.
    if args.yaml_pipeline_file:
      if args.yaml_pipeline_file.startswith('gs://'):
        # TODO(b/320740846): We could consider always downloading this to do
        # validation.
        parameters['yaml_pipeline_file'] = args.yaml_pipeline_file
      else:
        parameters['yaml_pipeline'] = files.ReadFileContents(
            args.yaml_pipeline_file
        )
    else:
      parameters['yaml_pipeline'] = args.yaml_pipeline

    if 'yaml_pipeline' in parameters:
      _validate_yaml(parameters['yaml_pipeline'])

    region_id = dataflow_util.GetRegion(args)

    arguments = apis.TemplateArguments(
        project_id=properties.VALUES.core.project.Get(required=True),
        region_id=region_id,
        job_name=args.job_name,
        gcs_location=YAML_TEMPLATE_GCS_LOCATION.format(region_id),
        parameters=parameters,
    )
    return apis.Templates.CreateJobFromFlexTemplate(arguments)


def _validate_yaml(yaml_pipeline):
  # TODO(b/320740846): Do more complete validation without requiring importing
  # the entire beam library.
  try:
    _ = yaml.load(yaml_pipeline)
  except Exception as exn:
    raise ValueError('yaml_pipeline must be a valid yaml.') from exn
