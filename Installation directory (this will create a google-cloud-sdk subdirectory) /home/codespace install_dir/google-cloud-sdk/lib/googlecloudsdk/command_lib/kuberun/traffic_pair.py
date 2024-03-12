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
"""Traffic representation for printing."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import operator

from googlecloudsdk.api_lib.kuberun import service
from googlecloudsdk.api_lib.kuberun import traffic

import six

# Human readable indicator for a missing traffic percentage or missing tags.
_MISSING_PERCENT_OR_TAGS = '-'

# String to join TrafficTarget tags referencing the same revision.
_TAGS_JOIN_STRING = ', '


def _FormatPercentage(percent):
  if percent == _MISSING_PERCENT_OR_TAGS:
    return _MISSING_PERCENT_OR_TAGS
  else:
    return '{}%'.format(percent)


def _SumPercent(targets):
  """Sums the percents of the given targets."""
  return sum(t.percent for t in targets if t.percent)


def SortKeyFromTarget(target):
  """Sorted key function to order TrafficTarget objects by key.

  TrafficTargets keys are one of:
  o revisionName
  o LATEST_REVISION_KEY

  Note LATEST_REVISION_KEY is not a str so its ordering with respect
  to revisionName keys is hard to predict.

  Args:
    target: A TrafficTarget.

  Returns:
    A value that sorts by revisionName with LATEST_REVISION_KEY
    last.
  """
  key = traffic.GetKey(target)
  if key == traffic.LATEST_REVISION_KEY:
    result = (2, key)
  else:
    result = (1, key)
  return result


class TrafficTag(object):
  """Contains the spec and status state for a traffic tag.

  Attributes:
    tag: The name of the tag.
    url: The tag's URL, or an empty string if the tag does not have a URL
      assigned yet. Defaults to an empty string.
    inSpec: Boolean that is true if the tag is present in the spec. Defaults to
      False.
    inStatus: Boolean that is true if the tag is present in the status. Defaults
      to False.
  """

  def __init__(self, tag, url='', in_spec=False, in_status=False):
    """Returns a new TrafficTag.

    Args:
      tag: The name of the tag.
      url: The tag's URL.
      in_spec: Boolean that is true if the tag is present in the spec.
      in_status: Boolean that is true if the tag is present in the status.
    """
    self.tag = tag
    self.url = url
    self.inSpec = in_spec  # pylint: disable=invalid-name
    self.inStatus = in_status  # pylint: disable=invalid-name


class TrafficTargetPair(object):
  """Holder for TrafficTarget status information.

  The representation of the status of traffic for a service
  includes:
    o User requested assignments (spec.traffic)
    o Actual assignments (status.traffic)

  Each of spec.traffic and status.traffic may contain multiple traffic targets
  that reference the same revision, either directly by name or indirectly by
  referencing the latest ready revision.

  The spec and status traffic targets for a revision may differ after a failed
  traffic update or during a successful one. A TrafficTargetPair holds all
  spec and status TrafficTargets that reference the same revision by name or
  reference the latest ready revision. Both the spec and status traffic targets
  can be empty.

  The latest revision can be included in the spec traffic targets
  two ways
    o by revisionName
    o by setting latestRevision to True.

  Attributes:
    key: Either the referenced revision name or 'LATEST' if the traffic targets
      reference the latest ready revision.
    latestRevision: Boolean indicating if the traffic targets reference the
      latest ready revision.
    revisionName: The name of the revision referenced by these traffic targets.
    specPercent: The percent of traffic allocated to the referenced revision in
      the service's spec.
    statusPercent: The percent of traffic allocated to the referenced revision
      in the service's status.
    specTags: Tags assigned to the referenced revision in the service's spec as
      a comma and space separated string.
    statusTags: Tags assigned to the referenced revision in the service's status
      as a comma and space separated string.
    urls: A list of urls that directly address the referenced revision.
    tags: A list of TrafficTag objects containing both the spec and status state
      for each traffic tag.
    displayPercent: Human-readable representation of the current percent
      assigned to the referenced revision.
    displayRevisionId: Human-readable representation of the name of the
      referenced revision.
    displayTags: Human-readable representation of the current tags assigned to
      the referenced revision.
    serviceUrl: The main URL for the service.
  """

  # This class has lower camel case public attribute names to implement our
  # desired style for json and yaml property names in structured output.
  #
  # This class gets passed to gcloud's printer to produce the output of
  # `gcloud run services update-traffic`. When users specify --format=yaml or
  # --format=json, the public attributes of this class get automatically
  # converted to fields in the resulting json or yaml output, with names
  # determined by this class's attribute names. We want the json and yaml output
  # to have lower camel case property names.

  def __init__(self,
               spec_targets,
               status_targets,
               revision_name,
               latest,
               service_url=''):
    """Creates a new TrafficTargetPair.

    Args:
      spec_targets: A list of spec TrafficTargets that all reference the same
        revision, either by name or the latest ready.
      status_targets: A list of status TrafficTargets that all reference the
        same revision, either by name or the latest ready.
      revision_name: The name of the revision referenced by the traffic targets.
      latest: A boolean indicating if these traffic targets reference the latest
        ready revision.
      service_url: The main URL for the service. Optional.

    Returns:
      A new TrafficTargetPair instance.
    """
    self._spec_targets = spec_targets
    self._status_targets = status_targets
    self._revision_name = revision_name
    self._latest = latest
    self._service_url = service_url
    self._tags = None

  @property
  def latestRevision(self):  # pylint: disable=invalid-name
    """Returns true if the traffic targets reference the latest revision."""
    return self._latest

  @property
  def revisionName(self):  # pylint: disable=invalid-name
    return self._revision_name

  @property
  def specPercent(self):  # pylint: disable=invalid-name
    if self._spec_targets:
      return six.text_type(_SumPercent(self._spec_targets))
    else:
      return _MISSING_PERCENT_OR_TAGS

  @property
  def statusPercent(self):  # pylint: disable=invalid-name
    if self._status_targets:
      return six.text_type(_SumPercent(self._status_targets))
    else:
      return _MISSING_PERCENT_OR_TAGS

  @property
  def specTags(self):  # pylint: disable=invalid-name
    spec_tags = _TAGS_JOIN_STRING.join(
        sorted(t.tag for t in self._spec_targets if t.tag))
    return spec_tags if spec_tags else _MISSING_PERCENT_OR_TAGS

  @property
  def statusTags(self):  # pylint: disable=invalid-name
    status_tags = _TAGS_JOIN_STRING.join(
        sorted(t.tag for t in self._status_targets if t.tag))
    return status_tags if status_tags else _MISSING_PERCENT_OR_TAGS

  @property
  def urls(self):
    return sorted(t.url for t in self._status_targets if t.url)

  @property
  def tags(self):
    if self._tags is None:
      self._ExtractTags()
    return self._tags

  def _ExtractTags(self):
    """Extracts the traffic tag state from spec and status into TrafficTags."""
    tags = {}
    for spec_target in self._spec_targets:
      if not spec_target.tag:
        continue
      tags[spec_target.tag] = TrafficTag(spec_target.tag, in_spec=True)
    for status_target in self._status_targets:
      if not status_target.tag:
        continue
      if status_target.tag in tags:
        tag = tags[status_target.tag]
      else:
        tag = tags.setdefault(status_target.tag, TrafficTag(status_target.tag))
      tag.url = status_target.url if status_target.url is not None else ''
      tag.inStatus = True
    self._tags = sorted(tags.values(), key=operator.attrgetter('tag'))

  @property
  def displayPercent(self):  # pylint: disable=invalid-name
    """Returns human readable revision percent."""
    if self.statusPercent == self.specPercent:
      return _FormatPercentage(self.statusPercent)
    else:
      return '{:4} (currently {})'.format(
          _FormatPercentage(self.specPercent),
          _FormatPercentage(self.statusPercent))

  @property
  def displayRevisionId(self):  # pylint: disable=invalid-name
    """Returns human readable revision identifier."""
    if self.latestRevision:
      return '%s (currently %s)' % (traffic.GetKey(self), self.revisionName)
    else:
      return self.revisionName

  @property
  def displayTags(self):  # pylint: disable=invalid-name
    spec_tags = self.specTags
    status_tags = self.statusTags
    if spec_tags == status_tags:
      return status_tags if status_tags != _MISSING_PERCENT_OR_TAGS else ''
    else:
      return '{} (currently {})'.format(spec_tags, status_tags)

  @property
  def serviceUrl(self):  # pylint: disable=invalid-name
    """The main URL for the service."""
    return self._service_url


def GetTrafficTargetPairs(spec_traffic,
                          status_traffic,
                          latest_ready_revision_name,
                          service_url=''):
  """Returns a list of TrafficTargetPairs for a Service.

  Given the spec and status traffic targets wrapped in a TrafficTargets instance
  for a sevice, this function pairs up all spec and status traffic targets that
  reference the same revision (either by name or the latest ready revision) into
  TrafficTargetPairs. This allows the caller to easily see any differences
  between the spec and status traffic.

  Args:
    spec_traffic: A dictionary of name->traffic.TrafficTarget for the spec
      traffic.
    status_traffic: A dictionary of name->traffic.TrafficTarget for the status
      traffic.
    latest_ready_revision_name: The name of the service's latest ready revision.
    service_url: The main URL for the service. Optional.

  Returns:
    A list of TrafficTargetPairs representing the current state of the service's
    traffic assignments. The TrafficTargetPairs are sorted by revision name,
    with targets referencing the latest ready revision at the end.
  """
  # Copy spec and status traffic to dictionaries to allow mapping
  # traffic.LATEST_REVISION_KEY to the same targets as
  # latest_ready_revision_name without modifying the underlying protos during
  # a read-only operation. These dictionaries map revision name (or "LATEST"
  # for the latest ready revision) to a list of TrafficTarget protos.
  spec_dict = dict(spec_traffic)
  status_dict = dict(status_traffic)

  result = []
  for k in set(spec_dict).union(status_dict):
    spec_targets = spec_dict.get(k, [])
    status_targets = status_dict.get(k, [])
    if k == traffic.LATEST_REVISION_KEY:
      revision_name = latest_ready_revision_name
      latest = True
    else:
      revision_name = k
      latest = False

    result.append(
        TrafficTargetPair(spec_targets, status_targets, revision_name, latest,
                          service_url))
  return sorted(result, key=SortKeyFromTarget)


def GetTrafficTargetPairsDict(service_dict):
  """Returns a list of TrafficTargetPairs for a Service as python dictionary.

  Delegates to GetTrafficTargetPairs().

  Args:
    service_dict: python dict-like object representing a Service unmarshalled
      from json
  """
  svc = service.Service(service_dict)
  return GetTrafficTargetPairs(svc.spec_traffic, svc.status_traffic,
                               svc.latest_ready_revision, svc.url)
