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
"""Base class for gkemulticloud API clients."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import itertools

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.container.gkemulticloud import util
from googlecloudsdk.command_lib.container.gkemulticloud import flags


class ClientBase(object):
  """Base class for gkemulticloud API clients."""

  def __init__(self, service=None, list_result_field=None):
    self._client = util.GetClientInstance()
    self._messages = util.GetMessagesModule()
    self._service = service
    self._list_result_field = list_result_field

  def _Fleet(self, args):
    kwargs = {
        'project': flags.GetFleetProject(args),
    }
    return (
        self._messages.GoogleCloudGkemulticloudV1Fleet(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _MaxPodsConstraint(self, args):
    kwargs = {'maxPodsPerNode': flags.GetMaxPodsPerNode(args)}
    return (
        self._messages.GoogleCloudGkemulticloudV1MaxPodsConstraint(**kwargs)
        if any(kwargs.values())
        else None
    )

  def _Labels(self, args, parent_type):
    labels = flags.GetNodeLabels(args)
    if not labels:
      return None
    label_type = parent_type.LabelsValue.AdditionalProperty
    return parent_type.LabelsValue(
        additionalProperties=[
            label_type(key=k, value=v) for k, v in labels.items()
        ]
    )

  def _Tags(self, args, parent_type):
    tags = flags.GetTags(args)
    if not tags:
      return None
    tag_type = parent_type.TagsValue.AdditionalProperty
    return parent_type.TagsValue(
        additionalProperties=[tag_type(key=k, value=v) for k, v in tags.items()]
    )

  def _Annotations(self, args, parent_type):
    """Parses the annotations from the args.

    Args:
      args: Arguments to be parsed.
      parent_type: Type of the parent object.

    Returns:
      Returns the parsed annotations.
    """
    annotations = flags.GetAnnotations(args)
    if not annotations:
      return None
    annotation_type = parent_type.AnnotationsValue.AdditionalProperty
    return parent_type.AnnotationsValue(
        additionalProperties=[
            annotation_type(key=k, value=v) for k, v in annotations.items()
        ]
    )

  def _BinaryAuthorization(self, args):
    evaluation_mode = flags.GetBinauthzEvaluationMode(args)
    if not evaluation_mode:
      return None
    return self._messages.GoogleCloudGkemulticloudV1BinaryAuthorization(
        evaluationMode=evaluation_mode
    )

  def List(self, parent_ref, page_size=None, limit=None, parent_field='parent'):
    """Lists gkemulticloud API resources.

    Args:
      parent_ref: Reference to the parent field to list resources.
      page_size: Page size for listing resources.
      limit: Limit for listing resources.
      parent_field: Name of the parent field.

    Returns:
      iterator: List of resources returned from the server.
      bool: True if empty. False, otherwise.
    """
    kwargs = {parent_field: parent_ref.RelativeName()}
    req = self._service.GetRequestType('List')(**kwargs)
    kwargs = {
        'field': self._list_result_field,
        'batch_size_attribute': 'pageSize',
    }
    if limit:
      kwargs['limit'] = limit
    if page_size:
      kwargs['batch_size'] = page_size
    items = list_pager.YieldFromList(self._service, req, **kwargs)
    try:
      first_item = next(items)
      items = itertools.chain([first_item], items)
      return items, False
    except StopIteration:
      return items, True

  def Get(self, resource_ref):
    """Gets a gkemulticloud API resource."""
    req = self._service.GetRequestType('Get')(name=resource_ref.RelativeName())
    return self._service.Get(req)

  def Delete(
      self,
      resource_ref,
      validate_only=None,
      allow_missing=None,
      ignore_errors=None,
  ):
    """Deletes a gkemulticloud API resource."""
    req = self._service.GetRequestType('Delete')(
        name=resource_ref.RelativeName()
    )
    if validate_only:
      req.validateOnly = True
    if allow_missing:
      req.allowMissing = True
    if ignore_errors:
      req.ignoreErrors = True
    return self._service.Delete(req)

  def HasNodePools(self, cluster_ref):
    """Checks if the cluster has a node pool."""
    req = self._service.GetRequestType('List')(
        parent=cluster_ref.RelativeName(), pageSize=1
    )
    res = self._service.List(req)
    node_pools = getattr(res, self._list_result_field, None)
    return True if node_pools else False
