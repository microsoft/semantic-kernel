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

"""Submit a Pig job to a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc.jobs import pig
from googlecloudsdk.command_lib.dataproc.jobs import submitter


class Pig(pig.PigBase, submitter.JobSubmitter):
  """Submit a Pig job to a cluster.

  Submit a Pig job to a cluster.

  ## EXAMPLES

  To submit a Pig job with a local script, run:

    $ {command} --cluster=my-cluster --file=my_queries.pig

  To submit a Pig job with inline queries, run:

    $ {command} --cluster=my-cluster
        -e="LNS = LOAD 'gs://my_bucket/my_file.txt' AS (line)"
        -e="WORDS = FOREACH LNS GENERATE FLATTEN(TOKENIZE(line)) AS word"
        -e="GROUPS = GROUP WORDS BY word"
        -e="WORD_COUNTS = FOREACH GROUPS GENERATE group, COUNT(WORDS)"
        -e="DUMP WORD_COUNTS"
  """

  @staticmethod
  def Args(parser):
    pig.PigBase.Args(parser)
    submitter.JobSubmitter.Args(parser)

  def ConfigureJob(self, messages, job, args):
    pig.PigBase.ConfigureJob(messages, job, self.files_by_type,
                             self.BuildLoggingConfig(
                                 messages, args.driver_log_levels), args)
    submitter.JobSubmitter.ConfigureJob(messages, job, args)
