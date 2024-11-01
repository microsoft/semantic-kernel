# Copyright (c) Microsoft. All rights reserved.

from typing import ClassVar

from semantic_kernel.kernel_pydantic import KernelBaseSettings


class VertexAISettings(KernelBaseSettings):
    """Vertex AI settings.

    The settings are first loaded from environment variables with
    the prefix 'VERTEX_AI_'.
    If the environment variables are not found, the settings can
    be loaded from a .env file with the encoding 'utf-8'.
    If the settings are not found in the .env file, the settings
    are ignored; however, validation will fail alerting that the
    settings are missing.

    Required settings for prefix 'VERTEX_AI_' are:
    - gemini_model_id: str - The Gemini model ID for the Vertex AI service, i.e. gemini-1.5-pro
                This value can be found in the Vertex AI service deployment.
                (Env var VERTEX_AI_GEMINI_MODEL_ID)
    - embedding_model_id: str - The embedding model ID for the Vertex AI service, i.e. text-embedding-004
                This value can be found in the Vertex AI service deployment.
                (Env var VERTEX_AI_EMBEDDING_MODEL_ID)
    - project_id: str - The Google Cloud project ID.
                (Env var VERTEX_AI_PROJECT_ID)
    - region: str - The Google Cloud region.
                (Env var VERTEX_AI_REGION)
    """

    env_prefix: ClassVar[str] = "VERTEX_AI_"

    gemini_model_id: str | None = None
    embedding_model_id: str | None = None
    project_id: str
    region: str | None = None
