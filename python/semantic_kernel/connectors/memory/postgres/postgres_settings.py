# Copyright (c) Microsoft. All rights reserved.

from pydantic import PostgresDsn, SecretStr

from semantic_kernel.connectors.memory.memory_settings_base import BaseModelSettings


class PostgresSettings(BaseModelSettings):
    """Postgres model settings

    Required:
    - connection_string: str - Postgres connection string
        (Env var POSTGRES_CONNECTION_STRING)
    """

    connection_string: SecretStr | PostgresDsn | None = None

    class Config(BaseModelSettings.Config):
        env_prefix = "POSTGRES_"
