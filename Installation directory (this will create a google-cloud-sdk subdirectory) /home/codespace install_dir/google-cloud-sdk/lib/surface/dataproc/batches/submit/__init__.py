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

"""The command group for cloud dataproc batches submit."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc.batches import (
    batches_create_request_factory)


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Submit(base.Group):
  """Submit a Dataproc batch job."""
  detailed_help = {
      'EXAMPLES':
          """\
          To submit a PySpark job, run:

            $ {command} pyspark my-pyspark.py --region='us-central1' --deps-bucket=gs://my-bucket --py-files='path/to/my/python/scripts'

          To submit a Spark job, run:

            $ {command} spark --region='us-central1' --deps-bucket=gs://my-bucket --jar='my_jar.jar' -- ARG1 ARG2

          To submit a Spark-R job, run:

            $ {command} spark-r my-main-r.r --region='us-central1' --deps-bucket=gs://my-bucket -- ARG1 ARG2

          To submit a Spark-Sql job, run:

            $ {command} spark-sql 'my-sql-script.sql' --region='us-central1' --deps-bucket=gs://my-bucket --vars='variable=value'
        """
  }

  @staticmethod
  def Args(parser):
    flags.AddAsync(parser)
    batches_create_request_factory.AddArguments(
        parser, dp.Dataproc().api_version)
