# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import logging
from typing import Any, Literal

from pydantic import Field, SerializeAsAny
from pydantic.dataclasses import dataclass

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


@dataclass
class ConnectionStringAuthentication:
    type: Literal["ConnectionString"] = "ConnectionString"
    connectionString: str | None = None


@dataclass
class ApiKeyAuthentication:
    type: Literal["APIKey"] = "APIKey"
    key: str | None = None


@dataclass
class AzureEmbeddingDependency:
    type: Literal["DeploymentName"] = "DeploymentName"
    deploymentName: str | None = None


@dataclass
class AzureDataSourceParameters:
    indexName: str
    indexLanguage: str | None = None
    fieldsMapping: dict[str, Any] = Field(default_factory=dict)
    inScope: bool | None = True
    topNDocuments: int | None = 5
    semanticConfiguration: str | None = None
    roleInformation: str | None = None
    filter: str | None = None
    embeddingKey: str | None = None
    embeddingEndpoint: str | None = None
    embeddingDeploymentName: str | None = None
    strictness: int = 3
    embeddingDependency: AzureEmbeddingDependency | None = None


@dataclass
class AzureCosmosDBDataSource(AzureDataSourceParameters):
    authentication: ConnectionStringAuthentication | None = None
    databaseName: str | None = None
    containerName: str | None = None
    embeddingDependencyType: AzureEmbeddingDependency | None = None


@dataclass
class AzureAISearchDataSources(AzureDataSourceParameters):
    endpoint: str | None = None
    key: str | None = None
    queryType: Literal["simple", "semantic", "vector", "vectorSimpleHybrid", "vectorSemanticHybrid"] = "simple"
    authentication: ApiKeyAuthentication | None = None


@dataclass
class AzureDataSources:
    """Class to hold Azure AI data source parameters."""

    type: Literal["AzureCognitiveSearch", "AzureCosmosDB"] = "AzureCognitiveSearch"
    parameters: SerializeAsAny[AzureDataSourceParameters] | None = None


# @dataclass
class ExtraBody(KernelBaseModel):
    data_sources: list[AzureDataSources] | None = Field(None, alias="dataSources")
    input_language: str | None = Field(None, serialization_alias="inputLanguage")
    output_language: str | None = Field(None, serialization_alias="outputLanguage")

    def __getitem__(self, item):
        return getattr(self, item)


class AzureChatPromptExecutionSettings(OpenAIChatPromptExecutionSettings):
    """Specific settings for the Azure OpenAI Chat Completion endpoint."""

    response_format: str | None = None
    extra_body: dict[str | Any, ExtraBody] | None = None
