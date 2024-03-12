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
"""Command to create transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.transfer import operations_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.storage import storage_url
from googlecloudsdk.command_lib.transfer import jobs_apitools_util
from googlecloudsdk.command_lib.transfer import jobs_flag_util
from googlecloudsdk.core import log


class Create(base.Command):
  """Create a Transfer Service transfer job."""

  # pylint:disable=line-too-long
  detailed_help = {
      'DESCRIPTION':
          """\
      Create a Transfer Service transfer job, allowing you to transfer data to
      Google Cloud Storage on a one-time or recurring basis.
      """,
      'EXAMPLES':
          """\
      To create a one-time, immediate transfer job to move data from Google
      Cloud Storage bucket "foo" into the "baz" folder in Cloud Storage bucket
      "bar", run:

        $ {command} gs://foo gs://bar/baz/

      To create a transfer job to move data from an Amazon S3 bucket called
      "foo" to a Google Cloud Storage bucket named "bar" that runs every day
      with custom name "my-test-job", run:

        $ {command} s3://foo gs://bar --name=my-test-job --source-creds-file=/examplefolder/creds.txt --schedule-repeats-every=1d

      To create a one-time, immediate transfer job to move data between Google
      Cloud Storage buckets "foo" and "bar" with filters to include objects that
      start with prefixes "baz" and "qux"; and objects modified in the 24 hours
      before the transfer started, run:

        $ {command} gs://foo gs://bar/ --include-prefixes=baz,qux --include-modified-after-relative=1d

      To create a one-time, immediate transfer job to move data from a directory
      with absolute path "/foo/bar/" in the filesystem associated with
      agent pool "my-pool" into Google Cloud Storage bucket "example-bucket",
      run:

        $ {command} posix:///foo/bar/ gs://example-bucket --source-agent-pool=my-pool
      """
  }
  # pylint:enable=line-too-long

  @staticmethod
  def Args(parser):
    jobs_flag_util.setup_parser(parser)

  def Run(self, args):
    is_hdfs_source = args.source.startswith(
        storage_url.ProviderPrefix.HDFS.value
    )
    is_posix_source = args.source.startswith(
        storage_url.ProviderPrefix.POSIX.value
    )
    is_posix_destination = args.destination.startswith(
        storage_url.ProviderPrefix.POSIX.value
    )
    if (is_hdfs_source or is_posix_source) and not args.source_agent_pool:
      raise ValueError(
          'Missing agent pool. Please add --source-agent-pool flag.')
    if is_posix_destination and not args.destination_agent_pool:
      raise ValueError(
          'Missing agent pool. Please add --destination-agent-pool flag.')
    if (is_posix_source and is_posix_destination and
        not args.intermediate_storage_path):
      raise ValueError('Missing intermediate storage path.'
                       ' Please add --intermediate-storage-path flag.')

    client = apis.GetClientInstance('transfer', 'v1')
    messages = apis.GetMessagesModule('transfer', 'v1')

    result = client.transferJobs.Create(
        jobs_apitools_util.generate_transfer_job_message(args, messages))

    if args.no_async:
      log.status.Print('Created job: {}'.format(result.name))
      operations_util.block_until_done(job_name=result.name)

    return result
