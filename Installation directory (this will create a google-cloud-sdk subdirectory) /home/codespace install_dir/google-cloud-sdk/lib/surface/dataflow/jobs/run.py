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
"""Implementation of gcloud dataflow jobs run command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.command_lib.dataflow import job_utils
from googlecloudsdk.core import properties


def _CommonArgs(parser):
  """Register flags for this command.

  Args:
    parser: argparse.ArgumentParser to register arguments with.
  """
  job_utils.CommonArgs(parser)

  parser.add_argument(
      'job_name',
      metavar='JOB_NAME',
      help='The unique name to assign to the job.')

  parser.add_argument(
      '--gcs-location',
      help=('The Google Cloud Storage location of the job template to run. '
            "(Must be a URL beginning with 'gs://'.)"),
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''),
      required=True)

  parser.add_argument(
      '--staging-location',
      help=('The Google Cloud Storage location to stage temporary files. '
            "(Must be a URL beginning with 'gs://'.)"),
      type=arg_parsers.RegexpValidator(r'^gs://.*',
                                       'Must begin with \'gs://\''))

  parser.add_argument(
      '--parameters',
      metavar='PARAMETERS',
      type=arg_parsers.ArgDict(),
      action=arg_parsers.UpdateAction,
      help='The parameters to pass to the job.')

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
      help=('Additional experiments to pass to the job. These experiments are '
            'appended to any experiments already set by the template.'))

  # TODO(b/139889563): Mark as required when default region is removed
  parser.add_argument(
      '--region',
      metavar='REGION_ID',
      help=('Region ID of the job\'s regional endpoint. ' +
            dataflow_util.DEFAULT_REGION_MESSAGE))


def _CommonRun(args):
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
      gcs_location=args.gcs_location,
      zone=args.zone,
      max_workers=args.max_workers,
      num_workers=args.num_workers,
      network=args.network,
      subnetwork=args.subnetwork,
      worker_machine_type=args.worker_machine_type,
      staging_location=args.staging_location,
      kms_key_name=args.dataflow_kms_key,
      disable_public_ips=properties.VALUES.dataflow.disable_public_ips.GetBool(
      ),
      parameters=args.parameters,
      service_account_email=args.service_account_email,
      worker_region=args.worker_region,
      worker_zone=args.worker_zone,
      enable_streaming_engine=properties.VALUES.dataflow.enable_streaming_engine
      .GetBool(),
      additional_experiments=args.additional_experiments)
  return apis.Templates.Create(arguments)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Run(base.Command):
  """Runs a job from the specified path."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    return _CommonRun(args)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RunBeta(Run):
  """Runs a job from the specified path."""

  @staticmethod
  def Args(parser):
    _CommonArgs(parser)

  def Run(self, args):
    return _CommonRun(args)
