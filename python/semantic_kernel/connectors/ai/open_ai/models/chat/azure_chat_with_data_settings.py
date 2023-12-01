# Copyright (c) Microsoft. All rights reserved.
"""Classes to handle Azure OpenAI Chat With Data settings."""
from enum import Enum
from typing import Optional

class DataSourceType(Enum):
    """Enum to hold data source type."""

    AZURE_AI_SEARCH = "AzureCognitiveSearch"

class DataSourceParametersBase:
    """Base class to hold data source parameters."""
    def asdict(self):
        return self.__dict__

class AzureAISearchDataSourceParameters(DataSourceParametersBase):
    """Class to hold Azure AI Search data source parameters."""

    indexName: str
    endpoint: str
    key: Optional[str]

    def __init__(self, indexName: str, endpoint: str, key: Optional[str] = None):
        self.indexName = indexName
        self.endpoint = endpoint
        self.key = key

class AzureChatWithDataSettings:
    """Class to hold Azure OpenAI Chat With Data settings, which might include data source type and authentication information."""

    data_source_type: DataSourceType = DataSourceType.AZURE_AI_SEARCH
    data_source_parameters: DataSourceParametersBase

    def __init__(self, data_source_type: DataSourceType, data_source_parameters: DataSourceParametersBase):
        self.data_source_type = data_source_type
        self.data_source_parameters = data_source_parameters
