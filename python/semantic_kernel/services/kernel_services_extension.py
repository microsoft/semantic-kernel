# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from collections.abc import Mapping, MutableMapping
from typing import TYPE_CHECKING, TypeVar

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.exceptions import KernelFunctionAlreadyExistsError, KernelServiceNotFoundError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.services.ai_service_selector import AIServiceSelector

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction

AI_SERVICE_CLIENT_TYPE = TypeVar("AI_SERVICE_CLIENT_TYPE", bound=AIServiceClientBase)

logger: logging.Logger = logging.getLogger(__name__)


class KernelServicesExtension(KernelBaseModel, ABC):
    """Kernel services extension.

    Adds all services related entities to the Kernel.
    """

    services: MutableMapping[str, AIServiceClientBase] = Field(default_factory=dict)
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
            return {services.service_id if services.service_id else DEFAULT_SERVICE_NAME: services}  # type: ignore
        if isinstance(services, list):
            return {s.service_id if s.service_id else DEFAULT_SERVICE_NAME: s for s in services}
        return services

    def select_ai_service(
        self,
        function: "KernelFunction | None" = None,
        arguments: "KernelArguments | None" = None,
        type: type[AI_SERVICE_CLIENT_TYPE] | tuple[type[AI_SERVICE_CLIENT_TYPE], ...] | None = None,
    ) -> tuple[AIServiceClientBase, PromptExecutionSettings]:
        """Uses the AI service selector to select a service for the function.

        Args:
            function (KernelFunction | None): The function used.
            arguments (KernelArguments | None): The arguments used.
            type (Type[AI_SERVICE_CLIENT_TYPE] | tuple[type[AI_SERVICE_CLIENT_TYPE], ...] | None): The type of
                service to select. Defaults to None.
        """
        return self.ai_service_selector.select_ai_service(self, function=function, arguments=arguments, type_=type)

    def get_service(
        self,
        service_id: str | None = None,
        type: type[AI_SERVICE_CLIENT_TYPE] | tuple[type[AI_SERVICE_CLIENT_TYPE], ...] | None = None,
    ) -> AI_SERVICE_CLIENT_TYPE:
        """Get a service by service_id and type.

        Type is optional and when not supplied, no checks are done.
        Type should be
            TextCompletionClientBase, ChatCompletionClientBase, EmbeddingGeneratorBase
            or a subclass of one.
            You can also check for multiple types in one go,
            by using a tuple: (TextCompletionClientBase, ChatCompletionClientBase).

        If type and service_id are both None, the first service is returned.

        Args:
            service_id (str | None): The service id,
                if None, the default service is returned or the first service is returned.
            type (Type[AI_SERVICE_CLIENT_TYPE] | tuple[type[AI_SERVICE_CLIENT_TYPE], ...] | None):
                The type of the service, if None, no checks are done on service type.

        Returns:
            AIServiceClientBase: The service, should be a class derived from AIServiceClientBase.

        Raises:
            KernelServiceNotFoundError: If no service is found that matches the type or id.

        """
        services = self.get_services_by_type(type)
        if not services:
            raise KernelServiceNotFoundError(f"No services found of type {type}.")
        if not service_id:
            service_id = DEFAULT_SERVICE_NAME

        if service_id not in services:
            if service_id == DEFAULT_SERVICE_NAME:
                return next(iter(services.values()))
            raise KernelServiceNotFoundError(
                f"Service with service_id '{service_id}' does not exist or has a different type."
            )
        return services[service_id]

    def get_services_by_type(
        self, type: type[AI_SERVICE_CLIENT_TYPE] | tuple[type[AI_SERVICE_CLIENT_TYPE], ...] | None
    ) -> Mapping[str, AI_SERVICE_CLIENT_TYPE]:
        """Get all services of a specific type."""
        if type is None:
            return self.services  # type: ignore
        return {service.service_id: service for service in self.services.values() if isinstance(service, type)}  # type: ignore

    def get_prompt_execution_settings_from_service_id(
        self, service_id: str, type: type[AI_SERVICE_CLIENT_TYPE] | None = None
    ) -> PromptExecutionSettings:
        """Get the specific request settings from the service, instantiated with the service_id and ai_model_id."""
        service = self.get_service(service_id, type=type)
        return service.instantiate_prompt_execution_settings(
            service_id=service_id,
            extension_data={"ai_model_id": service.ai_model_id},
        )

    def add_service(self, service: AIServiceClientBase, overwrite: bool = False) -> None:
        """Add a single service to the Kernel.

        Args:
            service (AIServiceClientBase): The service to add.
            overwrite (bool, optional): Whether to overwrite the service if it already exists. Defaults to False.
        """
        if service.service_id not in self.services or overwrite:
            self.services[service.service_id] = service
            return
        raise KernelFunctionAlreadyExistsError(f"Service with service_id '{service.service_id}' already exists")

    def remove_service(self, service_id: str) -> None:
        """Delete a single service from the Kernel."""
        if service_id not in self.services:
            raise KernelServiceNotFoundError(f"Service with service_id '{service_id}' does not exist")
        del self.services[service_id]

    def remove_all_services(self) -> None:
        """Removes the services from the Kernel, does not delete them."""
        self.services.clear()
