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
"""Utils to send survey responses to clearcut's concord table."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json
import platform
import socket
import time

from googlecloudsdk.command_lib.survey import question
from googlecloudsdk.core import config
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import metrics
from googlecloudsdk.core import properties
from googlecloudsdk.core import requests
from googlecloudsdk.core.survey import survey_check
from googlecloudsdk.core.util import platforms

from six.moves import http_client as httplib

_CLEARCUT_ENDPOINT = 'https://play.googleapis.com/log'


class Error(exceptions.Error):
  """Base Error type for this module."""


class SurveyNotRecordedError(Error):
  """Errors when the survey response cannot be logged to concord."""


def _SurveyEnvironment():
  """Gets user's environment."""

  install_type = ('Google' if socket.gethostname().endswith('.google.com') else
                  'External')

  env = {
      'install_type': install_type,
      'cid': config.GetCID(),
      'user_agent': metrics.GetUserAgent(),
      'release_channel': config.INSTALLATION_CONFIG.release_channel,
      'python_version': platform.python_version(),
      'environment': properties.GetMetricsEnvironment(),
      'environment_version': properties.VALUES.metrics.environment_version.Get()
  }
  return [{'key': k, 'value': v} for k, v in env.items() if v is not None]


def _UpdateSurveyCache():
  """Records the time user answers survey."""
  with survey_check.PromptRecord() as pr:
    pr.last_answer_survey_time = time.time()


def _ConcordEventForSurvey(survey_instance):
  return {
      'event_metadata': _SurveyEnvironment(),
      'client_install_id': config.GetCID(),
      'console_type': 'CloudSDK',
      'event_type': 'hatsSurvey',
      'hats_response': _HatsResponseFromSurvey(survey_instance)
  }


def _HatsResponseFromSurvey(survey_instance):
  """Puts survey response to a HatsResponse object.

  Args:
    survey_instance: googlecloudsdk.command_lib.survey.survey.Survey, a survey
      object which contains user's response.

  Returns:
    HatsResponse as a dictionary to send to concord.
  """
  hats_metadata = {
      'site_id': 'CloudSDK',
      'site_name': 'googlecloudsdk',
      'survey_id': survey_instance.name,
  }

  multi_choice_questions = []
  rating_questions = []
  open_text_questions = []

  for i, q in enumerate(survey_instance):
    if not q.IsAnswered():
      continue
    if isinstance(q, question.MultiChoiceQuestion):
      # Remap answers from 1-5 to 5-1 because we reversed choice indexing.
      # 5 is "Very satisfied" and 1 is "Very dissatisfied", but when we send
      # answer to log, we want 1 to be "Very satisfied" and 5 to be "Very
      # dissatisfied" to be backward compatible.
      answer_int = len(q) + 1 - int(q.answer)
      multi_choice_questions.append({
          'question_number': i,
          'order_index': [answer_int],
          'answer_index': [answer_int],
          'answer_text': [q.Choice(int(q.answer))],
          'order': list(range(1, len(q)+1))
      })
    elif isinstance(q, question.RatingQuestion):
      rating_questions.append({
          'question_number': i,
          'rating': int(q.answer)
      })
    elif isinstance(q, question.FreeTextQuestion):
      open_text_questions.append({
          'question_number': i,
          'answer_text': q.answer
      })

  response = {'hats_metadata': hats_metadata}
  if multi_choice_questions:
    response['multiple_choice_response'] = multi_choice_questions
  if rating_questions:
    response['rating_response'] = rating_questions
  if open_text_questions:
    response['open_text_response'] = open_text_questions
  return response


def _ClearcutRequest(survey_instance):
  """Prepares clearcut LogRequest.

  Args:
     survey_instance: googlecloudsdk.command_lib.survey.survey.Survey, a survey
       object which contains user's response.

  Returns:
    A clearcut LogRequest object.
  """
  current_platform = platforms.Platform.Current()

  log_event = [{
      'source_extension_json':
          json.dumps(_ConcordEventForSurvey(survey_instance), sort_keys=True),
      'event_time_ms':
          metrics.GetTimeMillis()
  }]

  return {
      'client_info': {
          'client_type': 'DESKTOP',
          'desktop_client_info': {
              'os': current_platform.operating_system.id
          }
      },
      'log_source_name': 'CONCORD',
      'zwieback_cookie': config.GetCID(),
      'request_time_ms': metrics.GetTimeMillis(),
      'log_event': log_event
  }


def LogSurveyAnswers(survey_instance):
  """Sends survey response to clearcut table."""
  http_client = requests.GetSession()
  headers = {'user-agent': metrics.GetUserAgent()}
  body = json.dumps(_ClearcutRequest(survey_instance), sort_keys=True)
  response = http_client.request(
      'POST', _CLEARCUT_ENDPOINT, data=body, headers=headers)
  if response.status_code != httplib.OK:
    raise SurveyNotRecordedError(
        'We cannot record your feedback at this time, please try again later.')
  _UpdateSurveyCache()
  log.err.Print('Your response is submitted.')
