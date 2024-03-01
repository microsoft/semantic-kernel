# Copyright (c) Microsoft. All rights reserved.

import aiohttp
from logging import Logger
from typing import Any, List, Optional
from semantic_kernel.connectors.search_engine.connector import ConnectorBase
from semantic_kernel.utils.null_logger import NullLogger
import json
import os
import ssl

class AMLConnector(ConnectorBase):
    """
    A AML connector that uses AML online endpoint to score a request.
   
    """
    _api_key: str
    _url: str
    _amldeployment: str
    def __init__(self, api_key: str,url: str,amldeployment: str, logger: Optional[Logger] = None) -> None:
        self._api_key = api_key
        self._url = url
        self._amldeployment = amldeployment
        self._logger = logger if logger else NullLogger()
    
        if not self._api_key:
            raise ValueError(
                "AzureML API key cannot be null. Please set environment variable AZURE_ML_API_KEY."
            )
        if not self._url:
            raise ValueError(
                "AzureML endpoint cannot be null. Please set environment variable AZURE_ML_ENDPOINT."
            )        
        if not self._amldeployment:
            raise ValueError(
                "AzureML deployment cannot be null. Please set environment variable AZURE_ML_MODEL_DEPLOYMENT."
            )  
    def allowSelfSignedHttps(allowed):
    # bypass the server certificate verification on client side
        if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
            ssl._create_default_https_context = ssl._create_unverified_context

    allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

# Request data goes here
# The example below assumes JSON formatting which may be updated
# depending on the format your endpoint expects.
# More information can be found here:
# https://docs.microsoft.com/azure/machine-learning/how-to-deploy-advanced-entry-script




    async def classify_webpage_async(self, input: str) -> str:
        
  #      url = 'https://#instace#.#region#.inference.ml.azure.com/score'

        headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ self._api_key), 'azureml-model-deployment': self._amldeployment } 

        async with aiohttp.ClientSession() as session:
            async with session.post(self._url, data=input.encode(), headers=headers) as response:
             if response.status != 200:
                print(f"The request failed with status code: {response.status}")
                print(await response.text())
             else:
                result = await response.text()
                return result
