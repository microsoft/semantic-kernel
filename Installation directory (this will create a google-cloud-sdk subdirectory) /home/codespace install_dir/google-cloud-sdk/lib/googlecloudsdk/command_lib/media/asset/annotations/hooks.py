# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Request hooks for Cloud Media Asset's asset transformation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from apitools.base.py import encoding
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.media.asset import utils


def AddParentInfoToAnnotationRequests(ref, args, req):
  """Python hook for yaml commands to wildcard the parent parameter in annotation requests."""
  del ref  # Unused
  project = utils.GetProject()
  location = utils.GetLocation(args)
  req.parent = utils.GetAnnotationParentTemplate(project, location,
                                                 args.asset_type, args.asset,
                                                 args.annotation_set)
  return req


def ParseAnnotationRequest(ref, args, req):
  """Prepare the annotation for create and update requests."""
  del ref  # Unused
  messages = apis.GetMessagesModule('mediaasset', 'v1alpha')
  # In update case, request's annotation is nill
  if req.annotation is None:
    req.annotation = encoding.DictToMessage({}, messages.Annotation)
  if args.IsKnownAndSpecified('labels'):
    req.annotation.labels = encoding.DictToMessage(
        args.labels, messages.Annotation.LabelsValue)
  if args.IsKnownAndSpecified('annotation_data_file'):
    annotation_data = json.loads(args.annotation_data_file)
    req.annotation.data = encoding.DictToMessage(annotation_data,
                                                 messages.Annotation.DataValue)
  return req
