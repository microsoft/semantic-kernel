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

"""gcloud dns response-policies rules command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class ResponsePolicyRules(base.Group):
  """Manage your Cloud DNS response policy rules.

  ## EXAMPLES

  To create a new response policy rule with local data rrsets, run:

    $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
    --dns-name="www.zone.com."
    --local-data=name=www.zone.com.,type=CNAME,ttl=21600,rrdatas=zone.com.

  To create a new response policy rule with behavior, run:

    $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
    --dns-name="www.zone.com." --behavior=bypassResponsePolicy

  To update a new response policy rule with local data rrsets, run:

    $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
    --local-data=name=www.zone.com.,type=A,ttl=21600,rrdatas=1.2.3.4

  To update a new response policy rule with behavior, run:

    $ {command} myresponsepolicyrule --response-policy="myresponsepolicy"
    --behavior=bypassResponsePolicy
  """
  pass
