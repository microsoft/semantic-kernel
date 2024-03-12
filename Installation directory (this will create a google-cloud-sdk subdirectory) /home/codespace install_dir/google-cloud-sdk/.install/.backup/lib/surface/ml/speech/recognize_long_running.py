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
"""Recognize speech in provided audio."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.api_lib.util import waiter
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml.speech import flags
from googlecloudsdk.command_lib.ml.speech import util

# As per https://cloud.google.com/speech-to-text/docs/basics, async recognition
# accepts audios of 480 minutes in duration. Since recognition can run up to 3x
# the audio length setting timeout at that limit.
OPERATION_TIMEOUT_MS = 3 * 480 * 60 * 1000


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RecognizeLongRunningGA(base.Command):
  """Get transcripts of longer audio from an audio file."""

  detailed_help = {
      'DESCRIPTION':
          """\
Get a transcript of audio up to 80 minutes in length. If the audio is
under 60 seconds, you may also use `{parent_command} recognize` to
analyze it.
""",
      'EXAMPLES':
          """\
To block the command from completing until analysis is finished, run:

  $ {command} AUDIO_FILE --language-code=LANGUAGE_CODE --sample-rate=SAMPLE_RATE

You can also receive an operation as the result of the command by running:

  $ {command} AUDIO_FILE --language-code=LANGUAGE_CODE --sample-rate=SAMPLE_RATE --async

This will return information about an operation. To get information about the
operation, run:

  $ {parent_command} operations describe OPERATION_ID

To poll the operation until it's complete, run:

  $ {parent_command} operations wait OPERATION_ID
""",
      'API REFERENCE':
          """\
This command uses the speech/v1 API. The full documentation for this API
can be found at: https://cloud.google.com/speech-to-text/docs/quickstart-protocol
""",
  }

  API_VERSION = 'v1'
  flags_mapper = flags.RecognizeArgsToRequestMapper()

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat('json')
    cls.flags_mapper.AddRecognizeArgsToParser(parser, cls.API_VERSION)
    # LRO specific flags.
    base.ASYNC_FLAG.AddToParser(parser)
    parser.add_argument(
        '--output-uri',
        type=util.ValidateOutputUri,
        help='Location to which the results should be written. Must be a '
        'Google Cloud Storage URI.')

  def MakeRequest(self, args, messages):
    request = messages.LongRunningRecognizeRequest(
        audio=util.GetRecognitionAudioFromPath(args.audio, self.API_VERSION),
        config=self.flags_mapper.MakeRecognitionConfig(args, messages))
    if args.output_uri is not None:
      request.outputConfig = messages.TranscriptOutputConfig(
          gcsUri=args.output_uri)
    return request

  def Run(self, args):
    """Run 'ml speech recognize'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
        with.

    Returns:
      Nothing.
    """
    client = apis.GetClientInstance(util.SPEECH_API, self.API_VERSION)
    self._request = self.MakeRequest(args, client.MESSAGES_MODULE)
    operation = client.speech.Longrunningrecognize(self._request)
    if args.async_:
      return operation

    return waiter.WaitFor(
        waiter.CloudOperationPollerNoResources(client.operations, lambda x: x),
        operation.name,
        'Waiting for [{}] to complete. This may take several minutes.'.format(
            operation.name),
        wait_ceiling_ms=OPERATION_TIMEOUT_MS)

  def Epilog(self, unused_resources_were_displayed):
    util.MaybePrintSttUiLink(self._request)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RecognizeLongRunningBeta(RecognizeLongRunningGA):
  __doc__ = RecognizeLongRunningGA.__doc__

  detailed_help = RecognizeLongRunningGA.detailed_help.copy()

  API_VERSION = 'v1p1beta1'

  @classmethod
  def Args(cls, parser):
    super(RecognizeLongRunningBeta, RecognizeLongRunningBeta).Args(parser)
    cls.flags_mapper.AddBetaRecognizeArgsToParser(parser)

  def MakeRequest(self, args, messages):
    request = super(RecognizeLongRunningBeta, self).MakeRequest(args, messages)
    self.flags_mapper.UpdateBetaArgsInRecognitionConfig(args, request.config)
    return request


RecognizeLongRunningBeta.detailed_help['API REFERENCE'] = """\
This command uses the speech/v1p1beta1 API. The full documentation for this API
can be found at: https://cloud.google.com/speech-to-text/docs/quickstart-protocol
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RecognizeLongRunningAlpha(RecognizeLongRunningBeta):
  __doc__ = RecognizeLongRunningBeta.__doc__

  API_VERSION = 'v1p1beta1'

  @classmethod
  def Args(cls, parser):
    super(RecognizeLongRunningAlpha, RecognizeLongRunningAlpha).Args(parser)
    cls.flags_mapper.AddAlphaRecognizeArgsToParser(parser, cls.API_VERSION)

  def MakeRequest(self, args, messages):
    request = super(RecognizeLongRunningAlpha, self).MakeRequest(args, messages)
    self.flags_mapper.UpdateAlphaArgsInRecognitionConfig(args, request.config)
    return request
