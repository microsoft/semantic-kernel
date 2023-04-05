# Copyright (c) Microsoft. All rights reserved.

from typing import Optional, Tuple


def try_get_api_info_from_synapse_mlflow() -> Optional[Tuple[str, str]]:
    """
    Attempts to get the endpoint and api_key from the Synapse MLFlow environment.

    :return: The endpoint and api_key (or None, if not found)
    """
    try:
        from synapse.ml.mlflow import get_mlflow_env_config

        mlflow_env_config = get_mlflow_env_config()
        return (
            f"{mlflow_env_config.workload_endpoint}cognitive/openai",
            mlflow_env_config.driver_aad_token,
        )
    except ImportError:
        return None
