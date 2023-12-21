import logging
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import Field
from pydantic.dataclasses import dataclass

from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
)
from semantic_kernel.sk_pydantic import SKBaseModel

logger = logging.getLogger(__name__)


@dataclass
class AzureCosmosDBAuthentication:
    type: Literal["ConnectionString"] = "ConnectionString"
    connectionString: Optional[str] = None


@dataclass
class AzureCosmosDBEmbeddingDependencyType:
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


@dataclass
class AzureCosmosDBDataSource(AzureDataSourceParameters):
    authentication: Optional[AzureCosmosDBAuthentication] = None
    databaseName: Optional[str] = None
    containerName: Optional[str] = None
    embeddingDependencyType: Optional[AzureCosmosDBEmbeddingDependencyType] = None


@dataclass
class AzureAISearchDataSources(AzureDataSourceParameters):
    endpoint: Optional[str] = None
    key: Optional[str] = None
    queryType: Literal[
        "simple", "semantic", "vector", "vectorSimpleHybrid", "vectorSemanticHybrid"
    ] = "simple"


@dataclass
class AzureDataSources:
    """Class to hold Azure AI data source parameters."""

    type: Literal["AzureCognitiveSearch", "AzureCosmosDB"] = "AzureCognitiveSearch"
    parameters: Optional[AzureDataSourceParameters] = None


# @dataclass
class ExtraBody(SKBaseModel):
    data_sources: Optional[List[AzureDataSources]] = Field(None, alias="dataSources")
    # input_language: Optional[str] = Field(None, serialization_alias="inputLanguage")
    # output_language: Optional[str] = Field(None, serialization_alias="outputLanguage")


class AzureChatRequestSettings(OpenAIChatRequestSettings):
    """Specific settings for the Azure OpenAI Chat Completion endpoint."""

    response_format: Optional[str] = None
    extra_body: Optional[Union[Dict[str, Any], ExtraBody]] = None
