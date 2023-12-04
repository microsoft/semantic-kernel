# Copyright (c) Microsoft. All rights reserved.
"""Classes to handle Azure OpenAI Chat With Data settings."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class DataSourceType(Enum):
    """Enum to hold data source type."""

    AZURE_AI_SEARCH = "AzureCognitiveSearch"


@dataclass
class DataSourceParametersBase:
    """Base class to hold data source parameters."""


@dataclass
class AzureAISearchDataSourceParameters(DataSourceParametersBase):
    """Class to hold Azure AI Search data source parameters."""

    indexName: str
    endpoint: str
    key: Optional[str] = None
    indexLanguage: Optional[str] = None
    fieldsMapping: Dict[str, Any] = field(default_factory=dict)
    inScope: Optional[bool] = True
    topNDocuments: Optional[int] = 5
    queryType: Optional[str] = "simple"
    semanticConfiguration: Optional[str] = None
    roleInformation: Optional[str] = None


@dataclass
class AzureChatWithDataSettings:
    """Class to hold Azure OpenAI Chat With Data settings, which might include data source type and authentication information."""

    data_source_type: DataSourceType = DataSourceType.AZURE_AI_SEARCH
    data_source_parameters: DataSourceParametersBase = None
