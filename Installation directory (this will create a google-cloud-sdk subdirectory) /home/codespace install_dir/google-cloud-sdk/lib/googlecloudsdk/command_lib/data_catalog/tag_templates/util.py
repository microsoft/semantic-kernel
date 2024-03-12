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
"""Utilities for Data Catalog tag-templates commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.data_catalog import tag_templates
from googlecloudsdk.api_lib.data_catalog import tag_templates_v1


def UpdateCreateTagTemplateRequestWithInput(unused_ref, args, request):
  """Hook for updating request with flags for tag-templates create."""
  del unused_ref
  client = tag_templates.TagTemplatesClient()
  return client.ParseCreateTagTemplateArgsIntoRequest(args, request)


def UpdateCreateTagTemplateRequestWithInputV1(unused_ref, args, request):
  """Hook for updating request with flags for tag-templates create."""
  del unused_ref
  client = tag_templates_v1.TagTemplatesClient()
  return client.ParseCreateTagTemplateArgsIntoRequest(args, request)


def UpdateCreateTagTemplateFieldRequestWithInput(unused_ref, args, request):
  """Hook for updating request with flags for tag-templates fields create."""
  del unused_ref
  client = tag_templates.TagTemplatesClient()
  return client.ParseCreateTagTemplateFieldArgsIntoRequest(args, request)


def UpdateCreateTagTemplateFieldRequestWithInputV1(unused_ref, args, request):
  """Hook for updating request with flags for tag-templates fields create."""
  del unused_ref
  client = tag_templates_v1.TagTemplatesClient()
  return client.ParseCreateTagTemplateFieldArgsIntoRequest(args, request)


def UpdateUpdateTagTemplateFieldRequestWithInput(unused_ref, args, request):
  """Hook for updating request with flags for tag-templates fields update."""
  del unused_ref
  update_mask = []
  if args.IsSpecified('display_name'):
    update_mask.append('display_name')
  if args.IsSpecified('enum_values'):
    update_mask.append('type.enum_type')
  if args.IsSpecified('required'):
    update_mask.append('is_required')
  request.updateMask = ','.join(update_mask)

  client = tag_templates.TagTemplatesClient()
  return client.ParseUpdateTagTemplateFieldArgsIntoRequest(args, request)


def UpdateUpdateTagTemplateFieldRequestWithInputV1(unused_ref, args, request):
  """Hook for updating request with flags for tag-templates fields update."""
  del unused_ref
  update_mask = []
  if args.IsSpecified('display_name'):
    update_mask.append('display_name')
  if args.IsSpecified('enum_values'):
    update_mask.append('type.enum_type')
  if args.IsSpecified('required'):
    update_mask.append('is_required')
  request.updateMask = ','.join(update_mask)

  client = tag_templates_v1.TagTemplatesClient()
  return client.ParseUpdateTagTemplateFieldArgsIntoRequest(args, request)

