# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Utilities for Transcoder API Job Templates."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.transcoder import util
from googlecloudsdk.command_lib.util.args import labels_util

VERSION_MAP = {base.ReleaseTrack.GA: 'v1'}


def _GetClientInstance(release_track=base.ReleaseTrack.GA):
  api_version = VERSION_MAP.get(release_track)
  return apis.GetClientInstance('transcoder', api_version)


class TemplatesClient(object):
  """Client for template service in the Transcoder API."""

  def __init__(self, release_track=base.ReleaseTrack.GA, client=None):
    self.client = client or _GetClientInstance(release_track)
    self.message = self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_jobTemplates
    self._template_class = self.client.MESSAGES_MODULE.JobTemplate

  def Create(self, parent_ref, template_id, args):
    """Create a job template.

    Args:
      parent_ref: a Resource reference to a transcoder.projects.locations
        resource for the parent of this template.
      template_id: the ID of the resource to create.
      args: arguments to create a job template.

    Returns:
      JobTemplate: Template created
    """
    template_json = util.GetContent(args.file, args.json)
    labels = labels_util.ParseCreateArgs(args,
                                         self.message.JobTemplate.LabelsValue)
    job_template = encoding.JsonToMessage(self._template_class, template_json)
    job_template.labels = labels or job_template.labels

    req = self.message.TranscoderProjectsLocationsJobTemplatesCreateRequest(
        parent=parent_ref.RelativeName(),
        jobTemplateId=template_id,
        jobTemplate=job_template)

    return self._service.Create(req)

  def Delete(self, template_ref):
    """Delete a job template.

    Args:
      template_ref: a resource reference to a
        transcoder.projects.locations.templates resource to delete

    Returns:
      Empty: An empty response message.
    """
    req = self.message.TranscoderProjectsLocationsJobTemplatesDeleteRequest(
        name=template_ref.RelativeName())
    return self._service.Delete(req)

  def Get(self, template_ref):
    """Get a job template.

    Args:
      template_ref: a resource reference to a
        transcoder.projects.locations.templates resource to get

    Returns:
      JobTemplate: if available, return the full template information.
    """
    req = self.message.TranscoderProjectsLocationsJobTemplatesGetRequest(
        name=template_ref.RelativeName())
    return self._service.Get(req)

  def List(self, parent_ref, page_size=100):
    """List jobs templates.

    Args:
      parent_ref: a Resource reference to a transcoder.projects.locations
        resource to list templates for.
      page_size (optional): the number of job templates to fetch in each request
        (affects requests made, but not the yielded results).

    Returns:
      JobTemplates: a list of job templates in the specified location
    """
    req = self.message.TranscoderProjectsLocationsJobTemplatesListRequest(
        parent=parent_ref.RelativeName(), pageSize=page_size)
    resp = list_pager.YieldFromList(
        service=self._service,
        request=req,
        batch_size=page_size,
        field='jobTemplates',
        batch_size_attribute='pageSize')
    return resp
