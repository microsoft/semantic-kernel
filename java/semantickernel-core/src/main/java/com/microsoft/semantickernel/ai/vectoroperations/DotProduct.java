// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.vectoroperations;

import com.microsoft.semantickernel.ai.EmbeddingVector;

public interface DotProduct<T extends Number> {
    double dot(EmbeddingVector<T> other);
}
