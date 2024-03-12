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
"""The gcloud Firestore backups list command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.firestore import backups
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.firestore import flags
from googlecloudsdk.core import properties


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class List(base.ListCommand):
  """List backups available to Cloud Firestore.

  ## EXAMPLES

  To list all backups in location us-east1.

      $ {command} --location=us-east1 --format="table(name, database, state)"

  To list all backups in all location.

      $ {command} --format="table(name, database, state)"
  """

  @staticmethod
  def Args(parser):
    flags.AddLocationFlag(parser)

  def Run(self, args):
    project = properties.VALUES.core.project.Get(required=True)
    location = '-' if args.location is None else args.location
    return backups.ListBackups(project, location)
