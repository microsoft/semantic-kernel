// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import com.microsoft.semantickernel.services.AIService;

/** Interface for text embedding generation services */
public interface TextEmbeddingGeneration extends EmbeddingGeneration<String, Float>, AIService {}
