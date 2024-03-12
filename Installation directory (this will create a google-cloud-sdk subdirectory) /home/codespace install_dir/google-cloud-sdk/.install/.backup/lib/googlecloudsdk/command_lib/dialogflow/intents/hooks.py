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

"""Declarative hooks for `gcloud dialogflow intents`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding


def TrainingPhrasesType(training_phrase):
  return {
      'parts': [{'text': training_phrase}],
      'type': 'EXAMPLE'
  }


def ResponseToMessage(response):
  return {'text': {'text': [response]}}


def AddOtherPropertiesToRequest(unused_instance_ref, args, request):
  intent = encoding.MessageToDict(request.googleCloudDialogflowV2Intent)
  if args.IsSpecified('other_properties'):
    intent.update(args.other_properties)
  request.googleCloudDialogflowV2Intent = encoding.DictToMessage(
      intent, type(request.googleCloudDialogflowV2Intent))
  return request
