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

"""The gcloud app instances group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Instances(base.Group):
  """View and manage your App Engine instances.

  This set of commands can be used to view and manage your existing App Engine
  instances.

  For more information on App Engine instances, see:
  https://cloud.google.com/appengine/docs/python/an-overview-of-app-engine
  """
  category = base.APP_ENGINE_CATEGORY
  detailed_help = {
      'EXAMPLES': """\
          To list your App Engine instances, run:

            $ {command} list
      """,
  }
