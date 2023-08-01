import asyncio

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.openapi import register_openapi_skill


if __name__ == "__main__":
    """Client"""
    kernel = sk.Kernel()

    openapi_skill = register_openapi_skill(kernel, "openApiSkill", "openapi.yaml")

    context_variables = sk.ContextVariables(variables={
        "request_body": {"input": "hello world"},
        "path_params": {"name": "mark"},
        "query_params": {"q": "0.7"},
        "headers": {'Content-Type': 'application/json', 'Header': 'example'}    
    })
    result = asyncio.run(
        # Call the function defined in openapi.yaml
        openapi_skill['helloWorld'].invoke_async(variables=context_variables)
    )
    print(result)
