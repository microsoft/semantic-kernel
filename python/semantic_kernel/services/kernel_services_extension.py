# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from typing import TYPE_CHECKING, TypeVar, Union

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import (
    KernelFunctionAlreadyExistsError,
    KernelServiceNotFoundError,
    ServiceInvalidTypeError,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.services.ai_service_selector import AIServiceSelector

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
    from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
    from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
    from semantic_kernel.functions.kernel_function import KernelFunction

T = TypeVar("T")

AI_SERVICE_CLIENT_TYPE = TypeVar("AI_SERVICE_CLIENT_TYPE", bound=AIServiceClientBase)
ALL_SERVICE_TYPES = Union["TextCompletionClientBase", "ChatCompletionClientBase", "EmbeddingGeneratorBase"]


logger: logging.Logger = logging.getLogger(__name__)


class KernelServicesExtension(KernelBaseModel, ABC):
    services: dict[str, AIServiceClientBase] = Field(default_factory=dict)
    ai_service_selector: AIServiceSelector = Field(default_factory=AIServiceSelector)

    @field_validator("services", mode="before")
    @classmethod
    def rewrite_services(
        cls,
        services: (
            AI_SERVICE_CLIENT_TYPE | list[AI_SERVICE_CLIENT_TYPE] | dict[str, AI_SERVICE_CLIENT_TYPE] | None
        ) = None,
    ) -> dict[str, AI_SERVICE_CLIENT_TYPE]:
        """Rewrite services to a dictionary."""
        if not services:
            return {}
        if isinstance(services, AIServiceClientBase):
            return {services.service_id if services.service_id else "default": services}  # type: ignore
        if isinstance(services, list):
            return {s.service_id if s.service_id else "default": s for s in services}
        return services

    def select_ai_service(
        self, function: "KernelFunction", arguments: KernelArguments
    ) -> tuple[ALL_SERVICE_TYPES, PromptExecutionSettings]:
        """Uses the AI service selector to select a service for the function."""
        return self.ai_service_selector.select_ai_service(self, function, arguments)

    def get_service(
        self,
        service_id: str | None = None,
        type: type[ALL_SERVICE_TYPES] | None = None,
    ) -> "AIServiceClientBase":
        """Get a service by service_id and type.

        Type is optional and when not supplied, no checks are done.
        Type should be
            TextCompletionClientBase, ChatCompletionClientBase, EmbeddingGeneratorBase
            or a subclass of one.
            You can also check for multiple types in one go,
            by using TextCompletionClientBase | ChatCompletionClientBase.

        If type and service_id are both None, the first service is returned.

        Args:
            service_id (str | None): The service id,
                if None, the default service is returned or the first service is returned.
            type (Type[ALL_SERVICE_TYPES] | None): The type of the service, if None, no checks are done.

        Returns:
            ALL_SERVICE_TYPES: The service.

        Raises:
            ValueError: If no service is found that matches the type.

        """
        service: "AIServiceClientBase | None" = None
        if not service_id or service_id == "default":
            if not type:
                if default_service := self.services.get("default"):
                    return default_service
                return list(self.services.values())[0]
            if default_service := self.services.get("default"):
                if isinstance(default_service, type):
                    return default_service
            for service in self.services.values():
                if isinstance(service, type):
                    return service
            raise KernelServiceNotFoundError(f"No service found of type {type}")
        if not (service := self.services.get(service_id)):
            raise KernelServiceNotFoundError(f"Service with service_id '{service_id}' does not exist")
        if type and not isinstance(service, type):
            raise ServiceInvalidTypeError(f"Service with service_id '{service_id}' is not of type {type}")
        return service

    def get_services_by_type(self, type: type[ALL_SERVICE_TYPES]) -> dict[str, ALL_SERVICE_TYPES]:
        return {service.service_id: service for service in self.services.values() if isinstance(service, type)}  # type: ignore

    def get_prompt_execution_settings_from_service_id(
        self, service_id: str, type: type[ALL_SERVICE_TYPES] | None = None
    ) -> PromptExecutionSettings:
        """Get the specific request settings from the service, instantiated with the service_id and ai_model_id."""
        service = self.get_service(service_id, type=type)
        return service.instantiate_prompt_execution_settings(
            service_id=service_id,
            extension_data={"ai_model_id": service.ai_model_id},
        )

    def add_service(self, service: AIServiceClientBase, overwrite: bool = False) -> None:
        if service.service_id not in self.services or overwrite:
            self.services[service.service_id] = service
        else:
            raise KernelFunctionAlreadyExistsError(f"Service with service_id '{service.service_id}' already exists")

    def remove_service(self, service_id: str) -> None:
        """Delete a single service from the Kernel."""
        if service_id not in self.services:
            raise KernelServiceNotFoundError(f"Service with service_id '{service_id}' does not exist")
        del self.services[service_id]

    def remove_all_services(self) -> None:
        """Removes the services from the Kernel, does not delete them."""
        self.services.clear()
