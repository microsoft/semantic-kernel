import logging
from typing import Any, Dict, List, Literal

from pydantic import AliasGenerator, ConfigDict, Field
from pydantic.alias_generators import to_camel, to_snake
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class AzureChatRequestBase(KernelBaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(validation_alias=to_camel, serialization_alias=to_snake),
        use_enum_values=True,
        extra="allow",
    )


def add_type(type_value: str):
    def decorator(cls):
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            if "type" not in kwargs:
                kwargs["type"] = type_value
            original_init(self, *args, **kwargs)

        cls.__init__ = new_init
        return cls

    return decorator


@add_type("connection_string")
class ConnectionStringAuthentication(AzureChatRequestBase):
    type: str
    connection_string: str | None = None


@add_type("api_key")
class ApiKeyAuthentication(AzureChatRequestBase):
    type: str
    key: str | None = None


@add_type("deployment_name")
class AzureEmbeddingDependency(AzureChatRequestBase):
    type: str
    deployment_name: str | None = None


class DataSourceFieldsMapping(AzureChatRequestBase):
    title_field: str | None = None
    url_field: str | None = None
    filepath_field: str | None = None
    content_fields: List[str] | None = None
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
    strictness: int | None = 3
    embedding_dependency: AzureEmbeddingDependency | None = None


class AzureCosmosDBDataSourceParameters(AzureDataSourceParameters):
    authentication: ConnectionStringAuthentication | None = None
    database_name: str | None = None
    container_name: str | None = None
    embedding_dependency_type: AzureEmbeddingDependency | None = None


@add_type("azure_cosmos_db")
class AzureCosmosDBDataSource(AzureChatRequestBase):
    type: str
    parameters: AzureCosmosDBDataSourceParameters


class AzureAISearchDataSourceParameters(AzureDataSourceParameters):
    endpoint: str | None = None
    query_type: Annotated[
        Literal["simple", "semantic", "vector", "vectorSimpleHybrid", "vectorSemanticHybrid"], AfterValidator(to_snake)
    ] = "simple"
    authentication: ApiKeyAuthentication | None = None


@add_type("azure_search")
class AzureAISearchDataSource(AzureChatRequestBase):
    type: str
    parameters: Annotated[dict, AzureAISearchDataSourceParameters]


class ExtraBody(KernelBaseModel):
    data_sources: List[AzureAISearchDataSource | AzureCosmosDBDataSource] | None = None
    input_language: str | None = Field(None, serialization_alias="inputLanguage")
    output_language: str | None = Field(None, serialization_alias="outputLanguage")

    def __getitem__(self, item):
        return getattr(self, item)


class AzureChatPromptExecutionSettings(OpenAIChatPromptExecutionSettings):
    """Specific settings for the Azure OpenAI Chat Completion endpoint."""

    response_format: str | None = None
    extra_body: Dict[str, Any] | ExtraBody | None = None
