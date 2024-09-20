# Copyright (c) Microsoft. All rights reserved.

DEFAULT_SCHEMA = "public"

# Limitation based on pgvector documentation https://github.com/pgvector/pgvector#what-if-i-want-to-index-vectors-with-more-than-2000-dimensions
MAX_DIMENSIONALITY = 2000

# Maximum number of keys that will be processed in a single batch statement
MAX_KEYS_PER_BATCH = 1000
