# Copyright (c) Microsoft. All rights reserved.

import asyncio

from azure.identity import AzureCliCredential

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.core_plugins.sessions_python_tool.sessions_python_plugin import SessionsPythonTool
from semantic_kernel.kernel import Kernel


async def main():
    kernel = Kernel()

    service_id = "python-code-interpreter"
    credential = AzureCliCredential()
    chat_service = AzureChatCompletion(service_id=service_id, credential=credential)
    kernel.add_service(chat_service)

    python_code_interpreter = SessionsPythonTool(credential=credential)

    sessions_tool = kernel.add_plugin(python_code_interpreter, "PythonCodeInterpreter")

    code = "import json\n\ndef add_numbers(a, b):\n    return a + b\n\nargs = '{\"a\": 1, \"b\": 1}'\nargs_dict = json.loads(args)\nprint(add_numbers(args_dict['a'], args_dict['b']))"  # noqa: E501
    result = await kernel.invoke(sessions_tool["execute_code"], code=code)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
