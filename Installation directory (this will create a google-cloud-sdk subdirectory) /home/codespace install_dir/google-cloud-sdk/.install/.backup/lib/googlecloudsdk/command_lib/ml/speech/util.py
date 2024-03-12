# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Wrapper for interacting with speech API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.storage import storage_util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.util import files

from six.moves import urllib


SPEECH_API = 'speech'
SPEECH_API_VERSION = 'v1'


OUTPUT_ERROR_MESSAGE = ('[{}] is not a valid format for result output. Must be '
                        'a Google Cloud Storage URI '
                        '(format: gs://bucket/file).')


class Error(exceptions.Error):
  """Exceptions for this module."""


class AudioException(Error):
  """Raised if audio is not found."""


class UriFormatError(Error):
  """Error if the specified URI is invalid."""


def GetRecognitionAudioFromPath(path, version):
  """Determine whether path to audio is local, set RecognitionAudio message."""
  messages = apis.GetMessagesModule(SPEECH_API, version)
  audio = messages.RecognitionAudio()

  if os.path.isfile(path):
    audio.content = files.ReadBinaryFileContents(path)
  elif storage_util.ObjectReference.IsStorageUrl(path):
    audio.uri = path
  else:
    raise AudioException(
        'Invalid audio source [{}]. The source must either be a local path '
        'or a Google Cloud Storage URL (such as gs://bucket/object).'.format(
            path))
  return audio


def GetAudioHook(version=SPEECH_API_VERSION):
  """Returns a hook to get the RecognitionAudio message for an API version."""
  def GetAudioFromPath(path):
    """Determine whether path to audio is local, build RecognitionAudio message.

    Args:
      path: str, the path to the audio.

    Raises:
      AudioException: If audio is not found locally and does not appear to be
        Google Cloud Storage URL.

    Returns:
      speech_v1_messages.RecognitionAudio, the audio message.
    """
    return GetRecognitionAudioFromPath(path, version)
  return GetAudioFromPath


def ValidateOutputUri(output_uri):
  """Validates given output URI against validator function.

  Args:
    output_uri: str, the output URI for the analysis.

  Raises:
    UriFormatError: if the URI is not valid.

  Returns:
    str, The same output_uri.
  """
  if output_uri and not storage_util.ObjectReference.IsStorageUrl(output_uri):
    raise UriFormatError(OUTPUT_ERROR_MESSAGE.format(output_uri))
  return output_uri


def MaybePrintSttUiLink(request):
  """Print Url to the Speech-to-text UI console for given recognize request."""
  if (console_io.IsRunFromShellScript() or
      properties.VALUES.core.disable_prompts.GetBool()):
    return
  audio_uri = request.audio.uri
  if not audio_uri:
    return
  payload = {
      'audio':
          urllib.parse.quote_plus(
              audio_uri[5:] if audio_uri.startswith('gs://') else audio_uri),
      'encoding':
          request.config.encoding,
      'model':
          request.config.model,
      'locale':
          request.config.languageCode,
      'sampling':
          request.config.sampleRateHertz,
      'channels':
          request.config.audioChannelCount,
      'enhanced':
          request.config.useEnhanced,
  }

  params = ';'.join('{}={}'.format(key, value)
                    for (key, value) in sorted(payload.items())
                    if value and ('unspecified' not in str(value).lower()))
  url_tuple = ('https', 'console.cloud.google.com',
               '/speech/transcriptions/create', params, '', '')
  target_url = urllib.parse.urlunparse(url_tuple)
  log.status.Print(
      'Try this using the Speech-to-Text UI at {}'.format(target_url))
