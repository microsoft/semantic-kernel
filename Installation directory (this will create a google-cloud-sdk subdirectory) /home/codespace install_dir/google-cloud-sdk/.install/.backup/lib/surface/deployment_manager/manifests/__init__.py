# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.
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

"""Deployment Manager manifests sub-group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions


class Manifests(base.Group):
  """Commands for Deployment Manager manifests.

  Commands to list and examine manifests within a deployment.
  """

  detailed_help = {
      'EXAMPLES': """\
          To view all details about a manifest, run:

            $ {command} describe manifest-name --deployment my-deployment

          To see the list of all manifests in a deployment, run:

            $ {command} list --deployment my-deployment
          """,
  }

