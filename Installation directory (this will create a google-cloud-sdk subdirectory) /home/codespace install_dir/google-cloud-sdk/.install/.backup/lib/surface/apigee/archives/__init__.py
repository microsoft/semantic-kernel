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
"""The archives command group for the Apigee CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import util


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class Archives(base.Group):
  """Manage Apigee archive deployments."""
  detailed_help = {
      "EXAMPLES": """
          To deploy a local archive deployment remotely to the management plane
          in the ``test'' environment, run:

              $ {command} deploy --environment=test

          To list all archive deployments in the ``dev'' environment, run:

              $ {command} list --environment=dev

          To describe the archive deployment with id ``abcdef01234'' in the
          ``demo'' environment of the ``my-org'' Apigee organization, run:

              $ {command} describe abcdef01234 --environment=demo --organization=my-org

          To update the labels of the archive deployment with id
          ``uvxwzy56789'' in the ``test'' environment, run:

              $ {command} update uvxwzy56789 --environment=demo --update-labels=foo=1,bar=2
      """,
  }
