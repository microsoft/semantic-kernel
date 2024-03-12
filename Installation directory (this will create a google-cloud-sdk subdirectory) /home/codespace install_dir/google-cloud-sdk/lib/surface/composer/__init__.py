# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""The main command group for Cloud Composer."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Composer(base.Group):
  """Create and manage Cloud Composer Environments.

  Cloud Composer is a managed Apache Airflow service that helps you create,
  schedule, monitor and manage workflows. Cloud Composer automation helps you
  create Airflow environments quickly and use Airflow-native tools, such as the
  powerful Airflow web interface and command line tools, so you can focus on
  your workflows and not your infrastructure.

  ## EXAMPLES

  To see how to create and manage environments, run:

      $ {command} environments --help

  To see how to manage long-running operations, run:

      $ {command} operations --help
  """

  category = base.DATA_ANALYTICS_CATEGORY

  def Filter(self, context, args):
    """Modify the context that will be given to this group's commands when run.

    Args:
      context: {str:object}, A set of key-value pairs that can be used for
          common initialization among commands.
      args: argparse.Namespace: The same namespace given to the corresponding
          .Run() invocation.

    Returns:
      The refined command context.
    """
    # TODO(b/190528955):  Determine if command group works with project number
    base.RequireProjectID(args)
    # The Composer API performs quota checking based on the resource project, so
    # user project overrides are not needed. The 'environments run' command
    # spawns a call to the Kubernetes Engine API, and the 'container' command
    # group also disables user project quota; removing this line will break
    # 'composer environments run.'
    base.DisableUserProjectQuota()

    return context
