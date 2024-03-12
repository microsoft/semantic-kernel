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
"""services list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.services import serviceusage
from googlecloudsdk.calliope import base


class List(base.ListCommand):
  """List service quota metrics for a consumer.

  This command lists the service quota metrics for a consumer. The supported
  consumers can be projects, folders, or organizations.

  ## EXAMPLES

  To list the quota metrics for service 'example.googleapis.com' and consumer
  'projects/12321', run:

    $ {command} --service=example.googleapis.com --consumer=projects/12321

  To list the quota metrics for service 'example.googleapis.com' and consumer
  'projects/hello-world', run:

    $ {command} --service=example.googleapis.com --consumer=projects/helloworld

  To list the quota metrics for service 'example.googleapis.com' and consumer
  'folders/12345', run:

    $ {command} --service=example.googleapis.com --consumer=folders/12345

  To list the quota metrics for service 'example.googleapis.com' and consumer
  'organizations/54321', run:

    $ {command} --service=example.googleapis.com --consumer=organizations/54321
  """

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go on
        the command line after this command. Positional arguments are allowed.
    """
    parser.add_argument(
        '--service',
        required=True,
        metavar='SERVICE',
        help='The service to list metrics for.')

    parser.add_argument(
        '--consumer',
        required=True,
        metavar='CONSUMER',
        help='The consumer to list metrics for.')

  def Run(self, args):
    """Run command.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      The list of quota metrics for the service and consumer.
    """
    metrics = serviceusage.ListQuotaMetrics(args.consumer, args.service,
                                            args.page_size, args.limit)
    return [self.delete_resource_name(m) for m in metrics]

  @staticmethod
  def delete_resource_name(metric):
    """Delete the name fields from metric message.

    Args:
      metric: The quota metric message.

    Returns:
      The updated metric message.
    """
    metric.reset('name')
    for l in metric.consumerQuotaLimits:
      l.reset('name')
    return metric
