# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class OnnxGenAISettings(KernelBaseSettings):
    """Onnx Gen AI model settings.

    The settings are first loaded from environment variables with the prefix 'ONNX_GEN_AI_'. If the
    environment variables are not found, the settings can be loaded from a .env file with the
    encoding 'utf-8'. If the settings are not found in the .env file, the settings are ignored;
    however, validation will fail alerting that the settings are missing.

    Optional settings for prefix 'ONNX_GEN_AI_' are:
    - model_path: Path to the Onnx model (ENV: ONNX_GEN_AI_MODEL_PATH).
    - env_file_path: if provided, the .env settings are read from this file path location
    """

    env_prefix: ClassVar[str] = "ONNX_GEN_AI_"
    model_path: str
