import logging
from typing import Any, Dict, List, Literal, Optional, Union

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
    connectionString: Optional[str] = None


@dataclass
class ApiKeyAuthentication:
    type: Literal["APIKey"] = "APIKey"
    key: Optional[str] = None


@dataclass
class AzureEmbeddingDependency:
    type: Literal["DeploymentName"] = "DeploymentName"
    deploymentName: Optional[str] = None


@dataclass
class AzureDataSourceParameters:
    indexName: str
    indexLanguage: Optional[str] = None
    fieldsMapping: Dict[str, Any] = Field(default_factory=dict)
    inScope: Optional[bool] = True
    topNDocuments: Optional[int] = 5
    semanticConfiguration: Optional[str] = None
    roleInformation: Optional[str] = None
    filter: Optional[str] = None
    embeddingKey: Optional[str] = None
    embeddingEndpoint: Optional[str] = None
    embeddingDeploymentName: Optional[str] = None
    strictness: int = 3
    embeddingDependency: Optional[AzureEmbeddingDependency] = None


@dataclass
class AzureCosmosDBDataSource(AzureDataSourceParameters):
    authentication: Optional[ConnectionStringAuthentication] = None
    databaseName: Optional[str] = None
    containerName: Optional[str] = None
    embeddingDependencyType: Optional[AzureEmbeddingDependency] = None


@dataclass
class AzureAISearchDataSources(AzureDataSourceParameters):
    endpoint: Optional[str] = None
    key: Optional[str] = None
    queryType: Literal["simple", "semantic", "vector", "vectorSimpleHybrid", "vectorSemanticHybrid"] = "simple"
    authentication: Optional[ApiKeyAuthentication] = None


@dataclass
class AzureDataSources:
    """Class to hold Azure AI data source parameters."""

    type: Literal["AzureCognitiveSearch", "AzureCosmosDB"] = "AzureCognitiveSearch"
    parameters: Optional[SerializeAsAny[AzureDataSourceParameters]] = None


# @dataclass
class ExtraBody(KernelBaseModel):
    data_sources: Optional[List[AzureDataSources]] = Field(None, alias="dataSources")
    input_language: Optional[str] = Field(None, serialization_alias="inputLanguage")
    output_language: Optional[str] = Field(None, serialization_alias="outputLanguage")

    def __getitem__(self, item):
        return getattr(self, item)


class AzureChatPromptExecutionSettings(OpenAIChatPromptExecutionSettings):
    """Specific settings for the Azure OpenAI Chat Completion endpoint."""

    response_format: Optional[str] = None
    extra_body: Optional[Union[Dict[str, Any], ExtraBody]] = None
