/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { EmbeddingReadOnlySpan } from './embeddingReadOnlySpan';
import { VectorOperations } from './vectorOperations';

/**
 * A view of a vector that allows for low-level, optimized, read-write mathematical operations.
 */
export class EmbeddingSpan {
    /**
     * The underlying Span of unmanaged data.
     */
    public span: number[];

    /**
     * Constructor
     * @param vector A a vector of contiguous, unmanaged data.
     */
    constructor(vector: number[]) {
        this.span = vector;
    }

    /**
     * Normalizes the underlying vector in-place, such that the Euclidean length is 1.
     * @returns A EmbeddingReadOnlySpan with 'IsNormalized' set to true.
     */
    public normalize(): EmbeddingReadOnlySpan {
        VectorOperations.normalizeInPlace(this.span);
        return new EmbeddingReadOnlySpan(this.span, true);
    }

    /**
     * Calculates the dot product of this vector with another.
     * @param other The second vector.
     * @returns The dot product as a double.
     */
    public dot(other: EmbeddingSpan): number {
        return VectorOperations.dotProduct(this.span, other.span);
    }

    /**
     * Calculates the Euclidean length of this vector.
     * @returns The Euclidean length as a double.
     */
    public euclideanLength(): number {
        return VectorOperations.euclideanLength(this.span);
    }

    /**
     * Calculates the cosine similarity of this vector with another.
     * @param other The second vector.
     * @returns The cosine similarity as a double.
     * @remarks This operation can be performed much faster if the vectors are known to be normalized, by
     * converting to a EmbeddingReadOnlySpan with constructor parameter 'isNormalized' true.
     */
    public cosineSimilarity(other: EmbeddingSpan): number {
        return VectorOperations.cosineSimilarity(this.span, other.span);
    }
}
