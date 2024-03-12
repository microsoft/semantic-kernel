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

"""Submit a Spark batch job."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc.batches import batch_submitter
from googlecloudsdk.command_lib.dataproc.batches import spark_batch_factory


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Spark(base.Command):
  """Submit a Spark batch job."""
  detailed_help = {
      'DESCRIPTION':
          """\
          Submit a Spark batch job.
          """,
      'EXAMPLES':
          """\
          To submit a Spark job, run:

            $ {command} --region=us-central1 --jar=my_jar.jar --deps-bucket=gs://my-bucket -- ARG1 ARG2

          To submit a Spark job that runs a specific class of a jar, run:

            $ {command} --region=us-central1 --class=org.my.main.Class --jars=my_jar1.jar,my_jar2.jar --deps-bucket=gs://my-bucket -- ARG1 ARG2

          To submit a Spark job that runs a jar installed on the cluster, run:

            $ {command} --region=us-central1 --class=org.apache.spark.examples.SparkPi --deps-bucket=gs://my-bucket --jars=file:///usr/lib/spark/examples/jars/spark-examples.jar -- 15
          """
  }

  @staticmethod
  def Args(parser):
    spark_batch_factory.AddArguments(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(base.ReleaseTrack.GA)
    spark_batch = spark_batch_factory.SparkBatchFactory(
        dataproc).UploadLocalFilesAndGetMessage(args)

    return batch_submitter.Submit(spark_batch, dataproc, args)
