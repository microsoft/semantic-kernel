# Copyright (c) Microsoft. All rights reserved.

import warnings

# Deprecation warning for Vertex AI services
warnings.warn(
    "The semantic_kernel.connectors.ai.google.vertex_ai module is deprecated and will be removed after 01/01/2026. "
    "Please use semantic_kernel.connectors.ai.google instead for Google AI services.",
    DeprecationWarning,
    stacklevel=2,
)
