# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple


def openai_settings_from_dot_env() -> Tuple[str, Optional[str]]:
    """
    Reads the OpenAI API key and organization ID from the .env file.

    Returns:
        Tuple[str, str]: The OpenAI API key, the OpenAI organization ID
    """

    api_key, org_id = None, None
    with open(".env", "r") as f:
        lines = f.readlines()

        for line in lines:
            if line.startswith("OPENAI_API_KEY"):
                parts = line.split("=")[1:]
                api_key = "=".join(parts).strip().strip('"')
                break

            if line.startswith("OPENAI_ORG_ID"):
                parts = line.split("=")[1:]
                org_id = "=".join(parts).strip().strip('"')
                break

    assert api_key is not None, "OpenAI API key not found in .env file"

    # It's okay if the org ID is not found (not required)
    return api_key, org_id


def azure_openai_settings_from_dot_env() -> Tuple[str, str]:
    """
    Reads the Azure OpenAI API key and endpoint from the .env file.

    Returns:
        Tuple[str, str]: The Azure OpenAI API key, the endpoint
    """

    api_key, endpoint = None, None
    with open(".env", "r") as f:
        lines = f.readlines()

        for line in lines:
            if line.startswith("AZURE_OPENAI_API_KEY"):
                parts = line.split("=")[1:]
                api_key = "=".join(parts).strip().strip('"')
                break

            if line.startswith("AZURE_OPENAI_ENDPOINT"):
                parts = line.split("=")[1:]
                endpoint = "=".join(parts).strip().strip('"')
                break

    # Azure requires both the API key and the endpoint URL.
    assert api_key is not None, "Azure OpenAI API key not found in .env file"
    assert endpoint is not None, "Azure OpenAI endpoint not found in .env file"

<<<<<<< main
    return api_key, endpoint
=======
    # API key not needed for local Weaviate deployment, URL still needed
    assert url is not None, "Weaviate instance URL not found in .env file"

    return api_key, url


def bing_search_settings_from_dot_env() -> str:
    """Reads the Bing Search API key from the .env file.

    Returns:
        str: The Bing Search API key
    """

    api_key = None
    config = dotenv_values(".env")
    api_key = config.get("BING_API_KEY", None)

    assert api_key is not None, "Bing Search API key not found in .env file"

    return api_key


def mongodb_atlas_settings_from_dot_env() -> str:
    """Returns the Atlas MongoDB Connection String from the .env file.

    Returns:
        str: MongoDB Connection String URI
    """

    config = dotenv_values(".env")
    uri = config.get("MONGODB_ATLAS_CONNECTION_STRING")
    assert uri is not None, "MongoDB Connection String not found in .env file"

    return uri


def google_palm_settings_from_dot_env() -> str:
    """
    Reads the Google PaLM API key from the .env file.

    Returns:
        str: The Google PaLM API key
    """

    config = dotenv_values(".env")
    api_key = config.get("GOOGLE_PALM_API_KEY", None)

    assert api_key is not None, "Google PaLM API key not found in .env file"

    return api_key


def azure_cosmos_db_settings_from_dot_env() -> Tuple[str, str]:
    """
    Reads the Azure CosmosDB environment variables for the .env file.
    Returns:
        dict: The Azure CosmosDB environment variables
    """
    config = dotenv_values(".env")
    cosmos_api = config.get("AZCOSMOS_API")
    cosmos_connstr = config.get("AZCOSMOS_CONNSTR")

    assert cosmos_connstr is not None, "Azure Cosmos Connection String not found in .env file"

    return cosmos_api, cosmos_connstr


def redis_settings_from_dot_env() -> str:
    """Reads the Redis connection string from the .env file.

    Returns:
        str: The Redis connection string
    """
    config = dotenv_values(".env")
    connection_string = config.get("REDIS_CONNECTION_STRING", None)

    assert connection_string is not None, "Redis connection string not found in .env file"

    return connection_string


def azure_aisearch_settings_from_dot_env(
    include_index_name=False,
) -> Union[Tuple[str, str], Tuple[str, str, str]]:
    """
    Reads the Azure AI Search environment variables for the .env file.

    Returns:
        Tuple[str, str]: Azure AI Search API key, the Azure AI Search URL
    """
    config = dotenv_values(".env")
    api_key = config.get("AZURE_AISEARCH_API_KEY", None)
    url = config.get("AZURE_AISEARCH_URL", None)

    assert url is not None, "Azure AI Search URL not found in .env file"
    assert api_key is not None, "Azure AI Search API key not found in .env file"

    if not include_index_name:
        return api_key, url
    else:
        index_name = config.get("AZURE_AISEARCH_INDEX_NAME", None)
        assert index_name is not None, "Azure AI Search index name not found in .env file"
        return api_key, url, index_name


def azure_aisearch_settings_from_dot_env_as_dict() -> Dict[str, str]:
    """
    Reads the Azure AI Search environment variables including index name from the .env file.

    Returns:
        Dict[str, str]: the Azure AI search environment variables
    """
    api_key, url, index_name = azure_aisearch_settings_from_dot_env(include_index_name=True)
    return {"key": api_key, "endpoint": url, "indexName": index_name}
>>>>>>> ms/small_fixes
