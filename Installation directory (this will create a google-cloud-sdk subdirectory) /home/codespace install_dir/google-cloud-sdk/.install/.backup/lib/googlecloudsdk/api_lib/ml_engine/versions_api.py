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
"""Utilities for dealing with ML versions API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import text
import six


class InvalidVersionConfigFile(exceptions.Error):
  """Error indicating an invalid Version configuration file."""


class NoFieldsSpecifiedError(exceptions.Error):
  """Error indicating an invalid Version configuration file."""


def GetMessagesModule(version='v1'):
  return apis.GetMessagesModule('ml', version)


def GetClientInstance(version='v1', no_http=False):
  return apis.GetClientInstance('ml', version, no_http=no_http)


class VersionsClient(object):
  """Client for the versions service of Cloud ML Engine."""

  _ALLOWED_YAML_FIELDS = frozenset([
      'autoScaling',
      'deploymentUri',
      'description',
      'framework',
      'labels',
      'machineType',
      'manualScaling',
      'packageUris',
      'predictionClass',
      'pythonVersion',
      'runtimeVersion',
      'serviceAccount',
  ])

  _CONTAINER_FIELDS = frozenset([
      'container',
      'routes',
  ])

  def __init__(self, client=None, messages=None):
    self.client = client or GetClientInstance()
    self.messages = messages or self.client.MESSAGES_MODULE

  @property
  def version_class(self):
    return self.messages.GoogleCloudMlV1Version

  def _MakeCreateRequest(self, parent, version):
    return self.messages.MlProjectsModelsVersionsCreateRequest(
        parent=parent,
        googleCloudMlV1Version=version)

  def _MakeSetDefaultRequest(self, name):
    request = self.messages.GoogleCloudMlV1SetDefaultVersionRequest()
    return self.messages.MlProjectsModelsVersionsSetDefaultRequest(
        name=name,
        googleCloudMlV1SetDefaultVersionRequest=request)

  def Create(self, model_ref, version):
    """Creates a new version in an existing model."""
    return self.client.projects_models_versions.Create(
        self._MakeCreateRequest(
            parent=model_ref.RelativeName(),
            version=version))

  def Patch(self, version_ref, labels_update, description=None,
            prediction_class_update=None, package_uris=None,
            manual_scaling_nodes=None, auto_scaling_min_nodes=None,
            auto_scaling_max_nodes=None, sampling_percentage=None,
            bigquery_table_name=None):
    """Update a version."""
    version = self.messages.GoogleCloudMlV1Version()
    update_mask = []
    if labels_update.needs_update:
      version.labels = labels_update.labels
      update_mask.append('labels')

    if description:
      version.description = description
      update_mask.append('description')

    if prediction_class_update is not None and prediction_class_update.needs_update:
      update_mask.append('predictionClass')
      version.predictionClass = prediction_class_update.value

    if package_uris is not None:
      update_mask.append('packageUris')
      version.packageUris = package_uris

    if manual_scaling_nodes is not None:
      update_mask.append('manualScaling.nodes')
      version.manualScaling = self.messages.GoogleCloudMlV1ManualScaling(
          nodes=manual_scaling_nodes)

    if auto_scaling_min_nodes is not None:
      update_mask.append('autoScaling.minNodes')
      version.autoScaling = self.messages.GoogleCloudMlV1AutoScaling(
          minNodes=auto_scaling_min_nodes)

    if auto_scaling_max_nodes is not None:
      update_mask.append('autoScaling.maxNodes')
      if version.autoScaling is not None:
        version.autoScaling.maxNodes = auto_scaling_max_nodes
      else:
        version.autoScaling = self.messages.GoogleCloudMlV1AutoScaling(
            maxNodes=auto_scaling_max_nodes)

    if bigquery_table_name is not None:
      update_mask.append('requestLoggingConfig')
      version.requestLoggingConfig = self.messages.GoogleCloudMlV1RequestLoggingConfig(
          bigqueryTableName=bigquery_table_name)

    if sampling_percentage is not None:
      if 'requestLoggingConfig' not in update_mask:
        update_mask.append('requestLoggingConfig')
        version.requestLoggingConfig = self.messages.GoogleCloudMlV1RequestLoggingConfig(
            samplingPercentage=sampling_percentage)
      else:
        version.requestLoggingConfig.samplingPercentage = sampling_percentage

    if not update_mask:
      raise NoFieldsSpecifiedError('No updates requested.')

    return self.client.projects_models_versions.Patch(
        self.messages.MlProjectsModelsVersionsPatchRequest(
            name=version_ref.RelativeName(),
            googleCloudMlV1Version=version,
            updateMask=','.join(sorted(update_mask))))

  def Delete(self, version_ref):
    """Deletes a version from a model."""
    return self.client.projects_models_versions.Delete(
        self.messages.MlProjectsModelsVersionsDeleteRequest(
            name=version_ref.RelativeName()))

  def Get(self, version_ref):
    """Gets details about an existing model version."""
    return self.client.projects_models_versions.Get(
        self.messages.MlProjectsModelsVersionsGetRequest(
            name=version_ref.RelativeName()))

  def List(self, model_ref):
    """Lists the versions for a model."""
    list_request = self.messages.MlProjectsModelsVersionsListRequest(
        parent=model_ref.RelativeName())
    return list_pager.YieldFromList(
        self.client.projects_models_versions, list_request,
        field='versions', batch_size_attribute='pageSize')

  def SetDefault(self, version_ref):
    """Sets a model's default version."""
    return self.client.projects_models_versions.SetDefault(
        self._MakeSetDefaultRequest(name=version_ref.RelativeName()))

  def ReadConfig(self, path, allowed_fields):
    """Read a config file and return Version object with the values.

    The object is based on a YAML configuration file. The file may only
    have the fields given in `allowed_fields`.

    Args:
      path: str, the path to the YAML file.
      allowed_fields: Collection, the fields allowed in the YAML.

    Returns:
      A Version object (for the corresponding API version).

    Raises:
      InvalidVersionConfigFile: If the file contains unexpected fields.
    """
    try:
      data = yaml.load_path(path)
    except (yaml.Error) as err:
      raise InvalidVersionConfigFile(
          'Could not read Version configuration file [{path}]:\n\n'
          '{err}'.format(path=path, err=six.text_type(err.inner_error)))
    if data:
      version = encoding.DictToMessage(data, self.version_class)

    specified_fields = set([f.name for f in version.all_fields() if
                            getattr(version, f.name)])
    invalid_fields = (specified_fields - allowed_fields |
                      set(version.all_unrecognized_fields()))
    if invalid_fields:
      raise InvalidVersionConfigFile(
          'Invalid {noun} [{fields}] in configuration file [{path}]. '
          'Allowed fields: [{allowed}].'.format(
              noun=text.Pluralize(len(invalid_fields), 'field'),
              fields=', '.join(sorted(invalid_fields)),
              path=path,
              allowed=', '.join(sorted(allowed_fields))))
    return version

  def _ConfigureContainer(self, version, **kwargs):
    """Adds `container` and `routes` fields to version."""
    if not any(kwargs.values()):
      # Nothing related to containers was specified!
      return

    if not kwargs['image']:  # Implied from above: some other parameter is set!
      set_flags = ', '.join(
          ['--{}'.format(k) for k, v in sorted(kwargs.items()) if v])
      raise ValueError(
          '--image was not provided, but other container related flags were '
          'specified. Please specify --image or remove the following flags: '
          '{}'.format(set_flags))

    version.container = self.messages.GoogleCloudMlV1ContainerSpec(
        image=kwargs['image'])
    if kwargs['command']:
      version.container.command = kwargs['command']
    if kwargs['args']:
      version.container.args = kwargs['args']
    if kwargs['env_vars']:
      version.container.env = [
          self.messages.GoogleCloudMlV1EnvVar(name=name, value=value)
          for name, value in kwargs['env_vars'].items()]
    if kwargs['ports']:
      version.container.ports = [
          self.messages.GoogleCloudMlV1ContainerPort(containerPort=p)
          for p in kwargs['ports']
      ]

    if kwargs['predict_route'] or kwargs['health_route']:
      version.routes = self.messages.GoogleCloudMlV1RouteMap(
          predict=kwargs['predict_route'],
          health=kwargs['health_route']
      )

  def _ConfigureAutoScaling(self, version, **kwargs):
    """Adds `auto_scaling` fields to version."""
    if not any(kwargs.values()):
      # Nothing related to containers was specified!
      return

    version.autoScaling = self.messages.GoogleCloudMlV1AutoScaling()
    if kwargs['min_nodes']:
      version.autoScaling.minNodes = kwargs['min_nodes']
    if kwargs['max_nodes']:
      version.autoScaling.maxNodes = kwargs['max_nodes']
    if kwargs['metrics']:
      version.autoScaling.metrics = []
      if 'cpu-usage' in kwargs['metrics']:
        t = int(kwargs['metrics']['cpu-usage'])
        version.autoScaling.metrics.append(
            self.messages.GoogleCloudMlV1MetricSpec(
                name=self.messages.GoogleCloudMlV1MetricSpec.NameValueValuesEnum
                .CPU_USAGE,
                target=t))
      if 'gpu-duty-cycle' in kwargs['metrics']:
        t = int(kwargs['metrics']['gpu-duty-cycle'])
        version.autoScaling.metrics.append(
            self.messages.GoogleCloudMlV1MetricSpec(
                name=self.messages.GoogleCloudMlV1MetricSpec.NameValueValuesEnum
                .GPU_DUTY_CYCLE,
                target=t))

  def BuildVersion(self,
                   name,
                   path=None,
                   deployment_uri=None,
                   runtime_version=None,
                   labels=None,
                   machine_type=None,
                   description=None,
                   framework=None,
                   python_version=None,
                   prediction_class=None,
                   package_uris=None,
                   accelerator_config=None,
                   service_account=None,
                   explanation_method=None,
                   num_integral_steps=None,
                   num_paths=None,
                   image=None,
                   command=None,
                   container_args=None,
                   env_vars=None,
                   ports=None,
                   predict_route=None,
                   health_route=None,
                   min_nodes=None,
                   max_nodes=None,
                   metrics=None,
                   containers_hidden=True,
                   autoscaling_hidden=True):
    """Create a Version object.

    The object is based on an optional YAML configuration file and the
    parameters to this method; any provided method parameters override any
    provided in-file configuration.

    The file may only have the fields given in
    VersionsClientBase._ALLOWED_YAML_FIELDS specified; the only parameters
    allowed are those that can be specified on the command line.

    Args:
      name: str, the name of the version object to create.
      path: str, the path to the YAML file.
      deployment_uri: str, the deploymentUri to set for the Version
      runtime_version: str, the runtimeVersion to set for the Version
      labels: Version.LabelsValue, the labels to set for the version
      machine_type: str, the machine type to serve the model version on.
      description: str, the version description.
      framework: FrameworkValueValuesEnum, the ML framework used to train this
        version of the model.
      python_version: str, The version of Python used to train the model.
      prediction_class: str, the FQN of a Python class implementing the Model
        interface for custom prediction.
      package_uris: list of str, Cloud Storage URIs containing user-supplied
        Python code to use.
      accelerator_config: an accelerator config message object.
      service_account: Specifies the service account for resource access
        control.
      explanation_method: Enables explanations and selects the explanation
        method. Valid options are 'integrated-gradients' and 'sampled-shapley'.
      num_integral_steps: Number of integral steps for Integrated Gradients and
        XRAI.
      num_paths: Number of paths for Sampled Shapley.
      image: The container image to deploy.
      command: Entrypoint for the container image.
      container_args: The command-line args to pass the container.
      env_vars: The environment variables to set on the container.
      ports: The ports to which traffic will be sent in the container.
      predict_route: The HTTP path within the container that predict requests
        are sent to.
      health_route: The HTTP path within the container that health checks are
        sent to.
      min_nodes: The minimum number of nodes to scale this model under load.
      max_nodes: The maximum number of nodes to scale this model under load.
      metrics: List of key-value pairs to set as metrics' target for
        autoscaling.
      containers_hidden: Whether or not container-related fields are hidden on
        this track.
      autoscaling_hidden: Whether or not autoscaling fields are hidden on this
        track.

    Returns:
      A Version object (for the corresponding API version).

    Raises:
      InvalidVersionConfigFile: If the file contains unexpected fields.
    """
    if path:
      allowed_fields = self._ALLOWED_YAML_FIELDS
      if not containers_hidden:
        allowed_fields |= self._CONTAINER_FIELDS
      version = self.ReadConfig(path, allowed_fields)
    else:
      version = self.version_class()

    additional_fields = {
        'name': name,
        'deploymentUri': deployment_uri,
        'runtimeVersion': runtime_version,
        'labels': labels,
        'machineType': machine_type,
        'description': description,
        'framework': framework,
        'pythonVersion': python_version,
        'predictionClass': prediction_class,
        'packageUris': package_uris,
        'acceleratorConfig': accelerator_config,
        'serviceAccount': service_account
    }

    explanation_config = None
    if explanation_method == 'integrated-gradients':
      explanation_config = self.messages.GoogleCloudMlV1ExplanationConfig()
      ig_config = self.messages.GoogleCloudMlV1IntegratedGradientsAttribution()
      ig_config.numIntegralSteps = num_integral_steps
      explanation_config.integratedGradientsAttribution = ig_config
    elif explanation_method == 'sampled-shapley':
      explanation_config = self.messages.GoogleCloudMlV1ExplanationConfig()
      shap_config = self.messages.GoogleCloudMlV1SampledShapleyAttribution()
      shap_config.numPaths = num_paths
      explanation_config.sampledShapleyAttribution = shap_config
    elif explanation_method == 'xrai':
      explanation_config = self.messages.GoogleCloudMlV1ExplanationConfig()
      xrai_config = self.messages.GoogleCloudMlV1XraiAttribution()
      xrai_config.numIntegralSteps = num_integral_steps
      explanation_config.xraiAttribution = xrai_config

    if explanation_config is not None:
      additional_fields['explanationConfig'] = explanation_config

    if not containers_hidden:
      self._ConfigureContainer(
          version,
          image=image,
          command=command,
          args=container_args,
          env_vars=env_vars,
          ports=ports,
          predict_route=predict_route,
          health_route=health_route)

    if not autoscaling_hidden:
      self._ConfigureAutoScaling(
          version, min_nodes=min_nodes, max_nodes=max_nodes, metrics=metrics)

    for field_name, value in additional_fields.items():
      if value is not None:
        setattr(version, field_name, value)

    return version
