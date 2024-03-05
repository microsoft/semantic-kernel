# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC
from typing import Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from pydantic import Field, StringConstraints

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.kernel_pydantic import KernelBaseModel


class AIServiceClientBase(KernelBaseModel, ABC):
    """Base class for all AI Services.

    Has a ai_model_id and service_id, any other fields have to be defined by the subclasses.

    The ai_model_id can refer to a specific model, like 'gpt-35-turbo' for OpenAI,
    or can just be a string that is used to identify the model in the service.

    The service_id is used in Semantic Kernel to identify the service, if empty the ai_model_id is used.
    """

    ai_model_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    service_id: str = Field("")

    def model_post_init(self, __context: Optional[object] = None):
        """Update the service_id if it is not set."""
        if not self.service_id:
            self.service_id = self.ai_model_id

    def get_prompt_execution_settings_class(self) -> "PromptExecutionSettings":
        """Get the request settings class."""
        return PromptExecutionSettings  # pragma: no cover

    def instantiate_prompt_execution_settings(self, **kwargs) -> "PromptExecutionSettings":
        """Create a request settings object.

        All arguments are passed to the constructor of the request settings object.
        """
        return self.get_prompt_execution_settings_class()(**kwargs)

    def get_prompt_execution_settings_from_settings(self, settings: PromptExecutionSettings) -> PromptExecutionSettings:
        """Get the request settings from a settings object."""
        return self.get_prompt_execution_settings_class().from_prompt_execution_settings(settings)
