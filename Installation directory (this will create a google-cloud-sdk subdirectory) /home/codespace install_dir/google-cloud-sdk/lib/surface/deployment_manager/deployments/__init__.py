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

"""Deployment Manager deployments sub-group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Deployments(base.Group):
  """Commands for Deployment Manager deployments.

  Commands to create, update, delete, and examine deployments of resources.
  """

  detailed_help = {
      'EXAMPLES': """\
          To create a deployment, run:

            $ {command} create my-deployment --config config.yaml

          To update a deployment, run:

            $ {command} update my-deployment --config new_config.yaml

          To stop a deployment create or update in progress, run:

            $ {command} stop my-deployment

          To cancel a previewed create or update, run:

            $ {command} cancel-preview my-deployment

          To delete a deployment, run:

            $ {command} delete my-deployment

          To view the details of a deployment, run:

            $ {command} describe my-deployment

          To see the list of all deployments, run:

            $ {command} list
          """,
  }
