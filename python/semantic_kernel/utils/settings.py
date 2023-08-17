# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple

from dotenv import dotenv_values


def openai_settings_from_dot_env() -> Tuple[str, Optional[str]]:
    """
    Reads the OpenAI API key and organization ID from the .env file.

    Returns:
        Tuple[str, str]: The OpenAI API key, the OpenAI organization ID
    """

    config = dotenv_values(".env")
    api_key = config.get("OPENAI_API_KEY", None)
    org_id = config.get("OPENAI_ORG_ID", None)

    assert api_key, "OpenAI API key not found in .env file"

    # It's okay if the org ID is not found (not required)
    return api_key, org_id


def azure_openai_settings_from_dot_env(include_deployment=True) -> Tuple[str, str, str]:
    """
    Reads the Azure OpenAI API key and endpoint from the .env file.

    Returns:
        Tuple[str, str, str]: The deployment name (or empty), Azure OpenAI API key,
            and the endpoint
    """

    deployment, api_key, endpoint = None, None, None
    config = dotenv_values(".env")
    deployment = config.get("AZURE_OPENAI_DEPLOYMENT_NAME", None)
    api_key = config.get("AZURE_OPENAI_API_KEY", None)
    endpoint = config.get("AZURE_OPENAI_ENDPOINT", None)

    # Azure requires the deployment name, the API key and the endpoint URL.
    if include_deployment:
        assert deployment, "Azure OpenAI deployment name not found in .env file"

    assert api_key, "Azure OpenAI API key not found in .env file"
    assert endpoint, "Azure OpenAI endpoint not found in .env file"

    return deployment or "", api_key, endpoint


def postgres_settings_from_dot_env() -> str:
    """Reads the Postgres connection string from the .env file.

    Returns:
        str: The Postgres connection string
    """
    connection_string = None
    config = dotenv_values(".env")
    connection_string = config.get("POSTGRES_CONNECTION_STRING", None)

    assert connection_string, "Postgres connection string not found in .env file"

    return connection_string


def pinecone_settings_from_dot_env() -> Tuple[str, str]:
    """Reads the Pinecone API key and Environment from the .env file.

    Returns:
        Tuple[str, str]: The Pinecone API key, the Pinecone Environment
    """

    api_key, environment = None, None
    config = dotenv_values(".env")
    api_key = config.get("PINECONE_API_KEY", None)
    environment = config.get("PINECONE_ENVIRONMENT", None)

    assert api_key, "Pinecone API key not found in .env file"
    assert environment, "Pinecone environment not found in .env file"

    return api_key, environment


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
