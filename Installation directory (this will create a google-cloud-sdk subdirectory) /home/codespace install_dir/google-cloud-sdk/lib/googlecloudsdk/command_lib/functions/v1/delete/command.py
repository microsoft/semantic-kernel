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

from googlecloudsdk.api_lib.functions.v1 import exceptions
from googlecloudsdk.api_lib.functions.v1 import operations
from googlecloudsdk.api_lib.functions.v1 import util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


def Run(args):
  """Delete a Google Cloud Function."""
  client = util.GetApiClientInstance()
  messages = client.MESSAGES_MODULE
  function_ref = args.CONCEPTS.name.Parse()
  function_url = function_ref.RelativeName()
  prompt_message = '1st gen function [{0}] will be deleted.'.format(
      function_url
  )
  if not console_io.PromptContinue(message=prompt_message):
    raise exceptions.FunctionsError('Deletion aborted by user.')
  op = client.projects_locations_functions.Delete(
      messages.CloudfunctionsProjectsLocationsFunctionsDeleteRequest(
          name=function_url
      )
  )
  operations.Wait(op, messages, client)
  log.DeletedResource(function_url)
