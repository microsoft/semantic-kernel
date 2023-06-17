import time
from typing import Union, TYPE_CHECKING

TOKEN_URL = "https://cognitiveservices.azure.com/.default"


if TYPE_CHECKING:
    from azure.core.credentials import TokenCredential


class AzureCredentialMixin:
    _api_key: str
    _credential = None
    _api_token = None

    def _init_credentials(
        self, api_key: str, ad_auth: Union[bool, str, "azure.core.credentials.TokenCredential"]
    ):
        if isinstance(ad_auth, bool):
            self._credential = None
            self._api_token = None
            self._api_key = api_key

        elif ad_auth:
            if api_key:
                raise ValueError("Cannot provide Azure API key when using credential")

            try:
                from azure.identity import DefaultAzureCredential
                from azure.core.credentials import TokenCredential

            except (ImportError, ModuleNotFoundError):
                raise ImportError(
                    "Please ensure that azure-identity package is installed to use Azure credentials"
                )

            if ad_auth == "auto":
                self._credential = DefaultAzureCredential()
            elif isinstance(ad_auth, TokenCredential):
                self._credential = ad_auth
            else:
                raise ValueError(
                    "The ad_auth parameter should be boolean, 'auto' or a TokenCredential"
                )

            self._set_renew_token()

        else:
            raise ValueError("Must provide either API key or Azure credentials")

    def _set_renew_token(self):
        """Sets the api token and key using the credentials.
        If it is already set and about to expire, renew it.
        """

        if not self._credential:
            return

        if not self._api_token or self._api_token.expires_on < int(time.time()) - 60:
            self._api_token = self._credential.get_token(TOKEN_URL)
            self._api_key = self._api_token.token

    def set_api_key(self, api_key: str):
        """Set or update the api_key"""
        self._api_key = api_key
