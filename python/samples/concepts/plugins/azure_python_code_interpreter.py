# Copyright (c) Microsoft. All rights reserved.

import asyncio
import datetime

from azure.core.credentials import AccessToken
from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin import SessionsPythonTool
from semantic_kernel.exceptions.function_exceptions import FunctionExecutionException
from semantic_kernel.kernel import Kernel

auth_token: AccessToken | None = None

ACA_TOKEN_ENDPOINT: str = "https://acasessions.io/.default"  # nosec


async def auth_callback() -> str:
    """Auth callback for the SessionsPythonTool.
    This is a sample auth callback that shows how to use Azure's DefaultAzureCredential
    to get an access token.
    """
    global auth_token
    current_utc_timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())

    if not auth_token or auth_token.expires_on < current_utc_timestamp:
        credential = DefaultAzureCredential()

        try:
            auth_token = credential.get_token(ACA_TOKEN_ENDPOINT)
        except ClientAuthenticationError as cae:
            err_messages = getattr(cae, "messages", [])
            raise FunctionExecutionException(
                f"Failed to retrieve the client auth token with messages: {' '.join(err_messages)}"
            ) from cae

    return auth_token.token


async def main():
    kernel = Kernel()

    service_id = "python-code-interpreter"
    chat_service = AzureChatCompletion(
        service_id=service_id,
    )
    kernel.add_service(chat_service)

    python_code_interpreter = SessionsPythonTool(auth_callback=auth_callback)

    sessions_tool = kernel.add_plugin(python_code_interpreter, "PythonCodeInterpreter")

    code = "import json\n\ndef add_numbers(a, b):\n    return a + b\n\nargs = '{\"a\": 1, \"b\": 1}'\nargs_dict = json.loads(args)\nprint(add_numbers(args_dict['a'], args_dict['b']))"  # noqa: E501
    result = await kernel.invoke(sessions_tool["execute_code"], code=code)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
