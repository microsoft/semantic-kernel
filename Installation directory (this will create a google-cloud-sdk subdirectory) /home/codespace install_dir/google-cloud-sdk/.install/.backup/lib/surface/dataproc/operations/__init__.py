# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""The command group for cloud dataproc operations."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class Operations(base.Group):
  """View and manage Dataproc operations.

  View and manage Dataproc operations.

  ## EXAMPLES

  To cancel an active operation, run:

    $ {command} cancel operation_id

  To view the details of an operation, run:

    $ {command} describe operation_id

  To see the list of all operations, run:

    $ {command} list

  To delete the record of an inactive operation, run:

    $ {command} delete operation_id
  """
