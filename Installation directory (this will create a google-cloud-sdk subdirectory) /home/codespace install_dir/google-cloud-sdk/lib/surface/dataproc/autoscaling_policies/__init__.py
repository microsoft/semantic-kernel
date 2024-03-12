# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""The command group for cloud dataproc autoscaling policies."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.GA)
class AutoscalingPolicies(base.Group):
  """Create and manage Dataproc autoscaling policies.

  Create and manage Dataproc autoscaling policies.

  ## EXAMPLES

  To see the list of all autoscaling policies, run:

    $ {command} list

  To view the details of an autoscaling policy, run:

    $ {command} describe my_policy

  To view just the non-output only fields of an autoscaling policy, run:

    $ {command} export my_policy --destination policy-file.yaml

  To create or update an autoscaling policy, run:

    $ {command} import my_policy --source policy-file.yaml

  To delete an autoscaling policy, run:

    $ {command} delete my_policy
  """
  pass
