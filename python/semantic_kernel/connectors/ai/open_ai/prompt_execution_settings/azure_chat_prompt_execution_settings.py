# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Annotated, Any, Literal, Union

from pydantic import AliasGenerator, ConfigDict, Field
from pydantic.alias_generators import to_camel, to_snake
from pydantic.functional_validators import AfterValidator

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.memory.azure_cognitive_search.azure_ai_search_settings import AzureAISearchSettings

logger = logging.getLogger(__name__)


class AzureChatRequestBase(KernelBaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=to_camel, serialization_alias=to_snake),
        use_enum_values=True,
        extra="allow",
    )


class ConnectionStringAuthentication(AzureChatRequestBase):
    type: Annotated[Literal["ConnectionString", "connection_string"], AfterValidator(to_snake)] = "connection_string"
    connection_string: str | None = None


class ApiKeyAuthentication(AzureChatRequestBase):
    type: Annotated[Literal["APIKey", "api_key"], AfterValidator(to_snake)] = "api_key"
    key: str | None = None


class AzureEmbeddingDependency(AzureChatRequestBase):
    type: Annotated[Literal["DeploymentName", "deployment_name"], AfterValidator(to_snake)] = "deployment_name"
    deployment_name: str | None = None


class DataSourceFieldsMapping(AzureChatRequestBase):
    title_field: str | None = None
    url_field: str | None = None
    filepath_field: str | None = None
    content_fields: list[str] | None = None
    vector_fields: list[str] | None = None
    content_fields_separator: str | None = "\n"


class AzureDataSourceParameters(AzureChatRequestBase):
    index_name: str
    index_language: str | None = None
    fields_mapping: DataSourceFieldsMapping | None = None
    in_scope: bool | None = True
    top_n_documents: int | None = 5
    semantic_configuration: str | None = None
    role_information: str | None = None
    filter: str | None = None
    strictness: int = 3
    embedding_dependency: AzureEmbeddingDependency | None = None


class AzureCosmosDBDataSourceParameters(AzureDataSourceParameters):
    authentication: ConnectionStringAuthentication | None = None
    database_name: str | None = None
    container_name: str | None = None
    embedding_dependency_type: AzureEmbeddingDependency | None = None


class AzureCosmosDBDataSource(AzureChatRequestBase):
    type: Literal["azure_cosmos_db"] = "azure_cosmos_db"
    parameters: AzureCosmosDBDataSourceParameters


class AzureAISearchDataSourceParameters(AzureDataSourceParameters):
    endpoint: str | None = None
    query_type: Annotated[
        Literal["simple", "semantic", "vector", "vectorSimpleHybrid", "vectorSemanticHybrid"], AfterValidator(to_snake)
    ] = "simple"
    authentication: ApiKeyAuthentication | None = None


class AzureAISearchDataSource(AzureChatRequestBase):
    type: Literal["azure_search"] = "azure_search"
    parameters: Annotated[dict, AzureAISearchDataSourceParameters]

    @classmethod
    def from_azure_ai_search_settings(cls, azure_ai_search_settings: "AzureAISearchSettings", **kwargs: Any):
        """Create an instance from Azure AI Search settings."""
        kwargs["parameters"] = {
            "endpoint": str(azure_ai_search_settings.endpoint),
            "index_name": azure_ai_search_settings.index_name,
            "authentication": {
                "key": azure_ai_search_settings.api_key.get_secret_value() if azure_ai_search_settings.api_key else None
            },
        }
        return cls(**kwargs)


DataSource = Annotated[Union[AzureAISearchDataSource, AzureCosmosDBDataSource], Field(discriminator="type")]


class ExtraBody(KernelBaseModel):
    data_sources: list[DataSource] | None = None
    input_language: str | None = Field(None, serialization_alias="inputLanguage")
    output_language: str | None = Field(None, serialization_alias="outputLanguage")

    def __getitem__(self, item):
        """Get an item from the ExtraBody."""
        return getattr(self, item)


class AzureChatPromptExecutionSettings(OpenAIChatPromptExecutionSettings):
    """Specific settings for the Azure OpenAI Chat Completion endpoint."""

    extra_body: dict[str, Any] | ExtraBody | None = None
