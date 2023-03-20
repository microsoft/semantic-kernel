/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Embedding } from './embedding';
import { IEmbeddingWithMetadata } from './iEmbeddingWithMetadata';

/**
 * Represents an searchable index of Embedding<TEmbedding> structs.
 */
export interface IEmbeddingIndex {
    /**
     * Gets the nearest matches to the Embedding<TEmbedding>.
     * @param container The storage container to search.
     * @param embedding The input Embedding<TEmbedding> to use as the search.
     * @param topNCount The max number of results to return.
     * @param minScore The minimum score to consider in the distance calculation.
     * @returns A tuple consisting of the IEmbeddingWithMetadata<TEmbedding> and the similarity score as a double.
     */
    getNearestNMatchesAsync(
        container: string,
        embedding: Embedding,
        topNCount?: number,
        minScore?: number
    ): Promise<[IEmbeddingWithMetadata, number]>;
}

/**
 * Common extension methods for IEmbeddingIndex<TEmbedding> objects.
 */
export class EmbeddingIndexExtensions {
    public static getNearestMatchAsync(
        index: IEmbeddingIndex,
        container: string,
        embedding: Embedding,
        minScore?: number
    ): Promise<[IEmbeddingWithMetadata, number]> {
        if (!index) {
            throw new Error('Embedding index cannot be NULL');
        }

        return index.getNearestNMatchesAsync(container, embedding, 1, minScore).then((match) => match || [null, 0]);
    }
}
