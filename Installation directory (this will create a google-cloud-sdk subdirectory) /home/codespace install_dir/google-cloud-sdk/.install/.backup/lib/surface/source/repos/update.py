# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""`gcloud source repos update` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.source import sourcerepo
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.source import flags
from googlecloudsdk.command_lib.source import util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA,
                    base.ReleaseTrack.ALPHA)
class Update(base.Command):
  r"""Update the configuration of a Cloud Source Repository.

  ## EXAMPLES

  To associate a Cloud Pub/Sub topic to receive repository update notifications,
  run:

    $ {command} --add-topic=TOPIC_NAME --service-account=SERVICE_ACCOUNT_EMAIL \
        --message-format=json
  """

  @staticmethod
  def Args(parser):
    flags.AddRepoUpdateArgs(parser)

  def Run(self, args):
    client = sourcerepo.Source()
    repo_ref = args.CONCEPTS.repo.Parse()
    repo = client.GetRepo(repo_ref)
    updated_repo = util.ParseSourceRepoWithModifiedTopic(args, repo)
    return client.PatchRepo(updated_repo, 'pubsubConfigs')
