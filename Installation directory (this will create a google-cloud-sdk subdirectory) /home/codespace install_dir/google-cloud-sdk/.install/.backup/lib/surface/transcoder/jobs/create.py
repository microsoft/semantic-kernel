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

"""Cloud Transcoder jobs create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transcoder import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transcoder import flags
from googlecloudsdk.command_lib.transcoder import resource_args
from googlecloudsdk.command_lib.transcoder import util
from googlecloudsdk.command_lib.util.args import labels_util


class Create(base.CreateCommand):
  """Create Transcoder jobs."""

  detailed_help = {'EXAMPLES': """
        To create a transcoder job with default template, input URI, and output URI:

          $ {command} --location=us-central1 --input-uri="gs://bucket/input.mp4" --output-uri="gs://bucket/output/"

        To create a transcoder job with template id, input URI, and output URI:

          $ {command} --location=us-central1 --input-uri="gs://bucket/input.mp4" --output-uri="gs://bucket/output/" --template-id=my-template

        To create a transcoder job with json format configuration:

          $ {command} --location=us-central1 --json="config: json-format"

        To create a transcoder job with json format configuration file:

          $ {command} --location=us-central1 --file="config.json"

        To create a transcoder job with labels:

          $ {command} --location=us-central1 --file="config.json" --labels=key=value

        To create a transcoder job in batch mode:

          $ {command} --location=us-central1 --file="config.json" --mode=PROCESSING_MODE_BATCH

        To create a transcoder job in batch mode with priority:

          $ {command} --location=us-central1 --file="config.json" --mode=PROCESSING_MODE_BATCH --batch-mode-priority=3

        To create a transcoder job with optimizations disabled:

          $ {command} --location=us-central1 --file="config.json" --optimization=DISABLED
      """}

  @staticmethod
  def Args(parser):
    resource_args.AddLocationResourceArg(parser)
    flags.AddCreateJobFlags(parser)
    parser.display_info.AddFormat('json')
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    """Create a job."""
    util.ValidateCreateJobArguments(args)

    client = jobs.JobsClient(self.ReleaseTrack())

    parent_ref = args.CONCEPTS.location.Parse()

    return client.Create(
        parent_ref=parent_ref,
        args=args,
    )
