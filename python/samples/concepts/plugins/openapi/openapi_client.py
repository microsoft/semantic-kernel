# Copyright (c) Microsoft. All rights reserved.

import asyncio

import semantic_kernel as sk
from semantic_kernel.functions.kernel_arguments import KernelArguments


async def main():
    """Client"""
    kernel = sk.Kernel()

    openapi_plugin = kernel.add_plugin_from_openapi(plugin_name="openApiPlugin", openapi_document_path="./openapi.yaml")

    arguments = {
        "request_body": '{"input": "hello world"}',
        "path_params": '{"name": "mark"}',
        "query_params": '{"q": "0.7"}',
        "headers": '{"Content-Type": "application/json", "Header": "example"}',
    }

    kernel_arguments = KernelArguments(**arguments)

    result = await kernel.invoke(openapi_plugin["helloWorld"], arguments=kernel_arguments)

    print(result)


if __name__ == "__main__":
    asyncio.run(main())
