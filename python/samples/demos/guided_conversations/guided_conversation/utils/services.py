from dotenv import dotenv_values
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion


def add_service(kernel: Kernel, service_id: str) -> Kernel:
    """Configure the AI service for the kernel

    Args:
        kernel (Kernel): The kernel to configure

    Returns:
        Kernel: The configured kernel
    """
    config = dotenv_values(".env")
    llm_service = config.get("GLOBAL_LLM_SERVICE", None)
    if not llm_service:
        print("GLOBAL_LLM_SERVICE not set, trying to use Azure OpenAI.")

    # Configure AI service used by the kernel. Load settings from the .env file.
    if llm_service == "OpenAI":
        kernel.add_service(OpenAIChatCompletion(service_id=service_id))
    else:
        kernel.add_service(
            AzureChatCompletion(
                service_id=service_id,
                deployment_name=config.get("AZURE_OPEN_AI_CHAT_COMPLETION_DEPLOYMENT_NAME"),
            )
        )

    return kernel
