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

"""The gcloud dns command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class DNS(base.Group):
  """Manage your Cloud DNS managed-zones and record-sets.

  The gcloud dns command group lets you create and manage DNS zones and
  their associated records on Google Cloud DNS.

  Cloud DNS is a scalable, reliable and managed authoritative DNS service
  running on the same infrastructure as Google. It has low latency, high
  availability and is a cost-effective way to make your applications and
  services available to your users.

  More information on Cloud DNS can be found here:
  https://cloud.google.com/dns and detailed documentation can be found
  here: https://cloud.google.com/dns/docs/

  ## EXAMPLES

  To see how to create and maintain managed-zones, run:

    $ {command} managed-zones --help

  To see how to maintain the record-sets within a managed-zone, run:

    $ {command} record-sets --help

  To display Cloud DNS related information for your project, run:

    $ {command} project-info describe --help
  """

  category = base.NETWORKING_CATEGORY

  def Filter(self, context, args):
    # TODO(b/190532649):  Determine if command group works with project number
    base.RequireProjectID(args)
    del context, args
    base.DisableUserProjectQuota()
