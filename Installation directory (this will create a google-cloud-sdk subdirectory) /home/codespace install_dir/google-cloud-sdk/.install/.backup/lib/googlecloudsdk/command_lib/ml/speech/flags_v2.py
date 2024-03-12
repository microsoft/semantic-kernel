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

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.command_lib.util.apis import yaml_data
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs


def AddRecognizerArgToParser(parser):
  """Sets up an argument for the recognizer resource."""
  resource_data = yaml_data.ResourceYAMLData.FromPath('ml.speech.recognizer')
  resource_spec = concepts.ResourceSpec.FromYaml(
      resource_data.GetData(), api_version='v2')
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='recognizer',
      concept_spec=resource_spec,
      required=True,
      group_help='recognizer.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLocationArgToParser(parser):
  """Parses location flag."""
  location_data = yaml_data.ResourceYAMLData.FromPath('ml.speech.location')
  resource_spec = concepts.ResourceSpec.FromYaml(location_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='--location',
      concept_spec=resource_spec,
      required=True,
      group_help='location.')
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddLocationPositionalArgToParser(parser):
  """Parses location when there is no flag."""
  location_data = yaml_data.ResourceYAMLData.FromPath('ml.speech.location')
  resource_spec = concepts.ResourceSpec.FromYaml(location_data.GetData())
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='location',
      concept_spec=resource_spec,
      required=True,
      group_help='location.',
  )
  return concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)


def AddAllFlagsToParser(parser, create=False):
  """Parses all flags for v2 STT API."""
  AddRecognizerArgToParser(parser)
  base.ASYNC_FLAG.AddToParser(parser)
  base.ASYNC_FLAG.SetDefault(parser, False)
  parser.add_argument(
      '--display-name',
      help="""\
      Name of this recognizer as it appears in UIs.
      """)
  parser.add_argument(
      '--model',
      required=create,
      help="""\
      `latest_long` or `latest_short`
      """)
  parser.add_argument(
      '--language-codes',
      metavar='LANGUAGE_CODE',
      required=create,
      type=arg_parsers.ArgList(),
      help="""\
      Language code is one of `en-US`, `en-GB`, `fr-FR`.
      Check [documentation](https://cloud.google.com/speech-to-text/docs/multiple-languages)
      for using more than one language code.
      """)
  parser.add_argument(
      '--profanity-filter',
      type=arg_parsers.ArgBoolean(),
      help="""\
      If true, the server will censor profanities.
      """)
  parser.add_argument(
      '--enable-word-time-offsets',
      type=arg_parsers.ArgBoolean(),
      help="""\
      If true, the top result includes a list of words and their timestamps.
      """)
  parser.add_argument(
      '--enable-word-confidence',
      type=arg_parsers.ArgBoolean(),
      help="""\
      If true, the top result includes a list of words and the confidence for
      those words.
      """)
  parser.add_argument(
      '--enable-automatic-punctuation',
      type=arg_parsers.ArgBoolean(),
      help="""\
      If true, adds punctuation to recognition result hypotheses.
      """)
  parser.add_argument(
      '--enable-spoken-punctuation',
      type=arg_parsers.ArgBoolean(),
      help="""\
      If true, replaces spoken punctuation with the corresponding symbols in the request.
      """)
  parser.add_argument(
      '--enable-spoken-emojis',
      type=arg_parsers.ArgBoolean(),
      help="""\
      If true, adds spoken emoji formatting.
      """)
  parser.add_argument(
      '--min-speaker-count',
      type=arg_parsers.BoundedInt(1, 6),
      help="""\
        Minimum number of speakers in the conversation.
        """)
  parser.add_argument(
      '--max-speaker-count',
      type=arg_parsers.BoundedInt(1, 6),
      help="""\
        Maximum number of speakers in the conversation.
        """)
  parser.add_argument(
      '--encoding',
      help="""\
          Encoding format of the provided audio. For headerless formats, must be set to `LINEAR16`, `MULAW,` or `ALAW`. For other formats, set to `AUTO`.
          """,
  )
  parser.add_argument(
      '--sample-rate',
      type=arg_parsers.BoundedInt(8000, 48000),
      help="""\
          Sample rate in Hertz of the audio data sent for recognition.
          Required if using explicit decoding.
          """,
  )
  parser.add_argument(
      '--audio-channel-count',
      type=arg_parsers.BoundedInt(1, 8),
      help="""\
          Number of channels present in the audio data sent for recognition.
          Supported for LINEAR16, MULAW, ALAW.
          """,
  )
