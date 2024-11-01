# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import HttpsUrl, KernelBaseSettings


class AzureKeyVaultSettings(KernelBaseSettings):
    """Azure Key Vault model settings

    Optional:
    - vault_url: HttpsUrl - Azure Key Vault URL
        (Env var AZURE_KEY_VAULT_VAULT_URL)
    - client_id: str - Azure Key Vault client ID
        (Env var AZURE_KEY_VAULT_CLIENT_ID)
    - client_secret: SecretStr - Azure Key Vault client secret
        (Env var AZURE_KEY_VAULT_CLIENT_SECRET)
    """

    env_prefix: ClassVar[str] = "AZURE_KEY_VAULT_"

    endpoint: HttpsUrl
    client_id: str
    client_secret: SecretStr
