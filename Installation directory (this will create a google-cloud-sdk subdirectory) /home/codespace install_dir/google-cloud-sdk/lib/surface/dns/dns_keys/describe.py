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
"""gcloud dns dns-keys describe command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dns import dns_keys
from googlecloudsdk.core import properties


class DescribeBase(object):
  """Show details about a DNSKEY."""

  detailed_help = dns_keys.DESCRIBE_HELP

  @staticmethod
  def Args(parser):
    dns_keys.AddDescribeFlags(parser, is_beta=True)

  def Run(self, args):
    keys = dns_keys.Keys.FromApiVersion(self.GetApiVersion())
    return keys.Describe(
        args.key_id,
        zone=args.zone,
        project=properties.VALUES.core.project.GetOrFail)

  def GetApiVersion(self):
    raise NotImplementedError


@base.ReleaseTracks(base.ReleaseTrack.GA)
class DescribeGA(DescribeBase, base.DescribeCommand):

  @staticmethod
  def Args(parser):
    dns_keys.AddDescribeFlags(parser, hide_short_zone_flag=True)

  def GetApiVersion(self):
    return 'v1'


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(DescribeBase, base.DescribeCommand):

  def GetApiVersion(self):
    return 'v1beta2'


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class DescribeAlpha(DescribeBase, base.DescribeCommand):

  def GetApiVersion(self):
    return 'v1alpha2'
