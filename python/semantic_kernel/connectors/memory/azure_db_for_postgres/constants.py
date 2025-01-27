# Copyright (c) Microsoft. All rights reserved.

AZURE_DB_FOR_POSTGRES_SCOPE = "https://ossrdbms-aad.database.windows.net/.default"

AZURE_DB_FOR_POSTGRES_CONNECTION_STRING_ENV_VAR = "AZURE_DB_FOR_POSTGRES_CONNECTION_STRING"
"""Azure DB for Postgres specific environment variable for the connection string.

This is useful if settings for both an Azure DB and a regular Postgres database are needed.
If not set, the regular POSTGRES_CONNECTION_STRING environment variable or other standard
Postgres environment variables will be used.
"""
