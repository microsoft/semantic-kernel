# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Callable, Optional, Tuple, Type, Union

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel


def get_ai_service(
    kernel: "Kernel", function: "KernelFunction", arguments: "KernelArguments"
) -> Tuple[
    Callable,
    Optional[PromptExecutionSettings],
    Type[Union[ChatCompletionClientBase, TextCompletionClientBase, EmbeddingGeneratorBase]],
]:
    """
    Attempt to select an AI service based on execution settings.

    Args:
        kernel: The kernel instance.
        function: The kernel function being executed.
        arguments: The arguments passed to the kernel function.

    Returns:
    A tuple (service, service_settings, service_base_type) where:
        service is the selected AI service or None if not found.
        service_settings is the execution settings for the service or None.
        service_base_type is the base class of the service type or None.
    """

    def get_service_base_type(service_type):
        """
        Determines the base type of a given service type.

        Args:
            service_type: The type of the service to check.

        Returns:
            The base class if a known service type, otherwise None.
        """
        for base_type in (ChatCompletionClientBase, TextCompletionClientBase, EmbeddingGeneratorBase):
            if issubclass(service_type, base_type):
                return base_type
        return None

    def find_service(services_and_types, settings=None):
        """
        Find a service given a list of service types and optional specific settings.

        Args:
            services_and_types: A list of tuples (service_id, service_type) to search through.
            settings: Optional; specific settings to look for a service.

        Returns:
            A tuple (service, settings, service_base_type) if found, otherwise (None, None, None).
        """
        for service_id, service_type in services_and_types:
            service_base_type = get_service_base_type(service_type)
            if service_base_type is None:
                raise ValueError(f"Service type {service_type} is not supported.")

            target_service = kernel.get_ai_service(service_base_type, service_id=service_id)
            if target_service:
                return target_service, settings, service_base_type
        return None, None, None

    execution_settings = arguments.execution_settings or function.prompt_execution_settings
    services_and_types = get_any_service(kernel)

    if not execution_settings:
        return find_service(services_and_types)

    # Handle specific execution settings
    for service_id, settings in execution_settings.items():
        if service_id and service_id not in (None, "", "default"):  # Skip default for now
            specific_service = kernel.services.get_keyed_service(service_id)
            if specific_service:
                service_base_type = get_service_base_type(type(specific_service))
                return specific_service, settings, service_base_type

    # Fallback to searching by model id or default execution settings
    default_settings = execution_settings.get(None) or execution_settings.get("default")
    return find_service(services_and_types, default_settings)


def get_any_service(kernel: "Kernel"):
    """
    Get any available AI service from the kernel.

    Args:
        kernel: The kernel instance.

    Returns:
        The first available AI service or None if not found.
    """
    unique_services = set()
    unique_services.update(kernel.all_chat_services_with_types())
    unique_services.update(kernel.all_text_completion_services_with_types())
    unique_services.update(kernel.all_text_embedding_generation_services_with_types())
    return list(unique_services)
