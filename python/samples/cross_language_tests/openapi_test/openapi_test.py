# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.kernel import Kernel


async def main():
    kernel = Kernel()

    openapi_spec_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "openapi_spec.json")

    plugin = await kernel.add_plugin_from_openapi(
        plugin_name="LightControl",
        openapi_document_path=openapi_spec_file,
    )

    print(plugin)

    # # Query parameters for the function
    # # q = Category or product that needs to be searched for
    # # size = Number of results to be returned
    # # budget = Maximum price of the matching product in Local Currency
    # # countryCode = currently, only US, GB, DE, SE, and DK are supported
    # query_params = {"q": "Laptop", "size": "3", "budget": "200", "countryCode": "US"}

    # result = await kernel.invoke(
    #     plugin["productsUsingGET"], query_params=query_params, headers={}, path_params={}, request_body={}
    # )

    # print(f"Function execution result: {str(result)}")


if __name__ == "__main__":
    asyncio.run(main())
