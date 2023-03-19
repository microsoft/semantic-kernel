// Copyright (c) Microsoft. All rights reserved.

import { Verify } from '../../utils/verify';
import { Embedding } from './embedding';
import { IEmbeddingWithMetadata } from './iEmbeddingWithMetadata';

/**
 * Represents an searchable index of {@link Embedding} structs.
 */
export interface IEmbeddingIndex {
    /**
     * Gets the nearest matches to the Embedding.
     *
     * @param collection The storage collection to search.
     * @param embedding The input {@link Embedding} to use as the search.
     * @param limit The max number of results to return.
     * @param minRelevanceScore The minimum score to consider in the distance calculation.
     * @returns A tuple consisting of the {@link IEmbeddingWithMetadata} and the similarity score as a double.
     */
    getNearestMatches(
        collection: string,
        embedding: Embedding,
        limit: number,
        minRelevanceScore: number
    ): Promise<[IEmbeddingWithMetadata, number]>;
}

/**
 * Common extension methods for {@link IEmbeddingIndex} objects.
 */
export class EmbeddingIndexExtensions {
    public static async getNearestMatch(
        index: IEmbeddingIndex,
        collection: string,
        embedding: Embedding,
        minScore: number = 0.0
    ): Promise<[IEmbeddingWithMetadata, number]> {
        Verify.notNull(index, 'Embedding index cannot be NULL');

        return index
            .getNearestMatches(collection, embedding, 1, minScore)
            .then((match) => match || [null, 0]);
    }
}
