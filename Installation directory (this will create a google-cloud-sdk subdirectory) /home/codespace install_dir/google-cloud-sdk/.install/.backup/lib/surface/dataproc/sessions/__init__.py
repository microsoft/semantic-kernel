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
"""The command group for cloud dataproc sessions."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Sessions(base.Group):
  """Create and manage Dataproc sessions.


  Create and manage Dataproc sessions.

  Create a session:

    $ {command} create

  List all sessions:

    $ {command} list

  List session details:

    $ {command} describe SESSION_ID

  Delete a session:

    $ {command} delete SESSION_ID

  Terminate an active session:

    $ {command} terminate SESSION_ID

  Enable Personal Auth on an active session:

    $ {command} enable-personal-auth-session SESSION_ID
  """
