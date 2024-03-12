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
"""Utilities for Data Catalog tags commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import tags
from googlecloudsdk.api_lib.data_catalog import tags_v1


def UpdateCreateTagRequestWithInput(unused_ref, args, request):
  del unused_ref

  client = tags.TagsClient()
  return client.ParseCreateTagArgsIntoRequest(args, request)


def UpdateCreateTagRequestWithInputV1(unused_ref, args, request):
  del unused_ref

  client = tags_v1.TagsClient()
  return client.ParseCreateTagArgsIntoRequest(args, request)


def UpdateUpdateTagRequestWithInput(unused_ref, args, request):
  del unused_ref

  client = tags.TagsClient()
  return client.ParseUpdateTagArgsIntoRequest(args, request)


def UpdateUpdateTagRequestWithInputV1(unused_ref, args, request):
  del unused_ref

  client = tags_v1.TagsClient()
  return client.ParseUpdateTagArgsIntoRequest(args, request)

