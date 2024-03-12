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
"""Cleanup migration resources given a data migration job id."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.spanner import flags
from googlecloudsdk.command_lib.spanner import migration_backend


class Cleanup(base.BinaryBackedCommand):
  """Cleanup migration resources given a data migration job id."""

  detailed_help = {
      'EXAMPLES': textwrap.dedent("""\
        To cleanup resources for a data migration job, specify the jobId and the
        boolean flags for the resources that need to be cleaned up. For sharded
        migrations, specific data shard Ids can also be provided.

          For a all shards of a sharded migration, or a non-sharded migration:
          $ {command} --job-id="XXX" --target-profile="XXX" --datastream --dataflow --pub-sub --monitoring

          For a subset of shards of a sharded migration:
          $ {command} --job-id="XXX" --data-shard-ids="lorem,epsum" --target-profile="XXX" --datastream --dataflow --pub-sub --monitoring

      """),
  }

  @staticmethod
  def Args(parser):
    """Register the flags for this command."""
    flags.GetSpannerMigrationJobIdFlag().AddToParser(parser)
    flags.GetSpannerMigrationDataShardIdsFlag().AddToParser(parser)
    flags.GetSpannerMigrationTargetProfileFlag().AddToParser(parser)
    flags.GetSpannerMigrationCleanupDatastreamResourceFlag().AddToParser(parser)
    flags.GetSpannerMigrationCleanupDataflowResourceFlag().AddToParser(parser)
    flags.GetSpannerMigrationCleanupPubsubResourceFlag().AddToParser(parser)
    flags.GetSpannerMigrationCleanupMonitoringResourceFlag().AddToParser(parser)
    flags.GetSpannerMigrationLogLevelFlag().AddToParser(parser)

  def Run(self, args):
    """Run the schema-and-data command."""
    command_executor = migration_backend.SpannerMigrationWrapper()
    env_vars = migration_backend.GetEnvArgsForCommand(
        extra_vars={'GCLOUD_HB_PLUGIN': 'true'}
    )
    response = command_executor(
        command='cleanup',
        job_id=args.job_id,
        data_shard_ids=args.data_shard_ids,
        target_profile=args.target_profile,
        datastream=args.datastream,
        dataflow=args.dataflow,
        pub_sub=args.pub_sub,
        monitoring=args.monitoring,
        log_level=args.log_level,
        env=env_vars,
    )
    self.exit_code = response.exit_code
    return self._DefaultOperationResponseHandler(response)
