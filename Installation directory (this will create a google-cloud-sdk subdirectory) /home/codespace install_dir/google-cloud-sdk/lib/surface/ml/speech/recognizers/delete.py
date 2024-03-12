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
"""Cloud Speech-to-text recognizers delete command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ml.speech import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml.speech import flags_v2
from googlecloudsdk.core import log


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(base.Command):
  """Delete a Speech-to-text recognizer."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags_v2.AddRecognizerArgToParser(parser)
    base.ASYNC_FLAG.AddToParser(parser)
    base.ASYNC_FLAG.SetDefault(parser, False)

  def Run(self, args):
    recognizer = args.CONCEPTS.recognizer.Parse()
    speech_client = client.SpeechV2Client()
    is_async = args.async_
    operation = speech_client.DeleteRecognizer(recognizer)

    if is_async:
      log.DeletedResource(
          operation.name, kind='speech recognizer', is_async=True)
      return operation

    resource = speech_client.WaitForRecognizerOperation(
        location=recognizer.Parent().Name(),
        operation_ref=speech_client.GetOperationRef(operation),
        message='waiting for recognizer [{}] to be deleted'.format(
            recognizer.RelativeName()))
    log.DeletedResource(resource.name, kind='speech recognizer')

    return resource
