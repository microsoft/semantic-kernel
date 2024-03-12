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
"""Describe metadata about the secret version."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.secrets import api as secrets_api
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.secrets import args as secrets_args


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  r"""Describe metadata about the secret version.

  Describe a secret version's metadata. This command does not include the
  secret version's secret data.

  ## EXAMPLES

  Describe version '123' of the secret named 'my-secret':

    $ {command} 123 --secret=my-secret
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddVersionOrAlias(
        parser, purpose='to describe', positional=True, required=True)

  def Run(self, args):
    version_ref = args.CONCEPTS.version.Parse()
    return secrets_api.Versions().Get(version_ref)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class DescribeBeta(Describe):
  r"""Describe metadata about the secret version.

  Describe a secret version's metadata. This command does not include the
  secret version's secret data.

  ## EXAMPLES

  Describe version '123' of the secret named 'my-secret':

    $ {command} 123 --secret=my-secret
  """

  @staticmethod
  def Args(parser):
    secrets_args.AddVersionOrAlias(
        parser, purpose='to describe', positional=True, required=True)
