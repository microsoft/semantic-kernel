# Copyright (c) Microsoft. All rights reserved.

DEFAULT_SCHEMA = "public"

# Limitation based on pgvector documentation https://github.com/pgvector/pgvector#what-if-i-want-to-index-vectors-with-more-than-2000-dimensions
MAX_DIMENSIONALITY = 2000

# The name of the column that returns distance value in the database.
# It is used in the similarity search query. Must not conflict with model property.
DISTANCE_COLUMN_NAME = "sk_pg_distance"

# Environment Variables
PGHOST_ENV_VAR = "PGHOST"
PGPORT_ENV_VAR = "PGPORT"
PGDATABASE_ENV_VAR = "PGDATABASE"
PGUSER_ENV_VAR = "PGUSER"
PGPASSWORD_ENV_VAR = "PGPASSWORD"
PGSSL_MODE_ENV_VAR = "PGSSL_MODE"
