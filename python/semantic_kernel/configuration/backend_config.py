# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.ai.open_ai.services.azure_open_ai_config import AzureOpenAIConfig
from semantic_kernel.ai.open_ai.services.open_ai_config import OpenAIConfig
from semantic_kernel.configuration.backend_types import BackendType


class BackendConfig:
    backend_type: BackendType = BackendType.Unknown
    azure_open_ai: Optional[AzureOpenAIConfig] = None
    open_ai: Optional[OpenAIConfig] = None

    def __init__(
        self,
        backend_type: BackendType,
        azure_open_ai: Optional[AzureOpenAIConfig] = None,
        open_ai: Optional[OpenAIConfig] = None,
    ) -> None:
        """
        Initializes a new instance of the BackendConfig class.

        Arguments:
            backend_type {BackendType} -- The backend type.

        Keyword Arguments:
            azure_open_ai {AzureOpenAIConfig} -- The Azure OpenAI
                configuration. (default: {None})
            open_ai {OpenAIConfig} -- The OpenAI configuration.
                (default: {None})
        """
        self.backend_type = backend_type
        self.azure_open_ai = azure_open_ai
        self.open_ai = open_ai
