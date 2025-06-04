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
    """Base class for Azure Chat requests."""

    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=to_camel, serialization_alias=to_snake),
        use_enum_values=True,
        extra="allow",
    )


class ConnectionStringAuthentication(AzureChatRequestBase):
    """Connection string authentication."""

    type: Annotated[Literal["ConnectionString", "connection_string"], AfterValidator(to_snake)] = "connection_string"
    connection_string: str | None = None


class ApiKeyAuthentication(AzureChatRequestBase):
    """API key authentication."""

    type: Annotated[Literal["APIKey", "api_key"], AfterValidator(to_snake)] = "api_key"
    key: str


class SystemAssignedManagedIdentityAuthentication(AzureChatRequestBase):
    """System assigned managed identity authentication."""

    type: Annotated[
        Literal["SystemAssignedManagedIdentity", "system_assigned_managed_identity"], AfterValidator(to_snake)
    ] = "system_assigned_managed_identity"


class UserAssignedManagedIdentityAuthentication(AzureChatRequestBase):
    """User assigned managed identity authentication."""

    type: Annotated[
        Literal["UserAssignedManagedIdentity", "user_assigned_managed_identity"], AfterValidator(to_snake)
    ] = "user_assigned_managed_identity"
    managed_identity_resource_id: str | None


class AccessTokenAuthentication(AzureChatRequestBase):
    """Access token authentication."""

    type: Annotated[Literal["AccessToken", "access_token"], AfterValidator(to_snake)] = "access_token"
    access_token: str | None


class AzureEmbeddingDependency(AzureChatRequestBase):
    """Azure embedding dependency."""

    type: Annotated[Literal["DeploymentName", "deployment_name"], AfterValidator(to_snake)] = "deployment_name"
    deployment_name: str | None = None


class DataSourceFieldsMapping(AzureChatRequestBase):
    """Data source fields mapping."""

    title_field: str | None = None
    url_field: str | None = None
    filepath_field: str | None = None
    content_fields: list[str] | None = None
    vector_fields: list[str] | None = None
    content_fields_separator: str | None = "\n"


class AzureDataSourceParameters(AzureChatRequestBase):
    """Azure data source parameters."""

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
    """Azure Cosmos DB data source parameters."""

    authentication: ConnectionStringAuthentication | None = None
    database_name: str | None = None
    container_name: str | None = None
    embedding_dependency_type: AzureEmbeddingDependency | None = None


class AzureCosmosDBDataSource(AzureChatRequestBase):
    """Azure Cosmos DB data source."""

    type: Literal["azure_cosmos_db"] = "azure_cosmos_db"
    parameters: AzureCosmosDBDataSourceParameters


class AzureAISearchDataSourceParameters(AzureDataSourceParameters):
    """Azure AI Search data source parameters."""

    endpoint: str | None = None
    query_type: Annotated[
        Literal["simple", "semantic", "vector", "vectorSimpleHybrid", "vectorSemanticHybrid"], AfterValidator(to_snake)
    ] = "simple"
    authentication: (
        ApiKeyAuthentication
        | SystemAssignedManagedIdentityAuthentication
        | UserAssignedManagedIdentityAuthentication
        | AccessTokenAuthentication
        | None
    ) = None


class AzureAISearchDataSource(AzureChatRequestBase):
    """Azure AI Search data source."""

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
    """Extra body for the Azure Chat Completion endpoint."""

    data_sources: list[DataSource] | None = None
    input_language: Annotated[str | None, Field(serialization_alias="inputLanguage")] = None
    output_language: Annotated[str | None, Field(serialization_alias="outputLanguage")] = None

    def __getitem__(self, item):
        """Get an item from the ExtraBody."""
        return getattr(self, item)


class AzureChatPromptExecutionSettings(OpenAIChatPromptExecutionSettings):
    """Specific settings for the Azure OpenAI Chat Completion endpoint."""

    extra_body: dict[str, Any] | ExtraBody | None = None  # type: ignore[assignment]
