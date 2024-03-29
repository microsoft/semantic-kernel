# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.kernel import Kernel


async def main():

    # This is an example of how to import a plugin from OpenAI and invoke a function from the plugin
    # It does not require authentication

    kernel = Kernel()
    plugin = await kernel.import_plugin_from_openai(
        plugin_name="Klarna",
        plugin_url="https://www.klarna.com/.well-known/ai-plugin.json",
    )

    # Query parameters for the function
    # q = Category or product that needs to be searched for
    # size = Number of results to be returned
    # budget = Maximum price of the matching product in Local Currency
    # countryCode = currently, only US, GB, DE, SE, and DK are supported
    query_params = {"q": "Laptop", "size": "3", "budget": "200", "countryCode": "US"}

    result = await kernel.invoke(
        plugin["productsUsingGET"], query_params=query_params, headers={}, path_params={}, request_body={}
    )

    print(f"Function execution result: {str(result)}")


if __name__ == "__main__":
    asyncio.run(main())
