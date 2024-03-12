# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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

"""The command group for cloud dataproc sessions create."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc.sessions import (
    sessions_create_request_factory)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class Create(base.Group):
  """Create a Dataproc session."""
  detailed_help = {
      'DESCRIPTION':
          """\
          Create various sessions, such as Spark.
          """,
      'EXAMPLES':
          """\

          To create a Spark session, run:

            $ {command} spark my-session --location='us-central1'
        """
  }

  @staticmethod
  def Args(parser):
    flags.AddAsync(parser)
    sessions_create_request_factory.AddArguments(parser)
