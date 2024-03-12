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
"""Commands for interacting with Immersive Stream for XR service instances."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.immersive_stream.xr import api_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.core import properties


def ProjectLocation(project, location):
  return 'projects/{}/locations/{}'.format(project, location)


def GenerateTargetLocationConfigs(
    release_track,
    add_region_configs,
    update_region_configs,
    remove_regions,
    current_instance,
):
  """Generates the target location configs.

  Args:
    release_track: ALPHA or GA release track
    add_region_configs: List of region config dicts of the form: [{'region':
      region1, 'capacity': capacity1, 'enable_autoscaling': enable_autoscaling1,
      'autoscaling_buffer': autoscaling_buffer1, 'autoscaling_min_capacity':
      autoscaling_min_capacity1}] that specifies the regions to add to the
      service instance
    update_region_configs: List of region config dicts of the form: [{'region':
      region1, 'capacity': capacity1}] that specifies the regions to update to
      the service instance
    remove_regions: List of regions to remove
    current_instance: instance object - current state of the service instance
      before update

  Returns:
    A LocationConfigsValue, with entries sorted by location
  """

  if current_instance is not None:
    additonal_properties = current_instance.locationConfigs.additionalProperties
    location_configs = {
        location_config.key: location_config.value
        for location_config in additonal_properties
    }
  else:
    location_configs = {}

  if add_region_configs:
    if any(
        region_config['region'] in location_configs
        for region_config in add_region_configs
    ):
      log.status.Print('Only new regions can be added.')
      return
    region_configs_diff = add_region_configs

  elif remove_regions:
    if any(region not in location_configs for region in remove_regions):
      log.status.Print('Only existing regions can be removed.')
      return None
    # Convert the list of regions to remove to a list of region configs with
    # 0 capacities.
    region_configs_diff = (
        {'region': region, 'capacity': 0, 'enable_autoscaling': False}
        for region in remove_regions
    )

  elif update_region_configs:
    if any(
        region_config['region'] not in location_configs
        for region_config in update_region_configs
    ):
      log.status.Print('Only existing regions can be updated.')
      return None
    # Update API is idempotent so we do not need to check if the capacity is
    # unchanged.
    region_configs_diff = update_region_configs

  messages = api_util.GetMessages(release_track)
  location_configs_diff = messages.StreamInstance.LocationConfigsValue()
  for region_config in region_configs_diff:
    region = region_config['region']
    capacity = int(region_config['capacity'])
    enable_autoscaling = region_config.get('enable_autoscaling', False)
    location_config = messages.LocationConfig(
        location=region,
        capacity=capacity,
        enableAutoscaling=enable_autoscaling,
    )
    if enable_autoscaling:
      location_config.autoscalingBuffer = int(
          region_config['autoscaling_buffer']
      )
      location_config.autoscalingMinCapacity = int(
          region_config['autoscaling_min_capacity']
      )

    location_configs_diff.additionalProperties.append(
        messages.StreamInstance.LocationConfigsValue.AdditionalProperty(
            key=region, value=location_config
        )
    )

  # Merge current location configs with the diff.
  for location_config in location_configs_diff.additionalProperties:
    if remove_regions and location_config.value.capacity == 0:
      # Remove a location.
      location_configs.pop(location_config.key, None)
    else:
      # Add or update a location.
      location_configs[location_config.key] = location_config.value

  # Convert the location configs from a dict to LocationConfigsValue.
  target_location_configs = messages.StreamInstance.LocationConfigsValue()
  # Sort the location config so that we have a deterministic order of items in
  # LocationConfigsValue.
  for key, location_config in sorted(location_configs.items()):
    target_location_configs.additionalProperties.append(
        messages.StreamInstance.LocationConfigsValue.AdditionalProperty(
            key=key, value=location_config
        )
    )

  return target_location_configs


def Get(release_track, instance_relative_name):
  """Get resource details of an Immersive Stream for XR service instance.

  Args:
    release_track: ALPHA or GA release track
    instance_relative_name: string - canonical resource name of the instance

  Returns:
    A service instance resource object.
  """
  client = api_util.GetClient(release_track)
  messages = api_util.GetMessages(release_track)
  service = client.ProjectsLocationsStreamInstancesService(client)

  return service.Get(
      messages.StreamProjectsLocationsStreamInstancesGetRequest(
          name=instance_relative_name
      )
  )


def Create(
    release_track,
    instance_name,
    content,
    location,
    version,
    target_location_configs,
    fallback_url=None,
    mode=None,
    gpu_class=None,
):
  """Create a new Immersive Stream for XR service instance.

  Args:
    release_track: ALPHA or GA release track
    instance_name: string - name of the service instance
    content: string - resource path of the content resource that is served by
      the instance
    location: string - location where the resource will be created
    version: string - content build version tag
    target_location_configs: A LocationConfigsValue proto message represents the
      target location configs to achieve
    fallback_url: string - A url to redirect users to when the instance is
      unable to provide the streaming experience
    mode: string - The rendering mode supported by the service instance
    gpu_class: string - The class of GPU used by this instance

  Returns:
    An Operation object which can be used to check on the progress of the
    service instance creation.
  """
  client = api_util.GetClient(release_track)
  messages = api_util.GetMessages(release_track)
  build_version = messages.BuildVersion(contentVersionTag=version)

  instance = messages.StreamInstance(
      content=content,
      contentBuildVersion=build_version,
      name=instance_name,
      locationConfigs=target_location_configs,
      mode=mode,
      gpuClass=gpu_class,
  )
  if fallback_url:
    stream_config = messages.StreamConfig(fallbackUri=fallback_url)
    instance.streamConfig = stream_config
  service = client.ProjectsLocationsStreamInstancesService(client)

  return service.Create(
      messages.StreamProjectsLocationsStreamInstancesCreateRequest(
          parent=ProjectLocation(
              properties.VALUES.core.project.Get(), location
          ),
          streamInstance=instance,
          streamInstanceId=instance_name,
      )
  )


def UpdateLocationConfigs(release_track, instance_ref, target_location_configs):
  """Updates the location configs for a service instance.

  Args:
    release_track: ALPHA or GA release track
    instance_ref: resource object - service instance to be updated
    target_location_configs: A LocationConfigsValue proto message represents the
      target location configs to achieve

  Returns:
    An Operation object which can be used to check on the progress of the
    service instance update.
  """
  if (
      not target_location_configs
      or not target_location_configs.additionalProperties
  ):
    raise exceptions.Error('Target location configs must be provided')

  client = api_util.GetClient(release_track)
  messages = api_util.GetMessages(release_track)
  # Puts merged location_configs into a StreamInstance
  instance = messages.StreamInstance(locationConfigs=target_location_configs)
  service = client.ProjectsLocationsStreamInstancesService(client)

  return service.Patch(
      messages.StreamProjectsLocationsStreamInstancesPatchRequest(
          name=instance_ref.RelativeName(),
          streamInstance=instance,
          updateMask='location_configs',
      )
  )


def UpdateContentBuildVersion(release_track, instance_ref, version):
  """Update content build version of an Immersive Stream for XR service instance.

  Args:
    release_track: ALPHA or GA release track
    instance_ref: resource object - service instance to be updated
    version: content build version tag

  Returns:
    An Operation object which can be used to check on the progress of the
    service instance update.
  """
  client = api_util.GetClient(release_track)
  messages = api_util.GetMessages(release_track)
  build_version = messages.BuildVersion(contentVersionTag=version)
  instance = messages.StreamInstance(contentBuildVersion=build_version)
  service = client.ProjectsLocationsStreamInstancesService(client)

  return service.Patch(
      messages.StreamProjectsLocationsStreamInstancesPatchRequest(
          name=instance_ref.RelativeName(),
          streamInstance=instance,
          updateMask='content_build_version',
      )
  )


def UpdateFallbackUrl(release_track, instance_ref, fallback_url):
  """Update fallback url of an Immersive Stream for XR service instance.

  Args:
    release_track: ALPHA or GA release track
    instance_ref: resource object - service instance to be updated
    fallback_url: string - fallback url to redirect users to when the instance
      is not available

  Returns:
    An Operation object which can be used to check on the progress of the
    service instance update.
  """
  client = api_util.GetClient(release_track)
  messages = api_util.GetMessages(release_track)
  service = client.ProjectsLocationsStreamInstancesService(client)

  stream_config = messages.StreamConfig(fallbackUri=fallback_url)
  instance = messages.StreamInstance()
  instance.streamConfig = stream_config
  return service.Patch(
      messages.StreamProjectsLocationsStreamInstancesPatchRequest(
          name=instance_ref.RelativeName(),
          streamInstance=instance,
          updateMask='stream_config',
      )
  )
