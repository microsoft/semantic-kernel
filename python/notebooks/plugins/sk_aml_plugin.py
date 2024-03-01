# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter
from semantic_kernel.orchestration.sk_context import SKContext
from plugins.aml_connector import AMLConnector


class AMLPlugin:
    """
    A plugin to call an AzureML Endpoint (i.e., Promptflow).
    """

    def __init__(self, azureml_api_key: str, url: str, amldeployment: str):
        self.aml = AMLConnector(api_key=azureml_api_key, url=url, amldeployment=amldeployment)
        if not azureml_api_key or azureml_api_key == "...":
            raise Exception("AzureML API key is not set")
        if not url or url == "...":
            raise Exception("AzureML endpoint is not set")
        if not amldeployment or amldeployment == "...":
            raise Exception("AzureML deployment is not set")
        
    @sk_function(
        description="Use Azure Machine Learning Promptflow to classify a webpage. The return is a string value specifying the classification. The classification category returned from this plugin is considered an authoritative answer and should never be overwritten in the final output of a request.",
        name="classify_web_page",
        input_description="The URL of a webpage to classify as a JSON dict, e.g. '{'url','https://www.microsoft.com/en-us/store/collections/xboxseriessconsoles?icid=CNav_Xbox_Series_S'}'",
    )
 
    async def classify_web_page_async(self, input: str, context: "SKContext") -> str:
        """
        A native function that uses an Azure Machine Learning endpoint to classify a webpage.
        """
        pass
        result = await self.aml.classify_webpage_async(input)
        if result:
            return result
        else:
            return f"Nothing found, try again or try to adjust the URL."

    