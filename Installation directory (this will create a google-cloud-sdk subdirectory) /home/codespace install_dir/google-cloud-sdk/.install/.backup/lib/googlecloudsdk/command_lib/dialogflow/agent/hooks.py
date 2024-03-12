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

"""Declarative hooks for `gcloud dialogflow agent`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import base64

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


def AddSessionPrefix(session):
  project = properties.VALUES.core.project.GetOrFail()
  return 'projects/{}/agent/sessions/{}'.format(project, session)


def SetQueryLanguage(unused_instance_ref, args, request):
  query_input = request.googleCloudDialogflowV2DetectIntentRequest.queryInput
  if args.IsSpecified('query_text'):
    query_input.text.languageCode = args.language
  elif args.IsSpecified('query_audio_file'):
    query_input.audioConfig.languageCode = args.language
  return request


def LogTrainSuccess(unused_response, unused_args):
  log.status.Print('Successfully trained agent.')


def IsBucketUri(path):
  return path.startswith(storage_util.GSUTIL_BUCKET_PREFIX)


def SetAgentUri(unused_instance_ref, args, request):
  dest = args.destination
  if IsBucketUri(dest) and storage_util.ValidateBucketUrl:
    request.googleCloudDialogflowV2ExportAgentRequest = {'agentUri': dest}
  return request


def SaveAgentToFile(response, args):
  dest = args.destination
  if not IsBucketUri(dest):
    props = response.additionalProperties
    agent_content = next(prop for prop in props if prop.key == 'agentContent')
    agent_content_bin = base64.b64decode(agent_content.value.string_value)
    log.WriteToFileOrStdout(dest, agent_content_bin, binary=True)
    if dest != '-':
      log.status.Print('Wrote agent to [{}].'.format(dest))
  return response


def ChooseImportOrRestoreMethod(unused_instance_ref, args):
  if args.replace_all:
    return 'restore'
  return 'import'


def _GetAgentRequestBody(source):
  if source.startswith('gs://'):
    return {'agentUri': source}
  else:
    return {'agentContent': files.ReadBinaryFileContents(source)}


def ModifyImportOrRestoreRequest(unused_instance_ref, args, request):
  body = _GetAgentRequestBody(args.source)

  if args.replace_all:
    request.googleCloudDialogflowV2RestoreAgentRequest = body
  else:
    request.googleCloudDialogflowV2ImportAgentRequest = body

  return request


def LogImportSuccess(response, args):
  path = args.source
  if not args.async_:
    if path != '-':
      log.status.Print('Successfully imported agent from [{}].'.format(path))
    else:
      log.status.Print('Successfully imported agent.')
    if args.replace_all:
      log.status.Print('Replaced all existing resources.')
  return response
