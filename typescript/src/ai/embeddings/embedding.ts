// Copyright (c) Microsoft. All rights reserved.

import { Verify } from '../../utils/verify';

/**
 * Represents a strongly typed vector of numeric data.
 */
export class Embedding {
    private readonly _vector: number[];

    /**
     * An empty {@link Embedding} instance.
     */
    public static readonly empty = new Embedding([]);

    /**
     * Initializes a new instance of the {@link Embedding} class
     * that contains numeric elements copied from the specified collection.
     *
     * @constructor
     * @param vector The source data.
     */
    public constructor(vector: number[]) {
        Verify.notNull(vector, 'Vector is null or undefined.');

        // Create a local, protected copy
        this._vector = [...vector];
    }

    /**
     * Gets the vector as read-only collection.
     *
     * @returns the vector as read-only collection.
     */
    public get vector(): readonly number[] {
        return this._vector;
    }

    /**
     * Check if vector is empty.
     *
     * @returns true if the vector is empty.
     */
    public get isEmpty(): boolean {
        return this._vector.length === 0;
    }

    /**
     * The number of elements in the vector.
     *
     * @returns The vector length.
     */
    public get count(): number {
        return this._vector.length;
    }

    /**
     * Compares two embeddings for equality.
     *
     * @param other The Embedding to compare with the current object.
     * @returns true if the specified object is equal to the current object; otherwise, false.
     */
    public equals(other: Embedding | object): boolean {
        if (other instanceof Embedding) {
            if (other._vector.length !== this._vector.length) {
                return false;
            }

            for (let i = 0; i < other._vector.length; i++) {
                if (other._vector[i] !== this._vector[i]) {
                    return false;
                }
            }
            return true;
        }

        return false;
    }

    /**
     * Compares two embeddings for equality.
     *
     * @param left The left Embedding.
     * @param right The right Embedding.
     * @returns true if the embeddings contain identical data; false otherwise.
     */
    public static equals(left: Embedding, right: Embedding): boolean {
        return left.equals(right);
    }

    /**
     * Implicit creation of an Embedding object from an array of data.
     *
     * @param vector An array of data.
     */
    public static fromArray(vector: number[]): Embedding {
        return new Embedding(vector);
    }

    /**
     * Implicit creation of an array of type TData from a Embedding.
     *
     * @param embedding Source Embedding.
     * @remarks A clone of the underlying data.
     */
    public static toArray(embedding: Embedding): number[] {
        return [...embedding._vector];
    }

    /**
     * Implicit creation of an ReadOnlySpan<T> from a Embedding.
     *
     * @param embedding Source Embedding.
     * @remarks A clone of the underlying data.
     */
    public static toReadOnlySpan(embedding: Embedding): readonly number[] {
        return [...embedding._vector];
    }
}
