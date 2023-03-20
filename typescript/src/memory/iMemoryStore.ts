// Copyright (c) Microsoft. All rights reserved.

import { IEmbeddingIndex, IEmbeddingWithMetadata } from '../ai/embeddings';

/**
 * An interface for storing and retrieving indexed {@link IEmbeddingWithMetadata}
 */
export interface IMemoryStore extends IDataStore<IEmbeddingWithMetadata, IEmbeddingIndex> {}
