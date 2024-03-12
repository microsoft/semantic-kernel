# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""API Library for gcloud tasks queues."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.core import exceptions

import six

http_target_update_masks_list = [
    'httpTarget.headerOverrides',
    'httpTarget.httpMethod',
    'httpTarget.oauthToken.serviceAccountEmail',
    'httpTarget.oauthToken.scope',
    'httpTarget.oidcToken.serviceAccountEmail',
    'httpTarget.oidcToken.audience',
    'httpTarget.uriOverride',
]


class CreatingPullAndAppEngineQueueError(exceptions.InternalError):
  """Error for when attempt to create a queue as both pull and App Engine."""


class CreatingHttpAndAppEngineQueueError(exceptions.InternalError):
  """Error for when attempt to create a queue with both http and App Engine targets."""


class NoFieldsSpecifiedError(exceptions.Error):
  """Error for when calling a patch method with no fields specified."""


class RequiredFieldsMissingError(exceptions.Error):
  """Error for when calling a patch method when a required field is unspecified."""


class BaseQueues(object):
  """Client for queues service in the Cloud Tasks API."""

  def __init__(self, messages, queues_service):
    self.messages = messages
    self.queues_service = queues_service

  def Get(self, queue_ref):
    request = self.messages.CloudtasksProjectsLocationsQueuesGetRequest(
        name=queue_ref.RelativeName()
    )
    return self.queues_service.Get(request)

  def List(self, parent_ref, limit=None, page_size=100):
    request = self.messages.CloudtasksProjectsLocationsQueuesListRequest(
        parent=parent_ref.RelativeName()
    )
    return list_pager.YieldFromList(
        self.queues_service,
        request,
        batch_size=page_size,
        limit=limit,
        field='queues',
        batch_size_attribute='pageSize',
    )

  def Delete(self, queue_ref):
    request = self.messages.CloudtasksProjectsLocationsQueuesDeleteRequest(
        name=queue_ref.RelativeName()
    )
    return self.queues_service.Delete(request)

  def Purge(self, queue_ref):
    request = self.messages.CloudtasksProjectsLocationsQueuesPurgeRequest(
        name=queue_ref.RelativeName()
    )
    return self.queues_service.Purge(request)

  def Pause(self, queue_ref):
    request = self.messages.CloudtasksProjectsLocationsQueuesPauseRequest(
        name=queue_ref.RelativeName()
    )
    return self.queues_service.Pause(request)

  def Resume(self, queue_ref):
    request = self.messages.CloudtasksProjectsLocationsQueuesResumeRequest(
        name=queue_ref.RelativeName()
    )
    return self.queues_service.Resume(request)

  def GetIamPolicy(self, queue_ref):
    request = (
        self.messages.CloudtasksProjectsLocationsQueuesGetIamPolicyRequest(
            resource=queue_ref.RelativeName()
        )
    )
    return self.queues_service.GetIamPolicy(request)

  def SetIamPolicy(self, queue_ref, policy):
    request = (
        self.messages.CloudtasksProjectsLocationsQueuesSetIamPolicyRequest(
            resource=queue_ref.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy
            ),
        )
    )
    return self.queues_service.SetIamPolicy(request)


class Queues(BaseQueues):
  """Client for queues service in the Cloud Tasks API."""

  def Create(
      self,
      parent_ref,
      queue_ref,
      retry_config=None,
      rate_limits=None,
      app_engine_routing_override=None,
      stackdriver_logging_config=None,
      http_target=None,
  ):
    """Prepares and sends a Create request for creating a queue."""
    targets = (app_engine_routing_override, http_target)
    if sum([1 if x is not None else 0 for x in targets]) > 1:
      raise CreatingHttpAndAppEngineQueueError(
          'Attempting to send multiple queue target types simultaneously: {}'
          ' , {}'.format(
              six.text_type(app_engine_routing_override),
              six.text_type(http_target),
          )
      )

    queue = self.messages.Queue(
        name=queue_ref.RelativeName(),
        retryConfig=retry_config,
        rateLimits=rate_limits,
        appEngineRoutingOverride=app_engine_routing_override,
        stackdriverLoggingConfig=stackdriver_logging_config,
        httpTarget=http_target
    )
    request = self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
        parent=parent_ref.RelativeName(), queue=queue
    )
    return self.queues_service.Create(request)

  def Patch(
      self,
      queue_ref,
      updated_fields,
      retry_config=None,
      rate_limits=None,
      app_engine_routing_override=None,
      stackdriver_logging_config=None,
      http_uri_override=None,
      http_method_override=None,
      http_header_override=None,
      http_oauth_email_override=None,
      http_oauth_scope_override=None,
      http_oidc_email_override=None,
      http_oidc_audience_override=None,
  ):
    """Prepares and sends a Patch request for modifying a queue."""
    if not any([retry_config, rate_limits, stackdriver_logging_config]):
      # If appEngineRoutingOverride is in updated_fields then an empty
      # app_engine_routing_override will remove the routing override field.
      if (
          not app_engine_routing_override
          and 'appEngineRoutingOverride' not in updated_fields
      ) and _NeitherUpdateNorClear(
          [
              http_uri_override,
              http_method_override,
              http_header_override,
              http_oauth_email_override,
              http_oauth_scope_override,
              http_oidc_email_override,
              http_oidc_audience_override,
          ],
          http_target_update_masks_list,
          updated_fields,
      ):
        raise NoFieldsSpecifiedError(
            'Must specify at least one field to update.'
        )

    queue = self.messages.Queue(name=queue_ref.RelativeName())

    if retry_config is not None:
      queue.retryConfig = retry_config
    if rate_limits is not None:
      queue.rateLimits = rate_limits
    if app_engine_routing_override is not None:
      if _IsEmptyConfig(app_engine_routing_override):
        queue.appEngineRoutingOverride = self.messages.AppEngineRouting()
      else:
        queue.appEngineRoutingOverride = app_engine_routing_override
    if stackdriver_logging_config is not None:
      queue.stackdriverLoggingConfig = stackdriver_logging_config

    # modifies the queue
    _GenerateHttpTargetUpdateMask(
        self.messages,
        queue,
        updated_fields,
        http_uri_override,
        http_method_override,
        http_header_override,
        http_oauth_email_override,
        http_oauth_scope_override,
        http_oidc_email_override,
        http_oidc_audience_override,
    )

    update_mask = ','.join(updated_fields)

    request = self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
        name=queue_ref.RelativeName(), queue=queue, updateMask=update_mask
    )
    return self.queues_service.Patch(request)


class BetaQueues(BaseQueues):
  """Client for queues service in the Cloud Tasks API."""

  def Create(
      self,
      parent_ref,
      queue_ref,
      retry_config=None,
      rate_limits=None,
      app_engine_http_queue=None,
      stackdriver_logging_config=None,
      queue_type=None,
      http_target=None,
  ):
    """Prepares and sends a Create request for creating a queue."""

    # There are different cases: if both app_engine and HTTP targets are
    # provided, then throw an error. If HTTP target is provided, then use it,
    # otherwise use app_engine by default.
    is_app_engine_target_set = (
        app_engine_http_queue is not None
        and app_engine_http_queue.appEngineRoutingOverride is not None
    )

    is_http_target_set = http_target is not None

    if is_app_engine_target_set and is_http_target_set:
      raise CreatingHttpAndAppEngineQueueError(
          'Attempting to send multiple queue target types simultaneously: {}'
          ' , {}'.format(
              six.text_type(app_engine_http_queue), six.text_type(http_target)
          )
      )
    if is_http_target_set:
      queue = self.messages.Queue(
          name=queue_ref.RelativeName(),
          retryConfig=retry_config,
          rateLimits=rate_limits,
          stackdriverLoggingConfig=stackdriver_logging_config,
          type=queue_type,
          httpTarget=http_target,
      )
    else:
      queue = self.messages.Queue(
          name=queue_ref.RelativeName(),
          retryConfig=retry_config,
          rateLimits=rate_limits,
          appEngineHttpQueue=app_engine_http_queue,
          stackdriverLoggingConfig=stackdriver_logging_config,
          type=queue_type,
      )
    request = self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
        parent=parent_ref.RelativeName(), queue=queue
    )

    return self.queues_service.Create(request)

  def Patch(
      self,
      queue_ref,
      updated_fields,
      retry_config=None,
      rate_limits=None,
      app_engine_routing_override=None,
      task_ttl=None,
      task_tombstone_ttl=None,
      stackdriver_logging_config=None,
      queue_type=None,
      http_uri_override=None,
      http_method_override=None,
      http_header_override=None,
      http_oauth_email_override=None,
      http_oauth_scope_override=None,
      http_oidc_email_override=None,
      http_oidc_audience_override=None,
  ):
    """Prepares and sends a Patch request for modifying a queue."""
    # The following block is necessary to modify pull queue attributes without
    # explicitly setting type to 'pull' during CLI invocation.
    if queue_type and queue_type != queue_type.PULL:
      queue_type = None

    if not any([
        retry_config,
        rate_limits,  # No effect here as it is not user-configurable
        task_ttl,  # No effect here as it is not user-configurable
        task_tombstone_ttl,
        stackdriver_logging_config,
    ]):
      # IF no app_engine_routing_override (for updating the value) AND
      # IF no appEngineRoutingOverride in the update fields (to clear the value)
      # AND IF none of the http target override parts are given (to update their
      # values) AND IF none of the http target override update masks are in the
      # update fields (to clear their values) THEN throw error.
      if _NeitherUpdateNorClear(
          [app_engine_routing_override],
          ['appEngineRoutingOverride'],
          updated_fields,
      ) and _NeitherUpdateNorClear(
          [
              http_uri_override,
              http_method_override,
              http_header_override,
              http_oauth_email_override,
              http_oauth_scope_override,
              http_oidc_email_override,
              http_oidc_audience_override,
          ],
          http_target_update_masks_list,
          updated_fields,
      ):
        raise NoFieldsSpecifiedError(
            'Must specify at least one field to update.'
        )

    queue = self.messages.Queue(name=queue_ref.RelativeName(), type=queue_type)

    if retry_config is not None:
      queue.retryConfig = retry_config
    if rate_limits is not None:
      queue.rateLimits = rate_limits
    if task_ttl is not None:
      queue.taskTtl = task_ttl
    if task_tombstone_ttl is not None:
      queue.tombstoneTtl = task_tombstone_ttl
    if stackdriver_logging_config is not None:
      queue.stackdriverLoggingConfig = stackdriver_logging_config

    if app_engine_routing_override is not None:
      if _IsEmptyConfig(app_engine_routing_override):
        queue.appEngineHttpQueue = self.messages.AppEngineHttpQueue()
      else:
        queue.appEngineHttpQueue = self.messages.AppEngineHttpQueue(
            appEngineRoutingOverride=app_engine_routing_override
        )

    # modifies the queue
    _GenerateHttpTargetUpdateMask(
        self.messages,
        queue,
        updated_fields,
        http_uri_override,
        http_method_override,
        http_header_override,
        http_oauth_email_override,
        http_oauth_scope_override,
        http_oidc_email_override,
        http_oidc_audience_override,
    )

    update_mask = ','.join(updated_fields)

    request = self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
        name=queue_ref.RelativeName(), queue=queue, updateMask=update_mask
    )
    return self.queues_service.Patch(request)


class AlphaQueues(BaseQueues):
  """Client for queues service in the Cloud Tasks API."""

  def Create(
      self,
      parent_ref,
      queue_ref,
      retry_config=None,
      rate_limits=None,
      pull_target=None,
      app_engine_http_target=None,
      http_target=None,
  ):
    """Prepares and sends a Create request for creating a queue."""

    targets = (app_engine_http_target, http_target)
    if sum([1 if x is not None else 0 for x in targets]) > 1:
      raise CreatingHttpAndAppEngineQueueError(
          'Attempting to send multiple queue target types simultaneously: {}'
          ' , {}'.format(
              six.text_type(app_engine_http_target), six.text_type(http_target)
          )
      )

    targets = (pull_target, app_engine_http_target, http_target)
    if sum([1 if x is not None else 0 for x in targets]) > 1:
      raise CreatingPullAndAppEngineQueueError(
          'Attempting to send multiple queue target types simultaneously'
      )
    queue = self.messages.Queue(
        name=queue_ref.RelativeName(),
        retryConfig=retry_config,
        rateLimits=rate_limits,
        pullTarget=pull_target,
        appEngineHttpTarget=app_engine_http_target,
        httpTarget=http_target,
    )
    request = self.messages.CloudtasksProjectsLocationsQueuesCreateRequest(
        parent=parent_ref.RelativeName(), queue=queue
    )
    return self.queues_service.Create(request)

  def Patch(
      self,
      queue_ref,
      updated_fields,
      retry_config=None,
      rate_limits=None,
      app_engine_routing_override=None,
      http_uri_override=None,
      http_method_override=None,
      http_header_override=None,
      http_oauth_email_override=None,
      http_oauth_scope_override=None,
      http_oidc_email_override=None,
      http_oidc_audience_override=None,
  ):
    """Prepares and sends a Patch request for modifying a queue."""

    if not any([retry_config, rate_limits]):
      # IF no app_engine_routing_override (for updating the value) AND
      # IF no appEngineRoutingOverride in the update fields (to clear the value)
      # AND IF none of the http target override parts are given (to update their
      # values) AND IF none of the http target override update masks are in the
      # update fields (to clear their values) THEN throw error.
      if _NeitherUpdateNorClear(
          [app_engine_routing_override],
          ['appEngineRoutingOverride'],
          updated_fields,
      ) and _NeitherUpdateNorClear(
          [
              http_uri_override,
              http_method_override,
              http_header_override,
              http_oauth_email_override,
              http_oauth_scope_override,
              http_oidc_email_override,
              http_oidc_audience_override,
          ],
          http_target_update_masks_list,
          updated_fields,
      ):
        raise NoFieldsSpecifiedError(
            'Must specify at least one field to update.'
        )

    queue = self.messages.Queue(name=queue_ref.RelativeName())

    if retry_config is not None:
      queue.retryConfig = retry_config
    if rate_limits is not None:
      queue.rateLimits = rate_limits

    if app_engine_routing_override is not None:
      if _IsEmptyConfig(app_engine_routing_override):
        queue.appEngineHttpTarget = self.messages.AppEngineHttpTarget()
      else:
        queue.appEngineHttpTarget = self.messages.AppEngineHttpTarget(
            appEngineRoutingOverride=app_engine_routing_override
        )
    # modifies the queue
    _GenerateHttpTargetUpdateMask(
        self.messages,
        queue,
        updated_fields,
        http_uri_override,
        http_method_override,
        http_header_override,
        http_oauth_email_override,
        http_oauth_scope_override,
        http_oidc_email_override,
        http_oidc_audience_override,
    )
    update_mask = ','.join(updated_fields)

    request = self.messages.CloudtasksProjectsLocationsQueuesPatchRequest(
        name=queue_ref.RelativeName(), queue=queue, updateMask=update_mask
    )
    return self.queues_service.Patch(request)


def _GenerateHttpTargetUpdateMask(
    messages,
    queue,
    updated_fields,
    http_uri_override=None,
    http_method_override=None,
    http_header_override=None,
    http_oauth_email_override=None,
    http_oauth_scope_override=None,
    http_oidc_email_override=None,
    http_oidc_audience_override=None,
):
  """A helper function to generate update mask given the override config."""

  if _HttpTargetNeedsUpdate(updated_fields):
    http_target = messages.HttpTarget()

    if 'httpTarget.uriOverride' in updated_fields:
      http_target.uriOverride = http_uri_override

    if 'httpTarget.httpMethod' in updated_fields:
      http_target.httpMethod = http_method_override

    if 'httpTarget.headerOverrides' in updated_fields:
      if http_header_override is None:
        http_target.headerOverrides = []
      else:
        headers_list = []
        for ho in http_header_override:
          header_override = messages.HeaderOverride(
              header=messages.Header(key=ho.header.key, value=ho.header.value)
          )
          headers_list.append(header_override)
        http_target.headerOverrides = headers_list

    if (
        'httpTarget.oauthToken.serviceAccountEmail' in updated_fields
        or 'httpTarget.oauthToken.scope' in updated_fields
    ):
      # service account email is required
      if 'httpTarget.oauthToken.serviceAccountEmail' not in updated_fields or (
          http_oauth_email_override is None
          and http_oauth_scope_override is not None
      ):
        # We raise exception here because CT backend generates an error:
        # generic::invalid_argument:
        # service_account_email must be set. [google.rpc.error_details_ext]
        # { message: \"service_account_email must be set.\" }
        raise RequiredFieldsMissingError(
            'Oauth service account email'
            ' (http-oauth-service-account-email-override) must be set.'
        )
      elif (
          http_oauth_email_override is None
          and http_oauth_scope_override is None
      ):
        http_target.oauthToken = None
      else:
        http_target.oauthToken = messages.OAuthToken(
            serviceAccountEmail=http_oauth_email_override,
            scope=http_oauth_scope_override,
        )

    if (
        'httpTarget.oidcToken.serviceAccountEmail' in updated_fields
        or 'httpTarget.oidcToken.audience' in updated_fields
    ):
      # service account email is required
      if 'httpTarget.oidcToken.serviceAccountEmail' not in updated_fields or (
          http_oidc_email_override is None
          and http_oidc_audience_override is not None
      ):
        raise RequiredFieldsMissingError(
            'Oidc service account email'
            ' (http-oidc-service-account-email-override) must be set.'
        )
      if (
          http_oidc_email_override is None
          and http_oidc_audience_override is None
      ):
        http_target.oidcToken = None
      else:
        http_target.oidcToken = messages.OidcToken(
            serviceAccountEmail=http_oidc_email_override,
            audience=http_oidc_audience_override,
        )

    queue.httpTarget = None if _IsEmptyConfig(http_target) else http_target


def _HttpTargetNeedsUpdate(updated_fields):
  for mask in http_target_update_masks_list:
    if mask in updated_fields:
      return True

  return False


def _NeitherUpdateNorClear(update_values, available_masks, update_fields):
  return all(item is None for item in update_values) and not any(
      item in available_masks for item in update_fields
  )


def _IsEmptyConfig(config):
  if config is None:
    return True

  config_dict = encoding.MessageToDict(config)
  return not any(config_dict.values())
