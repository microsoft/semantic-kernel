/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Embedding } from './embedding';
import { VectorOperations } from './vectorOperations';

/**
 * A view of a vector that allows for low-level, optimized, read-only mathematical operations.
 */
export class EmbeddingReadOnlySpan {
    private readonly _vector: ReadonlyArray<number>;
    private readonly _isNormalized: boolean;

    /**
     * Constructor
     * @param vector A a vector or Embedding of contiguous, unmanaged data.
     * @param isNormalized Indicates whether the data was pre-normalized.
     *
     * This does not verified that the data is normalized, nor make any guarantees that it remains so,
     * as the data can be modified at its source. The isNormalized parameter simply
     * directs these operations to perform faster if the data is known to be normalized.
     */
    constructor(vector: Embedding | number[] | ReadonlyArray<number>, isNormalized: boolean = false) {
        this._vector = vector instanceof Embedding ? Embedding.toReadOnlySpan(vector) : [...vector];
        this._isNormalized = isNormalized;
    }

    /**
     * Gets the underlying ReadOnlySpan of unmanaged data.
     */
    public get readOnlySpan(): ReadonlyArray<number> {
        return this._vector;
    }

    /**
     * True if the data was specified to be normalized at construction.
     */
    public get IsNormalized(): boolean {
        return this._isNormalized;
    }

    /**
     * Calculates the dot product of this vector with another.
     * @param other The second vector.
     * @returns The dot product as a double
     */
    public dot(other: EmbeddingReadOnlySpan): number {
        return VectorOperations.dotProduct(this.readOnlySpan, other.readOnlySpan);
    }

    /**
     * Calculates the Euclidean length of this vector.
     * @returns The Euclidean length as a double
     */
    public euclideanLength(): number {
        return VectorOperations.euclideanLength(this.readOnlySpan);
    }

    /**
     * Calculates the cosine similarity of this vector with another.
     * @param other The second vector.
     * @returns The cosine similarity as a double.
     */
    public cosineSimilarity(other: EmbeddingReadOnlySpan): number {
        if (this.IsNormalized && other.IsNormalized) {
            // Because Normalized embeddings already have normalized lengths, cosine similarity is much
            // faster - just a dot product. Don't have to compute lengths, square roots, etc.
            return this.dot(other);
        }

        return VectorOperations.cosineSimilarity(this.readOnlySpan, other.readOnlySpan);
    }
}
