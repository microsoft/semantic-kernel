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
"""Utilities for AI Platform models API."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import list_pager
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.ai import constants


class ModelsClient(object):
  """High-level client for the AI Platform models surface.

  Attributes:
    client: An instance of the given client, or the API client aiplatform of
      Beta version.
    messages: The messages module for the given client, or the API client
      aiplatform of Beta version.
  """

  def __init__(self, client=None, messages=None):
    self.client = client or apis.GetClientInstance(
        constants.AI_PLATFORM_API_NAME,
        constants.AI_PLATFORM_API_VERSION[constants.BETA_VERSION])
    self.messages = messages or self.client.MESSAGES_MODULE
    self._service = self.client.projects_locations_models

  def UploadV1Beta1(self,
                    region_ref=None,
                    display_name=None,
                    description=None,
                    version_description=None,
                    artifact_uri=None,
                    container_image_uri=None,
                    container_command=None,
                    container_args=None,
                    container_env_vars=None,
                    container_ports=None,
                    container_grpc_ports=None,
                    container_predict_route=None,
                    container_health_route=None,
                    container_deployment_timeout_seconds=None,
                    container_shared_memory_size_mb=None,
                    container_startup_probe_exec=None,
                    container_startup_probe_period_seconds=None,
                    container_startup_probe_timeout_seconds=None,
                    container_health_probe_exec=None,
                    container_health_probe_period_seconds=None,
                    container_health_probe_timeout_seconds=None,
                    explanation_spec=None,
                    parent_model=None,
                    model_id=None,
                    version_aliases=None,
                    labels=None):
    """Constructs, sends an UploadModel request and returns the LRO to be done.

    Args:
      region_ref: The resource reference for a given region. None if the region
        reference is not provided.
      display_name: The display name of the Model. The name can be up to 128
        characters long and can be consist of any UTF-8 characters.
      description: The description of the Model.
      version_description: The description of the Model version.
      artifact_uri: The path to the directory containing the Model artifact and
        any of its supporting files. Not present for AutoML Models.
      container_image_uri: Immutable. URI of the Docker image to be used as the
        custom container for serving predictions. This URI must identify an
        image in Artifact Registry or Container Registry. Learn more about the
        [container publishing requirements](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#publishing), including
        permissions requirements for the Vertex AI Service Agent. The container
        image is ingested upon ModelService.UploadModel, stored internally, and
        this original path is afterwards not used. To learn about the
        requirements for the Docker image itself, see [Custom container
        requirements](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#). You can use the URI
        to one of Vertex AI's [pre-built container images for
        prediction](https://cloud.google.com/vertex-ai/docs/predictions/pre-
        built-containers) in this field.
      container_command: Specifies the command that runs when the container
        starts. This overrides the container's [ENTRYPOINT](https://docs.docker.
        com/engine/reference/builder/#entrypoint). Specify this field as an
        array of executable and arguments, similar to a Docker `ENTRYPOINT`'s
        "exec" form, not its "shell" form. If you do not specify this field,
        then the container's `ENTRYPOINT` runs, in conjunction with the args
        field or the container's
        [`CMD`](https://docs.docker.com/engine/reference/builder/#cmd), if
        either exists. If this field is not specified and the container does not
        have an `ENTRYPOINT`, then refer to the Docker documentation about [how
        `CMD` and `ENTRYPOINT`
        interact](https://docs.docker.com/engine/reference/builder/#understand-
        how-cmd-and-entrypoint-interact). If you specify this field, then you
        can also specify the `args` field to provide additional arguments for
        this command. However, if you specify this field, then the container's
        `CMD` is ignored. See the [Kubernetes documentation about how the
        `command` and `args` fields interact with a container's `ENTRYPOINT` and
        `CMD`](https://kubernetes.io/docs/tasks/inject-data-application/define-
        command-argument-container/#notes). In this field, you can reference
        [environment variables set by Vertex
        AI](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables) and environment variables set in
        the env field. You cannot reference environment variables set in the
        Docker image. In order for environment variables to be expanded,
        reference them by using the following syntax: $( VARIABLE_NAME) Note
        that this differs from Bash variable expansion, which does not use
        parentheses. If a variable cannot be resolved, the reference in the
        input string is used unchanged. To avoid variable expansion, you can
        escape this syntax with `$$`; for example: $$(VARIABLE_NAME) This field
        corresponds to the `command` field of the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_args: Specifies arguments for the command that runs when the
        container starts. This overrides the container's
        [`CMD`](https://docs.docker.com/engine/reference/builder/#cmd). Specify
        this field as an array of executable and arguments, similar to a Docker
        `CMD`'s "default parameters" form. If you don't specify this field but
        do specify the command field, then the command from the `command` field
        runs without any additional arguments. See the [Kubernetes documentation
        about how the `command` and `args` fields interact with a container's
        `ENTRYPOINT` and `CMD`](https://kubernetes.io/docs/tasks/inject-data-
        application/define-command-argument-container/#notes). If you don't
        specify this field and don't specify the `command` field, then the
        container's
        [`ENTRYPOINT`](https://docs.docker.com/engine/reference/builder/#cmd)
        and `CMD` determine what runs based on their default behavior. See the
        Docker documentation about [how `CMD` and `ENTRYPOINT`
        interact](https://docs.docker.com/engine/reference/builder/#understand-
        how-cmd-and-entrypoint-interact). In this field, you can reference
        [environment variables set by Vertex
        AI](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables) and environment variables set in
        the env field. You cannot reference environment variables set in the
        Docker image. In order for environment variables to be expanded,
        reference them by using the following syntax: $( VARIABLE_NAME) Note
        that this differs from Bash variable expansion, which does not use
        parentheses. If a variable cannot be resolved, the reference in the
        input string is used unchanged. To avoid variable expansion, you can
        escape this syntax with `$$`; for example: $$(VARIABLE_NAME) This field
        corresponds to the `args` field of the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core)..
      container_env_vars: List of environment variables to set in the container.
        After the container starts running, code running in the container can
        read these environment variables. Additionally, the command and args
        fields can reference these variables. Later entries in this list can
        also reference earlier entries. For example, the following example sets
        the variable `VAR_2` to have the value `foo bar`: ```json [ { "name":
        "VAR_1", "value": "foo" }, { "name": "VAR_2", "value": "$(VAR_1) bar" }
        ] ``` If you switch the order of the variables in the example, then the
        expansion does not occur. This field corresponds to the `env` field of
        the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_ports: List of ports to expose from the container. Vertex AI
        sends any http prediction requests that it receives to the first port on
        this list. Vertex AI also sends [liveness and health
        checks](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#liveness) to this port. If you do not specify
        this field, it defaults to following value: ```json [ { "containerPort":
        8080 } ] ``` Vertex AI does not use ports other than the first one
        listed. This field corresponds to the `ports` field of the Kubernetes
        Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_grpc_ports: List of ports to expose from the container. Vertex
        AI sends any grpc prediction requests that it receives to the first port
        on this list. Vertex AI also sends [liveness and health
        checks](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#liveness) to this port. If you do not specify
        this field, gRPC requests to the container will be disabled. Vertex AI
        does not use ports other than the first one listed. This field
        corresponds to the `ports` field of the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_predict_route: HTTP path on the container to send prediction
        requests to. Vertex AI forwards requests sent using
        projects.locations.endpoints.predict to this path on the container's IP
        address and port. Vertex AI then returns the container's response in the
        API response. For example, if you set this field to `/foo`, then when
        Vertex AI receives a prediction request, it forwards the request body in
        a POST request to the `/foo` path on the port of your container
        specified by the first value of this `ModelContainerSpec`'s ports field.
        If you don't specify this field, it defaults to the following value when
        you deploy this Model to an Endpoint:
        /v1/endpoints/ENDPOINT/deployedModels/DEPLOYED_MODEL:predict The
        placeholders in this value are replaced as follows: * ENDPOINT: The last
        segment (following `endpoints/`)of the Endpoint.name][] field of the
        Endpoint where this Model has been deployed. (Vertex AI makes this value
        available to your container code as the [`AIP_ENDPOINT_ID` environment
        variable](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables).) * DEPLOYED_MODEL:
        DeployedModel.id of the `DeployedModel`. (Vertex AI makes this value
        available to your container code as the [`AIP_DEPLOYED_MODEL_ID`
        environment variable](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#aip-variables).)
      container_health_route: HTTP path on the container to send health checks
        to. Vertex AI intermittently sends GET requests to this path on the
        container's IP address and port to check that the container is healthy.
        Read more about [health checks](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#health). For example,
        if you set this field to `/bar`, then Vertex AI intermittently sends a
        GET request to the `/bar` path on the port of your container specified
        by the first value of this `ModelContainerSpec`'s ports field. If you
        don't specify this field, it defaults to the following value when you
        deploy this Model to an Endpoint: /v1/endpoints/ENDPOINT/deployedModels/
        DEPLOYED_MODEL:predict The placeholders in this value are replaced as
        follows * ENDPOINT: The last segment (following `endpoints/`)of the
        Endpoint.name][] field of the Endpoint where this Model has been
        deployed. (Vertex AI makes this value available to your container code
        as the [`AIP_ENDPOINT_ID` environment
        variable](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables).) * DEPLOYED_MODEL:
        DeployedModel.id of the `DeployedModel`. (Vertex AI makes this value
        available to your container code as the [`AIP_DEPLOYED_MODEL_ID`
        environment variable](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#aip-variables).)
      container_deployment_timeout_seconds (int): Deployment timeout in seconds.
      container_shared_memory_size_mb (int): The amount of the VM memory to
        reserve as the shared memory for the model in megabytes.
      container_startup_probe_exec (Sequence[str]): Exec specifies the action to
        take. Used by startup probe. An example of this argument would be
        ["cat", "/tmp/healthy"]
      container_startup_probe_period_seconds (int): How often (in seconds) to
        perform the startup probe. Default to 10 seconds. Minimum value is 1.
      container_startup_probe_timeout_seconds (int): Number of seconds after
        which the startup probe times out. Defaults to 1 second. Minimum value
        is 1.
      container_health_probe_exec (Sequence[str]): Exec specifies the action to
        take. Used by health probe. An example of this argument would be ["cat",
        "/tmp/healthy"]
      container_health_probe_period_seconds (int): How often (in seconds) to
        perform the health probe. Default to 10 seconds. Minimum value is 1.
      container_health_probe_timeout_seconds (int): Number of seconds after
        which the health probe times out. Defaults to 1 second. Minimum value is
        1.
      explanation_spec: The default explanation specification for this Model.
        The Model can be used for requesting explanation after being deployed if
        it is populated. The Model can be used for batch explanation if it is
        populated. All fields of the explanation_spec can be overridden by
        explanation_spec of DeployModelRequest.deployed_model, or
        explanation_spec of BatchPredictionJob. If the default explanation
        specification is not set for this Model, this Model can still be used
        for requesting explanation by setting explanation_spec of
        DeployModelRequest.deployed_model and for batch explanation by setting
        explanation_spec of BatchPredictionJob.
      parent_model: The resource name of the model into which to upload the
        version. Only specify this field when uploading a new version.
      model_id: The ID to use for the uploaded Model, which will become the
        final component of the model resource name. This value may be up to 63
        characters, and valid characters are `[a-z0-9_-]`. The first character
        cannot be a number or hyphen..
      version_aliases: User provided version aliases so that a model version can
        be referenced via alias (i.e. projects/{project}/locations/{location}/mo
        dels/{model_id}@{version_alias} instead of auto-generated version id
        (i.e.
        projects/{project}/locations/{location}/models/{model_id}@{version_id}).
        The format is a-z{0,126}[a-z0-9] to distinguish from version_id. A
        default version alias will be created for the first version of the
        model, and there must be exactly one default version alias for a model.
      labels: The labels with user-defined metadata to organize your Models.
        Label keys and values can be no longer than 64 characters (Unicode
        codepoints), can only contain lowercase letters, numeric characters,
        underscores and dashes. International characters are allowed. See
        https://goo.gl/xmQnxf for more information and examples of labels.

    Returns:
      Response from calling upload model with given request arguments.
    """
    container_spec = (
        self.messages.GoogleCloudAiplatformV1beta1ModelContainerSpec(
            healthRoute=container_health_route,
            imageUri=container_image_uri,
            predictRoute=container_predict_route,
        )
    )
    if container_command:
      container_spec.command = container_command
    if container_args:
      container_spec.args = container_args
    if container_env_vars:
      container_spec.env = [
          self.messages.GoogleCloudAiplatformV1beta1EnvVar(
              name=k, value=container_env_vars[k]) for k in container_env_vars
      ]
    if container_ports:
      container_spec.ports = [
          self.messages.GoogleCloudAiplatformV1beta1Port(containerPort=port)
          for port in container_ports
      ]
    if container_grpc_ports:
      container_spec.grpcPorts = [
          self.messages.GoogleCloudAiplatformV1beta1Port(containerPort=port)
          for port in container_grpc_ports
      ]
    if container_deployment_timeout_seconds:
      container_spec.deploymentTimeout = (
          str(container_deployment_timeout_seconds) + 's'
      )
    if container_shared_memory_size_mb:
      container_spec.sharedMemorySizeMb = container_shared_memory_size_mb
    if (
        container_startup_probe_exec
        or container_startup_probe_period_seconds
        or container_startup_probe_timeout_seconds
    ):
      startup_probe_exec = None
      if container_startup_probe_exec:
        startup_probe_exec = (
            self.messages.GoogleCloudAiplatformV1beta1ProbeExecAction(
                command=container_startup_probe_exec
            )
        )
      container_spec.startupProbe = (
          self.messages.GoogleCloudAiplatformV1beta1Probe(
              exec_=startup_probe_exec,
              periodSeconds=container_startup_probe_period_seconds,
              timeoutSeconds=container_startup_probe_timeout_seconds,
          )
      )
    if (
        container_health_probe_exec
        or container_health_probe_period_seconds
        or container_health_probe_timeout_seconds
    ):
      health_probe_exec = None
      if container_health_probe_exec:
        health_probe_exec = (
            self.messages.GoogleCloudAiplatformV1beta1ProbeExecAction(
                command=container_health_probe_exec
            )
        )
      container_spec.healthProbe = (
          self.messages.GoogleCloudAiplatformV1beta1Probe(
              exec_=health_probe_exec,
              periodSeconds=container_health_probe_period_seconds,
              timeoutSeconds=container_health_probe_timeout_seconds,
          )
      )

    model = self.messages.GoogleCloudAiplatformV1beta1Model(
        artifactUri=artifact_uri,
        containerSpec=container_spec,
        description=description,
        versionDescription=version_description,
        displayName=display_name,
        explanationSpec=explanation_spec)
    if version_aliases:
      model.versionAliases = version_aliases
    if labels:
      additional_properties = []
      for key, value in sorted(labels.items()):
        additional_properties.append(model.LabelsValue().AdditionalProperty(
            key=key, value=value))
      model.labels = model.LabelsValue(
          additionalProperties=additional_properties)

    return self._service.Upload(
        self.messages.AiplatformProjectsLocationsModelsUploadRequest(
            parent=region_ref.RelativeName(),
            googleCloudAiplatformV1beta1UploadModelRequest=self.messages
            .GoogleCloudAiplatformV1beta1UploadModelRequest(
                model=model,
                parentModel=parent_model,
                modelId=model_id)))

  def UploadV1(self,
               region_ref=None,
               display_name=None,
               description=None,
               version_description=None,
               artifact_uri=None,
               container_image_uri=None,
               container_command=None,
               container_args=None,
               container_env_vars=None,
               container_ports=None,
               container_grpc_ports=None,
               container_predict_route=None,
               container_health_route=None,
               container_deployment_timeout_seconds=None,
               container_shared_memory_size_mb=None,
               container_startup_probe_exec=None,
               container_startup_probe_period_seconds=None,
               container_startup_probe_timeout_seconds=None,
               container_health_probe_exec=None,
               container_health_probe_period_seconds=None,
               container_health_probe_timeout_seconds=None,
               explanation_spec=None,
               parent_model=None,
               model_id=None,
               version_aliases=None,
               labels=None):
    """Constructs, sends an UploadModel request and returns the LRO to be done.

    Args:
      region_ref: The resource reference for a given region. None if the region
        reference is not provided.
      display_name: The display name of the Model. The name can be up to 128
        characters long and can be consist of any UTF-8 characters.
      description: The description of the Model.
      version_description: The description of the Model version.
      artifact_uri: The path to the directory containing the Model artifact and
        any of its supporting files. Not present for AutoML Models.
      container_image_uri: Immutable. URI of the Docker image to be used as the
        custom container for serving predictions. This URI must identify an
        image in Artifact Registry or Container Registry. Learn more about the
        [container publishing requirements](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#publishing), including
        permissions requirements for the Vertex AI Service Agent. The container
        image is ingested upon ModelService.UploadModel, stored internally, and
        this original path is afterwards not used. To learn about the
        requirements for the Docker image itself, see [Custom container
        requirements](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#). You can use the URI
        to one of Vertex AI's [pre-built container images for
        prediction](https://cloud.google.com/vertex-ai/docs/predictions/pre-
        built-containers) in this field.
      container_command: Specifies the command that runs when the container
        starts. This overrides the container's [ENTRYPOINT](https://docs.docker.
        com/engine/reference/builder/#entrypoint). Specify this field as an
        array of executable and arguments, similar to a Docker `ENTRYPOINT`'s
        "exec" form, not its "shell" form. If you do not specify this field,
        then the container's `ENTRYPOINT` runs, in conjunction with the args
        field or the container's
        [`CMD`](https://docs.docker.com/engine/reference/builder/#cmd), if
        either exists. If this field is not specified and the container does not
        have an `ENTRYPOINT`, then refer to the Docker documentation about [how
        `CMD` and `ENTRYPOINT`
        interact](https://docs.docker.com/engine/reference/builder/#understand-
        how-cmd-and-entrypoint-interact). If you specify this field, then you
        can also specify the `args` field to provide additional arguments for
        this command. However, if you specify this field, then the container's
        `CMD` is ignored. See the [Kubernetes documentation about how the
        `command` and `args` fields interact with a container's `ENTRYPOINT` and
        `CMD`](https://kubernetes.io/docs/tasks/inject-data-application/define-
        command-argument-container/#notes). In this field, you can reference
        [environment variables set by Vertex
        AI](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables) and environment variables set in
        the env field. You cannot reference environment variables set in the
        Docker image. In order for environment variables to be expanded,
        reference them by using the following syntax: $( VARIABLE_NAME) Note
        that this differs from Bash variable expansion, which does not use
        parentheses. If a variable cannot be resolved, the reference in the
        input string is used unchanged. To avoid variable expansion, you can
        escape this syntax with `$$`; for example: $$(VARIABLE_NAME) This field
        corresponds to the `command` field of the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_args: Specifies arguments for the command that runs when the
        container starts. This overrides the container's
        [`CMD`](https://docs.docker.com/engine/reference/builder/#cmd). Specify
        this field as an array of executable and arguments, similar to a Docker
        `CMD`'s "default parameters" form. If you don't specify this field but
        do specify the command field, then the command from the `command` field
        runs without any additional arguments. See the [Kubernetes documentation
        about how the `command` and `args` fields interact with a container's
        `ENTRYPOINT` and `CMD`](https://kubernetes.io/docs/tasks/inject-data-
        application/define-command-argument-container/#notes). If you don't
        specify this field and don't specify the `command` field, then the
        container's
        [`ENTRYPOINT`](https://docs.docker.com/engine/reference/builder/#cmd)
        and `CMD` determine what runs based on their default behavior. See the
        Docker documentation about [how `CMD` and `ENTRYPOINT`
        interact](https://docs.docker.com/engine/reference/builder/#understand-
        how-cmd-and-entrypoint-interact). In this field, you can reference
        [environment variables set by Vertex
        AI](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables) and environment variables set in
        the env field. You cannot reference environment variables set in the
        Docker image. In order for environment variables to be expanded,
        reference them by using the following syntax: $( VARIABLE_NAME) Note
        that this differs from Bash variable expansion, which does not use
        parentheses. If a variable cannot be resolved, the reference in the
        input string is used unchanged. To avoid variable expansion, you can
        escape this syntax with `$$`; for example: $$(VARIABLE_NAME) This field
        corresponds to the `args` field of the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core)..
      container_env_vars: List of environment variables to set in the container.
        After the container starts running, code running in the container can
        read these environment variables. Additionally, the command and args
        fields can reference these variables. Later entries in this list can
        also reference earlier entries. For example, the following example sets
        the variable `VAR_2` to have the value `foo bar`: ```json [ { "name":
        "VAR_1", "value": "foo" }, { "name": "VAR_2", "value": "$(VAR_1) bar" }
        ] ``` If you switch the order of the variables in the example, then the
        expansion does not occur. This field corresponds to the `env` field of
        the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_ports: List of ports to expose from the container. Vertex AI
        sends any http prediction requests that it receives to the first port on
        this list. Vertex AI also sends [liveness and health
        checks](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#liveness) to this port. If you do not specify
        this field, it defaults to following value: ```json [ { "containerPort":
        8080 } ] ``` Vertex AI does not use ports other than the first one
        listed. This field corresponds to the `ports` field of the Kubernetes
        Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_grpc_ports: List of ports to expose from the container. Vertex
        AI sends any grpc prediction requests that it receives to the first port
        on this list. Vertex AI also sends [liveness and health
        checks](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#liveness) to this port. If you do not specify
        this field, gRPC requests to the container will be disabled. Vertex AI
        does not use ports other than the first one listed. This field
        corresponds to the `ports` field of the Kubernetes Containers [v1 core
        API](https://kubernetes.io/docs/reference/generated/kubernetes-
        api/v1.23/#container-v1-core).
      container_predict_route: HTTP path on the container to send prediction
        requests to. Vertex AI forwards requests sent using
        projects.locations.endpoints.predict to this path on the container's IP
        address and port. Vertex AI then returns the container's response in the
        API response. For example, if you set this field to `/foo`, then when
        Vertex AI receives a prediction request, it forwards the request body in
        a POST request to the `/foo` path on the port of your container
        specified by the first value of this `ModelContainerSpec`'s ports field.
        If you don't specify this field, it defaults to the following value when
        you deploy this Model to an Endpoint:
        /v1/endpoints/ENDPOINT/deployedModels/DEPLOYED_MODEL:predict The
        placeholders in this value are replaced as follows: * ENDPOINT: The last
        segment (following `endpoints/`)of the Endpoint.name][] field of the
        Endpoint where this Model has been deployed. (Vertex AI makes this value
        available to your container code as the [`AIP_ENDPOINT_ID` environment
        variable](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables).) * DEPLOYED_MODEL:
        DeployedModel.id of the `DeployedModel`. (Vertex AI makes this value
        available to your container code as the [`AIP_DEPLOYED_MODEL_ID`
        environment variable](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#aip-variables).)
      container_health_route: HTTP path on the container to send health checks
        to. Vertex AI intermittently sends GET requests to this path on the
        container's IP address and port to check that the container is healthy.
        Read more about [health checks](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#health). For example,
        if you set this field to `/bar`, then Vertex AI intermittently sends a
        GET request to the `/bar` path on the port of your container specified
        by the first value of this `ModelContainerSpec`'s ports field. If you
        don't specify this field, it defaults to the following value when you
        deploy this Model to an Endpoint: /v1/endpoints/ENDPOINT/deployedModels/
        DEPLOYED_MODEL:predict The placeholders in this value are replaced as
        follows * ENDPOINT: The last segment (following `endpoints/`)of the
        Endpoint.name][] field of the Endpoint where this Model has been
        deployed. (Vertex AI makes this value available to your container code
        as the [`AIP_ENDPOINT_ID` environment
        variable](https://cloud.google.com/vertex-ai/docs/predictions/custom-
        container-requirements#aip-variables).) * DEPLOYED_MODEL:
        DeployedModel.id of the `DeployedModel`. (Vertex AI makes this value
        available to your container code as the [`AIP_DEPLOYED_MODEL_ID`
        environment variable](https://cloud.google.com/vertex-
        ai/docs/predictions/custom-container-requirements#aip-variables).)
      container_deployment_timeout_seconds (int): Deployment timeout in seconds.
      container_shared_memory_size_mb (int): The amount of the VM memory to
        reserve as the shared memory for the model in megabytes.
      container_startup_probe_exec (Sequence[str]): Exec specifies the action to
        take. Used by startup probe. An example of this argument would be
        ["cat", "/tmp/healthy"]
      container_startup_probe_period_seconds (int): How often (in seconds) to
        perform the startup probe. Default to 10 seconds. Minimum value is 1.
      container_startup_probe_timeout_seconds (int): Number of seconds after
        which the startup probe times out. Defaults to 1 second. Minimum value
        is 1.
      container_health_probe_exec (Sequence[str]): Exec specifies the action to
        take. Used by health probe. An example of this argument would be ["cat",
        "/tmp/healthy"]
      container_health_probe_period_seconds (int): How often (in seconds) to
        perform the health probe. Default to 10 seconds. Minimum value is 1.
      container_health_probe_timeout_seconds (int): Number of seconds after
        which the health probe times out. Defaults to 1 second. Minimum value is
        1.
      explanation_spec: The default explanation specification for this Model.
        The Model can be used for requesting explanation after being deployed if
        it is populated. The Model can be used for batch explanation if it is
        populated. All fields of the explanation_spec can be overridden by
        explanation_spec of DeployModelRequest.deployed_model, or
        explanation_spec of BatchPredictionJob. If the default explanation
        specification is not set for this Model, this Model can still be used
        for requesting explanation by setting explanation_spec of
        DeployModelRequest.deployed_model and for batch explanation by setting
        explanation_spec of BatchPredictionJob.
      parent_model: The resource name of the model into which to upload the
        version. Only specify this field when uploading a new version.
      model_id: The ID to use for the uploaded Model, which will become the
        final component of the model resource name. This value may be up to 63
        characters, and valid characters are `[a-z0-9_-]`. The first character
        cannot be a number or hyphen..
      version_aliases: User provided version aliases so that a model version can
        be referenced via alias (i.e. projects/{project}/locations/{location}/mo
        dels/{model_id}@{version_alias} instead of auto-generated version id
        (i.e.
        projects/{project}/locations/{location}/models/{model_id}@{version_id}).
        The format is a-z{0,126}[a-z0-9] to distinguish from version_id. A
        default version alias will be created for the first version of the
        model, and there must be exactly one default version alias for a model.
      labels: The labels with user-defined metadata to organize your Models.
        Label keys and values can be no longer than 64 characters (Unicode
        codepoints), can only contain lowercase letters, numeric characters,
        underscores and dashes. International characters are allowed. See
        https://goo.gl/xmQnxf for more information and examples of labels.

    Returns:
      Response from calling upload model with given request arguments.
    """
    container_spec = self.messages.GoogleCloudAiplatformV1ModelContainerSpec(
        healthRoute=container_health_route,
        imageUri=container_image_uri,
        predictRoute=container_predict_route)
    if container_command:
      container_spec.command = container_command
    if container_args:
      container_spec.args = container_args
    if container_env_vars:
      container_spec.env = [
          self.messages.GoogleCloudAiplatformV1EnvVar(
              name=k, value=container_env_vars[k]) for k in container_env_vars
      ]
    if container_ports:
      container_spec.ports = [
          self.messages.GoogleCloudAiplatformV1Port(containerPort=port)
          for port in container_ports
      ]
    if container_grpc_ports:
      container_spec.grpcPorts = [
          self.messages.GoogleCloudAiplatformV1Port(containerPort=port)
          for port in container_grpc_ports
      ]
    if container_deployment_timeout_seconds:
      container_spec.deploymentTimeout = (
          str(container_deployment_timeout_seconds) + 's'
      )
    if container_shared_memory_size_mb:
      container_spec.sharedMemorySizeMb = container_shared_memory_size_mb
    if (
        container_startup_probe_exec
        or container_startup_probe_period_seconds
        or container_startup_probe_timeout_seconds
    ):
      startup_probe_exec = None
      if container_startup_probe_exec:
        startup_probe_exec = (
            self.messages.GoogleCloudAiplatformV1ProbeExecAction(
                command=container_startup_probe_exec
            )
        )
      container_spec.startupProbe = (
          self.messages.GoogleCloudAiplatformV1Probe(
              exec_=startup_probe_exec,
              periodSeconds=container_startup_probe_period_seconds,
              timeoutSeconds=container_startup_probe_timeout_seconds,
          )
      )
    if (
        container_health_probe_exec
        or container_health_probe_period_seconds
        or container_health_probe_timeout_seconds
    ):
      health_probe_exec = None
      if container_health_probe_exec:
        health_probe_exec = (
            self.messages.GoogleCloudAiplatformV1ProbeExecAction(
                command=container_health_probe_exec
            )
        )
      container_spec.healthProbe = (
          self.messages.GoogleCloudAiplatformV1Probe(
              exec_=health_probe_exec,
              periodSeconds=container_health_probe_period_seconds,
              timeoutSeconds=container_health_probe_timeout_seconds,
          )
      )

    model = self.messages.GoogleCloudAiplatformV1Model(
        artifactUri=artifact_uri,
        containerSpec=container_spec,
        description=description,
        versionDescription=version_description,
        displayName=display_name,
        explanationSpec=explanation_spec)
    if version_aliases:
      model.versionAliases = version_aliases
    if labels:
      additional_properties = []
      for key, value in sorted(labels.items()):
        additional_properties.append(model.LabelsValue().AdditionalProperty(
            key=key, value=value))
      model.labels = model.LabelsValue(
          additionalProperties=additional_properties)

    return self._service.Upload(
        self.messages.AiplatformProjectsLocationsModelsUploadRequest(
            parent=region_ref.RelativeName(),
            googleCloudAiplatformV1UploadModelRequest=self.messages
            .GoogleCloudAiplatformV1UploadModelRequest(
                model=model,
                parentModel=parent_model,
                modelId=model_id)))

  def Get(self, model_ref):
    """Gets (describe) the given model.

    Args:
      model_ref: The resource reference for a given model. None if model
        resource reference is not provided.

    Returns:
      Response from calling get model with request containing given model.
    """
    request = self.messages.AiplatformProjectsLocationsModelsGetRequest(
        name=model_ref.RelativeName())
    return self._service.Get(request)

  def Delete(self, model_ref):
    """Deletes the given model.

    Args:
      model_ref: The resource reference for a given model. None if model
        resource reference is not provided.

    Returns:
      Response from calling delete model with request containing given model.
    """
    request = self.messages.AiplatformProjectsLocationsModelsDeleteRequest(
        name=model_ref.RelativeName())
    return self._service.Delete(request)

  def DeleteVersion(self, model_version_ref):
    """Deletes the given model version.

    Args:
      model_version_ref: The resource reference for a given model version.

    Returns:
      Response from calling delete version with request containing given model
      version.
    """
    request = (
        self.messages.AiplatformProjectsLocationsModelsDeleteVersionRequest(
            name=model_version_ref.RelativeName()
        )
    )
    return self._service.DeleteVersion(request)

  def List(self, limit=None, region_ref=None):
    """List all models in the given region.

    Args:
      limit: int, The maximum number of records to yield. None if all available
        records should be yielded.
      region_ref: The resource reference for a given region. None if the region
        reference is not provided.

    Returns:
      Response from calling list models with request containing given models
      and limit.
    """
    return list_pager.YieldFromList(
        self._service,
        self.messages.AiplatformProjectsLocationsModelsListRequest(
            parent=region_ref.RelativeName()),
        field='models',
        batch_size_attribute='pageSize',
        limit=limit)

  def ListVersion(self, model_ref=None, limit=None):
    """List all model versions of the given model.

    Args:
      model_ref: The resource reference for a given model. None if model
        resource reference is not provided.
      limit: int, The maximum number of records to yield. None if all available
        records should be yielded.

    Returns:
      Response from calling list model versions with request containing given
      model and limit.
    """
    return list_pager.YieldFromList(
        self._service,
        self.messages.AiplatformProjectsLocationsModelsListVersionsRequest(
            name=model_ref.RelativeName()),
        method='ListVersions',
        field='models',
        batch_size_attribute='pageSize',
        limit=limit)

  def CopyV1Beta1(self,
                  destination_region_ref=None,
                  source_model=None,
                  kms_key_name=None,
                  destination_model_id=None,
                  destination_parent_model=None):
    """Copies the given source model into specified location.

    The source model is copied into specified location (including cross-region)
    either as a new model or a new model version under given parent model.

    Args:
      destination_region_ref: the resource reference to the location into which
        to copy the Model.
      source_model: The resource name of the Model to copy.
      kms_key_name: The KMS key name for specifying encryption spec.
      destination_model_id: The destination model resource name to copy the
        model into.
      destination_parent_model: The destination parent model to copy the model
        as a model version into.

    Returns:
      Response from calling copy model.
    """
    encryption_spec = None
    if kms_key_name:
      encryption_spec = (
          self.messages.GoogleCloudAiplatformV1beta1EncryptionSpec(
              kmsKeyName=kms_key_name
          )
      )
    request = self.messages.AiplatformProjectsLocationsModelsCopyRequest(
        parent=destination_region_ref.RelativeName(),
        googleCloudAiplatformV1beta1CopyModelRequest=self.messages
        .GoogleCloudAiplatformV1beta1CopyModelRequest(
            sourceModel=source_model,
            encryptionSpec=encryption_spec,
            parentModel=destination_parent_model,
            modelId=destination_model_id))
    return self._service.Copy(request)

  def CopyV1(self,
             destination_region_ref=None,
             source_model=None,
             kms_key_name=None,
             destination_model_id=None,
             destination_parent_model=None):
    """Copies the given source model into specified location.

    The source model is copied into specified location (including cross-region)
    either as a new model or a new model version under given parent model.

    Args:
      destination_region_ref: the resource reference to the location into which
        to copy the Model.
      source_model: The resource name of the Model to copy.
      kms_key_name: The name of the KMS key to use for model encryption.
      destination_model_id: Optional. Thew custom ID to be used as the resource
        name of the new model. This value may be up to 63 characters, and valid
        characters are  `[a-z0-9_-]`. The first character cannot be a number or
        hyphen.
      destination_parent_model: The destination parent model to copy the model
        as a model version into.

    Returns:
      Response from calling copy model.
    """
    encryption_spec = None
    if kms_key_name:
      encryption_spec = (
          self.messages.GoogleCloudAiplatformV1EncryptionSpec(
              kmsKeyName=kms_key_name
          )
      )
    request = self.messages.AiplatformProjectsLocationsModelsCopyRequest(
        parent=destination_region_ref.RelativeName(),
        googleCloudAiplatformV1CopyModelRequest=self.messages
        .GoogleCloudAiplatformV1CopyModelRequest(
            sourceModel=source_model,
            encryptionSpec=encryption_spec,
            parentModel=destination_parent_model,
            modelId=destination_model_id))
    return self._service.Copy(request)
