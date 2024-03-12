# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Cloud Speech-to-text recognizers update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml.speech import client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ml.speech import flags_v2
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.Command):
  """Update a Speech-to-text recognizer."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags_v2.AddAllFlagsToParser(parser)

  def Run(self, args):
    recognizer = args.CONCEPTS.recognizer.Parse()

    # TODO(b/272527653) Change errors to Actionable Error response type.
    if args.location not in client.PUBLIC_ALLOWED_LOCATIONS:
      raise exceptions.InvalidArgumentException(
          '--location',
          '[--location] must be set to one of '
          + ', '.join(client.PUBLIC_ALLOWED_LOCATIONS)
          + '.',
      )

    speech_client = client.SpeechV2Client()
    is_async = args.async_

    if (
        args.encoding is not None
        and args.encoding not in client.ENCODING_OPTIONS
    ):
      raise exceptions.InvalidArgumentException(
          '--encoding',
          '[--encoding] must be set to LINEAR16, MULAW, ALAW, or AUTO.',
      )

    operation = speech_client.UpdateRecognizer(
        recognizer,
        args.display_name,
        args.model,
        args.language_codes,
        args.profanity_filter,
        args.enable_word_time_offsets,
        args.enable_word_confidence,
        args.enable_automatic_punctuation,
        args.enable_spoken_punctuation,
        args.enable_spoken_emojis,
        args.min_speaker_count,
        args.max_speaker_count,
        args.encoding,
        args.sample_rate,
        args.audio_channel_count,
    )

    if is_async:
      log.UpdatedResource(
          operation.name, kind='speech recognizer', is_async=True)
      return operation

    resource = speech_client.WaitForRecognizerOperation(
        location=recognizer.Parent().Name(),
        operation_ref=speech_client.GetOperationRef(operation),
        message='waiting for recognizer [{}] to be updated'.format(
            recognizer.RelativeName()))
    log.UpdatedResource(resource.name, kind='speech recognizer')

    return resource
