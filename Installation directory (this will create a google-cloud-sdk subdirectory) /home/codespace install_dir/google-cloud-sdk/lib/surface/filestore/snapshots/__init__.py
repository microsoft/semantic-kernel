# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Command group for Filestore snapshots."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Snapshots(base.Group):
  """Create and manage Filestore snapshots.

  ## EXAMPLES

  To create a snapshot with the name 'my-snapshot', run:

    $ {command} create my-snapshot

  To delete a snapshot with the name 'my-snapshot', run:

    $ {command} delete my-snapshot

  To display the details for an snapshot with the name 'my-snapshot', run:

    $ {command} describe my-snapshot

  To list all the snapshots, run:

    $ {command} list

  To set the label 'env' to 'prod' for an snapshot with the name
  'my-snapshot', run:

    $ {command} my-snapshot --update-labels=env=prod
  """
