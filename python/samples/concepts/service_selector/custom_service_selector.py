# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_types import AI_SERVICE_CLIENT_TYPE
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.services.ai_service_selector import AIServiceSelector
from semantic_kernel.services.kernel_services_extension import KernelServicesExtension


class CustomServiceSelector(AIServiceSelector):
    def select_ai_service(
        self,
        kernel: "KernelServicesExtension",
        function: "KernelFunction",
        arguments: "KernelArguments",
        type_: type[AI_SERVICE_CLIENT_TYPE] | tuple[type[AI_SERVICE_CLIENT_TYPE], ...] | None = None,
    ) -> tuple["AIServiceClientBase", "PromptExecutionSettings"]:
        execution_settings_dict = arguments.execution_settings or {}
        if func_exec_settings := getattr(function, "prompt_execution_settings", None):
            for id, settings in func_exec_settings.items():
                if id not in execution_settings_dict:
                    execution_settings_dict[id] = settings
        if not execution_settings_dict:
            from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings

            execution_settings_dict = {DEFAULT_SERVICE_NAME: PromptExecutionSettings()}

        gpt_4_settings = {
            service_name: settings
            for service_name, settings in execution_settings_dict.items()
            if "gpt-4" in service_name
        }
        if gpt_4_settings:
            service_id = list(gpt_4_settings.keys())[0]
            service = kernel.get_service(service_id, type=type_)
            service_settings = service.get_prompt_execution_settings_from_settings(gpt_4_settings[service_id])
            return service, service_settings
        return super().select_ai_service(kernel, function, arguments, type_)


kernel = Kernel(ai_service_selector=CustomServiceSelector())
kernel.add_service(AzureChatCompletion(service_id="gpt-4o"))
kernel.add_service(OpenAIChatCompletion(service_id="gpt-3.5-turbo", ai_model_id="gpt-3.5-turbo"))

kernel.add_function(
    plugin_name="selector",
    function_name="select_ai_service",
    prompt="Always respond with your name. {{$chat_history}}",
    prompt_execution_settings={
        "gpt-4o": PromptExecutionSettings(service_id="gpt-4o", max_tokens=200, temperature=0.0),
        "gpt-3.5-turbo": PromptExecutionSettings(service_id="gpt-3.5-turbo", max_tokens=400, temperature=1.0),
    },
)


async def main():
    chat_history = ChatHistory()
    chat_history.add_user_message("I'm Eduard.")
    result = await kernel.invoke(plugin_name="selector", function_name="select_ai_service", chat_history=chat_history)
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
