// Copyright (c) Microsoft. All rights reserved.

import { Embedding } from './embedding';

/**
 * Represents an object that has an {@link Embedding}.
 */
export interface IEmbeddingWithMetadata {
    /**
     * Gets the {@link Embedding}.
     */
    readonly embedding: Embedding;
}
