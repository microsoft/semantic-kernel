# Copyright (c) Microsoft. All rights reserved.

DEFAULT_SCHEMA = "public"

# Limitation based on openGauss documentation https://docs.opengauss.org/zh/docs/latest/docs/DataVec/DataVec-Overview.html
MAX_DIMENSIONALITY = 2000

# The name of the column that returns distance value in the database.
# It is used in the similarity search query. Must not conflict with model property.
DISTANCE_COLUMN_NAME = "sk_gs_distance"

# Environment Variables
GSHOST_ENV_VAR = "GSHOST"
GSPORT_ENV_VAR = "GSPORT"
GSDATABASE_ENV_VAR = "GSDATABASE"
GSUSER_ENV_VAR = "GSUSER"
GSPASSWORD_ENV_VAR = "GSPASSWORD"
GSSSL_MODE_ENV_VAR = "GSSSL_MODE"
