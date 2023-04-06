# Copyright (c) Microsoft. All rights reserved.


from logging import Logger
from typing import Any, Optional

from semantic_kernel.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)
from semantic_kernel.utils.auth_providers import try_get_auth_from_named_provider


class AzureTextCompletion(OpenAITextCompletion):
    _endpoint: str
    _api_version: str
    _api_type: str

    def __init__(
        self,
        deployment_name: str,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2022-12-01",
        logger: Optional[Logger] = None,
        use_ad_auth=False,
        auth_provider: Optional[str] = None,
    ) -> None:
        """
        Initialize an AzureTextCompletion backend.

        You must provide either:
        - A deployment_name, endpoint, and api_key (plus, optionally: use_ad_auth)
        OR:
        - A deployment_name and auth_provider

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
        :param use_ad_auth: Whether to use Azure Active Directory authentication.
            (Optional) The default value is False.
        :param auth_provider: The name of the auth provider to use. (Optional)
            If the value provided is not None, the endpoint, api_key, and
            use_ad_auth values will be ignored and will be retrieved from the
            auth provider instead.

            Auth providers should be registered in the __sk_auth_providers
            global dictionary; e.g.,
                "my_provider": () => (endpoint, api_key, use_ad_auth)
        """
        if auth_provider is not None:
            # Try to get endpoint/api_key/use_ad_auth via dynamic provider
            try:
                endpoint, api_key, use_ad_auth = try_get_auth_from_named_provider(
                    auth_provider
                )
            except Exception as e:
                raise ValueError(
                    f"Failed to get auth from provider {auth_provider}: {e}"
                )

        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")
        if not api_key:
            raise ValueError("The Azure API key cannot be `None` or empty`")
        if not endpoint:
            raise ValueError("The Azure endpoint cannot be `None` or empty")
        if not endpoint.startswith("https://") and not use_ad_auth:
            raise ValueError("The Azure endpoint must start with https://")

        self._endpoint = endpoint
        self._api_version = api_version
        self._api_type = "azure_ad" if use_ad_auth else "azure"

        super().__init__(deployment_name, api_key, org_id=None, log=logger)

    def _setup_open_ai(self) -> Any:
        import openai

        openai.api_type = self._api_type
        openai.api_key = self._api_key
        openai.api_base = self._endpoint
        openai.api_version = self._api_version

        return openai
