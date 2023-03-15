# Copyright (c) Microsoft. All rights reserved.

from typing import Optional

from semantic_kernel.diagnostics.verify import Verify


# TODO: allow for overriding endpoints
class OpenAIConfig:
    """
    The OpenAI configuration.
    """

    # OpenAI model name, see https://platform.openai.com/docs/models
    model_id: str
    # OpenAI API key, see https://platform.openai.com/account/api-keys
    api_key: str
    # OpenAI organization ID. This is usually optional unless your
    # account belongs to multiple organizations.
    org_id: Optional[str]

    def __init__(
        self, model_id: str, api_key: str, org_id: Optional[str] = None
    ) -> None:
        """Initializes a new instance of the OpenAIConfig class.

        Arguments:
            model_id {str} -- OpenAI model name, see
                https://platform.openai.com/docs/models
            api_key {str} -- OpenAI API key, see
                https://platform.openai.com/account/api-keys
            org_id {Optional[str]} -- OpenAI organization ID.
                This is usually optional unless your
                account belongs to multiple organizations.
        """
        Verify.not_empty(model_id, "The model ID is empty")
        Verify.not_empty(api_key, "The API key is empty")

        self.model_id = model_id
        self.api_key = api_key
        self.org_id = org_id
