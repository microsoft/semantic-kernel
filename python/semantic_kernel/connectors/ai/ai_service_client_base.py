# Copyright (c) Microsoft. All rights reserved.

from abc import ABC

from pydantic import constr

from semantic_kernel.connectors.ai.ai_request_settings import AIRequestSettings
from semantic_kernel.sk_pydantic import SKBaseModel


class AIServiceClientBase(SKBaseModel, ABC):
    """Base class for all AI Services.

    Has a ai_model_id, any other fields have to be defined by the subclasses.

    The ai_model_id can refer to a specific model, like 'gpt-35-turbo' for OpenAI,
    or can just be a string that is used to identify the service.
    """

    ai_model_id: constr(strip_whitespace=True, min_length=1)

    def get_request_settings_class(self) -> "AIRequestSettings":
        """Create a request settings object."""
        return AIRequestSettings  # pragma: no cover
