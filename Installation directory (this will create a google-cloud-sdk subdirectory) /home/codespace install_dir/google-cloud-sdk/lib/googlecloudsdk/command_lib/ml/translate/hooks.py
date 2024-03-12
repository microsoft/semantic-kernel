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

"""Declarative hooks for ml speech."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import files


SPEECH_API = 'translate'


def _GetApiVersion(args):
  if args.calliope_command.ReleaseTrack() == calliope_base.ReleaseTrack.BETA:
    return 'v3'
  else:
    return 'v3beta1'


class Error(exceptions.Error):
  """Exceptions for this module."""


class ContentFileError(Error):
  """Error if content file can't be read and isn't a GCS URL."""


def UpdateRequestLangDetection(unused_instance_ref, args, request):
  """The hook to inject content into the language detection request."""
  content = args.content
  content_file = args.content_file
  messages = apis.GetMessagesModule(SPEECH_API, _GetApiVersion(args))
  detect_language_request = messages.DetectLanguageRequest()
  project = properties.VALUES.core.project.GetOrFail()

  request.parent = 'projects/{}/locations/{}'.format(project, args.zone)

  if args.IsSpecified('model'):
    project = properties.VALUES.core.project.GetOrFail()
    model = 'projects/{}/locations/{}/models/language-detection/{}'.format(
        project, args.zone, args.model)
    detect_language_request.model = model
  if content_file:
    if os.path.isfile(content_file):
      detect_language_request.content = files.ReadFileContents(content_file)
    else:
      raise ContentFileError(
          'Could not find --content-file [{}]. Content file must be a path '
          'to a local file)'.format(content_file))
  else:
    detect_language_request.content = content
  if args.IsSpecified('mime_type'):
    detect_language_request.mimeType = args.mime_type
  request.detectLanguageRequest = detect_language_request
  return request


def UpdateRequestTranslateText(unused_instance_ref, args, request):
  """The hook to inject content into the translate request."""
  content = args.content
  content_file = args.content_file
  messages = apis.GetMessagesModule(SPEECH_API, _GetApiVersion(args))
  translate_text_request = messages.TranslateTextRequest()
  project = properties.VALUES.core.project.GetOrFail()

  request.parent = 'projects/{}/locations/{}'.format(project, args.zone)

  if args.IsSpecified('model'):
    project = properties.VALUES.core.project.GetOrFail()
    model = 'projects/{}/locations/{}/models/{}'.format(
        project, args.zone, args.model)
    translate_text_request.model = model
  if content_file:
    if os.path.isfile(content_file):
      translate_text_request.contents = [files.ReadFileContents(content_file)]
    else:
      raise ContentFileError(
          'Could not find --content-file [{}]. Content file must be a path '
          'to a local file)'.format(content_file))
  else:
    translate_text_request.contents = [content]
  if args.IsSpecified('mime_type'):
    translate_text_request.mimeType = args.mime_type
  if args.IsSpecified('glossary_config'):
    translate_text_request.glossaryConfig = \
      messages.TranslateTextGlossaryConfig(glossary=args.glossaryConfig)
  if args.IsSpecified('source_language'):
    translate_text_request.sourceLanguageCode = args.source_language

  translate_text_request.targetLanguageCode = args.target_language
  request.translateTextRequest = translate_text_request
  return request


def UpdateRequestGetSupportedLanguages(unused_instance_ref, args, request):
  """The hook to inject content into the getSupportedLanguages request."""
  project = properties.VALUES.core.project.GetOrFail()
  request.parent = 'projects/{}/locations/{}'.format(project, args.zone)
  if args.IsSpecified('model'):
    model = 'projects/{}/locations/{}/models/{}'.format(
        project, args.zone, args.model)
    request.model = model
  return request


def UpdateRequestBatchTranslateText(unused_instance_ref, args, request):
  """The hook to inject content into the batch translate request."""
  messages = apis.GetMessagesModule(SPEECH_API, _GetApiVersion(args))
  batch_translate_text_request = messages.BatchTranslateTextRequest()
  project = properties.VALUES.core.project.GetOrFail()
  request.parent = 'projects/{}/locations/{}'.format(project, args.zone)
  batch_translate_text_request.sourceLanguageCode = args.source_language
  batch_translate_text_request.targetLanguageCodes = args.target_language_codes
  batch_translate_text_request.outputConfig = messages.OutputConfig(
      gcsDestination=messages.GcsDestination(outputUriPrefix=args.destination))
  batch_translate_text_request.inputConfigs = \
    [messages.InputConfig(gcsSource=messages.GcsSource(inputUri=k),
                          mimeType=v if v else None)
     for k, v in sorted(args.source.items())]
  if args.IsSpecified('models'):
    batch_translate_text_request.models = \
    messages.BatchTranslateTextRequest.ModelsValue(
        additionalProperties=[
            messages.BatchTranslateTextRequest.ModelsValue.AdditionalProperty(
                key=k, value='projects/{}/locations/{}/models/{}'.format(
                    project, args.zone, v)) for k, v in sorted(args.models.items())
        ]
    )
  if args.IsSpecified('glossaries'):
    additional_properties = \
      [messages.BatchTranslateTextRequest.GlossariesValue.AdditionalProperty(
          key=k, value=messages.TranslateTextGlossaryConfig(
              glossary='projects/{}/locations/{}/glossaries/{}'.format(project, args.zone, v))) for k, v in sorted(args.glossaries.items())]
    batch_translate_text_request.glossaries = \
      messages.BatchTranslateTextRequest.GlossariesValue(
          additionalProperties=additional_properties)

  request.batchTranslateTextRequest = batch_translate_text_request
  return request
