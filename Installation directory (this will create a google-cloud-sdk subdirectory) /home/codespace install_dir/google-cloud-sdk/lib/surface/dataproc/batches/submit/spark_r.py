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

"""Submit a SparkR batch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc.batches import batch_submitter
from googlecloudsdk.command_lib.dataproc.batches import sparkr_batch_factory


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class SparkR(base.Command):
  """Submit a Spark R batch job."""
  detailed_help = {
      'EXAMPLES':
          """\
          To submit a Spark R batch job running "my-main-r.r" script and upload it to "gs://my-bucket", run:

            $ {command} my-main-r.r --deps-bucket=gs://my-bucket --region='us-central1' -- ARG1 ARG2
          """
  }

  @staticmethod
  def Args(parser):
    sparkr_batch_factory.AddArguments(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)
    sparkr_batch = sparkr_batch_factory.SparkRBatchFactory(
        dataproc).UploadLocalFilesAndGetMessage(args)

    return batch_submitter.Submit(sparkr_batch, dataproc, args)
