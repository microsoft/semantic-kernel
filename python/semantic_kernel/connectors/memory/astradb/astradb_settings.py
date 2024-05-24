# Copyright (c) Microsoft. All rights reserved.

from pydantic import SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class AstraDBSettings(BaseModelSettings):
    """AstraDB model settings.

    Optional:
    - app_token: SecretStr | None - AstraDB token
        (Env var ASTRADB_APP_TOKEN)
    - db_id: str | None - AstraDB database ID
        (Env var ASTRADB_DB_ID)
    - region: str | None - AstraDB region
        (Env var ASTRADB_REGION)
    - keyspace: str | None - AstraDB keyspace
        (Env var ASTRADB_KEYSPACE)
    """

    app_token: SecretStr
    db_id: str
    region: str
    keyspace: str

    class Config(BaseModelSettings.Config):
        """Pydantic configuration settings."""

        env_prefix = "ASTRADB_"
