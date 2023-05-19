// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.ai.vectoroperations;

import com.microsoft.semantickernel.ai.EmbeddingVector;

public interface Divide<T extends Number> {
    EmbeddingVector<T> divide(double divisor);
}
