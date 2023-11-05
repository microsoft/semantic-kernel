# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)


class AzureChatCompletionDataSourceConfig:
    def __init__(
        self,
        endpoint: str,
        key: str,
        index_name: str,
        type: str = "AzureCognitiveSearch",
        fields_mapping: Optional[Dict] = None,
        in_scope: bool = True,
        top_n_documents: int = 5,
        query_type: str = "simple",
        semantic_configuration: Optional[str] = None,
        role_information: Optional[str] = None,
        filter: Optional[str] = None,
        embedding_endpoint: Optional[str] = None,
        embedding_key: Optional[str] = None,
        embedding_deployment_name: Optional[str] = None,
    ):
        """
        TODO: Docstring and validators
        See https://learn.microsoft.com/en-us/azure/ai-services/openai/reference for definitions
        """
        if (embedding_endpoint and embedding_key) and embedding_deployment_name:
            raise ValueError(
                "Either provide embedding_endpoint and embedding_key or only embedding_deployment_name"
            )

        self._endpoint = endpoint
        self._key = key
        self._index_name = index_name
        self._type = type
        self._fields_mapping = fields_mapping
        self._in_scope = in_scope
        self._top_n_documents = top_n_documents
        self._query_type = query_type
        self._semantic_configuration = semantic_configuration
        self._role_information = role_information
        self._filter = filter
        self._embedding_endpoint = embedding_endpoint
        self._embedding_key = embedding_key
        self._embedding_deployment_name = embedding_deployment_name

    def as_datasource_param(self) -> Dict:
        """Return instance variables as a dictionary with CamelCase keys."""
        param = {
            "type": self._type,
            "parameters": {
                "endpoint": self._endpoint,
                "key": self._key,
                "indexName": self._index_name,
                "fieldsMapping": self._fields_mapping,
                "inScope": self._in_scope,
                "topNDocuments": self._top_n_documents,
                "queryType": self._query_type,
                "semanticConfiguration": self._semantic_configuration,
                "roleInformation": self._role_information,
                "filter": self._filter,
            },
        }

        if self._embedding_deployment_name:
            param["parameters"][
                "embeddingDeploymentName"
            ] = self._embedding_deployment_name
        elif self._embedding_endpoint and self._embedding_key:
            param["parameters"]["embeddingEndpoint"] = self._embedding_endpoint
            param["parameters"]["embeddingKey"] = self._embedding_key

        return param


class AzureChatCompletionWithData(AzureChatCompletion):
    _data_source_configs: List[AzureChatCompletionDataSourceConfig]

    def __init__(
        self,
        deployment_name: str,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        data_source_configs: List[AzureChatCompletionDataSourceConfig] = [],
        api_version: str = "2023-08-01-preview",
        logger: Optional[Logger] = None,
        ad_auth=False,
    ) -> None:
        """
        Initialize an AzureChatCompletion service.

        You must provide:
        - A deployment_name, endpoint, and api_key (plus, optionally: ad_auth)

        :param deployment_name: The name of the Azure deployment. This value
            will correspond to the custom name you chose for your deployment
            when you deployed a model. This value can be found under
            Resource Management > Deployments in the Azure portal or, alternatively,
            under Management > Deployments in Azure OpenAI Studio.
        :param endpoint: The endpoint of the Azure deployment. This value
            can be found in the Keys & Endpoint section when examining
            your resource from the Azure portal.
        :param api_key: The API key for the Azure deployment. This value can be
            found in the Keys & Endpoint section when examining your resource in
            the Azure portal. You can use either KEY1 or KEY2.
        :param api_version: The API version to use. (Optional)
            The default value is "2022-12-01".
        :param logger: The logger instance to use. (Optional)
        :param ad_auth: Whether to use Azure Active Directory authentication.
            (Optional) The default value is False.
        """
        if len(data_source_configs) == 0:
            raise ValueError("The data source configs cannot be empty")

        if api_version != "2023-08-01-preview":
            raise ValueError('Only API version "2023-08-01-preview" is supported')

        self._data_source_configs = data_source_configs

        super().__init__(
            deployment_name,
            endpoint,
            api_key,
            api_version,
            logger,
            ad_auth,
        )

    def _validate_chat_request(
        self,
        messages: List[Tuple[str, str]],
        request_settings: ChatRequestSettings,
        stream: bool,
        functions: Optional[List[Dict[str, Any]]] = None,
    ):
        super()._validate_chat_request(messages, request_settings, stream, functions)
        # Chat with your data API does not support function call
        if functions is not None:
            raise ValueError("Chat with your data API does not support function call")

    def _gen_api_payload(
        self,
        messages: List[Tuple[str, str]],
        request_settings: ChatRequestSettings,
        stream: bool,
    ):
        return {
            "model": self._model_id,
            "messages": messages,
            "temperature": request_settings.temperature,
            "top_p": request_settings.top_p,
            "n": request_settings.number_of_responses,
            "stream": stream,
            "stop": (
                request_settings.stop_sequences
                if request_settings.stop_sequences is not None
                and len(request_settings.stop_sequences) > 0
                else None
            ),
            "max_tokens": request_settings.max_tokens,
            "presence_penalty": request_settings.presence_penalty,
            "frequency_penalty": request_settings.frequency_penalty,
            "logit_bias": (
                request_settings.token_selection_biases
                if request_settings.token_selection_biases is not None
                and len(request_settings.token_selection_biases) > 0
                else {}
            ),
            "dataSources": [
                ds.as_datasource_param() for ds in self._data_source_configs
            ],
        }

    def _gen_api_headers(self):
        headers = {
            "Content-Type": "application/json",
        }

        if self._api_type == "azure_ad":
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._api_type == "azure":
            headers["Api-Key"] = self._api_key
        else:
            raise ValueError('The api_type must be either "azure" or "azure_ad"')

        return headers

    def _parse_response(self, response: Dict) -> Tuple[Optional[str], Optional[str]]:
        if len(response["choices"]) == 1:
            choice = response["choices"][0]
            content = choice["message"]["content"]
            citations = choice["message"]["context"]["messages"][0]["content"]
            return (content, citations)
        else:
            return [
                (
                    choice["message"]["content"],
                    choice["message"]["context"]["messages"][0]["content"],
                )
                for choice in response["choices"]
            ]

    async def complete_chat_with_data_async(
        self,
        messages: List[Dict[str, str]],
        request_settings: ChatRequestSettings,
        logger: Optional[Logger] = None,
    ) -> Union[
        Tuple[Optional[str], Optional[dict]],
        List[Tuple[Optional[str], Optional[dict]]],
    ]:
        self._validate_chat_request(messages, request_settings, False, None)
        payload = self._gen_api_payload(messages, request_settings, False)
        headers = self._gen_api_headers()
        url = (
            f"{self._endpoint}"
            f"/openai/deployments/{self._model_id}"
            f"/extensions/chat/completions?api-version={self._api_version}"
        )
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                ) as response:
                    resp_dict = await response.json()
                    return self._parse_response(resp_dict)
        # TODO: Error handling
        except Exception as ex:
            raise AIException(
                AIException.ErrorCodes.ServiceError,
                f"{self.__class__.__name__} failed to complete the chat",
                ex,
            ) from ex

    async def complete_chat_async(
        self,
        messages: List[Dict[str, str]],
        request_settings: ChatRequestSettings,
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        result = await self.complete_chat_with_data_async(
            messages, request_settings, logger
        )
        # First element of the tuple is the response
        if isinstance(result, list):
            return [choice[0] for choice in result]
        return result[0]

    async def complete_async(
        self,
        prompt: str,
        request_settings: CompleteRequestSettings,
        logger: Optional[Logger] = None,
    ) -> Union[str, List[str]]:
        prompt_to_message = [{"role": "user", "content": prompt}]
        chat_settings = ChatRequestSettings.from_completion_config(request_settings)
        result = await self.complete_chat_async(
            prompt_to_message, chat_settings, logger
        )
        return result
