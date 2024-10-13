# Copyright (c) Microsoft. All rights reserved.

import logging

from azure.core.exceptions import ClientAuthenticationError
from azure.identity import DefaultAzureCredential

from semantic_kernel.exceptions.service_exceptions import ServiceInvalidAuthError

logger: logging.Logger = logging.getLogger(__name__)

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
logging.basicConfig(level=logging.DEBUG)

>>>>>>> main
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
logging.basicConfig(level=logging.DEBUG)

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head

def get_entra_auth_token(token_endpoint: str) -> str | None:
    """Retrieve a Microsoft Entra Auth Token for a given token endpoint.

    The token endpoint may be specified as an environment variable, via the .env
    file or as an argument. If the token endpoint is not provided, the default is None.

    Args:
        token_endpoint: The token endpoint to use to retrieve the authentication token.

    Returns:
        The Azure token or None if the token could not be retrieved.
    """
    if not token_endpoint:
        raise ServiceInvalidAuthError(
            "A token endpoint must be provided either in settings, as an environment variable, or as an argument."
        )

    credential = DefaultAzureCredential()

    try:
        auth_token = credential.get_token(token_endpoint)
    except ClientAuthenticationError:
        logger.error(f"Failed to retrieve Azure token for the specified endpoint: `{token_endpoint}`.")
        return None

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    logger.info(f"Successfully retrieved Azure token for the specified endpoint: `{token_endpoint}`.")

>>>>>>> main
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
    logger.info(f"Successfully retrieved Azure token for the specified endpoint: `{token_endpoint}`.")

>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    return auth_token.token if auth_token else None
