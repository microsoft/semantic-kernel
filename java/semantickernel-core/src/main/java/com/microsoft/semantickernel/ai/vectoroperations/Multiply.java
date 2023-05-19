// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.vectoroperations;

import com.microsoft.semantickernel.ai.EmbeddingVector;

public interface Multiply<T extends Number> {
    EmbeddingVector<T> multiply(double multiplier);
}
