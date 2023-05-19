// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.vectoroperations;

import com.microsoft.semantickernel.ai.EmbeddingVector;

public interface CosineSimilarity<T extends Number> {
    double cosineSimilarity(EmbeddingVector<T> other);
}
