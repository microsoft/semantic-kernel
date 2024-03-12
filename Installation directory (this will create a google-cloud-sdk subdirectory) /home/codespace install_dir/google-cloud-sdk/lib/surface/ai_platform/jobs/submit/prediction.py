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
"""ai-platform jobs submit batch prediction command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml_engine import jobs
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml_engine import flags
from googlecloudsdk.command_lib.ml_engine import jobs_util
from googlecloudsdk.command_lib.util.args import labels_util


def _AddAcceleratorFlags(parser):
  """Add arguments for accelerator config."""
  accelerator_config_group = base.ArgumentGroup(
      help='Accelerator Configuration.')

  accelerator_config_group.AddArgument(base.Argument(
      '--accelerator-count',
      required=True,
      default=1,
      type=arg_parsers.BoundedInt(lower_bound=1),
      help=('The number of accelerators to attach to the machines.'
            ' Must be >= 1.')))
  accelerator_config_group.AddArgument(
      jobs_util.AcceleratorFlagMap().choice_arg)
  accelerator_config_group.AddToParser(parser)


def _AddSubmitPredictionArgs(parser):
  """Add arguments for `jobs submit prediction` command."""
  parser.add_argument('job', help='Name of the batch prediction job.')
  model_group = parser.add_mutually_exclusive_group(required=True)
  model_group.add_argument(
      '--model-dir',
      help=('Cloud Storage location where '
            'the model files are located.'))
  model_group.add_argument(
      '--model', help='Name of the model to use for prediction.')
  parser.add_argument(
      '--version',
      help="""\
Model version to be used.

This flag may only be given if --model is specified. If unspecified, the default
version of the model will be used. To list versions for a model, run

    $ gcloud ai-platform versions list
""")
  # input location is a repeated field.
  parser.add_argument(
      '--input-paths',
      type=arg_parsers.ArgList(min_length=1),
      required=True,
      metavar='INPUT_PATH',
      help="""\
Cloud Storage paths to the instances to run prediction on.

Wildcards (```*```) accepted at the *end* of a path. More than one path can be
specified if multiple file patterns are needed. For example,

  gs://my-bucket/instances*,gs://my-bucket/other-instances1

will match any objects whose names start with `instances` in `my-bucket` as well
as the `other-instances1` bucket, while

  gs://my-bucket/instance-dir/*

will match any objects in the `instance-dir` "directory" (since directories
aren't a first-class Cloud Storage concept) of `my-bucket`.
""")
  jobs_util.DataFormatFlagMap().choice_arg.AddToParser(parser)
  parser.add_argument(
      '--output-path', required=True,
      help='Cloud Storage path to which to save the output. '
      'Example: gs://my-bucket/output.')
  parser.add_argument(
      '--region',
      required=True,
      help='The Compute Engine region to run the job in.')
  parser.add_argument(
      '--max-worker-count',
      required=False,
      type=int,
      help=('The maximum number of workers to be used for parallel processing. '
            'Defaults to 10 if not specified.'))
  parser.add_argument(
      '--batch-size',
      required=False,
      type=int,
      help=('The number of records per batch. The service will buffer '
            'batch_size number of records in memory before invoking TensorFlow.'
            ' Defaults to 64 if not specified.'))

  flags.SIGNATURE_NAME.AddToParser(parser)
  flags.RUNTIME_VERSION.AddToParser(parser)
  labels_util.AddCreateLabelsFlags(parser)


@base.ReleaseTracks(base.ReleaseTrack.GA,
                    base.ReleaseTrack.BETA)
class Prediction(base.Command):
  """Start an AI Platform batch prediction job."""

  @staticmethod
  def Args(parser):
    _AddSubmitPredictionArgs(parser)
    parser.display_info.AddFormat(jobs_util.JOB_FORMAT)

  def Run(self, args):
    data_format = jobs_util.DataFormatFlagMap().GetEnumForChoice(
        args.data_format)
    jobs_client = jobs.JobsClient()

    labels = jobs_util.ParseCreateLabels(jobs_client, args)
    return jobs_util.SubmitPrediction(
        jobs_client, args.job,
        model_dir=args.model_dir,
        model=args.model,
        version=args.version,
        input_paths=args.input_paths,
        data_format=data_format.name,
        output_path=args.output_path,
        region=args.region,
        runtime_version=args.runtime_version,
        max_worker_count=args.max_worker_count,
        batch_size=args.batch_size,
        signature_name=args.signature_name,
        labels=labels)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class PredictionAlpha(base.Command):
  """Start an AI Platform batch prediction job."""

  @staticmethod
  def Args(parser):
    _AddSubmitPredictionArgs(parser)
    _AddAcceleratorFlags(parser)
    parser.display_info.AddFormat(jobs_util.JOB_FORMAT)

  def Run(self, args):
    data_format = jobs_util.DataFormatFlagMap().GetEnumForChoice(
        args.data_format)
    jobs_client = jobs.JobsClient()

    labels = jobs_util.ParseCreateLabels(jobs_client, args)
    return jobs_util.SubmitPrediction(
        jobs_client, args.job,
        model_dir=args.model_dir,
        model=args.model,
        version=args.version,
        input_paths=args.input_paths,
        data_format=data_format.name,
        output_path=args.output_path,
        region=args.region,
        runtime_version=args.runtime_version,
        max_worker_count=args.max_worker_count,
        batch_size=args.batch_size,
        signature_name=args.signature_name,
        labels=labels,
        accelerator_type=args.accelerator_type,
        accelerator_count=args.accelerator_count)
