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
"""Flags for speech commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.ml.speech import util
from googlecloudsdk.command_lib.util.apis import arg_utils


def GetEncodingTypeMapper(version):
  messages = apis.GetMessagesModule(util.SPEECH_API, version)
  return arg_utils.ChoiceEnumMapper(
      '--encoding',
      messages.RecognitionConfig.EncodingValueValuesEnum,
      default='encoding-unspecified',
      help_str='The type of encoding of the file. Required if the file format '
      'is not WAV or FLAC.')


class RecognizeArgsToRequestMapper:
  """Utility class to map arguments to Recognize request."""

  def __init__(self):
    self._encoding_type_mapper = None
    self._original_media_type_mapper = None
    self._interaction_type_mapper = None
    self._microphone_distance_type_mapper = None
    self._device_type_mapper = None

  def AddRecognizeArgsToParser(self, parser, api_version):
    """Add common, GA level flags for recognize commands."""
    parser.add_argument(
        'audio',
        help='The location of the audio file to transcribe. '
        'Must be a local path or a Google Cloud Storage URL '
        '(in the format gs://bucket/object).')
    language_args = parser.add_group(mutex=True, required=True)
    language_args.add_argument(
        '--language-code',
        help='The language of the supplied audio as a BCP-47 '
        '(https://www.rfc-editor.org/rfc/bcp/bcp47.txt) language tag. Example: '
        '"en-US". See https://cloud.google.com/speech/docs/languages for a list '
        'of the currently supported language codes.')
    language_args.add_argument(
        '--language',
        action=actions.DeprecationAction(
            '--language',
            warn=('The `--language` flag is deprecated. '
                  'Use the `--language-code` flag instead.')),
        hidden=True,
        help='The language of the supplied audio as a BCP-47 '
        '(https://www.rfc-editor.org/rfc/bcp/bcp47.txt) language tag. Example: '
        '"en-US". See https://cloud.google.com/speech/docs/languages for a list '
        'of the currently supported language codes.')
    self._encoding_type_mapper = GetEncodingTypeMapper(api_version)
    self._encoding_type_mapper.choice_arg.AddToParser(parser)
    parser.add_argument(
        '--sample-rate',
        type=int,
        required=False,
        help='The sample rate in Hertz. For best results, set the sampling rate '
        'of the audio source to 16000 Hz. If that\'s not possible, '
        'use the native sample rate of the audio source '
        '(instead of re-sampling).')

    audio_channel_args = parser.add_group(
        required=False, help='Audio channel settings.')
    audio_channel_args.add_argument(
        '--audio-channel-count',
        type=int,
        required=True,
        help='The number of channels in the input audio data.  Set this for '
        'separate-channel-recognition. Valid values are: '
        '1)LINEAR16 and FLAC are 1-8 '
        '2)OGG_OPUS are 1-254 '
        '3) MULAW, AMR, AMR_WB and SPEEX_WITH_HEADER_BYTE is only `1`.')
    audio_channel_args.add_argument(
        '--separate-channel-recognition',
        action='store_true',
        required=True,
        help='Recognition result will contain a `channel_tag` field to state '
        'which channel that result belongs to. If this is not true, only '
        'the first channel will be recognized.')

    parser.add_argument(
        '--model',
        choices={
            'default': (
                'audio that is not one of the specific audio models. '
                'For example, long-form audio. '
                'Ideally the audio is high-fidelity, recorded at a 16khz '
                'or greater sampling rate.'
            ),
            'command_and_search': (
                'short queries such as voice commands or voice search.'
            ),
            'latest_long': (
                'Use this model for any kind of long form content such as media'
                ' or spontaneous speech and conversations. Consider using this'
                ' model in place of the video model, especially if the video'
                ' model is not available in your target language. You can also'
                ' use this in place of the default model.'
            ),
            'latest_short': (
                'Use this model for short utterances that are a few seconds in'
                ' length. It is useful for trying to capture commands or other'
                ' single shot directed speech use cases. Consider using this'
                ' model instead of the command and search model.'
            ),
            'medical_conversation': (
                'Best for audio that originated from a conversation between a '
                'medical provider and patient.'
            ),
            'medical_dictation': (
                'Best for audio that originated from dictation notes by a'
                ' medical provider.'
            ),
            'phone_call': (
                'audio that originated from a phone call (typically recorded at'
                ' an 8khz sampling rate).'
            ),
            'phone_call_enhanced': (
                'audio that originated from a phone call (typically recorded at'
                ' an 8khz sampling rate). This is a premium model and can'
                ' produce better results but costs more than the standard rate.'
            ),
            'telephony': (
                'Improved version of the "phone_call" model, best for audio '
                'that originated from a phone call, typically recorded at an '
                '8kHz sampling rate.'
            ),
            'telephony_short': (
                'Dedicated version of the modern "telephony" model for short '
                'or even single-word utterances for audio that originated from '
                'a phone call, typically recorded at an 8kHz sampling rate.'
            ),
            'video_enhanced': (
                'audio that originated from video or includes multiple'
                ' speakers. Ideally the audio is recorded at a 16khz or greater'
                ' sampling rate. This is a premium model that costs more than'
                ' the standard rate.'
            ),
        },
        help=(
            'Select the model best suited to your domain to get best results.'
            ' If you do not explicitly specify a model, Speech-to-Text will'
            ' auto-select a model based on your other specified parameters.'
            ' Some models are premium and cost more than standard models'
            ' (although you can reduce the price by opting into'
            ' https://cloud.google.com/speech-to-text/docs/data-logging)'
        ),
    )

    parser.add_argument(
        '--max-alternatives',
        type=int,
        default=1,
        help='Maximum number of recognition hypotheses to be returned. '
        'The server may return fewer than max_alternatives. '
        'Valid values are 0-30. A value of 0 or 1 will return a maximum '
        'of one.')
    parser.add_argument(
        '--hints',
        type=arg_parsers.ArgList(),
        metavar='HINT',
        default=[],
        help='A list of strings containing word and phrase "hints" so that the '
        'speech recognition is more likely to recognize them. This can be '
        'used to improve the accuracy for specific words and phrases, '
        'for example, if specific commands are typically spoken by '
        'the user. This can also be used to add additional words to the '
        'vocabulary of the recognizer. '
        'See https://cloud.google.com/speech/limits#content.')
    parser.add_argument(
        '--include-word-time-offsets',
        action='store_true',
        default=False,
        help='If True, the top result includes a list of words with the start '
        'and end time offsets (timestamps) for those words. If False, '
        'no word-level time offset information is returned.')
    parser.add_argument(
        '--filter-profanity',
        action='store_true',
        default=False,
        help='If True, the server will attempt to filter out profanities, '
        'replacing all but the initial character in each filtered word with '
        'asterisks, e.g. ```f***```.')
    parser.add_argument(
        '--enable-automatic-punctuation',
        action='store_true',
        help='Adds punctuation to recognition result hypotheses.')

  def MakeRecognitionConfig(self, args, messages):
    """Make RecognitionConfig message from given arguments."""
    config = messages.RecognitionConfig(
        languageCode=args.language_code
        if args.language_code else args.language,
        encoding=self._encoding_type_mapper.GetEnumForChoice(
            args.encoding.replace('_', '-').lower()),
        sampleRateHertz=args.sample_rate,
        audioChannelCount=args.audio_channel_count,
        maxAlternatives=args.max_alternatives,
        enableWordTimeOffsets=args.include_word_time_offsets,
        enableSeparateRecognitionPerChannel=args.separate_channel_recognition,
        profanityFilter=args.filter_profanity,
        speechContexts=[messages.SpeechContext(phrases=args.hints)])
    if args.enable_automatic_punctuation:
      config.enableAutomaticPunctuation = args.enable_automatic_punctuation
    if args.model is not None:
      if args.model in [
          'default',
          'command_and_search',
          'phone_call',
          'latest_long',
          'latest_short',
          'medical_conversation',
          'medical_dictation',
          'telephony',
          'telephony_short',
      ]:
        config.model = args.model
      elif args.model == 'phone_call_enhanced':
        config.model = 'phone_call'
        config.useEnhanced = True
      elif args.model == 'video_enhanced':
        config.model = 'video'
        config.useEnhanced = True
    return config

  def AddBetaRecognizeArgsToParser(self, parser):
    """Add beta arguments."""
    parser.add_argument(
        '--additional-language-codes',
        type=arg_parsers.ArgList(),
        default=[],
        metavar='LANGUAGE_CODE',
        help="""\
The BCP-47 language tags of other languages that the speech may be in.
Up to 3 can be provided.

If alternative languages are listed, recognition result will contain recognition
in the most likely language detected including the main language-code.""")

    speaker_args = parser.add_group(required=False)
    speaker_args.add_argument(
        '--diarization-speaker-count',
        type=int,
        hidden=True,
        action=actions.DeprecationAction(
            '--diarization-speaker-count',
            warn=('The `--diarization-speaker-count` flag is deprecated. '
                  'Use the `--min-diarization-speaker-count` and/or '
                  '`--max-diarization-speaker-count` flag instead.')),
        help='Estimated number of speakers in the conversation '
        'being recognized.')
    speaker_args.add_argument(
        '--min-diarization-speaker-count',
        type=int,
        help='Minimum estimated number of speakers in the conversation '
        'being recognized.')
    speaker_args.add_argument(
        '--max-diarization-speaker-count',
        type=int,
        help='Maximum estimated number of speakers in the conversation '
        'being recognized.')
    speaker_args.add_argument(
        '--enable-speaker-diarization',
        action='store_true',
        required=True,
        help='Enable speaker detection for each recognized word in the top '
        'alternative of the recognition result using an integer '
        'speaker_tag provided in the WordInfo.')

    parser.add_argument(
        '--include-word-confidence',
        action='store_true',
        help='Include a list of words and the confidence for those words in '
        'the top result.')

  def UpdateBetaArgsInRecognitionConfig(self, args, config):
    """Updates config from command line arguments."""
    config.alternativeLanguageCodes = args.additional_language_codes
    # If any of diarization flags are used enable diarization.
    if (args.enable_speaker_diarization or args.min_diarization_speaker_count or
        args.max_diarization_speaker_count or args.diarization_speaker_count):
      speaker_config = config.diarizationConfig = config.field_by_name(
          'diarizationConfig').message_type(enableSpeakerDiarization=True)
      if args.min_diarization_speaker_count:
        speaker_config.minSpeakerCount = args.min_diarization_speaker_count
      if args.max_diarization_speaker_count:
        speaker_config.maxSpeakerCount = args.max_diarization_speaker_count
      # Only use legacy flag if min/max fields were not used.
      if args.diarization_speaker_count:
        if (args.min_diarization_speaker_count or
            args.max_diarization_speaker_count):
          raise exceptions.InvalidArgumentException(
              '--diarization-speaker-count',
              'deprecated flag cannot be used with '
              '--max/min_diarization_speaker_count flags')
        speaker_config.minSpeakerCount = args.diarization_speaker_count
        speaker_config.maxSpeakerCount = args.diarization_speaker_count

    config.enableWordConfidence = args.include_word_confidence

  def AddAlphaRecognizeArgsToParser(self, parser, api_version):
    """Add alpha arguments."""
    meta_args = parser.add_group(
        required=False,
        help='Description of audio data to be recognized. '
        'Note that the Google Cloud Speech-to-text-api does not use this '
        'information, and only passes it through back into response.')
    meta_args.add_argument(
        '--naics-code',
        action=MakeDeprecatedRecgonitionFlagAction('naics-code'),
        type=int,
        help='The industry vertical to which this speech recognition request '
        'most closely applies.')
    self._original_media_type_mapper = GetOriginalMediaTypeMapper(api_version)
    self._original_media_type_mapper.choice_arg.AddToParser(meta_args)
    self._interaction_type_mapper = GetInteractionTypeMapper(api_version)
    self._interaction_type_mapper.choice_arg.AddToParser(meta_args)
    self._microphone_distance_type_mapper = GetMicrophoneDistanceTypeMapper(
        api_version)
    self._microphone_distance_type_mapper.choice_arg.AddToParser(meta_args)
    self._device_type_mapper = GetRecordingDeviceTypeMapper(api_version)
    self._device_type_mapper.choice_arg.AddToParser(meta_args)
    meta_args.add_argument(
        '--recording-device-name',
        action=MakeDeprecatedRecgonitionFlagAction('recording-device-name'),
        help='The device used to make the recording.  Examples: `Nexus 5X`, '
        '`Polycom SoundStation IP 6000`')
    meta_args.add_argument(
        '--original-mime-type',
        action=MakeDeprecatedRecgonitionFlagAction('original-mime-type'),
        help='Mime type of the original audio file. Examples: `audio/m4a`, '
        ' `audio/mp3`.')
    meta_args.add_argument(
        '--audio-topic',
        action=MakeDeprecatedRecgonitionFlagAction('audio-topic'),
        help='Description of the content, e.g. "Recordings of federal supreme '
        'court hearings from 2012".')

  def UpdateAlphaArgsInRecognitionConfig(self, args, config):
    """Update RecognitionConfig with args."""
    if (args.interaction_type is not None or
        args.original_media_type is not None or args.naics_code is not None or
        args.microphone_distance is not None or
        args.recording_device_type is not None or
        args.recording_device_name is not None or
        args.original_mime_type is not None or args.audio_topic is not None):
      if config.metadata is None:
        config.metadata = config.field_by_name('metadata').message_type()
      config.metadata.interactionType = (
          self._interaction_type_mapper.GetEnumForChoice(args.interaction_type))
      config.metadata.originalMediaType = (
          self._original_media_type_mapper.GetEnumForChoice(
              args.original_media_type))
      config.metadata.industryNaicsCodeOfAudio = args.naics_code
      config.metadata.microphoneDistance = (
          self._microphone_distance_type_mapper.GetEnumForChoice(
              args.microphone_distance))
      config.metadata.recordingDeviceType = (
          self._device_type_mapper.GetEnumForChoice(args.recording_device_type))
      config.metadata.recordingDeviceName = args.recording_device_name
      config.metadata.originalMimeType = args.original_mime_type
      config.metadata.audioTopic = args.audio_topic


def MakeDeprecatedRecgonitionFlagAction(flag_name):
  return actions.DeprecationAction(
      '--' + flag_name,
      warn='The `{}` flag is deprecated and will be removed. '
      'The Google Cloud Speech-to-text api does not use it, and only '
      'passes it through back into response.'.format(flag_name))


def GetRecordingDeviceTypeMapper(version):
  messages = apis.GetMessagesModule(util.SPEECH_API, version)
  return arg_utils.ChoiceEnumMapper(
      '--recording-device-type',
      messages.RecognitionMetadata.RecordingDeviceTypeValueValuesEnum,
      action=MakeDeprecatedRecgonitionFlagAction('recording-device-type'),
      custom_mappings={
          'SMARTPHONE': ('smartphone', 'Speech was recorded on a smartphone.'),
          'PC': ('pc',
                 'Speech was recorded using a personal computer or tablet.'),
          'PHONE_LINE':
              ('phone-line', 'Speech was recorded over a phone line.'),
          'VEHICLE': ('vehicle', 'Speech was recorded in a vehicle.'),
          'OTHER_OUTDOOR_DEVICE': ('outdoor', 'Speech was recorded outdoors.'),
          'OTHER_INDOOR_DEVICE': ('indoor', 'Speech was recorded indoors.')
      },
      help_str='The device type through which the original audio was '
      'recorded on.',
      include_filter=lambda x: not x.endswith('UNSPECIFIED'))


def GetMicrophoneDistanceTypeMapper(version):
  messages = apis.GetMessagesModule(util.SPEECH_API, version)
  return arg_utils.ChoiceEnumMapper(
      '--microphone-distance',
      messages.RecognitionMetadata.MicrophoneDistanceValueValuesEnum,
      action=MakeDeprecatedRecgonitionFlagAction('microphone-distance'),
      custom_mappings={
          'NEARFIELD': ('nearfield', """\
The audio was captured from a microphone close to the speaker, generally within
 1 meter. Examples include a phone, dictaphone, or handheld microphone."""),
          'MIDFIELD':
              ('midfield', 'The speaker is within 3 meters of the microphone.'),
          'FARFIELD':
              ('farfield',
               'The speaker is more than 3 meters away from the microphone.'),
      },
      help_str='The distance at which the audio device is placed to record '
      'the conversation.',
      include_filter=lambda x: not x.endswith('UNSPECIFIED'))


def GetInteractionTypeMapper(version):
  messages = apis.GetMessagesModule(util.SPEECH_API, version)
  return arg_utils.ChoiceEnumMapper(
      '--interaction-type',
      messages.RecognitionMetadata.InteractionTypeValueValuesEnum,
      action=MakeDeprecatedRecgonitionFlagAction('interaction-type'),
      custom_mappings={
          'DICTATION': (
              'dictation',
              'Transcribe speech to text to create a written document, such as '
              + 'a text-message, email or report.'),
          'DISCUSSION': ('discussion',
                         'Multiple people in a conversation or discussion.'),
          'PRESENTATION': ('presentation',
                           'One or more persons lecturing or presenting to ' +
                           'others, mostly uninterrupted.'),
          'PHONE_CALL': (
              'phone-call',
              'A phone-call or video-conference in which two or more people, ' +
              'who are not in the same room, are actively participating.'),
          'PROFESSIONALLY_PRODUCED':
              ('professionally-produced',
               'Professionally produced audio (eg. TV Show, Podcast).'),
          'VOICE_COMMAND':
              ('voice-command',
               'Transcribe voice commands, such as for controlling a device.'),
          'VOICE_SEARCH':
              ('voice-search',
               'Transcribe spoken questions and queries into text.'),
          'VOICEMAIL':
              ('voicemail',
               'A recorded message intended for another person to listen to.'),
      },
      help_str='Determining the interaction type in the conversation.',
      include_filter=lambda x: not x.endswith('UNSPECIFIED'))


def GetOriginalMediaTypeMapper(version):
  messages = apis.GetMessagesModule(util.SPEECH_API, version)
  return arg_utils.ChoiceEnumMapper(
      '--original-media-type',
      messages.RecognitionMetadata.OriginalMediaTypeValueValuesEnum,
      action=MakeDeprecatedRecgonitionFlagAction('original-media-type'),
      custom_mappings={
          'AUDIO': ('audio', 'The speech data is an audio recording.'),
          'VIDEO': ('video', 'The speech data originally recorded on a video.'),
      },
      help_str='The media type of the original audio conversation.',
      include_filter=lambda x: not x.endswith('UNSPECIFIED'))
