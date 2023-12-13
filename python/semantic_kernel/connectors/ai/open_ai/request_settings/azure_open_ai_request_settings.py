import logging
from typing import Any, Dict, List, Literal, Optional

from pydantic import Field
from pydantic.dataclasses import dataclass

from semantic_kernel.connectors.ai.open_ai.request_settings.open_ai_request_settings import (
    OpenAIChatRequestSettings,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class AzureDataSources:
    """Class to hold Azure AI data source parameters."""

    indexName: str
    type: Literal["AzureCognitiveSearch", "AzureCosmosDB"] = "AzureCognitiveSearch"
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
class AzureAISearchDataSources(AzureDataSources):
    endpoint: Optional[str] = None
    key: Optional[str] = None
    queryType: Literal[
        "simple", "semantic", "vector", "vectorSimpleHybrid", "vectorSemanticHybrid"
    ] = "simple"


@dataclass
class AzureCosmosDBAuthentication:
    type: Literal["ConnectionString"] = "ConnectionString"
    connectionString: Optional[str] = None


@dataclass
class AzureCosmosDBEmbeddingDependencyType:
    type: Literal["DeploymentName"] = "DeploymentName"
    deploymentName: Optional[str] = None


@dataclass
class AzureCosmosDBDataSource(AzureDataSources):
    authentication: Optional[AzureCosmosDBAuthentication] = None
    databaseName: Optional[str] = None
    containerName: Optional[str] = None
    embeddingDependencyType: Optional[AzureCosmosDBEmbeddingDependencyType] = None


class AzureOpenAIChatRequestSettings(OpenAIChatRequestSettings):
    """Specific settings for the Chat Completion endpoint."""

    response_format: Optional[str] = None
    input_language: Optional[str] = Field(None, serialization_alias="inputLanguage")
    output_language: Optional[str] = Field(None, serialization_alias="outputLanguage")
    data_sources: Optional[List[AzureDataSources]] = Field(
        None, serialization_alias="dataSources"
    )


# Format
# extra_body = {
#     "dataSources": [
#         {
#             "type": "AzureCognitiveSearch",
#             "parameters": {
#                 "endpoint": os.environ["SEARCH_ENDPOINT"],
#                 "key": os.environ["SEARCH_KEY"],
#                 "indexName": os.environ["SEARCH_INDEX_NAME"],
#             },
#         }
#     ]
# }
