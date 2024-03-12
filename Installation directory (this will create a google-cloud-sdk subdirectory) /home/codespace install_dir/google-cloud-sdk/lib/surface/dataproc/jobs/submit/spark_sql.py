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

"""Submit a Spark SQL job to a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc.jobs import spark_sql
from googlecloudsdk.command_lib.dataproc.jobs import submitter


class SparkSql(spark_sql.SparkSqlBase, submitter.JobSubmitter):
  """Submit a Spark SQL job to a cluster.

  Submit a Spark SQL job to a cluster.

  ## EXAMPLES

  To submit a Spark SQL job with a local script, run:

    $ {command} --cluster=my-cluster --file=my_queries.ql

  To submit a Spark SQL job with inline queries, run:

    $ {command} --cluster=my-cluster
        -e="CREATE EXTERNAL TABLE foo(bar int) LOCATION 'gs://my_bucket/'"
        -e="SELECT * FROM foo WHERE bar > 2"
  """

  @staticmethod
  def Args(parser):
    spark_sql.SparkSqlBase.Args(parser)
    submitter.JobSubmitter.Args(parser)

  def ConfigureJob(self, messages, job, args):
    spark_sql.SparkSqlBase.ConfigureJob(messages, job, self.files_by_type,
                                        self.BuildLoggingConfig(
                                            messages, args.driver_log_levels),
                                        args)
    submitter.JobSubmitter.ConfigureJob(messages, job, args)
