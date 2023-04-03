# Copyright (c) Microsoft. All rights reserved.


# TODO: support for AAD auth.
class AzureOpenAIConfig:
    """
    The Azure OpenAI configuration.
    """

    # Azure OpenAI deployment name,
    # https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
    deployment_name: str
    # Azure OpenAI deployment URL,
    # https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
    endpoint: str
    # Azure OpenAI API key,
    # https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
    api_key: str
    # Azure OpenAI API version,
    # https://learn.microsoft.com/azure/cognitive-services/openai/reference
    api_version: str

    def __init__(
        self,
        deployment_name: str,
        endpoint: str,
        api_key: str,
        api_version: str,
    ) -> None:
        """Initializes a new instance of the AzureOpenAIConfig class.

        Arguments:
            deployment_name {str} -- Azure OpenAI deployment name,
            https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource
            endpoint {str} -- Azure OpenAI deployment URL,
            https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
            api_key {str} -- Azure OpenAI API key,
            https://learn.microsoft.com/azure/cognitive-services/openai/quickstart
            api_version {str} -- Azure OpenAI API version,
            https://learn.microsoft.com/azure/cognitive-services/openai/reference
        """
        if not deployment_name:
            raise ValueError("The deployment name cannot be `None` or empty")
        if not api_key:
            raise ValueError("The Azure API key cannot be `None` or empty`")
        if not endpoint:
            raise ValueError("The Azure endpoint cannot be `None` or empty")
        if not endpoint.startswith("https://"):
            raise ValueError("The Azure endpoint must start with https://")

        self.deployment_name = deployment_name
        self.endpoint = endpoint
        self.api_key = api_key
        self.api_version = api_version
