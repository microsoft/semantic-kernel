// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.embeddings.vectoroperations;

import com.microsoft.semantickernel.ai.embeddings.EmbeddingVector;

public interface Multiply {
    EmbeddingVector multiply(float multiplier);
}
