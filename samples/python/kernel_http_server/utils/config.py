from dataclasses import dataclass

from enum import Enum

import semantic_kernel as sk


DEFAULT_OPENAI_MODEL = "text-davinci-003"


class AIService(Enum):
    AZURE_OPENAI = "0"
    OPENAI = "1"


class SKHttpHeaders(Enum):
    COMPLETION_MODEL = "x-ms-sk-completion-model"
    COMPLETION_ENDPOINT = "x-ms-sk-completion-endpoint"
    COMPLETION_SERVICE = "x-ms-sk-completion-backend"
    COMPLETION_KEY = "x-ms-sk-completion-key"
    EMBEDDING_MODEL = "x-ms-sk-embedding-model"
    EMBEDDING_ENDPOINT = "x-ms-sk-embedding-endpoint"
    EMBEDDING_SERVICE = "x-ms-sk-embedding-backend"
    EMBEDDING_KEY = "x-ms-sk-embedding-key"
    MS_GRAPH = "x-ms-sk-msgraph"


@dataclass
class AIServiceConfig:
    deployment_model_id: str
    endpoint: str
    key: str
    serviceid: str
    org_id: str = None


def headers_to_config(headers: dict) -> AIServiceConfig:
    if SKHttpHeaders.COMPLETION_MODEL.value in headers:
        return AIServiceConfig(
            deployment_model_id=headers[SKHttpHeaders.COMPLETION_MODEL.value],
            endpoint=headers[SKHttpHeaders.COMPLETION_ENDPOINT.value],
            key=headers[SKHttpHeaders.COMPLETION_KEY.value],
            serviceid=headers[SKHttpHeaders.COMPLETION_SERVICE.value],
        )
    elif SKHttpHeaders.EMBEDDING_MODEL.value in headers:
        return AIServiceConfig(
            deployment_model_id=headers[SKHttpHeaders.EMBEDDING_MODEL.value],
            endpoint=headers[SKHttpHeaders.EMBEDDING_ENDPOINT.value],
            key=headers[SKHttpHeaders.EMBEDDING_KEY.value],
            serviceid=headers[SKHttpHeaders.EMBEDDING_SERVICE.value],
        )
    raise ValueError("No valid headers found")


def dotenv_to_config(use_azure_openai=True):
    if use_azure_openai:
        deployment_model_id, api_key, endpoint = sk.azure_openai_settings_from_dot_env()
        return AIServiceConfig(
            deployment_model_id=deployment_model_id,
            endpoint=endpoint,
            key=api_key,
            serviceid=AIService.AZURE_OPENAI.value,
        )
    else:
        api_key, org_id = sk.openai_settings_from_dot_env()
        return AIServiceConfig(
            deployment_model_id=DEFAULT_OPENAI_MODEL,
            endpoint=None,
            key=api_key,
            serviceid=AIService.OPENAI.value,
            org_id=org_id,
        )
