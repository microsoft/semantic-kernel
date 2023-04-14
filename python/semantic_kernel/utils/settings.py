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
                continue

            if line.startswith("OPENAI_ORG_ID"):
                parts = line.split("=")[1:]
                org_id = "=".join(parts).strip().strip('"')
                continue

    assert api_key is not None, "OpenAI API key not found in .env file"

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
    with open(".env", "r") as f:
        lines = f.readlines()

        for line in lines:
            if include_deployment and line.startswith("AZURE_OPENAI_DEPLOYMENT_NAME"):
                parts = line.split("=")[1:]
                deployment = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("AZURE_OPENAI_API_KEY"):
                parts = line.split("=")[1:]
                api_key = "=".join(parts).strip().strip('"')
                continue

            if line.startswith("AZURE_OPENAI_ENDPOINT"):
                parts = line.split("=")[1:]
                endpoint = "=".join(parts).strip().strip('"')
                continue

    # Azure requires the deployment name, the API key and the endpoint URL.
    if include_deployment:
        assert (
            deployment is not None
        ), "Azure OpenAI deployment name not found in .env file"

    assert api_key is not None, "Azure OpenAI API key not found in .env file"
    assert endpoint is not None, "Azure OpenAI endpoint not found in .env file"

    return deployment or "", api_key, endpoint
