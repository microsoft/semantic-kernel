# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
from typing import Dict, Optional, Tuple, Union

from dotenv import dotenv_values
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes


def openai_settings_from_dot_env() -> Tuple[str, Optional[str]]:
    """
    Reads the OpenAI API key and organization ID from the .env file.

    Returns:
        Tuple[str, str]: The OpenAI API key, the OpenAI organization ID
    """

    api_key, org_id = None, None
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    with open(".env", "r") as f:
        lines = f.readlines()
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    with open(".env", "r") as f:
        lines = f.readlines()
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    config = dotenv_values(".env")
    api_key = config.get("OPENAI_API_KEY", None)
    org_id = config.get("OPENAI_ORG_ID", None)
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

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


<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
def azure_openai_settings_from_dot_env() -> Tuple[str, str]:
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
def azure_openai_settings_from_dot_env() -> Tuple[str, str]:
=======
    deployment, api_key, endpoint, api_version = None, None, None, None
    config = dotenv_values(".env")
    deployment = config.get("AZURE_OPENAI_DEPLOYMENT_NAME", None)
    api_key = config.get("AZURE_OPENAI_API_KEY", None)
    endpoint = config.get("AZURE_OPENAI_ENDPOINT", None)
    api_version = config.get("AZURE_OPENAI_API_VERSION", None)

    # Azure requires the deployment name, the API key and the endpoint URL.
    if include_deployment:
        assert deployment is not None, "Azure OpenAI deployment name not found in .env file"
    if include_api_version:
        assert api_version is not None, "Azure OpenAI API version not found in .env file"

    assert api_key, "Azure OpenAI API key not found in .env file"
    assert endpoint, "Azure OpenAI endpoint not found in .env file"

    if include_api_version:
        return deployment or "", api_key, endpoint, api_version or ""
    return deployment or "", api_key, endpoint


def azure_openai_settings_from_dot_env_as_dict(
    include_deployment: bool = True, include_api_version: bool = False
) -> Dict[str, str]:
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    """
    Reads the Azure OpenAI API key and endpoint from the .env file.

    Returns:
        Tuple[str, str]: The Azure OpenAI API key, the endpoint
    """

    api_key, endpoint = None, None
    with open(".env", "r") as f:
        lines = f.readlines()

        for line in lines:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
            if line.startswith("AZURE_OPENAI_API_KEY"):
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
            if line.startswith("AZURE_OPENAI_API_KEY"):
=======
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
            if line.startswith("PINECONE_API_KEY"):
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                parts = line.split("=")[1:]
                api_key = "=".join(parts).strip().strip('"')
                break

            if line.startswith("AZURE_OPENAI_ENDPOINT"):
                parts = line.split("=")[1:]
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
                endpoint = "=".join(parts).strip().strip('"')
                break
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
                endpoint = "=".join(parts).strip().strip('"')
                break
=======
                environment = "=".join(parts).strip().strip('"')
                continue

    assert api_key, "Pinecone API key not found in .env file"
    assert environment, "Pinecone environment not found in .env file"

    return api_key, environment


def astradb_settings_from_dot_env() -> Tuple[str, Optional[str]]:
    """
    Reads the Astradb API key and Environment from the .env file.
    Returns:
        Tuple[str, str]: The Astradb API key, the Astradb Environment
    """

    app_token, db_id, region, keyspace = None, None, None, None
    with open(".env", "r") as f:
        lines = f.readlines()

        for line in lines:
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
            if line.startswith("AZURE_OPENAI_API_KEY"):
=======
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
            if line.startswith("PINECONE_API_KEY"):
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
>>>>>>> head
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
            if line.startswith("ASTRADB_APP_TOKEN"):
                parts = line.split("=")[1:]
                app_token = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("ASTRADB_ID"):
                parts = line.split("=")[1:]
                db_id = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("ASTRADB_REGION"):
                parts = line.split("=")[1:]
                region = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("ASTRADB_KEYSPACE"):
                parts = line.split("=")[1:]
                keyspace = "=".join(parts).strip().strip('"')
                continue

    assert app_token, "Astradb Application token not found in .env file"
    assert db_id, "Astradb ID not found in .env file"
    assert region, "Astradb Region not found in .env file"
    assert keyspace, "Astradb Keyspace name not found in .env file"

    return app_token, db_id, region, keyspace


def astradb_settings_from_dot_env() -> Tuple[str, Optional[str]]:
    """
    Reads the Astradb API key and Environment from the .env file.
    Returns:
        Tuple[str, str]: The Astradb API key, the Astradb Environment
    """

    app_token, db_id, region, keyspace = None, None, None, None
    with open(".env", "r") as f:
        lines = f.readlines()

        for line in lines:
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
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
            if line.startswith("ASTRADB_APP_TOKEN"):
                parts = line.split("=")[1:]
                app_token = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("ASTRADB_ID"):
                parts = line.split("=")[1:]
                db_id = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("ASTRADB_REGION"):
                parts = line.split("=")[1:]
                region = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("ASTRADB_KEYSPACE"):
                parts = line.split("=")[1:]
                keyspace = "=".join(parts).strip().strip('"')
                continue

    assert app_token, "Astradb Application token not found in .env file"
    assert db_id, "Astradb ID not found in .env file"
    assert region, "Astradb Region not found in .env file"
    assert keyspace, "Astradb Keyspace name not found in .env file"

    return app_token, db_id, region, keyspace


def weaviate_settings_from_dot_env() -> Tuple[Optional[str], str]:
    """
    Reads the Weaviate API key and URL from the .env file.

    Returns:
        Tuple[str, str]: The Weaviate API key, the Weaviate URL
    """

    config = dotenv_values(".env")
    api_key = config.get("WEAVIATE_API_KEY", None)
    url = config.get("WEAVIATE_URL", None)

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
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

    # Azure requires both the API key and the endpoint URL.
    assert api_key is not None, "Azure OpenAI API key not found in .env file"
    assert endpoint is not None, "Azure OpenAI endpoint not found in .env file"

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
    return api_key, endpoint
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    return api_key, endpoint
=======
    if not include_index_name:
        return api_key, url
    else:
        index_name = config.get("AZURE_AISEARCH_INDEX_NAME", None)
        assert index_name is not None, "Azure AI Search index name not found in .env file"
        return api_key, url, index_name


def azure_aisearch_settings_from_dot_env_as_dict() -> Dict[str, str]:
    """
    Reads the Azure AI Search environment variables including index name from the .env file.

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
=======
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

<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    Returns:
        Dict[str, str]: the Azure AI search environment variables
    """
    api_key, url, index_name = azure_aisearch_settings_from_dot_env(include_index_name=True)
    return {"key": api_key, "endpoint": url, "indexName": index_name}
>>>>>>> ms/small_fixes
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
