# Copyright (c) Microsoft. All rights reserved.

import json
import os
import platform
from functools import reduce

import httpx
from aiohttp import ClientSession

from samples.concepts.plugins.azure_key_vault_settings import AzureKeyVaultSettings
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion, OpenAIChatPromptExecutionSettings
from semantic_kernel.connectors.openai_plugin import OpenAIAuthenticationType, OpenAIFunctionExecutionParameters
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions import KernelArguments, KernelFunction, KernelPlugin

# region Helper functions


def get_file_url(relative_path):
    absolute_path = os.path.abspath(relative_path)
    if platform.system() == "Windows":
        backslash_char = "\\"
        return f"file:///{absolute_path.replace(backslash_char, '/')}"
    return f"file://{absolute_path}"


def load_and_update_openai_spec():
    # Construct the path to the OpenAI spec file
    openai_spec_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "open_ai_plugins", "akv-openai.json"
    )

    # Read the OpenAI spec file
    with open(openai_spec_file) as file:
        openai_spec = json.load(file)

    # Adjust the OpenAI spec file to use the correct file URL based on platform
    openapi_yaml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "open_ai_plugins", "akv-openapi.yaml"
    )
    openai_spec["api"]["url"] = get_file_url(openapi_yaml_path)

    return json.dumps(openai_spec, indent=4)


def print_tool_calls(message: ChatMessageContent) -> None:
    # A helper method to pretty print the tool calls from the message.
    # This is only triggered if auto invoke tool calls is disabled.
    items = message.items
    formatted_tool_calls = []
    for i, item in enumerate(items, start=1):
        if isinstance(item, FunctionCallContent):
            tool_call_id = item.id
            function_name = item.name
            function_arguments = item.arguments
            formatted_str = (
                f"tool_call {i} id: {tool_call_id}\n"
                f"tool_call {i} function name: {function_name}\n"
                f"tool_call {i} arguments: {function_arguments}"
            )
            formatted_tool_calls.append(formatted_str)
    print("Tool calls:\n" + "\n\n".join(formatted_tool_calls))


# endregion

# region Sample Authentication Provider


class OpenAIAuthenticationProvider:
    """A Sample Authentication Provider for an OpenAI/OpenAPI plugin"""

    def __init__(
        self, oauth_values: dict[str, dict[str, str]] | None = None, credentials: dict[str, str] | None = None
    ):
        """Initializes the OpenAIAuthenticationProvider."""
        self.oauth_values = oauth_values or {}
        self.credentials = credentials or {}

    async def authenticate_request(
        self,
        plugin_name: str,
        openai_auth_config: OpenAIAuthenticationType,
        **kwargs,
    ) -> dict[str, str] | None:
        """An example of how to authenticate a request as part of an auth callback."""
        if openai_auth_config.type == OpenAIAuthenticationType.NoneType:
            return None

        scheme = ""
        credential = ""

        if openai_auth_config.type == OpenAIAuthenticationType.OAuth:
            if not openai_auth_config.authorization_url:
                raise ValueError("Authorization URL is required for OAuth.")

            domain = openai_auth_config.authorization_url.host
            domain_oauth_values = self.oauth_values.get(domain)

            if not domain_oauth_values:
                raise ValueError("No OAuth values found for the provided authorization URL.")

            values = domain_oauth_values | {"scope": openai_auth_config.scope or ""}

            content_type = openai_auth_config.authorization_content_type or "application/x-www-form-urlencoded"
            async with ClientSession() as session:
                authorization_url = str(openai_auth_config.authorization_url)

                if content_type == "application/x-www-form-urlencoded":
                    response = await session.post(authorization_url, data=values)
                elif content_type == "application/json":
                    response = await session.post(authorization_url, json=values)
                else:
                    raise ValueError(f"Unsupported authorization content type: {content_type}")

                response.raise_for_status()

                token_response = await response.json()
                scheme = token_response.get("token_type", "")
                credential = token_response.get("access_token", "")

        else:
            token = openai_auth_config.verification_tokens.get(plugin_name, "")
            scheme = openai_auth_config.authorization_type.value
            credential = token

        auth_header = f"{scheme} {credential}"
        return {"Authorization": auth_header}


# endregion

# region AKV Plugin Functions


async def add_secret_to_key_vault(kernel: Kernel, plugin: KernelPlugin):
    """Adds a secret to the Azure Key Vault."""
    arguments = KernelArguments()
    arguments["secret_name"] = "Foo"  # nosec
    arguments["api_version"] = "7.0"
    arguments["value"] = "Bar"
    arguments["enabled"] = True
    result = await kernel.invoke(
        function=plugin["SetSecret"],
        arguments=arguments,
    )

    print(f"Secret added to Key Vault: {result}")


async def get_secret_from_key_vault(kernel: Kernel, plugin: KernelPlugin):
    """Gets a secret from the Azure Key Vault."""
    arguments = KernelArguments()
    arguments["secret_name"] = "Foo"  # nosec
    arguments["api_version"] = "7.0"
    result = await kernel.invoke(
        function=plugin["GetSecret"],
        arguments=arguments,
    )

    print(f"Secret retrieved from Key Vault: {result}")


# endregion


kernel = Kernel()

kernel.add_service(OpenAIChatCompletion(service_id="chat"))

chat_function = kernel.add_function(
    prompt="{{$chat_history}}{{$user_input}}",
    plugin_name="ChatBot",
    function_name="Chat",
)

execution_settings = OpenAIChatPromptExecutionSettings(
    service_id="chat",
    max_tokens=2000,
    temperature=0.7,
    top_p=0.8,
    function_choice_behavior=FunctionChoiceBehavior.Auto(filters={"included_plugins": ["AzureKeyVaultPlugin"]}),
)

history = ChatHistory()
history.add_system_message("Use Api-version 7.0, if needed.")

arguments = KernelArguments(settings=execution_settings)


async def handle_streaming(
    kernel: Kernel,
    chat_function: "KernelFunction",
    arguments: KernelArguments,
) -> None:
    """Handle streaming chat messages."""
    response = kernel.invoke_stream(
        chat_function,
        return_function_results=False,
        arguments=arguments,
    )

    print("Security Agent:> ", end="")
    streamed_chunks: list[StreamingChatMessageContent] = []
    async for message in response:
        if (
            not execution_settings.function_choice_behavior.auto_invoke_kernel_functions
            and isinstance(message[0], StreamingChatMessageContent)
            and message[0].role == AuthorRole.ASSISTANT
        ):
            streamed_chunks.append(message[0])
        elif isinstance(message[0], StreamingChatMessageContent) and message[0].role == AuthorRole.ASSISTANT:
            print(str(message[0]), end="")

    if streamed_chunks:
        streaming_chat_message = reduce(lambda first, second: first + second, streamed_chunks)
        print("Auto tool calls is disabled, printing returned tool calls...")
        print_tool_calls(streaming_chat_message)

    print("\n")


async def main() -> None:
    """Main function to run the chat bot."""
    azure_keyvault_settings = AzureKeyVaultSettings.create()
    client_id = azure_keyvault_settings.client_id
    client_secret = azure_keyvault_settings.client_secret.get_secret_value()
    endpoint = azure_keyvault_settings.endpoint

    authentication_provider = OpenAIAuthenticationProvider({
        "login.microsoftonline.com": {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials",
        }
    })

    openai_spec = load_and_update_openai_spec()

    http_client = httpx.AsyncClient(timeout=5)

    await kernel.add_plugin_from_openai(
        plugin_name="AzureKeyVaultPlugin",
        plugin_str=openai_spec,
        execution_parameters=OpenAIFunctionExecutionParameters(
            http_client=http_client,
            auth_callback=authentication_provider.authenticate_request,
            server_url_override=str(endpoint),
            enable_dynamic_payload=True,
        ),
    )

    chatting = True
    print(
        "Welcome to the chat bot!\
        \n  Type 'exit' to exit.\
        \n  Try chatting about Azure Key Vault!"
    )
    while chatting:
        chatting = await chat()


async def chat() -> bool:
    """Chat with the bot."""
    try:
        user_input = input("User:> ")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    if user_input == "exit":
        print("\n\nExiting chat...")
        return False
    arguments["user_input"] = user_input
    arguments["chat_history"] = history

    await handle_streaming(kernel, chat_function, arguments=arguments)

    return True


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
