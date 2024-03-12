# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Spanner instanceConfigs API helper."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources
import six


class MissingReplicaError(core_exceptions.Error):
  """Indicates that the replica is missing in the source config."""

  def __init__(self, replica_location, replica_type):
    super(MissingReplicaError, self).__init__(
        'The replica {0} of type {1} is not in the source config\'s replicas'
        .format(replica_location, replica_type))


def Get(config):
  """Get the specified instance config."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      config,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instanceConfigs')
  req = msgs.SpannerProjectsInstanceConfigsGetRequest(
      name=ref.RelativeName())
  return client.projects_instanceConfigs.Get(req)


def List():
  """List instance configs in the project."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  req = msgs.SpannerProjectsInstanceConfigsListRequest(
      parent='projects/'+properties.VALUES.core.project.GetOrFail())
  return list_pager.YieldFromList(
      client.projects_instanceConfigs,
      req,
      field='instanceConfigs',
      batch_size_attribute='pageSize')


def Delete(config, etag=None, validate_only=False):
  """Delete an instance config."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      config,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instanceConfigs')
  req = msgs.SpannerProjectsInstanceConfigsDeleteRequest(
      name=ref.RelativeName(), etag=etag, validateOnly=validate_only)
  return client.projects_instanceConfigs.Delete(req)


def CreateUsingExistingConfig(args, config):
  """Create a new CMMR instance config based on an existing GMMR/CMMR config."""
  msgs = apis.GetMessagesModule('spanner', 'v1')

  # Override the user provided values, if any. Otherwise, clone the same from
  # an existing config values.
  display_name = args.display_name if args.display_name else config.displayName
  labels = args.labels if args.labels else config.labels

  # Note: baseConfig field is only set for user managed configurations.
  # Use config name if this is not set.
  base_config = config.baseConfig if config.baseConfig else config.name

  replica_info_list = config.replicas
  if args.skip_replicas:
    _SkipReplicas(msgs, args.skip_replicas, replica_info_list)
  if args.add_replicas:
    _AppendReplicas(msgs, args.add_replicas, replica_info_list)

  return _Create(msgs, args.config, display_name, base_config,
                 replica_info_list, labels, args.validate_only, args.etag)


def CreateUsingReplicas(config,
                        display_name,
                        base_config,
                        replicas_arg,
                        validate_only,
                        labels=None,
                        etag=None):
  """Create a new instance configs based on provided list of replicas."""
  msgs = apis.GetMessagesModule('spanner', 'v1')
  config_ref = resources.REGISTRY.Parse(
      base_config,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instanceConfigs')

  replica_info_list = []
  _AppendReplicas(msgs, replicas_arg, replica_info_list)

  labels_message = {}
  if labels is not None:
    labels_message = msgs.InstanceConfig.LabelsValue(additionalProperties=[
        msgs.InstanceConfig.LabelsValue.AdditionalProperty(
            key=key, value=value) for key, value in six.iteritems(labels)
    ])

  return _Create(msgs, config, display_name, config_ref.RelativeName(),
                 replica_info_list, labels_message, validate_only, etag)


def _Create(msgs,
            config,
            display_name,
            base_config,
            replica_info_list,
            labels,
            validate_only,
            etag=None):
  """Create instance configs in the project."""
  client = apis.GetClientInstance('spanner', 'v1')
  project_ref = resources.REGISTRY.Create(
      'spanner.projects', projectsId=properties.VALUES.core.project.GetOrFail)
  config_ref = resources.REGISTRY.Parse(
      config,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instanceConfigs')
  instance_config = msgs.InstanceConfig(
      name=config_ref.RelativeName(),
      displayName=display_name,
      baseConfig=base_config,
      labels=labels,
      replicas=replica_info_list)
  if etag:
    instance_config.etag = etag

  req = msgs.SpannerProjectsInstanceConfigsCreateRequest(
      parent=project_ref.RelativeName(),
      createInstanceConfigRequest=msgs.CreateInstanceConfigRequest(
          instanceConfigId=config,
          instanceConfig=instance_config,
          validateOnly=validate_only))
  return client.projects_instanceConfigs.Create(req)


def _AppendReplicas(msgs, add_replicas_arg, replica_info_list):
  """Appends each in add_replicas_arg to the given ReplicaInfo list."""
  for replica in add_replicas_arg:
    replica_type = arg_utils.ChoiceToEnum(replica['type'],
                                          msgs.ReplicaInfo.TypeValueValuesEnum)
    replica_info_list.append(
        msgs.ReplicaInfo(location=replica['location'], type=replica_type))


def _SkipReplicas(msgs, skip_replicas_arg, replica_info_list):
  """Skips each in skip_replicas_arg from the given ReplicaInfo list."""
  for replica_to_skip in skip_replicas_arg:
    index_to_delete = None
    replica_type = arg_utils.ChoiceToEnum(replica_to_skip['type'],
                                          msgs.ReplicaInfo.TypeValueValuesEnum)
    for index, replica in enumerate(replica_info_list):
      # Only skip the first found matching replica.
      if (replica.location == replica_to_skip['location'] and
          replica.type == replica_type):
        index_to_delete = index
        pass

    if index_to_delete is None:
      raise MissingReplicaError(replica_to_skip['location'], replica_type)

    replica_info_list.pop(index_to_delete)


def Patch(args):
  """Update an instance config."""
  client = apis.GetClientInstance('spanner', 'v1')
  msgs = apis.GetMessagesModule('spanner', 'v1')
  ref = resources.REGISTRY.Parse(
      args.config,
      params={'projectsId': properties.VALUES.core.project.GetOrFail},
      collection='spanner.projects.instanceConfigs')
  instance_config = msgs.InstanceConfig(name=ref.RelativeName())

  update_mask = []

  if args.display_name is not None:
    instance_config.displayName = args.display_name
    update_mask.append('display_name')

  if args.etag is not None:
    instance_config.etag = args.etag

  def GetLabels():
    req = msgs.SpannerProjectsInstanceConfigsGetRequest(name=ref.RelativeName())
    return client.projects_instanceConfigs.Get(req).labels

  labels_update = labels_util.ProcessUpdateArgsLazy(
      args, msgs.InstanceConfig.LabelsValue, GetLabels)
  if labels_update.needs_update:
    instance_config.labels = labels_update.labels
    update_mask.append('labels')

  if not update_mask:
    raise errors.NoFieldsSpecifiedError('No updates requested.')

  req = msgs.SpannerProjectsInstanceConfigsPatchRequest(
      name=ref.RelativeName(),
      updateInstanceConfigRequest=msgs.UpdateInstanceConfigRequest(
          instanceConfig=instance_config,
          updateMask=','.join(update_mask),
          validateOnly=args.validate_only))
  return client.projects_instanceConfigs.Patch(req)
