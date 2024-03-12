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
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ml.speech import flags
from googlecloudsdk.command_lib.ml.speech import util


@base.ReleaseTracks(base.ReleaseTrack.GA)
class RecognizeGA(base.Command):
  """Get transcripts of short (less than 60 seconds) audio from an audio file."""

  detailed_help = {
      'DESCRIPTION':
          """\
Get a transcript of an audio file that is less than 60 seconds. You can use
an audio file that is on your local drive or a Google Cloud Storage URL.

If the audio is longer than 60 seconds, you will get an error. Please use
`{parent_command} recognize-long-running` instead.
""",
      'EXAMPLES':
          """\
To get a transcript of an audio file 'my-recording.wav':

    $ {command} 'my-recording.wav' --language-code=en-US

To get a transcript of an audio file in bucket 'gs://bucket/myaudio' with a
custom sampling rate and encoding that uses hints and filters profanity:

    $ {command} 'gs://bucket/myaudio' \\
        --language-code=es-ES --sample-rate=2200 --hints=Bueno \\
        --encoding=OGG_OPUS --filter-profanity
""",
      'API REFERENCE':
          """\
This command uses the speech/v1 API. The full documentation for this API
can be found at: https://cloud.google.com/speech-to-text/docs/quickstart-protocol
"""
  }

  API_VERSION = 'v1'
  flags_mapper = flags.RecognizeArgsToRequestMapper()

  @classmethod
  def Args(cls, parser):
    parser.display_info.AddFormat('json')
    cls.flags_mapper.AddRecognizeArgsToParser(parser, cls.API_VERSION)

  def MakeRequest(self, args, messages):
    return messages.RecognizeRequest(
        audio=util.GetRecognitionAudioFromPath(args.audio, self.API_VERSION),
        config=self.flags_mapper.MakeRecognitionConfig(args, messages))

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
    return client.speech.Recognize(self._request)

  def Epilog(self, unused_resources_were_displayed):
    util.MaybePrintSttUiLink(self._request)


@base.ReleaseTracks(base.ReleaseTrack.BETA)
class RecognizeBeta(RecognizeGA):
  __doc__ = RecognizeGA.__doc__

  detailed_help = RecognizeGA.detailed_help.copy()
  API_VERSION = 'v1p1beta1'

  @classmethod
  def Args(cls, parser):
    super(RecognizeBeta, RecognizeBeta).Args(parser)
    cls.flags_mapper.AddBetaRecognizeArgsToParser(parser)

  def MakeRequest(self, args, messages):
    request = super(RecognizeBeta, self).MakeRequest(args, messages)
    self.flags_mapper.UpdateBetaArgsInRecognitionConfig(args, request.config)
    return request


RecognizeBeta.detailed_help['API REFERENCE'] = """\
This command uses the speech/v1p1beta1 API. The full documentation for this API
can be found at: https://cloud.google.com/speech-to-text/docs/quickstart-protocol
"""


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class RecognizeAlpha(RecognizeBeta):
  __doc__ = RecognizeBeta.__doc__

  API_VERSION = 'v1p1beta1'

  @classmethod
  def Args(cls, parser):
    super(RecognizeAlpha, RecognizeAlpha).Args(parser)
    cls.flags_mapper.AddAlphaRecognizeArgsToParser(parser, cls.API_VERSION)

  def MakeRequest(self, args, messages):
    request = super(RecognizeAlpha, self).MakeRequest(args, messages)
    self.flags_mapper.UpdateAlphaArgsInRecognitionConfig(args, request.config)
    return request
