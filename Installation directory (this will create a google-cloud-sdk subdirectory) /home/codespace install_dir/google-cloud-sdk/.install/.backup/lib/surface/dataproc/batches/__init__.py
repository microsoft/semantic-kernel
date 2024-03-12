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

"""The command group for cloud dataproc batches."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Batches(base.Group):
  """Submit Dataproc batch jobs.

  Submit Dataproc batch jobs.

  Submit a job:

    $ {command} submit

  List all batch jobs:

    $ {command} list

  List job details:

    $ {command} describe JOB_ID

  Delete a batch job:

    $ {command} delete JOB_ID

  Cancel a running batch job without removing the batch resource:

    $ {command} cancel JOB_ID

  View job output:

    $ {command} wait JOB_ID
  """
