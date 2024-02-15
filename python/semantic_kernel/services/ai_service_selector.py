from typing import TYPE_CHECKING, Tuple, Union

from semantic_kernel.connectors.ai.ai_exception import AIException
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.embeddings.embedding_generator_base import EmbeddingGeneratorBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel_pydantic import KernelBaseModel

ALL_SERVICE_TYPES = Union[TextCompletionClientBase, ChatCompletionClientBase, EmbeddingGeneratorBase]

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel


class AIServiceSelector(KernelBaseModel):
    """Default service selector, can be subclassed and overridden.

    To use a custom service selector, subclass this class and override the select_ai_service method.
    Make sure that the function signature stays the same.
    """

    def select_ai_service(
        self, kernel: "Kernel", function: KernelFunction, arguments: KernelArguments
    ) -> Tuple[ALL_SERVICE_TYPES, PromptExecutionSettings]:
        """Select a AI Service on a first come, first served basis,
        starting with execution settings in the arguments,
        followed by the execution settings from the function.
        If the same service_id is in both, the one in the arguments will be used.
        """
        if function.chat_prompt_template:
            requested_type = ChatCompletionClientBase
        else:
            requested_type = TextCompletionClientBase
        execution_settings_dict = arguments.execution_settings or {}
        for id, settings in function.prompt_execution_settings.items():
            if id not in execution_settings_dict:
                execution_settings_dict[id] = settings
        for service_id, settings in execution_settings_dict.items():
            service = kernel.get_service(service_id, requested_type)
            if service:
                service_settings = service.get_prompt_execution_settings_class().from_prompt_execution_settings(
                    settings
                )
                return service, service_settings
        raise AIException(AIException.ErrorCodes.NoServiceFound, "No service found.")
