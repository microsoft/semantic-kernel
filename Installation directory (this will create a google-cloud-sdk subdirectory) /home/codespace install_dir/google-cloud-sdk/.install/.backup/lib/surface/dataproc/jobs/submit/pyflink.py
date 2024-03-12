# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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

"""Submit a PyFlink job to a cluster."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.dataproc.jobs import pyflink
from googlecloudsdk.command_lib.dataproc.jobs import submitter


class PyFlink(pyflink.PyFlinkBase, submitter.JobSubmitter):
  # pylint: disable=line-too-long
  r"""Submit a PyFlink job to a cluster.

  Submit a PyFlink job to a cluster.

  ## EXAMPLES

    Submit a PyFlink job.

    $ gcloud dataproc jobs submit pyflink my-pyflink.py --region=us-central1

    Submit a PyFlink job with additional source and resource files.

    $ gcloud dataproc jobs submit pyflink my-pyflink.py \
      --region=us-central1 \
      --py-files=my-python-file1.py,my-python-file2.py

    Submit a PyFlink job with a jar file.

    $ gcloud dataproc jobs submit pyflink my-pyflink.py \
      --region=us-central1 \
      --jars=my-jar-file.jar

    Submit a PyFlink job with 'python-files' and 'python-module'.

    $ gcloud dataproc jobs submit pyflink my-pyflink.py \
      --region=us-central1 \
      --py-files=my-python-file1.py,my-python-file2.py
      --py-module=my-module

  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    pyflink.PyFlinkBase.Args(parser)
    submitter.JobSubmitter.Args(parser)

  def ConfigureJob(self, messages, job, args):
    pyflink.PyFlinkBase.ConfigureJob(messages, job, self.files_by_type,
                                     self.BuildLoggingConfig(
                                         messages, args.driver_log_levels),
                                     args)
    submitter.JobSubmitter.ConfigureJob(messages, job, args)
