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
"""Command group for Filestore backups."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Backups(base.Group):
  """Create and manage Filestore backups.

  ## EXAMPLES

  To create a backup with the name 'my-backup', run:

    $ {command} create my-backup --region=Region

  To delete a backup with the name 'my-backup', run:

    $ {command} delete my-backup --region=Region

  To display the details for an backup with the name 'my-backup', run:

    $ {command} describe my-backup --region=Region

  To list all the backups, run:

    $ {command} list [--region=Region]

  To set the label 'env' to 'prod' for an backup with the name
  'my-backup', run:

    $ {command} my-backup --update-labels=env=prod
  """
