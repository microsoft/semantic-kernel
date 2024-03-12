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
"""Implementation of `gcloud dataflow sql query` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import collections

from googlecloudsdk.api_lib.dataflow import apis
from googlecloudsdk.api_lib.dataflow import sql_query_parameters
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataflow import dataflow_util
from googlecloudsdk.command_lib.dataflow import sql_util
from googlecloudsdk.core import properties

DETAILED_HELP = {
    'DESCRIPTION':
        'Execute the user-specified SQL query on Dataflow. Queries must '
        'comply to the ZetaSQL dialect (https://github.com/google/zetasql). '
        'Results may be written to either BigQuery or Cloud Pub/Sub.',
    'EXAMPLES':
        """\
      To execute a simple SQL query on Dataflow that reads from and writes to BigQuery, run:

        $ {command} 'SELECT word FROM bigquery.table.`my-project`.input_dataset.input_table where count > 3' --job-name=my-job --region=us-west1 --bigquery-dataset=my_output_dataset --bigquery-table=my_output_table

      To execute a simple SQL query on Dataflow that reads from and writes to Cloud
      Pub/Sub, run:

        $ {command} 'SELECT word FROM pubsub.topic.`my-project`.input_topic where count > 3' --job-name=my-job --region=us-west1 --pubsub-topic=my_output_topic

      To join data from BigQuery and Cloud Pub/Sub and write the result to Cloud
      Pub/Sub, run:

        $ {command} 'SELECT bq.name AS name FROM pubsub.topic.`my-project`.input_topic p INNER JOIN bigquery.table.`my-project`.input_dataset.input_table bq ON p.id = bq.id' --job-name=my-job --region=us-west1 --pubsub-topic=my_output_topic

      To execute a parameterized SQL query that reads from and writes to BigQuery, run:

        $ {command} 'SELECT word FROM bigquery.table.`my-project`.input_dataset.input_table where count > @threshold' --parameter=threshold:INT64:5 --job-name=my-job --region=us-west1 --bigquery-dataset=my_output_dataset --bigquery-table=my_output_table

    """,
}


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Query(base.Command):
  """Execute the user-specified SQL query on Dataflow."""

  detailed_help = DETAILED_HELP

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: argparse.ArgumentParser to register arguments with.
    """
    sql_util.ArgsForSqlQuery(parser)

  def Run(self, args):
    use_dynamic_engine = (args.sql_launcher_template_engine == 'dynamic')
    region = dataflow_util.GetRegion(args)
    if args.sql_launcher_template:
      gcs_location = args.sql_launcher_template
    else:
      if use_dynamic_engine:
        suffix = 'sql_launcher_template'
      else:
        suffix = 'sql_launcher_flex_template'
      gcs_location = 'gs://dataflow-sql-templates-{}/latest/{}'.format(
          region, suffix)
    if args.parameters_file:
      query_parameters = sql_query_parameters.ParseParametersFile(
          args.parameters_file)
    elif args.parameter:
      query_parameters = sql_query_parameters.ParseParametersList(
          args.parameter)
    else:
      query_parameters = '[]'
    template_parameters = collections.OrderedDict([
        ('dryRun', 'true' if args.dry_run else 'false'),
        ('outputs', sql_util.ExtractOutputs(args)),
        ('queryParameters', query_parameters),
        ('queryString', args.query),
    ])
    arguments = apis.TemplateArguments(
        project_id=properties.VALUES.core.project.GetOrFail(),
        region_id=region,
        job_name=args.job_name,
        gcs_location=gcs_location,
        zone=args.zone,
        max_workers=args.max_workers,
        disable_public_ips=properties.VALUES.dataflow.disable_public_ips
        .GetBool(),
        parameters=template_parameters,
        service_account_email=args.service_account_email,
        kms_key_name=args.dataflow_kms_key,
        num_workers=args.num_workers,
        network=args.network,
        subnetwork=args.subnetwork,
        worker_machine_type=args.worker_machine_type,
        worker_region=args.worker_region,
        worker_zone=args.worker_zone)
    if use_dynamic_engine:
      return apis.Templates.LaunchDynamicTemplate(arguments)
    return apis.Templates.CreateJobFromFlexTemplate(arguments)
