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

"""gcloud dns managed-zones command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class ManagedZones(base.Group):
  """Manage your Cloud DNS managed-zones.

  Manage your Cloud DNS managed-zones. See
  [Managing Zones](https://cloud.google.com/dns/zones/) for details.

  ## EXAMPLES

  To create a managed-zone, run:

    $ {command} create my-zone --description="My Zone" --dns-name="my.zone.com."

  To delete a managed-zone, run:

    $ {command} delete my-zone

  To view the details of a managed-zone, run:

    $ {command} describe my-zone

  To see the list of all managed-zones, run:

    $ {command} list
  """
  pass
