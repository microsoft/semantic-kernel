/**
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License.
 */

import { Embedding } from './embedding';

/**
 * Represents a generator of embeddings.
 * @template TValue The type from which embeddings will be generated.
 */
interface IEmbeddingGenerator<TValue = string> {
    /**
     * Generates an embedding from the given data.
     * @param data List of strings to generate embeddings for
     * @returns List of embeddings
     */
    generateEmbeddings(data: TValue[]): Promise<Embedding[]>;
}

/**
 * Provides a collection of static methods for operating on IEmbeddingGenerator objects.
 */
export class EmbeddingGeneratorExtensions {
    /**
     * Generates an embedding from the given value.
     * @template TValue The type from which embeddings will be generated.
     * @param generator The embedding generator.
     * @param value A value from which an Embedding will be generated.
     * @returns A list of Embedding structs representing the input value.
     */
    static GenerateEmbeddingAsync<TValue = string>(
        generator: IEmbeddingGenerator<TValue>,
        value: TValue
    ): Promise<Embedding[]> {
        if (!generator) {
            throw new Error('Embeddings generator cannot be NULL');
        }
        return generator.generateEmbeddings([value]);
    }
}
