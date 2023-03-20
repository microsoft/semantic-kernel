/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

/**
 * Represents a strongly typed vector of numeric data.
 */
export class Embedding {
    private readonly _vector: number[];

    /**
     * An empty Embedding instance.
     */
    public static readonly Empty: Embedding = new Embedding([]);

    /**
     * Initializes a new instance of the Embedding class that contains numeric elements copied
     * from the specified collection.
     * @param vector The source data.
     */
    constructor(vector: number[]) {
        // Create a local, protected copy
        this._vector = [...vector];
    }

    /**
     * Gets the vector as a ReadOnlyCollection<T>.
     */
    public get vector(): ReadonlyArray<number> {
        return this._vector;
    }

    /**
     * true if the vector is empty.
     */
    public get isEmpty(): boolean {
        return this._vector.length === 0;
    }

    /**
     * The number of elements in the vector.
     */
    public get count(): number {
        return this._vector.length;
    }

    /**
     * Compares two embeddings for equality.
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
     * @param left The left Embedding<TData>.
     * @param right The right Embedding<TData>.
     * @returns true if the embeddings contain identical data; false otherwise
     */
    public static equals(left: Embedding, right: Embedding): boolean {
        return left.equals(right);
    }

    /**
     * Implicit creation of an Embedding<TData> object from an array of data.>
     * @param vector An array of data.
     */
    public static fromArray(vector: number[]): Embedding {
        return new Embedding(vector);
    }

    /**
     * Implicit creation of an array of type TData from a Embedding<TData>.
     * @param embedding Source Embedding<TData>.
     * @remarks A clone of the underlying data.
     */
    public static toArray(embedding: Embedding): number[] {
        return [...embedding._vector];
    }

    /**
     * Implicit creation of an ReadOnlySpan<T> from a Embedding<TData>.
     * @param embedding Source Embedding<TData>.
     * @remarks A clone of the underlying data.
     */
    public static toReadOnlySpan(embedding: Embedding): Readonly<number[]> {
        return [...embedding._vector];
    }
}
