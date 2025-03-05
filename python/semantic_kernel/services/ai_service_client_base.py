# Copyright (c) Microsoft. All rights reserved.

from abc import ABC
from typing import TYPE_CHECKING, Annotated

from pydantic import Field, StringConstraints

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


class AIServiceClientBase(KernelBaseModel, ABC):
    """Base class for all AI Services.

    Has an ai_model_id and service_id, any other fields have to be defined by the subclasses.

    The ai_model_id can refer to a specific model, like 'gpt-35-turbo' for OpenAI,
    or can just be a string that is used to identify the model in the service.

    The service_id is used in Semantic Kernel to identify the service, if empty the ai_model_id is used.
    """

    ai_model_id: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    service_id: str = Field("")

    def model_post_init(self, __context: object | None = None):
        """Update the service_id if it is not set."""
        if not self.service_id:
            self.service_id = self.ai_model_id

    # Override this in subclass to return the proper prompt execution type the
    # service is expecting.
    def get_prompt_execution_settings_class(self) -> type["PromptExecutionSettings"]:
        """Get the request settings class."""
        from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

        return PromptExecutionSettings

    def instantiate_prompt_execution_settings(self, **kwargs) -> "PromptExecutionSettings":
        """Create a request settings object.

        All arguments are passed to the constructor of the request settings object.
        """
        return self.get_prompt_execution_settings_class()(**kwargs)

    def get_prompt_execution_settings_from_settings(
        self, settings: "PromptExecutionSettings"
    ) -> "PromptExecutionSettings":
        """Get the request settings from a settings object."""
        prompt_execution_settings_type = self.get_prompt_execution_settings_class()
        if isinstance(settings, prompt_execution_settings_type):
            return settings

        return prompt_execution_settings_type.from_prompt_execution_settings(settings)

    def service_url(self) -> str | None:
        """Get the URL of the service.

        Override this in the subclass to return the proper URL.
        If the service does not have a URL, return None.
        """
        return None
