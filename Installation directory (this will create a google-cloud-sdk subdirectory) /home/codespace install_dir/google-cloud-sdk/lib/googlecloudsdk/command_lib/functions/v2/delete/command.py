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
"""This file provides the implementation of the `functions delete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.functions.v2 import exceptions
from googlecloudsdk.api_lib.functions.v2 import util as api_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def Run(args, release_track):
  """Delete a Google Cloud Function."""
  client = api_util.GetClientInstance(release_track=release_track)
  messages = api_util.GetMessagesModule(release_track=release_track)

  function_ref = args.CONCEPTS.name.Parse()
  function_relative_name = function_ref.RelativeName()

  prompt_message = '2nd gen function [{0}] will be deleted.'.format(
      function_relative_name
  )
  if not console_io.PromptContinue(message=prompt_message):
    raise exceptions.FunctionsError('Deletion aborted by user.')

  operation = client.projects_locations_functions.Delete(
      messages.CloudfunctionsProjectsLocationsFunctionsDeleteRequest(
          name=function_relative_name))
  api_util.WaitForOperation(client, messages, operation, 'Deleting function')

  log.DeletedResource(function_relative_name)
