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

"""gcloud dns response-policies command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class ResponsePolicy(base.Group):
  """Manage your Cloud DNS response policy.

  ## EXAMPLES

  To create a response policy, run:

    $ {command} create myresponsepolicy --description="My Response Policy" --network=''

  To update a response policy, run:

    $ {command} update myresponsepolicy --description="My Response Policy" --network=''

  To delete a response policy, run:

    $ {command} delete myresponsepolicy

  To view the details of a response policy, run

    $ {command} describe myresponsepolicy

  To see a list of all response policies, run

    $ {command} list
  """
  pass
