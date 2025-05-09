# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from pydantic import SecretStr

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AstraDBSettings(KernelBaseSettings):
    """AstraDB model settings.

    Settings for AstraDB connection:
    - app_token: SecretStr | None - AstraDB token (Env var ASTRADB_APP_TOKEN)
    - db_id: str | None - AstraDB database ID (Env var ASTRADB_DB_ID)
    - region: str | None - AstraDB region (Env var ASTRADB_REGION)
    - keyspace: str | None - AstraDB keyspace (Env var ASTRADB_KEYSPACE)
    """

    env_prefix: ClassVar[str] = "ASTRADB_"

    app_token: SecretStr
    db_id: str
    region: str
    keyspace: str
