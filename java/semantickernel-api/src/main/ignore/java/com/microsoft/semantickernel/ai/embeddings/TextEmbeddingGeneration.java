// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings;

import com.microsoft.semantickernel.aiservices.AIService;

/** Interface for text embedding generation services */
public interface TextEmbeddingGeneration extends EmbeddingGeneration<String>, AIService {
    interface Builder extends EmbeddingGeneration.Builder<String, TextEmbeddingGeneration> {}
}
